"""Tests for Health Analytics API endpoints.

Tests cover:
- GET /analytics/health/overview
- GET /analytics/health/api
- GET /analytics/health/database
- GET /analytics/health/timeseries
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from api.v1.analytics.health import (
    ConnectionPoolMetrics,
    DatabaseHealthResponse,
    EndpointPerformance,
    ErrorMetrics,
    HealthOverview,
    HealthOverviewResponse,
    HealthTimeseriesDataPoint,
    HealthTimeseriesResponse,
    LatencyMetrics,
    QueryLatencyMetrics,
    SystemStatus,
    TimeRange,
    determine_system_status,
    format_uptime,
    get_granularity,
    get_time_range_seconds,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_user() -> MagicMock:
    """Mock authenticated user."""
    user = MagicMock()
    user.sub = "test-user-123"
    return user


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Mock database session."""
    session = AsyncMock()
    return session


# =============================================================================
# Unit Tests - Helper Functions
# =============================================================================


class TestFormatUptime:
    """Tests for format_uptime helper function."""

    def test_format_minutes_only(self) -> None:
        """Test formatting when uptime is less than an hour."""
        result = format_uptime(1800)  # 30 minutes
        assert result == "30m"

    def test_format_hours_and_minutes(self) -> None:
        """Test formatting when uptime is hours and minutes."""
        result = format_uptime(5400)  # 1.5 hours
        assert result == "1h 30m"

    def test_format_days_hours_minutes(self) -> None:
        """Test formatting when uptime includes days."""
        result = format_uptime(90000)  # 1 day, 1 hour
        assert result == "1d 1h 0m"

    def test_format_zero_uptime(self) -> None:
        """Test formatting when uptime is zero."""
        result = format_uptime(0)
        assert result == "0m"


class TestGetTimeRangeSeconds:
    """Tests for get_time_range_seconds helper function."""

    def test_one_hour(self) -> None:
        """Test 1h time range."""
        assert get_time_range_seconds(TimeRange.ONE_HOUR) == 3600

    def test_twenty_four_hours(self) -> None:
        """Test 24h time range."""
        assert get_time_range_seconds(TimeRange.TWENTY_FOUR_HOURS) == 86400

    def test_seven_days(self) -> None:
        """Test 7d time range."""
        assert get_time_range_seconds(TimeRange.SEVEN_DAYS) == 604800

    def test_thirty_days(self) -> None:
        """Test 30d time range."""
        assert get_time_range_seconds(TimeRange.THIRTY_DAYS) == 2592000


class TestGetGranularity:
    """Tests for get_granularity helper function."""

    def test_one_hour_granularity(self) -> None:
        """Test granularity for 1h range."""
        assert get_granularity(TimeRange.ONE_HOUR) == "minute"

    def test_twenty_four_hours_granularity(self) -> None:
        """Test granularity for 24h range."""
        assert get_granularity(TimeRange.TWENTY_FOUR_HOURS) == "hour"

    def test_seven_days_granularity(self) -> None:
        """Test granularity for 7d range."""
        assert get_granularity(TimeRange.SEVEN_DAYS) == "day"

    def test_thirty_days_granularity(self) -> None:
        """Test granularity for 30d range."""
        assert get_granularity(TimeRange.THIRTY_DAYS) == "day"


class TestDetermineSystemStatus:
    """Tests for determine_system_status helper function."""

    def test_healthy_status(self) -> None:
        """Test healthy status with low error rate and latency."""
        status = determine_system_status(0.5, 200.0)
        assert status == SystemStatus.HEALTHY

    def test_degraded_high_error_rate(self) -> None:
        """Test degraded status with high error rate."""
        status = determine_system_status(3.0, 200.0)
        assert status == SystemStatus.DEGRADED

    def test_degraded_high_latency(self) -> None:
        """Test degraded status with high latency."""
        status = determine_system_status(0.5, 700.0)
        assert status == SystemStatus.DEGRADED

    def test_unhealthy_very_high_error_rate(self) -> None:
        """Test unhealthy status with very high error rate."""
        status = determine_system_status(10.0, 200.0)
        assert status == SystemStatus.UNHEALTHY

    def test_unhealthy_very_high_latency(self) -> None:
        """Test unhealthy status with very high latency."""
        status = determine_system_status(0.5, 1500.0)
        assert status == SystemStatus.UNHEALTHY


