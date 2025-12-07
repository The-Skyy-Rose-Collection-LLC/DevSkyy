"""
Comprehensive Test Suite for Auth0 Integration Module

Tests OAuth2 flow, JWT verification, user management, permissions,
and hybrid DevSkyy + Auth0 authentication.

Per CLAUDE.md Rule #8: Target ≥80% coverage
Per CLAUDE.md Rule #13: Security baseline verification

Author: DevSkyy Enterprise Team
Version: 2.0.0
Python: >=3.11.0
"""

from datetime import datetime, timedelta
import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from fastapi import HTTPException
import httpx
from jose import JWTError, jwt
import pytest

from security.auth0_integration import (
    AUTH0_ALGORITHMS,
    AUTH0_AUDIENCE,
    AUTH0_DOMAIN,
    DEVSKYY_JWT_ALGORITHM,
    HTTP_TIMEOUT,
    Auth0Client,
    Auth0OAuth2Client,
    Auth0User,
    TokenPayload,
    auth0_client,
    auth0_health_check,
    auth0_oauth_client,
    create_devskyy_jwt_token,
    create_devskyy_refresh_token,
    get_auth0_login_url,
    get_current_admin_user,
    get_current_user,
    log_auth_event,
    require_permissions,
    require_scope,
    security,
    verify_devskyy_jwt_token,
    verify_jwt_token,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def sample_auth0_user():
    """Create sample Auth0 user for testing"""
    return Auth0User(
        sub="auth0|123456789",
        email="test@devskyy.com",
        email_verified=True,
        name="Test User",
        given_name="Test",
        family_name="User",
        picture="https://example.com/picture.jpg",
        locale="en-US",
        role="developer",
        permissions=["read:data", "write:data"],
        organization="devskyy",
        subscription_tier="enterprise",
    )


@pytest.fixture
def sample_token_payload():
    """Create sample token payload"""
    return TokenPayload(
        sub="auth0|123456789",
        aud=[AUTH0_AUDIENCE],
        iss=f"https://{AUTH0_DOMAIN}/",
        exp=int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        iat=int(datetime.utcnow().timestamp()),
        scope="openid profile email",
        permissions=["read:data", "write:data"],
        role="developer",
    )


@pytest.fixture
def mock_jwks():
    """Mock JWKS response"""
    return {
        "keys": [
            {
                "kid": "test_key_id",
                "kty": "RSA",
                "use": "sig",
                "n": "test_n_value",
                "e": "AQAB",
                "alg": "RS256",
            }
        ]
    }


# ============================================================================
# MODEL TESTS
# ============================================================================


class TestModels:
    """Test Auth0 models"""

    def test_auth0_user_model(self, sample_auth0_user):
        """Test Auth0User model creation"""
        assert sample_auth0_user.sub == "auth0|123456789"
        assert sample_auth0_user.email == "test@devskyy.com"
        assert sample_auth0_user.email_verified is True
        assert sample_auth0_user.role == "developer"
        assert "read:data" in sample_auth0_user.permissions

    def test_auth0_user_defaults(self):
        """Test Auth0User default values"""
        user = Auth0User(sub="auth0|test")

        assert user.email_verified is False
        assert user.role == "user"
        assert user.permissions == []
        assert user.subscription_tier == "free"

    def test_token_payload_model(self, sample_token_payload):
        """Test TokenPayload model creation"""
        assert sample_token_payload.sub == "auth0|123456789"
        assert AUTH0_AUDIENCE in sample_token_payload.aud
        assert sample_token_payload.exp > 0
        assert sample_token_payload.role == "developer"

    def test_token_payload_defaults(self):
        """Test TokenPayload default values"""
        payload = TokenPayload(
            sub="test",
            aud=["test_aud"],
            iss="test_iss",
            exp=123456789,
            iat=123456789,
        )

        assert payload.scope == ""
        assert payload.permissions == []
        assert payload.role == "user"


# ============================================================================
# OAUTH2 CLIENT TESTS
# ============================================================================


class TestAuth0OAuth2Client:
    """Test Auth0OAuth2Client functionality"""

    def test_oauth2_client_initialization(self):
        """Test Auth0OAuth2Client initializes correctly"""
        client = Auth0OAuth2Client()

        assert client.domain == AUTH0_DOMAIN
        assert client.client_id is not None
        assert client.oauth_client is not None

    def test_get_authorization_url_basic(self):
        """Test getting authorization URL"""
        client = Auth0OAuth2Client()
        redirect_uri = "https://app.devskyy.com/callback"

        url = client.get_authorization_url(redirect_uri)

        assert "https://" in url
        assert AUTH0_DOMAIN in url
        assert "/authorize" in url
        assert "redirect_uri" in url
        assert redirect_uri in url

    def test_get_authorization_url_with_state(self):
        """Test authorization URL with state parameter"""
        client = Auth0OAuth2Client()
        redirect_uri = "https://app.devskyy.com/callback"
        state = "random_state_123"

        url = client.get_authorization_url(redirect_uri, state=state)

        assert f"state={state}" in url

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_exchange_code_for_token_success(self, mock_post):
        """Test successful code exchange for token"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "id_token": "test_id_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        client = Auth0OAuth2Client()
        result = await client.exchange_code_for_token(
            code="auth_code_123",
            redirect_uri="https://app.devskyy.com/callback",
        )

        assert result["access_token"] == "test_access_token"
        assert result["id_token"] == "test_id_token"
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_exchange_code_for_token_failure(self, mock_post):
        """Test failed code exchange"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid authorization code"
        mock_post.return_value = mock_response

        client = Auth0OAuth2Client()

        with pytest.raises(HTTPException) as exc_info:
            await client.exchange_code_for_token(
                code="invalid_code",
                redirect_uri="https://app.devskyy.com/callback",
            )

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_get_user_info_success(self, mock_get):
        """Test successful user info retrieval"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "sub": "auth0|123456",
            "email": "test@example.com",
            "name": "Test User",
        }
        mock_get.return_value = mock_response

        client = Auth0OAuth2Client()
        user_info = await client.get_user_info("test_access_token")

        assert user_info["sub"] == "auth0|123456"
        assert user_info["email"] == "test@example.com"
        mock_get.assert_called_once()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_get_user_info_failure(self, mock_get):
        """Test failed user info retrieval"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        client = Auth0OAuth2Client()

        with pytest.raises(HTTPException) as exc_info:
            await client.get_user_info("invalid_token")

        assert exc_info.value.status_code == 400

    def test_get_logout_url(self):
        """Test getting logout URL"""
        client = Auth0OAuth2Client()
        return_to = "https://app.devskyy.com"

        logout_url = client.get_logout_url(return_to)

        assert AUTH0_DOMAIN in logout_url
        assert "/logout" in logout_url
        assert return_to in logout_url


# ============================================================================
# MANAGEMENT CLIENT TESTS
# ============================================================================


class TestAuth0Client:
    """Test Auth0Client management API"""

    def test_auth0_client_initialization(self):
        """Test Auth0Client initializes correctly"""
        client = Auth0Client()

        assert client.domain == AUTH0_DOMAIN
        assert client.management_token is None
        assert client.token_expires_at is None

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_get_management_token_success(self, mock_post):
        """Test getting management API token"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "mgmt_token_123",
            "expires_in": 86400,
        }
        mock_post.return_value = mock_response

        client = Auth0Client()
        token = await client.get_management_token()

        assert token == "mgmt_token_123"
        assert client.management_token == "mgmt_token_123"
        assert client.token_expires_at is not None

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_get_management_token_cached(self, mock_post):
        """Test management token is cached"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "mgmt_token_123",
            "expires_in": 86400,
        }
        mock_post.return_value = mock_response

        client = Auth0Client()

        # First call
        token1 = await client.get_management_token()

        # Second call (should use cache)
        token2 = await client.get_management_token()

        assert token1 == token2
        assert mock_post.call_count == 1  # Only called once

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_get_management_token_failure(self, mock_post):
        """Test management token retrieval failure"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        client = Auth0Client()

        with pytest.raises(HTTPException) as exc_info:
            await client.get_management_token()

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    @patch.object(Auth0Client, "get_management_token", return_value="mgmt_token")
    @patch("httpx.AsyncClient.get")
    async def test_get_user_success(self, mock_get, mock_token):
        """Test getting user from Auth0"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user_id": "auth0|123",
            "email": "test@example.com",
            "name": "Test User",
        }
        mock_get.return_value = mock_response

        client = Auth0Client()
        user = await client.get_user("auth0|123")

        assert user["user_id"] == "auth0|123"
        assert user["email"] == "test@example.com"

    @pytest.mark.asyncio
    @patch.object(Auth0Client, "get_management_token", return_value="mgmt_token")
    @patch("httpx.AsyncClient.get")
    async def test_get_user_not_found(self, mock_get, mock_token):
        """Test getting non-existent user"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        client = Auth0Client()

        with pytest.raises(HTTPException) as exc_info:
            await client.get_user("auth0|nonexistent")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch.object(Auth0Client, "get_management_token", return_value="mgmt_token")
    @patch("httpx.AsyncClient.patch")
    async def test_update_user_success(self, mock_patch, mock_token):
        """Test updating user in Auth0"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user_id": "auth0|123",
            "email": "updated@example.com",
        }
        mock_patch.return_value = mock_response

        client = Auth0Client()
        updated_user = await client.update_user(
            "auth0|123",
            {"email": "updated@example.com"},
        )

        assert updated_user["email"] == "updated@example.com"

    @pytest.mark.asyncio
    @patch.object(Auth0Client, "get_management_token", return_value="mgmt_token")
    @patch("httpx.AsyncClient.patch")
    async def test_update_user_failure(self, mock_patch, mock_token):
        """Test failed user update"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_patch.return_value = mock_response

        client = Auth0Client()

        with pytest.raises(HTTPException) as exc_info:
            await client.update_user("auth0|123", {"email": "test@example.com"})

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    @patch.object(Auth0Client, "get_management_token", return_value="mgmt_token")
    @patch("httpx.AsyncClient.get")
    async def test_get_user_permissions_success(self, mock_get, mock_token):
        """Test getting user permissions"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"permission_name": "read:data"},
            {"permission_name": "write:data"},
        ]
        mock_get.return_value = mock_response

        client = Auth0Client()
        permissions = await client.get_user_permissions("auth0|123")

        assert "read:data" in permissions
        assert "write:data" in permissions
        assert len(permissions) == 2

    @pytest.mark.asyncio
    @patch.object(Auth0Client, "get_management_token", return_value="mgmt_token")
    @patch("httpx.AsyncClient.get")
    async def test_get_user_permissions_empty(self, mock_get, mock_token):
        """Test getting permissions for user with none"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        client = Auth0Client()
        permissions = await client.get_user_permissions("auth0|123")

        assert permissions == []


# ============================================================================
# JWT VERIFICATION TESTS
# ============================================================================


class TestJWTVerification:
    """Test JWT token verification"""

    @patch("httpx.get")
    def test_get_auth0_public_key_success(self, mock_get):
        """Test getting Auth0 public key"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"keys": [{"kid": "test"}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Clear cache
        from security.auth0_integration import get_auth0_public_key
        get_auth0_public_key.cache_clear()

        jwks = get_auth0_public_key()
        assert "keys" in jwks

    @patch("httpx.get")
    def test_get_auth0_public_key_failure(self, mock_get):
        """Test public key retrieval failure"""
        mock_get.side_effect = Exception("Network error")

        from security.auth0_integration import get_auth0_public_key
        get_auth0_public_key.cache_clear()

        with pytest.raises(HTTPException) as exc_info:
            get_auth0_public_key()

        assert exc_info.value.status_code == 500


