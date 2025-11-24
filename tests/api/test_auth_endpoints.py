"""
Comprehensive Tests for Authentication API Endpoints (api/v1/auth.py)
Tests JWT/OAuth2 authentication, user management, and security features
Coverage target: ≥90% for api/v1/auth.py

Author: DevSkyy Team
Version: 1.0.0
Python: >=3.11.0
Per CLAUDE.md Truth Protocol requirements
"""

from unittest.mock import Mock, patch

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import pytest

from api.validation_models import EnhancedRegisterRequest
from security.jwt_auth import TokenData, TokenResponse, User, UserRole


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_user_manager():
    """Mock user manager for testing"""
    with patch("api.v1.auth.user_manager") as mock:
        yield mock


@pytest.fixture
def sample_user():
    """Sample user for testing"""
    return User(
        id="user123",
        email="test@example.com",
        username="testuser",
        role=UserRole.API_USER,
        is_active=True,
        hashed_password="hashed_password_here",
    )


@pytest.fixture
def admin_user():
    """Sample admin user for testing"""
    return User(
        id="admin123",
        email="admin@example.com",
        username="admin",
        role=UserRole.ADMIN,
        is_active=True,
        hashed_password="hashed_password_here",
    )


@pytest.fixture
def sample_token_data():
    """Sample token data for testing"""
    return TokenData(
        user_id="user123",
        email="test@example.com",
        username="testuser",
        role=UserRole.API_USER,
    )


@pytest.fixture
def sample_tokens():
    """Sample token response for testing"""
    return TokenResponse(
        access_token="sample_access_token",
        refresh_token="sample_refresh_token",
        token_type="bearer",
        expires_in=1800,
    )


# ============================================================================
# TEST REGISTRATION ENDPOINT
# ============================================================================


class TestRegisterEndpoint:
    """Test /auth/register endpoint"""

    @pytest.mark.asyncio
    async def test_register_success(self, mock_user_manager, sample_user):
        """Should successfully register a new user"""
        from api.v1.auth import register

        # Mock user manager methods
        mock_user_manager.get_user_by_email.return_value = None
        mock_user_manager.create_user.return_value = sample_user

        # Create registration request
        request = EnhancedRegisterRequest(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            role=UserRole.API_USER,
        )

        # Call register endpoint
        result = await register(request)

        # Assertions
        assert result == sample_user
        mock_user_manager.get_user_by_email.assert_called_once_with("test@example.com")
        mock_user_manager.create_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_existing_email(self, mock_user_manager, sample_user):
        """Should reject registration with existing email"""
        from api.v1.auth import register

        # Mock existing user
        mock_user_manager.get_user_by_email.return_value = sample_user

        # Create registration request
        request = EnhancedRegisterRequest(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            role=UserRole.API_USER,
        )

        # Call register endpoint and expect exception
        with pytest.raises(HTTPException) as exc_info:
            await register(request)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_register_value_error(self, mock_user_manager):
        """Should handle ValueError from user creation"""
        from api.v1.auth import register

        # Mock user manager methods
        mock_user_manager.get_user_by_email.return_value = None
        mock_user_manager.create_user.side_effect = ValueError("Invalid input")

        # Create registration request
        request = EnhancedRegisterRequest(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            role=UserRole.API_USER,
        )

        # Call register endpoint and expect exception
        with pytest.raises(HTTPException) as exc_info:
            await register(request)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_register_generic_exception(self, mock_user_manager):
        """Should handle generic exceptions during registration"""
        from api.v1.auth import register

        # Mock user manager methods
        mock_user_manager.get_user_by_email.return_value = None
        mock_user_manager.create_user.side_effect = Exception("Database error")

        # Create registration request
        request = EnhancedRegisterRequest(
            email="test@example.com",
            username="testuser",
            password="TestPassword123!",
            role=UserRole.API_USER,
        )

        # Call register endpoint and expect exception
        with pytest.raises(HTTPException) as exc_info:
            await register(request)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Registration failed" in exc_info.value.detail


# ============================================================================
# TEST LOGIN ENDPOINT
# ============================================================================


