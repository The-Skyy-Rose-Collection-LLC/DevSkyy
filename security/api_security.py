"""
Comprehensive API Security Hardening
=====================================

Enterprise-grade API security for DevSkyy Platform:
- CORS configuration
- Security headers
- API versioning security
- Request/response validation
- API key management
- Request signing
- Replay attack prevention
"""

import hashlib
import hmac
import logging
import secrets
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from fastapi import HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class APISecurityLevel(str, Enum):
    """API security levels"""

    PUBLIC = "public"  # No authentication required
    BASIC = "basic"  # API key required
    STANDARD = "standard"  # JWT token required
    ELEVATED = "elevated"  # JWT + MFA required
    CRITICAL = "critical"  # JWT + MFA + request signing


class CORSConfig(BaseModel):
    """CORS configuration"""

    allow_origins: list[str] = Field(default_factory=lambda: ["*"])
    allow_methods: list[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "PATCH"]
    )
    allow_headers: list[str] = Field(
        default_factory=lambda: [
            "Authorization",
            "Content-Type",
            "X-API-Key",
            "X-Request-ID",
            "X-Timestamp",
            "X-Signature",
            "X-CSRF-Token",
        ]
    )
    allow_credentials: bool = True
    max_age: int = 600  # 10 minutes
    expose_headers: list[str] = Field(
        default_factory=lambda: [
            "X-Request-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ]
    )


class SecurityHeadersConfig(BaseModel):
    """Security headers configuration"""

    strict_transport_security: str = "max-age=31536000; includeSubDomains; preload"
    x_content_type_options: str = "nosniff"
    x_frame_options: str = "DENY"
    x_xss_protection: str = "1; mode=block"
    referrer_policy: str = "strict-origin-when-cross-origin"
    permissions_policy: str = "geolocation=(), microphone=(), camera=(), payment=()"
    cache_control: str = "no-store, no-cache, must-revalidate, private"
    pragma: str = "no-cache"


class APIKeyConfig(BaseModel):
    """API key configuration"""

    key_id: str
    key_hash: str  # SHA-256 hash of the key
    name: str
    owner_id: str
    permissions: list[str] = Field(default_factory=list)
    rate_limit: int = 1000  # requests per minute
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    is_active: bool = True
    allowed_ips: list[str] = Field(default_factory=list)
    allowed_origins: list[str] = Field(default_factory=list)


class RequestSignature(BaseModel):
    """Request signature for replay attack prevention"""

    timestamp: int
    nonce: str
    signature: str
    key_id: str


class APISecurityManager:
    """
    Comprehensive API security manager.

    Features:
    - CORS configuration and enforcement
    - Security headers management
    - API key generation and validation
    - Request signing and verification
    - Replay attack prevention
    - API versioning security
    - Request/response validation
    """

    def __init__(self):
        self.cors_config = CORSConfig()
        self.headers_config = SecurityHeadersConfig()

        # API key storage (in production, use database)
        self.api_keys: dict[str, APIKeyConfig] = {}

        # Nonce cache for replay attack prevention
        self.used_nonces: set[str] = set()
        self.nonce_expiry_seconds = 300  # 5 minutes

        # Request signing secret
        self.signing_secret = secrets.token_bytes(32)

        # Supported API versions
        self.supported_versions = {"v1", "v2"}
        self.deprecated_versions = {"v1"}  # v1 is deprecated but still supported
        self.current_version = "v2"

    def generate_api_key(
        self,
        name: str,
        owner_id: str,
        permissions: list[str] = None,
        rate_limit: int = 1000,
        expires_in_days: int = 365,
    ) -> tuple[str, APIKeyConfig]:
        """Generate a new API key"""
        # Generate key components
        key_id = f"sk_{secrets.token_hex(8)}"
        key_secret = secrets.token_urlsafe(32)
        full_key = f"{key_id}_{key_secret}"

        # Hash the key for storage
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()

        # Create configuration
        config = APIKeyConfig(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            owner_id=owner_id,
            permissions=permissions or ["read"],
            rate_limit=rate_limit,
            expires_at=datetime.now(UTC) + timedelta(days=expires_in_days),
        )

        # Store configuration
        self.api_keys[key_id] = config

        logger.info(f"Generated API key {key_id} for {owner_id}")

        # Return full key (only shown once) and config
        return full_key, config

    def validate_api_key(self, api_key: str, request: Request = None) -> APIKeyConfig | None:
        """Validate an API key"""
        if not api_key or "_" not in api_key:
            return None

        # Extract key ID
        parts = api_key.split("_", 2)
        if len(parts) < 3:
            return None

        key_id = f"{parts[0]}_{parts[1]}"

        # Get configuration
        config = self.api_keys.get(key_id)
        if not config:
            return None

        # Verify key hash
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        if not hmac.compare_digest(key_hash, config.key_hash):
            return None

        # Check if active
        if not config.is_active:
            return None

        # Check expiration
        if config.expires_at and datetime.now(UTC) > config.expires_at:
            return None

        # Check IP restrictions
        if config.allowed_ips and request:
            client_ip = request.client.host if request.client else ""
            if client_ip not in config.allowed_ips:
                logger.warning(f"API key {key_id} used from unauthorized IP: {client_ip}")
                return None

        # Check origin restrictions
        if config.allowed_origins and request:
            origin = request.headers.get("origin", "")
            if origin and origin not in config.allowed_origins:
                logger.warning(f"API key {key_id} used from unauthorized origin: {origin}")
                return None

        return config

    def sign_request(
        self, method: str, path: str, body: bytes = b"", timestamp: int = None
    ) -> RequestSignature:
        """Sign a request for verification"""
        timestamp = timestamp or int(time.time())
        nonce = secrets.token_hex(16)

        # Create signature payload
        payload = f"{method}:{path}:{timestamp}:{nonce}:{hashlib.sha256(body).hexdigest()}"

        # Generate HMAC signature
        signature = hmac.new(self.signing_secret, payload.encode(), hashlib.sha256).hexdigest()

        return RequestSignature(
            timestamp=timestamp, nonce=nonce, signature=signature, key_id="system"
        )

    def verify_request_signature(
        self, request: Request, signature: RequestSignature, body: bytes = b""
    ) -> bool:
        """Verify request signature to prevent tampering and replay attacks"""
        # Check timestamp (prevent replay attacks)
        current_time = int(time.time())
        if abs(current_time - signature.timestamp) > self.nonce_expiry_seconds:
            logger.warning("Request signature timestamp expired")
            return False

        # Check nonce (prevent replay attacks)
        nonce_key = f"{signature.nonce}:{signature.timestamp}"
        if nonce_key in self.used_nonces:
            logger.warning("Request nonce already used (replay attack detected)")
            return False

        # Add nonce to used set
        self.used_nonces.add(nonce_key)

        # Clean old nonces periodically
        self._cleanup_old_nonces()

        # Recreate signature
        payload = f"{request.method}:{request.url.path}:{signature.timestamp}:{signature.nonce}:{hashlib.sha256(body).hexdigest()}"

        expected_signature = hmac.new(
            self.signing_secret, payload.encode(), hashlib.sha256
        ).hexdigest()

        # Constant-time comparison
        return hmac.compare_digest(signature.signature, expected_signature)

    def _cleanup_old_nonces(self):
        """Clean up expired nonces"""
        # In production, use Redis with TTL
        if len(self.used_nonces) > 10000:
            self.used_nonces.clear()

    def validate_api_version(self, version: str) -> tuple[bool, str | None]:
        """Validate API version and return deprecation warning if applicable"""
        if version not in self.supported_versions:
            return False, f"API version {version} is not supported. Use {self.current_version}"

        if version in self.deprecated_versions:
            return (
                True,
                f"API version {version} is deprecated. Please migrate to {self.current_version}",
            )

        return True, None

    def get_security_headers(self) -> dict[str, str]:
        """Get all security headers"""
        return {
            "Strict-Transport-Security": self.headers_config.strict_transport_security,
            "X-Content-Type-Options": self.headers_config.x_content_type_options,
            "X-Frame-Options": self.headers_config.x_frame_options,
            "X-XSS-Protection": self.headers_config.x_xss_protection,
            "Referrer-Policy": self.headers_config.referrer_policy,
            "Permissions-Policy": self.headers_config.permissions_policy,
            "Cache-Control": self.headers_config.cache_control,
            "Pragma": self.headers_config.pragma,
        }

    def get_cors_config(self) -> dict[str, Any]:
        """Get CORS configuration for FastAPI middleware"""
        return {
            "allow_origins": self.cors_config.allow_origins,
            "allow_methods": self.cors_config.allow_methods,
            "allow_headers": self.cors_config.allow_headers,
            "allow_credentials": self.cors_config.allow_credentials,
            "max_age": self.cors_config.max_age,
            "expose_headers": self.cors_config.expose_headers,
        }


class APISecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for API security enforcement"""

    def __init__(self, app, security_manager: APISecurityManager = None):
        super().__init__(app)
        self.security_manager = security_manager or APISecurityManager()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply security checks and headers"""
        # Validate API version if present in path
        path = request.url.path
        if path.startswith("/api/"):
            parts = path.split("/")
            if len(parts) >= 3:
                version = parts[2]
                is_valid, warning = self.security_manager.validate_api_version(version)

                if not is_valid:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=warning)

        # Process request
        response = await call_next(request)

        # Add security headers
        for header, value in self.security_manager.get_security_headers().items():
            response.headers[header] = value

        # Add request ID for tracing
        request_id = request.headers.get("X-Request-ID", secrets.token_hex(8))
        response.headers["X-Request-ID"] = request_id

        return response


# Global instance
api_security = APISecurityManager()
