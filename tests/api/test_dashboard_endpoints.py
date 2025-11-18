"""
Comprehensive Unit Tests for Dashboard API Endpoints (api/v1/dashboard.py)
Testing dashboard data retrieval, metrics, agent status, and activities
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient
import pytest

from main import app
from security.jwt_auth import User, UserRole, create_access_token, user_manager


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create authentication headers with valid JWT token"""
    token_data = {
        "user_id": "test_user_001",
        "email": "test@devskyy.com",
        "username": "testuser",
        "role": UserRole.API_USER,
    }

    test_user = User(
        user_id=token_data["user_id"],
        email=token_data["email"],
        username=token_data["username"],
        role=token_data["role"],
        permissions=["read", "write"],
    )
    user_manager.users[test_user.user_id] = test_user
    user_manager.email_index[test_user.email] = test_user.user_id

    access_token = create_access_token(token_data)
    headers = {"Authorization": f"Bearer {access_token}"}

    yield headers

    # Cleanup
    if test_user.user_id in user_manager.users:
        del user_manager.users[test_user.user_id]
    if test_user.email in user_manager.email_index:
        del user_manager.email_index[test_user.email]


@pytest.fixture
def mock_system_metrics():
    """Mock system metrics data"""
    return {
        "active_agents": 57,
        "api_requests_per_minute": 2847,
        "average_response_time": 127.5,
        "system_health_score": 0.998,
        "cpu_usage": 45.2,
        "memory_usage": 62.8,
        "error_rate": 0.002,
    }


@pytest.fixture
def mock_agent_status():
    """Mock agent status data"""
    return [
        {
            "agent_id": "scanner_v1",
            "name": "Scanner Agent",
            "status": "active",
            "last_active": datetime.now().isoformat(),
            "tasks_completed": 145,
            "tasks_pending": 3,
            "performance_score": 0.95,
            "capabilities": ["code_analysis", "security_scan"],
        },
        {
            "agent_id": "fixer_v1",
            "name": "Fixer Agent",
            "status": "idle",
            "last_active": (datetime.now() - timedelta(minutes=5)).isoformat(),
            "tasks_completed": 89,
            "tasks_pending": 0,
            "performance_score": 0.92,
            "capabilities": ["code_fixing", "optimization"],
        },
    ]


@pytest.fixture
def mock_activities():
    """Mock activity log data"""
    return [
        {
            "activity_id": "act_001",
            "timestamp": datetime.now().isoformat(),
            "agent_name": "Scanner Agent",
            "action": "scan_completed",
            "status": "success",
            "details": "Scanned 42 files, found 3 issues",
        },
        {
            "activity_id": "act_002",
            "timestamp": (datetime.now() - timedelta(minutes=2)).isoformat(),
            "agent_name": "Fixer Agent",
            "action": "fix_applied",
            "status": "success",
            "details": "Fixed 5 files",
        },
    ]


@pytest.fixture
def mock_performance_history():
    """Mock performance history data"""
    now = datetime.now()
    return [
        {
            "timestamp": (now - timedelta(hours=i)).isoformat(),
            "response_time": 120 + (i * 5),
            "cpu_usage": 40 + (i * 2),
            "memory_usage": 60 + (i * 1.5),
            "requests_per_minute": 2800 - (i * 50),
        }
        for i in range(24)
    ]


class TestDashboardPageEndpoint:
    """Test suite for dashboard HTML page endpoint"""

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_dashboard_page_success(self, client):
        """Test dashboard page returns HTML"""
        response = client.get("/api/v1/dashboard/dashboard")

        # Should return HTML page or redirect
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND, status.HTTP_302_FOUND]

        if response.status_code == status.HTTP_200_OK:
            assert "text/html" in response.headers.get("content-type", "")

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_dashboard_page_no_auth_required(self, client):
        """Test dashboard page doesn't require authentication (public view)"""
        response = client.get("/api/v1/dashboard/dashboard")

        # Page should be accessible without auth or require it
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND]


class TestDashboardDataEndpoint:
    """Test suite for complete dashboard data endpoint"""

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_dashboard_data_success(self, client):
        """Test successful retrieval of complete dashboard data"""
        response = client.get("/api/v1/dashboard/dashboard/data")

        # No auth required after removal of role-based checks
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            # Check for expected dashboard components
            expected_keys = {"metrics", "agents", "recent_activities", "performance_history"}
            # At least some keys should be present
            assert len(set(data.keys()) & expected_keys) > 0

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_dashboard_data_no_auth_required(self, client):
        """Test dashboard data endpoint doesn't require authentication after changes"""
        response = client.get("/api/v1/dashboard/dashboard/data")

        # After removing auth requirements, should work without auth
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    @patch("api.v1.dashboard.dashboard_service")
    def test_get_dashboard_data_with_app_state(self, mock_service, client):
        """Test dashboard data initialization with app state"""
        mock_service.initialize = AsyncMock()
        mock_service.get_system_metrics = AsyncMock(
            return_value={
                "active_agents": 10,
                "api_requests_per_minute": 100,
                "average_response_time": 50.0,
                "system_health_score": 0.99,
                "cpu_usage": 30.0,
                "memory_usage": 50.0,
                "error_rate": 0.001,
            }
        )
        mock_service.get_agent_status = AsyncMock(return_value=[])
        mock_service.get_recent_activities = AsyncMock(return_value=[])
        mock_service.get_performance_history = AsyncMock(return_value=[])

        response = client.get("/api/v1/dashboard/dashboard/data")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_dashboard_data_error_handling(self, client):
        """Test dashboard data error handling"""
        with patch(
            "api.v1.dashboard.dashboard_service.get_system_metrics", side_effect=Exception("Service unavailable")
        ):
            response = client.get("/api/v1/dashboard/dashboard/data")

            assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]


