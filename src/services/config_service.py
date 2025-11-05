"""Configuration service for managing server-specific settings."""

import json
from pathlib import Path
from typing import Optional

from src.config import FilterLevel, Settings
from src.logging_config import BotLogger
from src.models import ServerConfig


class ConfigService:
    """Manages server-specific configurations.

    This service handles loading, saving, and querying server
    configurations with proper validation and defaults.

    Attributes:
        settings: Application settings
        logger: Logger instance
    """

    def __init__(self, settings: Settings, logger: BotLogger) -> None:
        """Initialize the configuration service.

        Args:
            settings: Application settings
            logger: Logger instance
        """
        self.settings = settings
        self.logger = logger
        self._configs: dict[str, ServerConfig] = {}
        self._load_configs()

    def _get_guild_key(self, guild_id: Optional[int]) -> str:
        """Convert guild ID to string key.

        Args:
            guild_id: Discord guild ID (None for DMs)

        Returns:
            String key for storage
        """
        return str(guild_id) if guild_id else "dm"

    def _load_configs(self) -> None:
        """Load configurations from file."""
        if not self.settings.config_file.exists():
            self.logger.info(
                "Config file not found, using defaults",
                action="INFO",
            )
            return

        try:
            with open(self.settings.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Convert to ServerConfig objects
            for guild_key, config_data in data.items():
                try:
                    self._configs[guild_key] = ServerConfig(
                        guild_id=guild_key,
                        **config_data,
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Failed to load config for {guild_key}",
                        action="WARNING",
                        error=str(e),
                    )

            self.logger.info(
                "Configurations loaded",
                action="SUCCESS",
                count=len(self._configs),
            )

        except Exception as e:
            self.logger.error(
                "Failed to load configurations",
                action="ERROR",
                exc_info=True,
            )

    def _save_configs(self) -> None:
        """Save configurations to file."""
        try:
            # Convert to dict for JSON serialization
            data = {
                guild_key: config.model_dump(exclude={"guild_id"})
                for guild_key, config in self._configs.items()
            }

            with open(self.settings.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            self.logger.debug(
                "Configurations saved",
                count=len(self._configs),
            )

        except Exception as e:
            self.logger.error(
                "Failed to save configurations",
                action="ERROR",
                exc_info=True,
            )

    def get_filter_level(
        self,
        guild_id: Optional[int],
    ) -> FilterLevel:
        """Get filter level for a guild.

        Args:
            guild_id: Discord guild ID (None for DMs)

        Returns:
            Filter level for the guild
        """
        guild_key = self._get_guild_key(guild_id)

        if guild_key in self._configs:
            level_str = self._configs[guild_key].filter_level
            try:
                return FilterLevel(level_str)
            except ValueError:
                self.logger.warning(
                    f"Invalid filter level for {guild_key}: {level_str}",
                    action="WARNING",
                )

        # Return default
        return self.settings.default_filter_level

    def set_filter_level(
        self,
        guild_id: Optional[int],
        filter_level: FilterLevel,
    ) -> None:
        """Set filter level for a guild.

        Args:
            guild_id: Discord guild ID (None for DMs)
            filter_level: Filter level to set
        """
        guild_key = self._get_guild_key(guild_id)

        # Update or create config
        if guild_key in self._configs:
            self._configs[guild_key].filter_level = filter_level.value
        else:
            self._configs[guild_key] = ServerConfig(
                guild_id=guild_key,
                filter_level=filter_level.value,
            )

        # Save to disk
        self._save_configs()

        self.logger.info(
            "Filter level updated",
            action="CONFIG",
            guild_id=guild_key,
            new_level=filter_level.value,
        )

    def get_config(
        self,
        guild_id: Optional[int],
    ) -> ServerConfig:
        """Get full configuration for a guild.

        Args:
            guild_id: Discord guild ID (None for DMs)

        Returns:
            Server configuration
        """
        guild_key = self._get_guild_key(guild_id)

        if guild_key in self._configs:
            return self._configs[guild_key]

        # Return default config
        return ServerConfig(
            guild_id=guild_key,
            filter_level=self.settings.default_filter_level.value,
        )

    def delete_config(self, guild_id: Optional[int]) -> bool:
        """Delete configuration for a guild.

        Args:
            guild_id: Discord guild ID (None for DMs)

        Returns:
            True if config was deleted
        """
        guild_key = self._get_guild_key(guild_id)

        if guild_key in self._configs:
            del self._configs[guild_key]
            self._save_configs()

            self.logger.info(
                "Configuration deleted",
                action="CONFIG",
                guild_id=guild_key,
            )
            return True

        return False

    def get_all_configs(self) -> dict[str, ServerConfig]:
        """Get all server configurations.

        Returns:
            Dictionary mapping guild keys to configs
        """
        return self._configs.copy()
