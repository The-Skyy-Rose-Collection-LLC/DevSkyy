"""
Core Authentication Types
=========================

Zero-dependency enumerations for authentication and authorization.
These types are used throughout the codebase and must not import
from api/, security/, agents/, or services/ modules.

Standards:
- RFC 7519: JWT Token Types
- OWASP: RBAC Role Definitions
"""

from __future__ import annotations

from enum import Enum


class UserRole(str, Enum):
    """
    RBAC Roles - ordered by privilege level.

    Privilege Hierarchy (highest to lowest):
    - SUPER_ADMIN: Full system access, can manage other admins
    - ADMIN: Administrative access, can manage users and settings
    - DEVELOPER: API and development access, can access developer tools
    - API_USER: Standard API access for authenticated users
    - READ_ONLY: Read-only access, cannot modify data
    - GUEST: Minimal access, typically for unauthenticated preview

    Usage:
        from core.auth import UserRole

        user_role = UserRole.API_USER
        if user_role == UserRole.ADMIN:
            # Admin-specific logic
            pass
    """

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    DEVELOPER = "developer"
    API_USER = "api_user"
    READ_ONLY = "read_only"
    GUEST = "guest"

    def __str__(self) -> str:
        return self.value


class TokenType(str, Enum):
    """
    Token types for different authentication purposes.

    Types:
    - ACCESS: Short-lived token for API access (typically 15 min)
    - REFRESH: Long-lived token for obtaining new access tokens (typically 7 days)
    - RESET_PASSWORD: Single-use token for password reset flows
    - VERIFY_EMAIL: Single-use token for email verification
    - API_KEY: Long-lived token for machine-to-machine communication

    Usage:
        from core.auth import TokenType

        if token_payload.type == TokenType.ACCESS:
            # Validate as access token
            pass
    """

    ACCESS = "access"
    REFRESH = "refresh"
    RESET_PASSWORD = "reset_password"
    VERIFY_EMAIL = "verify_email"
    API_KEY = "api_key"

    def __str__(self) -> str:
        return self.value


class AuthStatus(str, Enum):
    """
    Authentication status codes for auth operations.

    Used in AuthResult to indicate the outcome of authentication attempts.
    """

    SUCCESS = "success"
    FAILED = "failed"
    EXPIRED = "expired"
    REVOKED = "revoked"
    LOCKED = "locked"
    MFA_REQUIRED = "mfa_required"
    INVALID_CREDENTIALS = "invalid_credentials"
    RATE_LIMITED = "rate_limited"

    def __str__(self) -> str:
        return self.value


class AuthErrorCode(str, Enum):
    """
    Error codes for authentication failures.

    Provides machine-readable error codes for client applications.
    """

    INVALID_TOKEN = "invalid_token"
    EXPIRED_TOKEN = "expired_token"
    REVOKED_TOKEN = "revoked_token"
    INVALID_CREDENTIALS = "invalid_credentials"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_DISABLED = "account_disabled"
    MFA_REQUIRED = "mfa_required"
    MFA_FAILED = "mfa_failed"
    RATE_LIMITED = "rate_limited"
    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"
    SESSION_EXPIRED = "session_expired"
    INVALID_REFRESH_TOKEN = "invalid_refresh_token"

    def __str__(self) -> str:
        return self.value


class Permission(str, Enum):
    """
    Fine-grained permissions for resource access control.

    These permissions complement roles for granular access control.
    Format: RESOURCE_ACTION (e.g., USER_READ, PRODUCT_CREATE)
    """

    # User permissions
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_ADMIN = "user:admin"

    # Product permissions
    PRODUCT_READ = "product:read"
    PRODUCT_CREATE = "product:create"
    PRODUCT_UPDATE = "product:update"
    PRODUCT_DELETE = "product:delete"

    # Order permissions
    ORDER_READ = "order:read"
    ORDER_CREATE = "order:create"
    ORDER_UPDATE = "order:update"
    ORDER_DELETE = "order:delete"

    # Analytics permissions
    ANALYTICS_READ = "analytics:read"
    ANALYTICS_EXPORT = "analytics:export"

    # Admin permissions
    ADMIN_ACCESS = "admin:access"
    ADMIN_SETTINGS = "admin:settings"
    ADMIN_AUDIT = "admin:audit"

    # Agent permissions
    AGENT_EXECUTE = "agent:execute"
    AGENT_CONFIGURE = "agent:configure"
    AGENT_ADMIN = "agent:admin"

    def __str__(self) -> str:
        return self.value


class SubscriptionTier(str, Enum):
    """
    Subscription tiers for rate limiting and feature access.

    Each tier has different rate limits and feature access levels.
    """

    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"

    def __str__(self) -> str:
        return self.value
