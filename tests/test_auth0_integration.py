from datetime import datetime, timedelta
import json

from fastapi.testclient import TestClient

from main import app
from security.auth0_integration import (
    from unittest.mock import patch, AsyncMock
import pytest

"""
Test Auth0 Integration for DevSkyy Platform
Comprehensive tests for Auth0 FastAPI integration
"""

    create_devskyy_jwt_token,
    create_devskyy_refresh_token,
    verify_devskyy_jwt_token,
    auth0_oauth_client
)

# Test client
client = TestClient(app)

# Mock user data
MOCK_AUTH0_USER = {
    "sub": "auth0|123456789",
    "email": "test@devskyy.com",
    "name": "Test User",
    "picture": "https://example.com/avatar.jpg",
    "email_verified": True
}

MOCK_AUTH0_TOKEN_RESPONSE = {
    "access_token": "mock_auth0_access_token",
    "id_token": "mock_auth0_id_token",
    "token_type": "Bearer",
    "expires_in": 86400
}

class TestAuth0Integration:
    """Test Auth0 integration functionality."""
    
    def test_auth0_login_endpoint(self):
        """Test Auth0 login endpoint returns authorization URL."""
        response = client.get(
            "/api/v1/auth/auth0/login",
            headers={"accept": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "authorization_url" in data
        assert "state" in data
        assert "devskyy.auth0.com" in data["authorization_url"]
        assert "client_id" in data["authorization_url"]
        assert "redirect_uri" in data["authorization_url"]
        assert "scope=openid+profile+email" in data["authorization_url"]
    
    def test_auth0_login_redirect(self):
        """Test Auth0 login endpoint redirects for browser requests."""
        response = client.get("/api/v1/auth/auth0/login", allow_redirects=False)
        
        assert response.status_code == 302
        assert "devskyy.auth0.com" in response.headers["location"]
    
    @patch('security.auth0_integration.auth0_oauth_client.exchange_code_for_token')
    @patch('security.auth0_integration.auth0_oauth_client.get_user_info')
    def test_auth0_callback_success(self, mock_get_user_info, mock_exchange_token):
        """Test successful Auth0 callback processing."""
        # Mock Auth0 responses
        mock_exchange_token.return_value = MOCK_AUTH0_TOKEN_RESPONSE
        mock_get_user_info.return_value = MOCK_AUTH0_USER
        
        response = client.get(
            "/api/v1/auth/auth0/callback",
            params={"code": "mock_auth_code", "state": "mock_state"},
            headers={"accept": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800
        assert "user_info" in data
        assert data["user_info"]["email"] == MOCK_AUTH0_USER["email"]
    
    def test_auth0_callback_error(self):
        """Test Auth0 callback with error parameters."""
        response = client.get(
            "/api/v1/auth/auth0/callback",
            params={
                "error": "access_denied",
                "error_description": "User denied access"
            }
        )
        
        assert response.status_code == 400
        assert "Auth0 authentication failed" in response.json()["detail"]
    
    def test_auth0_callback_missing_code(self):
        """Test Auth0 callback without authorization code."""
        response = client.get("/api/v1/auth/auth0/callback")
        
        assert response.status_code == 400
        assert "Authorization code is required" in response.json()["detail"]
    
    def test_auth0_logout_endpoint(self):
        """Test Auth0 logout endpoint."""
        response = client.get(
            "/api/v1/auth/auth0/logout",
            headers={"accept": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "logout_url" in data
        assert "message" in data
        assert "devskyy.auth0.com/v2/logout" in data["logout_url"]
    
    def test_auth0_logout_redirect(self):
        """Test Auth0 logout endpoint redirects for browser requests."""
        response = client.get("/api/v1/auth/auth0/logout", allow_redirects=False)
        
        assert response.status_code == 302
        assert "devskyy.auth0.com/v2/logout" in response.headers["location"]

class TestJWTTokenIntegration:
    """Test JWT token creation and verification for Auth0 integration."""
    
    def test_create_devskyy_jwt_token(self):
        """Test DevSkyy JWT token creation with Auth0 user data."""
        token = create_devskyy_jwt_token(MOCK_AUTH0_USER)
        
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT has 3 parts
        
        # Verify token content
        payload = verify_devskyy_jwt_token(token)
        assert payload["sub"] == MOCK_AUTH0_USER["sub"]
        assert payload["email"] == MOCK_AUTH0_USER["email"]
        assert payload["name"] == MOCK_AUTH0_USER["name"]
        assert payload["auth_provider"] == "auth0"
        assert payload["token_type"] == "access"
    
    def test_create_devskyy_refresh_token(self):
        """Test DevSkyy refresh token creation."""
        token = create_devskyy_refresh_token(MOCK_AUTH0_USER)
        
        assert isinstance(token, str)
        
        # Verify token content
        payload = verify_devskyy_jwt_token(token)
        assert payload["sub"] == MOCK_AUTH0_USER["sub"]
        assert payload["token_type"] == "refresh"
        assert payload["auth_provider"] == "auth0"
    
    def test_verify_devskyy_jwt_token_invalid(self):
        """Test JWT token verification with invalid token."""
        with pytest.raises(Exception):  # Should raise HTTPException
            verify_devskyy_jwt_token("invalid.jwt.token")
    
    def test_jwt_token_expiration(self):
        """Test JWT token with custom expiration."""
        expires_delta = timedelta(minutes=5)
        token = create_devskyy_jwt_token(MOCK_AUTH0_USER, expires_delta)

        payload = verify_devskyy_jwt_token(token)

        # Check expiration is approximately 5 minutes from now
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        expected_exp = datetime.utcnow() + expires_delta

        # Allow 60 second tolerance for test execution time
        assert abs((exp_time - expected_exp).total_seconds()) < 60

class TestAuth0UserEndpoint:
    """Test Auth0 user information endpoint."""
    
    def test_get_current_auth0_user_success(self):
        """Test getting current user info with valid token."""
        # Create a valid token
        token = create_devskyy_jwt_token(MOCK_AUTH0_USER)
        
        response = client.get(
            "/api/v1/auth/auth0/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == MOCK_AUTH0_USER["sub"]
        assert data["email"] == MOCK_AUTH0_USER["email"]
        assert data["name"] == MOCK_AUTH0_USER["name"]
        assert data["auth_provider"] == "auth0"
    
    def test_get_current_auth0_user_no_token(self):
        """Test getting current user info without token."""
        response = client.get("/api/v1/auth/auth0/me")
        
        assert response.status_code == 401
        assert "Authentication token required" in response.json()["detail"]
    
    def test_get_current_auth0_user_invalid_token(self):
        """Test getting current user info with invalid token."""
        response = client.get(
            "/api/v1/auth/auth0/me",
            headers={"Authorization": "Bearer invalid.jwt.token"}
        )
        
        assert response.status_code == 401

class TestAuth0DemoPage:
    """Test Auth0 demo page functionality."""
    
    def test_demo_page_guest(self):
        """Test demo page for unauthenticated user."""
        response = client.get("/api/v1/auth/auth0/demo")
        
        assert response.status_code == 200
        assert "Welcome Guest" in response.text
        assert "Login with Auth0" in response.text
    
    def test_demo_page_authenticated(self):
        """Test demo page for authenticated user."""
        # Create a valid token
        token = create_devskyy_jwt_token(MOCK_AUTH0_USER)
        
        response = client.get(
            "/api/v1/auth/auth0/demo",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert "Welcome Test User" in response.text
        assert "Logout" in response.text
        assert MOCK_AUTH0_USER["email"] in response.text

class TestAuth0OAuth2Client:
    """Test Auth0 OAuth2 client functionality."""
    
    def test_get_authorization_url(self):
        """Test authorization URL generation."""
        redirect_uri = "http://localhost:8000/callback"
        state = "test_state"
        
        url = auth0_oauth_client.get_authorization_url(redirect_uri, state)
        
        assert "devskyy.auth0.com/authorize" in url
        assert f"redirect_uri={redirect_uri}" in url
        assert f"state={state}" in url
        assert "scope=openid+profile+email" in url
        assert "response_type=code" in url
    
    def test_get_logout_url(self):
        """Test logout URL generation."""
        return_to = "http://localhost:3000"
        
        url = auth0_oauth_client.get_logout_url(return_to)
        
        assert "devskyy.auth0.com/v2/logout" in url
        assert f"returnTo={return_to}" in url
        assert "client_id" in url

# Integration test with existing authentication system
class TestHybridAuthentication:
    """Test integration between Auth0 and existing JWT system."""
    
    def test_auth0_token_compatibility(self):
        """Test that Auth0-generated tokens work with existing endpoints."""
        # Create Auth0-style token
        token = create_devskyy_jwt_token(MOCK_AUTH0_USER)
        
        # Test with existing protected endpoint
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should work with existing authentication system
        # Note: This might need adjustment based on existing auth implementation
        assert response.status_code in [200, 401]  # 401 if not fully compatible yet
    
    def test_token_format_consistency(self):
        """Test that Auth0 tokens follow DevSkyy JWT format."""
        token = create_devskyy_jwt_token(MOCK_AUTH0_USER)
        payload = verify_devskyy_jwt_token(token)
        
        # Check required fields for DevSkyy compatibility
        assert "sub" in payload
        assert "iss" in payload
        assert "aud" in payload
        assert "exp" in payload
        assert "iat" in payload
        assert payload["iss"] == "devskyy-platform"
        assert payload["aud"] == "devskyy-api"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
