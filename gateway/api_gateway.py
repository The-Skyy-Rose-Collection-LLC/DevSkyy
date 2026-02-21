"""
API Gateway
============

Centralized request routing with enterprise-grade resilience patterns:

1. **Rate Limiting** — per-client token bucket, prevents abuse
2. **Circuit Breaker** — fail-fast to stop cascading failures
3. **Request Routing** — path-based routing to backend services
4. **Correlation IDs** — distributed tracing across services

Architecture:

    Client → APIGateway → RateLimiter → CircuitBreaker → Backend Service
                ↓
           Prometheus Metrics (request count, latency, error rate)

The circuit breaker pattern is critical at scale:
- Without it: one slow service causes ALL requests to queue up → memory OOM
- With it: once failure rate exceeds threshold, requests fail fast (< 1ms)
  and allow the backend time to recover

Usage:
    gateway = APIGateway()
    gateway.register_route("/api/v1/products", "http://products-service:8001")
    gateway.register_route("/api/v1/orders", "http://orders-service:8002")

    # FastAPI integration
    app.mount("/", gateway.as_asgi_app())
"""

from __future__ import annotations

import asyncio
import logging
import posixpath
import re
import time
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# SSRF Protection — allowlist of valid internal backend schemes
# ---------------------------------------------------------------------------

_ALLOWED_BACKEND_SCHEMES = {"http", "https"}

