"""
Enterprise-Grade Middleware for DevSkyy Platform

Implements comprehensive middleware stack per Truth Protocol requirements:
- Rate limiting (Rule #7: Input Validation)
- Security headers (Rule #13: Security Baseline)
- Request/Response logging with PII redaction (Rule #10: No-Skip Rule)
- Performance monitoring (Rule #12: Performance SLOs)
- Error tracking with sanitization (Rule #10: Error Ledger Required)
"""

from collections.abc import Callable
from datetime import datetime
import json
import logging
from pathlib import Path
import re
import time

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger(__name__)

# ============================================================================
# PII REDACTION UTILITIES
# ============================================================================

# Patterns to redact sensitive data
PII_PATTERNS = {
    "password": re.compile(r'"password"\s*:\s*"[^"]*"', re.IGNORECASE),
    "api_key": re.compile(r'"api_key"\s*:\s*"[^"]*"', re.IGNORECASE),
    "token": re.compile(r'"token"\s*:\s*"[^"]*"', re.IGNORECASE),
    "secret": re.compile(r'"secret"\s*:\s*"[^"]*"', re.IGNORECASE),
    "authorization": re.compile(r'"authorization"\s*:\s*"[^"]*"', re.IGNORECASE),
    "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    "credit_card": re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'),
    "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
}


def redact_sensitive_data(text: str) -> str:
    """
    Redact sensitive information from logs and error messages.

    Per Truth Protocol Rule #10 (No-Skip Rule): PII sanitization required.
    """
    if not text:
        return text

    redacted = text
    for pattern_name, pattern in PII_PATTERNS.items():
        if pattern_name in ["password", "api_key", "token", "secret", "authorization"]:
            # For JSON fields, replace the value
            redacted = pattern.sub(f'"{pattern_name}":"***REDACTED***"', redacted)
        else:
            # For direct matches, replace with placeholder
            redacted = pattern.sub(f"[REDACTED_{pattern_name.upper()}]", redacted)

    return redacted


# ============================================================================
# SECURITY HEADERS MIDDLEWARE
# ============================================================================


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add enterprise security headers to all responses.

    Implements OWASP security best practices and Truth Protocol Rule #13.
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """Add security headers to response."""
        response = await call_next(request)

        # Content Security Policy (CSP)
        # Per Truth Protocol Rule #7: CSP headers for browser-based UI
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Frame options
        response.headers["X-Frame-Options"] = "DENY"

        # Strict Transport Security (HSTS)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=()"
        )

        # Remove server header for security
        response.headers["Server"] = "DevSkyy"

        return response


# ============================================================================
# RATE LIMITING MIDDLEWARE
# ============================================================================


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware per Truth Protocol Rule #7.

    Target: 100 requests/minute per IP (as specified in CLAUDE.md).
    """

    def __init__(self, app, rate_limit: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.

        Args:
            app: FastAPI application
            rate_limit: Maximum requests per window
            window_seconds: Time window in seconds
        """
        super().__init__(app)
        self.rate_limit = rate_limit
        self.window_seconds = window_seconds
        self.requests = {}  # {ip: [(timestamp, count), ...]}

    def _clean_old_requests(self, ip: str, current_time: float):
        """Remove requests outside the current window."""
        if ip not in self.requests:
            return

        cutoff_time = current_time - self.window_seconds
        self.requests[ip] = [
            (timestamp, count) for timestamp, count in self.requests[ip] if timestamp > cutoff_time
        ]

    def _get_request_count(self, ip: str, current_time: float) -> int:
        """Get total request count for IP in current window."""
        self._clean_old_requests(ip, current_time)
        return sum(count for _, count in self.requests.get(ip, []))

    def _add_request(self, ip: str, current_time: float):
        """Add a request for the IP."""
        if ip not in self.requests:
            self.requests[ip] = []
        self.requests[ip].append((current_time, 1))

    async def dispatch(self, request: Request, call_next: Callable):
        """Apply rate limiting."""
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics", "/status"]:
            return await call_next(request)

        current_time = time.time()

        # Check rate limit
        request_count = self._get_request_count(client_ip, current_time)

        if request_count >= self.rate_limit:
            logger.warning(
                f"Rate limit exceeded for IP {client_ip}: {request_count}/{self.rate_limit} requests in window"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.rate_limit} requests per {self.window_seconds} seconds",
                    "retry_after": int(self.window_seconds),
                },
                headers={"Retry-After": str(self.window_seconds)},
            )

        # Add request
        self._add_request(client_ip, current_time)

        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(self.rate_limit - request_count - 1)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_seconds))

        return response