class TestLoginEndpoint:
    """Test /auth/login endpoint"""

    @pytest.mark.asyncio
    async def test_login_success(self, mock_user_manager, sample_user):
        """Should successfully login with valid credentials"""
        from api.v1.auth import login

        # Mock user manager and token creation
        mock_user_manager.authenticate_user.return_value = sample_user

        with patch("api.v1.auth.create_user_tokens") as mock_create_tokens:
            mock_tokens = TokenResponse(
                access_token="access_token",
                refresh_token="refresh_token",
                token_type="bearer",
                expires_in=1800,
            )
            mock_create_tokens.return_value = mock_tokens

            # Create OAuth2 form data
            form_data = OAuth2PasswordRequestForm(
                username="test@example.com",
                password="TestPassword123!",
                scope="",
            )

            # Call login endpoint
            result = await login(form_data)

            # Assertions
            assert result == mock_tokens
            mock_user_manager.authenticate_user.assert_called_once_with(
                "test@example.com", "TestPassword123!"
            )

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, mock_user_manager):
        """Should reject login with invalid credentials"""
        from api.v1.auth import login

        # Mock authentication failure
        mock_user_manager.authenticate_user.return_value = None

        # Create OAuth2 form data
        form_data = OAuth2PasswordRequestForm(
            username="test@example.com",
            password="WrongPassword",
            scope="",
        )

        # Call login endpoint and expect exception
        with pytest.raises(HTTPException) as exc_info:
            await login(form_data)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username/email or password" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, mock_user_manager, sample_user):
        """Should reject login for inactive user"""
        from api.v1.auth import login

        # Set user as inactive
        sample_user.is_active = False
        mock_user_manager.authenticate_user.return_value = sample_user

        # Create OAuth2 form data
        form_data = OAuth2PasswordRequestForm(
            username="test@example.com",
            password="TestPassword123!",
            scope="",
        )

        # Call login endpoint and expect exception
        with pytest.raises(HTTPException) as exc_info:
            await login(form_data)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "disabled" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_login_generic_exception(self, mock_user_manager):
        """Should handle generic exceptions during login"""
        from api.v1.auth import login

        # Mock exception
        mock_user_manager.authenticate_user.side_effect = Exception("Database error")

        # Create OAuth2 form data
        form_data = OAuth2PasswordRequestForm(
            username="test@example.com",
            password="TestPassword123!",
            scope="",
        )

        # Call login endpoint and expect exception
        with pytest.raises(HTTPException) as exc_info:
            await login(form_data)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Login failed" in exc_info.value.detail


# ============================================================================
# TEST REFRESH TOKEN ENDPOINT
# ============================================================================


class TestRefreshTokenEndpoint:
    """Test /auth/refresh endpoint"""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, mock_user_manager, sample_user, sample_token_data):
        """Should successfully refresh access token"""
        from api.v1.auth import refresh_token

        # Mock verify_token and user manager
        with patch("api.v1.auth.verify_token") as mock_verify:
            mock_verify.return_value = sample_token_data
            mock_user_manager.get_user_by_id.return_value = sample_user

            with patch("api.v1.auth.create_user_tokens") as mock_create_tokens:
                mock_tokens = TokenResponse(
                    access_token="new_access_token",
                    refresh_token="new_refresh_token",
                    token_type="bearer",
                    expires_in=1800,
                )
                mock_create_tokens.return_value = mock_tokens

                # Call refresh endpoint
                result = await refresh_token("valid_refresh_token")

                # Assertions
                assert result == mock_tokens
                mock_verify.assert_called_once_with("valid_refresh_token", token_type="refresh")
                mock_user_manager.get_user_by_id.assert_called_once_with("user123")

    @pytest.mark.asyncio
    async def test_refresh_token_user_not_found(self, mock_user_manager, sample_token_data):
        """Should reject refresh when user not found"""
        from api.v1.auth import refresh_token

        # Mock verify_token and user not found
        with patch("api.v1.auth.verify_token") as mock_verify:
            mock_verify.return_value = sample_token_data
            mock_user_manager.get_user_by_id.return_value = None

            # Call refresh endpoint and expect exception
            with pytest.raises(HTTPException) as exc_info:
                await refresh_token("valid_refresh_token")

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "User not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_refresh_token_invalid_token(self, mock_user_manager):
        """Should reject invalid refresh token"""
        from api.v1.auth import refresh_token

        # Mock verify_token to raise exception
        with patch("api.v1.auth.verify_token") as mock_verify:
            mock_verify.side_effect = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

            # Call refresh endpoint and expect exception
            with pytest.raises(HTTPException) as exc_info:
                await refresh_token("invalid_token")

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_refresh_token_generic_exception(self, mock_user_manager):
        """Should handle generic exceptions during token refresh"""
        from api.v1.auth import refresh_token

        # Mock exception
        with patch("api.v1.auth.verify_token") as mock_verify:
            mock_verify.side_effect = Exception("Database error")

            # Call refresh endpoint and expect exception
            with pytest.raises(HTTPException) as exc_info:
                await refresh_token("valid_refresh_token")

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid refresh token" in exc_info.value.detail


