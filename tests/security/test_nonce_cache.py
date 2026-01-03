"""
Tests for Nonce Cache implementations
======================================

Comprehensive tests for replay attack prevention via nonce caching.

Tests cover:
- InMemoryNonceCache (development/testing)
- RedisNonceCache (production)
- Integration with APISecurityManager
- Edge cases and error conditions
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from security.api_security import (
    APISecurityManager,
    InMemoryNonceCache,
    NonceCache,
    RedisNonceCache,
)


class TestNonceCache:
    """Tests for NonceCache base class"""

    def test_base_class_raises_not_implemented(self):
        """NonceCache base class should raise NotImplementedError"""
        cache = NonceCache()

        with pytest.raises(NotImplementedError):
            cache.add("nonce", 123456)

        with pytest.raises(NotImplementedError):
            cache.exists("nonce", 123456)

        with pytest.raises(NotImplementedError):
            cache.cleanup()


class TestInMemoryNonceCache:
    """Tests for InMemoryNonceCache implementation"""

    def test_init_with_default_expiry(self):
        """Should initialize with default expiry seconds"""
        cache = InMemoryNonceCache()
        assert cache.expiry_seconds == 300
        assert cache.used_nonces == set()

    def test_init_with_custom_expiry(self):
        """Should initialize with custom expiry seconds"""
        cache = InMemoryNonceCache(expiry_seconds=600)
        assert cache.expiry_seconds == 600

    def test_add_nonce(self):
        """Should add nonce to cache"""
        cache = InMemoryNonceCache()
        timestamp = int(time.time())
        nonce = "abc123"

        cache.add(nonce, timestamp)

        expected_key = f"{nonce}:{timestamp}"
        assert expected_key in cache.used_nonces

    def test_exists_returns_true_for_cached_nonce(self):
        """Should return True for nonce that exists in cache"""
        cache = InMemoryNonceCache()
        timestamp = int(time.time())
        nonce = "abc123"

        cache.add(nonce, timestamp)

        assert cache.exists(nonce, timestamp) is True

    def test_exists_returns_false_for_uncached_nonce(self):
        """Should return False for nonce not in cache"""
        cache = InMemoryNonceCache()
        timestamp = int(time.time())

        assert cache.exists("nonexistent", timestamp) is False

    def test_exists_returns_false_for_different_timestamp(self):
        """Should return False if nonce exists but with different timestamp"""
        cache = InMemoryNonceCache()
        timestamp = int(time.time())
        nonce = "abc123"

        cache.add(nonce, timestamp)

        # Different timestamp
        assert cache.exists(nonce, timestamp + 100) is False

    def test_cleanup_clears_when_exceeds_threshold(self):
        """Should clear all nonces when threshold exceeded"""
        cache = InMemoryNonceCache()

        # Add more than 10,000 nonces to trigger cleanup
        for i in range(10001):
            cache.used_nonces.add(f"nonce_{i}:12345")

        # Verify we have 10,001 nonces
        assert len(cache.used_nonces) == 10001

        # This should trigger cleanup via add() which calls cleanup() AFTER adding
        cache.add("new_nonce", int(time.time()))

        # Cleanup clears ALL nonces when > 10,000, so cache is empty
        # (cleanup is called after add, so the new nonce gets cleared too)
        assert len(cache.used_nonces) == 0

    def test_cleanup_does_nothing_under_threshold(self):
        """Should not clear nonces when under threshold"""
        cache = InMemoryNonceCache()

        # Add 100 nonces (well under 10,000)
        for i in range(100):
            cache.add(f"nonce_{i}", 12345)

        assert len(cache.used_nonces) == 100


class TestRedisNonceCache:
    """Tests for RedisNonceCache implementation"""

    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client"""
        mock_client = MagicMock()
        mock_client.setex = MagicMock()
        mock_client.exists = MagicMock()
        return mock_client

    def test_init_with_redis_client(self, mock_redis_client):
        """Should initialize with provided Redis client"""
        cache = RedisNonceCache(redis_client=mock_redis_client, expiry_seconds=600)

        assert cache._redis == mock_redis_client
        assert cache.expiry_seconds == 600
        assert cache._nonce_prefix == "request_nonce:"

    @patch("security.api_security.redis")
    def test_init_without_redis_client_creates_connection(self, mock_redis_module):
        """Should create Redis connection when none provided"""
        mock_client = MagicMock()
        mock_redis_module.from_url.return_value = mock_client

        with patch.dict("os.environ", {"REDIS_URL": "redis://custom:6379/1"}):
            cache = RedisNonceCache()

        mock_redis_module.from_url.assert_called_once_with(
            "redis://custom:6379/1", decode_responses=True
        )
        assert cache._redis == mock_client

    @patch("security.api_security.redis")
    def test_init_uses_default_redis_url(self, mock_redis_module):
        """Should use default Redis URL when REDIS_URL not set"""
        mock_client = MagicMock()
        mock_redis_module.from_url.return_value = mock_client

        with patch.dict("os.environ", {}, clear=True):
            RedisNonceCache()

        mock_redis_module.from_url.assert_called_once_with(
            "redis://localhost:6379/0", decode_responses=True
        )

    def test_init_raises_runtime_error_when_redis_not_installed(self):
        """Should raise RuntimeError if redis module not available"""
        with (
            patch("security.api_security.redis", None),
            patch("security.api_security.Redis", None),
            pytest.raises(
                RuntimeError,
                match="redis package required for RedisNonceCache",
            ),
        ):
            RedisNonceCache()

    def test_add_nonce_stores_with_ttl(self, mock_redis_client):
        """Should store nonce in Redis with TTL"""
        cache = RedisNonceCache(redis_client=mock_redis_client, expiry_seconds=300)
        timestamp = int(time.time())
        nonce = "abc123"

        cache.add(nonce, timestamp)

        expected_key = f"request_nonce:{nonce}:{timestamp}"
        mock_redis_client.setex.assert_called_once_with(expected_key, 300, "1")

    def test_add_nonce_uses_custom_expiry(self, mock_redis_client):
        """Should use custom expiry seconds when storing nonce"""
        cache = RedisNonceCache(redis_client=mock_redis_client, expiry_seconds=600)
        timestamp = int(time.time())
        nonce = "custom_nonce"

        cache.add(nonce, timestamp)

        expected_key = f"request_nonce:{nonce}:{timestamp}"
        mock_redis_client.setex.assert_called_once_with(expected_key, 600, "1")

    def test_exists_returns_true_when_nonce_present(self, mock_redis_client):
        """Should return True when nonce exists in Redis"""
        mock_redis_client.exists.return_value = 1  # Redis returns 1 for exists

        cache = RedisNonceCache(redis_client=mock_redis_client)
        timestamp = int(time.time())
        nonce = "abc123"

        result = cache.exists(nonce, timestamp)

        expected_key = f"request_nonce:{nonce}:{timestamp}"
        mock_redis_client.exists.assert_called_once_with(expected_key)
        assert result is True

    def test_exists_returns_false_when_nonce_absent(self, mock_redis_client):
        """Should return False when nonce doesn't exist in Redis"""
        mock_redis_client.exists.return_value = 0  # Redis returns 0 for non-existent

        cache = RedisNonceCache(redis_client=mock_redis_client)
        timestamp = int(time.time())
        nonce = "nonexistent"

        result = cache.exists(nonce, timestamp)

        expected_key = f"request_nonce:{nonce}:{timestamp}"
        mock_redis_client.exists.assert_called_once_with(expected_key)
        assert result is False

    def test_cleanup_is_noop(self, mock_redis_client):
        """Cleanup should be a no-op for Redis (automatic TTL expiration)"""
        cache = RedisNonceCache(redis_client=mock_redis_client)

        # Should not raise any exceptions
        cache.cleanup()

        # Should not call any Redis methods
        mock_redis_client.delete.assert_not_called()
        mock_redis_client.scan.assert_not_called()


