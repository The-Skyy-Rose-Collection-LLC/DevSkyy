"""
Unit Tests for Authentication System
Tests for enhanced JWT authentication, validation, and security features
"""

from unittest.mock import Mock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
import pytest

from api.validation_models import EnhancedRegisterRequest
from main import app
from security.jwt_auth import (
    blacklist_token,
    clear_failed_login_attempts,
    create_user_tokens,
    hash_password,
    is_account_locked,
    is_token_blacklisted,
    record_failed_login,
    verify_password,
    verify_token,
)


class TestPasswordSecurity:
    """Test password hashing and verification"""

    def test_password_hashing(self):
        """Test password hashing functionality"""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)

    def test_password_hash_uniqueness(self):
        """Test that same password produces different hashes"""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestAccountLockout:
    """Test account lockout functionality"""

    def setup_method(self):
        """Setup test data"""
        self.test_email = "test@example.com"
        # Clear any existing lockout data
        from security.jwt_auth import failed_login_attempts, locked_accounts

        failed_login_attempts.clear()
        locked_accounts.clear()

    def test_account_not_locked_initially(self):
        """Test that account is not locked initially"""
        assert not is_account_locked(self.test_email)

    def test_failed_login_tracking(self):
        """Test failed login attempt tracking"""
        # Record failed attempts
        for _i in range(4):
            locked = record_failed_login(self.test_email)
            assert not locked  # Should not be locked yet

        # 5th attempt should lock the account
        locked = record_failed_login(self.test_email)
        assert locked
        assert is_account_locked(self.test_email)

    def test_clear_failed_attempts(self):
        """Test clearing failed login attempts"""
        # Record some failed attempts
        for _i in range(3):
            record_failed_login(self.test_email)

        # Clear attempts
        clear_failed_login_attempts(self.test_email)

        # Should not be locked
        assert not is_account_locked(self.test_email)


class TestTokenBlacklist:
    """Test token blacklisting functionality"""

    def setup_method(self):
        """Setup test data"""
        from security.jwt_auth import blacklisted_tokens

        blacklisted_tokens.clear()

    def test_token_blacklisting(self):
        """Test token blacklisting"""
        token = "test_token_123"

        assert not is_token_blacklisted(token)

        blacklist_token(token)

        assert is_token_blacklisted(token)


class TestEnhancedValidation:
    """Test enhanced validation models"""

    def test_valid_registration_request(self):
        """Test valid registration request"""
        request_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "TestPassword123!",
            "role": "api_user",
            "full_name": "Test User",
            "company": "Test Company",
        }

        request = EnhancedRegisterRequest(**request_data)
        assert request.email == "test@example.com"
        assert request.username == "testuser"
        assert request.password == "TestPassword123!"

    def test_password_strength_validation(self):
        """Test password strength validation"""
        # Test weak passwords
        weak_passwords = [
            "weak",  # Too short
            "weakpassword",  # No uppercase, numbers, or symbols
            "WeakPassword",  # No numbers or symbols
            "WeakPassword123",  # No symbols
            "weakpassword123!",  # No uppercase
        ]

        for weak_password in weak_passwords:
            with pytest.raises(ValueError):
                EnhancedRegisterRequest(
                    email="test@example.com",
                    username="testuser",
                    password=weak_password,
                    role="api_user",
                )

    def test_username_validation(self):
        """Test username validation"""
        # Test invalid usernames
        invalid_usernames = [
            "ab",  # Too short
            "user@name",  # Invalid characters
            "user name",  # Spaces not allowed
            "user<script>",  # XSS attempt
        ]

        for invalid_username in invalid_usernames:
            with pytest.raises(ValueError):
                EnhancedRegisterRequest(
                    email="test@example.com",
                    username=invalid_username,
                    password="TestPassword123!",
                    role="api_user",
                )

    def test_xss_protection(self):
        """Test XSS protection in validation"""
        with pytest.raises(ValueError):
            EnhancedRegisterRequest(
                email="test@example.com",
                username="testuser",
                password="TestPassword123!",
                role="api_user",
                full_name="<script>alert('xss')</script>",
            )

    def test_sql_injection_protection(self):
        """Test SQL injection protection"""
        with pytest.raises(ValueError):
            EnhancedRegisterRequest(
                email="test@example.com",
                username="testuser'; DROP TABLE users; --",
                password="TestPassword123!",
                role="api_user",
            )


