        import re
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time

from fastapi import Request, Response, status
from pydantic import ValidationError

from api.validation_models import SecurityViolationResponse, ValidationErrorResponse
from collections import defaultdict, deque
from typing import Dict, List, Optional
import logging
import uuid

"""
Security Middleware for DevSkyy Enterprise Platform
Comprehensive security enforcement, rate limiting, and threat detection
"""

logger = logging.getLogger(__name__)

# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """Advanced rate limiter with multiple strategies"""

    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.blocked_ips: Dict[str, datetime] = {}
        self.suspicious_patterns: Dict[str, int] = defaultdict(int)

        # Rate limits (requests per minute)
        self.limits = {
            "default": 60,
            "auth": 10,
            "ml": 30,
            "agents": 100,
            "admin": 200,
        }

        # Burst limits (requests per second)
        self.burst_limits = {
            "default": 10,
            "auth": 2,
            "ml": 5,
            "agents": 15,
            "admin": 30,
        }

    def is_allowed(
        self, client_ip: str, endpoint_category: str = "default"
    ) -> tuple[bool, Optional[str]]:
        """Check if request is allowed based on rate limits"""
        now = datetime.now()

        # Check if IP is temporarily blocked
        if client_ip in self.blocked_ips:
            if now < self.blocked_ips[client_ip]:
                return False, "IP temporarily blocked due to suspicious activity"
            else:
                del self.blocked_ips[client_ip]

        # Clean old requests (older than 1 minute)
        minute_ago = now - timedelta(minutes=1)
        second_ago = now - timedelta(seconds=1)

        client_requests = self.requests[client_ip]

        # Remove old requests
        while client_requests and client_requests[0] < minute_ago:
            client_requests.popleft()

        # Check rate limits
        requests_per_minute = len(client_requests)
        requests_per_second = sum(
            1 for req_time in client_requests if req_time > second_ago
)

        minute_limit = self.limits.get(endpoint_category, self.limits["default"])
        burst_limit = self.burst_limits.get(
            endpoint_category, self.burst_limits["default"]
        )

        if requests_per_minute >= minute_limit:
            self._record_violation(client_ip, "rate_limit_exceeded")
            return False, f"Rate limit exceeded: {minute_limit} requests per minute"

        if requests_per_second >= burst_limit:
            self._record_violation(client_ip, "burst_limit_exceeded")
            return False, f"Burst limit exceeded: {burst_limit} requests per second"

        # Record this request
        client_requests.append(now)
        return True, None

    def _record_violation(self, client_ip: str, violation_type: str):
        """Record security violation and potentially block IP"""
        self.suspicious_patterns[client_ip] += 1

        # Block IP if too many violations
        if self.suspicious_patterns[client_ip] >= 5:
            self.blocked_ips[client_ip] = datetime.now() + timedelta(minutes=15)
            logger.warning(
                f"🚨 IP {client_ip} blocked for 15 minutes due to {violation_type}"
            )

# ============================================================================
# SECURITY PATTERNS DETECTION
# ============================================================================

