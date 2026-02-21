"""
Tests for API Gateway
======================

Tests CircuitBreaker, RateLimiter, and APIGateway routing logic.
All tests are unit-level — no real HTTP connections made.
"""

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest

from gateway.api_gateway import (
    APIGateway,
    CircuitBreaker,
    CircuitState,
    RateLimiter,
    RouteConfig,
)


@pytest.mark.unit
class TestCircuitBreaker:
    """Tests for CircuitBreaker state machine"""

    def test_initial_state_is_closed(self):
        """A new circuit breaker starts CLOSED (normal operation)."""
        cb = CircuitBreaker(name="test", window_size=10)
        assert cb.state == CircuitState.CLOSED
        assert cb.is_open is False

    def test_trips_open_after_threshold_failures(self):
        """
        Circuit trips to OPEN when failure rate exceeds threshold.
        With window_size=10 and threshold=0.5: needs 5+ failures in 10 requests.
        """
        cb = CircuitBreaker(name="test", failure_threshold=0.5, window_size=10)

        # 5 failures + 5 successes = 50% failure rate — right at threshold, NOT tripped
        for _ in range(5):
            cb.record_success()
        for _ in range(5):
            cb.record_failure()

        # Window is full (10 entries), failure rate = 0.5 — should be OPEN
        assert cb.state == CircuitState.OPEN

    def test_success_in_half_open_closes_circuit(self):
        """A success in HALF_OPEN state transitions circuit back to CLOSED."""
        cb = CircuitBreaker(name="test", failure_threshold=0.5, window_size=4, recovery_timeout=0.01)

        # Trip circuit
        for _ in range(4):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(0.02)
        assert cb.state == CircuitState.HALF_OPEN

        # One success closes it
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_failure_in_half_open_reopens_circuit(self):
        """A failure in HALF_OPEN state re-opens the circuit immediately."""
        cb = CircuitBreaker(name="test", failure_threshold=0.5, window_size=4, recovery_timeout=0.01)

        # Trip circuit
        for _ in range(4):
            cb.record_failure()

        # Wait for half-open
        time.sleep(0.02)
        assert cb.state == CircuitState.HALF_OPEN

        # Failure in half-open → stays or goes back to OPEN
        cb.record_failure()
        # After another failure, window is full of failures → OPEN
        assert cb.state == CircuitState.OPEN

    def test_reset_clears_state(self):
        """Manual reset returns circuit to CLOSED with empty window."""
        cb = CircuitBreaker(name="test", failure_threshold=0.5, window_size=4)
        for _ in range(4):
            cb.record_failure()
        assert cb.is_open

        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_rate == 0.0

    def test_failure_rate_calculation(self):
        """failure_rate property returns accurate float in 0.0–1.0 range."""
        cb = CircuitBreaker(name="test", window_size=10, failure_threshold=0.9)
        cb.record_success()
        cb.record_success()
        cb.record_failure()
        cb.record_failure()
        # 2 failures / 4 total = 0.5
        assert abs(cb.failure_rate - 0.5) < 0.01


@pytest.mark.unit
class TestRateLimiter:
    """Tests for token-bucket RateLimiter"""

    def test_new_client_is_allowed(self):
        """A fresh client starts with a full bucket — first request allowed."""
        limiter = RateLimiter(capacity=10, refill_rate=1.0)
        assert limiter.is_allowed("client-A") is True

    def test_exceeding_capacity_is_rejected(self):
        """A client that exhausts their tokens gets rejected."""
        limiter = RateLimiter(capacity=3, refill_rate=0.0)  # No refill

        assert limiter.is_allowed("client-X") is True
        assert limiter.is_allowed("client-X") is True
        assert limiter.is_allowed("client-X") is True
        assert limiter.is_allowed("client-X") is False  # Bucket empty

    def test_different_clients_have_independent_buckets(self):
        """Rate limits are per-client — one client exhausting their quota
        does not affect others."""
        limiter = RateLimiter(capacity=2, refill_rate=0.0)

        limiter.is_allowed("client-A")
        limiter.is_allowed("client-A")
        assert limiter.is_allowed("client-A") is False  # A is exhausted

        assert limiter.is_allowed("client-B") is True  # B is untouched

    def test_reset_restores_full_bucket(self):
        """reset() gives the client a fresh full bucket."""
        limiter = RateLimiter(capacity=2, refill_rate=0.0)
        limiter.is_allowed("client-Z")
        limiter.is_allowed("client-Z")
        assert limiter.is_allowed("client-Z") is False

        limiter.reset("client-Z")
        assert limiter.is_allowed("client-Z") is True


