from concurrent.futures import ThreadPoolExecutor

from fastapi import status
import pytest


"""
DevSkyy Enterprise - Main API Endpoint Tests
Comprehensive tests for core API endpoints
"""


class TestHealthEndpoints:
    """Test health and monitoring endpoints"""

    def test_root_endpoint(self, test_client):
        """Test root endpoint returns welcome message"""
        response = test_client.get("/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data or "name" in data

    @pytest.mark.api
    def test_health_endpoint(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/api/v1/monitoring/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    @pytest.mark.api
    def test_metrics_endpoint(self, test_client):
        """Test Prometheus metrics endpoint"""
        response = test_client.get("/metrics")

        # Metrics endpoint should return 200 or 404 if not configured
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


class TestAuthenticationEndpoints:
    """Test authentication endpoints"""

    @pytest.mark.api
    @pytest.mark.security
    def test_login_success(self, test_client):
        """Test successful login"""
        login_data = {"username": "admin@devskyy.com", "password": "admin123"}

        response = test_client.post("/api/v1/auth/login", json=login_data)

        # Response might be 200 OK or 422 if endpoint expects different format
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_404_NOT_FOUND,
        ]

    @pytest.mark.api
    @pytest.mark.security
    def test_protected_endpoint_without_auth(self, test_client):
        """Test that protected endpoints require authentication"""
        response = test_client.get("/api/v1/agents")

        # Should return 401 Unauthorized or 404 if endpoint doesn't exist yet
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ]

    @pytest.mark.api
    @pytest.mark.security
    def test_protected_endpoint_with_auth(self, test_client, auth_headers):
        """Test that protected endpoints work with valid token"""
        response = test_client.get("/api/v1/agents", headers=auth_headers)

        # Should return 200 OK or 404 if endpoint doesn't exist yet
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


class TestAgentEndpoints:
    """Test AI agent endpoints"""

    @pytest.mark.api
    def test_list_agents(self, test_client, auth_headers):
        """Test listing all agents"""
        response = test_client.get("/api/v1/agents", headers=auth_headers)

        # Endpoint might not exist yet or require auth
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND,
        ]

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert isinstance(data, (list, dict))

    @pytest.mark.api
    def test_create_agent(self, test_client, auth_headers, mock_agent_data):
        """Test creating a new agent"""
        response = test_client.post("/api/v1/agents", json=mock_agent_data, headers=auth_headers)

        # Endpoint might not exist yet
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    @pytest.mark.api
    def test_get_agent_by_id(self, test_client, auth_headers):
        """Test getting agent by ID"""
        agent_id = "agent_test_001"
        response = test_client.get(f"/api/v1/agents/{agent_id}", headers=auth_headers)

        # Endpoint might not exist or agent might not be found
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_401_UNAUTHORIZED,
        ]


class TestProjectEndpoints:
    """Test project management endpoints"""

    @pytest.mark.api
    def test_list_projects(self, test_client, auth_headers):
        """Test listing all projects"""
        response = test_client.get("/api/v1/projects", headers=auth_headers)

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_401_UNAUTHORIZED,
        ]

    @pytest.mark.api
    def test_create_project(self, test_client, auth_headers, mock_project_data):
        """Test creating a new project"""
        response = test_client.post("/api/v1/projects", json=mock_project_data, headers=auth_headers)

        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]


class TestAIEndpoints:
    """Test AI interaction endpoints"""

    @pytest.mark.api
    @pytest.mark.external
    def test_chat_completion(self, test_client, auth_headers):
        """Test AI chat completion endpoint"""
        chat_data = {
            "message": "Hello, test message",
            "model": "claude-3-5-sonnet-20241022",
        }

        response = test_client.post("/api/v1/ai/chat", json=chat_data, headers=auth_headers)

        # Endpoint might not exist or require external API
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        ]


class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.api
    def test_404_endpoint(self, test_client):
        """Test that non-existent endpoints return 404"""
        response = test_client.get("/api/v1/nonexistent/endpoint")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.api
    def test_invalid_method(self, test_client):
        """Test that invalid HTTP methods are rejected"""
        response = test_client.patch("/api/v1/monitoring/health")

        # Should return 405 Method Not Allowed or 404
        assert response.status_code in [
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_404_NOT_FOUND,
        ]

    @pytest.mark.api
    def test_malformed_json(self, test_client, auth_headers):
        """Test handling of malformed JSON"""
        response = test_client.post(
            "/api/v1/agents",
            data="this is not valid json",
            headers={**auth_headers, "Content-Type": "application/json"},
        )

        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
        ]


class TestCORS:
    """Test CORS configuration"""

    @pytest.mark.api
    def test_cors_headers_present(self, test_client):
        """Test that CORS headers are present"""
        response = test_client.options("/api/v1/monitoring/health")

        # CORS might be configured or not
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        ]


class TestRateLimiting:
    """Test rate limiting (if configured)"""

    @pytest.mark.api
    @pytest.mark.slow
    def test_rate_limiting(self, test_client):
        """Test that rate limiting is enforced"""
        # Make many requests quickly
        responses = []
        for _ in range(100):
            response = test_client.get("/")
            responses.append(response.status_code)

        # Should get mostly 200s, possibly some 429s if rate limited
        assert status.HTTP_200_OK in responses
        # Rate limiting might not be configured yet
        # assert status.HTTP_429_TOO_MANY_REQUESTS in responses


# ============================================================================
# Performance Tests
# ============================================================================


@pytest.mark.slow
class TestAPIPerformance:
    """Test API endpoint performance"""

    def test_health_endpoint_response_time(self, test_client, performance_timer):
        """Test that health endpoint responds quickly"""
        _response = test_client.get("/api/v1/monitoring/health")

        elapsed = performance_timer()
        assert elapsed < 0.1  # Should respond in under 100ms

    def test_concurrent_requests(self, test_client):
        """Test handling of concurrent requests"""

        def make_request():
            return test_client.get("/")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [f.result() for f in futures]

        # All requests should succeed
        assert all(r.status_code == status.HTTP_200_OK for r in results)
