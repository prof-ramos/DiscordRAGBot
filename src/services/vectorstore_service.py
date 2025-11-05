"""Vector store service for document retrieval and embedding."""

from typing import Optional

from langchain_community.vectorstores import SupabaseVectorStore
from langchain_core.documents import Document as LangChainDocument
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import OpenAIEmbeddings

from src.config import Settings
from src.exceptions import VectorStoreError, VectorStoreNotLoadedError
from src.logging_config import BotLogger
from src.models import Document
from src.services.supabase_service import SupabaseService


class VectorStoreService:
    """Manages vector store operations for document retrieval.

    This service handles embedding generation, vector storage,
    and similarity search operations.

    Attributes:
        settings: Application settings
        logger: Logger instance
        supabase_service: Supabase service instance
    """

    def __init__(
        self,
        settings: Settings,
        logger: BotLogger,
        supabase_service: SupabaseService,
    ) -> None:
        """Initialize the vector store service.

        Args:
            settings: Application settings
            logger: Logger instance
            supabase_service: Supabase service for database access
        """
        self.settings = settings
        self.logger = logger
        self.supabase_service = supabase_service
        self._embeddings: Optional[OpenAIEmbeddings] = None
        self._vectorstore: Optional[SupabaseVectorStore] = None
        self._retriever: Optional[VectorStoreRetriever] = None
        self._loaded = False

    @property
    def embeddings(self) -> OpenAIEmbeddings:
        """Get or create embeddings model (lazy initialization).

        Returns:
            OpenAI embeddings instance
        """
        if self._embeddings is None:
            self._embeddings = self._create_embeddings()
        return self._embeddings

    @property
    def vectorstore(self) -> SupabaseVectorStore:
        """Get vector store instance.

        Returns:
            Vector store instance

        Raises:
            VectorStoreNotLoadedError: If vector store not loaded
        """
        if self._vectorstore is None:
            raise VectorStoreNotLoadedError(
                "Vector store must be loaded before use. Call load() first."
            )
        return self._vectorstore

    @property
    def retriever(self) -> VectorStoreRetriever:
        """Get retriever instance.

        Returns:
            Retriever instance

        Raises:
            VectorStoreNotLoadedError: If vector store not loaded
        """
        if self._retriever is None:
            raise VectorStoreNotLoadedError(
                "Retriever not available. Ensure vector store is loaded."
            )
        return self._retriever

    @property
    def is_loaded(self) -> bool:
        """Check if vector store is loaded and ready."""
        return self._loaded

    def _create_embeddings(self) -> OpenAIEmbeddings:
        """Create OpenAI embeddings model.

        Returns:
            Configured embeddings model
        """
        self.logger.info(
            "Creating embeddings model",
            action="LOADING",
            model=self.settings.embedding_model,
        )

        embeddings = OpenAIEmbeddings(
            model=self.settings.embedding_model,
            openai_api_key=self.settings.openai_api_key,
        )

        self.logger.info(
            "Embeddings model created",
            action="SUCCESS",
        )

        return embeddings

    async def load(self) -> None:
        """Load vector store from Supabase.

        Raises:
            VectorStoreError: If loading fails
        """
        try:
            self.logger.info(
                "Loading vector store from Supabase",
                action="LOADING",
                table=self.settings.supabase_table_name,
            )

            # Initialize vector store
            self._vectorstore = SupabaseVectorStore(
                client=self.supabase_service.client,
                embedding=self.embeddings,
                table_name=self.settings.supabase_table_name,
                query_name=self.settings.supabase_query_name,
            )

            # Create retriever
            self._retriever = self._vectorstore.as_retriever(
                search_kwargs={"k": self.settings.k_documents}
            )

            self._loaded = True

            self.logger.info(
                "Vector store loaded successfully",
                action="SUCCESS",
                k_docs=self.settings.k_documents,
            )

        except Exception as e:
            self._loaded = False
            self.logger.error(
                "Failed to load vector store",
                action="ERROR",
                exc_info=True,
            )
            raise VectorStoreError(
                "Failed to load vector store",
                operation="load",
                original_error=e,
            ) from e

    async def similarity_search(
        self,
        query: str,
        k: Optional[int] = None,
    ) -> list[Document]:
        """Perform similarity search.

        Args:
            query: Search query
            k: Number of results (uses default if None)

        Returns:
            List of similar documents

        Raises:
            VectorStoreNotLoadedError: If vector store not loaded
            VectorStoreError: If search fails
        """
        if not self.is_loaded:
            raise VectorStoreNotLoadedError()

        try:
            k = k or self.settings.k_documents

            self.logger.debug(
                "Performing similarity search",
                query=query[:50],
                k=k,
            )

            # Perform search
            docs = await self.vectorstore.asimilarity_search(query, k=k)

            # Convert to our Document model
            results = [
                Document(
                    content=doc.page_content,
                    metadata=doc.metadata,
                )
                for doc in docs
            ]

            self.logger.debug(
                "Similarity search completed",
                results_found=len(results),
            )

            return results

        except VectorStoreNotLoadedError:
            raise
        except Exception as e:
            self.logger.error(
                "Similarity search failed",
                action="ERROR",
                exc_info=True,
            )
            raise VectorStoreError(
                "Similarity search failed",
                operation="similarity_search",
                original_error=e,
            ) from e

    async def add_documents(
        self,
        documents: list[Document],
    ) -> list[str]:
        """Add documents to vector store.

        Args:
            documents: Documents to add

        Returns:
            List of document IDs

        Raises:
            VectorStoreError: If adding documents fails
        """
        try:
            self.logger.info(
                "Adding documents to vector store",
                action="LOADING",
                count=len(documents),
            )

            # Convert to LangChain documents
            lc_docs = [
                LangChainDocument(
                    page_content=doc.content,
                    metadata=doc.metadata,
                )
                for doc in documents
            ]

            # Add to vector store
            ids = await self.vectorstore.aadd_documents(lc_docs)

            self.logger.info(
                "Documents added successfully",
                action="SUCCESS",
                count=len(ids),
            )

            return ids

        except Exception as e:
            self.logger.error(
                "Failed to add documents",
                action="ERROR",
                exc_info=True,
            )
            raise VectorStoreError(
                "Failed to add documents",
                operation="add_documents",
                original_error=e,
            ) from e
