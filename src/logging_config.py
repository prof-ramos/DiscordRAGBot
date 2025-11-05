"""Structured logging configuration with contextual information.

This module sets up comprehensive logging with rotation, formatting,
and context tracking for better observability.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional

from src.config import Settings


class ContextFilter(logging.Filter):
    """Add contextual information to log records.

    This filter enriches log records with additional context like
    guild_id, user_id, and query_type for better tracing.
    """

    def __init__(self) -> None:
        super().__init__()
        self.context: dict[str, Any] = {}

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record.

        Args:
            record: Log record to enrich

        Returns:
            True to allow record through
        """
        for key, value in self.context.items():
            setattr(record, key, value)
        return True

    def set_context(self, **kwargs: Any) -> None:
        """Set context variables.

        Args:
            **kwargs: Context key-value pairs
        """
        self.context.update(kwargs)

    def clear_context(self) -> None:
        """Clear all context."""
        self.context.clear()


class BotLogger:
    """Centralized logger with structured output.

    Provides methods for logging with automatic context enrichment
    and emoji-based visual categorization.
    """

    EMOJI_MAP = {
        "DEBUG": "🔍",
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "🚨",
        # Action-specific emojis
        "STARTUP": "🤖",
        "SHUTDOWN": "👋",
        "QUERY": "💬",
        "COMMAND": "🔹",
        "MENTION": "📩",
        "DM": "📨",
        "CONFIG": "📝",
        "SUCCESS": "✅",
        "LOADING": "🔄",
        "CACHE_HIT": "⚡",
        "CACHE_MISS": "💾",
    }

    def __init__(
        self,
        name: str,
        settings: Settings,
        context_filter: Optional[ContextFilter] = None,
    ) -> None:
        """Initialize the logger.

        Args:
            name: Logger name
            settings: Application settings
            context_filter: Optional context filter for enrichment
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(settings.log_level)
        self.context_filter = context_filter or ContextFilter()

        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers(settings)

    def _setup_handlers(self, settings: Settings) -> None:
        """Set up file and console handlers.

        Args:
            settings: Application settings
        """
        # Formatter with context support
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # File handler with rotation
        file_handler = RotatingFileHandler(
            settings.logs_dir / "bot.log",
            maxBytes=settings.log_max_bytes,
            backupCount=settings.log_backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(self.context_filter)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(self.context_filter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _get_emoji(self, level_or_action: str) -> str:
        """Get emoji for log level or action.

        Args:
            level_or_action: Log level or action name

        Returns:
            Corresponding emoji
        """
        return self.EMOJI_MAP.get(level_or_action.upper(), "")

    def _format_message(
        self,
        action: str,
        message: str,
        **context: Any,
    ) -> str:
        """Format log message with emoji and context.

        Args:
            action: Action being performed
            message: Log message
            **context: Additional context

        Returns:
            Formatted message
        """
        emoji = self._get_emoji(action)
        parts = [f"{emoji} {message}" if emoji else message]

        if context:
            context_str = " | ".join(f"{k}={v}" for k, v in context.items())
            parts.append(context_str)

        return " | ".join(parts)

    def debug(
        self,
        message: str,
        action: str = "DEBUG",
        **context: Any,
    ) -> None:
        """Log debug message.

        Args:
            message: Log message
            action: Action category
            **context: Additional context
        """
        self.logger.debug(self._format_message(action, message, **context))

    def info(
        self,
        message: str,
        action: str = "INFO",
        **context: Any,
    ) -> None:
        """Log info message.

        Args:
            message: Log message
            action: Action category
            **context: Additional context
        """
        self.logger.info(self._format_message(action, message, **context))

    def warning(
        self,
        message: str,
        action: str = "WARNING",
        **context: Any,
    ) -> None:
        """Log warning message.

        Args:
            message: Log message
            action: Action category
            **context: Additional context
        """
        self.logger.warning(self._format_message(action, message, **context))

    def error(
        self,
        message: str,
        action: str = "ERROR",
        exc_info: bool = False,
        **context: Any,
    ) -> None:
        """Log error message.

        Args:
            message: Log message
            action: Action category
            exc_info: Include exception traceback
            **context: Additional context
        """
        self.logger.error(
            self._format_message(action, message, **context),
            exc_info=exc_info,
        )

    def critical(
        self,
        message: str,
        action: str = "CRITICAL",
        exc_info: bool = True,
        **context: Any,
    ) -> None:
        """Log critical message.

        Args:
            message: Log message
            action: Action category
            exc_info: Include exception traceback
            **context: Additional context
        """
        self.logger.critical(
            self._format_message(action, message, **context),
            exc_info=exc_info,
        )

    def exception(
        self,
        message: str,
        action: str = "ERROR",
        **context: Any,
    ) -> None:
        """Log exception with traceback.

        Args:
            message: Log message
            action: Action category
            **context: Additional context
        """
        self.logger.exception(self._format_message(action, message, **context))


# Global logger instance
_global_logger: Optional[BotLogger] = None


def get_logger(settings: Optional[Settings] = None) -> BotLogger:
    """Get or create the global logger instance.

    Args:
        settings: Application settings (required for first call)

    Returns:
        Global logger instance
    """
    global _global_logger
    if _global_logger is None:
        if settings is None:
            from src.config import get_settings

            settings = get_settings()
        _global_logger = BotLogger("DiscordRAGBot", settings)
    return _global_logger


def reset_logger() -> None:
    """Reset logger (useful for testing)."""
    global _global_logger
    if _global_logger is not None:
        # Remove all handlers
        for handler in _global_logger.logger.handlers[:]:
            _global_logger.logger.removeHandler(handler)
            handler.close()
    _global_logger = None