# ============================================================================
# TEST GET CURRENT USER ENDPOINT
# ============================================================================


class TestGetCurrentUserEndpoint:
    """Test /auth/me endpoint"""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_user_manager, sample_user, sample_token_data):
        """Should successfully get current user info"""
        from api.v1.auth import get_current_user_info

        # Mock user manager
        mock_user_manager.get_user_by_id.return_value = sample_user

        # Call endpoint
        result = await get_current_user_info(sample_token_data)

        # Assertions
        assert result == sample_user
        mock_user_manager.get_user_by_id.assert_called_once_with("user123")

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self, mock_user_manager, sample_token_data):
        """Should handle user not found"""
        from api.v1.auth import get_current_user_info

        # Mock user not found
        mock_user_manager.get_user_by_id.return_value = None

        # Call endpoint and expect exception
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_info(sample_token_data)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in exc_info.value.detail


# ============================================================================
# TEST LOGOUT ENDPOINT
# ============================================================================


class TestLogoutEndpoint:
    """Test /auth/logout endpoint"""

    @pytest.mark.asyncio
    async def test_logout_success(self, sample_token_data):
        """Should successfully logout user"""
        from api.v1.auth import logout

        # Call logout endpoint
        result = await logout(sample_token_data)

        # Assertions
        assert "message" in result
        assert "Successfully logged out" in result["message"]
        assert result["user"] == sample_token_data.email


# ============================================================================
# TEST LIST USERS ENDPOINT
# ============================================================================


class TestListUsersEndpoint:
    """Test /auth/users endpoint"""

    @pytest.mark.asyncio
    async def test_list_users_as_admin(self, mock_user_manager, sample_user, admin_user):
        """Should successfully list users as admin"""
        from api.v1.auth import list_users

        # Create admin token data
        admin_token_data = TokenData(
            user_id="admin123",
            email="admin@example.com",
            username="admin",
            role=UserRole.ADMIN,
        )

        # Mock user manager users dict
        mock_user_manager.users = {
            "user123": sample_user,
            "admin123": admin_user,
        }

        # Call endpoint
        result = await list_users(admin_token_data)

        # Assertions
        assert "users" in result
        assert "count" in result
        assert result["count"] == 2
        assert len(result["users"]) == 2

    @pytest.mark.asyncio
    async def test_list_users_as_super_admin(self, mock_user_manager, sample_user):
        """Should successfully list users as super admin"""
        from api.v1.auth import list_users

        # Create super admin token data
        super_admin_token_data = TokenData(
            user_id="superadmin123",
            email="superadmin@example.com",
            username="superadmin",
            role=UserRole.SUPER_ADMIN,
        )

        # Mock user manager users dict
        mock_user_manager.users = {"user123": sample_user}

        # Call endpoint
        result = await list_users(super_admin_token_data)

        # Assertions
        assert "users" in result
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_list_users_forbidden_for_regular_user(self, sample_token_data):
        """Should forbid regular users from listing users"""
        from api.v1.auth import list_users

        # Call endpoint with regular user and expect exception
        with pytest.raises(HTTPException) as exc_info:
            await list_users(sample_token_data)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Admin access required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_list_users_forbidden_for_developer(self):
        """Should forbid developers from listing users"""
        from api.v1.auth import list_users

        # Create developer token data
        developer_token_data = TokenData(
            user_id="dev123",
            email="dev@example.com",
            username="developer",
            role=UserRole.DEVELOPER,
        )

        # Call endpoint and expect exception
        with pytest.raises(HTTPException) as exc_info:
            await list_users(developer_token_data)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# TEST LOG SANITIZATION
