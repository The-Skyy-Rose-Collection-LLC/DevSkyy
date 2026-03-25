"""
Core Authentication Interfaces
==============================

Abstract base classes defining contracts for authentication components.
Implementations in security/ module will implement these interfaces.

This enables dependency inversion - api/ depends on abstractions (interfaces),
not concrete implementations (security/).

MUST NOT depend on api/, security/, agents/, or services/ modules.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import AuthCredentials, AuthResult, TokenResponse
    from .token_payload import TokenPayload
    from .types import TokenType


class ITokenValidator(ABC):
    """
    Interface for token validation.

    Implementations must validate JWT tokens and return decoded payloads.

    Usage:
        class JWTValidator(ITokenValidator):
            def validate_token(self, token: str, expected_type: TokenType) -> TokenPayload:
                # Implementation
                pass
    """

    @abstractmethod
    def validate_token(
        self,
        token: str,
        expected_type: TokenType | None = None,
    ) -> TokenPayload:
        """
        Validate a token and return the decoded payload.

        Args:
            token: JWT token string
            expected_type: Expected token type (optional validation)

        Returns:
            Decoded TokenPayload

        Raises:
            InvalidTokenError: If token is invalid
            ExpiredTokenError: If token has expired
        """
        ...

    @abstractmethod
    def is_token_revoked(self, jti: str) -> bool:
        """
        Check if a token has been revoked.

        Args:
            jti: JWT ID (unique token identifier)

        Returns:
            True if token is revoked, False otherwise
        """
        ...


class IAuthProvider(ABC):
    """
    Interface for authentication providers.

    Implementations handle user authentication and token management.

    Usage:
        class JWTAuthProvider(IAuthProvider):
            async def authenticate(self, credentials: AuthCredentials) -> AuthResult:
                # Implementation
                pass
    """

    @abstractmethod
    async def authenticate(
        self,
        credentials: AuthCredentials,
        *,
        correlation_id: str | None = None,
    ) -> AuthResult:
        """
        Authenticate user with credentials.

        Args:
            credentials: User credentials (username/password)
            correlation_id: Request correlation ID for tracing

        Returns:
            AuthResult with tokens on success, error on failure
        """
        ...

    @abstractmethod
    async def refresh_tokens(
        self,
        refresh_token: str,
        *,
        correlation_id: str | None = None,
    ) -> TokenResponse:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token
            correlation_id: Request correlation ID for tracing

        Returns:
            New TokenResponse with fresh tokens

        Raises:
            InvalidTokenError: If refresh token is invalid
            ExpiredTokenError: If refresh token has expired
        """
        ...

    @abstractmethod
    async def revoke_token(
        self,
        token: str,
        *,
        correlation_id: str | None = None,
    ) -> None:
        """
        Revoke a specific token.

        Args:
            token: Token to revoke
            correlation_id: Request correlation ID for tracing
        """
        ...

    @abstractmethod
    async def revoke_all_user_tokens(
        self,
        user_id: str,
        *,
        correlation_id: str | None = None,
    ) -> None:
        """
        Revoke all tokens for a user (logout all sessions).

        Args:
            user_id: User identifier
            correlation_id: Request correlation ID for tracing
        """
        ...


class ITokenBlacklist(ABC):
    """
    Interface for token blacklist storage.

    Implementations manage revoked tokens for security.
    """

    @abstractmethod
    def add(self, jti: str, expires_at: datetime) -> None:
        """
        Add token to blacklist.

        Args:
            jti: JWT ID (unique token identifier)
            expires_at: Token expiration time (for cleanup)
        """
        ...

    @abstractmethod
    def is_blacklisted(self, jti: str) -> bool:
        """
        Check if token is blacklisted.

        Args:
            jti: JWT ID to check

        Returns:
            True if blacklisted, False otherwise
        """
        ...

    @abstractmethod
    def revoke_family(self, family_id: str) -> None:
        """
        Revoke all tokens in a family.

        Args:
            family_id: Token family identifier
        """
        ...

    @abstractmethod
    def is_family_revoked(self, family_id: str) -> bool:
        """
        Check if token family is revoked.

        Args:
            family_id: Family ID to check

        Returns:
            True if family is revoked, False otherwise
        """
        ...


class IRateLimiter(ABC):
    """
    Interface for rate limiting.

    Implementations track and limit request rates.
    """

    @abstractmethod
    def is_allowed(self, key: str) -> bool:
        """
        Check if action is allowed under rate limit.

        Args:
            key: Rate limit key (e.g., "login:{ip}:{username}")

        Returns:
            True if allowed, False if rate limited
        """
        ...

    @abstractmethod
    def record_attempt(self, key: str) -> None:
        """
        Record an attempt for rate limiting.

        Args:
            key: Rate limit key
        """
        ...

    @abstractmethod
    def get_remaining_attempts(self, key: str) -> int:
        """
        Get remaining attempts before rate limit.

        Args:
            key: Rate limit key

        Returns:
            Number of remaining attempts
        """
        ...

    @abstractmethod
    def get_reset_time(self, key: str) -> datetime | None:
        """
        Get time when rate limit resets.

        Args:
            key: Rate limit key

        Returns:
            Reset datetime or None if no limit active
        """
        ...


class IPasswordHasher(ABC):
    """
    Interface for password hashing.

    Implementations handle secure password hashing and verification.
    """

    @abstractmethod
    def hash_password(self, password: str) -> str:
        """
        Hash a password securely.

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        ...

    @abstractmethod
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify password against hash.

        Args:
            password: Plain text password to verify
            hashed_password: Stored hash to compare against

        Returns:
            True if password matches, False otherwise
        """
        ...

    @abstractmethod
    def needs_rehash(self, hashed_password: str) -> bool:
        """
        Check if password needs rehashing (algorithm upgrade).

        Args:
            hashed_password: Stored hash to check

        Returns:
            True if rehash needed, False otherwise
        """
        ...
