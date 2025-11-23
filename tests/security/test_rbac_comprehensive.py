"""
Comprehensive tests for RBAC (Role-Based Access Control) module.

Tests all 5 roles per Truth Protocol Rule #6:
- SuperAdmin: Full platform access
- Admin: Agent deployment, configuration, user management
- Developer: Code deployment, testing, monitoring
- APIUser: API access for external integrations
- ReadOnly: View-only access to dashboards and logs

Per Truth Protocol Rule #8: Test coverage ≥90%
"""

import pytest

from security.rbac import (
    DEFAULT_ROLE,
    DEPLOYMENT_ROLES,
    FINETUNING_ROLES,
    ROLE_HIERARCHY,
    ROLE_PERMISSIONS,
    WORDPRESS_ROLES,
    Role,
    has_permission,
    is_role_higher_or_equal,
)


class TestRoleEnum:
    """Test the Role enum definition."""

    def test_all_roles_exist(self) -> None:
        """Verify all 5 RBAC roles are defined."""
        assert Role.SUPER_ADMIN == "SuperAdmin"
        assert Role.ADMIN == "Admin"
        assert Role.DEVELOPER == "Developer"
        assert Role.API_USER == "APIUser"
        assert Role.READ_ONLY == "ReadOnly"

    def test_role_count(self) -> None:
        """Verify exactly 5 roles exist (per Truth Protocol Rule #6)."""
        assert len(Role) == 5

    def test_roles_are_strings(self) -> None:
        """Verify all roles are string enums."""
        for role in Role:
            assert isinstance(role.value, str)


class TestRoleHierarchy:
    """Test role hierarchy and inheritance."""

    def test_super_admin_has_all_roles(self) -> None:
        """SuperAdmin should have access to all role permissions."""
        accessible = ROLE_HIERARCHY[Role.SUPER_ADMIN]
        assert Role.SUPER_ADMIN in accessible
        assert Role.ADMIN in accessible
        assert Role.DEVELOPER in accessible
        assert Role.API_USER in accessible
        assert Role.READ_ONLY in accessible
        assert len(accessible) == 5

    def test_admin_hierarchy(self) -> None:
        """Admin should have access to Admin, Developer, APIUser, ReadOnly."""
        accessible = ROLE_HIERARCHY[Role.ADMIN]
        assert Role.SUPER_ADMIN not in accessible
        assert Role.ADMIN in accessible
        assert Role.DEVELOPER in accessible
        assert Role.API_USER in accessible
        assert Role.READ_ONLY in accessible
        assert len(accessible) == 4

    def test_developer_hierarchy(self) -> None:
        """Developer should have access to Developer, APIUser, ReadOnly."""
        accessible = ROLE_HIERARCHY[Role.DEVELOPER]
        assert Role.SUPER_ADMIN not in accessible
        assert Role.ADMIN not in accessible
        assert Role.DEVELOPER in accessible
        assert Role.API_USER in accessible
        assert Role.READ_ONLY in accessible
        assert len(accessible) == 3

    def test_api_user_hierarchy(self) -> None:
        """APIUser should have access to APIUser and ReadOnly."""
        accessible = ROLE_HIERARCHY[Role.API_USER]
        assert Role.SUPER_ADMIN not in accessible
        assert Role.ADMIN not in accessible
        assert Role.DEVELOPER not in accessible
        assert Role.API_USER in accessible
        assert Role.READ_ONLY in accessible
        assert len(accessible) == 2

    def test_read_only_hierarchy(self) -> None:
        """ReadOnly should only have access to ReadOnly."""
        accessible = ROLE_HIERARCHY[Role.READ_ONLY]
        assert Role.SUPER_ADMIN not in accessible
        assert Role.ADMIN not in accessible
        assert Role.DEVELOPER not in accessible
        assert Role.API_USER not in accessible
        assert Role.READ_ONLY in accessible
        assert len(accessible) == 1