# ============================================================================
# REQUEST LOGGING MIDDLEWARE
# ============================================================================


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all requests with PII redaction per Truth Protocol Rule #10.

    Generates structured logs for observability and error tracking.
    """

    def __init__(self, app, log_file: str | None = None):
        """
        Initialize request logging.

        Args:
            app: FastAPI application
            log_file: Optional log file path
        """
        super().__init__(app)
        self.log_file = log_file
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

    async def dispatch(self, request: Request, call_next: Callable):
        """Log request and response."""
        # Start timer
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000000)}"

        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Log request (with PII redaction)
        request_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": client_ip,
            "user_agent": redact_sensitive_data(user_agent),
        }

        # Process request
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            response_log = {
                **request_log,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "success": 200 <= response.status_code < 400,
            }

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Log to file if configured
            if self.log_file:
                with open(self.log_file, "a") as f:
                    f.write(json.dumps(response_log) + "\n")

            # Log to standard logger
            if response.status_code >= 400:
                logger.warning(f"Request failed: {json.dumps(response_log)}")
            else:
                logger.info(f"Request completed: {json.dumps(response_log)}")

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            # Log error (with PII redaction)
            error_log = {
                **request_log,
                "status_code": 500,
                "duration_ms": round(duration_ms, 2),
                "success": False,
                "error": redact_sensitive_data(str(e)),
            }

            logger.error(f"Request error: {json.dumps(error_log)}", exc_info=True)

            if self.log_file:
                with open(self.log_file, "a") as f:
                    f.write(json.dumps(error_log) + "\n")

            # Re-raise exception
            raise


# ============================================================================
# PERFORMANCE MONITORING MIDDLEWARE
# ============================================================================


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Monitor request performance per Truth Protocol Rule #12.

    Target: P95 < 200ms
    """

    def __init__(self, app, p95_threshold_ms: float = 200.0):
        """
        Initialize performance monitoring.

        Args:
            app: FastAPI application
            p95_threshold_ms: P95 latency threshold in milliseconds
        """
        super().__init__(app)
        self.p95_threshold_ms = p95_threshold_ms
        self.latencies = []  # Store last 1000 latencies

    async def dispatch(self, request: Request, call_next: Callable):
        """Monitor request performance."""
        start_time = time.time()

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # Store latency (keep last 1000)
            self.latencies.append(duration_ms)
            if len(self.latencies) > 1000:
                self.latencies.pop(0)

            # Add performance headers
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

            # Warn if over threshold
            if duration_ms > self.p95_threshold_ms:
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path} "
                    f"took {duration_ms:.2f}ms (threshold: {self.p95_threshold_ms}ms)"
                )

            return response

        except Exception:
            # Still track timing even on errors
            duration_ms = (time.time() - start_time) * 1000
            self.latencies.append(duration_ms)
            if len(self.latencies) > 1000:
                self.latencies.pop(0)
            raise

    def get_p95_latency(self) -> float | None:
        """Calculate P95 latency from stored samples."""
        if not self.latencies:
            return None

        sorted_latencies = sorted(self.latencies)
        p95_index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[p95_index] if p95_index < len(sorted_latencies) else sorted_latencies[-1]


# ============================================================================
# FACTORY FUNCTION
# ============================================================================


def add_enterprise_middleware(app, **kwargs):
    """
    Add all enterprise middleware to FastAPI app.

    Args:
        app: FastAPI application
        **kwargs: Configuration options for middleware

    Configuration:
        - rate_limit: Requests per minute (default: 100)
        - rate_window: Rate limit window in seconds (default: 60)
        - p95_threshold: Performance threshold in ms (default: 200)
        - log_file: Request log file path (optional)
    """
    # Performance monitoring
    perf_middleware = PerformanceMonitoringMiddleware(
        app, p95_threshold_ms=kwargs.get("p95_threshold", 200.0)
    )
    app.add_middleware(BaseHTTPMiddleware, dispatch=perf_middleware.dispatch)
    app.state.performance_monitor = perf_middleware

    # Request logging
    log_file = kwargs.get("log_file", "logs/requests.jsonl")
    app.add_middleware(BaseHTTPMiddleware, dispatch=RequestLoggingMiddleware(app, log_file).dispatch)

    # Rate limiting
    app.add_middleware(
        BaseHTTPMiddleware,
        dispatch=RateLimitMiddleware(
            app, rate_limit=kwargs.get("rate_limit", 100), window_seconds=kwargs.get("rate_window", 60)
        ).dispatch,
    )

    # Security headers
    app.add_middleware(BaseHTTPMiddleware, dispatch=SecurityHeadersMiddleware(app).dispatch)

    logger.info("✅ Enterprise middleware stack configured:")
    logger.info("   - Security headers: CSP, HSTS, X-Frame-Options, etc.")
    logger.info(f"   - Rate limiting: {kwargs.get('rate_limit', 100)}/min per IP")
    logger.info(f"   - Performance monitoring: P95 < {kwargs.get('p95_threshold', 200)}ms")
    logger.info(f"   - Request logging: {log_file}")
