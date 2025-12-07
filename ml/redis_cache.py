import hashlib
import json
import logging
import os
from typing import Any

import redis


"""
Redis Caching Layer - Distributed caching for scalability
References: Redis Best Practices (redis.io/topics/lru-cache)
"""

logger = logging.getLogger(__name__)

try:

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available - using in-memory cache")


class RedisCache:
    """Distributed Redis cache with fallback to in-memory"""

    def __init__(self, host: str | None = None, port: int | None = None, db: int = 0, ttl: int = 3600):
        self.ttl = ttl
        self.memory_cache = {}

        if REDIS_AVAILABLE and (host or os.getenv("REDIS_URL")):
            try:
                redis_url = os.getenv("REDIS_URL") or f"redis://{host or 'localhost'}:{port or 6379}/{db}"
                self.client = redis.from_url(redis_url, decode_responses=True)
                self.client.ping()
                self.mode = "redis"
                logger.info(f"✅ Redis cache connected: {redis_url}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, using memory cache")
                self.client = None
                self.mode = "memory"
        else:
            self.client = None
            self.mode = "memory"

    def _hash_key(self, key: str) -> str:
        """Generate consistent hash for key"""
        return hashlib.sha256(key.encode()).hexdigest()

    def get(self, key: str) -> Any | None:
        """Get cached value"""
        hashed_key = self._hash_key(key)

        if self.mode == "redis" and self.client:
            try:
                value = self.client.get(hashed_key)
                return json.loads(value) if value else None
            except Exception as e:
                logger.error(f"Redis get error: {e}")
                return self.memory_cache.get(hashed_key)
        else:
            return self.memory_cache.get(hashed_key)

    def set(self, key: str, value: Any, ttl: int | None = None):
        """Set cached value"""
        hashed_key = self._hash_key(key)
        serialized = json.dumps(value)

        if self.mode == "redis" and self.client:
            try:
                self.client.setex(hashed_key, ttl or self.ttl, serialized)
            except Exception as e:
                logger.error(f"Redis set error: {e}")
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
        hashed_key = self._hash_key(key)
        deletion_success = True

        if self.mode == "redis" and self.client:
            try:
                result = self.client.delete(hashed_key)
                logger.debug(f"🗑️ Redis delete result for key '{key}': {result}")
            except redis.ConnectionError as e:
                logger.warning(f"🔌 Redis connection error during delete of '{key}': {e}")
                deletion_success = False
            except redis.TimeoutError as e:
                logger.warning(f"⏰ Redis timeout during delete of '{key}': {e}")
                deletion_success = False
            except Exception as e:
                logger.error(f"❌ Unexpected Redis error during delete of '{key}': {e}")
                deletion_success = False

        # Always try to delete from memory cache as fallback
        if hashed_key in self.memory_cache:
            try:
                del self.memory_cache[hashed_key]
                logger.debug(f"🧠 Deleted '{key}' from memory cache")
            except Exception as e:
                logger.error(f"❌ Failed to delete '{key}' from memory cache: {e}")
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
                result = self.client.flushdb()
                logger.info(f"🧹 Redis cache cleared successfully: {result}")
            except redis.ConnectionError as e:
                logger.warning(f"🔌 Redis connection error during cache clear: {e}")
                clear_success = False
            except redis.TimeoutError as e:
                logger.warning(f"⏰ Redis timeout during cache clear: {e}")
                clear_success = False
            except Exception as e:
                logger.error(f"❌ Unexpected Redis error during cache clear: {e}")
                clear_success = False

        # Always clear memory cache
        try:
            cache_size = len(self.memory_cache)
            self.memory_cache.clear()
            logger.info(f"🧠 Memory cache cleared: {cache_size} items removed")
        except Exception as e:
            logger.error(f"❌ Failed to clear memory cache: {e}")
            clear_success = False

        return clear_success

    def stats(self) -> dict:
        """Get cache statistics"""
        if self.mode == "redis" and self.client:
            try:
                info = self.client.info("stats")
                return {
                    "mode": "redis",
                    "total_commands_processed": info.get("total_commands_processed", 0),
                }
            except Exception:
                return {"mode": "redis", "status": "error"}
        return {"mode": "memory", "size": len(self.memory_cache)}


redis_cache = RedisCache()
