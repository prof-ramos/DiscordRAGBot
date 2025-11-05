"""Tests for data models."""

import pytest
from pydantic import ValidationError

from src.models import (
    Document,
    QueryRequest,
    QueryResult,
    ServerConfig,
    RateLimitInfo,
)


class TestDocument:
    """Test suite for Document model."""

    def test_valid_document(self) -> None:
        """Test creating a valid document."""
        doc = Document(
            content="Test content",
            metadata={"source": "test.pdf", "page": 1},
        )

        assert doc.content == "Test content"
        assert doc.metadata["source"] == "test.pdf"

    def test_empty_content_validation(self) -> None:
        """Test validation fails for empty content."""
        with pytest.raises(ValidationError):
            Document(content="   ", metadata={})


class TestQueryRequest:
    """Test suite for QueryRequest model."""

    def test_valid_request(self) -> None:
        """Test creating a valid query request."""
        request = QueryRequest(
            question="What is Python?",
            guild_id="12345",
            user_id="67890",
            query_type="RAG",
        )

        assert request.question == "What is Python?"
        assert request.guild_id == "12345"

    def test_question_stripping(self) -> None:
        """Test question is stripped of whitespace."""
        request = QueryRequest(
            question="  What is Python?  ",
            user_id="67890",
        )

        assert request.question == "What is Python?"

    def test_empty_question_validation(self) -> None:
        """Test validation fails for empty question."""
        with pytest.raises(ValidationError):
            QueryRequest(
                question="   ",
                user_id="67890",
            )


class TestQueryResult:
    """Test suite for QueryResult model."""

    def test_query_result(self) -> None:
        """Test creating a query result."""
        sources = [
            Document(content="Source 1", metadata={"source": "file1.pdf"}),
            Document(content="Source 2", metadata={"source": "file2.pdf"}),
        ]

        result = QueryResult(
            answer="Test answer",
            sources=sources,
        )

        assert result.answer == "Test answer"
        assert result.source_count == 2

    def test_get_source_names(self) -> None:
        """Test extracting source names."""
        sources = [
            Document(content="Source 1", metadata={"source": "file1.pdf"}),
            Document(content="Source 2", metadata={"source": "file2.pdf"}),
            Document(content="Source 3", metadata={"source": "file3.pdf"}),
            Document(content="Source 4", metadata={"source": "file4.pdf"}),
        ]

        result = QueryResult(answer="Test", sources=sources)

        # Should return only max_sources (default 3)
        names = result.get_source_names()
        assert len(names) == 3
        assert "file1.pdf" in names


class TestServerConfig:
    """Test suite for ServerConfig model."""

    def test_valid_config(self) -> None:
        """Test creating a valid server config."""
        config = ServerConfig(
            guild_id="12345",
            filter_level="moderado",
        )

        assert config.guild_id == "12345"
        assert config.filter_level == "moderado"

    def test_invalid_filter_level(self) -> None:
        """Test validation fails for invalid filter level."""
        with pytest.raises(ValidationError):
            ServerConfig(
                guild_id="12345",
                filter_level="invalid",
            )


class TestRateLimitInfo:
    """Test suite for RateLimitInfo model."""

    def test_rate_limit_creation(self) -> None:
        """Test creating rate limit info."""
        info = RateLimitInfo(
            user_id="12345",
            window_duration=60,
        )

        assert info.user_id == "12345"
        assert info.request_count == 0

    def test_increment(self) -> None:
        """Test incrementing request count."""
        info = RateLimitInfo(user_id="12345")

        info.increment()
        assert info.request_count == 1

        info.increment()
        assert info.request_count == 2

    def test_is_limited(self) -> None:
        """Test rate limit checking."""
        info = RateLimitInfo(user_id="12345")

        # Not limited initially
        assert info.is_limited(max_requests=5) is False

        # Increment to limit
        for _ in range(5):
            info.increment()

        # Should be limited now
        assert info.is_limited(max_requests=5) is True

    def test_window_expiration(self) -> None:
        """Test window expiration and reset."""
        from datetime import datetime, timedelta

        info = RateLimitInfo(
            user_id="12345",
            window_duration=60,
        )

        # Increment some requests
        info.increment()
        info.increment()

        # Simulate expired window
        info.window_start = datetime.now() - timedelta(seconds=120)

        # Should reset on next check
        assert info.is_window_expired() is True

        info.increment()
        assert info.request_count == 1  # Reset to 1 after expiration
