"""Tests for ConfigService."""

import pytest
from pathlib import Path

from src.config import FilterLevel, Settings
from src.logging_config import BotLogger
from src.models import ServerConfig
from src.services.config_service import ConfigService


class TestConfigService:
    """Test suite for ConfigService."""

    @pytest.fixture
    def config_service(
        self,
        test_settings: Settings,
        test_logger: BotLogger,
        tmp_path: Path,
    ) -> ConfigService:
        """Create config service for testing.

        Args:
            test_settings: Test settings
            test_logger: Test logger
            tmp_path: Temporary directory

        Returns:
            ConfigService instance
        """
        # Use temp file for config
        test_settings.config_file = tmp_path / "test_config.json"
        return ConfigService(test_settings, test_logger)

    def test_get_default_filter_level(
        self,
        config_service: ConfigService,
    ) -> None:
        """Test getting default filter level."""
        level = config_service.get_filter_level(None)
        assert level == FilterLevel.MODERATE

    def test_set_filter_level(
        self,
        config_service: ConfigService,
    ) -> None:
        """Test setting filter level."""
        guild_id = 123456789
        config_service.set_filter_level(guild_id, FilterLevel.LIBERAL)

        # Verify it was saved
        level = config_service.get_filter_level(guild_id)
        assert level == FilterLevel.LIBERAL

    def test_get_config(
        self,
        config_service: ConfigService,
    ) -> None:
        """Test getting full configuration."""
        guild_id = 123456789
        config_service.set_filter_level(guild_id, FilterLevel.CONSERVATIVE)

        config = config_service.get_config(guild_id)
        assert isinstance(config, ServerConfig)
        assert config.filter_level == FilterLevel.CONSERVATIVE.value

    def test_delete_config(
        self,
        config_service: ConfigService,
    ) -> None:
        """Test deleting configuration."""
        guild_id = 123456789
        config_service.set_filter_level(guild_id, FilterLevel.LIBERAL)

        # Verify it exists
        assert config_service.delete_config(guild_id) is True

        # Should return default now
        level = config_service.get_filter_level(guild_id)
        assert level == FilterLevel.MODERATE

    def test_dm_config(
        self,
        config_service: ConfigService,
    ) -> None:
        """Test DM-specific configuration."""
        config_service.set_filter_level(None, FilterLevel.LIBERAL)

        level = config_service.get_filter_level(None)
        assert level == FilterLevel.LIBERAL

    def test_persistence(
        self,
        test_settings: Settings,
        test_logger: BotLogger,
        tmp_path: Path,
    ) -> None:
        """Test configuration persistence across instances."""
        test_settings.config_file = tmp_path / "test_config.json"

        # Create first instance and save config
        service1 = ConfigService(test_settings, test_logger)
        service1.set_filter_level(12345, FilterLevel.CONSERVATIVE)

        # Create new instance (should load from file)
        service2 = ConfigService(test_settings, test_logger)
        level = service2.get_filter_level(12345)

        assert level == FilterLevel.CONSERVATIVE