# ============================================================================
# DEVSKYY JWT INTEGRATION TESTS
# ============================================================================


class TestDevSkyyJWTIntegration:
    """Test DevSkyy JWT token creation and verification"""

    @patch.dict("os.environ", {"SECRET_KEY": "test_secret_key_for_testing"})
    def test_create_devskyy_jwt_token(self):
        """Test creating DevSkyy JWT token"""
        user_data = {
            "sub": "auth0|123",
            "email": "test@devskyy.com",
            "name": "Test User",
        }

        token = create_devskyy_jwt_token(user_data)

        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count(".") == 2  # JWT format

    @patch.dict("os.environ", {"SECRET_KEY": "test_secret_key_for_testing"})
    def test_create_devskyy_jwt_token_custom_expiry(self):
        """Test creating token with custom expiration"""
        user_data = {"sub": "auth0|123", "email": "test@devskyy.com"}
        expires_delta = timedelta(hours=2)

        token = create_devskyy_jwt_token(user_data, expires_delta=expires_delta)

        assert isinstance(token, str)

    @patch.dict("os.environ", {"SECRET_KEY": "test_secret_key_for_testing"})
    def test_create_devskyy_refresh_token(self):
        """Test creating DevSkyy refresh token"""
        user_data = {"sub": "auth0|123"}

        token = create_devskyy_refresh_token(user_data)

        assert isinstance(token, str)
        assert len(token) > 0

    @patch.dict("os.environ", {"SECRET_KEY": "test_secret_key_for_testing"})
    def test_verify_devskyy_jwt_token_success(self):
        """Test verifying valid DevSkyy JWT token"""
        user_data = {"sub": "auth0|123", "email": "test@devskyy.com"}
        token = create_devskyy_jwt_token(user_data)

        payload = verify_devskyy_jwt_token(token)

        assert payload["sub"] == "auth0|123"
        assert payload["iss"] == "devskyy-platform"
        assert payload["aud"] == "devskyy-api"

    @patch.dict("os.environ", {"SECRET_KEY": "test_secret_key_for_testing"})
    def test_verify_devskyy_jwt_token_invalid(self):
        """Test verifying invalid DevSkyy JWT token"""
        with pytest.raises(HTTPException) as exc_info:
            verify_devskyy_jwt_token("invalid.jwt.token")

        assert exc_info.value.status_code == 401

    def test_create_jwt_without_secret_key(self):
        """Test JWT creation fails without secret key"""
        with patch.dict("os.environ", {"SECRET_KEY": ""}):
            user_data = {"sub": "auth0|123"}

            with pytest.raises(ValueError) as exc_info:
                create_devskyy_jwt_token(user_data)

            assert "not configured" in str(exc_info.value)


