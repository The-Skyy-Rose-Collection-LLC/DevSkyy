"""
Redis infrastructure tests for DevSkyy platform.

WHY: Validate caching layer connectivity and performance
HOW: Test Redis connections, pub/sub, and cache operations
IMPACT: Ensures caching layer reliability
"""

import pytest


@pytest.mark.infrastructure
class TestRedisConnectivity:
    """Test Redis connection and basic operations."""

    def test_redis_connection(self, test_redis_url):
        """
        Test Redis connection can be established.

        WHY: Verify Redis is accessible
        HOW: Connect and ping Redis
        IMPACT: Catches configuration issues early
        """
        import redis

        client = redis.from_url(test_redis_url)
        assert client.ping() is True

    def test_redis_set_get(self, test_redis_url):
        """
        Test basic Redis set/get operations.

        WHY: Verify Redis can store and retrieve data
        HOW: Set a key and retrieve it
        IMPACT: Ensures caching functionality works
        """
        import redis

        client = redis.from_url(test_redis_url)

        # Set value
        client.set("test_key", "test_value", ex=60)

        # Get value
        value = client.get("test_key")
        assert value.decode("utf-8") == "test_value"

        # Cleanup
        client.delete("test_key")


# Pytest fixtures
@pytest.fixture
def test_redis_url():
    """Provide test Redis URL."""
    import os

    return os.getenv("REDIS_URL", "redis://localhost:6379/0")
