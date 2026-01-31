"""
Role Hierarchy
==============

Role privilege hierarchy for RBAC authorization.
Defines permission levels and provides utility functions for role comparison.

MUST NOT depend on api/, security/, agents/, or services/ modules.
"""

from __future__ import annotations

from .types import UserRole

# Role hierarchy mapping - higher value = more privileges
ROLE_HIERARCHY: dict[UserRole, int] = {
    UserRole.SUPER_ADMIN: 100,  # Full system access
    UserRole.ADMIN: 80,  # Administrative access
    UserRole.DEVELOPER: 60,  # API and development access
    UserRole.API_USER: 40,  # Standard API access
    UserRole.READ_ONLY: 20,  # Read-only access
    UserRole.GUEST: 0,  # Minimal access
}


def get_role_level(role: UserRole) -> int:
    """
    Get the privilege level for a role.

    Args:
        role: UserRole to get level for

    Returns:
        Integer privilege level (0-100)

    Example:
        >>> get_role_level(UserRole.ADMIN)
        80
    """
    return ROLE_HIERARCHY.get(role, 0)


def is_role_at_least(user_role: UserRole, required_role: UserRole) -> bool:
    """
    Check if user role meets or exceeds required role level.

    Args:
        user_role: User's current role
        required_role: Minimum required role

    Returns:
        True if user_role >= required_role in hierarchy

    Example:
        >>> is_role_at_least(UserRole.ADMIN, UserRole.API_USER)
        True
        >>> is_role_at_least(UserRole.GUEST, UserRole.API_USER)
        False
    """
    user_level = get_role_level(user_role)
    required_level = get_role_level(required_role)
    return user_level >= required_level


def has_required_role(user_roles: list[str], required_roles: set[UserRole]) -> bool:
    """
    Check if user has any of the required roles.

    Args:
        user_roles: List of role strings from token
        required_roles: Set of required UserRole values

    Returns:
        True if user has at least one required role

    Example:
        >>> has_required_role(["admin", "api_user"], {UserRole.ADMIN})
        True
    """
    user_role_set = set(user_roles)
    required_role_values = {r.value for r in required_roles}
    return bool(user_role_set & required_role_values)


def get_minimum_required_level(required_roles: set[UserRole]) -> int:
    """
    Get the minimum privilege level needed from a set of roles.

    Args:
        required_roles: Set of acceptable roles

    Returns:
        Minimum privilege level that satisfies requirements

    Example:
        >>> get_minimum_required_level({UserRole.ADMIN, UserRole.DEVELOPER})
        60  # Developer level is the minimum
    """
    if not required_roles:
        return 0
    return min(get_role_level(role) for role in required_roles)


def get_roles_at_or_above(minimum_role: UserRole) -> list[UserRole]:
    """
    Get all roles at or above the specified level.

    Args:
        minimum_role: Minimum role level

    Returns:
        List of roles meeting or exceeding the level

    Example:
        >>> get_roles_at_or_above(UserRole.DEVELOPER)
        [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.DEVELOPER]
    """
    min_level = get_role_level(minimum_role)
    return [role for role, level in ROLE_HIERARCHY.items() if level >= min_level]


def get_highest_role_from_list(roles: list[str]) -> UserRole | None:
    """
    Get the highest privilege role from a list of role strings.

    Args:
        roles: List of role value strings

    Returns:
        Highest UserRole or None if no valid roles

    Example:
        >>> get_highest_role_from_list(["api_user", "admin"])
        UserRole.ADMIN
    """
    max_level = -1
    highest: UserRole | None = None

    for role_str in roles:
        try:
            role = UserRole(role_str)
            level = get_role_level(role)
            if level > max_level:
                max_level = level
                highest = role
        except ValueError:
            # Skip invalid role strings
            continue

    return highest