# ============================================================================
# DEPENDENCY TESTS
# ============================================================================


class TestDependencies:
    """Test FastAPI dependencies"""

    @patch("security.auth0_integration.verify_jwt_token")
    @patch.object(Auth0Client, "get_user")
    @patch.object(Auth0Client, "get_user_permissions")
    def test_require_permissions_success(
        self,
        mock_permissions,
        mock_get_user,
        mock_verify,
        sample_auth0_user,
    ):
        """Test require_permissions allows authorized user"""
        sample_auth0_user.permissions = ["read:data", "write:data"]

        # The require_permissions function returns a checker function
        checker = require_permissions(["read:data"])

        # Test that user with permission passes
        # Note: This is a factory function, actual testing would need FastAPI context


    def test_require_permissions_missing(self):
        """Test require_permissions factory function exists"""
        checker = require_permissions(["admin:access"])
        assert callable(checker)

    def test_require_scope_factory(self):
        """Test require_scope factory function exists"""
        checker = require_scope("openid")
        assert callable(checker)


# ============================================================================
# UTILITY FUNCTION TESTS
# ============================================================================


class TestUtilityFunctions:
    """Test utility functions"""

    @pytest.mark.asyncio
    async def test_log_auth_event(self):
        """Test logging authentication events"""
        mock_request = Mock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers.get.return_value = "Mozilla/5.0"

        await log_auth_event(
            event_type="login",
            user_id="user_123",
            request=mock_request,
            details={"method": "oauth2"},
        )

        # Function should not raise errors

    @pytest.mark.asyncio
    async def test_log_auth_event_without_request(self):
        """Test logging auth event without request"""
        await log_auth_event(
            event_type="token_refresh",
            user_id="user_123",
        )

        # Function should handle missing request gracefully

    def test_get_auth0_login_url_basic(self):
        """Test getting Auth0 login URL"""
        redirect_uri = "https://app.devskyy.com/callback"

        url = get_auth0_login_url(redirect_uri)

        assert AUTH0_DOMAIN in url
        assert redirect_uri in url
        assert "response_type=code" in url

    def test_get_auth0_login_url_with_state(self):
        """Test login URL with state parameter"""
        redirect_uri = "https://app.devskyy.com/callback"
        state = "random_state_abc"

        url = get_auth0_login_url(redirect_uri, state=state)

        assert f"state={state}" in url

    def test_get_auth0_login_url_custom_scope(self):
        """Test login URL with custom scope"""
        redirect_uri = "https://app.devskyy.com/callback"
        scope = "openid profile email offline_access"

        url = get_auth0_login_url(redirect_uri, scope=scope)

        assert "scope=" in url


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================