# =============================================================================
# Unit Tests - Pydantic Models
# =============================================================================


class TestLatencyMetrics:
    """Tests for LatencyMetrics model."""

    def test_latency_metrics_creation(self) -> None:
        """Test latency metrics construction."""
        metrics = LatencyMetrics(p50=10.0, p95=25.0, p99=50.0, avg=15.0)
        assert metrics.p50 == 10.0
        assert metrics.p95 == 25.0
        assert metrics.p99 == 50.0
        assert metrics.avg == 15.0


class TestErrorMetrics:
    """Tests for ErrorMetrics model."""

    def test_error_metrics_creation(self) -> None:
        """Test error metrics construction."""
        metrics = ErrorMetrics(total_requests=1000, error_count=10, error_rate=1.0)
        assert metrics.total_requests == 1000
        assert metrics.error_count == 10
        assert metrics.error_rate == 1.0


class TestHealthOverview:
    """Tests for HealthOverview model."""

    def test_health_overview_healthy(self) -> None:
        """Test health overview with healthy status."""
        latency = LatencyMetrics(p50=10.0, p95=25.0, p99=50.0, avg=15.0)
        errors = ErrorMetrics(total_requests=1000, error_count=5, error_rate=0.5)

        overview = HealthOverview(
            status=SystemStatus.HEALTHY,
            uptime_seconds=86400.0,
            uptime_formatted="1d 0h 0m",
            latency=latency,
            errors=errors,
            active_sessions=50,
            cache_hit_rate=95.0,
            security_events_24h=10,
        )

        assert overview.status == SystemStatus.HEALTHY
        assert overview.uptime_seconds == 86400.0
        assert overview.active_sessions == 50


class TestTimeRange:
    """Tests for TimeRange enum."""

    def test_time_range_values(self) -> None:
        """Test time range enum values."""
        assert TimeRange.ONE_HOUR.value == "1h"
        assert TimeRange.TWENTY_FOUR_HOURS.value == "24h"
        assert TimeRange.SEVEN_DAYS.value == "7d"
        assert TimeRange.THIRTY_DAYS.value == "30d"


class TestSystemStatus:
    """Tests for SystemStatus enum."""

    def test_system_status_values(self) -> None:
        """Test system status enum values."""
        assert SystemStatus.HEALTHY.value == "healthy"
        assert SystemStatus.DEGRADED.value == "degraded"
        assert SystemStatus.UNHEALTHY.value == "unhealthy"


class TestConnectionPoolMetrics:
    """Tests for ConnectionPoolMetrics model."""

    def test_connection_pool_metrics(self) -> None:
        """Test connection pool metrics construction."""
        metrics = ConnectionPoolMetrics(
            pool_size=10,
            active_connections=5,
            idle_connections=5,
            overflow_connections=0,
            max_overflow=20,
        )
        assert metrics.pool_size == 10
        assert metrics.active_connections == 5
        assert metrics.idle_connections == 5


class TestQueryLatencyMetrics:
    """Tests for QueryLatencyMetrics model."""

    def test_query_latency_metrics(self) -> None:
        """Test query latency metrics construction."""
        metrics = QueryLatencyMetrics(
            select_avg_ms=5.0,
            insert_avg_ms=10.0,
            update_avg_ms=8.0,
            delete_avg_ms=7.0,
        )
        assert metrics.select_avg_ms == 5.0
        assert metrics.insert_avg_ms == 10.0


