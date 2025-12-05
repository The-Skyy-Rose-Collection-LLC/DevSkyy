"""
Comprehensive Unit Tests for Orchestration API Endpoints (api/v1/orchestration.py)
Testing all orchestration endpoints to achieve 80%+ coverage

Per Truth Protocol:
- Rule #8: Test coverage ≥90%
- Rule #1: Never guess - Verify all functionality
- Rule #12: Performance SLOs - P95 < 500ms per test

Author: DevSkyy Test Automation
Version: 1.0.0
"""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import status
from fastapi.testclient import TestClient
import pytest

from main import app
from security.jwt_auth import User, UserRole, create_access_token, user_manager


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def admin_headers():
    """Create admin authentication headers"""
    token_data = {
        "user_id": "admin_orch_001",
        "email": "admin@devskyy.com",
        "username": "admin_orchestration",
        "role": UserRole.ADMIN,
    }

    test_user = User(
        user_id=token_data["user_id"],
        username=token_data["username"],
        email=token_data["email"],
        role=token_data["role"],
        active=True,
        permissions=["read", "write", "admin"],
    )
    user_manager.users[test_user.user_id] = test_user
    user_manager.email_index[test_user.email] = test_user.user_id

    access_token = create_access_token(data=token_data)
    headers = {"Authorization": f"Bearer {access_token}"}

    yield headers

    # Cleanup
    if test_user.user_id in user_manager.users:
        del user_manager.users[test_user.user_id]
    if test_user.email in user_manager.email_index:
        del user_manager.email_index[test_user.email]


@pytest.fixture
def orchestration_manager_headers():
    """Create orchestration manager authentication headers"""
    token_data = {
        "user_id": "orch_mgr_001",
        "email": "orchestration@devskyy.com",
        "username": "orch_manager",
        "role": "orchestration_manager",  # Custom role for orchestration
    }

    test_user = User(
        user_id=token_data["user_id"],
        username=token_data["username"],
        email=token_data["email"],
        role=UserRole.DEVELOPER,  # Map to Developer role
        active=True,
        permissions=["read", "write", "orchestration"],
    )
    user_manager.users[test_user.user_id] = test_user
    user_manager.email_index[test_user.email] = test_user.user_id

    access_token = create_access_token(data=token_data)
    headers = {"Authorization": f"Bearer {access_token}"}

    yield headers

    # Cleanup
    if test_user.user_id in user_manager.users:
        del user_manager.users[test_user.user_id]
    if test_user.email in user_manager.email_index:
        del user_manager.email_index[test_user.email]


@pytest.fixture
def mock_central_command():
    """Mock ClaudeCentralCommand for testing"""
    with patch("api.v1.orchestration.get_orchestration_system") as mock_get:
        mock_system = MagicMock()

        # Mock partnership types
        from enum import Enum

        class MockPartnershipType(Enum):
            CURSOR_TECHNICAL = "cursor_technical"
            GROK_BRAND = "grok_brand"
            CLAUDE_STRATEGIC = "claude_strategic"
            PERPLEXITY_RESEARCH = "perplexity_research"

        # Mock partnership performance
        mock_system._get_partnership_performance = AsyncMock(
            return_value={
                "uptime": 99.9,
                "response_time": 45.0,
                "success_rate": 98.7,
                "error_rate": 0.5,
                "requests_per_minute": 150.0,
            }
        )

        # Mock deliverable progress
        mock_system._check_deliverable_progress = AsyncMock(
            return_value={
                "code_optimization": 95.0,
                "performance_tuning": 87.5,
                "security_audit": 92.0,
            }
        )

        # Mock strategic decision engine
        mock_system.strategic_decision_engine = AsyncMock(
            return_value={
                "decision": "EXPAND_PARTNERSHIP_NETWORK",
                "rationale": "Analysis shows 23% revenue increase potential with Q1 expansion",
                "implementation_plan": [
                    {
                        "phase": 1,
                        "action": "Identify new partners",
                        "timeline": "2 weeks",
                        "resources": "2 FTEs",
                    },
                    {
                        "phase": 2,
                        "action": "Negotiate terms",
                        "timeline": "3 weeks",
                        "resources": "Legal + 1 FTE",
                    },
                ],
                "success_metrics": [
                    "Revenue growth ≥20%",
                    "Partnership satisfaction ≥4.5/5",
                    "Integration time < 4 weeks",
                ],
                "risk_mitigation": [
                    "Gradual rollout with pilot partners",
                    "Weekly performance monitoring",
                    "Rollback plan in place",
                ],
            }
        )

        # Mock partnerships configuration
        mock_system.partnerships = {
            MockPartnershipType.CURSOR_TECHNICAL: {
                "name": "Cursor Technical Partnership",
                "enabled": True,
            },
            MockPartnershipType.GROK_BRAND: {
                "name": "Grok Brand Partnership",
                "enabled": True,
            },
        }

        # Patch PartnershipType
        with patch("api.v1.orchestration.PartnershipType", MockPartnershipType):
            mock_get.return_value = mock_system
            yield mock_system


