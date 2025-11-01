import aioredis
import json
import os
import redis
import time

from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict
import asyncio
import hashlib
import logging

"""
Advanced Caching System for DevSkyy Enhanced Platform
Intelligent multi-level caching for optimal performance

Features:
- Redis integration for distributed caching
- In-memory LRU cache for hot data
- Database query result caching
- API response caching
- File system caching for static assets
- Cache warming and invalidation strategies
"""

logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    """Cache configuration settings."""

    redis_url: str = "redis://localhost:6379"
    default_ttl: int = 3600  # 1 hour
    max_memory_cache_size: int = 1000
    enable_compression: bool = True
    enable_encryption: bool = False
    cache_prefix: str = "devskyy:"

class AdvancedCacheManager:
    """
    Advanced caching system with multiple cache layers and intelligent strategies.
    """

    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.redis_client = None
        self.async_redis_client = None
        self.memory_cache = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0,
        }
        self.memory_cache_order = []  # For LRU implementation
        self._initialize_redis()

    def _initialize_redis(self):
        """Initialize Redis connections."""
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}. Using memory cache only.")
            self.redis_client = None

    async def _initialize_async_redis(self):
        """Initialize async Redis connection."""
        if not self.async_redis_client:
            try:
                self.async_redis_client = await aioredis.from_url(
                    self.config.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                )
                await self.async_redis_client.ping()
                logger.info("✅ Async Redis connection established")
            except Exception as e:
                logger.warning(f"⚠️ Async Redis connection failed: {e}")
                self.async_redis_client = None

    def _generate_cache_key(self, key: str, namespace: str = "default") -> str:
        """Generate a cache key with proper namespace and prefix."""
        return f"{self.config.cache_prefix}{namespace}:{key}"

    def _serialize_value(self, value: Any) -> str:
        """Serialize value for storage."""
        try:
            if self.config.enable_compression:
                # Only serialize JSON-compatible types for security
                if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                    return json.dumps(value)
                else:
                    # Convert non-JSON types to string representation for security
                    logger.warning(
                        f"Converting non-JSON type {type(value)} to string for security"
                    )
                    return json.dumps(str(value))
            else:
                return json.dumps(value)
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            return json.dumps(str(value))

    def _deserialize_value(self, value: str) -> Any:
        """Deserialize value from storage."""
        try:
            # Try JSON first
            return json.loads(value)
        except json.JSONDecodeError:
            # Log warning about unsupported pickle data
            logger.warning(
                "Pickle deserialization is disabled for security reasons. Data may be lost."
            )
            return None

    def _update_memory_cache_lru(self, key: str):
        """Update LRU order for memory cache."""
        if key in self.memory_cache_order:
            self.memory_cache_order.remove(key)
        self.memory_cache_order.append(key)

        # Evict oldest entries if cache is full
        while len(self.memory_cache) > self.config.max_memory_cache_size:
            oldest_key = self.memory_cache_order.pop(0)
            if oldest_key in self.memory_cache:
                del self.memory_cache[oldest_key]

    def get(self, key: str, namespace: str = "default", default: Any = None) -> Any:
        """
        Get value from cache (synchronous).
        Checks memory cache first, then Redis.
        """
        try:
            cache_key = self._generate_cache_key(key, namespace)

            # Check memory cache first
            if cache_key in self.memory_cache:
                self._update_memory_cache_lru(cache_key)
                self.cache_stats["hits"] += 1
                return self.memory_cache[cache_key]["value"]

            # Check Redis cache
            if self.redis_client:
                try:
                    redis_value = self.redis_client.get(cache_key)
                    if redis_value is not None:
                        value = self._deserialize_value(redis_value)

                        # Store in memory cache for faster access
                        self.memory_cache[cache_key] = {
                            "value": value,
                            "timestamp": time.time(),
                        }
                        self._update_memory_cache_lru(cache_key)

                        self.cache_stats["hits"] += 1
                        return value
                except Exception as e:
                    logger.error(f"Redis get error: {e}")
                    self.cache_stats["errors"] += 1

            self.cache_stats["misses"] += 1
            return default

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.cache_stats["errors"] += 1
            return default

    async def aget(
        self, key: str, namespace: str = "default", default: Any = None
    ) -> Any:
        """
        Get value from cache (asynchronous).
        """
        try:
            cache_key = self._generate_cache_key(key, namespace)

            # Check memory cache first
            if cache_key in self.memory_cache:
                self._update_memory_cache_lru(cache_key)
                self.cache_stats["hits"] += 1
                return self.memory_cache[cache_key]["value"]

            # Check Redis cache
            if not self.async_redis_client:
                await self._initialize_async_redis()

            if self.async_redis_client:
                try:
                    redis_value = await self.async_redis_client.get(cache_key)
                    if redis_value is not None:
                        value = self._deserialize_value(redis_value)

                        # Store in memory cache
                        self.memory_cache[cache_key] = {
                            "value": value,
                            "timestamp": time.time(),
                        }
                        self._update_memory_cache_lru(cache_key)

                        self.cache_stats["hits"] += 1
                        return value
                except Exception as e:
                    logger.error(f"Async Redis get error: {e}")
                    self.cache_stats["errors"] += 1

            self.cache_stats["misses"] += 1
            return default

        except Exception as e:
            logger.error(f"Async cache get error: {e}")
            self.cache_stats["errors"] += 1
            return default

    def set(
        self, key: str, value: Any, ttl: int = None, namespace: str = "default"
    ) -> bool:
        """
        Set value in cache (synchronous).
        Stores in both memory and Redis cache.
        """
        try:
            cache_key = self._generate_cache_key(key, namespace)
            ttl = ttl or self.config.default_ttl

            # Store in memory cache
            self.memory_cache[cache_key] = {
                "value": value,
                "timestamp": time.time(),
                "ttl": ttl,
            }
            self._update_memory_cache_lru(cache_key)

            # Store in Redis cache
            if self.redis_client:
                try:
                    serialized_value = self._serialize_value(value)
                    self.redis_client.setex(cache_key, ttl, serialized_value)
                except Exception as e:
                    logger.error(f"Redis set error: {e}")
                    self.cache_stats["errors"] += 1

            self.cache_stats["sets"] += 1
            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self.cache_stats["errors"] += 1
            return False

    async def aset(
        self, key: str, value: Any, ttl: int = None, namespace: str = "default"
    ) -> bool:
        """
        Set value in cache (asynchronous).
        """
        try:
            cache_key = self._generate_cache_key(key, namespace)
            ttl = ttl or self.config.default_ttl

            # Store in memory cache
            self.memory_cache[cache_key] = {
                "value": value,
                "timestamp": time.time(),
                "ttl": ttl,
            }
            self._update_memory_cache_lru(cache_key)

            # Store in Redis cache
            if not self.async_redis_client:
                await self._initialize_async_redis()

            if self.async_redis_client:
                try:
                    serialized_value = self._serialize_value(value)
                    await self.async_redis_client.setex(
                        cache_key, ttl, serialized_value
                    )
                except Exception as e:
                    logger.error(f"Async Redis set error: {e}")
                    self.cache_stats["errors"] += 1

            self.cache_stats["sets"] += 1
            return True

        except Exception as e:
            logger.error(f"Async cache set error: {e}")
            self.cache_stats["errors"] += 1
            return False

    def delete(self, key: str, namespace: str = "default") -> bool:
        """
        Delete value from cache.
        """
        try:
            cache_key = self._generate_cache_key(key, namespace)

            # Remove from memory cache
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]
                if cache_key in self.memory_cache_order:
                    self.memory_cache_order.remove(cache_key)

            # Remove from Redis cache
            if self.redis_client:
                try:
                    self.redis_client.delete(cache_key)
                except Exception as e:
                    logger.error(f"Redis delete error: {e}")
                    self.cache_stats["errors"] += 1

            self.cache_stats["deletes"] += 1
            return True

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            self.cache_stats["errors"] += 1
            return False

    async def adelete(self, key: str, namespace: str = "default") -> bool:
        """
        Delete value from cache (asynchronous).
        """
        try:
            cache_key = self._generate_cache_key(key, namespace)

            # Remove from memory cache
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]
                if cache_key in self.memory_cache_order:
                    self.memory_cache_order.remove(cache_key)

            # Remove from Redis cache
            if not self.async_redis_client:
                await self._initialize_async_redis()

            if self.async_redis_client:
                try:
                    await self.async_redis_client.delete(cache_key)
                except Exception as e:
                    logger.error(f"Async Redis delete error: {e}")
                    self.cache_stats["errors"] += 1

            self.cache_stats["deletes"] += 1
            return True

        except Exception as e:
            logger.error(f"Async cache delete error: {e}")
            self.cache_stats["errors"] += 1
            return False

    def clear_namespace(self, namespace: str) -> bool:
        """
        Clear all entries in a specific namespace.
        """
        try:
            pattern = self._generate_cache_key("*", namespace)

            # Clear from memory cache
            keys_to_delete = [
                key
                for key in self.memory_cache.keys()
                if key.startswith(f"{self.config.cache_prefix}{namespace}:")
            ]
            for key in keys_to_delete:
                del self.memory_cache[key]
                if key in self.memory_cache_order:
                    self.memory_cache_order.remove(key)

            # Clear from Redis cache
            if self.redis_client:
                try:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                except Exception as e:
                    logger.error(f"Redis clear namespace error: {e}")
                    self.cache_stats["errors"] += 1

            return True

        except Exception as e:
            logger.error(f"Clear namespace error: {e}")
            self.cache_stats["errors"] += 1
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        """
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (
            (self.cache_stats["hits"] / total_requests * 100)
            if total_requests > 0
            else 0
        )

        return {
            "cache_stats": self.cache_stats,
            "hit_rate": f"{hit_rate:.2f}%",
            "memory_cache_size": len(self.memory_cache),
            "memory_cache_max_size": self.config.max_memory_cache_size,
            "redis_connected": self.redis_client is not None
            and self.redis_client.ping(),
            "async_redis_connected": self.async_redis_client is not None,
        }

    def warm_cache(
        self, warmup_data: Dict[str, Any], namespace: str = "warmup"
    ) -> bool:
        """
        Warm the cache with frequently accessed data.
        """
        try:
            for key, value in warmup_data.items():
                self.set(key, value, namespace=namespace)

            logger.info(f"✅ Cache warmed with {len(warmup_data)} entries")
            return True

        except Exception as e:
            logger.error(f"Cache warming error: {e}")
            return False

# Cache decorators for easy integration
def cached(ttl: int = 3600, namespace: str = "default", key_func: Callable = None):
    """
    Decorator for caching function results.

    Args:
        ttl: Time to live in seconds
        namespace: Cache namespace
        key_func: Function to generate cache key
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.sha256(":".join(key_parts).encode()).hexdigest()

            # Try to get from cache
            cache_manager = get_cache_manager()
            cached_result = cache_manager.get(cache_key, namespace)

            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl, namespace)

            return result

        return wrapper

    return decorator

