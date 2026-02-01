"""
Core Authentication Models
==========================

Pydantic models for authentication data structures.
These models are used for request/response validation and data transfer.

MUST NOT depend on api/, security/, agents/, or services/ modules.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from .types import AuthErrorCode, AuthStatus, SubscriptionTier, UserRole


class AuthCredentials(BaseModel):
    """
    Authentication credentials for login requests.

    Supports both username and email-based authentication.
    """

    username: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Username or email address",
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="User password",
    )


class TokenRequest(BaseModel):
    """Token request model for OAuth2 login."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """
    Token response model following OAuth2 conventions.

    Includes both access and refresh tokens with metadata.
    """

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Seconds until access token expires")
    refresh_expires_in: int = Field(..., description="Seconds until refresh token expires")
    scope: str | None = Field(default=None, description="OAuth2 scope (optional)")


class TokenPair(BaseModel):
    """
    Internal token pair representation.

    Used for token creation and refresh operations.
    """

    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime
    family_id: str


class AuthResult(BaseModel):
    """
    Result of an authentication attempt.

    Contains status, optional tokens, and error information.
    """

    status: AuthStatus
    tokens: TokenResponse | None = None
    error_code: AuthErrorCode | None = None
    error_message: str | None = None
    user_id: str | None = None
    requires_mfa: bool = False
    mfa_token: str | None = None

    @property
    def is_success(self) -> bool:
        """Check if authentication was successful."""
        return self.status == AuthStatus.SUCCESS


class UserBase(BaseModel):
    """
    Base user model with common fields.

    Used as foundation for UserCreate and UserInDB.
    """

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Unique username (alphanumeric, underscore, hyphen)",
    )
    email: EmailStr = Field(..., description="User email address")
    roles: list[UserRole] = Field(
        default=[UserRole.API_USER],
        description="User roles for RBAC",
    )
    tier: SubscriptionTier = Field(
        default=SubscriptionTier.FREE,
        description="Subscription tier",
    )


class UserCreate(UserBase):
    """
    User registration model with OWASP password validation.

    Validates password strength according to OWASP guidelines:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (must meet strength requirements)",
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """OWASP password strength validation."""
        errors: list[str] = []

        if len(v) < 8:
            errors.append("at least 8 characters")
        if not any(c.isupper() for c in v):
            errors.append("uppercase letter")
        if not any(c.islower() for c in v):
            errors.append("lowercase letter")
        if not any(c.isdigit() for c in v):
            errors.append("digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            errors.append("special character")

        if errors:
            raise ValueError(f"Password must contain: {', '.join(errors)}")

        return v


class UserInDB(BaseModel):
    """
    User model as stored in database.

    Contains all user fields including security-sensitive data.
    """

    id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Unique username")
    email: str = Field(..., description="User email address")
    hashed_password: str = Field(..., description="Argon2id hashed password")
    roles: list[str] = Field(
        default_factory=lambda: [UserRole.API_USER.value],
        description="User roles",
    )
    tier: str = Field(
        default=SubscriptionTier.FREE.value,
        description="Subscription tier",
    )
    is_active: bool = Field(default=True, description="Account active status")
    is_verified: bool = Field(default=False, description="Email verification status")
    failed_login_attempts: int = Field(default=0, description="Failed login counter")
    locked_until: datetime | None = Field(default=None, description="Account lockout timestamp")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Account creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Last update timestamp",
    )
    last_login: datetime | None = Field(default=None, description="Last successful login")

    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until is None:
            return False
        return datetime.now(UTC) < self.locked_until

    def get_roles_as_enum(self) -> list[UserRole]:
        """Convert role strings to UserRole enums."""
        result: list[UserRole] = []
        for role_str in self.roles:
            try:
                result.append(UserRole(role_str))
            except ValueError:
                continue
        return result
