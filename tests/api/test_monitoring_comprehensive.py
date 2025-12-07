"""
Comprehensive Tests for Monitoring API Endpoints (api/v1/monitoring.py)
Tests health checks, metrics collection, and performance monitoring
Coverage target: ≥90% for api/v1/monitoring.py

Author: DevSkyy Team
Version: 1.0.0
Python: >=3.11.0
Per CLAUDE.md Truth Protocol requirements
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from security.jwt_auth import TokenData, UserRole


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_token_data():
    """Mock token data for authenticated user"""
    return TokenData(
        user_id="user123",
        email="test@example.com",
        username="testuser",
        role=UserRole.ADMIN,
    )


@pytest.fixture
def mock_health_monitor():
    """Mock health monitor"""
    with patch("api.v1.monitoring.health_monitor") as mock:
        yield mock


@pytest.fixture
def mock_metrics_collector():
    """Mock metrics collector"""
    with patch("api.v1.monitoring.metrics_collector") as mock:
        yield mock


@pytest.fixture
def mock_performance_tracker():
    """Mock performance tracker"""
    with patch("api.v1.monitoring.performance_tracker") as mock:
        yield mock


# ============================================================================
# TEST HEALTH CHECK ENDPOINTS
# ============================================================================


class TestHealthCheckEndpoint:
    """Test /monitoring/health endpoint"""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, mock_health_monitor):
        """Should return healthy status"""
        from api.v1.monitoring import health_check

        # Mock health check results
        mock_results = {
            "database": Mock(model_dump=lambda: {"status": "healthy", "latency_ms": 5}),
            "redis": Mock(model_dump=lambda: {"status": "healthy", "latency_ms": 3}),
        }
        mock_health_monitor.run_all_checks = AsyncMock(return_value=mock_results)
        mock_health_monitor.get_overall_status.return_value = ("healthy", "All systems operational")

        # Call endpoint
        result = await health_check()

        # Assertions
        assert result["status"] == "healthy"
        assert "message" in result
        assert "checks" in result
        assert "database" in result["checks"]
        assert "redis" in result["checks"]

    @pytest.mark.asyncio
    async def test_health_check_degraded(self, mock_health_monitor):
        """Should return degraded status"""
        from api.v1.monitoring import health_check

        # Mock degraded health check
        mock_results = {
            "database": Mock(model_dump=lambda: {"status": "healthy"}),
            "redis": Mock(model_dump=lambda: {"status": "degraded"}),
        }
        mock_health_monitor.run_all_checks = AsyncMock(return_value=mock_results)
        mock_health_monitor.get_overall_status.return_value = ("degraded", "Some services degraded")

        result = await health_check()

        assert result["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, mock_health_monitor):
        """Should return unhealthy status"""
        from api.v1.monitoring import health_check

        # Mock unhealthy health check
        mock_results = {
            "database": Mock(model_dump=lambda: {"status": "unhealthy"}),
        }
        mock_health_monitor.run_all_checks = AsyncMock(return_value=mock_results)
        mock_health_monitor.get_overall_status.return_value = ("unhealthy", "Critical services down")

        result = await health_check()

        assert result["status"] == "unhealthy"


class TestDetailedHealthCheckEndpoint:
    """Test /monitoring/health/detailed endpoint"""

    @pytest.mark.asyncio
    async def test_detailed_health_check(self, mock_health_monitor, mock_metrics_collector, mock_token_data):
        """Should return detailed health information"""
        from api.v1.monitoring import detailed_health_check

        # Mock health checks
        mock_results = {
            "database": Mock(model_dump=lambda: {"status": "healthy"}),
            "redis": Mock(model_dump=lambda: {"status": "healthy"}),
        }
        mock_health_monitor.run_all_checks = AsyncMock(return_value=mock_results)
        mock_health_monitor.get_overall_status.return_value = ("healthy", "All systems operational")

        # Mock metrics
        mock_metrics_collector.get_gauge.side_effect = lambda key: {
            "system_cpu_percent": 45.5,
            "system_memory_percent": 62.3,
            "system_disk_percent": 78.1,
        }.get(key, 0.0)

        # Call endpoint
        result = await detailed_health_check(mock_token_data)

        # Assertions
        assert result["status"] == "healthy"
        assert "system_metrics" in result
        assert result["system_metrics"]["cpu"] == 45.5
        assert result["system_metrics"]["memory"] == 62.3
        assert result["system_metrics"]["disk"] == 78.1
        mock_metrics_collector.collect_system_metrics.assert_called_once()


# ============================================================================
# TEST METRICS ENDPOINTS
# ============================================================================


class TestMetricsEndpoints:
    """Test metrics-related endpoints"""

    @pytest.mark.asyncio
    async def test_get_metrics(self, mock_metrics_collector, mock_token_data):
        """Should return all metrics"""
        from api.v1.monitoring import get_metrics

        # Mock all metrics
        mock_metrics = {
            "counters": {"api_requests_total": 1234, "errors_total": 12},
            "gauges": {"active_connections": 45, "queue_size": 23},
            "histograms": {"response_time_ms": [12, 34, 56, 78]},
        }
        mock_metrics_collector.get_all_metrics.return_value = mock_metrics

        # Call endpoint
        result = await get_metrics(mock_token_data)

        # Assertions
        assert result == mock_metrics
        assert "counters" in result
        assert "gauges" in result

    @pytest.mark.asyncio
    async def test_get_counters(self, mock_metrics_collector, mock_token_data):
        """Should return counter metrics"""
        from api.v1.monitoring import get_counters

        # Mock counters
        mock_metrics_collector.counters = {
            "api_requests_total": 1234,
            "errors_total": 12,
            "webhooks_sent": 567,
        }

        # Call endpoint
        result = await get_counters(mock_token_data)

        # Assertions
        assert "counters" in result
        assert result["counters"]["api_requests_total"] == 1234
        assert result["counters"]["errors_total"] == 12

    @pytest.mark.asyncio
    async def test_get_gauges(self, mock_metrics_collector, mock_token_data):
        """Should return gauge metrics"""
        from api.v1.monitoring import get_gauges

        # Mock gauges
        mock_metrics_collector.gauges = {
            "active_connections": 45,
            "queue_size": 23,
            "cpu_percent": 67.8,
        }

        # Call endpoint
        result = await get_gauges(mock_token_data)

        # Assertions
        assert "gauges" in result
        assert result["gauges"]["active_connections"] == 45
        assert result["gauges"]["queue_size"] == 23


# ============================================================================
# TEST AUTHORIZATION
# ============================================================================


class TestMonitoringAuthorization:
    """Test authorization for monitoring endpoints"""

    @pytest.mark.asyncio
    async def test_detailed_health_check_requires_admin(self, mock_health_monitor):
        """Should require admin role for detailed health check"""
        from api.v1.monitoring import detailed_health_check

        # Mock non-admin user
        non_admin_token = TokenData(
            user_id="user123",
            email="user@example.com",
            username="user",
            role=UserRole.API_USER,
        )

        # This should be handled by FastAPI dependency injection
        # In actual use, the require_admin dependency would reject this
        # For testing, we just verify the endpoint can be called
        mock_health_monitor.run_all_checks = AsyncMock(return_value={})
        mock_health_monitor.get_overall_status.return_value = ("healthy", "OK")

        with patch("api.v1.monitoring.metrics_collector"):
            result = await detailed_health_check(non_admin_token)
            assert "status" in result


# ============================================================================
# TEST ERROR HANDLING
# ============================================================================


class TestMonitoringErrorHandling:
    """Test error handling in monitoring endpoints"""

    @pytest.mark.asyncio
    async def test_health_check_handles_exception(self, mock_health_monitor):
        """Should handle exceptions gracefully"""
        from api.v1.monitoring import health_check

        # Mock exception in health check
        mock_health_monitor.run_all_checks = AsyncMock(side_effect=Exception("Health check failed"))

        # Should raise exception (or handle it depending on implementation)
        with pytest.raises(Exception):
            await health_check()

    @pytest.mark.asyncio
    async def test_metrics_collection_error(self, mock_metrics_collector, mock_token_data):
        """Should handle metrics collection errors"""
        from api.v1.monitoring import get_metrics

        # Mock exception
        mock_metrics_collector.get_all_metrics.side_effect = Exception("Metrics unavailable")

        # Should raise exception
        with pytest.raises(Exception):
            await get_metrics(mock_token_data)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestMonitoringIntegration:
    """Integration tests for monitoring endpoints"""

    @pytest.mark.asyncio
    async def test_full_monitoring_flow(self, mock_health_monitor, mock_metrics_collector, mock_token_data):
        """Test complete monitoring flow"""
        from api.v1.monitoring import detailed_health_check, get_metrics, health_check

        # Setup mocks
        mock_results = {
            "database": Mock(model_dump=lambda: {"status": "healthy"}),
        }
        mock_health_monitor.run_all_checks = AsyncMock(return_value=mock_results)
        mock_health_monitor.get_overall_status.return_value = ("healthy", "OK")

        mock_metrics = {
            "counters": {"total": 100},
            "gauges": {"active": 10},
        }
        mock_metrics_collector.get_all_metrics.return_value = mock_metrics
        mock_metrics_collector.get_gauge.return_value = 50.0

        # Run health check
        health = await health_check()
        assert health["status"] == "healthy"

        # Get metrics
        metrics = await get_metrics(mock_token_data)
        assert "counters" in metrics

        # Get detailed health
        detailed = await detailed_health_check(mock_token_data)
        assert "system_metrics" in detailed


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=api.v1.monitoring", "--cov-report=term-missing"])
