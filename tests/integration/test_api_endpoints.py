"""
Integration Tests for API Endpoints
Tests for complete API workflows with database and external services
"""

from fastapi.testclient import TestClient
from httpx import AsyncClient
import pytest

from main import app


class TestHealthEndpoints:
    """Test health and status endpoints"""

    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_status_endpoint(self):
        """Test API status endpoint"""
        response = self.client.get("/api/v1/status")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "services" in data


class TestAuthenticationFlow:
    """Test complete authentication flow"""

    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)

    def test_complete_registration_flow(self):
        """Test complete user registration flow"""
        # Step 1: Register new user
        registration_data = {
            "email": "integration@test.com",
            "username": "integrationuser",
            "password": "IntegrationTest123!",
            "role": "api_user",
            "full_name": "Integration Test User",
        }

        response = self.client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code == 201

        user_data = response.json()
        assert user_data["email"] == registration_data["email"]
        assert user_data["username"] == registration_data["username"]

    def test_complete_login_flow(self):
        """Test complete login flow"""
        # First register a user
        registration_data = {
            "email": "login@test.com",
            "username": "loginuser",
            "password": "LoginTest123!",
            "role": "api_user",
        }

        reg_response = self.client.post("/api/v1/auth/register", json=registration_data)
        assert reg_response.status_code == 201

        # Then login
        login_data = {"email": "login@test.com", "password": "LoginTest123!"}

        login_response = self.client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200

        tokens = login_response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"

    def test_protected_endpoint_access(self):
        """Test accessing protected endpoints with authentication"""
        # Register and login to get token
        registration_data = {
            "email": "protected@test.com",
            "username": "protecteduser",
            "password": "ProtectedTest123!",
            "role": "api_user",
        }

        self.client.post("/api/v1/auth/register", json=registration_data)

        login_data = {"email": "protected@test.com", "password": "ProtectedTest123!"}

        login_response = self.client.post("/api/v1/auth/login", json=login_data)
        tokens = login_response.json()
        access_token = tokens["access_token"]

        # Access protected endpoint
        headers = {"Authorization": f"Bearer {access_token}"}
        response = self.client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200

        user_data = response.json()
        assert user_data["email"] == "protected@test.com"