class TestAPISecurityManagerNonceCache:
    """Tests for nonce cache integration with APISecurityManager"""

    def test_manager_uses_provided_nonce_cache(self):
        """Should use provided nonce cache instance"""
        custom_cache = InMemoryNonceCache(expiry_seconds=600)
        manager = APISecurityManager(nonce_cache=custom_cache)

        assert manager.nonce_cache == custom_cache
        assert manager.nonce_cache.expiry_seconds == 600

    @patch("security.api_security.RedisNonceCache")
    def test_manager_uses_redis_cache_when_use_redis_true(self, mock_redis_cache_class):
        """Should create RedisNonceCache when use_redis=True"""
        mock_instance = MagicMock()
        mock_redis_cache_class.return_value = mock_instance

        manager = APISecurityManager(use_redis=True)

        mock_redis_cache_class.assert_called_once()
        assert manager.nonce_cache == mock_instance

    @patch("security.api_security.RedisNonceCache")
    @patch("security.api_security.logger")
    def test_manager_falls_back_to_memory_when_redis_fails(
        self, mock_logger, mock_redis_cache_class
    ):
        """Should fallback to InMemoryNonceCache when Redis initialization fails"""
        mock_redis_cache_class.side_effect = RuntimeError("Redis not available")

        manager = APISecurityManager(use_redis=True)

        # Should fallback to InMemoryNonceCache
        assert isinstance(manager.nonce_cache, InMemoryNonceCache)

        # Should log warning about Redis failure (may have additional warnings)
        mock_logger.warning.assert_called()
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
        redis_warning_found = any(
            "Failed to initialize Redis nonce cache" in call for call in warning_calls
        )
        assert redis_warning_found, f"Redis warning not found in: {warning_calls}"

    def test_manager_uses_memory_cache_by_default(self):
        """Should use InMemoryNonceCache by default"""
        manager = APISecurityManager()

        assert isinstance(manager.nonce_cache, InMemoryNonceCache)

    def test_verify_signature_detects_replay_attack(self):
        """Should detect replay attack via nonce reuse"""
        manager = APISecurityManager()
        timestamp = int(time.time())

        # Create mock request
        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.url.path = "/api/v2/test"

        # Create valid signature
        signature = manager.sign_request("POST", "/api/v2/test", b"test body", timestamp)

        # First verification should succeed
        result1 = manager.verify_request_signature(mock_request, signature, b"test body")
        assert result1 is True

        # Second verification with same nonce should fail (replay attack)
        result2 = manager.verify_request_signature(mock_request, signature, b"test body")
        assert result2 is False

    def test_verify_signature_rejects_expired_timestamp(self):
        """Should reject signature with expired timestamp"""
        manager = APISecurityManager()
        old_timestamp = int(time.time()) - 400  # More than 300 seconds ago

        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/v2/resource"

        signature = manager.sign_request("GET", "/api/v2/resource", b"", old_timestamp)

        result = manager.verify_request_signature(mock_request, signature, b"")
        assert result is False

    def test_verify_signature_adds_nonce_to_cache(self):
        """Should add nonce to cache after successful verification"""
        manager = APISecurityManager()
        timestamp = int(time.time())
        nonce = "test_nonce_123"

        # Ensure nonce not in cache initially
        assert manager.nonce_cache.exists(nonce, timestamp) is False

        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.url.path = "/api/v2/test"

        # Create signature with specific nonce
        signature = manager.sign_request("POST", "/api/v2/test", b"", timestamp)
        signature.nonce = nonce  # Override with known nonce

        # Verify (should add nonce to cache)
        manager.verify_request_signature(mock_request, signature, b"")

        # Nonce should now be in cache
        assert manager.nonce_cache.exists(nonce, timestamp) is True