class ThreatDetector:
    """Advanced threat detection system"""

    def __init__(self):
        self.suspicious_patterns = [
            # SQL Injection patterns
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(--|#|/\*|\*/)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            # XSS patterns
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            # Path traversal
            r"(\.\./|\.\.\\)",
            r"(/etc/passwd|/etc/shadow)",
            # Command injection
            r"(;|\||\&\&|\|\|)",
            r"(\$\(|\`)",
        ]

        self.blocked_user_agents = [
            "sqlmap",
            "nikto",
            "nmap",
            "masscan",
            "burpsuite",
        ]

    def analyze_request(
        self, request: Request
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """Analyze request for security threats"""

        # Check User-Agent
        user_agent = request.headers.get("user-agent", "").lower()
        for blocked_agent in self.blocked_user_agents:
            if blocked_agent in user_agent:
                return (
                    False,
                    "blocked_user_agent",
                    f"Blocked user agent: {blocked_agent}",
                )

        # Check URL for suspicious patterns
        url_path = str(request.url.path)
        query_params = str(request.url.query) if request.url.query else ""

        for pattern in self.suspicious_patterns:
            if re.search(pattern, url_path + query_params, re.IGNORECASE):
                return (
                    False,
                    "suspicious_pattern",
                    f"Suspicious pattern detected: {pattern}",
                )

        # Check for excessive header size (potential DoS)
        total_header_size = sum(len(k) + len(v) for k, v in request.headers.items())
        if total_header_size > 8192:  # 8KB limit
            return False, "excessive_headers", "Request headers too large"

        return True, None, None

# ============================================================================
# SECURITY MIDDLEWARE
# ============================================================================

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware"""

    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = RateLimiter()
        self.threat_detector = ThreatDetector()
        self.request_log: List[Dict] = deque(maxlen=1000)  # Keep last 1000 requests

    async def dispatch(self, request: Request, call_next):
        """Process request through security pipeline"""
        start_time = time.time()
        request_id = str(uuid.uuid4())
        client_ip = self._get_client_ip(request)

        # Add request ID to request state
        request.state.request_id = request_id

        try:
            # 1. Threat Detection
            is_safe, threat_type, threat_message = self.threat_detector.analyze_request(
                request
            )
            if not is_safe:
                return await self._security_violation_response(
                    request_id, client_ip, threat_type, threat_message
                )

            # 2. Rate Limiting
            endpoint_category = self._get_endpoint_category(request.url.path)
            is_allowed, rate_message = self.rate_limiter.is_allowed(
                client_ip, endpoint_category
            )
            if not is_allowed:
                return await self._rate_limit_response(
                    request_id, client_ip, rate_message
                )

            # 3. Process request
            response = await call_next(request)

            # 4. Log successful request
            processing_time = time.time() - start_time
            await self._log_request(
                request, response, request_id, client_ip, processing_time
            )

            # 5. Add security headers
            response = self._add_security_headers(response, request_id)

            return response

        except ValidationError as e:
            return await self._validation_error_response(request_id, e)
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return await self._internal_error_response(request_id)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        # Check for forwarded headers (behind proxy/load balancer)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _get_endpoint_category(self, path: str) -> str:
        """Categorize endpoint for rate limiting"""
        if "/auth/" in path:
            return "auth"
        elif "/ml/" in path:
            return "ml"
        elif "/agents/" in path:
            return "agents"
        elif "/admin/" in path:
            return "admin"
        else:
            return "default"

    def _add_security_headers(self, response: Response, request_id: str) -> Response:
        """Add security headers to response"""
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response

    async def _security_violation_response(
        self, request_id: str, client_ip: str, threat_type: str, message: str
    ) -> JSONResponse:
        """Return security violation response"""
        logger.warning(
            f"🚨 Security violation: {threat_type} from {client_ip} - {message}"
        )

        response_data = SecurityViolationResponse(
            violation_type=threat_type, message=message, request_id=request_id
        )

        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN, content=response_data.dict()
        )

    async def _rate_limit_response(
        self, request_id: str, client_ip: str, message: str
    ) -> JSONResponse:
        """Return rate limit response"""
        logger.warning(f"⚠️ Rate limit exceeded: {client_ip} - {message}")

        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "rate_limit_exceeded",
                "message": message,
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def _validation_error_response(
        self, request_id: str, error: ValidationError
    ) -> JSONResponse:
        """Return validation error response"""
        response_data = ValidationErrorResponse(
            message="Request validation failed",
            details=[
                {"field": err["loc"], "message": err["msg"]} for err in error.errors()
            ],
            request_id=request_id,
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response_data.dict(),
        )

    async def _internal_error_response(self, request_id: str) -> JSONResponse:
        """Return internal error response"""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_server_error",
                "message": "An internal error occurred",
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def _log_request(
        self,
        request: Request,
        response: Response,
        request_id: str,
        client_ip: str,
        processing_time: float,
    ):
        """Log request for monitoring and analysis"""
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "client_ip": client_ip,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "processing_time_ms": round(processing_time * 1000, 2),
            "user_agent": request.headers.get("user-agent", ""),
        }

        self.request_log.append(log_entry)

        # Log to structured logger
        logger.info(
            f"🌐 {request.method} {request.url.path} - "
            f"{response.status_code} - {log_entry['processing_time_ms']}ms - "
            f"{client_ip} - {request_id}"
        )