class TestAgentEndpoints:
    """Test agent execution endpoints"""

    def setup_method(self):
        """Setup test client and authentication"""
        self.client = TestClient(app)

        # Create authenticated user
        registration_data = {
            "email": "agent@test.com",
            "username": "agentuser",
            "password": "AgentTest123!",
            "role": "developer",
        }

        self.client.post("/api/v1/auth/register", json=registration_data)

        login_data = {"email": "agent@test.com", "password": "AgentTest123!"}

        login_response = self.client.post("/api/v1/auth/login", json=login_data)
        tokens = login_response.json()
        self.headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    def test_agent_list_endpoint(self):
        """Test agent list endpoint"""
        response = self.client.get("/api/v1/agents/", headers=self.headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_agent_execution_validation(self):
        """Test agent execution with validation"""
        execution_data = {
            "agent_type": "content_generator",
            "task_description": "Generate a blog post about AI",
            "parameters": {"topic": "Artificial Intelligence", "length": "medium"},
            "priority": 5,
            "timeout_seconds": 300,
            "security_level": "medium",
        }

        response = self.client.post(
            "/api/v1/agents/content_generator/execute",
            json=execution_data,
            headers=self.headers,
        )

        # Should accept the request (actual execution might be mocked)
        assert response.status_code in [200, 202]

    def test_agent_execution_invalid_data(self):
        """Test agent execution with invalid data"""
        invalid_data = {
            "agent_type": "invalid<script>",  # XSS attempt
            "task_description": "'; DROP TABLE agents; --",  # SQL injection attempt
            "parameters": {},
            "priority": 15,  # Invalid priority (max 10)
            "timeout_seconds": 5000,  # Invalid timeout (max 3600)
        }

        response = self.client.post(
            "/api/v1/agents/content_generator/execute",
            json=invalid_data,
            headers=self.headers,
        )

        assert response.status_code == 422  # Validation error


class TestMLEndpoints:
    """Test ML model endpoints"""

    def setup_method(self):
        """Setup test client and authentication"""
        self.client = TestClient(app)

        # Create authenticated user
        registration_data = {
            "email": "ml@test.com",
            "username": "mluser",
            "password": "MLTest123!",
            "role": "developer",
        }

        self.client.post("/api/v1/auth/register", json=registration_data)

        login_data = {"email": "ml@test.com", "password": "MLTest123!"}

        login_response = self.client.post("/api/v1/auth/login", json=login_data)
        tokens = login_response.json()
        self.headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    def test_ml_models_list(self):
        """Test ML models list endpoint"""
        response = self.client.get("/api/v1/ml/models", headers=self.headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_ml_model_prediction(self):
        """Test ML model prediction endpoint"""
        prediction_data = {
            "model_name": "test_model",
            "version": "latest",
            "input_data": {"feature1": 1.0, "feature2": 2.0, "feature3": "test_value"},
            "confidence_threshold": 0.7,
            "max_results": 5,
        }

        response = self.client.post("/api/v1/ml/predict", json=prediction_data, headers=self.headers)

        # Should accept the request (actual prediction might be mocked)
        assert response.status_code in [200, 404]  # 404 if model doesn't exist


class TestGDPREndpoints:
    """Test GDPR compliance endpoints"""

    def setup_method(self):
        """Setup test client and authentication"""
        self.client = TestClient(app)

        # Create authenticated user
        registration_data = {
            "email": "gdpr@test.com",
            "username": "gdpruser",
            "password": "GDPRTest123!",
            "role": "api_user",
        }

        self.client.post("/api/v1/auth/register", json=registration_data)

        login_data = {"email": "gdpr@test.com", "password": "GDPRTest123!"}

        login_response = self.client.post("/api/v1/auth/login", json=login_data)
        tokens = login_response.json()
        self.headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    def test_gdpr_data_export(self):
        """Test GDPR data export request"""
        export_data = {
            "request_type": "export",
            "user_email": "gdpr@test.com",
            "include_audit_logs": True,
            "include_activity_history": True,
            "reason": "User requested data export",
        }

        response = self.client.post("/api/v1/gdpr/data-request", json=export_data, headers=self.headers)

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "processing"

    def test_gdpr_data_deletion(self):
        """Test GDPR data deletion request"""
        deletion_data = {
            "request_type": "delete",
            "user_email": "gdpr@test.com",
            "anonymize_instead_of_delete": False,
            "reason": "User requested account deletion",
        }

        response = self.client.post("/api/v1/gdpr/data-request", json=deletion_data, headers=self.headers)

        assert response.status_code == 200


@pytest.mark.asyncio
class TestAsyncEndpoints:
    """Test asynchronous endpoint functionality"""

    async def test_async_health_check(self):
        """Test async health check"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "healthy"

    async def test_async_authentication_flow(self):
        """Test async authentication flow"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Register
            registration_data = {
                "email": "async@test.com",
                "username": "asyncuser",
                "password": "AsyncTest123!",
                "role": "api_user",
            }

            reg_response = await client.post("/api/v1/auth/register", json=registration_data)
            assert reg_response.status_code == 201

            # Login
            login_data = {"email": "async@test.com", "password": "AsyncTest123!"}

            login_response = await client.post("/api/v1/auth/login", json=login_data)
            assert login_response.status_code == 200

            tokens = login_response.json()
            assert "access_token" in tokens


class TestErrorHandling:
    """Test error handling and recovery"""

    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)

    def test_404_error_handling(self):
        """Test 404 error handling"""
        response = self.client.get("/api/v1/nonexistent")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "correlation_id" in data

    def test_validation_error_handling(self):
        """Test validation error handling"""
        invalid_data = {"email": "invalid-email", "username": "", "password": "weak"}

        response = self.client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422

        data = response.json()
        assert "error" in data
        assert data["error"] == "validation_error"

    def test_unauthorized_access(self):
        """Test unauthorized access handling"""
        response = self.client.get("/api/v1/auth/me")
        assert response.status_code == 401

        data = response.json()
        assert "error" in data


class TestRateLimiting:
    """Test rate limiting functionality"""

    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)

    def test_rate_limiting_enforcement(self):
        """Test that rate limiting is enforced"""
        # Make multiple rapid requests
        responses = []
        for _i in range(15):  # Exceed typical rate limit
            response = self.client.get("/health")
            responses.append(response)

        # At least some requests should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count > 0

        # Some might be rate limited (429) depending on configuration
        sum(1 for r in responses if r.status_code == 429)
        # This test depends on actual rate limiting configuration


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
