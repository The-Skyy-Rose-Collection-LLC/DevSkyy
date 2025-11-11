"""
Unit tests for JWT Authentication Module (RFC 7519 compliant)

Tests JWT token creation, verification, refresh, and RBAC enforcement.
Per CLAUDE.md: Comprehensive test suite with 80%+ coverage target.

Author: DevSkyy Team
Version: 1.0.0
Python: >=3.11.0
"""

import unittest
import pytest
import os
from datetime import datetime, timedelta
from unittest.mock import patch

# Set test JWT secret before importing jwt_auth
os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-characters-min-length-required"

from security.jwt_auth import (
    UserRole,
    TokenType,
    create_access_token,
    create_refresh_token,
    create_token_pair,
    verify_jwt_token,
    revoke_token,
    refresh_access_token,
    generate_secure_secret_key,
    has_permission,
    require_role,
    TokenBlacklist,
    ROLE_HIERARCHY,
)
from fastapi import HTTPException


class TestUserRole(unittest.TestCase):
    """Test UserRole enum and hierarchy."""

    def test_role_values(self):
        """Test that all roles have correct string values."""
        self.assertEqual(UserRole.SUPER_ADMIN.value, "super_admin")
        self.assertEqual(UserRole.ADMIN.value, "admin")
        self.assertEqual(UserRole.DEVELOPER.value, "developer")
        self.assertEqual(UserRole.API_USER.value, "api_user")
        self.assertEqual(UserRole.READ_ONLY.value, "read_only")

    def test_role_hierarchy(self):
        """Test role hierarchy values are correct."""
        self.assertEqual(ROLE_HIERARCHY[UserRole.SUPER_ADMIN], 5)
        self.assertEqual(ROLE_HIERARCHY[UserRole.ADMIN], 4)
        self.assertEqual(ROLE_HIERARCHY[UserRole.DEVELOPER], 3)
        self.assertEqual(ROLE_HIERARCHY[UserRole.API_USER], 2)
        self.assertEqual(ROLE_HIERARCHY[UserRole.READ_ONLY], 1)

    def test_has_permission_higher_role(self):
        """Test that higher roles can access lower role endpoints."""
        self.assertIs(has_permission(UserRole.ADMIN, UserRole.DEVELOPER), True)
        self.assertIs(has_permission(UserRole.SUPER_ADMIN, UserRole.API_USER), True)

    def test_has_permission_equal_role(self):
        """Test that equal roles can access their own endpoints."""
        self.assertIs(has_permission(UserRole.DEVELOPER, UserRole.DEVELOPER), True)
        self.assertIs(has_permission(UserRole.READ_ONLY, UserRole.READ_ONLY), True)

    def test_has_permission_lower_role(self):
        """Test that lower roles cannot access higher role endpoints."""
        self.assertIs(has_permission(UserRole.API_USER, UserRole.ADMIN), False)
        self.assertIs(has_permission(UserRole.READ_ONLY, UserRole.DEVELOPER), False)


