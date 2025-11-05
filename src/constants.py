"""Constants and enumerations for the Discord RAG Bot.

This module centralizes all constants, magic values, and enumerations
used throughout the application to improve maintainability and type safety.
"""

from enum import Enum
from typing import Final

# ============================================================================
# Application Metadata
# ============================================================================

APP_NAME: Final[str] = "Discord RAG Bot"
APP_VERSION: Final[str] = "2.0.0"
APP_DESCRIPTION: Final[str] = "Production-ready Discord bot with RAG capabilities"
APP_AUTHOR: Final[str] = "Professor Ramos"

# ============================================================================
# Discord Limits
# ============================================================================

DISCORD_MAX_MESSAGE_LENGTH: Final[int] = 2000
DISCORD_MAX_EMBED_TITLE_LENGTH: Final[int] = 256
DISCORD_MAX_EMBED_DESCRIPTION_LENGTH: Final[int] = 4096
DISCORD_MAX_EMBED_FIELDS: Final[int] = 25
DISCORD_MAX_EMBED_FIELD_NAME_LENGTH: Final[int] = 256
DISCORD_MAX_EMBED_FIELD_VALUE_LENGTH: Final[int] = 1024
DISCORD_MAX_EMBEDS_PER_MESSAGE: Final[int] = 10

# ============================================================================
# RAG Configuration Defaults
# ============================================================================

DEFAULT_CHUNK_SIZE: Final[int] = 1000
DEFAULT_CHUNK_OVERLAP: Final[int] = 200
DEFAULT_K_DOCUMENTS: Final[int] = 5
DEFAULT_LLM_TEMPERATURE: Final[float] = 0.7
DEFAULT_MAX_TOKENS: Final[int] = 1000

# ============================================================================
# Embedding Configuration
# ============================================================================

EMBEDDING_MODEL: Final[str] = "text-embedding-3-small"
EMBEDDING_DIMENSION: Final[int] = 1536  # OpenAI text-embedding-3-small

# ============================================================================
# Cache Configuration
# ============================================================================

DEFAULT_CACHE_TTL: Final[int] = 3600  # 1 hour in seconds
DEFAULT_CACHE_MAX_SIZE: Final[int] = 1000
CACHE_KEY_PREFIX: Final[str] = "rag:cache:"

# ============================================================================
# Rate Limiting
# ============================================================================

DEFAULT_RATE_LIMIT_REQUESTS: Final[int] = 10
DEFAULT_RATE_LIMIT_WINDOW: Final[int] = 60  # 1 minute in seconds
RATE_LIMIT_KEY_PREFIX: Final[str] = "rag:ratelimit:"

# ============================================================================
# Logging
# ============================================================================

LOG_FORMAT: Final[str] = (
    "%(asctime)s | %(levelname)-8s | %(message)s"
)
LOG_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_LEVEL: Final[str] = "INFO"
DEFAULT_LOG_MAX_BYTES: Final[int] = 5 * 1024 * 1024  # 5MB
DEFAULT_LOG_BACKUP_COUNT: Final[int] = 5

# ============================================================================
# Database Table Names
# ============================================================================

TABLE_DOCUMENTS: Final[str] = "documents"
TABLE_SERVER_CONFIGS: Final[str] = "server_configs"
TABLE_QUERY_HISTORY: Final[str] = "query_history"
TABLE_QUERY_CACHE: Final[str] = "query_cache"
TABLE_RATE_LIMITS: Final[str] = "rate_limits"
TABLE_USER_PROFILES: Final[str] = "user_profiles"
TABLE_FEEDBACK: Final[str] = "feedback"
TABLE_AUDIT_LOGS: Final[str] = "audit_logs"
TABLE_DOCUMENT_SOURCES: Final[str] = "document_sources"
TABLE_PROCESSING_LOG: Final[str] = "document_processing_log"

# ============================================================================
# Database Function Names
# ============================================================================

