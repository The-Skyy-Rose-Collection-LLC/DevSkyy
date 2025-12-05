"""
Role-Based Access Control (RBAC) for DevSkyy Platform

Defines roles and permissions for the multi-agent platform per Truth Protocol Rule #6.

Per CLAUDE.md Truth Protocol:
- Rule #6: RBAC roles – SuperAdmin, Admin, Developer, APIUser, ReadOnly
- Rule #7: Input validation – Schema enforcement and permission checking

Roles Hierarchy (highest to lowest):
1. SuperAdmin - Full platform access, can manage all agents and settings
2. Admin - Agent deployment, configuration, user management
3. Developer - Code deployment, testing, monitoring
4. APIUser - API access for external integrations
5. ReadOnly - View-only access to dashboards and logs
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable


class Role(str, Enum):
    """
    RBAC roles for DevSkyy platform.

    Per Truth Protocol Rule #6, these roles enforce access control across:
    - Agent deployment and management
    - Finetuning operations
    - WordPress integration
    - Security settings
    - User management
    """

    SUPER_ADMIN = "SuperAdmin"
    ADMIN = "Admin"
    DEVELOPER = "Developer"
    API_USER = "APIUser"
    READ_ONLY = "ReadOnly"


# Role hierarchy for permission inheritance
ROLE_HIERARCHY: dict[Role, set[Role]] = {
    Role.SUPER_ADMIN: {Role.SUPER_ADMIN, Role.ADMIN, Role.DEVELOPER, Role.API_USER, Role.READ_ONLY},
    Role.ADMIN: {Role.ADMIN, Role.DEVELOPER, Role.API_USER, Role.READ_ONLY},
    Role.DEVELOPER: {Role.DEVELOPER, Role.API_USER, Role.READ_ONLY},
    Role.API_USER: {Role.API_USER, Role.READ_ONLY},
    Role.READ_ONLY: {Role.READ_ONLY},
}


# Permission definitions per role
ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.SUPER_ADMIN: {
        # Full access
        "manage:users",
        "manage:agents",
        "manage:settings",
        "deploy:agents",
        "finetune:agents",
        "manage:wordpress",
        "manage:security",
        "view:all",
        "delete:all",
    },
    Role.ADMIN: {
        # Agent and deployment management
        "manage:agents",
        "deploy:agents",
        "finetune:agents",
        "manage:wordpress",
        "view:all",
        "manage:users",
    },
    Role.DEVELOPER: {
        # Development and testing
        "deploy:code",
        "test:agents",
        "view:logs",
        "view:metrics",
        "deploy:agents",
    },
    Role.API_USER: {
        # API access
        "api:read",
        "api:write",
        "view:metrics",
    },
    Role.READ_ONLY: {
        # View-only access
        "view:dashboard",
        "view:logs",
    },
}


def has_permission(user_role: Role, required_permission: str) -> bool:
    """
    Check if a role has a specific permission.

    Uses role hierarchy to allow higher roles to inherit lower role permissions.

    Args:
        user_role: The user's role
        required_permission: The permission to check (e.g., "deploy:agents")

    Returns:
        True if the role has the permission, False otherwise

    Example:
        >>> has_permission(Role.ADMIN, "deploy:agents")
        True
        >>> has_permission(Role.READ_ONLY, "deploy:agents")
        False
    """
    # Get all roles this user has access to (including inherited)
    accessible_roles = ROLE_HIERARCHY.get(user_role, {user_role})

    # Check if any accessible role has the required permission
    for role in accessible_roles:
        if required_permission in ROLE_PERMISSIONS.get(role, set()):
            return True

    return False


def is_role_higher_or_equal(user_role: Role, required_role: Role) -> bool:
    """
    Check if user's role is higher than or equal to required role.

    Args:
        user_role: The user's current role
        required_role: The minimum required role

    Returns:
        True if user_role >= required_role in hierarchy

    Example:
        >>> is_role_higher_or_equal(Role.ADMIN, Role.DEVELOPER)
        True
        >>> is_role_higher_or_equal(Role.DEVELOPER, Role.ADMIN)
        False
    """
    accessible_roles = ROLE_HIERARCHY.get(user_role, {user_role})
    return required_role in accessible_roles


# Default role for new users
DEFAULT_ROLE = Role.READ_ONLY

# Roles that can deploy agents
DEPLOYMENT_ROLES = {Role.SUPER_ADMIN, Role.ADMIN, Role.DEVELOPER}

# Roles that can finetune agents
FINETUNING_ROLES = {Role.SUPER_ADMIN, Role.ADMIN}

# Roles that can manage WordPress integration
WORDPRESS_ROLES = {Role.SUPER_ADMIN, Role.ADMIN}


@dataclass(slots=True)
class Permission:
    """Represents a discrete permission and which roles are allowed to use it."""

    name: str
    description: str = ""
    allowed_roles: set[Role] = field(default_factory=set)

    def allows(self, role: Role) -> bool:
        """Return True when the provided role (or any inherited role) is allowed."""
        accessible_roles = ROLE_HIERARCHY.get(role, {role})
        return any(allowed_role in accessible_roles for allowed_role in self.allowed_roles)


class RBACManager:
    """
    Lightweight RBAC manager that mirrors the expectations encoded in the test-suite.

    The manager keeps an in-memory permission registry derived from ROLE_PERMISSIONS but allows
    registering additional permissions at runtime. It also understands user-specific overrides
    via the `permissions` attribute (e.g., ["*", "agent:read"]).
    """

    def __init__(self, permissions: dict[str, Permission] | None = None) -> None:
        self._permissions: dict[str, Permission] = permissions or self._build_default_permissions()
        self._audit_log: list[dict[str, Any]] = []

    # --------------------------------------------------------------------- utils
    @staticmethod
    def _resolve_role(target: Any) -> Role | None:
        """Resolve a Role enum from a user object, dict, str, or Role."""
        if isinstance(target, Role):
            return target
        if isinstance(target, str):
            try:
                return Role(target)
            except ValueError:
                return None
        if isinstance(target, dict) and "role" in target:
            return RBACManager._resolve_role(target["role"])
        role_value = getattr(target, "role", None)
        if role_value is None:
            return None
        return RBACManager._resolve_role(role_value)

    @staticmethod
    def _get_user_permissions(user: Any) -> set[str]:
        raw_permissions = getattr(user, "permissions", None)
        if raw_permissions is None and isinstance(user, dict):
            raw_permissions = user.get("permissions")
        if not raw_permissions:
            return set()
        return set(raw_permissions)

    def _build_default_permissions(self) -> dict[str, Permission]:
        """Create Permission objects from ROLE_PERMISSIONS."""
        permissions: dict[str, Permission] = {}
        for role, role_permissions in ROLE_PERMISSIONS.items():
            for perm_name in role_permissions:
                perm = permissions.get(perm_name)
                if perm is None:
                    perm = Permission(
                        name=perm_name,
                        description=f"Auto-generated permission for {perm_name}",
                    )
                    permissions[perm_name] = perm
                perm.allowed_roles.add(role)
        return permissions

    def _log(self, event: str, user: Any, permission: str, allowed: bool) -> None:
        """Store a minimal audit record for debugging/testing."""
        user_id = getattr(user, "user_id", None) or getattr(user, "id", None)
        username = getattr(user, "username", None)
        self._audit_log.append(
            {
                "event": event,
                "user_id": user_id,
                "username": username,
                "permission": permission,
                "allowed": allowed,
            }
        )

    # ---------------------------------------------------------------- permission API
    def register_permission(self, permission: Permission) -> None:
        """Register a completely custom permission."""
        self._permissions[permission.name] = permission

    def grant_permission_to_role(self, permission_name: str, role: Role) -> None:
        """Grant an existing permission to an additional role."""
        permission = self._permissions.setdefault(
            permission_name,
            Permission(name=permission_name, description=f"Dynamically added permission {permission_name}"),
        )
        permission.allowed_roles.add(role)

    def revoke_permission_from_role(self, permission_name: str, role: Role) -> None:
        """Revoke a role's access to a permission if present."""
        if permission_name in self._permissions:
            self._permissions[permission_name].allowed_roles.discard(role)

    def check_permission(self, user: Any, permission: str) -> bool:
        """
        Evaluate whether the supplied user object has the requested permission.

        Order of evaluation:
        1. User-level overrides via `permissions` attribute (supports "*" wildcard)
        2. Role-derived permissions from ROLE_PERMISSIONS (+ inheritance)
        3. Custom Permission objects registered on the manager
        """
        if user is None:
            self._log("rbac_denied", user, permission, False)
            return False

        user_permissions = self._get_user_permissions(user)
        if "*" in user_permissions or permission in user_permissions:
            self._log("rbac_allowed_user_override", user, permission, True)
            return True

        role = self._resolve_role(user)
        if role is None:
            self._log("rbac_denied_no_role", user, permission, False)
            return False

        permission_entry = self._permissions.get(permission)
        if permission_entry and permission_entry.allows(role):
            self._log("rbac_allowed_role_permission", user, permission, True)
            return True

        allowed = has_permission(role, permission)
        self._log("rbac_allowed_inherited" if allowed else "rbac_denied_role", user, permission, allowed)
        return allowed

    # ---------------------------------------------------------------- helpers for tests/introspection
    @property
    def audit_log(self) -> Iterable[dict[str, Any]]:
        """Expose recorded authorization events (useful for debugging/tests)."""
        return tuple(self._audit_log)


def check_permission(user_role: Role | str, required_permission: str) -> bool:
    """
    Convenience wrapper mirroring historical API where only the role was supplied.
    """
    role = user_role
    if isinstance(user_role, str):
        try:
            role = Role(user_role)
        except ValueError:
            return False
    return has_permission(role, required_permission) if isinstance(role, Role) else False
