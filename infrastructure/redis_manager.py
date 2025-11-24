from dataclasses import asdict, dataclass
from datetime import datetime
import hashlib
import json
import logging
import pickle
import time
from typing import Any

import redis.asyncio as redis
from redis.asyncio import ConnectionPool
from redis.exceptions import ConnectionError, RedisError, TimeoutError


"""
Enterprise Redis Manager - High Performance Caching & Session Management
Implements connection pooling, session management, and cache invalidation strategies
Target: <50ms response times, 99.9% cache hit ratio
"""

logger = logging.getLogger(__name__)


@dataclass
class CacheMetrics:
    """Cache performance metrics"""

    hits: int = 0
    misses: int = 0
    total_requests: int = 0
    avg_response_time: float = 0.0
    last_updated: datetime = None

    @property
    def hit_ratio(self) -> float:
        """Calculate cache hit ratio"""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": self.total_requests,
            "hit_ratio": self.hit_ratio,
            "avg_response_time": self.avg_response_time,
            "last_updated": (self.last_updated.isoformat() if self.last_updated else None),
        }


@dataclass
class SessionData:
    """Session data structure"""

    user_id: str
    username: str
    email: str
    role: str
    permissions: list[str]
    created_at: datetime
    last_accessed: datetime
    ip_address: str
    user_agent: str
    fashion_preferences: dict[str, Any] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for Redis storage"""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["last_accessed"] = self.last_accessed.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionData":
        """Create from dictionary"""
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["last_accessed"] = datetime.fromisoformat(data["last_accessed"])
        return cls(**data)


class RedisManager:
    """Enterprise Redis Manager with connection pooling and advanced features"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: str | None = None,
        db: int = 0,
        max_connections: int = 20,
        min_connections: int = 10,
        socket_timeout: float = 5.0,
        socket_connect_timeout: float = 5.0,
        retry_on_timeout: bool = True,
        health_check_interval: int = 30,
    ):
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.max_connections = max_connections
        self.min_connections = min_connections

        # Create connection pool
        self.pool = ConnectionPool(
            host=host,
            port=port,
            password=password,
            db=db,
            max_connections=max_connections,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            retry_on_timeout=retry_on_timeout,
            health_check_interval=health_check_interval,
        )

        self.redis_client = redis.Redis(connection_pool=self.pool)
        self.metrics = CacheMetrics()
        self.is_connected = False

        # Cache configuration
        self.default_ttl = 3600  # 1 hour
        self.session_ttl = 86400  # 24 hours
        self.max_key_length = 250

        # Fashion industry specific cache prefixes
        self.cache_prefixes = {
            "session": "sess:",
            "user": "user:",
            "fashion_trends": "trends:",
            "inventory": "inv:",
            "analytics": "analytics:",
            "recommendations": "rec:",
            "api_cache": "api:",
            "ml_models": "ml:",
            "notifications": "notif:",
        }

        logger.info(f"Redis Manager initialized - Pool: {min_connections}-{max_connections} connections")

    async def connect(self) -> bool:
        """Establish Redis connection and verify connectivity"""
        try:
            await self.redis_client.ping()
            self.is_connected = True

            # Initialize metrics
            self.metrics.last_updated = datetime.now()

            logger.info(f"✅ Redis connected: {self.host}:{self.port} (DB: {self.db})")
            return True

        except (ConnectionError, TimeoutError) as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """Close Redis connection and cleanup"""
        try:
            await self.redis_client.close()
            self.is_connected = False
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")

    def _generate_key(self, prefix: str, identifier: str) -> str:
        """Generate standardized cache key"""
        key = f"{self.cache_prefixes.get(prefix, prefix)}{identifier}"

        # Ensure key length doesn't exceed Redis limits
        if len(key) > self.max_key_length:
            # Use hash for long keys
            hash_suffix = hashlib.sha256(key.encode()).hexdigest()[:8]
            key = key[: self.max_key_length - 9] + f":{hash_suffix}"

        return key

    async def _record_metrics(self, operation_time: float, hit: bool):
        """Record cache performance metrics"""
        self.metrics.total_requests += 1

        if hit:
            self.metrics.hits += 1
        else:
            self.metrics.misses += 1

        # Update average response time
        if self.metrics.avg_response_time == 0:
            self.metrics.avg_response_time = operation_time
        else:
            self.metrics.avg_response_time = (
                self.metrics.avg_response_time * (self.metrics.total_requests - 1) + operation_time
            ) / self.metrics.total_requests

        self.metrics.last_updated = datetime.now()

    async def set(self, key: str, value: Any, ttl: int | None = None, prefix: str = "api_cache") -> bool:
        """Set cache value with optional TTL"""
        start_time = time.time()

        try:
            cache_key = self._generate_key(prefix, key)
            ttl = ttl or self.default_ttl

            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            elif isinstance(value, str):
                serialized_value = value
            else:
                serialized_value = pickle.dumps(value)

            await self.redis_client.setex(cache_key, ttl, serialized_value)

            operation_time = (time.time() - start_time) * 1000  # Convert to ms
            await self._record_metrics(operation_time, False)  # Set is not a hit

            logger.debug(f"Cache SET: {cache_key} (TTL: {ttl}s, Time: {operation_time:.2f}ms)")
            return True

        except RedisError as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False

    async def get(self, key: str, prefix: str = "api_cache", deserialize_json: bool = True) -> Any | None:
        """Get cache value"""
        start_time = time.time()

        try:
            cache_key = self._generate_key(prefix, key)
            value = await self.redis_client.get(cache_key)

            operation_time = (time.time() - start_time) * 1000  # Convert to ms

            if value is None:
                await self._record_metrics(operation_time, False)  # Cache miss
                logger.debug(f"Cache MISS: {cache_key} (Time: {operation_time:.2f}ms)")
                return None

            await self._record_metrics(operation_time, True)  # Cache hit

            # Deserialize value
            try:
                if deserialize_json:
                    return json.loads(value)
                else:
                    return value.decode("utf-8")
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Try pickle deserialization
                try:
                    return pickle.loads(value)
                except (pickle.PickleError, TypeError, ValueError) as e:
                    logger.debug(f"Pickle deserialization failed for key {key}: {e}")
                    return value.decode("utf-8")

        except RedisError as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            await self._record_metrics((time.time() - start_time) * 1000, False)
            return None

    async def delete(self, key: str, prefix: str = "api_cache") -> bool:
        """Delete cache key"""
        try:
            cache_key = self._generate_key(prefix, key)
            result = await self.redis_client.delete(cache_key)
            logger.debug(f"Cache DELETE: {cache_key} (Result: {result})")
            return result > 0
        except RedisError as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False

    async def exists(self, key: str, prefix: str = "api_cache") -> bool:
        """Check if key exists"""
        try:
            cache_key = self._generate_key(prefix, key)
            return await self.redis_client.exists(cache_key) > 0
        except RedisError as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False

    async def expire(self, key: str, ttl: int, prefix: str = "api_cache") -> bool:
        """Set expiration for existing key"""
        try:
            cache_key = self._generate_key(prefix, key)
            return await self.redis_client.expire(cache_key, ttl)
        except RedisError as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
            return False

    async def invalidate_pattern(self, pattern: str, prefix: str = "api_cache") -> int:
        """Invalidate keys matching pattern"""
        try:
            cache_pattern = self._generate_key(prefix, pattern)
            keys = await self.redis_client.keys(cache_pattern)

            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"Cache invalidation: {deleted} keys deleted for pattern {cache_pattern}")
                return deleted

            return 0

        except RedisError as e:
            logger.error(f"Redis pattern invalidation error for {pattern}: {e}")
            return 0

    # Session Management Methods
    async def create_session(self, session_id: str, session_data: SessionData) -> bool:
        """Create user session with 24-hour TTL"""
        try:
            session_key = self._generate_key("session", session_id)
            session_json = json.dumps(session_data.to_dict())

            await self.redis_client.setex(session_key, self.session_ttl, session_json)

            # Also store user-to-session mapping
            user_session_key = self._generate_key("user", f"{session_data.user_id}:session")
            await self.redis_client.setex(user_session_key, self.session_ttl, session_id)

            logger.info(f"Session created: {session_id} for user {session_data.user_id}")
            return True

        except RedisError as e:
            logger.error(f"Session creation error: {e}")
            return False

    async def get_session(self, session_id: str) -> SessionData | None:
        """Get session data"""
        try:
            session_key = self._generate_key("session", session_id)
            session_json = await self.redis_client.get(session_key)

            if session_json:
                session_dict = json.loads(session_json)
                return SessionData.from_dict(session_dict)

            return None

        except (RedisError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"Session retrieval error: {e}")
            return None

    async def update_session_access(self, session_id: str) -> bool:
        """Update session last accessed time"""
        session = await self.get_session(session_id)
        if session:
            session.last_accessed = datetime.now()
            return await self.create_session(session_id, session)
        return False

    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        try:
            session = await self.get_session(session_id)
            if session:
                # Delete session
                session_key = self._generate_key("session", session_id)
                await self.redis_client.delete(session_key)

                # Delete user-to-session mapping
                user_session_key = self._generate_key("user", f"{session.user_id}:session")
                await self.redis_client.delete(user_session_key)

                logger.info(f"Session deleted: {session_id}")
                return True

            return False

        except RedisError as e:
            logger.error(f"Session deletion error: {e}")
            return False

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions (automatic with Redis TTL)"""
        # Redis automatically handles TTL cleanup, but we can get stats
        try:
            session_pattern = self._generate_key("session", "*")
            active_sessions = await self.redis_client.keys(session_pattern)
            logger.info(f"Active sessions: {len(active_sessions)}")
            return len(active_sessions)
        except RedisError as e:
            logger.error(f"Session cleanup error: {e}")
            return 0

    async def get_metrics(self) -> dict[str, Any]:
        """Get cache performance metrics"""
        pool_stats = {
            "max_connections": self.max_connections,
            "created_connections": self.pool.created_connections,
            "available_connections": len(self.pool._available_connections),
            "in_use_connections": len(self.pool._in_use_connections),
        }

        return {
            "cache_metrics": self.metrics.to_dict(),
            "connection_pool": pool_stats,
            "is_connected": self.is_connected,
            "redis_info": {"host": self.host, "port": self.port, "db": self.db},
        }

    async def health_check(self) -> dict[str, Any]:
        """Comprehensive health check"""
        start_time = time.time()

        try:
            # Test basic connectivity
            await self.redis_client.ping()

            # Test set/get operation
            test_key = "health_check_test"
            test_value = {"timestamp": datetime.now().isoformat(), "test": True}

            await self.set(test_key, test_value, ttl=60)
            await self.get(test_key)
            await self.delete(test_key)

            response_time = (time.time() - start_time) * 1000

            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "connectivity": True,
                "operations": "working",
                "target_response_time": "<50ms",
                "meets_target": response_time < 50,
                "metrics": await self.get_metrics(),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connectivity": False,
                "response_time_ms": (time.time() - start_time) * 1000,
            }


# Global Redis manager instance
redis_manager = RedisManager()