FUNCTION_MATCH_DOCUMENTS: Final[str] = "match_documents"
FUNCTION_CLEAN_CACHE: Final[str] = "clean_expired_cache"
FUNCTION_RESET_RATE_LIMIT: Final[str] = "reset_rate_limit_if_expired"
FUNCTION_UPDATE_USER_PROFILE: Final[str] = "update_user_profile"
FUNCTION_IS_DOCUMENT_PROCESSED: Final[str] = "is_document_processed"
FUNCTION_GET_KB_STATS: Final[str] = "get_knowledge_base_stats"

# ============================================================================
# File Types
# ============================================================================

SUPPORTED_DOCUMENT_TYPES: Final[set[str]] = {
    ".pdf",
    ".txt",
    ".md",
    ".rst",
}

PDF_FILE_EXTENSION: Final[str] = ".pdf"
TEXT_FILE_EXTENSION: Final[str] = ".txt"
MARKDOWN_FILE_EXTENSION: Final[str] = ".md"

# ============================================================================
# Hash Algorithm
# ============================================================================

HASH_ALGORITHM: Final[str] = "sha256"
HASH_CHUNK_SIZE: Final[int] = 4096  # Bytes to read at once when hashing

# ============================================================================
# Error Messages
# ============================================================================

ERROR_NO_DOCUMENTS: Final[str] = "No PDF files found in the data directory"
ERROR_VECTORSTORE_NOT_LOADED: Final[str] = "Vector store must be loaded before use"
ERROR_INVALID_FILTER_LEVEL: Final[str] = "Invalid filter level"
ERROR_RATE_LIMIT_EXCEEDED: Final[str] = "Rate limit exceeded. Please try again later"
ERROR_CACHE_MISS: Final[str] = "Cache miss"
ERROR_DATABASE_CONNECTION: Final[str] = "Failed to connect to database"
ERROR_DOCUMENT_PROCESSING: Final[str] = "Failed to process document"

# ============================================================================
# Success Messages
# ============================================================================

SUCCESS_VECTORSTORE_LOADED: Final[str] = "Vector store loaded successfully"
SUCCESS_DOCUMENT_PROCESSED: Final[str] = "Document processed successfully"
SUCCESS_CACHE_HIT: Final[str] = "Cache hit"
SUCCESS_CONFIG_UPDATED: Final[str] = "Configuration updated successfully"

# ============================================================================
# Enumerations
# ============================================================================


class FilterLevel(str, Enum):
    """Content filter levels for bot responses."""

    CONSERVATIVE = "conservador"
    MODERATE = "moderado"
    LIBERAL = "liberal"

    def __str__(self) -> str:
        """Return the enum value as string."""
        return self.value


class QueryType(str, Enum):
    """Types of queries the bot can handle."""

    RAG = "RAG"  # Regular RAG query
    DM = "DM"  # Direct message
    MENTION = "Mention"  # Bot mention
    SLASH = "Slash"  # Slash command

    def __str__(self) -> str:
        """Return the enum value as string."""
        return self.value


