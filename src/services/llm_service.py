"""LLM service for response generation with RAG."""

from typing import Optional

from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import (
    create_stuff_documents_chain,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.cache import cached
from src.config import FilterLevel, PromptTemplates, Settings
from src.exceptions import LLMError, VectorStoreNotLoadedError
from src.logging_config import BotLogger
from src.models import Document, QueryRequest, QueryResult
from src.services.vectorstore_service import VectorStoreService


class LLMService:
    """Manages LLM interactions for query processing.

    This service orchestrates RAG queries, combining retrieval
    and generation with configurable prompts.

    Attributes:
        settings: Application settings
        logger: Logger instance
        vectorstore_service: Vector store service for retrieval
    """

    def __init__(
        self,
        settings: Settings,
        logger: BotLogger,
        vectorstore_service: VectorStoreService,
    ) -> None:
        """Initialize the LLM service.

        Args:
            settings: Application settings
            logger: Logger instance
            vectorstore_service: Vector store service for document retrieval
        """
        self.settings = settings
        self.logger = logger
        self.vectorstore_service = vectorstore_service
        self._llm: Optional[ChatOpenAI] = None

    @property
    def llm(self) -> ChatOpenAI:
        """Get or create LLM instance (lazy initialization).

        Returns:
            ChatOpenAI instance
        """
        if self._llm is None:
            self._llm = self._create_llm()
        return self._llm

    def _create_llm(self) -> ChatOpenAI:
        """Create ChatOpenAI instance.

        Returns:
            Configured ChatOpenAI instance
        """
        self.logger.info(
            "Creating LLM instance",
            action="LOADING",
            model=self.settings.openrouter_model,
        )

        llm = ChatOpenAI(
            model=self.settings.openrouter_model,
            api_key=self.settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=self.settings.llm_temperature,
            model_kwargs={"max_tokens": self.settings.llm_max_tokens},
        )

        self.logger.info(
            "LLM instance created",
            action="SUCCESS",
        )

        return llm

    def _get_prompt_template(
        self,
        filter_level: FilterLevel,
    ) -> ChatPromptTemplate:
        """Get prompt template for given filter level.

        Args:
            filter_level: Content filter level

        Returns:
            Configured prompt template
        """
        system_prompt = PromptTemplates.get_template(filter_level)

        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

    @cached(ttl=3600, key_prefix="query")
    async def process_query(
        self,
        request: QueryRequest,
        filter_level: FilterLevel,
    ) -> QueryResult:
        """Process a user query with RAG.

        This method retrieves relevant documents and generates
        a response using the LLM.

        Args:
            request: Query request with question and metadata
            filter_level: Content filter level for prompts

        Returns:
            Query result with answer and sources

        Raises:
            VectorStoreNotLoadedError: If vector store not loaded
            LLMError: If query processing fails
        """
        if not self.vectorstore_service.is_loaded:
            self.logger.warning(
                "Vector store not loaded",
                action="WARNING",
                user_id=request.user_id,
                guild_id=request.guild_id,
            )
            raise VectorStoreNotLoadedError(
                "⚠️ **Bot ainda não está pronto!**\n\n"
                "O vectorstore não foi carregado. Por favor:\n"
                "1. Adicione arquivos PDF na pasta `data/`\n"
                "2. Execute `python load.py` para indexar os documentos no Supabase\n"
                "3. Reinicie o bot"
            )

        try:
            guild_info = f"Servidor: {request.guild_id}" if request.guild_id else "DM"

            self.logger.info(
                "Processing query",
                action="QUERY",
                query=request.question[:50],
                type=request.query_type,
                guild_id=request.guild_id or "DM",
                user_id=request.user_id,
                filter_level=filter_level.value,
            )

            # Get prompt template
            prompt = self._get_prompt_template(filter_level)

            # Create chains
            question_answer_chain = create_stuff_documents_chain(
                self.llm,
                prompt,
            )

            qa_chain = create_retrieval_chain(
                self.vectorstore_service.retriever,
                question_answer_chain,
            )

            # Execute query
            result = await qa_chain.ainvoke({"input": request.question})

            # Extract results
            answer = result["answer"]
            context_docs = result.get("context", [])

            # Convert to our Document model
            sources = [
                Document(
                    content=doc.page_content,
                    metadata=doc.metadata,
                )
                for doc in context_docs
            ]

            self.logger.info(
                "Query processed successfully",
                action="SUCCESS",
                guild_id=request.guild_id or "DM",
                user_id=request.user_id,
                sources=len(sources),
            )

            return QueryResult(
                answer=answer,
                sources=sources,
                metadata={
                    "filter_level": filter_level.value,
                    "query_type": request.query_type,
                    "guild_id": request.guild_id,
                    "user_id": request.user_id,
                },
            )

        except VectorStoreNotLoadedError:
            raise
        except Exception as e:
            self.logger.error(
                "Query processing failed",
                action="ERROR",
                exc_info=True,
                guild_id=request.guild_id or "DM",
                user_id=request.user_id,
            )
            raise LLMError(
                f"❌ Erro ao processar: {str(e)}",
                model=self.settings.openrouter_model,
                original_error=e,
            ) from e
