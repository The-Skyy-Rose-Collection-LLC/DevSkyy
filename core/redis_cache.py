"""
Redis Caching Layer
====================

Production-ready Redis caching for LLM responses and expensive operations.

Features:
- Async Redis client with connection pooling
- Automatic serialization/deserialization
- TTL support with smart expiration
- Cache warming and invalidation
- Metrics and monitoring

Following patterns from:
- instructor LLM caching
- FastAPI best practices
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, TypeVar

from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Prometheus metrics for cache monitoring
cache_hits = Counter("redis_cache_hits_total", "Total cache hits")
cache_misses = Counter("redis_cache_misses_total", "Total cache misses")
cache_errors = Counter("redis_cache_errors_total", "Total cache errors")
cache_hit_rate = Gauge("redis_cache_hit_rate", "Cache hit rate percentage")


@dataclass(slots=True)
class RedisConfig:
    """Redis configuration from environment."""

    url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    max_connections: int = field(
        default_factory=lambda: int(os.getenv("REDIS_MAX_CONNECTIONS", "20"))
    )
    socket_timeout: float = field(
        default_factory=lambda: float(os.getenv("REDIS_SOCKET_TIMEOUT", "2.0"))
    )
    socket_connect_timeout: float = field(
        default_factory=lambda: float(os.getenv("REDIS_CONNECT_TIMEOUT", "2.0"))
    )
    retry_on_timeout: bool = field(
        default_factory=lambda: os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true"
    )
    decode_responses: bool = True
    # LLM cache specific
    llm_cache_ttl: int = field(default_factory=lambda: int(os.getenv("LLM_CACHE_TTL", "3600")))
    llm_cache_prefix: str = "llm:"


class RedisCache:
    """
    Async Redis cache for LLM responses.

    Features:
    - Connection pooling via redis-py async
    - Pydantic model serialization
    - Cache key generation with schema hashing
    - Graceful degradation (returns None on errors)

    Usage:
        cache = RedisCache()
        await cache.connect()

        # Cache LLM response
        await cache.set_llm_response(prompt, model, response, ttl=3600)

        # Get cached response
        cached = await cache.get_llm_response(prompt, model)
    """

    __slots__ = ("_client", "_pool", "_config", "_connected", "_metrics")

    def __init__(self, config: RedisConfig | None = None) -> None:
        self._config = config or RedisConfig()
        self._client: Any = None
        self._pool: Any = None
        self._connected = False
        self._metrics = {"hits": 0, "misses": 0, "errors": 0}

    async def connect(self) -> bool:
        """Connect to Redis with connection pooling."""
        if self._connected:
            return True

        try:
            import redis.asyncio as redis

            self._pool = redis.ConnectionPool.from_url(
                self._config.url,
                max_connections=self._config.max_connections,
                socket_timeout=self._config.socket_timeout,
                socket_connect_timeout=self._config.socket_connect_timeout,
                retry_on_timeout=self._config.retry_on_timeout,
                decode_responses=self._config.decode_responses,
            )
            self._client = redis.Redis(connection_pool=self._pool)

            # Test connection
            await self._client.ping()
            self._connected = True
            logger.info(
                f"Redis connected: {self._config.url.split('@')[-1] if '@' in self._config.url else 'localhost'}"
            )
            return True

        except ImportError:
            logger.warning("redis package not installed - caching disabled")
            return False
        except Exception as e:
            logger.warning(f"Redis connection failed: {e} - caching disabled")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()
            if self._pool:
                await self._pool.disconnect()
            self._connected = False
            logger.info("Redis disconnected")

    def _generate_key(self, prompt: str, model: str, **kwargs: Any) -> str:
        """Generate cache key from prompt and parameters."""
        key_data = {"prompt": prompt, "model": model, **kwargs}
        key_hash = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()[:16]
        return f"{self._config.llm_cache_prefix}{model}:{key_hash}"

    async def get_llm_response(
        self, prompt: str, model: str, **kwargs: Any
    ) -> dict[str, Any] | None:
        """Get cached LLM response."""
        if not self._connected:
            return None

        try:
            key = self._generate_key(prompt, model, **kwargs)
            data = await self._client.get(key)

            if data:
                self._metrics["hits"] += 1
                cache_hits.inc()
                # Update hit rate gauge
                total = self._metrics["hits"] + self._metrics["misses"]
                if total > 0:
                    cache_hit_rate.set((self._metrics["hits"] / total) * 100)
                return json.loads(data)

            self._metrics["misses"] += 1
            cache_misses.inc()
            # Update hit rate gauge
            total = self._metrics["hits"] + self._metrics["misses"]
            if total > 0:
                cache_hit_rate.set((self._metrics["hits"] / total) * 100)
            return None

        except Exception as e:
            self._metrics["errors"] += 1
            cache_errors.inc()
            logger.debug(f"Cache get error: {e}")
            return None

    async def set_llm_response(
        self,
        prompt: str,
        model: str,
        response: dict[str, Any],
        ttl: int | None = None,
        **kwargs: Any,
    ) -> bool:
        """Cache LLM response."""
        if not self._connected:
            return False

        try:
            key = self._generate_key(prompt, model, **kwargs)
            ttl = ttl or self._config.llm_cache_ttl
            await self._client.setex(key, ttl, json.dumps(response))
            return True

        except Exception as e:
            self._metrics["errors"] += 1
            cache_errors.inc()
            logger.debug(f"Cache set error: {e}")
            return False

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics including hit rate.

        Returns:
            Dictionary with cache metrics:
            - hit_rate: Percentage of cache hits (0-100)
            - total_hits: Total number of cache hits
            - total_misses: Total number of cache misses
            - total_errors: Total number of cache errors
            - connection_pool_size: Max connections in pool
        """
        total_requests = self._metrics["hits"] + self._metrics["misses"]
        hit_rate = (self._metrics["hits"] / total_requests) * 100 if total_requests > 0 else 0.0

        return {
            "hit_rate": round(hit_rate, 2),
            "total_hits": self._metrics["hits"],
            "total_misses": self._metrics["misses"],
            "total_errors": self._metrics["errors"],
            "connection_pool_size": self._pool.max_connections if self._pool else 0,
        }