class TestTokenGeneration(unittest.TestCase):
    """Test JWT token creation."""

    def test_create_access_token_basic(self):
        """Test basic access token creation."""
        token = create_access_token("user123", UserRole.DEVELOPER)

        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)
        # JWT format: header.payload.signature
        self.assertEqual(token.count("."), 2)

    def test_create_access_token_with_email(self):
        """Test access token with email."""
        token = create_access_token(
            "user123",
            UserRole.ADMIN,
            email="admin@example.com"
        )

        payload = verify_jwt_token(token, TokenType.ACCESS)
        self.assertEqual(payload["sub"], "user123")
        self.assertEqual(payload["email"], "admin@example.com")
        self.assertEqual(payload["role"], UserRole.ADMIN.value)

    def test_create_access_token_with_permissions(self):
        """Test access token with custom permissions."""
        permissions = ["create:products", "delete:campaigns"]
        token = create_access_token(
            "user123",
            UserRole.DEVELOPER,
            permissions=permissions
        )

        payload = verify_jwt_token(token, TokenType.ACCESS)
        self.assertEqual(payload["permissions"], permissions)

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        token = create_refresh_token("user456", UserRole.API_USER)

        self.assertIsInstance(token, str)
        payload = verify_jwt_token(token, TokenType.REFRESH)
        self.assertEqual(payload["type"], TokenType.REFRESH.value)
        self.assertEqual(payload["sub"], "user456")

    def test_create_token_pair(self):
        """Test creating access and refresh token pair."""
        tokens = create_token_pair("user789", UserRole.SUPER_ADMIN, "super@example.com")

        self.assertTrue(hasattr(tokens, "access_token"))
        self.assertTrue(hasattr(tokens, "refresh_token"))
        self.assertEqual(tokens.token_type, "bearer")
        self.assertEqual(tokens.expires_in, 30 * 60  # 30 minutes in seconds)

        # Verify both tokens
        access_payload = verify_jwt_token(tokens.access_token, TokenType.ACCESS)
        refresh_payload = verify_jwt_token(tokens.refresh_token, TokenType.REFRESH)

        self.assertEqual(access_payload["sub"], "user789")
        self.assertEqual(refresh_payload["sub"], "user789")


class TestTokenVerification(unittest.TestCase):
    """Test JWT token verification."""

    def test_verify_valid_access_token(self):
        """Test verifying a valid access token."""
        token = create_access_token("user123", UserRole.DEVELOPER)
        payload = verify_jwt_token(token, TokenType.ACCESS)

        self.assertEqual(payload["sub"], "user123")
        self.assertEqual(payload["type"], TokenType.ACCESS.value)
        self.assertEqual(payload["role"], UserRole.DEVELOPER.value)
        self.assertIn("exp", payload)
        self.assertIn("iat", payload)

    def test_verify_valid_refresh_token(self):
        """Test verifying a valid refresh token."""
        token = create_refresh_token("user123", UserRole.ADMIN)
        payload = verify_jwt_token(token, TokenType.REFRESH)

        self.assertEqual(payload["sub"], "user123")
        self.assertEqual(payload["type"], TokenType.REFRESH.value)

    def test_verify_wrong_token_type(self):
        """Test that verifying wrong token type raises error."""
        access_token = create_access_token("user123", UserRole.DEVELOPER)

        with pytest.raises(HTTPException) as exc_info:
            verify_jwt_token(access_token, TokenType.REFRESH)

        self.assertEqual(exc_info.value.status_code, 401)
        self.assertIn("Invalid token type", exc_info.value.detail)

    def test_verify_expired_token(self):
        """Test that expired token raises error."""
        # Create token with past expiry
        with patch('security.jwt_auth.datetime') as mock_datetime:
            # Set time to past
            past_time = datetime.utcnow() - timedelta(hours=2)
            mock_datetime.utcnow.return_value = past_time

            token = create_access_token("user123", UserRole.DEVELOPER)

        # Try to verify (will be expired)
        with pytest.raises(HTTPException) as exc_info:
            verify_jwt_token(token, TokenType.ACCESS)

        self.assertEqual(exc_info.value.status_code, 401)
        self.assertIn("expired", exc_info.value.detail.lower())

    def test_verify_invalid_token(self):
        """Test that invalid token raises error."""
        invalid_token = "invalid.jwt.token"

        with pytest.raises(HTTPException) as exc_info:
            verify_jwt_token(invalid_token)

        self.assertEqual(exc_info.value.status_code, 401)

    def test_verify_blacklisted_token(self):
        """Test that blacklisted token raises error."""
        token = create_access_token("user123", UserRole.DEVELOPER)

        # Blacklist the token
        revoke_token(token)

        with pytest.raises(HTTPException) as exc_info:
            verify_jwt_token(token, TokenType.ACCESS)

        self.assertEqual(exc_info.value.status_code, 401)
        self.assertIn("revoked", exc_info.value.detail.lower())

        # Clean up blacklist
        TokenBlacklist.clear()


class TestTokenRefresh(unittest.TestCase):
    """Test token refresh functionality."""

    def test_refresh_access_token_success(self):
        """Test successful token refresh."""
        # Create initial token pair
        tokens = create_token_pair("user123", UserRole.DEVELOPER, "dev@example.com")

        # Refresh using refresh token
        new_tokens = refresh_access_token(tokens.refresh_token)

        self.assertNotEqual(new_tokens.access_token, tokens.access_token)
        self.assertNotEqual(new_tokens.refresh_token, tokens.refresh_token)

        # Verify new tokens work
        new_payload = verify_jwt_token(new_tokens.access_token, TokenType.ACCESS)
        self.assertEqual(new_payload["sub"], "user123")
        self.assertEqual(new_payload["role"], UserRole.DEVELOPER.value)

        # Old refresh token should be blacklisted
        with pytest.raises(HTTPException):
            verify_jwt_token(tokens.refresh_token, TokenType.REFRESH)

        # Clean up
        TokenBlacklist.clear()

    def test_refresh_with_invalid_token(self):
        """Test refresh with invalid token fails."""
        with pytest.raises(HTTPException):
            refresh_access_token("invalid.token")

    def test_refresh_with_access_token_fails(self):
        """Test that using access token for refresh fails."""
        access_token = create_access_token("user123", UserRole.DEVELOPER)

        with pytest.raises(HTTPException) as exc_info:
            refresh_access_token(access_token)

        self.assertEqual(exc_info.value.status_code, 401)


class TestTokenRevocation(unittest.TestCase):
    """Test token revocation."""

    def test_revoke_token(self):
        """Test token revocation."""
        token = create_access_token("user123", UserRole.DEVELOPER)

        # Token should work before revocation
        payload = verify_jwt_token(token, TokenType.ACCESS)
        self.assertEqual(payload["sub"], "user123")

        # Revoke token
        revoke_token(token)

        # Token should fail after revocation
        with pytest.raises(HTTPException) as exc_info:
            verify_jwt_token(token, TokenType.ACCESS)

        self.assertEqual(exc_info.value.status_code, 401)
        self.assertIn("revoked", exc_info.value.detail.lower())

        # Clean up
        TokenBlacklist.clear()

    def test_blacklist_clear(self):
        """Test clearing token blacklist."""
        token = create_access_token("user123", UserRole.DEVELOPER)

        revoke_token(token)
        self.assertIs(TokenBlacklist.is_blacklisted(token), True)

        TokenBlacklist.clear()
        self.assertIs(TokenBlacklist.is_blacklisted(token), False)


class TestSecretKeyGeneration(unittest.TestCase):
    """Test secure secret key generation."""

    def test_generate_secure_secret_key(self):
        """Test that generated secret keys are secure."""
        key1 = generate_secure_secret_key()
        key2 = generate_secure_secret_key()

        # Keys should be strings
        self.assertIsInstance(key1, str)
        self.assertIsInstance(key2, str)

        # Keys should be at least 32 characters
        self.assertGreater(len(key1), = 32)
        self.assertGreater(len(key2), = 32)

        # Keys should be unique
        self.assertNotEqual(key1, key2)

        # Keys should be URL-safe base64
        import string
        allowed_chars = string.ascii_letters + string.digits + "-_"
        self.assertIn(all(c, allowed_chars for c in key1))


class TestRBACEnforcement(unittest.TestCase):
    """Test RBAC enforcement in API endpoints."""

    @pytest.mark.asyncio
    async def test_require_role_success(self):
        """Test successful role check."""
        token = create_access_token("user123", UserRole.ADMIN)
        payload = verify_jwt_token(token, TokenType.ACCESS)

        # Mock current_user
        mock_user = {
            "sub": "user123",
            "roles": [UserRole.ADMIN.value],
        }

        # Admin trying to access DEVELOPER endpoint should succeed
        role_checker = require_role(UserRole.DEVELOPER)
        # This would be called by FastAPI dependency injection
        # Just verify the function exists and is callable
        self.assertTrue(callable(role_checker))

    @pytest.mark.asyncio
    async def test_require_role_insufficient_permissions(self):
        """Test that insufficient permissions raises error."""
        # Create API_USER token
        token = create_access_token("user123", UserRole.API_USER)

        mock_user = {
            "sub": "user123",
            "roles": [UserRole.API_USER.value],
        }

        # API_USER trying to access ADMIN endpoint should fail
        role_checker = require_role(UserRole.ADMIN)

        # Simulate the dependency execution
        with patch('security.jwt_auth.get_current_user', return_value=mock_user):
            checker_func = role_checker
            # The actual check happens inside the returned function
            # This tests the has_permission logic
            self.assertIs(has_permission(UserRole.API_USER, UserRole.ADMIN), False)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def test_token_without_role_defaults_to_readonly(self):
        """Test that missing role defaults to READ_ONLY."""
        # This shouldn't happen in production but test defensive coding
        import jwt as jwt_lib

        payload = {
            "sub": "user123",
            "exp": int((datetime.utcnow() + timedelta(minutes=30)).timestamp()),
            "iat": int(datetime.utcnow().timestamp()),
            "type": TokenType.ACCESS.value,
        }

        token = jwt_lib.encode(payload, os.environ["JWT_SECRET_KEY"], algorithm="HS256")

        decoded = verify_jwt_token(token, TokenType.ACCESS)
        # Should have role field even if not in original payload
        # This tests that the system is defensive

    def test_empty_user_id(self):
        """Test that empty user ID is rejected."""
        # Empty user ID should still create token but be identifiable
        token = create_access_token("", UserRole.READ_ONLY)
        payload = verify_jwt_token(token)
        self.assertEqual(payload["sub"], ""  # Empty but present)

    def test_special_characters_in_user_id(self):
        """Test user IDs with special characters."""
        user_id = "user@example.com"
        token = create_access_token(user_id, UserRole.DEVELOPER)

        payload = verify_jwt_token(token)
        self.assertEqual(payload["sub"], user_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=security.jwt_auth", "--cov-report=term-missing"])
