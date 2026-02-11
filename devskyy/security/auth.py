"""
DevSkyy Authentication Service
==============================

Enterprise-grade authentication with:
- JWT tokens (RFC 7519 compliant)
- Password hashing with Argon2/bcrypt
- Token verification and refresh
- Explicit error handling

Security References:
- RFC 7519: JSON Web Token (JWT)
- RFC 8725: JWT Best Current Practices
- OWASP Password Storage Cheat Sheet
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Optional

import jwt
from passlib.context import CryptContext


class AuthErrorCode(Enum):
    """Explicit error codes for authentication operations."""

    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    TOKEN_MALFORMED = "TOKEN_MALFORMED"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_LOCKED = "USER_LOCKED"
    USER_INACTIVE = "USER_INACTIVE"
    PASSWORD_WEAK = "PASSWORD_WEAK"


class AuthenticationError(Exception):
    """Base exception for authentication operations."""

    def __init__(self, message: str, code: AuthErrorCode, details: Optional[str] = None):
        self.code = code
        self.details = details
        super().__init__(f"[{code.value}] {message}")


class TokenExpiredError(AuthenticationError):
    """Exception for expired tokens."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, AuthErrorCode.TOKEN_EXPIRED)


class InvalidTokenError(AuthenticationError):
    """Exception for invalid tokens."""

    def __init__(self, message: str = "Token is invalid", details: Optional[str] = None):
        super().__init__(message, AuthErrorCode.TOKEN_INVALID, details)


@dataclass(frozen=True)
class AuthConfig:
    """Immutable authentication configuration.

    Attributes:
        secret_key: JWT signing key (should be 256+ bits)
        algorithm: JWT algorithm (HS256, RS256, etc.)
        access_token_expire_minutes: Access token lifetime
        refresh_token_expire_days: Refresh token lifetime
        issuer: JWT issuer claim
        audience: JWT audience claim
    """

    secret_key: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    issuer: str = "devskyy"
    audience: str = "devskyy-api"


@dataclass(frozen=True)
class TokenPayload:
    """Validated JWT token payload."""

    sub: str  # Subject (usually user ID or username)
    exp: datetime  # Expiration time
    iat: datetime  # Issued at
    jti: str  # JWT ID (for revocation)
    user_id: Optional[int] = None
    roles: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenPayload":
        """Create TokenPayload from decoded JWT dict."""
        return cls(
            sub=data.get("sub", ""),
            exp=datetime.fromtimestamp(data["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(data.get("iat", 0), tz=timezone.utc),
            jti=data.get("jti", ""),
            user_id=data.get("user_id"),
            roles=tuple(data.get("roles", [])),
            permissions=tuple(data.get("permissions", [])),
        )


class SecurityManager:
    """Enterprise authentication and security manager.

    Features:
    - JWT token generation and verification
    - Password hashing with Argon2 (bcrypt fallback)
    - Token refresh flow
    - Explicit error handling

    Example:
        >>> mgr = SecurityManager(AuthConfig(secret_key="my-secret"))
        >>> hashed = mgr.hash_password("user-password")
        >>> assert mgr.verify_password("user-password", hashed)
        >>> token = mgr.create_access_token({"sub": "user123", "user_id": 1})
        >>> payload = mgr.verify_token(token)
    """

    def __init__(self, config: Optional[AuthConfig] = None) -> None:
        """Initialize security manager.

        Args:
            config: Optional authentication configuration
        """
        self._config = config or AuthConfig()
        self._pwd_context = CryptContext(
            schemes=["argon2", "bcrypt"],
            deprecated="auto",
            argon2__time_cost=2,
            argon2__memory_cost=65536,
            argon2__parallelism=1,
            bcrypt__rounds=12,
        )

    @property
    def config(self) -> AuthConfig:
        """Get current configuration (read-only)."""
        return self._config

    def hash_password(self, password: str) -> str:
        """Hash password using Argon2 (or bcrypt fallback).

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        return self._pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Stored hash to verify against

        Returns:
            True if password matches, False otherwise
        """
        try:
            return self._pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False

    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create JWT access token.

        Args:
            data: Payload data (must include 'sub')
            expires_delta: Optional custom expiration

        Returns:
            Encoded JWT string

        Example:
            >>> token = mgr.create_access_token({"sub": "user123", "user_id": 1})
        """
        to_encode = data.copy()
        now = datetime.now(timezone.utc)

        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=self._config.access_token_expire_minutes)

        to_encode.update(
            {
                "exp": expire,
                "iat": now,
                "jti": secrets.token_urlsafe(16),
                "iss": self._config.issuer,
                "aud": self._config.audience,
            }
        )

        return jwt.encode(
            to_encode,
            self._config.secret_key,
            algorithm=self._config.algorithm,
        )

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token with longer expiration.

        Args:
            data: Payload data (must include 'sub')

        Returns:
            Encoded JWT refresh token
        """
        expires_delta = timedelta(days=self._config.refresh_token_expire_days)
        to_encode = data.copy()
        to_encode["token_type"] = "refresh"
        return self.create_access_token(to_encode, expires_delta)

    def verify_token(self, token: str) -> TokenPayload:
        """Verify and decode JWT token.

        Args:
            token: JWT token string

        Returns:
            Validated TokenPayload

        Raises:
            TokenExpiredError: If token has expired
            InvalidTokenError: If token is malformed or invalid
        """
        try:
            payload = jwt.decode(
                token,
                self._config.secret_key,
                algorithms=[self._config.algorithm],
                issuer=self._config.issuer,
                audience=self._config.audience,
            )
            return TokenPayload.from_dict(payload)
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError()
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(details=str(e))

    def decode_token_unsafe(self, token: str) -> Dict[str, Any]:
        """Decode token without verification (for debugging only).

        WARNING: Do not use for authentication! This is for debugging only.

        Args:
            token: JWT token string

        Returns:
            Decoded payload dict
        """
        return jwt.decode(
            token,
            options={"verify_signature": False},
        )

    def generate_api_key(self, prefix: str = "dsk") -> str:
        """Generate a secure API key.

        Args:
            prefix: Key prefix for identification

        Returns:
            API key in format: {prefix}_{random_string}
        """
        random_part = secrets.token_urlsafe(32)
        return f"{prefix}_{random_part}"

    def validate_password_strength(self, password: str) -> tuple[bool, list[str]]:
        """Validate password meets security requirements.

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        if len(password) < 8:
            errors.append("Password must be at least 8 characters")
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")

        return len(errors) == 0, errors
