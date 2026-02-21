"""
Multi-Tier Cache - L1/L2/L3 Caching Strategy
==============================================

Provides a cache-aside pattern with three tiers:
  L1: In-memory LRU (microseconds) — per-process
  L2: Redis (milliseconds) — shared across processes
  L3: CDN (seconds) — for static/immutable assets (future)

Promotion strategy: L2 hit → promote to L1 to avoid repeat Redis round-trips.

Usage:
    # Direct use
    cache = MultiTierCache()
    await cache.set("product:br-001", data, ttl=300)
    result = await cache.get("product:br-001")

    # Decorator
    @cached(ttl=300)
    async def get_product(sku: str) -> dict:
        return await db.find_product(sku)
"""

from __future__ import annotations

import asyncio
import functools
import hashlib
import json
import logging
import os
from typing import Any, Callable, Optional

from cachetools import LRUCache, TTLCache

logger = logging.getLogger(__name__)


class MultiTierCache:
    """
    Multi-tier cache: L1 (in-memory LRU) → L2 (Redis) → None

    Thread-safe for async use. L1 is per-process; L2 is shared.
    """

    def __init__(
        self,
        l1_max_size: int = 1000,
        l1_ttl: int = 60,
        redis_url: Optional[str] = None,
    ) -> None:
        # L1: In-memory TTLCache (combines LRU eviction with TTL expiration)
        self._l1: TTLCache = TTLCache(maxsize=l1_max_size, ttl=l1_ttl)
        self._redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis_client: Any = None
        self._redis_connected = False

        # Stats tracking
        self.stats: dict[str, int] = {
            "l1_hits": 0,
            "l1_misses": 0,
            "l2_hits": 0,
            "l2_misses": 0,
            "total_sets": 0,
            "total_invalidations": 0,
        }

    @property
    def l1_size(self) -> int:
        """Current number of entries in L1 cache"""
        return len(self._l1)

    async def _ensure_redis(self) -> bool:
        """Connect to Redis lazily"""
        if self._redis_connected:
            return True
        try:
            import redis.asyncio as redis

            self._redis_client = redis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=2.0,
                socket_connect_timeout=2.0,
            )
            await self._redis_client.ping()
            self._redis_connected = True
        except Exception as e:
            logger.debug(f"Redis unavailable: {e} — L2 cache disabled")
            self._redis_connected = False
        return self._redis_connected

    async def _l2_get(self, key: str) -> Optional[Any]:
        """Get value from L2 (Redis)"""
        if not await self._ensure_redis():
            return None
        try:
            raw = await self._redis_client.get(key)
            if raw is not None:
                return json.loads(raw)
        except Exception as e:
            logger.debug(f"L2 get error: {e}")
        return None

    async def _l2_set(self, key: str, value: Any, ttl: int) -> None:
        """Set value in L2 (Redis)"""
        if not await self._ensure_redis():
            return
        try:
            await self._redis_client.setex(key, ttl, json.dumps(value, default=str))
        except Exception as e:
            logger.debug(f"L2 set error: {e}")

    async def _l2_delete(self, key: str) -> None:
        """Delete value from L2 (Redis)"""
        if not await self._ensure_redis():
            return
        try:
            await self._redis_client.delete(key)
        except Exception as e:
            logger.debug(f"L2 delete error: {e}")

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache — checks L1 then L2.

        On L2 hit, value is promoted to L1 for faster subsequent access.
        Returns None on complete miss.
        """
        # L1 check (in-memory)
        value = self._l1.get(key)
        if value is not None:
            self.stats["l1_hits"] += 1
            return value

        self.stats["l1_misses"] += 1

        # L2 check (Redis)
        value = await self._l2_get(key)
        if value is not None:
            self.stats["l2_hits"] += 1
            # Promote to L1
            self._l1[key] = value
            return value

        self.stats["l2_misses"] += 1
        return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """
        Set value in all tiers.

        Writes synchronously to L1, then fires L2 write as background task.
        """
        # L1: immediate write
        self._l1[key] = value
        self.stats["total_sets"] += 1

        # L2: async write (don't block the caller)
        await self._l2_set(key, value, ttl)

    async def invalidate(self, key: str) -> None:
        """Remove value from all cache tiers"""
        # L1: immediate removal
        self._l1.pop(key, None)
        self.stats["total_invalidations"] += 1

        # L2: Redis deletion
        await self._l2_delete(key)

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern (e.g., "product:*").
        Returns count of invalidated keys.
        """
        # Clear all from L1 that match pattern
        keys_to_remove = [k for k in self._l1.keys() if k.startswith(pattern.rstrip("*"))]
        for k in keys_to_remove:
            self._l1.pop(k, None)

        # Clear from Redis
        count = len(keys_to_remove)
        if await self._ensure_redis():
            try:
                cursor = 0
                while True:
                    cursor, keys = await self._redis_client.scan(cursor, match=pattern, count=100)
                    if keys:
                        await self._redis_client.delete(*keys)
                        count += len(keys)
                    if cursor == 0:
                        break
            except Exception as e:
                logger.debug(f"Pattern invalidation error: {e}")

        self.stats["total_invalidations"] += count
        return count

    def get_stats(self) -> dict[str, Any]:
        """Return cache statistics including hit rate"""
        total = self.stats["l1_hits"] + self.stats["l1_misses"]
        total_requests = total
        l1_hit_rate = (self.stats["l1_hits"] / total * 100) if total > 0 else 0.0

        total_l2 = self.stats["l2_hits"] + self.stats["l2_misses"]
        l2_hit_rate = (self.stats["l2_hits"] / total_l2 * 100) if total_l2 > 0 else 0.0

        return {
            "total_requests": total_requests,
            "l1_hits": self.stats["l1_hits"],
            "l1_misses": self.stats["l1_misses"],
            "l1_hit_rate": round(l1_hit_rate, 2),
            "l2_hits": self.stats["l2_hits"],
            "l2_misses": self.stats["l2_misses"],
            "l2_hit_rate": round(l2_hit_rate, 2),
            "hit_rate": round(l1_hit_rate, 2),  # Primary hit rate (L1)
            "l1_size": self.l1_size,
            "total_sets": self.stats["total_sets"],
            "total_invalidations": self.stats["total_invalidations"],
        }

    async def close(self) -> None:
        """Disconnect from Redis"""
        if self._redis_client and self._redis_connected:
            await self._redis_client.aclose()
            self._redis_connected = False