# ============================================================================


class TestLogSanitization:
    """Test log sanitization in auth module"""

    def test_sanitize_log_input_basic(self):
        """Test basic log input sanitization"""
        from api.v1.auth import _sanitize_log_input

        # Create mock self object
        mock_self = Mock()

        # Test sanitization
        result = _sanitize_log_input(mock_self, "test\ndata\rwith\tcontrol")

        # Should replace newlines and tabs with spaces
        assert "\n" not in result
        assert "\r" not in result
        assert "\t" not in result

    def test_sanitize_log_input_length_limit(self):
        """Test log input length limiting"""
        from api.v1.auth import _sanitize_log_input

        # Create mock self object
        mock_self = Mock()

        # Test with long input
        long_input = "x" * 600
        result = _sanitize_log_input(mock_self, long_input)

        # Should truncate to 500 chars
        assert len(result) <= 504  # 500 + "..."
        assert result.endswith("...")

    def test_sanitize_log_input_control_characters(self):
        """Test removal of control characters"""
        from api.v1.auth import _sanitize_log_input

        # Create mock self object
        mock_self = Mock()

        # Test with control characters
        result = _sanitize_log_input(mock_self, "test\x00\x1f\x7fdata")

        # Should remove control characters
        assert "\x00" not in result
        assert "\x1f" not in result
        assert "\x7f" not in result

    def test_sanitize_log_input_non_string(self):
        """Test sanitization of non-string input"""
        from api.v1.auth import _sanitize_log_input

        # Create mock self object
        mock_self = Mock()

        # Test with non-string
        result = _sanitize_log_input(mock_self, 12345)

        # Should convert to string
        assert isinstance(result, str)
        assert "12345" in result


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestAuthenticationIntegration:
    """Integration tests for authentication flow"""

    @pytest.mark.asyncio
    async def test_full_registration_login_flow(self):
        """Test complete registration and login flow"""
        from api.v1.auth import login, register

        # Mock user manager
        with patch("api.v1.auth.user_manager") as mock_manager:
            # Setup mocks for registration
            mock_manager.get_user_by_email.return_value = None

            new_user = User(
                id="newuser123",
                email="newuser@example.com",
                username="newuser",
                role=UserRole.API_USER,
                is_active=True,
                hashed_password="hashed_pwd",
            )
            mock_manager.create_user.return_value = new_user

            # Register
            request = EnhancedRegisterRequest(
                email="newuser@example.com",
                username="newuser",
                password="NewPassword123!",
                role=UserRole.API_USER,
            )

            registered_user = await register(request)
            assert registered_user.email == "newuser@example.com"

            # Setup mocks for login
            mock_manager.authenticate_user.return_value = new_user

            with patch("api.v1.auth.create_user_tokens") as mock_tokens:
                mock_tokens.return_value = TokenResponse(
                    access_token="token",
                    refresh_token="refresh",
                    token_type="bearer",
                    expires_in=1800,
                )

                # Login
                form_data = OAuth2PasswordRequestForm(
                    username="newuser@example.com",
                    password="NewPassword123!",
                    scope="",
                )

                tokens = await login(form_data)
                assert tokens.access_token == "token"


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


class TestAuthenticationErrorHandling:
    """Test error handling in authentication endpoints"""

    @pytest.mark.asyncio
    async def test_register_with_missing_fields(self):
        """Test registration with missing required fields"""
        # This should be caught by Pydantic validation
        with pytest.raises(Exception):  # Will raise ValidationError
            EnhancedRegisterRequest(
                email="test@example.com",
                # Missing username and password
            )

    @pytest.mark.asyncio
    async def test_login_with_empty_credentials(self):
        """Test login with empty credentials"""
        from api.v1.auth import login

        with patch("api.v1.auth.user_manager") as mock_manager:
            mock_manager.authenticate_user.return_value = None

            form_data = OAuth2PasswordRequestForm(
                username="",
                password="",
                scope="",
            )

            with pytest.raises(HTTPException):
                await login(form_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=api.v1.auth", "--cov-report=term-missing"])
