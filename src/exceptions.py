"""Custom exception hierarchy for the Discord RAG Bot.

This module defines a comprehensive exception hierarchy that provides
fine-grained error handling throughout the application.
"""

from typing import Any, Optional


class BotError(Exception):
    """Base exception for all bot-related errors.

    Attributes:
        message: Human-readable error message
        details: Optional dictionary with additional error context
        original_error: The original exception if this wraps another exception
    """

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ) -> None:
        self.message = message
        self.details = details or {}
        self.original_error = original_error
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return formatted error message with details."""
        base = self.message
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            base = f"{base} ({details_str})"
        if self.original_error:
            base = f"{base} | Caused by: {self.original_error}"
        return base


class ConfigurationError(BotError):
    """Raised when configuration is invalid or missing."""

    def __init__(
        self,
        message: str = "Configuration error",
        missing_keys: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if missing_keys:
            details["missing_keys"] = missing_keys
        super().__init__(message, details=details, **kwargs)


class VectorStoreError(BotError):
    """Raised when vectorstore operations fail."""

    def __init__(
        self,
        message: str = "Vector store operation failed",
        operation: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if operation:
            details["operation"] = operation
        super().__init__(message, details=details, **kwargs)


class VectorStoreNotLoadedError(VectorStoreError):
    """Raised when attempting to use an unloaded vectorstore."""

    def __init__(self, message: str = "Vector store not loaded", **kwargs: Any) -> None:
        super().__init__(message, operation="access", **kwargs)


class LLMError(BotError):
    """Raised when LLM operations fail."""

    def __init__(
        self,
        message: str = "LLM operation failed",
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if model:
            details["model"] = model
        super().__init__(message, details=details, **kwargs)


class SupabaseError(BotError):
    """Raised when Supabase operations fail."""

    def __init__(
        self,
        message: str = "Supabase operation failed",
        operation: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if operation:
            details["operation"] = operation
        super().__init__(message, details=details, **kwargs)


class DocumentLoadError(BotError):
    """Raised when document loading fails."""

    def __init__(
        self,
        message: str = "Document loading failed",
        file_path: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if file_path:
            details["file_path"] = file_path
        super().__init__(message, details=details, **kwargs)


class PermissionError(BotError):
    """Raised when user lacks required permissions."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_permission: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if required_permission:
            details["required_permission"] = required_permission
        super().__init__(message, details=details, **kwargs)


class RateLimitError(BotError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, details=details, **kwargs)