class TestRolePermissions:
    """Test permissions for each role."""

    def test_super_admin_permissions(self) -> None:
        """SuperAdmin should have all critical permissions."""
        perms = ROLE_PERMISSIONS[Role.SUPER_ADMIN]
        assert "manage:users" in perms
        assert "manage:agents" in perms
        assert "manage:settings" in perms
        assert "deploy:agents" in perms
        assert "finetune:agents" in perms
        assert "manage:wordpress" in perms
        assert "manage:security" in perms
        assert "view:all" in perms
        assert "delete:all" in perms

    def test_admin_permissions(self) -> None:
        """Admin should have agent management and deployment permissions."""
        perms = ROLE_PERMISSIONS[Role.ADMIN]
        assert "manage:agents" in perms
        assert "deploy:agents" in perms
        assert "finetune:agents" in perms
        assert "manage:wordpress" in perms
        assert "view:all" in perms
        assert "manage:users" in perms
        # Should NOT have security or delete all
        assert "manage:security" not in perms
        assert "delete:all" not in perms

    def test_developer_permissions(self) -> None:
        """Developer should have code deployment and testing permissions."""
        perms = ROLE_PERMISSIONS[Role.DEVELOPER]
        assert "deploy:code" in perms
        assert "test:agents" in perms
        assert "view:logs" in perms
        assert "view:metrics" in perms
        assert "deploy:agents" in perms
        # Should NOT have management permissions
        assert "manage:users" not in perms
        assert "manage:agents" not in perms
        assert "finetune:agents" not in perms

    def test_api_user_permissions(self) -> None:
        """APIUser should have API access permissions only."""
        perms = ROLE_PERMISSIONS[Role.API_USER]
        assert "api:read" in perms
        assert "api:write" in perms
        assert "view:metrics" in perms
        # Should NOT have deployment or management
        assert "deploy:agents" not in perms
        assert "manage:users" not in perms

    def test_read_only_permissions(self) -> None:
        """ReadOnly should have view-only permissions."""
        perms = ROLE_PERMISSIONS[Role.READ_ONLY]
        assert "view:dashboard" in perms
        assert "view:logs" in perms
        # Should NOT have any write permissions
        assert "deploy:agents" not in perms
        assert "manage:users" not in perms
        assert "api:write" not in perms


class TestHasPermission:
    """Test the has_permission() function."""

    # SuperAdmin tests
    def test_super_admin_has_all_permissions(self) -> None:
        """SuperAdmin should have all permissions including lower roles."""
        assert has_permission(Role.SUPER_ADMIN, "manage:users") is True
        assert has_permission(Role.SUPER_ADMIN, "deploy:agents") is True
        assert has_permission(Role.SUPER_ADMIN, "manage:security") is True
        assert has_permission(Role.SUPER_ADMIN, "delete:all") is True
        # Inherited from lower roles
        assert has_permission(Role.SUPER_ADMIN, "deploy:code") is True  # Developer
        assert has_permission(Role.SUPER_ADMIN, "api:read") is True  # APIUser
        assert has_permission(Role.SUPER_ADMIN, "view:dashboard") is True  # ReadOnly

    # Admin tests
    def test_admin_has_management_permissions(self) -> None:
        """Admin should have agent and user management permissions."""
        assert has_permission(Role.ADMIN, "manage:agents") is True
        assert has_permission(Role.ADMIN, "deploy:agents") is True
        assert has_permission(Role.ADMIN, "finetune:agents") is True
        assert has_permission(Role.ADMIN, "manage:wordpress") is True
        assert has_permission(Role.ADMIN, "manage:users") is True

    def test_admin_inherits_lower_permissions(self) -> None:
        """Admin should inherit Developer, APIUser, ReadOnly permissions."""
        assert has_permission(Role.ADMIN, "deploy:code") is True  # Developer
        assert has_permission(Role.ADMIN, "view:logs") is True  # Developer/ReadOnly
        assert has_permission(Role.ADMIN, "api:read") is True  # APIUser
        assert has_permission(Role.ADMIN, "view:dashboard") is True  # ReadOnly

    def test_admin_denied_super_admin_permissions(self) -> None:
        """Admin should NOT have SuperAdmin-only permissions."""
        assert has_permission(Role.ADMIN, "manage:security") is False
        assert has_permission(Role.ADMIN, "delete:all") is False

    # Developer tests
    def test_developer_has_code_permissions(self) -> None:
        """Developer should have code deployment and testing permissions."""
        assert has_permission(Role.DEVELOPER, "deploy:code") is True
        assert has_permission(Role.DEVELOPER, "test:agents") is True
        assert has_permission(Role.DEVELOPER, "view:logs") is True
        assert has_permission(Role.DEVELOPER, "deploy:agents") is True

    def test_developer_inherits_api_and_readonly(self) -> None:
        """Developer should inherit APIUser and ReadOnly permissions."""
        assert has_permission(Role.DEVELOPER, "api:read") is True
        assert has_permission(Role.DEVELOPER, "view:metrics") is True
        assert has_permission(Role.DEVELOPER, "view:dashboard") is True

    def test_developer_denied_management_permissions(self) -> None:
        """Developer should NOT have management permissions."""
        assert has_permission(Role.DEVELOPER, "manage:users") is False
        assert has_permission(Role.DEVELOPER, "manage:agents") is False
        assert has_permission(Role.DEVELOPER, "finetune:agents") is False
        assert has_permission(Role.DEVELOPER, "manage:security") is False

    # APIUser tests
    def test_api_user_has_api_permissions(self) -> None:
        """APIUser should have API access permissions."""
        assert has_permission(Role.API_USER, "api:read") is True
        assert has_permission(Role.API_USER, "api:write") is True
        assert has_permission(Role.API_USER, "view:metrics") is True

    def test_api_user_inherits_readonly(self) -> None:
        """APIUser should inherit ReadOnly permissions."""
        assert has_permission(Role.API_USER, "view:dashboard") is True
        assert has_permission(Role.API_USER, "view:logs") is True

    def test_api_user_denied_deployment(self) -> None:
        """APIUser should NOT have deployment or management permissions."""
        assert has_permission(Role.API_USER, "deploy:agents") is False
        assert has_permission(Role.API_USER, "manage:users") is False
        assert has_permission(Role.API_USER, "deploy:code") is False

    # ReadOnly tests
    def test_read_only_has_view_permissions(self) -> None:
        """ReadOnly should have view-only permissions."""
        assert has_permission(Role.READ_ONLY, "view:dashboard") is True
        assert has_permission(Role.READ_ONLY, "view:logs") is True

    def test_read_only_denied_all_write_permissions(self) -> None:
        """ReadOnly should be denied all write/management permissions."""
        assert has_permission(Role.READ_ONLY, "deploy:agents") is False
        assert has_permission(Role.READ_ONLY, "manage:users") is False
        assert has_permission(Role.READ_ONLY, "api:write") is False
        assert has_permission(Role.READ_ONLY, "deploy:code") is False
        assert has_permission(Role.READ_ONLY, "finetune:agents") is False

    # Edge cases
    def test_nonexistent_permission_denied(self) -> None:
        """Non-existent permissions should be denied for all roles."""
        assert has_permission(Role.SUPER_ADMIN, "invalid:permission") is False
        assert has_permission(Role.ADMIN, "invalid:permission") is False
        assert has_permission(Role.DEVELOPER, "invalid:permission") is False
        assert has_permission(Role.API_USER, "invalid:permission") is False
        assert has_permission(Role.READ_ONLY, "invalid:permission") is False