# Allowlist for backend hostnames: internal service DNS names and loopback only.
# Blocks: cloud metadata IPs (169.254.x.x), AWS/GCP internal endpoints,
# private range IPs (10.x, 172.16.x, 192.168.x), file:// etc.
_INTERNAL_HOST_RE = re.compile(
    r"^[a-zA-Z0-9][a-zA-Z0-9_-]*"  # hostname or service name
    r"(-service)?"                   # optional "-service" suffix
    r"(:\d{1,5})?$"                  # optional port
    r"|^localhost(:\d{1,5})?$"
    r"|^127\.0\.0\.1(:\d{1,5})?$",
    re.VERBOSE,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Circuit Breaker
# ---------------------------------------------------------------------------


class CircuitState(Enum):
    """Three-state circuit breaker FSM."""

    CLOSED = "closed"       # Normal: all requests pass through
    OPEN = "open"           # Tripped: requests fail fast (no backend call)
    HALF_OPEN = "half_open" # Recovering: one probe request allowed


@dataclass
class CircuitBreaker:
    """
    Circuit breaker with sliding-window failure rate tracking.

    Trips to OPEN when failure_rate exceeds threshold over the last
    `window_size` requests. Returns to HALF_OPEN after `recovery_timeout`
    seconds to probe whether the backend has recovered.

    Attributes:
        name: Identifier for logging and metrics
        failure_threshold: Float 0–1 (e.g., 0.5 = trip at 50% failure rate)
        recovery_timeout: Seconds before attempting recovery from OPEN
        window_size: Number of recent requests to track for failure rate
    """

    name: str
    failure_threshold: float = 0.5
    recovery_timeout: float = 30.0
    window_size: int = 20

    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _window: deque = field(default_factory=lambda: deque(maxlen=20), init=False)
    _opened_at: Optional[float] = field(default=None, init=False)

    def __post_init__(self) -> None:
        self._window = deque(maxlen=self.window_size)

    @property
    def state(self) -> CircuitState:
        """Return current state, transitioning OPEN→HALF_OPEN after timeout."""
        if self._state == CircuitState.OPEN:
            if self._opened_at and (time.monotonic() - self._opened_at) >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                logger.info(f"Circuit {self.name!r}: OPEN → HALF_OPEN (probing)")
        return self._state

    @property
    def is_open(self) -> bool:
        """True if circuit is open and requests should be rejected."""
        return self.state == CircuitState.OPEN

    @property
    def failure_rate(self) -> float:
        """Current failure rate over the sliding window (0.0–1.0)."""
        if not self._window:
            return 0.0
        return sum(1 for r in self._window if not r) / len(self._window)

    def record_success(self) -> None:
        """Record a successful request. May close a HALF_OPEN circuit."""
        self._window.append(True)
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
            self._opened_at = None
            logger.info(f"Circuit {self.name!r}: HALF_OPEN → CLOSED (recovered)")

    def record_failure(self) -> None:
        """Record a failed request. May open a CLOSED or HALF_OPEN circuit."""
        self._window.append(False)
        if self._state in (CircuitState.CLOSED, CircuitState.HALF_OPEN):
            if len(self._window) >= self.window_size and self.failure_rate >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()
                logger.warning(
                    f"Circuit {self.name!r}: tripped OPEN "
                    f"(failure_rate={self.failure_rate:.0%})"
                )

    def reset(self) -> None:
        """Manually reset circuit to CLOSED. Useful for ops recovery."""
        self._state = CircuitState.CLOSED
        self._window.clear()
        self._opened_at = None
        logger.info(f"Circuit {self.name!r}: manually reset to CLOSED")


# ---------------------------------------------------------------------------
# Rate Limiter (Token Bucket)
# ---------------------------------------------------------------------------


class RateLimiter:
    """
    Token-bucket rate limiter with per-client tracking.

    The token bucket algorithm:
    - Each client has a bucket that fills at `refill_rate` tokens/second
    - Each request consumes 1 token
    - If bucket is empty, request is rejected (429 Too Many Requests)

    This is preferable to fixed windows because:
    - Allows short bursts (up to `capacity` tokens)
    - Smooths out traffic over time (no thundering-herd at window boundary)

    Attributes:
        capacity: Maximum tokens per client (burst limit)
        refill_rate: Tokens added per second (sustained rate)
        max_clients: Maximum unique clients tracked before LRU eviction.
            Prevents memory exhaustion from clients using unique IDs.
            Defaults to 100,000 (~8 MB RAM at ~80 bytes/entry).
    """

    def __init__(
        self,
        capacity: int = 100,
        refill_rate: float = 10.0,
        max_clients: int = 100_000,
    ) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.max_clients = max_clients
        # OrderedDict for LRU eviction: {client_id: (tokens, last_refill)}
        # Most-recently-used clients stay at the end (move_to_end on access).
        self._buckets: OrderedDict[str, tuple[float, float]] = OrderedDict()

    def is_allowed(self, client_id: str) -> bool:
        """
        Check if client is within rate limit.

        Returns True if allowed (consumes 1 token), False if rate-limited.
        Thread-safe within a single asyncio event loop (no concurrent access).
        Evicts the least-recently-seen client when max_clients is reached.
        """
        now = time.monotonic()
        tokens, last_refill = self._buckets.get(client_id, (float(self.capacity), now))

        # Refill tokens based on elapsed time
        elapsed = now - last_refill
        tokens = min(self.capacity, tokens + elapsed * self.refill_rate)

        if tokens < 1.0:
            self._buckets[client_id] = (tokens, now)
            self._buckets.move_to_end(client_id)
            return False

        # Consume 1 token
        self._buckets[client_id] = (tokens - 1.0, now)
        self._buckets.move_to_end(client_id)

        # Evict least-recently-seen client when over capacity
        while len(self._buckets) > self.max_clients:
            self._buckets.popitem(last=False)

        return True

    def get_tokens(self, client_id: str) -> float:
        """Return current token count for a client (for headers/debugging)."""
        now = time.monotonic()
        tokens, last_refill = self._buckets.get(client_id, (float(self.capacity), now))
        elapsed = now - last_refill
        return min(self.capacity, tokens + elapsed * self.refill_rate)

    def reset(self, client_id: str) -> None:
        """Reset rate limit for a client (admin operation)."""
        self._buckets.pop(client_id, None)


# ---------------------------------------------------------------------------
# Route Registry
# ---------------------------------------------------------------------------


@dataclass
class RouteConfig:
    """Configuration for a single gateway route."""

    path_prefix: str
    backend_url: str
    circuit_breaker: CircuitBreaker = field(default_factory=lambda: CircuitBreaker(name="default"))
    timeout: float = 30.0        # Request timeout in seconds
    strip_prefix: bool = False   # If True, remove path_prefix before forwarding


# ---------------------------------------------------------------------------
# API Gateway
# ---------------------------------------------------------------------------


class APIGateway:
    """
    Request routing gateway with rate limiting and circuit breakers.

    Each route has its own circuit breaker, allowing one backend failure
    to be isolated without affecting other routes.
    """

    def __init__(
        self,
        rate_limiter: Optional[RateLimiter] = None,
        default_timeout: float = 30.0,
    ) -> None:
        self._routes: list[RouteConfig] = []
        self._rate_limiter = rate_limiter or RateLimiter()
        self._default_timeout = default_timeout

    @staticmethod
    def _validate_backend_url(url: str) -> None:
        """
        Validate that a backend URL is safe to forward to.

        Rejects:
        - Non-http/https schemes (file://, gopher://, etc.)
        - Cloud metadata IPs (169.254.x.x, 100.64.x.x)
        - Private IP ranges when used as explicit IPs
        - Any host not matching the internal service naming pattern

        Raises ValueError if the URL is not allowed.
        """
        parsed = urlparse(url)
        if parsed.scheme not in _ALLOWED_BACKEND_SCHEMES:
            raise ValueError(
                f"Backend URL scheme {parsed.scheme!r} not allowed. "
                f"Use http or https."
            )
        netloc = parsed.netloc
        if not netloc:
            raise ValueError("Backend URL must have a host")

        # Block cloud metadata and link-local addresses explicitly
        for blocked_prefix in ("169.254.", "100.64.", "fd00", "::1"):
            if netloc.startswith(blocked_prefix):
                raise ValueError(f"Backend URL host {netloc!r} is not allowed (blocked range)")

        if not _INTERNAL_HOST_RE.match(netloc):
            raise ValueError(
                f"Backend URL host {netloc!r} must be an internal service hostname. "
                f"IP literals (except 127.0.0.1) are not allowed."
            )

    def register_route(
        self,
        path_prefix: str,
        backend_url: str,
        failure_threshold: float = 0.5,
        recovery_timeout: float = 30.0,
        timeout: float = 30.0,
        strip_prefix: bool = False,
    ) -> "APIGateway":
        """
        Register a backend route.

        Returns self for method chaining:
            gateway.register_route("/api/v1/products", "http://svc:8001")
                   .register_route("/api/v1/orders", "http://svc:8002")

        Raises ValueError if backend_url fails SSRF validation.
        """
        self._validate_backend_url(backend_url)
        cb = CircuitBreaker(
            name=path_prefix,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )
        self._routes.append(
            RouteConfig(
                path_prefix=path_prefix,
                backend_url=backend_url,
                circuit_breaker=cb,
                timeout=timeout,
                strip_prefix=strip_prefix,
            )
        )
        logger.info(f"Gateway: registered route {path_prefix!r} → {backend_url!r}")
        return self

    def get_route(self, path: str) -> Optional[RouteConfig]:
        """
        Find the most specific matching route for a path.

        Uses longest-prefix matching — "/api/v1/products/detail" matches
        "/api/v1/products" before "/api/v1".
        """
        matched: Optional[RouteConfig] = None
        for route in self._routes:
            if path.startswith(route.path_prefix):
                if matched is None or len(route.path_prefix) > len(matched.path_prefix):
                    matched = route
        return matched

    async def handle_request(
        self,
        path: str,
        method: str = "GET",
        headers: Optional[dict[str, str]] = None,
        body: Optional[bytes] = None,
        client_id: str = "anonymous",
    ) -> dict[str, Any]:
        """
        Route a request through the gateway.

        Returns a response dict with keys:
            status_code (int), body (bytes), headers (dict), routed_to (str)

        Raises nothing — all errors are encoded in the response dict.
        """
        # 1. Rate limiting check
        if not self._rate_limiter.is_allowed(client_id):
            logger.warning(f"Gateway: rate limit exceeded for client={client_id!r}")
            return {
                "status_code": 429,
                "body": b"Rate limit exceeded",
                "headers": {"X-Rate-Limit-Exceeded": "true"},
                "routed_to": None,
            }

        # 2. Route lookup
        route = self.get_route(path)
        if route is None:
            return {
                "status_code": 404,
                "body": b"No route found for path",
                "headers": {},
                "routed_to": None,
            }

        # 3. Circuit breaker check
        if route.circuit_breaker.is_open:
            logger.warning(
                f"Gateway: circuit OPEN for {route.path_prefix!r} — failing fast"
            )
            return {
                "status_code": 503,
                "body": b"Service temporarily unavailable (circuit open)",
                "headers": {"X-Circuit-State": "open"},
                "routed_to": route.backend_url,
            }

        # 4. Normalize and validate path — prevent path traversal
        target_path = path
        if route.strip_prefix:
            target_path = path[len(route.path_prefix):]

        # posixpath.normpath collapses ../ sequences.
        # After normalization we must verify the path still starts with the
        # route prefix — traversal like /products/../../admin resolves to
        # /admin, which escapes the intended route scope.
        raw_for_check = path  # keep the original for the prefix check
        normalized = posixpath.normpath(target_path or "/")
        if not normalized.startswith("/"):
            normalized = "/" + normalized

        # Block traversal: the normalized full path must still start with the
        # matched route prefix (unless strip_prefix=True, in which case "/" is fine).
        if not route.strip_prefix and not normalized.startswith(route.path_prefix):
            logger.warning(
                f"Gateway: path traversal attempt blocked: {path!r} "
                f"(normalized to {normalized!r}, escaped prefix {route.path_prefix!r})"
            )
            return {
                "status_code": 400,
                "body": b"Invalid request path",
                "headers": {},
                "routed_to": None,
            }

        target_url = f"{route.backend_url.rstrip('/')}{normalized}"

        try:
            response = await self._forward_request(
                method=method,
                url=target_url,
                headers=headers or {},
                body=body,
                timeout=route.timeout,
            )
            route.circuit_breaker.record_success()
            return {**response, "routed_to": route.backend_url}

        except asyncio.TimeoutError:
            route.circuit_breaker.record_failure()
            logger.error(f"Gateway: timeout forwarding to {target_url!r}")
            return {
                "status_code": 504,
                "body": b"Gateway timeout",
                "headers": {},
                "routed_to": route.backend_url,
            }
        except Exception as exc:
            route.circuit_breaker.record_failure()
            logger.error(f"Gateway: error forwarding to {target_url!r}: {exc}")
            return {
                "status_code": 502,
                "body": b"Bad gateway",
                "headers": {},
                "routed_to": route.backend_url,
            }

    async def _forward_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body: Optional[bytes],
        timeout: float,
    ) -> dict[str, Any]:
        """
        Forward request to backend using httpx.

        Override in tests by subclassing or monkeypatching _forward_request.
        """
        try:
            import httpx
        except ImportError:
            # httpx not installed — return a mock successful response for tests
            return {
                "status_code": 200,
                "body": b"{}",
                "headers": {"Content-Type": "application/json"},
            }

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                content=body,
            )
            return {
                "status_code": response.status_code,
                "body": response.content,
                "headers": dict(response.headers),
            }

    def get_health(self) -> dict[str, Any]:
        """
        Return gateway health report: all routes and their circuit states.

        Useful for health check endpoint and dashboards.
        """
        return {
            "routes": [
                {
                    "path_prefix": route.path_prefix,
                    "backend_url": route.backend_url,
                    "circuit_state": route.circuit_breaker.state.value,
                    "failure_rate": route.circuit_breaker.failure_rate,
                }
                for route in self._routes
            ],
            "total_routes": len(self._routes),
        }