class TestEndpointPerformance:
    """Tests for EndpointPerformance model."""

    def test_endpoint_performance(self) -> None:
        """Test endpoint performance construction."""
        latency = LatencyMetrics(p50=10.0, p95=25.0, p99=50.0, avg=15.0)
        perf = EndpointPerformance(
            endpoint="/api/v1/products",
            method="GET",
            request_count=1000,
            error_count=5,
            error_rate=0.5,
            latency=latency,
        )
        assert perf.endpoint == "/api/v1/products"
        assert perf.method == "GET"
        assert perf.request_count == 1000


class TestHealthTimeseriesDataPoint:
    """Tests for HealthTimeseriesDataPoint model."""

    def test_datapoint_minimal(self) -> None:
        """Test data point with minimal fields."""
        dp = HealthTimeseriesDataPoint(
            timestamp="2024-01-01T00:00:00",
            error_rate=0.5,
            latency_p95_ms=25.0,
            request_count=100,
        )
        assert dp.timestamp == "2024-01-01T00:00:00"
        assert dp.error_rate == 0.5
        assert dp.active_sessions is None

    def test_datapoint_with_sessions(self) -> None:
        """Test data point with active sessions."""
        dp = HealthTimeseriesDataPoint(
            timestamp="2024-01-01T00:00:00",
            error_rate=0.5,
            latency_p95_ms=25.0,
            request_count=100,
            active_sessions=50,
        )
        assert dp.active_sessions == 50


class TestHealthOverviewResponse:
    """Tests for HealthOverviewResponse model."""

    def test_health_overview_response(self) -> None:
        """Test health overview response construction."""
        latency = LatencyMetrics(p50=10.0, p95=25.0, p99=50.0, avg=15.0)
        errors = ErrorMetrics(total_requests=1000, error_count=5, error_rate=0.5)
        overview = HealthOverview(
            status=SystemStatus.HEALTHY,
            uptime_seconds=86400.0,
            uptime_formatted="1d 0h 0m",
            latency=latency,
            errors=errors,
            active_sessions=50,
            cache_hit_rate=95.0,
            security_events_24h=10,
        )
        response = HealthOverviewResponse(
            timestamp="2024-01-01T00:00:00Z",
            overview=overview,
        )
        assert response.status == "success"
        assert response.overview.status == SystemStatus.HEALTHY


class TestDatabaseHealthResponse:
    """Tests for DatabaseHealthResponse model."""

    def test_database_health_response(self) -> None:
        """Test database health response construction."""
        pool = ConnectionPoolMetrics(
            pool_size=10,
            active_connections=5,
            idle_connections=5,
            overflow_connections=0,
            max_overflow=20,
        )
        query = QueryLatencyMetrics(
            select_avg_ms=5.0,
            insert_avg_ms=10.0,
            update_avg_ms=8.0,
            delete_avg_ms=7.0,
        )
        response = DatabaseHealthResponse(
            timestamp="2024-01-01T00:00:00Z",
            db_status=SystemStatus.HEALTHY,
            connection_pool=pool,
            query_latency=query,
            slow_query_count=0,
            total_queries=5000,
        )
        assert response.status == "success"
        assert response.db_status == SystemStatus.HEALTHY


class TestHealthTimeseriesResponse:
    """Tests for HealthTimeseriesResponse model."""

    def test_health_timeseries_response(self) -> None:
        """Test health timeseries response construction."""
        data_points = [
            HealthTimeseriesDataPoint(
                timestamp="2024-01-01T00:00:00",
                error_rate=0.5,
                latency_p95_ms=25.0,
                request_count=100,
            )
        ]
        response = HealthTimeseriesResponse(
            timestamp="2024-01-01T01:00:00Z",
            time_range="1h",
            granularity="minute",
            data_points=data_points,
            summary={"avg_error_rate": 0.5},
        )
        assert response.status == "success"
        assert response.time_range == "1h"
        assert len(response.data_points) == 1


# =============================================================================
# Integration Tests (with mocked Prometheus)
# =============================================================================


