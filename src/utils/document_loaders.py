"""Carregadores customizados de documentos para diversos formatos.

Este módulo fornece carregadores especializados para formatos que requerem
processamento customizado, particularmente para dados estruturados como CSV e Excel.
"""

from pathlib import Path
from typing import Iterator, List

import pandas as pd
from langchain_core.documents import Document


class CSVLoader:
    """Carregador para arquivos CSV que converte dados tabulares em documentos de texto.

    Este carregador lê arquivos CSV e converte cada linha em uma representação textual,
    opcionalmente incluindo cabeçalhos de colunas para contexto.

    Attributes:
        file_path: Caminho para o arquivo CSV
        encoding: Codificação do arquivo (padrão: utf-8)
        include_headers: Se deve incluir cabeçalhos de coluna em cada linha
        source_column: Coluna opcional para usar como fonte do documento
    """

    def __init__(
        self,
        file_path: str | Path,
        encoding: str = "utf-8",
        include_headers: bool = True,
        source_column: str | None = None,
    ) -> None:
        """Inicializa o carregador CSV.

        Args:
            file_path: Caminho para o arquivo CSV
            encoding: Codificação do arquivo (padrão: utf-8)
            include_headers: Se deve incluir cabeçalhos de coluna em cada linha
            source_column: Nome opcional da coluna para usar como fonte do documento
        """
        self.file_path = Path(file_path)
        self.encoding = encoding
        self.include_headers = include_headers
        self.source_column = source_column

    def load(self) -> List[Document]:
        """Carrega e analisa o arquivo CSV.

        Returns:
            Lista de objetos Document, um por linha

        Raises:
            FileNotFoundError: Se o arquivo CSV não existir
            pd.errors.EmptyDataError: Se o arquivo CSV estiver vazio
            pd.errors.ParserError: Se o arquivo CSV estiver malformado
        """
        # Lê o arquivo CSV
        df = pd.read_csv(self.file_path, encoding=self.encoding)

        documents = []
        for idx, row in df.iterrows():
            # Cria representação textual da linha
            if self.include_headers:
                # Formato: "Coluna1: valor1, Coluna2: valor2, ..."
                content = ", ".join(
                    f"{col}: {row[col]}" for col in df.columns if pd.notna(row[col])
                )
            else:
                # Formato: "valor1, valor2, valor3, ..."
                content = ", ".join(str(val) for val in row if pd.notna(val))

            # Determina a fonte
            source = str(self.file_path)
            if self.source_column and self.source_column in df.columns:
                source = f"{self.file_path} - Linha {idx}: {row[self.source_column]}"
            else:
                source = f"{self.file_path} - Linha {idx}"

            # Cria documento com metadados
            doc = Document(
                page_content=content,
                metadata={
                    "source": source,
                    "row": int(idx),
                    "format": "csv",
                    "columns": list(df.columns),
                },
            )
            documents.append(doc)

        return documents

    def lazy_load(self) -> Iterator[Document]:
        """Carrega documentos de forma lazy, um de cada vez.

        Yields:
            Objetos Document um de cada vez

        Raises:
            FileNotFoundError: Se o arquivo CSV não existir
            pd.errors.EmptyDataError: Se o arquivo CSV estiver vazio
            pd.errors.ParserError: Se o arquivo CSV estiver malformado
        """
        # Lê CSV em chunks para eficiência de memória
        chunk_size = 1000
        for chunk in pd.read_csv(
            self.file_path, encoding=self.encoding, chunksize=chunk_size
        ):
            for idx, row in chunk.iterrows():
                if self.include_headers:
                    content = ", ".join(
                        f"{col}: {row[col]}"
                        for col in chunk.columns
                        if pd.notna(row[col])
                    )
                else:
                    content = ", ".join(str(val) for val in row if pd.notna(val))

                source = str(self.file_path)
                if self.source_column and self.source_column in chunk.columns:
                    source = f"{self.file_path} - Linha {idx}: {row[self.source_column]}"
                else:
                    source = f"{self.file_path} - Linha {idx}"

                yield Document(
                    page_content=content,
                    metadata={
                        "source": source,
                        "row": int(idx),
                        "format": "csv",
                        "columns": list(chunk.columns),
                    },
                )


