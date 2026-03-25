"""
DevSkyy Core Auth Module
========================

Zero-dependency authentication types, models, and interfaces.
This module breaks circular dependencies between api ↔ security modules.

This module MUST NOT depend on:
- api/
- security/
- agents/
- services/

Only depends on:
- pydantic (for models)
- standard library

Usage:
    from core.auth import UserRole, TokenPayload, TokenType
    from core.auth import IAuthProvider, ITokenValidator
    from core.auth import ROLE_HIERARCHY, get_role_level
"""

from .interfaces import (
    IAuthProvider,
    IPasswordHasher,
    IRateLimiter,
    ITokenBlacklist,
    ITokenValidator,
)
from .models import (
    AuthCredentials,
    AuthResult,
    TokenPair,
    TokenRequest,
    TokenResponse,
    UserBase,
    UserCreate,
    UserInDB,
)
from .role_hierarchy import (
    ROLE_HIERARCHY,
    get_highest_role_from_list,
    get_minimum_required_level,
    get_role_level,
    get_roles_at_or_above,
    has_required_role,
    is_role_at_least,
)
from .token_payload import TokenPayload
from .types import (
    AuthErrorCode,
    AuthStatus,
    Permission,
    SubscriptionTier,
    TokenType,
    UserRole,
)

__all__ = [
    # Types (Enums)
    "UserRole",
    "TokenType",
    "AuthStatus",
    "AuthErrorCode",
    "Permission",
    "SubscriptionTier",
    # Token Payload
    "TokenPayload",
    # Role Hierarchy
    "ROLE_HIERARCHY",
    "get_role_level",
    "is_role_at_least",
    "has_required_role",
    "get_minimum_required_level",
    "get_roles_at_or_above",
    "get_highest_role_from_list",
    # Models (Pydantic)
    "AuthCredentials",
    "AuthResult",
    "TokenRequest",
    "TokenResponse",
    "TokenPair",
    "UserBase",
    "UserCreate",
    "UserInDB",
    # Interfaces (Abstract Base Classes)
    "IAuthProvider",
    "ITokenValidator",
    "ITokenBlacklist",
    "IRateLimiter",
    "IPasswordHasher",
]
