"""Supabase client management service with connection pooling."""

from typing import Optional

from supabase import Client, create_client

from src.config import Settings
from src.exceptions import SupabaseError
from src.logging_config import BotLogger


class SupabaseService:
    """Manages Supabase client lifecycle and operations.

    This service provides a centralized way to interact with Supabase,
    with proper error handling and logging.

    Attributes:
        settings: Application settings
        logger: Logger instance
    """

    def __init__(self, settings: Settings, logger: BotLogger) -> None:
        """Initialize the Supabase service.

        Args:
            settings: Application settings
            logger: Logger instance
        """
        self.settings = settings
        self.logger = logger
        self._client: Optional[Client] = None

    @property
    def client(self) -> Client:
        """Get or create Supabase client (lazy initialization).

        Returns:
            Supabase client instance

        Raises:
            SupabaseError: If client creation fails
        """
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self) -> Client:
        """Create a new Supabase client.

        Returns:
            Configured Supabase client

        Raises:
            SupabaseError: If client creation fails
        """
        try:
            self.logger.info(
                "Creating Supabase client",
                action="LOADING",
                url=self.settings.supabase_url,
            )

            client = create_client(
                self.settings.supabase_url,
                self.settings.supabase_api_key,
            )

            self.logger.info(
                "Supabase client created successfully",
                action="SUCCESS",
            )

            return client

        except Exception as e:
            self.logger.error(
                "Failed to create Supabase client",
                action="ERROR",
                exc_info=True,
            )
            raise SupabaseError(
                "Failed to create Supabase client",
                operation="create_client",
                original_error=e,
            ) from e

    def test_connection(self) -> bool:
        """Test Supabase connection.

        Returns:
            True if connection is successful

        Raises:
            SupabaseError: If connection test fails
        """
        try:
            # Try a simple query to test connection
            self.client.table(self.settings.supabase_table_name).select(
                "count"
            ).limit(1).execute()

            self.logger.info(
                "Supabase connection test successful",
                action="SUCCESS",
            )
            return True

        except Exception as e:
            self.logger.error(
                "Supabase connection test failed",
                action="ERROR",
                exc_info=True,
            )
            raise SupabaseError(
                "Connection test failed",
                operation="test_connection",
                original_error=e,
            ) from e

    def reset(self) -> None:
        """Reset the client (useful for reconnection)."""
        self._client = None
        self.logger.info("Supabase client reset", action="INFO")
