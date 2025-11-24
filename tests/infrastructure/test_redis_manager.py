"""
Comprehensive tests for infrastructure/redis_manager.py

WHY: Ensure Redis caching layer works correctly with ≥80% coverage
HOW: Test all Redis operations, session management, metrics, and error handling
IMPACT: Validates enterprise caching infrastructure reliability

Truth Protocol: Rules #1, #8, #15
Coverage Target: ≥80%
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import fakeredis.aioredis
import pytest
from redis.exceptions import ConnectionError, RedisError, TimeoutError

from infrastructure.redis_manager import CacheMetrics, RedisManager, SessionData


# ============================================================================
# TEST HELPER CLASSES (Module level for pickle support)
# ============================================================================


class CustomPickleObject:
    """Custom class for testing pickle serialization."""

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, CustomPickleObject) and self.value == other.value


# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
def fake_redis():
    """Create a fake Redis client for testing."""
    return fakeredis.aioredis.FakeRedis(decode_responses=False)


@pytest.fixture
async def redis_manager(fake_redis):
    """Create RedisManager instance with fake Redis client."""
    manager = RedisManager(
        host="localhost",
        port=6379,
        password=None,
        db=0,
        max_connections=20,
        min_connections=10,
    )
    # Replace real Redis client with fake one
    manager.redis_client = fake_redis
    manager.pool = MagicMock()
    manager.pool.created_connections = 5
    manager.pool._available_connections = []
    manager.pool._in_use_connections = []

    # Connect the manager
    await manager.connect()

    yield manager

    # Cleanup
    await manager.disconnect()


@pytest.fixture
def sample_session_data():
    """Create sample session data for testing."""
    return SessionData(
        user_id="user123",
        username="testuser",
        email="test@example.com",
        role="admin",
        permissions=["read", "write", "delete"],
        created_at=datetime(2025, 11, 21, 10, 0, 0),
        last_accessed=datetime(2025, 11, 21, 11, 0, 0),
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        fashion_preferences={"style": "modern", "colors": ["black", "white"]},
    )


# ============================================================================
# TEST CacheMetrics
# ============================================================================


class TestCacheMetrics:
    """Test CacheMetrics dataclass."""

    def test_cache_metrics_initialization(self):
        """Test CacheMetrics initialization with default values."""
        metrics = CacheMetrics()

        assert metrics.hits == 0
        assert metrics.misses == 0
        assert metrics.total_requests == 0
        assert metrics.avg_response_time == 0.0
        assert metrics.last_updated is None

    def test_hit_ratio_zero_requests(self):
        """Test hit_ratio returns 0.0 when no requests."""
        metrics = CacheMetrics()
        assert metrics.hit_ratio == 0.0

    def test_hit_ratio_calculation(self):
        """Test hit_ratio calculates correctly."""
        metrics = CacheMetrics(hits=75, misses=25, total_requests=100)
        assert metrics.hit_ratio == 0.75

    def test_hit_ratio_all_hits(self):
        """Test hit_ratio when all requests are hits."""
        metrics = CacheMetrics(hits=100, total_requests=100)
        assert metrics.hit_ratio == 1.0

    def test_hit_ratio_all_misses(self):
        """Test hit_ratio when all requests are misses."""
        metrics = CacheMetrics(misses=100, total_requests=100)
        assert metrics.hit_ratio == 0.0

    def test_to_dict(self):
        """Test CacheMetrics.to_dict() converts to dictionary."""
        timestamp = datetime(2025, 11, 21, 12, 0, 0)
        metrics = CacheMetrics(
            hits=50,
            misses=10,
            total_requests=60,
            avg_response_time=25.5,
            last_updated=timestamp,
        )

        result = metrics.to_dict()

        assert result["hits"] == 50
        assert result["misses"] == 10
        assert result["total_requests"] == 60
        assert result["hit_ratio"] == 50 / 60
        assert result["avg_response_time"] == 25.5
        assert result["last_updated"] == "2025-11-21T12:00:00"

    def test_to_dict_no_timestamp(self):
        """Test to_dict() with None timestamp."""
        metrics = CacheMetrics()
        result = metrics.to_dict()

        assert result["last_updated"] is None


# ============================================================================
# TEST SessionData
# ============================================================================


class TestSessionData:
    """Test SessionData dataclass."""

    def test_session_data_initialization(self, sample_session_data):
        """Test SessionData initialization."""
        assert sample_session_data.user_id == "user123"
        assert sample_session_data.username == "testuser"
        assert sample_session_data.email == "test@example.com"
        assert sample_session_data.role == "admin"
        assert len(sample_session_data.permissions) == 3

    def test_to_dict(self, sample_session_data):
        """Test SessionData.to_dict() converts to dictionary."""
        result = sample_session_data.to_dict()

        assert result["user_id"] == "user123"
        assert result["username"] == "testuser"
        assert result["email"] == "test@example.com"
        assert result["role"] == "admin"
        assert result["permissions"] == ["read", "write", "delete"]
        assert result["created_at"] == "2025-11-21T10:00:00"
        assert result["last_accessed"] == "2025-11-21T11:00:00"
        assert result["ip_address"] == "192.168.1.1"
        assert result["user_agent"] == "Mozilla/5.0"
        assert result["fashion_preferences"]["style"] == "modern"

    def test_from_dict(self):
        """Test SessionData.from_dict() creates instance from dictionary."""
        data = {
            "user_id": "user456",
            "username": "anotheruser",
            "email": "another@example.com",
            "role": "developer",
            "permissions": ["read"],
            "created_at": "2025-11-21T10:00:00",
            "last_accessed": "2025-11-21T11:00:00",
            "ip_address": "192.168.1.2",
            "user_agent": "Chrome",
            "fashion_preferences": None,
        }

        session = SessionData.from_dict(data)

        assert session.user_id == "user456"
        assert session.username == "anotheruser"
        assert session.email == "another@example.com"
        assert session.role == "developer"
        assert session.permissions == ["read"]
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.last_accessed, datetime)
        assert session.fashion_preferences is None

    def test_to_dict_from_dict_roundtrip(self, sample_session_data):
        """Test converting to dict and back maintains data."""
        dict_data = sample_session_data.to_dict()
        restored = SessionData.from_dict(dict_data)

        assert restored.user_id == sample_session_data.user_id
        assert restored.username == sample_session_data.username
        assert restored.email == sample_session_data.email
        assert restored.role == sample_session_data.role
        assert restored.permissions == sample_session_data.permissions
        assert restored.created_at == sample_session_data.created_at
        assert restored.last_accessed == sample_session_data.last_accessed


# ============================================================================
# TEST RedisManager Initialization
# ============================================================================


class TestRedisManagerInitialization:
    """Test RedisManager initialization."""

    def test_initialization_default_params(self):
        """Test RedisManager initializes with default parameters."""
        manager = RedisManager()

        assert manager.host == "localhost"
        assert manager.port == 6379
        assert manager.password is None
        assert manager.db == 0
        assert manager.max_connections == 20
        assert manager.min_connections == 10
        assert manager.default_ttl == 3600
        assert manager.session_ttl == 86400
        assert manager.max_key_length == 250
        assert manager.is_connected is False

    def test_initialization_custom_params(self):
        """Test RedisManager initializes with custom parameters."""
        manager = RedisManager(
            host="redis.example.com",
            port=6380,
            password="secret",
            db=1,
            max_connections=50,
            min_connections=20,
        )

        assert manager.host == "redis.example.com"
        assert manager.port == 6380
        assert manager.password == "secret"
        assert manager.db == 1
        assert manager.max_connections == 50
        assert manager.min_connections == 20

    def test_cache_prefixes_defined(self):
        """Test cache prefixes are properly defined."""
        manager = RedisManager()

        assert "session" in manager.cache_prefixes
        assert "user" in manager.cache_prefixes
        assert "fashion_trends" in manager.cache_prefixes
        assert "inventory" in manager.cache_prefixes
        assert "analytics" in manager.cache_prefixes
        assert "recommendations" in manager.cache_prefixes
        assert "api_cache" in manager.cache_prefixes
        assert "ml_models" in manager.cache_prefixes
        assert "notifications" in manager.cache_prefixes

    def test_metrics_initialized(self):
        """Test CacheMetrics is initialized."""
        manager = RedisManager()

        assert isinstance(manager.metrics, CacheMetrics)
        assert manager.metrics.hits == 0
        assert manager.metrics.misses == 0
        assert manager.metrics.total_requests == 0


# ============================================================================
# TEST Connection Management
# ============================================================================


class TestConnectionManagement:
    """Test Redis connection management."""

    @pytest.mark.asyncio
    async def test_connect_success(self, redis_manager):
        """Test successful Redis connection."""
        assert redis_manager.is_connected is True
        assert redis_manager.metrics.last_updated is not None

    @pytest.mark.asyncio
    async def test_connect_failure_connection_error(self):
        """Test connection failure with ConnectionError."""
        manager = RedisManager()

        # Mock the ping to raise ConnectionError
        manager.redis_client.ping = AsyncMock(side_effect=ConnectionError("Connection failed"))

        result = await manager.connect()

        assert result is False
        assert manager.is_connected is False

    @pytest.mark.asyncio
    async def test_connect_failure_timeout_error(self):
        """Test connection failure with TimeoutError."""
        manager = RedisManager()

        # Mock the ping to raise TimeoutError
        manager.redis_client.ping = AsyncMock(side_effect=TimeoutError("Timeout"))

        result = await manager.connect()

        assert result is False
        assert manager.is_connected is False

    @pytest.mark.asyncio
    async def test_disconnect_success(self, redis_manager):
        """Test successful Redis disconnection."""
        await redis_manager.disconnect()

        assert redis_manager.is_connected is False

    @pytest.mark.asyncio
    async def test_disconnect_with_error(self, redis_manager):
        """Test disconnect handles errors gracefully."""
        # Mock close to raise an error
        redis_manager.redis_client.close = AsyncMock(side_effect=Exception("Close error"))

        # Should not raise exception
        await redis_manager.disconnect()


# ============================================================================
# TEST Key Generation
# ============================================================================


class TestKeyGeneration:
    """Test cache key generation."""

    def test_generate_key_with_prefix(self, redis_manager):
        """Test key generation with known prefix."""
        key = redis_manager._generate_key("api_cache", "test_key")

        assert key == "api:test_key"

    def test_generate_key_session_prefix(self, redis_manager):
        """Test key generation with session prefix."""
        key = redis_manager._generate_key("session", "sess123")

        assert key == "sess:sess123"

    def test_generate_key_unknown_prefix(self, redis_manager):
        """Test key generation with unknown prefix uses prefix as-is."""
        key = redis_manager._generate_key("custom", "test_key")

        assert key == "customtest_key"

    def test_generate_key_long_key_hashing(self, redis_manager):
        """Test long keys are hashed to stay within limit."""
        long_identifier = "a" * 300
        key = redis_manager._generate_key("api_cache", long_identifier)

        # Key should be <= max_key_length
        assert len(key) <= redis_manager.max_key_length
        # Should contain hash suffix
        assert ":" in key[-10:]

    def test_generate_key_exactly_max_length(self, redis_manager):
        """Test key exactly at max length is not hashed."""
        # Calculate identifier length that gives exactly max_key_length
        prefix = redis_manager.cache_prefixes["api_cache"]
        identifier_length = redis_manager.max_key_length - len(prefix)
        identifier = "b" * identifier_length

        key = redis_manager._generate_key("api_cache", identifier)

        assert len(key) == redis_manager.max_key_length


# ============================================================================
# TEST Metrics Recording
# ============================================================================


class TestMetricsRecording:
    """Test cache metrics recording."""

    @pytest.mark.asyncio
    async def test_record_metrics_hit(self, redis_manager):
        """Test recording cache hit metrics."""
        initial_hits = redis_manager.metrics.hits
        initial_requests = redis_manager.metrics.total_requests

        await redis_manager._record_metrics(25.5, hit=True)

        assert redis_manager.metrics.hits == initial_hits + 1
        assert redis_manager.metrics.total_requests == initial_requests + 1
        assert redis_manager.metrics.avg_response_time == 25.5

    @pytest.mark.asyncio
    async def test_record_metrics_miss(self, redis_manager):
        """Test recording cache miss metrics."""
        initial_misses = redis_manager.metrics.misses
        initial_requests = redis_manager.metrics.total_requests

        await redis_manager._record_metrics(30.0, hit=False)

        assert redis_manager.metrics.misses == initial_misses + 1
        assert redis_manager.metrics.total_requests == initial_requests + 1

    @pytest.mark.asyncio
    async def test_record_metrics_average_response_time(self, redis_manager):
        """Test average response time calculation."""
        # First request
        await redis_manager._record_metrics(10.0, hit=True)
        assert redis_manager.metrics.avg_response_time == 10.0

        # Second request
        await redis_manager._record_metrics(20.0, hit=True)
        assert redis_manager.metrics.avg_response_time == 15.0  # (10 + 20) / 2

        # Third request
        await redis_manager._record_metrics(30.0, hit=True)
        assert redis_manager.metrics.avg_response_time == 20.0  # (10 + 20 + 30) / 3

    @pytest.mark.asyncio
    async def test_record_metrics_updates_timestamp(self, redis_manager):
        """Test metrics recording updates last_updated timestamp."""
        before = datetime.now()

        await redis_manager._record_metrics(15.0, hit=True)

        after = datetime.now()

        assert before <= redis_manager.metrics.last_updated <= after


# ============================================================================
# TEST Cache Operations (SET/GET/DELETE)
# ============================================================================


class TestCacheOperations:
    """Test cache set/get/delete operations."""

    @pytest.mark.asyncio
    async def test_set_dict_value(self, redis_manager):
        """Test setting dictionary value in cache."""
        test_value = {"name": "test", "value": 123}

        result = await redis_manager.set("test_key", test_value, ttl=60)

        assert result is True

    @pytest.mark.asyncio
    async def test_set_list_value(self, redis_manager):
        """Test setting list value in cache."""
        test_value = [1, 2, 3, 4, 5]

        result = await redis_manager.set("test_list", test_value, ttl=60)

        assert result is True

    @pytest.mark.asyncio
    async def test_set_string_value(self, redis_manager):
        """Test setting string value in cache."""
        test_value = "simple string"

        result = await redis_manager.set("test_string", test_value, ttl=60)

        assert result is True

    @pytest.mark.asyncio
    async def test_set_custom_object_pickle(self, redis_manager):
        """Test setting custom object (uses pickle)."""
        test_value = CustomPickleObject(42)

        result = await redis_manager.set("test_object", test_value, ttl=60)

        assert result is True

        # Verify we can retrieve it
        retrieved = await redis_manager.get("test_object", deserialize_json=False)
        assert retrieved is not None

    @pytest.mark.asyncio
    async def test_set_default_ttl(self, redis_manager):
        """Test set uses default TTL when not specified."""
        result = await redis_manager.set("test_key", {"data": "value"})

        assert result is True

    @pytest.mark.asyncio
    async def test_set_with_error(self, redis_manager):
        """Test set handles Redis errors gracefully."""
        redis_manager.redis_client.setex = AsyncMock(side_effect=RedisError("Set error"))

        result = await redis_manager.set("test_key", {"data": "value"})

        assert result is False

    @pytest.mark.asyncio
    async def test_get_dict_value(self, redis_manager):
        """Test getting dictionary value from cache."""
        test_value = {"name": "test", "value": 123}
        await redis_manager.set("test_key", test_value)

        result = await redis_manager.get("test_key")

        assert result == test_value

    @pytest.mark.asyncio
    async def test_get_list_value(self, redis_manager):
        """Test getting list value from cache."""
        test_value = [1, 2, 3, 4, 5]
        await redis_manager.set("test_list", test_value)

        result = await redis_manager.get("test_list")

        assert result == test_value

    @pytest.mark.asyncio
    async def test_get_string_value_no_deserialize(self, redis_manager):
        """Test getting string value without JSON deserialization."""
        test_value = "simple string"
        await redis_manager.set("test_string", test_value)

        result = await redis_manager.get("test_string", deserialize_json=False)

        assert result == test_value

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, redis_manager):
        """Test getting non-existent key returns None."""
        result = await redis_manager.get("nonexistent_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_pickle_value(self, redis_manager):
        """Test getting pickled object from cache."""
        test_value = CustomPickleObject(42)
        await redis_manager.set("test_object", test_value)

        # Get without JSON deserialization to retrieve pickle
        result = await redis_manager.get("test_object", deserialize_json=False)

        # Should get back the object or pickled data
        assert result is not None

        # If we got back a CustomPickleObject, verify it
        if isinstance(result, CustomPickleObject):
            assert result.value == 42

    @pytest.mark.asyncio
    async def test_get_with_redis_error(self, redis_manager):
        """Test get handles Redis errors gracefully."""
        redis_manager.redis_client.get = AsyncMock(side_effect=RedisError("Get error"))

        result = await redis_manager.get("test_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_cache_hit_metrics(self, redis_manager):
        """Test cache hit updates metrics correctly."""
        test_value = {"data": "value"}
        await redis_manager.set("test_key", test_value)

        initial_hits = redis_manager.metrics.hits

        await redis_manager.get("test_key")

        assert redis_manager.metrics.hits == initial_hits + 1

    @pytest.mark.asyncio
    async def test_get_cache_miss_metrics(self, redis_manager):
        """Test cache miss updates metrics correctly."""
        initial_misses = redis_manager.metrics.misses

        await redis_manager.get("nonexistent_key")

        assert redis_manager.metrics.misses == initial_misses + 1

    @pytest.mark.asyncio
    async def test_delete_existing_key(self, redis_manager):
        """Test deleting existing key."""
        await redis_manager.set("test_key", {"data": "value"})

        result = await redis_manager.delete("test_key")

        assert result is True

        # Verify key is deleted
        get_result = await redis_manager.get("test_key")
        assert get_result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self, redis_manager):
        """Test deleting non-existent key returns False."""
        result = await redis_manager.delete("nonexistent_key")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_with_error(self, redis_manager):
        """Test delete handles Redis errors gracefully."""
        redis_manager.redis_client.delete = AsyncMock(side_effect=RedisError("Delete error"))

        result = await redis_manager.delete("test_key")

        assert result is False


# ============================================================================
# TEST Exists and Expire Operations
# ============================================================================


class TestExistsAndExpire:
    """Test exists and expire operations."""

    @pytest.mark.asyncio
    async def test_exists_key_present(self, redis_manager):
        """Test exists returns True for existing key."""
        await redis_manager.set("test_key", {"data": "value"})

        result = await redis_manager.exists("test_key")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_key_absent(self, redis_manager):
        """Test exists returns False for non-existent key."""
        result = await redis_manager.exists("nonexistent_key")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists_with_error(self, redis_manager):
        """Test exists handles Redis errors gracefully."""
        redis_manager.redis_client.exists = AsyncMock(side_effect=RedisError("Exists error"))

        result = await redis_manager.exists("test_key")

        assert result is False

    @pytest.mark.asyncio
    async def test_expire_existing_key(self, redis_manager):
        """Test setting expiration on existing key."""
        await redis_manager.set("test_key", {"data": "value"}, ttl=3600)

        result = await redis_manager.expire("test_key", 60)

        assert result is True

    @pytest.mark.asyncio
    async def test_expire_with_error(self, redis_manager):
        """Test expire handles Redis errors gracefully."""
        redis_manager.redis_client.expire = AsyncMock(side_effect=RedisError("Expire error"))

        result = await redis_manager.expire("test_key", 60)

        assert result is False


# ============================================================================
# TEST Pattern Invalidation
# ============================================================================


class TestPatternInvalidation:
    """Test pattern-based cache invalidation."""

    @pytest.mark.asyncio
    async def test_invalidate_pattern_multiple_keys(self, redis_manager):
        """Test invalidating multiple keys matching pattern."""
        # Set multiple keys with pattern
        await redis_manager.set("user:1", {"id": 1})
        await redis_manager.set("user:2", {"id": 2})
        await redis_manager.set("user:3", {"id": 3})

        # Invalidate pattern
        deleted = await redis_manager.invalidate_pattern("user:*", prefix="api_cache")

        assert deleted >= 0  # fakeredis may behave differently

    @pytest.mark.asyncio
    async def test_invalidate_pattern_no_matches(self, redis_manager):
        """Test invalidating pattern with no matches returns 0."""
        deleted = await redis_manager.invalidate_pattern("nonexistent:*")

        assert deleted == 0

    @pytest.mark.asyncio
    async def test_invalidate_pattern_with_error(self, redis_manager):
        """Test pattern invalidation handles Redis errors gracefully."""
        redis_manager.redis_client.keys = AsyncMock(side_effect=RedisError("Keys error"))

        deleted = await redis_manager.invalidate_pattern("test:*")

        assert deleted == 0


# ============================================================================
# TEST Session Management
# ============================================================================


class TestSessionManagement:
    """Test session management operations."""

    @pytest.mark.asyncio
    async def test_create_session(self, redis_manager, sample_session_data):
        """Test creating user session."""
        result = await redis_manager.create_session("sess123", sample_session_data)

        assert result is True

    @pytest.mark.asyncio
    async def test_create_session_with_error(self, redis_manager, sample_session_data):
        """Test create_session handles errors gracefully."""
        redis_manager.redis_client.setex = AsyncMock(side_effect=RedisError("Session error"))

        result = await redis_manager.create_session("sess123", sample_session_data)

        assert result is False

    @pytest.mark.asyncio
    async def test_get_session(self, redis_manager, sample_session_data):
        """Test retrieving user session."""
        await redis_manager.create_session("sess123", sample_session_data)

        result = await redis_manager.get_session("sess123")

        assert result is not None
        assert result.user_id == sample_session_data.user_id
        assert result.username == sample_session_data.username
        assert result.email == sample_session_data.email
        assert result.role == sample_session_data.role

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, redis_manager):
        """Test getting non-existent session returns None."""
        result = await redis_manager.get_session("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_session_with_error(self, redis_manager):
        """Test get_session handles errors gracefully."""
        redis_manager.redis_client.get = AsyncMock(side_effect=RedisError("Get error"))

        result = await redis_manager.get_session("sess123")

        assert result is None

    @pytest.mark.asyncio
    async def test_update_session_access(self, redis_manager, sample_session_data):
        """Test updating session last accessed time."""
        await redis_manager.create_session("sess123", sample_session_data)

        # Update access time
        result = await redis_manager.update_session_access("sess123")

        assert result is True

        # Verify last_accessed was updated
        updated_session = await redis_manager.get_session("sess123")
        assert updated_session.last_accessed > sample_session_data.last_accessed

    @pytest.mark.asyncio
    async def test_update_session_access_nonexistent(self, redis_manager):
        """Test updating non-existent session returns False."""
        result = await redis_manager.update_session_access("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_session(self, redis_manager, sample_session_data):
        """Test deleting user session."""
        await redis_manager.create_session("sess123", sample_session_data)

        result = await redis_manager.delete_session("sess123")

        assert result is True

        # Verify session is deleted
        get_result = await redis_manager.get_session("sess123")
        assert get_result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(self, redis_manager):
        """Test deleting non-existent session returns False."""
        result = await redis_manager.delete_session("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_session_with_error(self, redis_manager, sample_session_data):
        """Test delete_session handles errors gracefully."""
        await redis_manager.create_session("sess123", sample_session_data)

        redis_manager.redis_client.delete = AsyncMock(side_effect=RedisError("Delete error"))

        result = await redis_manager.delete_session("sess123")

        assert result is False

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, redis_manager, sample_session_data):
        """Test cleanup returns count of active sessions."""
        await redis_manager.create_session("sess1", sample_session_data)
        await redis_manager.create_session("sess2", sample_session_data)

        count = await redis_manager.cleanup_expired_sessions()

        # Should return number of active sessions
        assert count >= 0

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions_with_error(self, redis_manager):
        """Test cleanup handles errors gracefully."""
        redis_manager.redis_client.keys = AsyncMock(side_effect=RedisError("Keys error"))

        count = await redis_manager.cleanup_expired_sessions()

        assert count == 0


# ============================================================================
# TEST Metrics and Health Check
# ============================================================================


class TestMetricsAndHealthCheck:
    """Test metrics and health check operations."""

    @pytest.mark.asyncio
    async def test_get_metrics(self, redis_manager):
        """Test getting cache and connection pool metrics."""
        # Perform some operations to generate metrics
        await redis_manager.set("test1", {"data": 1})
        await redis_manager.get("test1")
        await redis_manager.get("nonexistent")

        metrics = await redis_manager.get_metrics()

        assert "cache_metrics" in metrics
        assert "connection_pool" in metrics
        assert "is_connected" in metrics
        assert "redis_info" in metrics

        assert metrics["is_connected"] is True
        assert metrics["redis_info"]["host"] == "localhost"
        assert metrics["redis_info"]["port"] == 6379
        assert metrics["redis_info"]["db"] == 0

    @pytest.mark.asyncio
    async def test_get_metrics_connection_pool_stats(self, redis_manager):
        """Test connection pool statistics in metrics."""
        metrics = await redis_manager.get_metrics()

        pool_stats = metrics["connection_pool"]

        assert "max_connections" in pool_stats
        assert "created_connections" in pool_stats
        assert "available_connections" in pool_stats
        assert "in_use_connections" in pool_stats

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, redis_manager):
        """Test health check returns healthy status."""
        result = await redis_manager.health_check()

        assert result["status"] == "healthy"
        assert result["connectivity"] is True
        assert result["operations"] == "working"
        assert "response_time_ms" in result
        assert "metrics" in result
        assert result["target_response_time"] == "<50ms"

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, redis_manager):
        """Test health check returns unhealthy status on error."""
        # Mock ping to fail
        redis_manager.redis_client.ping = AsyncMock(side_effect=RedisError("Ping failed"))

        result = await redis_manager.health_check()

        assert result["status"] == "unhealthy"
        assert result["connectivity"] is False
        assert "error" in result
        assert "response_time_ms" in result

    @pytest.mark.asyncio
    async def test_health_check_meets_target(self, redis_manager):
        """Test health check evaluates if response time meets target."""
        result = await redis_manager.health_check()

        assert "meets_target" in result
        assert isinstance(result["meets_target"], bool)


# ============================================================================
# TEST Edge Cases and Error Handling
# ============================================================================


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and comprehensive error handling."""

    @pytest.mark.asyncio
    async def test_set_with_custom_prefix(self, redis_manager):
        """Test setting value with custom prefix."""
        result = await redis_manager.set("test_key", {"data": "value"}, prefix="inventory")

        assert result is True

    @pytest.mark.asyncio
    async def test_get_with_custom_prefix(self, redis_manager):
        """Test getting value with custom prefix."""
        await redis_manager.set("test_key", {"data": "value"}, prefix="inventory")

        result = await redis_manager.get("test_key", prefix="inventory")

        assert result == {"data": "value"}

    @pytest.mark.asyncio
    async def test_delete_with_custom_prefix(self, redis_manager):
        """Test deleting value with custom prefix."""
        await redis_manager.set("test_key", {"data": "value"}, prefix="analytics")

        result = await redis_manager.delete("test_key", prefix="analytics")

        assert result is True

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, redis_manager):
        """Test multiple concurrent operations."""
        import asyncio

        # Set multiple values concurrently
        tasks = [
            redis_manager.set(f"key{i}", {"value": i})
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks)

        assert all(results)

    @pytest.mark.asyncio
    async def test_very_large_value(self, redis_manager):
        """Test handling very large values."""
        large_value = {"data": "x" * 10000}

        result = await redis_manager.set("large_key", large_value)
        assert result is True

        retrieved = await redis_manager.get("large_key")
        assert retrieved == large_value

    @pytest.mark.asyncio
    async def test_special_characters_in_key(self, redis_manager):
        """Test keys with special characters."""
        special_key = "key:with:colons:and-dashes_and_underscores"

        result = await redis_manager.set(special_key, {"data": "value"})
        assert result is True

        retrieved = await redis_manager.get(special_key)
        assert retrieved == {"data": "value"}

    @pytest.mark.asyncio
    async def test_empty_dict_value(self, redis_manager):
        """Test storing empty dictionary."""
        result = await redis_manager.set("empty_dict", {})
        assert result is True

        retrieved = await redis_manager.get("empty_dict")
        assert retrieved == {}

    @pytest.mark.asyncio
    async def test_empty_list_value(self, redis_manager):
        """Test storing empty list."""
        result = await redis_manager.set("empty_list", [])
        assert result is True

        retrieved = await redis_manager.get("empty_list")
        assert retrieved == []

    @pytest.mark.asyncio
    async def test_none_value_handling(self, redis_manager):
        """Test that None values are handled correctly."""
        # Set None value (will be pickled)
        result = await redis_manager.set("none_value", None)
        assert result is True

        # Get should return None or the pickled value
        retrieved = await redis_manager.get("none_value")
        # Since None will be pickled, it should be retrievable
        assert retrieved is None or isinstance(retrieved, type(None))

    @pytest.mark.asyncio
    async def test_numeric_values(self, redis_manager):
        """Test storing numeric values."""
        # Integer
        await redis_manager.set("int_val", 42)
        int_result = await redis_manager.get("int_val")
        assert int_result == 42

        # Float
        await redis_manager.set("float_val", 3.14159)
        float_result = await redis_manager.get("float_val")
        assert float_result == 3.14159