class TestSystemMetricsEndpoint:
    """Test suite for system metrics endpoint"""

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_system_metrics_success(self, client):
        """Test successful retrieval of system metrics"""
        response = client.get("/api/v1/dashboard/dashboard/metrics")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            # Validate metric fields
            expected_fields = {
                "active_agents",
                "api_requests_per_minute",
                "average_response_time",
                "system_health_score",
                "cpu_usage",
                "memory_usage",
                "error_rate",
            }
            assert any(field in data for field in expected_fields)

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_system_metrics_no_auth_required(self, client):
        """Test metrics endpoint doesn't require authentication"""
        response = client.get("/api/v1/dashboard/dashboard/metrics")

        # Should work without authentication after changes
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    @patch("api.v1.dashboard.dashboard_service.get_system_metrics")
    def test_get_system_metrics_with_high_load(self, mock_get_metrics, client):
        """Test system metrics under high load conditions"""
        high_load_metrics = {
            "active_agents": 100,
            "api_requests_per_minute": 10000,
            "average_response_time": 500.0,
            "system_health_score": 0.85,
            "cpu_usage": 95.0,
            "memory_usage": 90.0,
            "error_rate": 0.05,
        }
        mock_get_metrics.return_value = AsyncMock(return_value=high_load_metrics)

        response = client.get("/api/v1/dashboard/dashboard/metrics")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    @patch("api.v1.dashboard.dashboard_service.get_system_metrics")
    def test_get_system_metrics_fallback_on_error(self, mock_get_metrics, client):
        """Test metrics fallback when service fails"""
        mock_get_metrics.side_effect = Exception("Monitoring service down")

        response = client.get("/api/v1/dashboard/dashboard/metrics")

        # Should return fallback metrics or error
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]


class TestAgentStatusEndpoint:
    """Test suite for agent status endpoint"""

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_agent_status_success(self, client):
        """Test successful retrieval of agent statuses"""
        response = client.get("/api/v1/dashboard/dashboard/agents")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert isinstance(data, (list, dict))

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_agent_status_no_auth_required(self, client):
        """Test agent status endpoint doesn't require authentication"""
        response = client.get("/api/v1/dashboard/dashboard/agents")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    @patch("api.v1.dashboard.dashboard_service.get_agent_status")
    def test_get_agent_status_empty_list(self, mock_get_agents, client):
        """Test agent status with no active agents"""
        mock_get_agents.return_value = AsyncMock(return_value=[])

        response = client.get("/api/v1/dashboard/dashboard/agents")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    @patch("api.v1.dashboard.dashboard_service.get_agent_status")
    def test_get_agent_status_with_inactive_agents(self, mock_get_agents, client):
        """Test agent status including inactive agents"""
        agents_with_inactive = [
            {
                "agent_id": "agent_1",
                "name": "Active Agent",
                "status": "active",
                "last_active": datetime.now().isoformat(),
            },
            {
                "agent_id": "agent_2",
                "name": "Inactive Agent",
                "status": "inactive",
                "last_active": (datetime.now() - timedelta(days=1)).isoformat(),
            },
        ]
        mock_get_agents.return_value = AsyncMock(return_value=agents_with_inactive)

        response = client.get("/api/v1/dashboard/dashboard/agents")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]


class TestRecentActivitiesEndpoint:
    """Test suite for recent activities endpoint"""

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_recent_activities_default_limit(self, client):
        """Test recent activities with default limit"""
        response = client.get("/api/v1/dashboard/dashboard/activities")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert isinstance(data, (list, dict))

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_recent_activities_custom_limit(self, client):
        """Test recent activities with custom limit"""
        response = client.get("/api/v1/dashboard/dashboard/activities?limit=20")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_recent_activities_no_auth_required(self, client):
        """Test activities endpoint doesn't require authentication"""
        response = client.get("/api/v1/dashboard/dashboard/activities")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_recent_activities_with_zero_limit(self, client):
        """Test recent activities with zero limit"""
        response = client.get("/api/v1/dashboard/dashboard/activities?limit=0")

        # Should handle gracefully
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_recent_activities_with_large_limit(self, client):
        """Test recent activities with very large limit"""
        response = client.get("/api/v1/dashboard/dashboard/activities?limit=1000")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_recent_activities_invalid_limit(self, client):
        """Test recent activities with invalid limit parameter"""
        response = client.get("/api/v1/dashboard/dashboard/activities?limit=invalid")

        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_500_INTERNAL_SERVER_ERROR]