def async_cached(
    ttl: int = 3600, namespace: str = "default", key_func: Callable = None
):
    """
    Decorator for caching async function results.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.sha256(":".join(key_parts).encode()).hexdigest()

            # Try to get from cache
            cache_manager = get_cache_manager()
            cached_result = await cache_manager.aget(cache_key, namespace)

            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.aset(cache_key, result, ttl, namespace)

            return result

        return wrapper

    return decorator

# Database query caching
class DatabaseCacheManager:
    """
    Specialized cache manager for database queries.
    """

    def __init__(self, cache_manager: AdvancedCacheManager):
        self.cache_manager = cache_manager
        self.namespace = "database"

    def cache_query_result(
        self, query: str, params: tuple, result: Any, ttl: int = 300
    ):
        """
        Cache database query result.
        """
        query_hash = hashlib.sha256(f"{query}:{str(params)}".encode()).hexdigest()
        self.cache_manager.set(query_hash, result, ttl, self.namespace)

    def get_cached_query_result(self, query: str, params: tuple) -> Any:
        """
        Get cached database query result.
        """
        query_hash = hashlib.sha256(f"{query}:{str(params)}".encode()).hexdigest()
        return self.cache_manager.get(query_hash, self.namespace)

    def invalidate_table_cache(self, table_name: str):
        """
        Invalidate all cached queries for a specific table.
        """
        # This would require tracking which queries affect which tables
        # For simplicity, we'll clear the entire database namespace
        self.cache_manager.clear_namespace(self.namespace)

# API response caching
class APICacheManager:
    """
    Specialized cache manager for API responses.
    """

    def __init__(self, cache_manager: AdvancedCacheManager):
        self.cache_manager = cache_manager
        self.namespace = "api"

    def cache_api_response(
        self, endpoint: str, params: Dict[str, Any], response: Any, ttl: int = 600
    ):
        """
        Cache API response.
        """
        cache_key = f"{endpoint}:{hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()}"
        self.cache_manager.set(cache_key, response, ttl, self.namespace)

    def get_cached_api_response(self, endpoint: str, params: Dict[str, Any]) -> Any:
        """
        Get cached API response.
        """
        cache_key = f"{endpoint}:{hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()}"
        return self.cache_manager.get(cache_key, self.namespace)

# Global cache manager instance
_cache_manager = None

def get_cache_manager() -> AdvancedCacheManager:
    """
    Get global cache manager instance.
    """
    global _cache_manager
    if _cache_manager is None:
        config = CacheConfig(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
            default_ttl=int(os.getenv("CACHE_DEFAULT_TTL", "3600")),
            max_memory_cache_size=int(os.getenv("CACHE_MEMORY_SIZE", "1000")),
        )
        _cache_manager = AdvancedCacheManager(config)

    return _cache_manager

def initialize_cache_system():
    """
    Initialize the cache system with warmup data.
    """
    cache_manager = get_cache_manager()

    # Warm up cache with frequently accessed data
    warmup_data = {
        "brand_colors": ["#E8B4B8", "#C9A96E", "#FFD700", "#C0C0C0"],
        "luxury_keywords": ["luxury", "premium", "exclusive", "designer"],
        "agent_capabilities": [
            "brand_intelligence",
            "performance_optimization",
            "security_monitoring",
        ],
    }

    cache_manager.warm_cache(warmup_data, "system")
    logger.info("✅ Cache system initialized and warmed up")

# Example usage
async def example_usage():
    """
    Example usage of the advanced caching system.
    """
    # Initialize cache manager
    cache_manager = get_cache_manager()

    # Basic cache operations
    await cache_manager.aset(
        "user:123", {"name": "John", "email": "john@example.com"}, ttl=1800
    )
    user_data = await cache_manager.aget("user:123")
    logger.info(f"Cached user data: {user_data}")

    # Using decorators
    @async_cached(ttl=600, namespace="api")
    async def get_user_profile(user_id: int):
        # Simulate API call
        await asyncio.sleep(0.1)
        return {"id": user_id, "name": f"User {user_id}", "premium": True}

    # First call - will execute function and cache result
    profile1 = await get_user_profile(123)
    logger.info(f"First call result: {profile1}")

    # Second call - will return cached result
    profile2 = await get_user_profile(123)
    logger.info(f"Second call result (cached): {profile2}")

    # Get cache statistics
    stats = cache_manager.get_stats()
    logger.info(f"Cache statistics: {stats}")

if __name__ == "__main__":
    asyncio.run(example_usage())