class TestIsRoleHigherOrEqual:
    """Test the is_role_higher_or_equal() function."""

    def test_super_admin_higher_than_all(self) -> None:
        """SuperAdmin should be higher or equal to all roles."""
        assert is_role_higher_or_equal(Role.SUPER_ADMIN, Role.SUPER_ADMIN) is True
        assert is_role_higher_or_equal(Role.SUPER_ADMIN, Role.ADMIN) is True
        assert is_role_higher_or_equal(Role.SUPER_ADMIN, Role.DEVELOPER) is True
        assert is_role_higher_or_equal(Role.SUPER_ADMIN, Role.API_USER) is True
        assert is_role_higher_or_equal(Role.SUPER_ADMIN, Role.READ_ONLY) is True

    def test_admin_hierarchy_checks(self) -> None:
        """Admin should be higher than Developer, APIUser, ReadOnly but not SuperAdmin."""
        assert is_role_higher_or_equal(Role.ADMIN, Role.SUPER_ADMIN) is False
        assert is_role_higher_or_equal(Role.ADMIN, Role.ADMIN) is True
        assert is_role_higher_or_equal(Role.ADMIN, Role.DEVELOPER) is True
        assert is_role_higher_or_equal(Role.ADMIN, Role.API_USER) is True
        assert is_role_higher_or_equal(Role.ADMIN, Role.READ_ONLY) is True

    def test_developer_hierarchy_checks(self) -> None:
        """Developer should be higher than APIUser, ReadOnly but not Admin/SuperAdmin."""
        assert is_role_higher_or_equal(Role.DEVELOPER, Role.SUPER_ADMIN) is False
        assert is_role_higher_or_equal(Role.DEVELOPER, Role.ADMIN) is False
        assert is_role_higher_or_equal(Role.DEVELOPER, Role.DEVELOPER) is True
        assert is_role_higher_or_equal(Role.DEVELOPER, Role.API_USER) is True
        assert is_role_higher_or_equal(Role.DEVELOPER, Role.READ_ONLY) is True

    def test_api_user_hierarchy_checks(self) -> None:
        """APIUser should be higher than ReadOnly but not Developer/Admin/SuperAdmin."""
        assert is_role_higher_or_equal(Role.API_USER, Role.SUPER_ADMIN) is False
        assert is_role_higher_or_equal(Role.API_USER, Role.ADMIN) is False
        assert is_role_higher_or_equal(Role.API_USER, Role.DEVELOPER) is False
        assert is_role_higher_or_equal(Role.API_USER, Role.API_USER) is True
        assert is_role_higher_or_equal(Role.API_USER, Role.READ_ONLY) is True

    def test_read_only_hierarchy_checks(self) -> None:
        """ReadOnly should only be equal to itself, not higher than any role."""
        assert is_role_higher_or_equal(Role.READ_ONLY, Role.SUPER_ADMIN) is False
        assert is_role_higher_or_equal(Role.READ_ONLY, Role.ADMIN) is False
        assert is_role_higher_or_equal(Role.READ_ONLY, Role.DEVELOPER) is False
        assert is_role_higher_or_equal(Role.READ_ONLY, Role.API_USER) is False
        assert is_role_higher_or_equal(Role.READ_ONLY, Role.READ_ONLY) is True

    def test_role_equality_reflexive(self) -> None:
        """All roles should be equal to themselves."""
        for role in Role:
            assert is_role_higher_or_equal(role, role) is True