class TestNonceCacheEdgeCases:
    """Edge cases and boundary conditions for nonce cache"""

    def test_inmemory_cache_handles_unicode_nonces(self):
        """Should handle Unicode characters in nonces"""
        cache = InMemoryNonceCache()
        timestamp = int(time.time())
        unicode_nonce = "nonce_测试_emoji_🔐"

        cache.add(unicode_nonce, timestamp)
        assert cache.exists(unicode_nonce, timestamp) is True

    def test_inmemory_cache_handles_very_long_nonces(self):
        """Should handle very long nonce strings"""
        cache = InMemoryNonceCache()
        timestamp = int(time.time())
        long_nonce = "a" * 10000  # 10K characters

        cache.add(long_nonce, timestamp)
        assert cache.exists(long_nonce, timestamp) is True

    def test_redis_cache_handles_concurrent_adds(self, mocker):
        """Should handle concurrent add operations"""
        mock_redis = MagicMock()
        cache = RedisNonceCache(redis_client=mock_redis)

        timestamp = int(time.time())
        nonces = [f"nonce_{i}" for i in range(100)]

        # Simulate concurrent adds
        for nonce in nonces:
            cache.add(nonce, timestamp)

        # Should have called setex 100 times
        assert mock_redis.setex.call_count == 100

    def test_redis_cache_key_format_consistency(self, mocker):
        """Should maintain consistent key format"""
        mock_redis = MagicMock()
        cache = RedisNonceCache(redis_client=mock_redis)

        cache.add("test", 12345)
        cache.exists("test", 12345)

        # Both operations should use the same key format
        add_key = mock_redis.setex.call_args[0][0]
        exists_key = mock_redis.exists.call_args[0][0]

        assert add_key == exists_key
        assert add_key == "request_nonce:test:12345"