class ProcessingStatus(str, Enum):
    """Document processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    OUTDATED = "outdated"

    def __str__(self) -> str:
        """Return the enum value as string."""
        return self.value


class LogAction(str, Enum):
    """Log action types for structured logging."""

    STARTUP = "STARTUP"
    SHUTDOWN = "SHUTDOWN"
    LOADING = "LOADING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    CONFIG = "CONFIG"
    MENTION = "MENTION"
    DM = "DM"
    COMMAND = "COMMAND"

    def __str__(self) -> str:
        """Return the enum value as string."""
        return self.value


class SourceType(str, Enum):
    """Types of document sources."""

    PDF = "pdf"
    TXT = "txt"
    MARKDOWN = "md"
    HTML = "html"
    DOCX = "docx"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        """Return the enum value as string."""
        return self.value

    @classmethod
    def from_extension(cls, extension: str) -> "SourceType":
        """Get source type from file extension.

        Args:
            extension: File extension (with or without dot)

        Returns:
            Corresponding SourceType enum

        Example:
            >>> SourceType.from_extension(".pdf")
            SourceType.PDF
            >>> SourceType.from_extension("txt")
            SourceType.TXT
        """
        # Remove leading dot if present
        ext = extension.lstrip(".").lower()

        mapping = {
            "pdf": cls.PDF,
            "txt": cls.TXT,
            "md": cls.MARKDOWN,
            "markdown": cls.MARKDOWN,
            "html": cls.HTML,
            "htm": cls.HTML,
            "docx": cls.DOCX,
            "doc": cls.DOCX,
        }

        return mapping.get(ext, cls.UNKNOWN)


class CacheStatus(str, Enum):
    """Cache operation status."""

    HIT = "hit"
    MISS = "miss"
    EXPIRED = "expired"
    INVALID = "invalid"

    def __str__(self) -> str:
        """Return the enum value as string."""
        return self.value


class DatabaseOperation(str, Enum):
    """Database operation types for audit logging."""

    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    SELECT = "SELECT"

    def __str__(self) -> str:
        """Return the enum value as string."""
        return self.value


# ============================================================================
# Time Constants
# ============================================================================

SECONDS_PER_MINUTE: Final[int] = 60
SECONDS_PER_HOUR: Final[int] = 3600
SECONDS_PER_DAY: Final[int] = 86400
MILLISECONDS_PER_SECOND: Final[int] = 1000

# ============================================================================
# Retry Configuration
# ============================================================================

DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_RETRY_DELAY: Final[float] = 1.0  # seconds
DEFAULT_BACKOFF_FACTOR: Final[float] = 2.0  # exponential backoff

# ============================================================================
# HTTP Configuration
# ============================================================================

DEFAULT_TIMEOUT: Final[int] = 30  # seconds
DEFAULT_MAX_CONNECTIONS: Final[int] = 100
DEFAULT_MAX_KEEPALIVE_CONNECTIONS: Final[int] = 20

# ============================================================================
# Development/Production Flags
# ============================================================================

DEBUG_MODE_ENV_VAR: Final[str] = "DEBUG"
ENVIRONMENT_ENV_VAR: Final[str] = "ENVIRONMENT"

# ============================================================================
# Validation Limits
# ============================================================================

MIN_CHUNK_SIZE: Final[int] = 100
MAX_CHUNK_SIZE: Final[int] = 8000
MIN_CHUNK_OVERLAP: Final[int] = 0
MAX_CHUNK_OVERLAP: Final[int] = 1000
MIN_K_DOCUMENTS: Final[int] = 1
MAX_K_DOCUMENTS: Final[int] = 20
MIN_TEMPERATURE: Final[float] = 0.0
MAX_TEMPERATURE: Final[float] = 2.0
MIN_MAX_TOKENS: Final[int] = 100
MAX_MAX_TOKENS: Final[int] = 8000

# ============================================================================
# Unicode Symbols
# ============================================================================

SYMBOL_CHECK: Final[str] = "✅"
SYMBOL_CROSS: Final[str] = "❌"
SYMBOL_WARNING: Final[str] = "⚠️"
SYMBOL_INFO: Final[str] = "ℹ️"
SYMBOL_LOADING: Final[str] = "⏳"
SYMBOL_SUCCESS: Final[str] = "🎉"
SYMBOL_ERROR: Final[str] = "🔥"
SYMBOL_QUESTION: Final[str] = "❓"
SYMBOL_ROBOT: Final[str] = "🤖"
SYMBOL_BOOK: Final[str] = "📚"
SYMBOL_CHART: Final[str] = "📊"
SYMBOL_LOCK: Final[str] = "🔒"
SYMBOL_KEY: Final[str] = "🔑"
