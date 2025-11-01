        import redis.asyncio as redis
from datetime import datetime, timedelta
import json

from functools import wraps
from typing import Any, Dict, Optional, Union
import asyncio
import hashlib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheManager:
    """High-performance caching system with TTL and memory management."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.cache = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.access_times = {}
        self.hit_count = 0
        self.miss_count = 0

    def _generate_key(self, key: Union[str, Dict]) -> str:
        """Generate a consistent cache key."""
        if isinstance(key, dict):
            key_str = json.dumps(key, sort_keys=True)
        else:
            key_str = str(key)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def _is_expired(self, timestamp: datetime, ttl: int) -> bool:
        """Check if cache entry is expired."""
        return datetime.now() - timestamp > timedelta(seconds=ttl)

    def _evict_lru(self):
        """Evict least recently used items when cache is full."""
        if len(self.cache) >= self.max_size:
            # Remove oldest accessed item
            oldest_key = min(
                self.access_times.keys(), key=lambda k: self.access_times[k]
            )
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
            logger.info(f"Evicted LRU cache entry: {oldest_key}")

    def get(self, key: Union[str, Dict], default: Any = None) -> Any:
        """Get value from cache."""
        cache_key = self._generate_key(key)

        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if not self._is_expired(entry["timestamp"], entry["ttl"]):
                self.access_times[cache_key] = datetime.now()
                self.hit_count += 1
                logger.debug(f"Cache hit for key: {cache_key}")
                return entry["value"]
            else:
                # Remove expired entry
                del self.cache[cache_key]
                if cache_key in self.access_times:
                    del self.access_times[cache_key]

        self.miss_count += 1
        logger.debug(f"Cache miss for key: {cache_key}")
        return default

    def set(self, key: Union[str, Dict], value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        cache_key = self._generate_key(key)
        ttl = ttl or self.default_ttl

        # Evict if necessary
        if len(self.cache) >= self.max_size and cache_key not in self.cache:
            self._evict_lru()

        self.cache[cache_key] = {
            "value": value,
            "timestamp": datetime.now(),
            "ttl": ttl,
        }
        self.access_times[cache_key] = datetime.now()
        logger.debug(f"Cached value for key: {cache_key}")

    def delete(self, key: Union[str, Dict]) -> bool:
        """Delete key from cache."""
        cache_key = self._generate_key(key)
        if cache_key in self.cache:
            del self.cache[cache_key]
            if cache_key in self.access_times:
                del self.access_times[cache_key]
            logger.debug(f"Deleted cache entry: {cache_key}")
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.access_times.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests,
        }

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items."""
        expired_keys = []

        for key, entry in self.cache.items():
            if self._is_expired(entry["timestamp"], entry["ttl"]):
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)

# Global cache instance
cache_manager = CacheManager(max_size=2000, default_ttl=600)  # 10 minutes default TTL

def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function results."""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = {
                "func": func.__name__,
                "args": args,
                "kwargs": kwargs,
                "prefix": key_prefix,
            }

            # Try to get from cache
            result = cache_manager.get(cache_key)
            if result is not None:
                return result

            # Execute function and cache result
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            cache_manager.set(cache_key, result, ttl)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = {
                "func": func.__name__,
                "args": args,
                "kwargs": kwargs,
                "prefix": key_prefix,
            }

            # Try to get from cache
            result = cache_manager.get(cache_key)
            if result is not None:
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator

class ConnectionPool:
    """Connection pooling for database and external services."""

    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.connections = asyncio.Queue(maxsize=max_connections)
        self.active_connections = 0
        self.connection_stats = {"created": 0, "reused": 0, "closed": 0, "errors": 0}

    async def get_connection(self):
        """Get a connection from the pool."""
        try:
            if not self.connections.empty():
                connection = await self.connections.get()
                self.connection_stats["reused"] += 1
                logger.debug("Reused connection from pool")
                return connection
            elif self.active_connections < self.max_connections:
                # Create new connection
                connection = await self._create_connection()
                self.active_connections += 1
                self.connection_stats["created"] += 1
                logger.debug("Created new connection")
                return connection
            else:
                # Wait for available connection
                connection = await self.connections.get()
                self.connection_stats["reused"] += 1
                logger.debug("Waited for and got connection from pool")
                return connection
        except Exception as e:
            self.connection_stats["errors"] += 1
            logger.error(f"Error getting connection: {e}")
            raise

    async def return_connection(self, connection):
        """Return a connection to the pool."""
        try:
            if connection and not connection.is_closed():
                await self.connections.put(connection)
                logger.debug("Returned connection to pool")
            else:
                self.active_connections -= 1
                self.connection_stats["closed"] += 1
                logger.debug("Closed invalid connection")
        except Exception as e:
            self.connection_stats["errors"] += 1
            logger.error(f"Error returning connection: {e}")

    async def _create_connection(self):
        """Create a new Redis connection with enterprise configuration."""

        try:
            connection = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )

            # Test the connection
            await connection.ping()
            logger.info("✅ Redis connection created successfully")
            return connection

        except Exception as e:
            logger.error(f"❌ Failed to create Redis connection: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        return {
            "max_connections": self.max_connections,
            "active_connections": self.active_connections,
            "available_connections": self.connections.qsize(),
            "stats": self.connection_stats,
        }

# Background task for cache cleanup
async def cache_cleanup_task():
    """Background task to clean up expired cache entries."""
    while True:
        try:
            await asyncio.sleep(300)  # TODO: Move to config  # Run every 5 minutes
            cleaned = cache_manager.cleanup_expired()
            if cleaned > 0:
                logger.info(f"Cache cleanup: removed {cleaned} expired entries")
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")

# Start background cleanup task
def start_cache_cleanup():
    """Start the background cache cleanup task."""
    try:
        asyncio.create_task(cache_cleanup_task())
        logger.info("Started cache cleanup background task")
    except RuntimeError as e:
        if "no running event loop" in str(e):
            logger.info(
                "No event loop available, cache cleanup will start when server starts"
            )
        else:
            raise
