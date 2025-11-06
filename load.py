#!/usr/bin/env python3
"""Script de Carregamento e Indexação de Documentos.

Este script carrega documentos em múltiplos formatos (PDF, DOCX, TXT, MD, CSV, Excel),
divide-os em chunks, gera embeddings e os armazena no Supabase para RAG.
"""

import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langchain_community.document_loaders import (
    DirectoryLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    UnstructuredWordDocumentLoader,
)
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_core.documents import Document as LangChainDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_settings
from src.constants import SUPPORTED_DOCUMENT_TYPES
from src.exceptions import DocumentLoadError, VectorStoreError
from src.logging_config import get_logger
from src.services import SupabaseService
from src.utils.document_loaders import CSVLoader, ExcelLoader

# Load environment variables
load_dotenv()


class DocumentIndexer:
    """Gerencia o carregamento, divisão e indexação de documentos.

    Esta classe fornece uma interface limpa para o pipeline de
    indexação de documentos com tratamento adequado de erros.

    Attributes:
        settings: Configurações da aplicação
        logger: Instância do logger
        supabase_service: Serviço Supabase para armazenamento
    """

    def __init__(self) -> None:
        """Inicializa o indexador de documentos."""
        self.settings = get_settings()
        self.logger = get_logger(self.settings)
        self.supabase_service = SupabaseService(
            settings=self.settings,
            logger=self.logger,
        )

    def _get_loader_for_file(self, file_path: Path) -> object:
        """Obtém o carregador apropriado para um arquivo baseado em sua extensão.

        Args:
            file_path: Caminho para o arquivo

        Returns:
            Instância apropriada do carregador para o tipo de arquivo

        Raises:
            ValueError: Se o tipo de arquivo não for suportado
        """
        extension = file_path.suffix.lower()

        loader_map = {
            ".pdf": lambda: PyPDFLoader(str(file_path)),
            ".txt": lambda: TextLoader(str(file_path), encoding="utf-8"),
            ".md": lambda: UnstructuredMarkdownLoader(str(file_path)),
            ".rst": lambda: TextLoader(str(file_path), encoding="utf-8"),
            ".doc": lambda: UnstructuredWordDocumentLoader(str(file_path)),
            ".docx": lambda: UnstructuredWordDocumentLoader(str(file_path)),
            ".csv": lambda: CSVLoader(file_path),
            ".xlsx": lambda: ExcelLoader(file_path),
            ".xls": lambda: ExcelLoader(file_path),
        }

        if extension not in loader_map:
            raise ValueError(f"Tipo de arquivo não suportado: {extension}")

        return loader_map[extension]()

    def load_documents(self) -> list[LangChainDocument]:
        """Carrega todos os documentos suportados do diretório de dados.

        Suporta: PDF, DOCX, DOC, TXT, Markdown, CSV, Excel (XLSX, XLS)

        Returns:
            Lista de documentos carregados

        Raises:
            DocumentLoadError: Se nenhum documento for encontrado ou o carregamento falhar
        """
        self.logger.info(
            "Carregando documentos",
            action="LOADING",
            directory=str(self.settings.data_dir),
        )

        if not self.settings.data_dir.exists():
            raise DocumentLoadError(
                f"Diretório de dados '{self.settings.data_dir}' não encontrado. "
                f"Por favor, crie-o e adicione arquivos de documentos."
            )

        # Encontra todos os arquivos suportados
        supported_files = []
        file_types_found = {}

        for ext in SUPPORTED_DOCUMENT_TYPES:
            files = list(self.settings.data_dir.glob(f"*{ext}"))
            if files:
                supported_files.extend(files)
                file_types_found[ext] = len(files)

        if not supported_files:
            formats = ", ".join(SUPPORTED_DOCUMENT_TYPES)
            raise DocumentLoadError(
                f"Nenhum documento suportado encontrado em '{self.settings.data_dir}'. "
                f"Formatos suportados: {formats}"
            )

        self.logger.info(
            "Arquivos suportados encontrados",
            action="SUCCESS",
            total=len(supported_files),
            by_type=file_types_found,
        )

        # Carrega documentos
        all_documents = []
        load_errors = []

        try:
            for file_path in supported_files:
                try:
                    self.logger.info(
                        f"Carregando arquivo: {file_path.name}",
                        action="LOADING",
                        file_type=file_path.suffix,
                    )

                    loader = self._get_loader_for_file(file_path)
                    documents = loader.load()
                    all_documents.extend(documents)

                    self.logger.info(
                        f"Arquivo carregado com sucesso: {file_path.name}",
                        action="SUCCESS",
                        chunks=len(documents),
                    )

                except Exception as e:
                    error_msg = f"Falha ao carregar {file_path.name}: {str(e)}"
                    self.logger.warning(
                        error_msg,
                        action="WARNING",
                        file=str(file_path),
                        error=str(e),
                    )
                    load_errors.append(error_msg)

            if not all_documents:
                error_summary = "\n".join(load_errors)
                raise DocumentLoadError(
                    f"Falha ao carregar qualquer documento. Erros:\n{error_summary}"
                )

            if load_errors:
                self.logger.warning(
                    "Alguns arquivos falharam ao carregar",
                    action="WARNING",
                    failed_count=len(load_errors),
                    success_count=len(all_documents),
                )

            self.logger.info(
                "Todos os documentos carregados com sucesso",
                action="SUCCESS",
                total_chunks=len(all_documents),
                files_processed=len(supported_files),
                files_failed=len(load_errors),
            )

            return all_documents

        except DocumentLoadError:
            raise

        except Exception as e:
            self.logger.error(
                "Falha ao carregar documentos",
                action="ERROR",
                exc_info=True,
            )
            raise DocumentLoadError(
                "Falha ao carregar documentos",
                original_error=e,
            ) from e

    def split_documents(
        self,
        documents: list[LangChainDocument],
    ) -> list[LangChainDocument]:
        """Divide documentos em chunks menores.

        Args:
            documents: Documentos para dividir

        Returns:
            Lista de chunks de documentos
        """
        self.logger.info(
            "Dividindo documentos em chunks",
            action="LOADING",
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

        chunks = text_splitter.split_documents(documents)

        self.logger.info(
            "Documentos divididos em chunks",
            action="SUCCESS",
            chunks=len(chunks),
        )

        return chunks

    async def index_documents(
        self,
        chunks: list[LangChainDocument],
    ) -> SupabaseVectorStore:
        """Cria vector store e indexa documentos.

        Args:
            chunks: Chunks de documentos para indexar

        Returns:
            Vector store configurado

        Raises:
            VectorStoreError: Se a indexação falhar
        """
        self.logger.info(
            "Criando vector store no Supabase",
            action="LOADING",
            table=self.settings.supabase_table_name,
        )
        self.logger.info(
            "Isso pode levar alguns minutos...",
            action="LOADING",
        )

        try:
            # Import aqui para evitar dependência circular
            from langchain_openai import OpenAIEmbeddings

            # Cria embeddings
            embeddings = OpenAIEmbeddings(
                model=self.settings.embedding_model,
                openai_api_key=self.settings.openai_api_key,
            )

            # Cria vector store
            vectorstore = SupabaseVectorStore.from_documents(
                documents=chunks,
                embedding=embeddings,
                client=self.supabase_service.client,
                table_name=self.settings.supabase_table_name,
                query_name=self.settings.supabase_query_name,
            )

            self.logger.info(
                "Vector store criado com sucesso",
                action="SUCCESS",
                vectors=len(chunks),
            )

            return vectorstore

        except Exception as e:
            self.logger.error(
                "Falha ao criar vector store",
                action="ERROR",
                exc_info=True,
            )
            raise VectorStoreError(
                "Falha ao indexar documentos no Supabase",
                operation="create_vectorstore",
                original_error=e,
            ) from e

    async def run(self) -> None:
        """Executa o pipeline completo de indexação."""
        print("\n" + "=" * 60)
        print("🚀 INDEXAÇÃO DE DOCUMENTOS - RAG")
        print("=" * 60 + "\n")

        try:
            # Carrega documentos
            documents = self.load_documents()

            # Divide em chunks
            chunks = self.split_documents(documents)

            # Indexa documentos
            await self.index_documents(chunks)

            # Resumo de sucesso
            print("\n" + "=" * 60)
            print("✅ INDEXAÇÃO COMPLETA!")
            print("=" * 60)
            print(f"📊 Total de vetores: {len(chunks)}")
            print(f"📁 Localização: Supabase (tabela '{self.settings.supabase_table_name}')")
            print("\n💡 Próximo passo: Execute 'python bot.py' para iniciar o bot")
            print("=" * 60 + "\n")

        except DocumentLoadError as e:
            print(f"\n❌ Erro ao Carregar Documentos: {e}\n")
            sys.exit(1)

        except VectorStoreError as e:
            print(f"\n❌ Erro no Vector Store: {e}\n")
            sys.exit(1)

        except Exception as e:
            print(f"\n❌ Erro Inesperado: {e}\n")
            import traceback

            traceback.print_exc()
            sys.exit(1)


async def main() -> None:
    """Ponto de entrada principal para indexação de documentos."""
    indexer = DocumentIndexer()
    await indexer.run()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