class ExcelLoader:
    """Carregador para arquivos Excel (.xlsx, .xls) que converte dados tabulares em texto.

    Este carregador lê arquivos Excel e converte cada linha em uma representação textual.
    Suporta múltiplas planilhas e vários formatos Excel.

    Attributes:
        file_path: Caminho para o arquivo Excel
        sheet_name: Nome ou índice da planilha (padrão: 0 para primeira planilha)
        include_headers: Se deve incluir cabeçalhos de coluna em cada linha
        source_column: Coluna opcional para usar como fonte do documento
    """

    def __init__(
        self,
        file_path: str | Path,
        sheet_name: str | int = 0,
        include_headers: bool = True,
        source_column: str | None = None,
    ) -> None:
        """Inicializa o carregador Excel.

        Args:
            file_path: Caminho para o arquivo Excel
            sheet_name: Nome da planilha (str) ou índice (int). Use 0 para primeira planilha.
            include_headers: Se deve incluir cabeçalhos de coluna em cada linha
            source_column: Nome opcional da coluna para usar como fonte do documento
        """
        self.file_path = Path(file_path)
        self.sheet_name = sheet_name
        self.include_headers = include_headers
        self.source_column = source_column

    def load(self) -> List[Document]:
        """Carrega e analisa o arquivo Excel.

        Returns:
            Lista de objetos Document, um por linha

        Raises:
            FileNotFoundError: Se o arquivo Excel não existir
            ValueError: Se a planilha não existir
        """
        # Determina o engine baseado na extensão do arquivo
        engine = "openpyxl" if self.file_path.suffix == ".xlsx" else "xlrd"

        # Lê o arquivo Excel
        df = pd.read_excel(
            self.file_path, sheet_name=self.sheet_name, engine=engine
        )

        documents = []
        sheet_info = (
            self.sheet_name if isinstance(self.sheet_name, str) else f"Planilha{self.sheet_name}"
        )

        for idx, row in df.iterrows():
            # Cria representação textual da linha
            if self.include_headers:
                content = ", ".join(
                    f"{col}: {row[col]}" for col in df.columns if pd.notna(row[col])
                )
            else:
                content = ", ".join(str(val) for val in row if pd.notna(val))

            # Determina a fonte
            if self.source_column and self.source_column in df.columns:
                source = (
                    f"{self.file_path} - {sheet_info} - Linha {idx}: {row[self.source_column]}"
                )
            else:
                source = f"{self.file_path} - {sheet_info} - Linha {idx}"

            # Cria documento com metadados
            doc = Document(
                page_content=content,
                metadata={
                    "source": source,
                    "row": int(idx),
                    "sheet": sheet_info,
                    "format": "excel",
                    "file_type": self.file_path.suffix,
                    "columns": list(df.columns),
                },
            )
            documents.append(doc)

        return documents

    def lazy_load(self) -> Iterator[Document]:
        """Carrega documentos de forma lazy, um de cada vez.

        Yields:
            Objetos Document um de cada vez

        Raises:
            FileNotFoundError: Se o arquivo Excel não existir
            ValueError: Se a planilha não existir
        """
        engine = "openpyxl" if self.file_path.suffix == ".xlsx" else "xlrd"
        df = pd.read_excel(
            self.file_path, sheet_name=self.sheet_name, engine=engine
        )

        sheet_info = (
            self.sheet_name if isinstance(self.sheet_name, str) else f"Planilha{self.sheet_name}"
        )

        for idx, row in df.iterrows():
            if self.include_headers:
                content = ", ".join(
                    f"{col}: {row[col]}" for col in df.columns if pd.notna(row[col])
                )
            else:
                content = ", ".join(str(val) for val in row if pd.notna(val))

            if self.source_column and self.source_column in df.columns:
                source = (
                    f"{self.file_path} - {sheet_info} - Linha {idx}: {row[self.source_column]}"
                )
            else:
                source = f"{self.file_path} - {sheet_info} - Linha {idx}"

            yield Document(
                page_content=content,
                metadata={
                    "source": source,
                    "row": int(idx),
                    "sheet": sheet_info,
                    "format": "excel",
                    "file_type": self.file_path.suffix,
                    "columns": list(df.columns),
                },
            )


