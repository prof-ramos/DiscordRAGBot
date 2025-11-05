#!/usr/bin/env python3
"""Document Loading and Indexing Script.

This script loads PDF documents, splits them into chunks,
generates embeddings, and stores them in Supabase for RAG.
"""

import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_core.documents import Document as LangChainDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_settings
from src.exceptions import DocumentLoadError, VectorStoreError
from src.logging_config import get_logger
from src.services import SupabaseService

# Load environment variables
load_dotenv()


class DocumentIndexer:
    """Handles document loading, splitting, and indexing.

    This class provides a clean interface for the document
    indexing pipeline with proper error handling.

    Attributes:
        settings: Application settings
        logger: Logger instance
        supabase_service: Supabase service for storage
    """

    def __init__(self) -> None:
        """Initialize the document indexer."""
        self.settings = get_settings()
        self.logger = get_logger(self.settings)
        self.supabase_service = SupabaseService(
            settings=self.settings,
            logger=self.logger,
        )

    def load_documents(self) -> list[LangChainDocument]:
        """Load all PDF documents from data directory.

        Returns:
            List of loaded documents

        Raises:
            DocumentLoadError: If no documents found or loading fails
        """
        self.logger.info(
            "Loading documents",
            action="LOADING",
            directory=str(self.settings.data_dir),
        )

        if not self.settings.data_dir.exists():
            raise DocumentLoadError(
                f"Data directory '{self.settings.data_dir}' not found. "
                f"Please create it and add PDF files."
            )

        # Find PDF files
        pdf_files = list(self.settings.data_dir.glob("*.pdf"))

        if not pdf_files:
            raise DocumentLoadError(
                f"No PDF files found in '{self.settings.data_dir}'. "
                f"Please add .pdf files to this directory."
            )

        self.logger.info(
            "PDF files found",
            action="SUCCESS",
            count=len(pdf_files),
        )

        # Load documents
        try:
            loader = DirectoryLoader(
                str(self.settings.data_dir),
                glob="**/*.pdf",
                loader_cls=PyPDFLoader,
                show_progress=True,
            )

            documents = loader.load()

            self.logger.info(
                "Documents loaded",
                action="SUCCESS",
                pages=len(documents),
            )

            return documents

        except Exception as e:
            self.logger.error(
                "Failed to load documents",
                action="ERROR",
                exc_info=True,
            )
            raise DocumentLoadError(
                "Failed to load PDF documents",
                original_error=e,
            ) from e

    def split_documents(
        self,
        documents: list[LangChainDocument],
    ) -> list[LangChainDocument]:
        """Split documents into smaller chunks.

        Args:
            documents: Documents to split

        Returns:
            List of document chunks
        """
        self.logger.info(
            "Splitting documents into chunks",
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
            "Documents split into chunks",
            action="SUCCESS",
            chunks=len(chunks),
        )

        return chunks

    async def index_documents(
        self,
        chunks: list[LangChainDocument],
    ) -> SupabaseVectorStore:
        """Create vector store and index documents.

        Args:
            chunks: Document chunks to index

        Returns:
            Configured vector store

        Raises:
            VectorStoreError: If indexing fails
        """
        self.logger.info(
            "Creating vector store in Supabase",
            action="LOADING",
            table=self.settings.supabase_table_name,
        )
        self.logger.info(
            "This may take several minutes...",
            action="LOADING",
        )

        try:
            # Import here to avoid circular dependency
            from langchain_openai import OpenAIEmbeddings

            # Create embeddings
            embeddings = OpenAIEmbeddings(
                model=self.settings.embedding_model,
                openai_api_key=self.settings.openai_api_key,
            )

            # Create vector store
            vectorstore = SupabaseVectorStore.from_documents(
                documents=chunks,
                embedding=embeddings,
                client=self.supabase_service.client,
                table_name=self.settings.supabase_table_name,
                query_name=self.settings.supabase_query_name,
            )

            self.logger.info(
                "Vector store created successfully",
                action="SUCCESS",
                vectors=len(chunks),
            )

            return vectorstore

        except Exception as e:
            self.logger.error(
                "Failed to create vector store",
                action="ERROR",
                exc_info=True,
            )
            raise VectorStoreError(
                "Failed to index documents in Supabase",
                operation="create_vectorstore",
                original_error=e,
            ) from e

    async def run(self) -> None:
        """Run the complete indexing pipeline."""
        print("\n" + "=" * 60)
        print("🚀 DOCUMENT INDEXING - RAG")
        print("=" * 60 + "\n")

        try:
            # Load documents
            documents = self.load_documents()

            # Split into chunks
            chunks = self.split_documents(documents)

            # Index documents
            await self.index_documents(chunks)

            # Success summary
            print("\n" + "=" * 60)
            print("✅ INDEXING COMPLETE!")
            print("=" * 60)
            print(f"📊 Total vectors: {len(chunks)}")
            print(f"📁 Location: Supabase (table '{self.settings.supabase_table_name}')")
            print("\n💡 Next step: Run 'python bot.py' to start the bot")
            print("=" * 60 + "\n")

        except DocumentLoadError as e:
            print(f"\n❌ Document Loading Error: {e}\n")
            sys.exit(1)

        except VectorStoreError as e:
            print(f"\n❌ Vector Store Error: {e}\n")
            sys.exit(1)

        except Exception as e:
            print(f"\n❌ Unexpected Error: {e}\n")
            import traceback

            traceback.print_exc()
            sys.exit(1)


async def main() -> None:
    """Main entry point for document indexing."""
    indexer = DocumentIndexer()
    await indexer.run()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