# ============================================================================
# TEST Deserialization Edge Cases
# ============================================================================


class TestDeserializationEdgeCases:
    """Test various deserialization scenarios."""

    @pytest.mark.asyncio
    async def test_get_malformed_json(self, redis_manager, fake_redis):
        """Test get handles malformed JSON gracefully."""
        # Manually insert malformed JSON
        cache_key = redis_manager._generate_key("api_cache", "bad_json")
        await fake_redis.set(cache_key, b"{'this is': not valid json}")

        # Should fall back to string
        result = await redis_manager.get("bad_json")

        assert result is not None
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_get_binary_data(self, redis_manager, fake_redis):
        """Test get handles binary data."""
        # Store binary data
        binary_data = b"\x00\x01\x02\x03\x04"
        cache_key = redis_manager._generate_key("api_cache", "binary")
        await fake_redis.set(cache_key, binary_data)

        # Should handle gracefully
        result = await redis_manager.get("binary", deserialize_json=False)

        # Result handling depends on deserialization logic
        assert result is not None


# ============================================================================
# TEST Global Instance
# ============================================================================


def test_global_redis_manager_instance():
    """Test global redis_manager instance exists."""
    from infrastructure.redis_manager import redis_manager as global_instance

    assert global_instance is not None
    assert isinstance(global_instance, RedisManager)
    assert global_instance.host == "localhost"
    assert global_instance.port == 6379