class MultiSheetExcelLoader:
    """Carregador para arquivos Excel que processa todas as planilhas.

    Este carregador lê todas as planilhas de um arquivo Excel e converte cada linha
    de cada planilha em uma representação textual.

    Attributes:
        file_path: Caminho para o arquivo Excel
        include_headers: Se deve incluir cabeçalhos de coluna em cada linha
        source_column: Coluna opcional para usar como fonte do documento
    """

    def __init__(
        self,
        file_path: str | Path,
        include_headers: bool = True,
        source_column: str | None = None,
    ) -> None:
        """Inicializa o carregador Excel multi-planilhas.

        Args:
            file_path: Caminho para o arquivo Excel
            include_headers: Se deve incluir cabeçalhos de coluna em cada linha
            source_column: Nome opcional da coluna para usar como fonte do documento
        """
        self.file_path = Path(file_path)
        self.include_headers = include_headers
        self.source_column = source_column

    def load(self) -> List[Document]:
        """Carrega e analisa todas as planilhas do arquivo Excel.

        Returns:
            Lista de objetos Document de todas as planilhas

        Raises:
            FileNotFoundError: Se o arquivo Excel não existir
        """
        engine = "openpyxl" if self.file_path.suffix == ".xlsx" else "xlrd"

        # Lê todas as planilhas
        excel_file = pd.ExcelFile(self.file_path, engine=engine)
        documents = []

        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)

            for idx, row in df.iterrows():
                if self.include_headers:
                    content = ", ".join(
                        f"{col}: {row[col]}" for col in df.columns if pd.notna(row[col])
                    )
                else:
                    content = ", ".join(str(val) for val in row if pd.notna(val))

                if self.source_column and self.source_column in df.columns:
                    source = (
                        f"{self.file_path} - {sheet_name} - Linha {idx}: {row[self.source_column]}"
                    )
                else:
                    source = f"{self.file_path} - {sheet_name} - Linha {idx}"

                doc = Document(
                    page_content=content,
                    metadata={
                        "source": source,
                        "row": int(idx),
                        "sheet": sheet_name,
                        "format": "excel",
                        "file_type": self.file_path.suffix,
                        "columns": list(df.columns),
                    },
                )
                documents.append(doc)

        return documents

    def lazy_load(self) -> Iterator[Document]:
        """Carrega documentos de forma lazy de todas as planilhas.

        Yields:
            Objetos Document um de cada vez através de todas as planilhas

        Raises:
            FileNotFoundError: Se o arquivo Excel não existir
        """
        engine = "openpyxl" if self.file_path.suffix == ".xlsx" else "xlrd"
        excel_file = pd.ExcelFile(self.file_path, engine=engine)

        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)

            for idx, row in df.iterrows():
                if self.include_headers:
                    content = ", ".join(
                        f"{col}: {row[col]}" for col in df.columns if pd.notna(row[col])
                    )
                else:
                    content = ", ".join(str(val) for val in row if pd.notna(val))

                if self.source_column and self.source_column in df.columns:
                    source = (
                        f"{self.file_path} - {sheet_name} - Linha {idx}: {row[self.source_column]}"
                    )
                else:
                    source = f"{self.file_path} - {sheet_name} - Linha {idx}"

                yield Document(
                    page_content=content,
                    metadata={
                        "source": source,
                        "row": int(idx),
                        "sheet": sheet_name,
                        "format": "excel",
                        "file_type": self.file_path.suffix,
                        "columns": list(df.columns),
                    },
                )