@pytest.mark.unit
@pytest.mark.asyncio
class TestAPIGateway:
    """Tests for APIGateway routing, rate limiting, and circuit breaking"""

    def _make_gateway(self, **kwargs) -> APIGateway:
        """Create a gateway with high rate limits by default to avoid noise."""
        rl = RateLimiter(capacity=1000, refill_rate=1000.0)
        return APIGateway(rate_limiter=rl, **kwargs)

    async def test_route_found_returns_200(self):
        """
        Requests to registered routes are forwarded and return the backend response.
        """
        gw = self._make_gateway()
        gw.register_route("/api/v1/products", "http://products:8001")

        mock_response = {"status_code": 200, "body": b'{"ok": true}', "headers": {}}

        with patch.object(gw, "_forward_request", new=AsyncMock(return_value=mock_response)):
            result = await gw.handle_request("/api/v1/products/list", client_id="user-1")

        assert result["status_code"] == 200
        assert result["routed_to"] == "http://products:8001"

    async def test_unknown_path_returns_404(self):
        """Requests to unregistered paths return 404."""
        gw = self._make_gateway()
        gw.register_route("/api/v1/products", "http://products:8001")

        result = await gw.handle_request("/api/v2/unknown", client_id="user-1")

        assert result["status_code"] == 404

    async def test_rate_limited_client_returns_429(self):
        """A client that exceeds the rate limit gets a 429 response."""
        rl = RateLimiter(capacity=0, refill_rate=0.0)  # Instantly exhausted
        gw = APIGateway(rate_limiter=rl)
        gw.register_route("/api/v1/products", "http://products:8001")

        result = await gw.handle_request("/api/v1/products", client_id="spammer")

        assert result["status_code"] == 429

    async def test_open_circuit_returns_503(self):
        """
        When a route's circuit is OPEN, requests return 503 without hitting backend.
        """
        gw = self._make_gateway()
        gw.register_route(
            "/api/v1/orders",
            "http://orders:8002",
            failure_threshold=0.5,
        )

        route = gw.get_route("/api/v1/orders")
        # Manually trip the circuit
        route.circuit_breaker._state = CircuitState.OPEN
        route.circuit_breaker._opened_at = time.monotonic()

        result = await gw.handle_request("/api/v1/orders", client_id="user-1")

        assert result["status_code"] == 503

    async def test_backend_error_records_failure(self):
        """Backend errors are recorded in the circuit breaker."""
        gw = self._make_gateway()
        gw.register_route("/api/v1/products", "http://products:8001")

        with patch.object(gw, "_forward_request", new=AsyncMock(side_effect=Exception("timeout"))):
            result = await gw.handle_request("/api/v1/products", client_id="user-1")

        assert result["status_code"] == 502
        route = gw.get_route("/api/v1/products")
        assert route.circuit_breaker.failure_rate > 0

    async def test_longest_prefix_matching(self):
        """
        The most specific (longest) matching route wins.
        "/api/v1/products/detail" → "/api/v1/products", not "/api/v1".
        """
        gw = self._make_gateway()
        gw.register_route("/api/v1", "http://general:8000")
        gw.register_route("/api/v1/products", "http://products:8001")

        route = gw.get_route("/api/v1/products/br-001")
        assert route.backend_url == "http://products:8001"

    def test_get_health_returns_all_routes(self):
        """get_health() includes all registered routes with circuit states."""
        gw = self._make_gateway()
        gw.register_route("/api/v1/products", "http://products:8001")
        gw.register_route("/api/v1/orders", "http://orders:8002")

        health = gw.get_health()

        assert health["total_routes"] == 2
        assert len(health["routes"]) == 2
        assert all(r["circuit_state"] == "closed" for r in health["routes"])


@pytest.mark.unit
class TestSSRFProtection:
    """Security tests — verify SSRF protection in register_route()"""

    def test_valid_internal_service_url_accepted(self):
        """Internal service hostnames are accepted."""
        gw = APIGateway()
        gw.register_route("/api/v1/products", "http://products-service:8001")
        gw.register_route("/api/v1/orders", "http://orders:8002")
        assert len(gw._routes) == 2

    def test_cloud_metadata_ip_blocked(self):
        """AWS/GCP metadata endpoint (169.254.169.254) is blocked."""
        gw = APIGateway()
        with pytest.raises(ValueError, match="not allowed"):
            gw.register_route("/api/v1/x", "http://169.254.169.254/latest/meta-data/")

    def test_file_scheme_blocked(self):
        """file:// scheme is blocked — would read local files."""
        gw = APIGateway()
        with pytest.raises(ValueError, match="not allowed"):
            gw.register_route("/api/v1/x", "file:///etc/passwd")

    def test_localhost_accepted(self):
        """localhost and 127.0.0.1 are valid for development."""
        gw = APIGateway()
        gw.register_route("/api/v1/x", "http://localhost:8001")
        gw.register_route("/api/v1/y", "http://127.0.0.1:8002")
        assert len(gw._routes) == 2

    @pytest.mark.asyncio
    async def test_path_traversal_blocked(self):
        """/../ path traversal attempts return 400."""
        rl = RateLimiter(capacity=1000, refill_rate=1000.0)
        gw = APIGateway(rate_limiter=rl)
        gw.register_route("/api/v1/products", "http://products:8001")

        result = await gw.handle_request(
            "/api/v1/products/../../admin/secrets", client_id="attacker"
        )

        assert result["status_code"] == 400

    def test_rate_limiter_bounded_client_storage(self):
        """
        RateLimiter evicts oldest clients when max_clients is exceeded.
        Prevents memory exhaustion from unique-ID flooding.
        """
        limiter = RateLimiter(capacity=100, refill_rate=10.0, max_clients=5)

        for i in range(10):
            limiter.is_allowed(f"client-{i}")

        assert len(limiter._buckets) <= 5
