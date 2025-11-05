"""Tests for caching functionality."""

import pytest
from datetime import datetime, timedelta

from src.cache import AsyncLRUCache, get_cache
from src.models import CacheEntry, QueryResult, Document


class TestAsyncLRUCache:
    """Test suite for AsyncLRUCache."""

    @pytest.fixture
    def cache(self) -> AsyncLRUCache:
        """Create cache for testing.

        Returns:
            AsyncLRUCache instance
        """
        return AsyncLRUCache(max_size=3, default_ttl=60)

    @pytest.fixture
    def sample_result(self) -> QueryResult:
        """Create sample query result.

        Returns:
            Sample QueryResult
        """
        return QueryResult(
            answer="Test answer",
            sources=[
                Document(
                    content="Test content",
                    metadata={"source": "test.pdf"},
                )
            ],
        )

    def test_cache_set_and_get(
        self,
        cache: AsyncLRUCache,
        sample_result: QueryResult,
    ) -> None:
        """Test basic cache set and get."""
        cache.set("test_key", sample_result)
        result = cache.get("test_key")

        assert result is not None
        assert result.answer == "Test answer"

    def test_cache_miss(self, cache: AsyncLRUCache) -> None:
        """Test cache miss."""
        result = cache.get("nonexistent_key")
        assert result is None

    def test_cache_expiration(
        self,
        cache: AsyncLRUCache,
        sample_result: QueryResult,
    ) -> None:
        """Test cache entry expiration."""
        # Set with very short TTL
        cache.set("test_key", sample_result, ttl=0)

        # Should be expired immediately
        result = cache.get("test_key")
        assert result is None

    def test_lru_eviction(
        self,
        cache: AsyncLRUCache,
        sample_result: QueryResult,
    ) -> None:
        """Test LRU eviction when max size exceeded."""
        # Fill cache to max
        cache.set("key1", sample_result)
        cache.set("key2", sample_result)
        cache.set("key3", sample_result)

        # Add one more (should evict oldest)
        cache.set("key4", sample_result)

        # key1 should be evicted
        assert cache.get("key1") is None
        assert cache.get("key4") is not None

    def test_cache_stats(
        self,
        cache: AsyncLRUCache,
        sample_result: QueryResult,
    ) -> None:
        """Test cache statistics."""
        cache.set("key1", sample_result)

        # Hit
        cache.get("key1")

        # Miss
        cache.get("key2")

        stats = cache.stats
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1

    def test_cache_clear(
        self,
        cache: AsyncLRUCache,
        sample_result: QueryResult,
    ) -> None:
        """Test cache clear."""
        cache.set("key1", sample_result)
        cache.set("key2", sample_result)

        cache.clear()

        assert cache.size == 0
        assert cache.get("key1") is None

    def test_cache_invalidate(
        self,
        cache: AsyncLRUCache,
        sample_result: QueryResult,
    ) -> None:
        """Test cache invalidation."""
        cache.set("key1", sample_result)

        assert cache.invalidate("key1") is True
        assert cache.get("key1") is None

        # Invalidating non-existent key
        assert cache.invalidate("nonexistent") is False


class TestCacheEntry:
    """Test suite for CacheEntry model."""

    def test_cache_entry_creation(self) -> None:
        """Test creating a cache entry."""
        result = QueryResult(answer="Test", sources=[])

        entry = CacheEntry(
            key="test_key",
            result=result,
            ttl=3600,
        )

        assert entry.key == "test_key"
        assert entry.result.answer == "Test"
        assert entry.is_expired is False

    def test_cache_entry_expiration(self) -> None:
        """Test cache entry expiration logic."""
        result = QueryResult(answer="Test", sources=[])

        # Create expired entry (simulated)
        entry = CacheEntry(
            key="test_key",
            result=result,
            ttl=1,
        )

        # Manually set old creation time
        entry.created_at = datetime.now() - timedelta(seconds=10)

        assert entry.is_expired is True