# =============================================================================
# TEST HEALTH ENDPOINT
# =============================================================================


class TestHealthEndpoint:
    """Test suite for /health endpoint"""

    @pytest.mark.asyncio
    async def test_health_check_success(self, client, admin_headers, mock_central_command):
        """Test successful health check with all partnerships healthy"""
        response = client.get("/api/v1/orchestration/health", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "status" in data
        assert "partnerships" in data
        assert "last_updated" in data

        # Verify partnerships health
        partnerships = data["partnerships"]
        assert isinstance(partnerships, dict)

        # Should have health metrics
        if partnerships and "error" not in partnerships:
            for health_data in partnerships.values():
                assert "health" in health_data
                assert "score" in health_data
                assert health_data["health"] in ["excellent", "good", "fair", "poor"]

    def test_health_check_unauthorized(self, client):
        """Test health check without authentication"""
        response = client.get("/api/v1/orchestration/health")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_health_check_insufficient_permissions(self, client, mock_central_command):
        """Test health check with non-admin user"""
        # Create a read-only user
        token_data = {
            "user_id": "readonly_001",
            "email": "readonly@devskyy.com",
            "username": "readonly",
            "role": "read_only",
        }

        test_user = User(
            user_id=token_data["user_id"],
            username=token_data["username"],
            email=token_data["email"],
            role=UserRole.READ_ONLY,
            active=True,
        )
        user_manager.users[test_user.user_id] = test_user

        access_token = create_access_token(data=token_data)
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.get("/api/v1/orchestration/health", headers=headers)

        # Should fail with 403 Forbidden for read-only users
        # The endpoint requires admin/orchestration_manager/system_admin roles
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED]

        # Cleanup
        if test_user.user_id in user_manager.users:
            del user_manager.users[test_user.user_id]


# =============================================================================
# TEST METRICS ENDPOINTS
# =============================================================================