class TestConstants:
    """Test RBAC constants."""

    def test_default_role(self) -> None:
        """Default role should be ReadOnly (least privilege)."""
        assert DEFAULT_ROLE == Role.READ_ONLY

    def test_deployment_roles(self) -> None:
        """Only SuperAdmin, Admin, Developer should deploy agents."""
        assert Role.SUPER_ADMIN in DEPLOYMENT_ROLES
        assert Role.ADMIN in DEPLOYMENT_ROLES
        assert Role.DEVELOPER in DEPLOYMENT_ROLES
        assert Role.API_USER not in DEPLOYMENT_ROLES
        assert Role.READ_ONLY not in DEPLOYMENT_ROLES
        assert len(DEPLOYMENT_ROLES) == 3

    def test_finetuning_roles(self) -> None:
        """Only SuperAdmin and Admin should finetune agents."""
        assert Role.SUPER_ADMIN in FINETUNING_ROLES
        assert Role.ADMIN in FINETUNING_ROLES
        assert Role.DEVELOPER not in FINETUNING_ROLES
        assert Role.API_USER not in FINETUNING_ROLES
        assert Role.READ_ONLY not in FINETUNING_ROLES
        assert len(FINETUNING_ROLES) == 2

    def test_wordpress_roles(self) -> None:
        """Only SuperAdmin and Admin should manage WordPress."""
        assert Role.SUPER_ADMIN in WORDPRESS_ROLES
        assert Role.ADMIN in WORDPRESS_ROLES
        assert Role.DEVELOPER not in WORDPRESS_ROLES
        assert Role.API_USER not in WORDPRESS_ROLES
        assert Role.READ_ONLY not in WORDPRESS_ROLES
        assert len(WORDPRESS_ROLES) == 2


class TestRoleAccessControl:
    """Integration tests for role-based access control enforcement."""

    @pytest.mark.parametrize(
        "role,permission,expected",
        [
            # SuperAdmin - should have everything
            (Role.SUPER_ADMIN, "manage:security", True),
            (Role.SUPER_ADMIN, "delete:all", True),
            # Admin - should have most things except security
            (Role.ADMIN, "manage:users", True),
            (Role.ADMIN, "manage:security", False),
            # Developer - should deploy but not manage
            (Role.DEVELOPER, "deploy:code", True),
            (Role.DEVELOPER, "manage:users", False),
            # APIUser - API only
            (Role.API_USER, "api:write", True),
            (Role.API_USER, "deploy:code", False),
            # ReadOnly - view only
            (Role.READ_ONLY, "view:logs", True),
            (Role.READ_ONLY, "api:write", False),
        ],
    )
    def test_permission_matrix(self, role: Role, permission: str, expected: bool) -> None:
        """Test permission matrix across all roles."""
        assert has_permission(role, permission) is expected

    def test_role_separation_of_duties(self) -> None:
        """Verify separation of duties between roles."""
        # Only SuperAdmin can manage security
        security_perm = "manage:security"
        assert has_permission(Role.SUPER_ADMIN, security_perm) is True
        assert has_permission(Role.ADMIN, security_perm) is False
        assert has_permission(Role.DEVELOPER, security_perm) is False

        # Only SuperAdmin can delete all
        delete_perm = "delete:all"
        assert has_permission(Role.SUPER_ADMIN, delete_perm) is True
        assert has_permission(Role.ADMIN, delete_perm) is False

        # Only Admin and SuperAdmin can finetune
        finetune_perm = "finetune:agents"
        assert has_permission(Role.SUPER_ADMIN, finetune_perm) is True
        assert has_permission(Role.ADMIN, finetune_perm) is True
        assert has_permission(Role.DEVELOPER, finetune_perm) is False

    def test_least_privilege_principle(self) -> None:
        """Verify least privilege principle - ReadOnly has minimal permissions."""
        read_only_perms = ROLE_PERMISSIONS[Role.READ_ONLY]
        # Should only have view permissions
        assert all(perm.startswith("view:") for perm in read_only_perms)
        # Should be the smallest permission set
        for role in [Role.SUPER_ADMIN, Role.ADMIN, Role.DEVELOPER, Role.API_USER]:
            assert len(read_only_perms) < len(ROLE_PERMISSIONS[role])