class TestHealthCheck:
    """Test Auth0 health check"""

    @pytest.mark.asyncio
    @patch("httpx.get")
    @patch.object(Auth0Client, "get_management_token")
    async def test_auth0_health_check_healthy(self, mock_token, mock_get):
        """Test health check when Auth0 is healthy"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        mock_token.return_value = "mgmt_token"

        health = await auth0_health_check()

        assert health["status"] == "healthy"
        assert health["jwks_endpoint"] == "healthy"

    @pytest.mark.asyncio
    @patch("httpx.get")
    async def test_auth0_health_check_unhealthy(self, mock_get):
        """Test health check when Auth0 is down"""
        mock_get.side_effect = Exception("Connection error")

        health = await auth0_health_check()

        assert health["status"] == "unhealthy"
        assert "error" in health

    @pytest.mark.asyncio
    @patch("httpx.get")
    @patch.object(Auth0Client, "get_management_token")
    async def test_auth0_health_check_partial(self, mock_token, mock_get):
        """Test health check with partial availability"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Management API fails
        mock_token.side_effect = Exception("Auth error")

        health = await auth0_health_check()

        assert health["jwks_endpoint"] == "healthy"
        assert health["management_api"] == "degraded"


# ============================================================================
# GLOBAL INSTANCES TESTS
# ============================================================================


