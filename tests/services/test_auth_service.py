"""
Authentication Service Tests
Test authentication, user creation, and password management

Author: DevSkyy Enterprise Team
Date: 2025-11-10
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from services.auth_service import AuthService


class TestAuthService:
    """Test cases for AuthService"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "TestPassword123!"
        hashed = AuthService.hash_password(password)

        assert hashed is not None
        assert len(hashed) > 0
        assert hashed != password  # Ensure it's actually hashed
        assert hashed.startswith("$argon2")  # Argon2 hash format

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "TestPassword123!"
        hashed = AuthService.hash_password(password)

        result = AuthService.verify_password(password, hashed)
        assert result is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = AuthService.hash_password(password)

        result = AuthService.verify_password(wrong_password, hashed)
        assert result is False

    def test_verify_password_invalid_hash(self):
        """Test password verification with invalid hash"""
        password = "TestPassword123!"
        invalid_hash = "not_a_valid_hash"

        result = AuthService.verify_password(password, invalid_hash)
        assert result is False

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self):
        """Test successful user authentication"""
        # Create mock session
        mock_session = AsyncMock()

        # Create mock user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.full_name = "Test User"
        mock_user.is_active = True
        mock_user.is_superuser = False
        mock_user.created_at = datetime.utcnow()
        mock_user.hashed_password = AuthService.hash_password("TestPassword123!")

        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        # Test authentication
        user = await AuthService.authenticate_user(mock_session, "testuser", "TestPassword123!")

        assert user is not None
        assert user["id"] == 1
        assert user["username"] == "testuser"
        assert user["email"] == "test@example.com"
        assert "SuperAdmin" not in user["roles"]
        assert "User" in user["roles"]

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self):
        """Test authentication with non-existent user"""
        mock_session = AsyncMock()

        # Mock database query returning None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Test authentication
        user = await AuthService.authenticate_user(mock_session, "nonexistent", "password")

        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self):
        """Test authentication with inactive user"""
        mock_session = AsyncMock()

        # Create mock inactive user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "inactiveuser"
        mock_user.is_active = False
        mock_user.hashed_password = AuthService.hash_password("password")

        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        # Test authentication
        user = await AuthService.authenticate_user(mock_session, "inactiveuser", "password")

        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self):
        """Test authentication with wrong password"""
        mock_session = AsyncMock()

        # Create mock user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.is_active = True
        mock_user.hashed_password = AuthService.hash_password("CorrectPassword")

        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        # Test authentication with wrong password
        user = await AuthService.authenticate_user(mock_session, "testuser", "WrongPassword")

        assert user is None

    @pytest.mark.asyncio
    async def test_create_user_success(self):
        """Test successful user creation"""
        mock_session = AsyncMock()

        # Mock no existing user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Mock user creation
        with patch('services.auth_service.User') as mock_user_class:
            mock_new_user = MagicMock()
            mock_new_user.id = 1
            mock_new_user.username = "newuser"
            mock_new_user.email = "new@example.com"
            mock_new_user.full_name = "New User"
            mock_new_user.is_active = True
            mock_new_user.is_superuser = False
            mock_new_user.created_at = datetime.utcnow()
            mock_user_class.return_value = mock_new_user

            # Test user creation
            user = await AuthService.create_user(
                session=mock_session,
                username="newuser",
                email="new@example.com",
                password="Password123!",
                full_name="New User"
            )

            assert mock_session.add.called
            assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self):
        """Test user creation with duplicate username"""
        mock_session = AsyncMock()

        # Mock existing user
        mock_existing_user = MagicMock()
        mock_existing_user.username = "existinguser"
        mock_existing_user.email = "other@example.com"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_existing_user
        mock_session.execute.return_value = mock_result

        # Test user creation
        user = await AuthService.create_user(
            session=mock_session,
            username="existinguser",
            email="new@example.com",
            password="Password123!"
        )

        assert user is None
        assert not mock_session.add.called

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self):
        """Test getting user by ID"""
        mock_session = AsyncMock()

        # Mock user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.is_superuser = False
        mock_user.created_at = datetime.utcnow()
        mock_user.updated_at = datetime.utcnow()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        # Test getting user
        user = await AuthService.get_user_by_id(mock_session, 1)

        assert user is not None
        assert user["id"] == 1
        assert user["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self):
        """Test getting non-existent user by ID"""
        mock_session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Test getting user
        user = await AuthService.get_user_by_id(mock_session, 999)

        assert user is None

    @pytest.mark.asyncio
    async def test_update_user_password_success(self):
        """Test password update"""
        mock_session = AsyncMock()

        # Mock user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.hashed_password = "old_hash"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        # Test password update
        result = await AuthService.update_user_password(mock_session, 1, "NewPassword123!")

        assert result is True
        assert mock_session.commit.called
        assert mock_user.hashed_password != "old_hash"

    @pytest.mark.asyncio
    async def test_deactivate_user_success(self):
        """Test user deactivation"""
        mock_session = AsyncMock()

        # Mock user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.is_active = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        # Test user deactivation
        result = await AuthService.deactivate_user(mock_session, 1)

        assert result is True
        assert mock_user.is_active is False
        assert mock_session.commit.called


# Integration tests (require database)
@pytest.mark.integration
class TestAuthServiceIntegration:
    """Integration tests for AuthService (requires database)"""

    @pytest.mark.asyncio
    async def test_full_user_lifecycle(self, test_db_session):
        """Test complete user lifecycle: create, authenticate, update, deactivate"""
        # This would require a test database session
        # Implementation depends on test database setup
        pytest.skip("Integration test requires database setup")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
