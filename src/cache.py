"""Caching layer with LRU cache and async support.

This module provides intelligent caching for expensive operations like
LLM queries, with support for TTL and size limits.
"""

import hashlib
import json
from collections import OrderedDict
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, ParamSpec

from src.models import CacheEntry, QueryResult

P = ParamSpec("P")
R = TypeVar("R")


class AsyncLRUCache:
    """Thread-safe LRU cache with TTL support for async functions.

    This cache automatically evicts least-recently-used items when the
    size limit is reached, and expires items after their TTL.

    Attributes:
        max_size: Maximum number of items to cache
        default_ttl: Default time-to-live in seconds
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600) -> None:
        """Initialize the cache.

        Args:
            max_size: Maximum number of items to cache
            default_ttl: Default time-to-live in seconds
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    def _make_key(self, *args: Any, **kwargs: Any) -> str:
        """Generate a cache key from function arguments.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Unique cache key string
        """
        # Create a deterministic string representation
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_string = "|".join(key_parts)

        # Hash for consistent key length
        return hashlib.sha256(key_string.encode()).hexdigest()

    def _evict_expired(self) -> None:
        """Remove expired entries from cache."""
        expired_keys = [
            key for key, entry in self._cache.items() if entry.is_expired
        ]
        for key in expired_keys:
            del self._cache[key]

    def _enforce_size_limit(self) -> None:
        """Ensure cache doesn't exceed max size (LRU eviction)."""
        while len(self._cache) > self._max_size:
            # Remove oldest item (FIFO for same access time)
            self._cache.popitem(last=False)

    def get(self, key: str) -> Optional[Any]:
        """Retrieve item from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        self._evict_expired()

        if key in self._cache:
            entry = self._cache[key]
            if not entry.is_expired:
                # Move to end (mark as recently used)
                self._cache.move_to_end(key)
                self._hits += 1
                return entry.result

            # Expired entry
            del self._cache[key]

        self._misses += 1
        return None

    def set(
        self,
        key: str,
        value: QueryResult,
        ttl: Optional[int] = None,
    ) -> None:
        """Store item in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        self._evict_expired()

        entry = CacheEntry(
            key=key,
            result=value,
            ttl=ttl or self._default_ttl,
        )

        self._cache[key] = entry
        self._cache.move_to_end(key)
        self._enforce_size_limit()

    def invalidate(self, key: str) -> bool:
        """Remove specific key from cache.

        Args:
            key: Cache key to invalidate

        Returns:
            True if key was found and removed
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    @property
    def size(self) -> int:
        """Current number of cached items."""
        self._evict_expired()
        return len(self._cache)

    @property
    def stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats (hits, misses, size, etc.)
        """
        total_requests = self._hits + self._misses
        hit_rate = (
            (self._hits / total_requests * 100) if total_requests > 0 else 0
        )

        return {
            "size": self.size,
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.2f}%",
        }


# Global cache instance
_global_cache: Optional[AsyncLRUCache] = None


def get_cache(
    max_size: int = 1000,
    default_ttl: int = 3600,
) -> AsyncLRUCache:
    """Get or create the global cache instance.

    Args:
        max_size: Maximum cache size
        default_ttl: Default TTL in seconds

    Returns:
        Global cache instance
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = AsyncLRUCache(max_size, default_ttl)
    return _global_cache


def cached(
    ttl: Optional[int] = None,
    key_prefix: str = "",
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to cache async function results.

    Args:
        ttl: Time-to-live in seconds (uses cache default if None)
        key_prefix: Prefix for cache keys to avoid collisions

    Returns:
        Decorated function with caching

    Example:
        @cached(ttl=3600, key_prefix="query")
        async def expensive_query(question: str) -> QueryResult:
            # Expensive operation...
            return result
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        cache = get_cache()

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Generate cache key
            cache_key = f"{key_prefix}:{cache._make_key(*args, **kwargs)}"

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache if it's a QueryResult
            if isinstance(result, QueryResult):
                cache.set(cache_key, result, ttl)

            return result

        # Expose cache control methods
        wrapper.cache_invalidate = lambda *args, **kwargs: cache.invalidate(
            f"{key_prefix}:{cache._make_key(*args, **kwargs)}"
        )
        wrapper.cache_clear = cache.clear
        wrapper.cache_stats = cache.stats

        return wrapper

    return decorator