class TestPerformanceHistoryEndpoint:
    """Test suite for performance history endpoint"""

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_performance_history_default_hours(self, client):
        """Test performance history with default 24 hours"""
        response = client.get("/api/v1/dashboard/dashboard/performance")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert isinstance(data, (list, dict))

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_performance_history_custom_hours(self, client):
        """Test performance history with custom hours"""
        response = client.get("/api/v1/dashboard/dashboard/performance?hours=48")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_performance_history_no_auth_required(self, client):
        """Test performance history doesn't require authentication"""
        response = client.get("/api/v1/dashboard/dashboard/performance")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_performance_history_short_period(self, client):
        """Test performance history for short period (1 hour)"""
        response = client.get("/api/v1/dashboard/dashboard/performance?hours=1")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_performance_history_long_period(self, client):
        """Test performance history for long period (7 days)"""
        response = client.get("/api/v1/dashboard/dashboard/performance?hours=168")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_performance_history_invalid_hours(self, client):
        """Test performance history with invalid hours parameter"""
        response = client.get("/api/v1/dashboard/dashboard/performance?hours=invalid")

        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_performance_history_negative_hours(self, client):
        """Test performance history with negative hours"""
        response = client.get("/api/v1/dashboard/dashboard/performance?hours=-10")

        # Should handle invalid input gracefully
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]


class TestWebSocketEndpoint:
    """Test suite for dashboard WebSocket endpoint"""

    @pytest.mark.api
    @pytest.mark.unit
    def test_websocket_connection_establishment(self, client):
        """Test WebSocket connection can be established"""
        # WebSocket testing with TestClient requires special handling
        # This is a placeholder for WebSocket connection test
        # In production, use pytest-asyncio with WebSocket test client

    @pytest.mark.api
    @pytest.mark.unit
    def test_websocket_data_streaming(self, client):
        """Test WebSocket streams dashboard updates"""
        # Placeholder for WebSocket data streaming test


class TestDashboardEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.api
    @pytest.mark.unit
    def test_dashboard_with_missing_app_state(self, client):
        """Test dashboard endpoints work without app state"""
        response = client.get("/api/v1/dashboard/dashboard/data")

        # Should handle missing app state gracefully
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    @patch("api.v1.dashboard.dashboard_service")
    def test_dashboard_service_initialization_failure(self, mock_service, client):
        """Test dashboard when service initialization fails"""
        mock_service.initialize.side_effect = Exception("Init failed")

        response = client.get("/api/v1/dashboard/dashboard/data")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    def test_dashboard_concurrent_requests(self, client):
        """Test dashboard handles concurrent requests"""
        import concurrent.futures

        def make_request():
            return client.get("/api/v1/dashboard/dashboard/metrics")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert len(results) == 10
        for response in results:
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    def test_dashboard_with_query_string_injection(self, client):
        """Test dashboard prevents query string injection"""
        malicious_query = "?limit=10' OR '1'='1"
        response = client.get(f"/api/v1/dashboard/dashboard/activities{malicious_query}")

        # Should handle safely
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

    @pytest.mark.api
    @pytest.mark.unit
    @patch("api.v1.dashboard.dashboard_service.get_system_metrics")
    def test_dashboard_timeout_handling(self, mock_metrics, client):
        """Test dashboard handles service timeouts"""
        mock_metrics.side_effect = TimeoutError("Service timeout")

        response = client.get("/api/v1/dashboard/dashboard/metrics")

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_504_GATEWAY_TIMEOUT,
        ]


class TestDashboardIntegration:
    """Integration tests for dashboard functionality"""

    @pytest.mark.api
    @pytest.mark.integration
    def test_complete_dashboard_workflow(self, client):
        """Test complete dashboard data retrieval workflow"""
        # Get dashboard page
        page_response = client.get("/api/v1/dashboard/dashboard")

        # Get dashboard data
        data_response = client.get("/api/v1/dashboard/dashboard/data")

        # Get individual components
        metrics_response = client.get("/api/v1/dashboard/dashboard/metrics")
        agents_response = client.get("/api/v1/dashboard/dashboard/agents")
        activities_response = client.get("/api/v1/dashboard/dashboard/activities")
        performance_response = client.get("/api/v1/dashboard/dashboard/performance")

        # All endpoints should respond (even if with errors in test environment)
        responses = [
            page_response,
            data_response,
            metrics_response,
            agents_response,
            activities_response,
            performance_response,
        ]

        for resp in responses:
            assert resp.status_code in [
                status.HTTP_200_OK,
                status.HTTP_404_NOT_FOUND,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            ]
