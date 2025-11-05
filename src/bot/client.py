"""Discord bot client with dependency injection."""

from typing import Optional

import discord
from discord.ext import commands

from src.config import Settings, get_settings
from src.exceptions import BotError
from src.logging_config import BotLogger, get_logger
from src.services import (
    ConfigService,
    LLMService,
    SupabaseService,
    VectorStoreService,
)


class DiscordRAGBot(commands.Bot):
    """Discord bot with RAG capabilities.

    This bot uses dependency injection for services and provides
    async context manager support for proper resource management.

    Attributes:
        settings: Application settings
        logger: Logger instance
        supabase_service: Supabase service
        vectorstore_service: Vector store service
        llm_service: LLM service
        config_service: Configuration service
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        logger: Optional[BotLogger] = None,
    ) -> None:
        """Initialize the bot.

        Args:
            settings: Application settings (creates default if None)
            logger: Logger instance (creates default if None)
        """
        # Initialize settings and logger
        self.settings = settings or get_settings()
        self.logger = logger or get_logger(self.settings)

        # Configure intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.dm_messages = True

        # Initialize bot
        super().__init__(
            command_prefix="!",
            intents=intents,
        )

        # Initialize services (dependency injection)
        self.supabase_service = SupabaseService(
            settings=self.settings,
            logger=self.logger,
        )

        self.vectorstore_service = VectorStoreService(
            settings=self.settings,
            logger=self.logger,
            supabase_service=self.supabase_service,
        )

        self.llm_service = LLMService(
            settings=self.settings,
            logger=self.logger,
            vectorstore_service=self.vectorstore_service,
        )

        self.config_service = ConfigService(
            settings=self.settings,
            logger=self.logger,
        )

        self._initialized = False

    async def setup_hook(self) -> None:
        """Bot setup hook - called when bot is starting.

        This is the proper place to initialize async resources.
        """
        try:
            self.logger.info(
                "Setting up bot...",
                action="LOADING",
            )

            # Load vector store
            await self._initialize_vectorstore()

            # Sync commands
            await self._sync_commands()

            self._initialized = True

            self.logger.info(
                "Bot setup complete",
                action="SUCCESS",
            )

        except Exception as e:
            self.logger.error(
                "Bot setup failed",
                action="ERROR",
                exc_info=True,
            )
            # Don't raise - allow bot to start but with limited functionality

    async def _initialize_vectorstore(self) -> None:
        """Initialize vector store connection."""
        try:
            self.logger.info(
                "Initializing RAG...",
                action="LOADING",
            )

            await self.vectorstore_service.load()

            self.logger.info(
                "RAG initialized",
                action="SUCCESS",
                model=self.settings.openrouter_model,
                k_docs=self.settings.k_documents,
            )

        except Exception as e:
            self.logger.error(
                "Failed to initialize RAG",
                action="ERROR",
                exc_info=True,
            )
            self.logger.warning(
                "Bot will start but cannot answer questions until RAG is loaded",
                action="WARNING",
            )

    async def _sync_commands(self) -> None:
        """Sync slash commands with Discord."""
        try:
            synced = await self.tree.sync()
            self.logger.info(
                "Commands synced",
                action="SUCCESS",
                count=len(synced),
            )
        except Exception as e:
            self.logger.error(
                "Failed to sync commands",
                action="ERROR",
                exc_info=True,
            )

    async def on_ready(self) -> None:
        """Called when bot is ready."""
        self.logger.info(
            "Bot connected",
            action="STARTUP",
            name=str(self.user),
            guilds=len(self.guilds),
        )

    async def on_error(self, event: str, *args, **kwargs) -> None:
        """Global error handler.

        Args:
            event: Event name that caused the error
            *args: Event arguments
            **kwargs: Event keyword arguments
        """
        self.logger.exception(
            f"Error in event {event}",
            action="ERROR",
        )

    async def close(self) -> None:
        """Close bot and cleanup resources."""
        self.logger.info(
            "Shutting down bot...",
            action="SHUTDOWN",
        )

        await super().close()

        self.logger.info(
            "Bot shutdown complete",
            action="SHUTDOWN",
        )

    def run_bot(self) -> None:
        """Run the bot with the configured token.

        This is a convenience method that handles token retrieval.
        """
        try:
            self.run(self.settings.discord_token)
        except Exception as e:
            self.logger.critical(
                "Failed to start bot",
                action="CRITICAL",
                exc_info=True,
            )
            raise BotError(
                "Failed to start bot",
                original_error=e,
            ) from e