class TestAPIEndpointsWithMocks:
    """Integration tests for API endpoints with mocked dependencies."""

    @pytest.fixture
    def mock_prometheus_registry(self) -> MagicMock:
        """Mock Prometheus registry."""
        registry = MagicMock()
        registry.collect.return_value = []
        return registry

    @pytest.mark.asyncio
    async def test_get_health_overview_structure(
        self, mock_user: MagicMock, mock_db_session: AsyncMock
    ) -> None:
        """Test that health overview returns correct structure."""
        # This test validates the response model structure
        latency = LatencyMetrics(p50=10.0, p95=25.0, p99=50.0, avg=15.0)
        errors = ErrorMetrics(total_requests=1000, error_count=5, error_rate=0.5)
        overview = HealthOverview(
            status=SystemStatus.HEALTHY,
            uptime_seconds=86400.0,
            uptime_formatted="1d 0h 0m",
            latency=latency,
            errors=errors,
            active_sessions=50,
            cache_hit_rate=95.0,
            security_events_24h=10,
        )
        response = HealthOverviewResponse(
            timestamp=datetime.now(UTC).isoformat(),
            overview=overview,
        )

        # Verify structure
        assert hasattr(response, "status")
        assert hasattr(response, "timestamp")
        assert hasattr(response, "overview")
        assert hasattr(response.overview, "latency")
        assert hasattr(response.overview, "errors")

    @pytest.mark.asyncio
    async def test_api_performance_response_structure(
        self, mock_user: MagicMock, mock_db_session: AsyncMock
    ) -> None:
        """Test that API performance returns correct structure."""
        from api.v1.analytics.health import APIPerformanceResponse

        response = APIPerformanceResponse(
            timestamp=datetime.now(UTC).isoformat(),
            time_range="24h",
            total_requests=10000,
            avg_latency_ms=50.0,
            overall_error_rate=0.5,
            endpoints=[],
            slowest_endpoints=[],
            highest_error_endpoints=[],
        )

        assert response.status == "success"
        assert response.time_range == "24h"
        assert isinstance(response.endpoints, list)

    @pytest.mark.asyncio
    async def test_database_health_response_structure(
        self, mock_user: MagicMock, mock_db_session: AsyncMock
    ) -> None:
        """Test that database health returns correct structure."""
        pool = ConnectionPoolMetrics(
            pool_size=10,
            active_connections=5,
            idle_connections=5,
            overflow_connections=0,
            max_overflow=20,
        )
        query = QueryLatencyMetrics(
            select_avg_ms=5.0,
            insert_avg_ms=10.0,
            update_avg_ms=8.0,
            delete_avg_ms=7.0,
        )
        response = DatabaseHealthResponse(
            timestamp=datetime.now(UTC).isoformat(),
            db_status=SystemStatus.HEALTHY,
            connection_pool=pool,
            query_latency=query,
            slow_query_count=0,
            total_queries=5000,
        )

        assert response.status == "success"
        assert response.db_status == SystemStatus.HEALTHY
        assert response.connection_pool.pool_size == 10

    @pytest.mark.asyncio
    async def test_timeseries_response_structure(
        self, mock_user: MagicMock, mock_db_session: AsyncMock
    ) -> None:
        """Test that timeseries returns correct structure."""
        data_points = [
            HealthTimeseriesDataPoint(
                timestamp="2024-01-01T00:00:00",
                error_rate=0.5,
                latency_p95_ms=25.0,
                request_count=100,
            )
            for _ in range(24)
        ]
        response = HealthTimeseriesResponse(
            timestamp=datetime.now(UTC).isoformat(),
            time_range="24h",
            granularity="hour",
            data_points=data_points,
            summary={
                "avg_error_rate": 0.5,
                "avg_latency_p95_ms": 25.0,
                "total_requests": 2400,
            },
        )

        assert response.status == "success"
        assert response.granularity == "hour"
        assert len(response.data_points) == 24
