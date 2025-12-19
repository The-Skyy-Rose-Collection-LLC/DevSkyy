"""
Comprehensive Security Middleware
=================================

Integrated security middleware for DevSkyy Enterprise Platform that combines:
- Rate limiting
- Input validation
- Authentication verification
- CSRF protection
- Security headers
- Request logging
- Threat detection
"""

import json
import logging
import secrets
import time
from collections.abc import Callable

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from .advanced_auth import AdvancedAuthManager
from .input_validation import SecurityValidator
from .rate_limiting import AdvancedRateLimiter

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware that provides:
    - Rate limiting with DDoS protection
    - Input validation and sanitization
    - Authentication and session management
    - CSRF protection
    - Security headers
    - Request/response logging
    - Threat detection and blocking
    """

    def __init__(
        self,
        app,
        auth_manager: AdvancedAuthManager | None = None,
        rate_limiter: AdvancedRateLimiter | None = None,
        validator: SecurityValidator | None = None,
        enable_csrf: bool = True,
        enable_logging: bool = True,
        protected_endpoints: list[str] | None = None,
    ):
        super().__init__(app)

        # Initialize security components
        self.auth_manager = auth_manager or AdvancedAuthManager()
        self.rate_limiter = rate_limiter or AdvancedRateLimiter()
        self.validator = validator or SecurityValidator()

        # Configuration
        self.enable_csrf = enable_csrf
        self.enable_logging = enable_logging

        # Protected endpoints that require authentication
        self.protected_endpoints = protected_endpoints or [
            "/api/v1/agents/",
            "/api/v1/user/",
            "/api/v1/admin/",
        ]

        # Public endpoints that don't require authentication
        self.public_endpoints = {
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/",
        }

        # Security headers to add to all responses
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "X-Permitted-Cross-Domain-Policies": "none",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Resource-Policy": "same-origin",
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main middleware dispatch method"""
        start_time = time.time()

        try:
            # 1. Rate limiting check
            await self._check_rate_limits(request)

            # 2. Basic security validation
            await self._validate_request_security(request)

            # 3. Authentication check for protected endpoints
            await self._check_authentication(request)

            # 4. Input validation for POST/PUT/PATCH requests
            if request.method in ["POST", "PUT", "PATCH"]:
                await self._validate_input(request)

            # 5. CSRF protection for state-changing requests
            if self.enable_csrf and request.method in ["POST", "PUT", "PATCH", "DELETE"]:
                await self._check_csrf_protection(request)

            # Process the request
            response = await call_next(request)

            # 6. Add security headers to response
            self._add_security_headers(response)

            # 7. Log successful request
            if self.enable_logging:
                self._log_request(request, response, time.time() - start_time)

            return response

        except HTTPException as e:
            # Log security violations
            if self.enable_logging:
                self._log_security_violation(request, e, time.time() - start_time)
            raise

        except Exception as e:
            # Log unexpected errors
            logger.error(f"Security middleware error: {e}")
            if self.enable_logging:
                self._log_error(request, e, time.time() - start_time)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal security error"
            )

    async def _check_rate_limits(self, request: Request):
        """Check rate limits for the request"""
        try:
            await self.rate_limiter.enforce_rate_limit(request)
        except HTTPException:
            # Log rate limit violation
            ip = request.client.host if request.client else "unknown"
            logger.warning(f"Rate limit exceeded for IP {ip} on {request.url.path}")
            raise

    async def _validate_request_security(self, request: Request):
        """Perform basic security validation on the request"""
        # Check request size
        if not self.validator.validate_request_size(request, max_size=10 * 1024 * 1024):  # 10MB
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Request too large"
            )

        # Check for suspicious headers
        user_agent = request.headers.get("user-agent", "")
        if not user_agent or len(user_agent) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or missing User-Agent header",
            )

        # Check for parameter pollution in query parameters
        if request.query_params:
            pollution_indicators = self.validator.detect_parameter_pollution(
                dict(request.query_params)
            )
            if pollution_indicators:
                logger.warning(f"Parameter pollution detected: {pollution_indicators}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request parameters"
                )

    async def _check_authentication(self, request: Request):
        """Check authentication for protected endpoints"""
        path = request.url.path

        # Skip authentication for public endpoints
        if path in self.public_endpoints:
            return

        # Check if endpoint requires authentication
        requires_auth = any(path.startswith(protected) for protected in self.protected_endpoints)

        if requires_auth:
            # Extract token from Authorization header
            auth_header = request.headers.get("authorization", "")
            if not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing or invalid authorization header",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            token = auth_header.split(" ", 1)[1]

            # Validate token (simplified - in production use your JWT validation)
            if not token or len(token) < 10:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Store user info in request state for later use
            request.state.authenticated = True
            request.state.token = token

    async def _validate_input(self, request: Request):
        """Validate input data for security issues"""
        try:
            # Get request body
            body = await request.body()
            if not body:
                return

            # Parse JSON if content type is JSON
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    json_data = json.loads(body)

                    # Validate JSON structure and content
                    validation_result = self.validator.validate_json_input(json_data)

                    if not validation_result["valid"]:
                        logger.warning(f"Input validation failed: {validation_result['errors']}")
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data"
                        )

                    # Store sanitized data in request state
                    request.state.sanitized_data = validation_result["sanitized_data"]

                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON format"
                    )

        except Exception as e:
            logger.error(f"Input validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Input validation failed"
            )

    async def _check_csrf_protection(self, request: Request):
        """Check CSRF protection for state-changing requests"""
        if not self.enable_csrf:
            return

        # Skip CSRF for API requests with proper authentication
        if request.headers.get("authorization"):
            return

        # Check for CSRF token in headers or form data
        csrf_token = request.headers.get("x-csrf-token")

        if not csrf_token:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token missing")

        # Validate CSRF token (simplified implementation)
        session_id = request.headers.get("x-session-id", "")
        if not self.validator.validate_csrf_token(csrf_token, session_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")

    def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        for header, value in self.security_headers.items():
            response.headers[header] = value

        # Add CSP header with cryptographically secure nonce
        nonce = secrets.token_hex(16)
        csp = f"default-src 'self'; script-src 'self' 'nonce-{nonce}'; style-src 'self' 'unsafe-inline'"
        response.headers["Content-Security-Policy"] = csp

    def _log_request(self, request: Request, response: Response, duration: float):
        """Log successful request"""
        ip = request.client.host if request.client else "unknown"
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"IP: {ip} Status: {response.status_code} Duration: {duration:.3f}s"
        )

    def _log_security_violation(self, request: Request, exception: HTTPException, duration: float):
        """Log security violation"""
        ip = request.client.host if request.client else "unknown"
        logger.warning(
            f"Security violation: {request.method} {request.url.path} "
            f"IP: {ip} Status: {exception.status_code} "
            f"Detail: {exception.detail} Duration: {duration:.3f}s"
        )

    def _log_error(self, request: Request, exception: Exception, duration: float):
        """Log unexpected error"""
        ip = request.client.host if request.client else "unknown"
        logger.error(
            f"Error: {request.method} {request.url.path} "
            f"IP: {ip} Exception: {str(exception)} Duration: {duration:.3f}s"
        )


# Factory function to create security middleware
def create_security_middleware(
    enable_csrf: bool = True,
    enable_logging: bool = True,
    protected_endpoints: list[str] | None = None,
) -> SecurityMiddleware:
    """Create configured security middleware instance"""
    return SecurityMiddleware(
        app=None,  # Will be set by FastAPI
        enable_csrf=enable_csrf,
        enable_logging=enable_logging,
        protected_endpoints=protected_endpoints,
    )
