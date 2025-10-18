"""
Redis Caching Layer - Distributed caching for scalability
References: Redis Best Practices (redis.io/topics/lru-cache)
"""
import json
import logging
import os
from typing import Any, Optional
import hashlib

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available - using in-memory cache")


class RedisCache:
    """Distributed Redis cache with fallback to in-memory"""

    def __init__(self, host: str = None, port: int = None, db: int = 0, ttl: int = 3600):
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
        return hashlib.md5(key.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
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

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
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

    def delete(self, key: str):
        """Delete cached value"""
        hashed_key = self._hash_key(key)

        if self.mode == "redis" and self.client:
            try:
                self.client.delete(hashed_key)
            except:
                pass
        if hashed_key in self.memory_cache:
            del self.memory_cache[hashed_key]

    def clear(self):
        """Clear all cache"""
        if self.mode == "redis" and self.client:
            try:
                self.client.flushdb()
            except:
                pass
        self.memory_cache.clear()

    def stats(self) -> dict:
        """Get cache statistics"""
        if self.mode == "redis" and self.client:
            try:
                info = self.client.info("stats")
                return {"mode": "redis", "total_commands_processed": info.get("total_commands_processed", 0)}
            except:
                return {"mode": "redis", "status": "error"}
        return {"mode": "memory", "size": len(self.memory_cache)}


redis_cache = RedisCache()
