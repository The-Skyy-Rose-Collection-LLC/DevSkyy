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

from enum import Enum
from typing import Any


class Permission(str, Enum):
    """
    Permission types for RBAC.

    Fine-grained permission control for DevSkyy platform resources.
    """

    # User management
    MANAGE_USERS = "manage:users"
    VIEW_USERS = "view:users"

    # Agent management
    MANAGE_AGENTS = "manage:agents"
    DEPLOY_AGENTS = "deploy:agents"
    FINETUNE_AGENTS = "finetune:agents"
    TEST_AGENTS = "test:agents"
    VIEW_AGENTS = "view:agents"

    # Settings and configuration
    MANAGE_SETTINGS = "manage:settings"
    VIEW_SETTINGS = "view:settings"

    # WordPress integration
    MANAGE_WORDPRESS = "manage:wordpress"
    VIEW_WORDPRESS = "view:wordpress"

    # Security
    MANAGE_SECURITY = "manage:security"
    VIEW_SECURITY = "view:security"

    # Code deployment
    DEPLOY_CODE = "deploy:code"

    # Monitoring
    VIEW_LOGS = "view:logs"
    VIEW_METRICS = "view:metrics"
    VIEW_DASHBOARD = "view:dashboard"
    VIEW_ALL = "view:all"

    # API access
    API_READ = "api:read"
    API_WRITE = "api:write"

    # Delete operations
    DELETE_ALL = "delete:all"


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


def check_permission(user_role: Role | str, required_permission: str | Permission) -> bool:
    """
    Check if a user with given role has the required permission.

    This is an alias for has_permission with support for string inputs.

    Args:
        user_role: The user's role (Role enum or string)
        required_permission: The permission to check (Permission enum or string)

    Returns:
        True if the role has the permission, False otherwise

    Example:
        >>> check_permission(Role.ADMIN, Permission.DEPLOY_AGENTS)
        True
        >>> check_permission("Developer", "deploy:agents")
        True
    """
    # Convert string role to Role enum if needed
    if isinstance(user_role, str):
        try:
            user_role = Role(user_role)
        except ValueError:
            # Try matching by name
            for role in Role:
                if role.value == user_role or role.name == user_role:
                    user_role = role
                    break
            else:
                return False

    # Convert Permission enum to string if needed
    if isinstance(required_permission, Permission):
        required_permission = required_permission.value

    return has_permission(user_role, required_permission)


class RBACManager:
    """
    Role-Based Access Control Manager for DevSkyy Platform.

    Provides centralized RBAC functionality including:
    - Permission checking
    - Role assignment and validation
    - Access control decisions
    - Audit logging for access decisions

    Per Truth Protocol Rule #6: RBAC roles (5-tier)
    """

    def __init__(self):
        """Initialize RBAC Manager."""
        self._role_cache: dict[str, Role] = {}
        self._permission_cache: dict[tuple[Role, str], bool] = {}

    def check_permission(
        self, user_role: Role | str, required_permission: str | Permission
    ) -> bool:
        """
        Check if a user role has a specific permission.

        Args:
            user_role: The user's role
            required_permission: The required permission

        Returns:
            True if permitted, False otherwise
        """
        return check_permission(user_role, required_permission)

    def get_role_permissions(self, role: Role) -> set[str]:
        """
        Get all permissions for a role including inherited permissions.

        Args:
            role: The role to get permissions for

        Returns:
            Set of all permissions for the role
        """
        all_permissions: set[str] = set()
        accessible_roles = ROLE_HIERARCHY.get(role, {role})

        for r in accessible_roles:
            all_permissions.update(ROLE_PERMISSIONS.get(r, set()))

        return all_permissions

    def validate_role(self, role_value: str) -> Role | None:
        """
        Validate and convert a role string to Role enum.

        Args:
            role_value: String representation of role

        Returns:
            Role enum if valid, None otherwise
        """
        # Check cache first
        if role_value in self._role_cache:
            return self._role_cache[role_value]

        # Try direct value match
        for role in Role:
            if role.value == role_value or role.name == role_value:
                self._role_cache[role_value] = role
                return role

        return None

    def is_authorized(
        self,
        user_role: Role | str,
        required_permissions: list[str | Permission],
        require_all: bool = True,
    ) -> bool:
        """
        Check if user is authorized based on multiple permissions.

        Args:
            user_role: The user's role
            required_permissions: List of required permissions
            require_all: If True, all permissions required; if False, any one

        Returns:
            True if authorized, False otherwise
        """
        if not required_permissions:
            return True

        results = [
            self.check_permission(user_role, perm) for perm in required_permissions
        ]

        if require_all:
            return all(results)
        return any(results)

    def get_effective_role(self, user_roles: list[Role]) -> Role:
        """
        Get the highest effective role from a list of roles.

        Args:
            user_roles: List of user's roles

        Returns:
            The highest role in hierarchy
        """
        if not user_roles:
            return DEFAULT_ROLE

        # Role priority order (highest first)
        role_priority = [
            Role.SUPER_ADMIN,
            Role.ADMIN,
            Role.DEVELOPER,
            Role.API_USER,
            Role.READ_ONLY,
        ]

        for role in role_priority:
            if role in user_roles:
                return role

        return DEFAULT_ROLE

    def can_access_resource(
        self,
        user_role: Role | str,
        resource_type: str,
        action: str = "view",
    ) -> bool:
        """
        Check if user can access a specific resource type with given action.

        Args:
            user_role: The user's role
            resource_type: Type of resource (e.g., "agents", "users", "wordpress")
            action: Action to perform (e.g., "view", "manage", "deploy")

        Returns:
            True if access allowed, False otherwise
        """
        # Build permission string
        permission_str = f"{action}:{resource_type}"
        return self.check_permission(user_role, permission_str)