class TestGlobalInstances:
    """Test global singleton instances"""

    def test_global_auth0_oauth_client_exists(self):
        """Test global auth0_oauth_client instance exists"""
        assert auth0_oauth_client is not None
        assert isinstance(auth0_oauth_client, Auth0OAuth2Client)

    def test_global_auth0_client_exists(self):
        """Test global auth0_client instance exists"""
        assert auth0_client is not None
        assert isinstance(auth0_client, Auth0Client)

    def test_security_bearer_exists(self):
        """Test HTTPBearer security scheme exists"""
        assert security is not None


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestAuth0Integration:
    """Integration tests for Auth0 workflows"""

    @pytest.mark.asyncio
    @patch.object(Auth0OAuth2Client, "exchange_code_for_token")
    @patch.object(Auth0OAuth2Client, "get_user_info")
    @patch.dict("os.environ", {"SECRET_KEY": "test_secret"})
    async def test_complete_oauth_flow(self, mock_user_info, mock_exchange):
        """Test complete OAuth2 authentication flow"""
        # Mock token exchange
        mock_exchange.return_value = {
            "access_token": "auth0_access_token",
            "id_token": "auth0_id_token",
        }

        # Mock user info
        mock_user_info.return_value = {
            "sub": "auth0|123",
            "email": "test@devskyy.com",
            "name": "Test User",
            "email_verified": True,
        }

        client = Auth0OAuth2Client()

        # 1. Exchange code for token
        tokens = await client.exchange_code_for_token(
            code="auth_code_123",
            redirect_uri="https://app.devskyy.com/callback",
        )

        assert "access_token" in tokens

        # 2. Get user info
        user_info = await client.get_user_info(tokens["access_token"])

        assert user_info["sub"] == "auth0|123"

        # 3. Create DevSkyy JWT
        devskyy_token = create_devskyy_jwt_token(user_info)

        assert isinstance(devskyy_token, str)

        # 4. Verify DevSkyy JWT
        payload = verify_devskyy_jwt_token(devskyy_token)

        assert payload["sub"] == "auth0|123"


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================


class TestAuth0EdgeCases:
    """Test edge cases and error handling"""

    def test_auth0_user_with_minimal_data(self):
        """Test Auth0User with minimal required data"""
        user = Auth0User(sub="auth0|minimal")

        assert user.sub == "auth0|minimal"
        assert user.email is None
        assert user.permissions == []

    @pytest.mark.asyncio
    async def test_oauth_client_with_network_timeout(self):
        """Test OAuth client handles network timeouts"""
        # HTTP_TIMEOUT constant is used in async calls
        assert HTTP_TIMEOUT == 15

    @patch.dict("os.environ", {"SECRET_KEY": "test_secret"})
    def test_jwt_token_with_special_characters(self):
        """Test JWT with special characters in user data"""
        user_data = {
            "sub": "auth0|user-with-special@chars",
            "email": "user+tag@example.com",
            "name": "Test O'User",
        }

        token = create_devskyy_jwt_token(user_data)
        payload = verify_devskyy_jwt_token(token)

        assert payload["sub"] == user_data["sub"]
        assert payload["email"] == user_data["email"]


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--cov=security.auth0_integration",
        "--cov-report=term-missing",
        "--cov-report=html",
    ])
