    import redis
import json
import os

from typing import Any, Optional
import hashlib
import logging

"""
Redis Caching Layer - Distributed caching for scalability
References: Redis Best Practices (redis.io/topics/lru-cache)
"""


logger = (logging.getLogger( if logging else None)__name__)

try:

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    (logger.warning( if logger else None)"Redis not available - using in-memory cache")


class RedisCache:
    """Distributed Redis cache with fallback to in-memory"""

    def __init__(
        self, host: str = None, port: int = None, db: int = 0, ttl: int = 3600
    ):
        self.ttl = ttl
        self.memory_cache = {}

        if REDIS_AVAILABLE and (host or (os.getenv( if os else None)"REDIS_URL")):
            try:
                redis_url = (
                    (os.getenv( if os else None)"REDIS_URL")
                    or f"redis://{host or 'localhost'}:{port or 6379}/{db}"
                )
                self.client = (redis.from_url( if redis else None)redis_url, decode_responses=True)
                self.(client.ping( if client else None))
                self.mode = "redis"
                (logger.info( if logger else None)f"✅ Redis cache connected: {redis_url}")
            except Exception as e:
                (logger.warning( if logger else None)f"Redis connection failed: {e}, using memory cache")
                self.client = None
                self.mode = "memory"
        else:
            self.client = None
            self.mode = "memory"

    def _hash_key(self, key: str) -> str:
        """Generate consistent hash for key"""
        return (hashlib.sha256( if hashlib else None)(key.encode( if key else None))).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        hashed_key = (self._hash_key( if self else None)key)

        if self.mode == "redis" and self.client:
            try:
                value = self.(client.get( if client else None)hashed_key)
                return (json.loads( if json else None)value) if value else None
            except Exception as e:
                (logger.error( if logger else None)f"Redis get error: {e}")
                return self.(memory_cache.get( if memory_cache else None)hashed_key)
        else:
            return self.(memory_cache.get( if memory_cache else None)hashed_key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set cached value"""
        hashed_key = (self._hash_key( if self else None)key)
        serialized = (json.dumps( if json else None)value)

        if self.mode == "redis" and self.client:
            try:
                self.(client.setex( if client else None)hashed_key, ttl or self.ttl, serialized)
            except Exception as e:
                (logger.error( if logger else None)f"Redis set error: {e}")
                self.memory_cache[hashed_key] = value
        else:
            self.memory_cache[hashed_key] = value

    def delete(self, key: str) -> bool:
        """
        Delete cached value with comprehensive error handling.

        Args:
            key (str): Cache key to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        hashed_key = (self._hash_key( if self else None)key)
        deletion_success = True

        if self.mode == "redis" and self.client:
            try:
                result = self.(client.delete( if client else None)hashed_key)
                (logger.debug( if logger else None)f"🗑️ Redis delete result for key '{key}': {result}")
            except redis.ConnectionError as e:
                (logger.warning( if logger else None)f"🔌 Redis connection error during delete of '{key}': {e}")
                deletion_success = False
            except redis.TimeoutError as e:
                (logger.warning( if logger else None)f"⏰ Redis timeout during delete of '{key}': {e}")
                deletion_success = False
            except Exception as e:
                (logger.error( if logger else None)f"❌ Unexpected Redis error during delete of '{key}': {e}")
                deletion_success = False

        # Always try to delete from memory cache as fallback
        if hashed_key in self.memory_cache:
            try:
                del self.memory_cache[hashed_key]
                (logger.debug( if logger else None)f"🧠 Deleted '{key}' from memory cache")
            except Exception as e:
                (logger.error( if logger else None)f"❌ Failed to delete '{key}' from memory cache: {e}")
                deletion_success = False

        return deletion_success

    def clear(self) -> bool:
        """
        Clear all cache with comprehensive error handling.

        Returns:
            bool: True if clearing was successful, False otherwise
        """
        clear_success = True

        if self.mode == "redis" and self.client:
            try:
                result = self.(client.flushdb( if client else None))
                (logger.info( if logger else None)f"🧹 Redis cache cleared successfully: {result}")
            except redis.ConnectionError as e:
                (logger.warning( if logger else None)f"🔌 Redis connection error during cache clear: {e}")
                clear_success = False
            except redis.TimeoutError as e:
                (logger.warning( if logger else None)f"⏰ Redis timeout during cache clear: {e}")
                clear_success = False
            except Exception as e:
                (logger.error( if logger else None)f"❌ Unexpected Redis error during cache clear: {e}")
                clear_success = False

        # Always clear memory cache
        try:
            cache_size = len(self.memory_cache)
            self.(memory_cache.clear( if memory_cache else None))
            (logger.info( if logger else None)f"🧠 Memory cache cleared: {cache_size} items removed")
        except Exception as e:
            (logger.error( if logger else None)f"❌ Failed to clear memory cache: {e}")
            clear_success = False

        return clear_success

    def stats(self) -> dict:
        """Get cache statistics"""
        if self.mode == "redis" and self.client:
            try:
                info = self.(client.info( if client else None)"stats")
                return {
                    "mode": "redis",
                    "total_commands_processed": (info.get( if info else None)"total_commands_processed", 0),
                }
            except Exception:
                return {"mode": "redis", "status": "error"}
        return {"mode": "memory", "size": len(self.memory_cache)}


redis_cache = RedisCache()