# Global shared cache instance (lazy init)
_default_cache: Optional[MultiTierCache] = None


def get_cache() -> MultiTierCache:
    """Get or create the default global cache instance"""
    global _default_cache
    if _default_cache is None:
        _default_cache = MultiTierCache()
    return _default_cache


def cached(ttl: int = 300, key_prefix: str = "") -> Callable:
    """
    Decorator for automatic caching of async function results.

    Cache key is derived from function name + arguments.
    Different argument combinations get separate cache entries.

    Args:
        ttl: Cache TTL in seconds (default: 5 minutes)
        key_prefix: Optional prefix for cache keys

    Example:
        @cached(ttl=300)
        async def get_product(sku: str) -> dict:
            return await db.find_product(sku)
    """
    # Each decorated function gets its own isolated cache
    # to avoid cross-function key collisions
    def decorator(func: Callable) -> Callable:
        func_cache = MultiTierCache(l1_max_size=500, l1_ttl=ttl)
        prefix = key_prefix or func.__name__

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Build cache key from function name + serialized args
            key_data = {
                "args": [str(a) for a in args],
                "kwargs": {k: str(v) for k, v in sorted(kwargs.items())},
            }
            # 32 hex chars = 128 bits — reduces birthday collision probability
            # from ~1/2^32 (16 hex, 65k keys) to ~1/2^64 (32 hex, negligible)
            key_hash = hashlib.sha256(
                json.dumps(key_data, sort_keys=True).encode()
            ).hexdigest()[:32]
            cache_key = f"{prefix}:{key_hash}"

            # Check cache
            cached_value = await func_cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Cache miss — call function
            result = await func(*args, **kwargs)

            # Store in cache
            if result is not None:
                await func_cache.set(cache_key, result, ttl=ttl)

            return result

        # Expose cache instance for testing/invalidation
        wrapper.cache = func_cache  # type: ignore[attr-defined]
        wrapper.cache_invalidate = lambda *a, **k: func_cache.invalidate(  # type: ignore[attr-defined]
            f"{prefix}:{hashlib.sha256(json.dumps({'args': [str(x) for x in a], 'kwargs': {kk: str(vv) for kk, vv in sorted(k.items())}}, sort_keys=True).encode()).hexdigest()[:32]}"
        )

        return wrapper

    return decorator
