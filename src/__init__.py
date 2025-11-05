"""Discord RAG Bot - A production-ready RAG chatbot for Discord."""

__version__ = "2.0.0"
__author__ = "Discord RAG Bot Contributors"

from src.config import Settings
from src.exceptions import (
    BotError,
    ConfigurationError,
    VectorStoreError,
    LLMError,
)

__all__ = [
    "Settings",
    "BotError",
    "ConfigurationError",
    "VectorStoreError",
    "LLMError",
]