class TestMetricsEndpoints:
    """Test suite for metrics endpoints"""

    @pytest.mark.asyncio
    async def test_get_all_metrics_success(self, client, admin_headers, mock_central_command):
        """Test successful retrieval of all partnership metrics"""
        response = client.get("/api/v1/orchestration/metrics", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert isinstance(data, list)
        # Should have metrics for each partnership
        if data:
            for metric in data:
                assert "partnership_type" in metric
                assert "metrics" in metric
                assert "timestamp" in metric
                assert isinstance(metric["metrics"], dict)

    @pytest.mark.asyncio
    async def test_get_partnership_metrics_success(self, client, admin_headers, mock_central_command):
        """Test successful retrieval of specific partnership metrics"""
        partnership_type = "cursor_technical"
        response = client.get(
            f"/api/v1/orchestration/metrics/{partnership_type}",
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "partnership_type" in data
        assert data["partnership_type"] == partnership_type
        assert "metrics" in data
        assert "timestamp" in data

        # Verify metrics structure
        metrics = data["metrics"]
        assert isinstance(metrics, dict)

    def test_get_partnership_metrics_invalid_type(self, client, admin_headers, mock_central_command):
        """Test getting metrics for invalid partnership type"""
        response = client.get(
            "/api/v1/orchestration/metrics/invalid_partnership",
            headers=admin_headers,
        )

        # Should return 400 Bad Request for invalid partnership type
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]

    def test_get_metrics_unauthorized(self, client):
        """Test metrics endpoint without authentication"""
        response = client.get("/api/v1/orchestration/metrics")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================================================================
# TEST STRATEGIC DECISION ENGINE
# =============================================================================


class TestStrategicDecisionEngine:
    """Test suite for strategic decision engine endpoint"""

    @pytest.mark.asyncio
    async def test_make_strategic_decision_success(self, client, admin_headers, mock_central_command):
        """Test successful strategic decision making"""
        decision_context = {
            "business_goal": "increase_revenue",
            "timeframe": "Q1_2025",
            "budget": 50000,
            "current_performance": {"revenue": 1000000, "growth_rate": 0.15},
        }

        response = client.post(
            "/api/v1/orchestration/decisions",
            json={"context": decision_context},
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "decision" in data
        assert "rationale" in data
        assert "implementation_plan" in data
        assert "success_metrics" in data
        assert "risk_mitigation" in data

        # Verify types
        assert isinstance(data["decision"], str)
        assert isinstance(data["rationale"], str)
        assert isinstance(data["implementation_plan"], list)
        assert isinstance(data["success_metrics"], list)
        assert isinstance(data["risk_mitigation"], list)

    def test_make_strategic_decision_empty_context(self, client, admin_headers, mock_central_command):
        """Test strategic decision with empty context"""
        response = client.post(
            "/api/v1/orchestration/decisions",
            json={"context": {}},
            headers=admin_headers,
        )

        # Should fail validation
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

    def test_make_strategic_decision_unauthorized(self, client):
        """Test decision endpoint without authentication"""
        response = client.post(
            "/api/v1/orchestration/decisions",
            json={"context": {"goal": "test"}},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================================================================
# TEST PARTNERSHIP MANAGEMENT
# =============================================================================


class TestPartnershipManagement:
    """Test suite for partnership management endpoints"""

    @pytest.mark.asyncio
    async def test_get_all_partnerships_success(self, client, admin_headers, mock_central_command):
        """Test successful retrieval of all partnerships"""
        response = client.get("/api/v1/orchestration/partnerships", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert isinstance(data, list)
        # Should have partnership status entries
        if data:
            for partnership in data:
                assert "id" in partnership
                assert "name" in partnership
                assert "health" in partnership
                assert "progress" in partnership
                assert "deliverables" in partnership

                # Verify types
                assert isinstance(partnership["progress"], (int, float))
                assert isinstance(partnership["deliverables"], list)

    @pytest.mark.asyncio
    async def test_get_partnership_status_success(self, client, admin_headers, mock_central_command):
        """Test successful retrieval of specific partnership status"""
        partnership_id = "cursor_technical"
        response = client.get(
            f"/api/v1/orchestration/partnerships/{partnership_id}/status",
            headers=admin_headers,
        )

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "id" in data
            assert data["id"] == partnership_id
            assert "health" in data
            assert "progress" in data

    def test_get_partnership_status_not_found(self, client, admin_headers, mock_central_command):
        """Test getting status for non-existent partnership"""
        response = client.get(
            "/api/v1/orchestration/partnerships/nonexistent_partnership/status",
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# TEST SYSTEM INFORMATION
# =============================================================================


class TestSystemInformation:
    """Test suite for system information endpoints"""

    @pytest.mark.asyncio
    async def test_get_system_info_success(self, client, admin_headers, mock_central_command):
        """Test successful system info retrieval"""
        response = client.get("/api/v1/orchestration/info", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "system" in data
        assert "version" in data
        assert "status" in data
        assert "partnerships" in data
        assert "features" in data
        assert "api_version" in data
        assert "statistics" in data

        # Verify types
        assert isinstance(data["features"], list)
        assert isinstance(data["statistics"], dict)

    @pytest.mark.asyncio
    async def test_get_system_status_success(self, client, admin_headers, mock_central_command):
        """Test successful system status retrieval"""
        response = client.get("/api/v1/orchestration/status", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "overall_status" in data
        assert "components" in data
        assert "resource_usage" in data
        assert "recent_activity" in data

        # Verify types
        assert isinstance(data["components"], dict)
        assert isinstance(data["resource_usage"], dict)
        assert isinstance(data["recent_activity"], list)


# =============================================================================
# TEST CONFIGURATION MANAGEMENT
# =============================================================================


class TestConfigurationManagement:
    """Test suite for configuration management endpoint"""

    @pytest.mark.asyncio
    async def test_get_system_configuration_admin_success(self, client, admin_headers, mock_central_command):
        """Test successful config retrieval by admin"""
        response = client.get("/api/v1/orchestration/config", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "configuration" in data
        assert "last_updated" in data
        assert "version" in data

        config = data["configuration"]
        assert "api_settings" in config
        assert "security_settings" in config
        assert "orchestration_settings" in config
        assert "partnership_settings" in config

    def test_get_system_configuration_non_admin_forbidden(
        self, client, orchestration_manager_headers, mock_central_command
    ):
        """Test config retrieval by non-admin user (should fail)"""
        response = client.get("/api/v1/orchestration/config", headers=orchestration_manager_headers)

        # Should fail with 403 Forbidden for non-admin users
        # The endpoint explicitly requires admin role
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED]


# =============================================================================
# TEST DEPLOYMENT READINESS
# =============================================================================


class TestDeploymentReadiness:
    """Test suite for deployment readiness endpoint"""

    @pytest.mark.asyncio
    async def test_check_deployment_readiness_success(self, client, admin_headers, mock_central_command):
        """Test successful deployment readiness check"""
        response = client.get("/api/v1/orchestration/deployment/readiness", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "overall_status" in data
        assert "readiness_score" in data
        assert "checks" in data
        assert "summary" in data
        assert "recommendations" in data

        # Verify types
        assert isinstance(data["readiness_score"], (int, float))
        assert isinstance(data["checks"], dict)
        assert isinstance(data["summary"], dict)
        assert isinstance(data["recommendations"], list)

        # Verify summary structure
        summary = data["summary"]
        assert "total_checks" in summary
        assert "passed" in summary
        assert "warnings" in summary
        assert "failed" in summary


# =============================================================================
# TEST API DOCUMENTATION
# =============================================================================


class TestAPIDocumentation:
    """Test suite for API documentation endpoint"""

    @pytest.mark.asyncio
    async def test_get_api_documentation_success(self, client, admin_headers, mock_central_command):
        """Test successful API documentation retrieval"""
        response = client.get("/api/v1/orchestration/docs/endpoints", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "api_version" in data
        assert "base_url" in data
        assert "authentication" in data
        assert "rate_limiting" in data
        assert "error_handling" in data
        assert "endpoints" in data

        # Verify endpoints documentation
        endpoints = data["endpoints"]
        assert isinstance(endpoints, dict)

        # Should have documentation for key endpoints
        expected_endpoints = [
            "health",
            "metrics",
            "decisions",
            "partnerships",
            "status",
            "config",
            "deployment_readiness",
        ]

        for endpoint_key in expected_endpoints:
            if endpoint_key in endpoints:
                endpoint_doc = endpoints[endpoint_key]
                assert "method" in endpoint_doc
                assert "path" in endpoint_doc
                assert "description" in endpoint_doc


# =============================================================================
# TEST PERFORMANCE
# =============================================================================


class TestOrchestrationPerformance:
    """Test suite for performance requirements (Rule #12: P95 < 500ms)"""

    @pytest.mark.asyncio
    async def test_health_endpoint_performance(self, client, admin_headers, mock_central_command):
        """Test health endpoint response time < 500ms"""
        import time

        start_time = time.time()
        response = client.get("/api/v1/orchestration/health", headers=admin_headers)
        elapsed_ms = (time.time() - start_time) * 1000

        assert response.status_code == status.HTTP_200_OK
        # Per Rule #12: P95 < 500ms for API endpoints
        # Individual test should be much faster
        assert elapsed_ms < 500, f"Health endpoint took {elapsed_ms:.2f}ms (should be < 500ms)"

    @pytest.mark.asyncio
    async def test_metrics_endpoint_performance(self, client, admin_headers, mock_central_command):
        """Test metrics endpoint response time < 500ms"""
        import time

        start_time = time.time()
        response = client.get("/api/v1/orchestration/metrics", headers=admin_headers)
        elapsed_ms = (time.time() - start_time) * 1000

        assert response.status_code == status.HTTP_200_OK
        assert elapsed_ms < 500, f"Metrics endpoint took {elapsed_ms:.2f}ms (should be < 500ms)"


# =============================================================================
# TEST ERROR HANDLING
# =============================================================================


class TestOrchestrationErrorHandling:
    """Test suite for error handling per Rule #10: No-Skip Rule"""

    def test_invalid_json_payload(self, client, admin_headers):
        """Test handling of invalid JSON payload"""
        response = client.post(
            "/api/v1/orchestration/decisions",
            data="invalid json",  # Invalid JSON
            headers={**admin_headers, "Content-Type": "application/json"},
        )

        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    def test_missing_required_fields(self, client, admin_headers, mock_central_command):
        """Test handling of missing required fields"""
        # Missing 'context' field
        response = client.post(
            "/api/v1/orchestration/decisions",
            json={},
            headers=admin_headers,
        )

        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