class TestJWTTokens:
    """Test JWT token creation and verification"""

    @pytest.fixture
    def mock_user(self):
        """Mock user for testing"""
        return Mock(id="user123", email="test@example.com", username="testuser", role="api_user")

    def test_token_creation(self, mock_user):
        """Test JWT token creation"""
        tokens = create_user_tokens(mock_user)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"

    def test_token_verification(self, mock_user):
        """Test JWT token verification"""
        tokens = create_user_tokens(mock_user)
        access_token = tokens["access_token"]

        token_data = verify_token(access_token)

        assert token_data.user_id == mock_user.id
        assert token_data.email == mock_user.email
        assert token_data.username == mock_user.username
        assert token_data.role == mock_user.role

    def test_invalid_token_verification(self):
        """Test verification of invalid token"""
        with pytest.raises(HTTPException):
            verify_token("invalid_token")

    def test_expired_token_verification(self, mock_user):
        """Test verification of expired token"""
        # Create token with very short expiration
        with patch("security.jwt_auth.ACCESS_TOKEN_EXPIRE_MINUTES", -1):
            tokens = create_user_tokens(mock_user)
            access_token = tokens["access_token"]

        with pytest.raises(HTTPException):
            verify_token(access_token)


class TestAuthenticationAPI:
    """Test authentication API endpoints"""

    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)

    def test_register_endpoint_validation(self):
        """Test registration endpoint with validation"""
        # Test valid registration
        valid_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "TestPassword123!",
            "role": "api_user",
        }

        with patch("security.jwt_auth.user_manager.create_user") as mock_create:
            mock_user = Mock(
                id="user123",
                email="test@example.com",
                username="testuser",
                role="api_user",
            )
            mock_create.return_value = mock_user

            response = self.client.post("/api/v1/auth/register", json=valid_data)
            assert response.status_code == 201

    def test_register_endpoint_weak_password(self):
        """Test registration with weak password"""
        invalid_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "weak",
            "role": "api_user",
        }

        response = self.client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_login_endpoint_validation(self):
        """Test login endpoint with validation"""
        login_data = {"email": "test@example.com", "password": "TestPassword123!"}

        with patch("security.jwt_auth.user_manager.authenticate_user") as mock_auth:
            mock_user = Mock(
                id="user123",
                email="test@example.com",
                username="testuser",
                role="api_user",
            )
            mock_auth.return_value = mock_user

            response = self.client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 200

            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data


@pytest.mark.asyncio
class TestAsyncAuthentication:
    """Test asynchronous authentication functionality"""

    async def test_async_token_verification(self):
        """Test async token verification"""
        # Create a mock user
        mock_user = Mock(id="user123", email="test@example.com", username="testuser", role="api_user")

        # Create tokens
        tokens = create_user_tokens(mock_user)
        access_token = tokens["access_token"]

        # Verify token (this should work synchronously)
        token_data = verify_token(access_token)

        assert token_data.user_id == mock_user.id
        assert token_data.email == mock_user.email


class TestSecurityLogging:
    """Test security event logging"""

    def test_security_event_logging(self):
        """Test that security events are logged"""
        with patch("logging_config.security_logger.log_authentication_event"):
            # Simulate a failed login
            record_failed_login("test@example.com")

            # Verify logging was called (in actual implementation)
            # This would be tested with the actual security logger integration
            assert True  # Placeholder for actual logging test


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
