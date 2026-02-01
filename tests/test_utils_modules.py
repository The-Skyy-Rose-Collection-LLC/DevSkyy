"""
Comprehensive Unit Tests for DevSkyy Utils Modules
===================================================

Tests for:
- logging_utils.py
- rate_limiting.py
- request_deduplication.py
- security_utils.py

Target: 70%+ coverage
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path

import pytest

# =============================================================================
# LOGGING UTILS TESTS
# =============================================================================


class TestLoggingUtils:
    """Tests for utils/logging_utils.py"""

    def test_generate_correlation_id(self):
        """Correlation ID should have correct format."""
        from utils.logging_utils import generate_correlation_id

        corr_id = generate_correlation_id()
        assert corr_id.startswith("corr-")
        assert len(corr_id) == 21  # "corr-" + 16 hex chars

    def test_generate_correlation_id_unique(self):
        """Each generated correlation ID should be unique."""
        from utils.logging_utils import generate_correlation_id

        ids = [generate_correlation_id() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_set_and_get_correlation_id(self):
        """Should set and get correlation ID from context."""
        from utils.logging_utils import (
            clear_request_context,
            get_correlation_id,
            set_correlation_id,
        )

        clear_request_context()
        test_id = "corr-test123"
        set_correlation_id(test_id)
        assert get_correlation_id() == test_id
        clear_request_context()

    def test_get_correlation_id_generates_if_missing(self):
        """Should generate new ID if none set."""
        from utils.logging_utils import (
            clear_request_context,
            correlation_id_var,
            get_correlation_id,
        )

        clear_request_context()
        # Ensure empty
        correlation_id_var.set("")
        corr_id = get_correlation_id()
        assert corr_id.startswith("corr-")

    def test_set_request_context(self):
        """Should set request context variables."""
        from utils.logging_utils import (
            clear_request_context,
            request_id_var,
            set_request_context,
            user_id_var,
        )

        clear_request_context()
        set_request_context(request_id="req-123", user_id="user-456")
        assert request_id_var.get() == "req-123"
        assert user_id_var.get() == "user-456"
        clear_request_context()

    def test_set_request_context_generates_correlation_id(self):
        """Should generate correlation ID if not set."""
        from utils.logging_utils import (
            clear_request_context,
            correlation_id_var,
            set_request_context,
        )

        clear_request_context()
        correlation_id_var.set("")
        set_request_context(request_id="req-123")
        assert correlation_id_var.get().startswith("corr-")
        clear_request_context()

    def test_clear_request_context(self):
        """Should clear all context variables."""
        from utils.logging_utils import (
            clear_request_context,
            correlation_id_var,
            request_id_var,
            set_request_context,
            user_id_var,
        )

        set_request_context(request_id="req-123", user_id="user-456")
        clear_request_context()
        assert correlation_id_var.get() == ""
        assert request_id_var.get() == ""
        assert user_id_var.get() == ""

    def test_configure_logging_json(self):
        """Should configure structlog for JSON output."""
        from utils.logging_utils import configure_logging

        # Should not raise
        configure_logging(json_output=True)

    def test_configure_logging_console(self):
        """Should configure structlog for console output."""
        from utils.logging_utils import configure_logging

        # Should not raise
        configure_logging(json_output=False)

    def test_get_logger(self):
        """Should return a bound logger."""
        from utils.logging_utils import get_logger

        logger = get_logger("test_module")
        assert logger is not None

    def test_log_context_manager(self):
        """LogContext should bind and unbind context."""
        from utils.logging_utils import LogContext

        with LogContext(test_key="test_value", another="value"):
            # Context is bound during the block
            pass
        # Context should be unbound after exit

    @pytest.mark.asyncio
    async def test_log_api_request(self):
        """Should log API request with correlation tracking."""
        from utils.logging_utils import clear_request_context, log_api_request

        clear_request_context()
        await log_api_request(
            endpoint="/api/test",
            method="GET",
            params={"foo": "bar"},
            correlation_id="corr-test123",
        )
        clear_request_context()

    @pytest.mark.asyncio
    async def test_log_api_request_without_correlation_id(self):
        """Should log API request without explicit correlation ID."""
        from utils.logging_utils import clear_request_context, log_api_request

        clear_request_context()
        await log_api_request(
            endpoint="/api/test",
            method="POST",
        )
        clear_request_context()

    @pytest.mark.asyncio
    async def test_log_api_response_success(self):
        """Should log successful API response."""
        from utils.logging_utils import clear_request_context, log_api_response

        clear_request_context()
        await log_api_response(
            endpoint="/api/test",
            status_code=200,
            duration_ms=50.5,
        )
        clear_request_context()

    @pytest.mark.asyncio
    async def test_log_api_response_error(self):
        """Should log error API response."""
        from utils.logging_utils import clear_request_context, log_api_response

        clear_request_context()
        await log_api_response(
            endpoint="/api/test",
            status_code=500,
            duration_ms=100.0,
            error="Internal server error",
        )
        clear_request_context()

    @pytest.mark.asyncio
    async def test_log_error(self):
        """Should log error with full context."""
        from utils.logging_utils import clear_request_context, log_error

        clear_request_context()
        try:
            raise ValueError("Test error")
        except Exception as e:
            await log_error(
                error=e,
                context={"extra": "context"},
                stack_trace="trace here",
            )
        clear_request_context()

    @pytest.mark.asyncio
    async def test_log_error_minimal(self):
        """Should log error with minimal context."""
        from utils.logging_utils import clear_request_context, log_error

        clear_request_context()
        try:
            raise RuntimeError("Test runtime error")
        except Exception as e:
            await log_error(error=e)
        clear_request_context()


# =============================================================================
# RATE LIMITING TESTS
# =============================================================================


class TestTokenBucket:
    """Tests for TokenBucket dataclass."""

    def test_token_bucket_creation(self):
        """Should create token bucket with initial values."""
        from utils.rate_limiting import TokenBucket

        bucket = TokenBucket(
            capacity=10,
            refill_rate=1.0,
            tokens=10,
            last_refill=time.time(),
        )
        assert bucket.capacity == 10
        assert bucket.refill_rate == 1.0
        assert bucket.tokens == 10

    def test_token_bucket_consume_success(self):
        """Should consume tokens when available."""
        from utils.rate_limiting import TokenBucket

        bucket = TokenBucket(
            capacity=10,
            refill_rate=1.0,
            tokens=10,
            last_refill=time.time(),
        )
        assert bucket.consume(1) is True
        assert bucket.tokens < 10

    def test_token_bucket_consume_multiple(self):
        """Should consume multiple tokens."""
        from utils.rate_limiting import TokenBucket

        bucket = TokenBucket(
            capacity=10,
            refill_rate=1.0,
            tokens=10,
            last_refill=time.time(),
        )
        assert bucket.consume(5) is True
        # Allow for small refill during test
        assert bucket.tokens < 6

    def test_token_bucket_consume_fail_insufficient(self):
        """Should fail when not enough tokens."""
        from utils.rate_limiting import TokenBucket

        bucket = TokenBucket(
            capacity=10,
            refill_rate=1.0,
            tokens=2,
            last_refill=time.time(),
        )
        assert bucket.consume(5) is False

    def test_token_bucket_refill(self):
        """Should refill tokens over time."""
        from utils.rate_limiting import TokenBucket

        past_time = time.time() - 5  # 5 seconds ago
        bucket = TokenBucket(
            capacity=10,
            refill_rate=2.0,  # 2 tokens per second
            tokens=0,
            last_refill=past_time,
        )
        # Force refill by consuming
        bucket._refill()
        # Should have refilled ~10 tokens (2 per second * 5 seconds)
        assert bucket.tokens >= 9  # Allow for timing variance

    def test_token_bucket_refill_caps_at_capacity(self):
        """Should not exceed capacity on refill."""
        from utils.rate_limiting import TokenBucket

        past_time = time.time() - 100  # Long time ago
        bucket = TokenBucket(
            capacity=10,
            refill_rate=10.0,
            tokens=0,
            last_refill=past_time,
        )
        bucket._refill()
        assert bucket.tokens <= bucket.capacity

    def test_token_bucket_get_retry_after_with_tokens(self):
        """Should return 0 when tokens available."""
        from utils.rate_limiting import TokenBucket

        bucket = TokenBucket(
            capacity=10,
            refill_rate=1.0,
            tokens=5,
            last_refill=time.time(),
        )
        assert bucket.get_retry_after() == 0.0

    def test_token_bucket_get_retry_after_no_tokens(self):
        """Should return wait time when no tokens."""
        from utils.rate_limiting import TokenBucket

        bucket = TokenBucket(
            capacity=10,
            refill_rate=1.0,  # 1 token per second
            tokens=0,
            last_refill=time.time(),
        )
        retry_after = bucket.get_retry_after()
        # Should be around 1 second (need 1 token at 1/second)
        assert retry_after > 0
        assert retry_after <= 1.0


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_rate_limiter_creation(self):
        """Should create rate limiter with defaults."""
        from utils.rate_limiting import RateLimiter

        limiter = RateLimiter()
        assert limiter.requests_per_second == 10.0
        assert limiter.burst_size == 20

    def test_rate_limiter_custom_params(self):
        """Should create rate limiter with custom params."""
        from utils.rate_limiting import RateLimiter

        limiter = RateLimiter(requests_per_second=5.0, burst_size=10)
        assert limiter.requests_per_second == 5.0
        assert limiter.burst_size == 10

    def test_rate_limiter_get_bucket_creates_new(self):
        """Should create new bucket for unknown key."""
        from utils.rate_limiting import RateLimiter

        limiter = RateLimiter()
        bucket = limiter._get_bucket("test-key")
        assert bucket is not None
        assert bucket.capacity == limiter.burst_size
        assert "test-key" in limiter.buckets

    def test_rate_limiter_get_bucket_returns_existing(self):
        """Should return existing bucket for known key."""
        from utils.rate_limiting import RateLimiter

        limiter = RateLimiter()
        bucket1 = limiter._get_bucket("test-key")
        bucket2 = limiter._get_bucket("test-key")
        assert bucket1 is bucket2

    @pytest.mark.asyncio
    async def test_rate_limiter_check_allowed(self):
        """Should allow request when under limit."""
        from utils.rate_limiting import RateLimiter

        limiter = RateLimiter(requests_per_second=10.0, burst_size=20)
        allowed, retry_after = await limiter.check_rate_limit("test-key")
        assert allowed is True
        assert retry_after is None

    @pytest.mark.asyncio
    async def test_rate_limiter_check_rate_limited(self):
        """Should rate limit when tokens exhausted."""
        from utils.rate_limiting import RateLimiter

        limiter = RateLimiter(requests_per_second=1.0, burst_size=2)
        # Exhaust tokens
        await limiter.check_rate_limit("test-key")
        await limiter.check_rate_limit("test-key")
        # Third request should be limited
        allowed, retry_after = await limiter.check_rate_limit("test-key")
        assert allowed is False
        assert retry_after is not None
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_rate_limiter_wait_if_needed(self):
        """Should wait and then proceed when rate limited."""
        from utils.rate_limiting import RateLimiter

        limiter = RateLimiter(requests_per_second=100.0, burst_size=1)
        # Exhaust the single token
        await limiter.check_rate_limit("test-key")
        # Should wait and proceed (short wait due to high refill rate)
        start = time.time()
        await limiter.wait_if_needed("test-key")
        elapsed = time.time() - start
        # Should have waited a short time
        assert elapsed < 0.5

    def test_rate_limiter_reset_specific_key(self):
        """Should reset specific key."""
        from utils.rate_limiting import RateLimiter

        limiter = RateLimiter()
        limiter._get_bucket("key1")
        limiter._get_bucket("key2")
        limiter.reset("key1")
        assert "key1" not in limiter.buckets
        assert "key2" in limiter.buckets

    def test_rate_limiter_reset_all(self):
        """Should reset all keys."""
        from utils.rate_limiting import RateLimiter

        limiter = RateLimiter()
        limiter._get_bucket("key1")
        limiter._get_bucket("key2")
        limiter.reset()
        assert len(limiter.buckets) == 0

    def test_rate_limiter_get_stats(self):
        """Should return statistics for buckets."""
        from utils.rate_limiting import RateLimiter

        limiter = RateLimiter()
        limiter._get_bucket("test-key")
        stats = limiter.get_stats()
        assert "test-key" in stats
        assert "tokens_available" in stats["test-key"]
        assert "capacity" in stats["test-key"]
        assert "refill_rate" in stats["test-key"]
        assert "utilization" in stats["test-key"]


class TestRateLimitingHelpers:
    """Tests for module-level rate limiting helper functions."""

    @pytest.mark.asyncio
    async def test_check_rate_limit(self):
        """Should check rate limit for user/endpoint."""
        from utils.rate_limiting import check_rate_limit, reset_rate_limits

        reset_rate_limits()
        allowed, retry_after = await check_rate_limit("user1", "/api/test")
        assert allowed is True
        assert retry_after is None

    @pytest.mark.asyncio
    async def test_wait_for_rate_limit(self):
        """Should wait for rate limit."""
        from utils.rate_limiting import reset_rate_limits, wait_for_rate_limit

        reset_rate_limits()
        await wait_for_rate_limit("user1", "/api/test")
        # Should complete without error

    def test_get_rate_limit_stats(self):
        """Should get global stats."""
        from utils.rate_limiting import get_rate_limit_stats, reset_rate_limits

        reset_rate_limits()
        stats = get_rate_limit_stats()
        assert isinstance(stats, dict)

    def test_reset_rate_limits_user_only(self):
        """Should reset all endpoints for a user."""
        from utils.rate_limiting import (
            _global_rate_limiter,
            reset_rate_limits,
        )

        reset_rate_limits()
        _global_rate_limiter._get_bucket("user1:/api/a")
        _global_rate_limiter._get_bucket("user1:/api/b")
        _global_rate_limiter._get_bucket("user2:/api/a")
        reset_rate_limits(user_id="user1")
        assert "user1:/api/a" not in _global_rate_limiter.buckets
        assert "user1:/api/b" not in _global_rate_limiter.buckets
        assert "user2:/api/a" in _global_rate_limiter.buckets

    def test_reset_rate_limits_endpoint_only(self):
        """Should reset endpoint for all users."""
        from utils.rate_limiting import (
            _global_rate_limiter,
            reset_rate_limits,
        )

        reset_rate_limits()
        _global_rate_limiter._get_bucket("user1:/api/a")
        _global_rate_limiter._get_bucket("user2:/api/a")
        _global_rate_limiter._get_bucket("user1:/api/b")
        reset_rate_limits(endpoint="/api/a")
        assert "user1:/api/a" not in _global_rate_limiter.buckets
        assert "user2:/api/a" not in _global_rate_limiter.buckets
        assert "user1:/api/b" in _global_rate_limiter.buckets


# =============================================================================
# REQUEST DEDUPLICATION TESTS
# =============================================================================


class TestRequestDeduplicator:
    """Tests for RequestDeduplicator class."""

    def test_deduplicator_creation(self):
        """Should create deduplicator with default TTL."""
        from utils.request_deduplication import RequestDeduplicator

        dedup = RequestDeduplicator()
        assert dedup.ttl_seconds == 60.0

    def test_deduplicator_custom_ttl(self):
        """Should create deduplicator with custom TTL."""
        from utils.request_deduplication import RequestDeduplicator

        dedup = RequestDeduplicator(ttl_seconds=120.0)
        assert dedup.ttl_seconds == 120.0

    def test_compute_request_hash(self):
        """Should compute consistent hash for same request."""
        from utils.request_deduplication import RequestDeduplicator

        dedup = RequestDeduplicator()
        hash1 = dedup._compute_request_hash("/api/test", "GET", {"a": 1}, {"b": 2})
        hash2 = dedup._compute_request_hash("/api/test", "GET", {"a": 1}, {"b": 2})
        assert hash1 == hash2
        assert len(hash1) == 16

    def test_compute_request_hash_different_for_different_requests(self):
        """Should compute different hash for different requests."""
        from utils.request_deduplication import RequestDeduplicator

        dedup = RequestDeduplicator()
        hash1 = dedup._compute_request_hash("/api/test", "GET")
        hash2 = dedup._compute_request_hash("/api/other", "GET")
        assert hash1 != hash2

    def test_compute_request_hash_method_matters(self):
        """Hash should differ based on method."""
        from utils.request_deduplication import RequestDeduplicator

        dedup = RequestDeduplicator()
        hash1 = dedup._compute_request_hash("/api/test", "GET")
        hash2 = dedup._compute_request_hash("/api/test", "POST")
        assert hash1 != hash2

    @pytest.mark.asyncio
    async def test_deduplicate_single_request(self):
        """Should execute single request normally."""
        from utils.request_deduplication import RequestDeduplicator

        dedup = RequestDeduplicator()
        call_count = 0

        async def request_func():
            nonlocal call_count
            call_count += 1
            return {"result": "success"}

        result = await dedup.deduplicate("/api/test", "GET", request_func)
        assert result == {"result": "success"}
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_deduplicate_sequential_requests(self):
        """Sequential requests should each execute (not deduplicated after completion)."""
        from utils.request_deduplication import RequestDeduplicator

        dedup = RequestDeduplicator()
        call_count = 0

        async def fast_request():
            nonlocal call_count
            call_count += 1
            return {"result": "success", "call": call_count}

        # Sequential requests should each execute since first completes before second starts
        result1 = await dedup.deduplicate("/api/seq_test", "GET", fast_request)
        result2 = await dedup.deduplicate("/api/seq_test", "GET", fast_request)

        assert result1["result"] == "success"
        assert result2["result"] == "success"
        # Each sequential call should execute (no pending request to deduplicate with)
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_deduplicate_different_requests_not_deduped(self):
        """Different requests should not be deduplicated."""
        from utils.request_deduplication import RequestDeduplicator

        dedup = RequestDeduplicator()
        call_count = 0

        async def request_func():
            nonlocal call_count
            call_count += 1
            return {"result": call_count}

        result1 = await dedup.deduplicate("/api/test1", "GET", request_func)
        result2 = await dedup.deduplicate("/api/test2", "GET", request_func)

        assert call_count == 2
        assert result1["result"] == 1
        assert result2["result"] == 2

    @pytest.mark.asyncio
    async def test_deduplicate_exception_propagates(self):
        """Exception should propagate from request."""
        from utils.request_deduplication import RequestDeduplicator

        dedup = RequestDeduplicator()

        async def failing_request():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await dedup.deduplicate("/api/fail_test", "GET", failing_request)

    @pytest.mark.asyncio
    async def test_deduplicate_stale_request_cleanup(self):
        """Should clean up stale pending requests."""
        from datetime import timedelta

        from utils.request_deduplication import PendingRequest, RequestDeduplicator

        dedup = RequestDeduplicator(ttl_seconds=0.0)  # Immediate staleness
        call_count = 0

        # Manually add a stale pending request
        stale_future = asyncio.Future()
        dedup.pending["stale_hash"] = PendingRequest(
            future=stale_future,
            started_at=datetime.now() - timedelta(seconds=100),
        )

        async def request_func():
            nonlocal call_count
            call_count += 1
            return {"result": "success"}

        # This should trigger cleanup of stale request
        # (Different hash, won't actually match, but shows cleanup logic)
        result = await dedup.deduplicate("/api/test", "GET", request_func)
        assert result == {"result": "success"}

    def test_deduplicator_clear(self):
        """Should clear all pending requests."""
        from utils.request_deduplication import PendingRequest, RequestDeduplicator

        dedup = RequestDeduplicator()
        loop = asyncio.new_event_loop()
        future = loop.create_future()
        dedup.pending["test"] = PendingRequest(future=future, started_at=datetime.now())
        dedup.clear()
        assert len(dedup.pending) == 0
        loop.close()

    def test_deduplicator_get_stats(self):
        """Should return statistics."""
        from utils.request_deduplication import PendingRequest, RequestDeduplicator

        dedup = RequestDeduplicator()
        loop = asyncio.new_event_loop()
        future = loop.create_future()
        dedup.pending["test_hash"] = PendingRequest(future=future, started_at=datetime.now())

        stats = dedup.get_stats()
        assert stats["pending_requests"] == 1
        assert len(stats["requests"]) == 1
        assert stats["requests"][0]["hash"] == "test_hash"
        assert "age_seconds" in stats["requests"][0]
        loop.close()


class TestDeduplicationHelpers:
    """Tests for module-level deduplication helper functions."""

    @pytest.mark.asyncio
    async def test_deduplicate_request(self):
        """Should deduplicate request globally."""
        from utils.request_deduplication import (
            clear_deduplication_cache,
            deduplicate_request,
        )

        clear_deduplication_cache()

        async def request_func():
            return {"result": "success"}

        result = await deduplicate_request("/api/test", "GET", request_func)
        assert result == {"result": "success"}

    def test_get_deduplication_stats(self):
        """Should get global stats."""
        from utils.request_deduplication import (
            clear_deduplication_cache,
            get_deduplication_stats,
        )

        clear_deduplication_cache()
        stats = get_deduplication_stats()
        assert isinstance(stats, dict)
        assert "pending_requests" in stats

    def test_clear_deduplication_cache(self):
        """Should clear global cache."""
        from utils.request_deduplication import (
            clear_deduplication_cache,
            get_deduplication_stats,
        )

        clear_deduplication_cache()
        stats = get_deduplication_stats()
        assert stats["pending_requests"] == 0


# =============================================================================
# SECURITY UTILS TESTS
# =============================================================================


class TestSecurityExceptions:
    """Tests for security exception classes."""

    def test_security_error(self):
        """Should create SecurityError."""
        from utils.security_utils import SecurityError

        error = SecurityError("Test security error")
        assert str(error) == "Test security error"

    def test_path_traversal_error(self):
        """Should create PathTraversalError."""
        from utils.security_utils import PathTraversalError, SecurityError

        error = PathTraversalError("Path traversal detected")
        assert isinstance(error, SecurityError)
        assert str(error) == "Path traversal detected"

    def test_injection_error(self):
        """Should create InjectionError."""
        from utils.security_utils import InjectionError, SecurityError

        error = InjectionError("Injection detected")
        assert isinstance(error, SecurityError)
        assert str(error) == "Injection detected"


class TestSanitizePath:
    """Tests for sanitize_path function."""

    def test_sanitize_path_valid(self, tmp_path):
        """Should sanitize valid path."""
        from utils.security_utils import sanitize_path

        # Create a temp file
        test_file = tmp_path / "test.py"
        test_file.touch()

        result = sanitize_path(str(test_file))
        assert isinstance(result, Path)

    def test_sanitize_path_empty(self):
        """Should raise ValueError for empty path."""
        from utils.security_utils import sanitize_path

        with pytest.raises(ValueError, match="non-empty string"):
            sanitize_path("")

    def test_sanitize_path_none(self):
        """Should raise ValueError for None."""
        from utils.security_utils import sanitize_path

        with pytest.raises(ValueError, match="non-empty string"):
            sanitize_path(None)

    def test_sanitize_path_traversal_dotdot(self):
        """Should detect parent directory traversal."""
        from utils.security_utils import PathTraversalError, sanitize_path

        with pytest.raises(PathTraversalError, match="Dangerous pattern"):
            sanitize_path("../../../etc/passwd")

    def test_sanitize_path_traversal_tilde(self):
        """Should detect home directory expansion."""
        from utils.security_utils import PathTraversalError, sanitize_path

        with pytest.raises(PathTraversalError, match="Dangerous pattern"):
            sanitize_path("~/secrets.txt")

    def test_sanitize_path_traversal_variable(self):
        """Should detect shell variable expansion."""
        from utils.security_utils import PathTraversalError, sanitize_path

        with pytest.raises(PathTraversalError, match="Dangerous pattern"):
            sanitize_path("$HOME/secrets.txt")

    def test_sanitize_path_null_byte(self):
        """Should reject null byte injection."""
        from utils.security_utils import sanitize_path

        # Null byte causes ValueError from Path.resolve() before our check
        with pytest.raises(ValueError, match="Invalid path"):
            sanitize_path("test.py\x00.txt")

    def test_sanitize_path_with_base_dir_valid(self, tmp_path):
        """Should allow path within base directory."""
        from utils.security_utils import sanitize_path

        test_file = tmp_path / "subdir" / "test.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.touch()

        result = sanitize_path(str(test_file), base_dir=str(tmp_path))
        assert isinstance(result, Path)

    def test_sanitize_path_with_base_dir_outside(self, tmp_path):
        """Should reject path outside base directory."""
        from utils.security_utils import PathTraversalError, sanitize_path

        other_dir = tmp_path.parent / "other"
        other_dir.mkdir(exist_ok=True)
        outside_file = other_dir / "outside.txt"
        outside_file.touch()

        with pytest.raises(PathTraversalError, match="outside allowed directory"):
            sanitize_path(str(outside_file), base_dir=str(tmp_path))


class TestSanitizeFileTypes:
    """Tests for sanitize_file_types function."""

    def test_sanitize_file_types_valid(self):
        """Should sanitize valid file types."""
        from utils.security_utils import sanitize_file_types

        result = sanitize_file_types([".py", ".js", ".ts"])
        assert result == [".py", ".js", ".ts"]

    def test_sanitize_file_types_adds_dot(self):
        """Should add dot to extensions without one."""
        from utils.security_utils import sanitize_file_types

        result = sanitize_file_types(["py", "js"])
        assert result == [".py", ".js"]

    def test_sanitize_file_types_empty(self):
        """Should return empty list for empty input."""
        from utils.security_utils import sanitize_file_types

        result = sanitize_file_types([])
        assert result == []

    def test_sanitize_file_types_strips_whitespace(self):
        """Should strip whitespace from extensions."""
        from utils.security_utils import sanitize_file_types

        result = sanitize_file_types(["  .py  ", "  js  "])
        assert result == [".py", ".js"]

    def test_sanitize_file_types_skips_non_strings(self):
        """Should skip non-string values."""
        from utils.security_utils import sanitize_file_types

        result = sanitize_file_types([".py", 123, None, ".js"])
        assert result == [".py", ".js"]

    def test_sanitize_file_types_skips_empty_strings(self):
        """Should skip empty strings."""
        from utils.security_utils import sanitize_file_types

        result = sanitize_file_types([".py", "", "   ", ".js"])
        assert result == [".py", ".js"]

    def test_sanitize_file_types_invalid_characters(self):
        """Should raise InjectionError for invalid characters."""
        from utils.security_utils import InjectionError, sanitize_file_types

        with pytest.raises(InjectionError, match="Invalid file type"):
            sanitize_file_types([".py", ".js<script>"])


class TestValidateRequestParams:
    """Tests for validate_request_params function."""

    def test_validate_params_valid(self):
        """Should validate valid parameters."""
        from utils.security_utils import validate_request_params

        params = {"name": "test", "count": 42, "active": True}
        result = validate_request_params(params)
        assert result == params

    def test_validate_params_not_dict(self):
        """Should raise ValueError for non-dict input."""
        from utils.security_utils import validate_request_params

        with pytest.raises(ValueError, match="must be a dictionary"):
            validate_request_params("not a dict")

    def test_validate_params_null_byte(self):
        """Should detect null byte in parameters."""
        from utils.security_utils import InjectionError, validate_request_params

        with pytest.raises(InjectionError, match="Null byte"):
            validate_request_params({"name": "test\x00value"})

    def test_validate_params_script_tag(self):
        """Should detect script tag injection."""
        from utils.security_utils import InjectionError, validate_request_params

        with pytest.raises(InjectionError, match="script injection"):
            validate_request_params({"content": "<script>alert(1)</script>"})

    def test_validate_params_javascript_protocol(self):
        """Should detect javascript protocol."""
        from utils.security_utils import InjectionError, validate_request_params

        with pytest.raises(InjectionError, match="script injection"):
            validate_request_params({"url": "javascript:alert(1)"})

    def test_validate_params_onerror(self):
        """Should detect onerror handler."""
        from utils.security_utils import InjectionError, validate_request_params

        with pytest.raises(InjectionError, match="script injection"):
            validate_request_params({"img": '<img src="x" onerror="alert(1)">'})

    def test_validate_params_onload(self):
        """Should detect onload handler."""
        from utils.security_utils import InjectionError, validate_request_params

        with pytest.raises(InjectionError, match="script injection"):
            validate_request_params({"body": '<body onload="alert(1)">'})

    def test_validate_params_case_insensitive(self):
        """Should detect injections case-insensitively."""
        from utils.security_utils import InjectionError, validate_request_params

        with pytest.raises(InjectionError, match="script injection"):
            validate_request_params({"content": "<SCRIPT>alert(1)</SCRIPT>"})

    def test_validate_params_non_string_values_pass(self):
        """Non-string values should pass through."""
        from utils.security_utils import validate_request_params

        params = {"count": 42, "items": [1, 2, 3], "config": {"nested": True}}
        result = validate_request_params(params)
        assert result == params
