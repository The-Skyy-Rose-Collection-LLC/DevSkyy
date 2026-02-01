"""
Token Payload
=============

Dataclass representing decoded JWT token payload.
Contains all claims from a validated token.

MUST NOT depend on api/, security/, agents/, or services/ modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import TokenType, UserRole


@dataclass
class TokenPayload:
    """
    Decoded token payload structure.

    Contains all JWT claims for an authenticated user.
    Used throughout the application for authorization decisions.

    Attributes:
        sub: Subject (user_id) - RFC 7519
        jti: JWT ID (unique identifier) - RFC 7519
        type: Token type (access, refresh, etc.)
        roles: User roles for RBAC
        family_id: Token family for rotation tracking
        tier: Subscription tier for rate limiting
        exp: Expiration time - RFC 7519
        iat: Issued at time - RFC 7519
        iss: Issuer - RFC 7519
        aud: Audience - RFC 7519

    Usage:
        payload = token_validator.validate_token(token)
        if payload.has_role(UserRole.ADMIN):
            # Admin-specific logic
            pass
    """

    sub: str  # Subject (user_id)
    jti: str  # JWT ID (unique identifier)
    type: TokenType  # Token type
    roles: list[str] = field(default_factory=list)  # User roles
    family_id: str | None = None  # Token family for rotation tracking
    tier: str = "free"  # Subscription tier
    exp: datetime | None = None  # Expiration time
    iat: datetime | None = None  # Issued at time
    iss: str | None = None  # Issuer
    aud: str | None = None  # Audience

    def has_role(self, role: UserRole) -> bool:
        """
        Check if payload has a specific role.

        Args:
            role: UserRole to check for

        Returns:
            True if user has the role, False otherwise
        """
        return role.value in self.roles

    def has_any_role(self, roles: set[UserRole]) -> bool:
        """
        Check if payload has any of the specified roles.

        Args:
            roles: Set of UserRole to check

        Returns:
            True if user has at least one role, False otherwise
        """
        role_values = {r.value for r in roles}
        return bool(set(self.roles) & role_values)

    def has_all_roles(self, roles: set[UserRole]) -> bool:
        """
        Check if payload has all of the specified roles.

        Args:
            roles: Set of UserRole to check

        Returns:
            True if user has all roles, False otherwise
        """
        role_values = {r.value for r in roles}
        return role_values.issubset(set(self.roles))

    def get_highest_role(self) -> UserRole | None:
        """
        Get the highest privilege role.

        Uses ROLE_HIERARCHY to determine privilege levels.

        Returns:
            Highest UserRole or None if no valid roles
        """
        # Import here to avoid circular dependency at module level
        from .role_hierarchy import ROLE_HIERARCHY
        from .types import UserRole

        max_level = -1
        highest: UserRole | None = None

        for role_str in self.roles:
            try:
                role = UserRole(role_str)
                level = ROLE_HIERARCHY.get(role, 0)
                if level > max_level:
                    max_level = level
                    highest = role
            except ValueError:
                continue

        return highest

    @property
    def user_id(self) -> str:
        """Alias for sub (subject) claim."""
        return self.sub

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        if self.exp is None:
            return False
        from datetime import UTC

        return datetime.now(UTC) > self.exp

    def __post_init__(self) -> None:
        """Validate required fields after initialization."""
        if not self.sub:
            raise ValueError("Token payload must have a subject (sub)")
        if not self.jti:
            raise ValueError("Token payload must have a JWT ID (jti)")
