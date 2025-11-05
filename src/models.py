"""Data models for the Discord RAG Bot.

This module defines Pydantic models for data validation and serialization.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class Document(BaseModel):
    """Represents a document chunk with metadata."""

    content: str = Field(..., description="Document content")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Document metadata",
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, content: str) -> str:
        """Ensure content is not empty."""
        if not content.strip():
            raise ValueError("Document content cannot be empty")
        return content


class QueryResult(BaseModel):
    """Result from a RAG query."""

    answer: str = Field(..., description="Generated answer")
    sources: list[Document] = Field(
        default_factory=list,
        description="Source documents used",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )

    @property
    def source_count(self) -> int:
        """Number of source documents."""
        return len(self.sources)

    def get_source_names(self, max_sources: int = 3) -> list[str]:
        """Get list of source file names."""
        sources = []
        for doc in self.sources[:max_sources]:
            source = doc.metadata.get("source", "N/A")
            if source not in sources:
                sources.append(source)
        return sources


class ServerConfig(BaseModel):
    """Configuration for a specific Discord server."""

    guild_id: str = Field(..., description="Discord guild ID")
    filter_level: str = Field(
        default="moderado",
        description="Content filter level",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When config was created",
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="When config was last updated",
    )

    @field_validator("filter_level")
    @classmethod
    def validate_filter_level(cls, level: str) -> str:
        """Ensure filter level is valid."""
        valid_levels = {"conservador", "moderado", "liberal"}
        if level not in valid_levels:
            raise ValueError(
                f"Invalid filter level: {level}. Must be one of {valid_levels}"
            )
        return level


class QueryRequest(BaseModel):
    """Request to process a user query."""

    question: str = Field(..., min_length=1, description="User question")
    guild_id: Optional[str] = Field(
        default=None,
        description="Discord guild ID (None for DM)",
    )
    user_id: str = Field(..., description="Discord user ID")
    query_type: str = Field(
        default="RAG",
        description="Type of query (RAG, DM, etc.)",
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, question: str) -> str:
        """Ensure question is not empty after stripping."""
        if not question.strip():
            raise ValueError("Question cannot be empty")
        return question.strip()


class CacheEntry(BaseModel):
    """Cached query result with expiration."""

    key: str = Field(..., description="Cache key")
    result: QueryResult = Field(..., description="Cached result")
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When cached",
    )
    ttl: int = Field(
        default=3600,
        ge=60,
        description="Time to live in seconds",
    )

    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl


class RateLimitInfo(BaseModel):
    """Rate limit tracking information."""

    user_id: str = Field(..., description="User identifier")
    request_count: int = Field(default=0, ge=0, description="Request count")
    window_start: datetime = Field(
        default_factory=datetime.now,
        description="Start of current window",
    )
    window_duration: int = Field(
        default=60,
        ge=1,
        description="Window duration in seconds",
    )

    def is_window_expired(self) -> bool:
        """Check if current window has expired."""
        age = (datetime.now() - self.window_start).total_seconds()
        return age > self.window_duration

    def reset_window(self) -> None:
        """Reset the rate limit window."""
        self.request_count = 0
        self.window_start = datetime.now()

    def increment(self) -> None:
        """Increment request count."""
        if self.is_window_expired():
            self.reset_window()
        self.request_count += 1

    def is_limited(self, max_requests: int) -> bool:
        """Check if rate limit is exceeded."""
        if self.is_window_expired():
            self.reset_window()
        return self.request_count >= max_requests
