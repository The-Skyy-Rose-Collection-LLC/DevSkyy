"""Tests for Dashboard Summary API endpoint.

Tests cover:
- GET /analytics/dashboard/summary
- Role-based access control
- Section filtering
- Response caching
- Error handling
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from api.v1.analytics.dashboard import (
    AlertInfo,
    AlertSeverity,
    AlertsSection,
    BusinessMetric,
    BusinessSection,
    DashboardCache,
    DashboardSection,
    MLPipelineInfo,
    MLPipelinesSection,
    PipelineStatus,
    ServiceHealth,
    SystemHealthSection,
    fetch_active_alerts,
    fetch_business_metrics,
    fetch_ml_pipelines,
    fetch_system_health,
    get_allowed_sections,
    get_dashboard_summary,
)
from security.jwt_oauth2_auth import TokenPayload, TokenType, UserRole

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_admin_user() -> MagicMock:
    """Mock admin user with full access."""
    user = MagicMock(spec=TokenPayload)
    user.sub = "admin-user-123"
    user.roles = [UserRole.ADMIN.value]
    user.type = TokenType.ACCESS

    def has_any_role(roles: set[UserRole]) -> bool:
        user_roles = {r for r in UserRole if r.value in user.roles}
        return bool(user_roles & roles)

    user.has_any_role = has_any_role
    user.get_highest_role = MagicMock(return_value=UserRole.ADMIN)
    return user


@pytest.fixture
def mock_business_user() -> MagicMock:
    """Mock business user with limited access."""
    user = MagicMock(spec=TokenPayload)
    user.sub = "business-user-456"
    user.roles = [UserRole.API_USER.value]
    user.type = TokenType.ACCESS

    def has_any_role(roles: set[UserRole]) -> bool:
        user_roles = {r for r in UserRole if r.value in user.roles}
        return bool(user_roles & roles)

    user.has_any_role = has_any_role
    user.get_highest_role = MagicMock(return_value=UserRole.API_USER)
    return user


@pytest.fixture
def mock_guest_user() -> MagicMock:
    """Mock guest user with no access."""
    user = MagicMock(spec=TokenPayload)
    user.sub = "guest-user-789"
    user.roles = [UserRole.GUEST.value]
    user.type = TokenType.ACCESS

    def has_any_role(roles: set[UserRole]) -> bool:
        user_roles = {r for r in UserRole if r.value in user.roles}
        return bool(user_roles & roles)

    user.has_any_role = has_any_role
    user.get_highest_role = MagicMock(return_value=UserRole.GUEST)
    return user


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Mock database session."""
    session = AsyncMock()
    return session


# =============================================================================
# Unit Tests - Enums
# =============================================================================


class TestDashboardSection:
    """Tests for DashboardSection enum."""

    def test_section_values(self) -> None:
        """Test enum values."""
        assert DashboardSection.HEALTH.value == "health"
        assert DashboardSection.ML.value == "ml"
        assert DashboardSection.BUSINESS.value == "business"
        assert DashboardSection.ALERTS.value == "alerts"


class TestAlertSeverity:
    """Tests for AlertSeverity enum."""

    def test_severity_values(self) -> None:
        """Test enum values."""
        assert AlertSeverity.CRITICAL.value == "critical"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.INFO.value == "info"


class TestPipelineStatus:
    """Tests for PipelineStatus enum."""

    def test_status_values(self) -> None:
        """Test enum values."""
        assert PipelineStatus.RUNNING.value == "running"
        assert PipelineStatus.COMPLETED.value == "completed"
        assert PipelineStatus.FAILED.value == "failed"
        assert PipelineStatus.PENDING.value == "pending"


# =============================================================================
# Unit Tests - Pydantic Models
# =============================================================================


class TestServiceHealth:
    """Tests for ServiceHealth model."""

    def test_service_health(self) -> None:
        """Test service health construction."""
        service = ServiceHealth(
            name="api",
            status="healthy",
            response_time_ms=12.5,
            last_check="2024-01-01T00:00:00Z",
        )
        assert service.name == "api"
        assert service.status == "healthy"
        assert service.response_time_ms == 12.5


class TestBusinessMetric:
    """Tests for BusinessMetric model."""

    def test_minimal_metric(self) -> None:
        """Test metric with only required field."""
        metric = BusinessMetric(value=100.0)
        assert metric.value == 100.0
        assert metric.change_pct is None
        assert metric.trend is None

    def test_full_metric(self) -> None:
        """Test metric with all fields."""
        metric = BusinessMetric(
            value=120.0,
            change_pct=20.0,
            trend="up",
        )
        assert metric.value == 120.0
        assert metric.change_pct == 20.0
        assert metric.trend == "up"


class TestMLPipelineInfo:
    """Tests for MLPipelineInfo model."""

    def test_pipeline_info(self) -> None:
        """Test pipeline info construction."""
        pipeline = MLPipelineInfo(
            pipeline_id="pipe-001",
            name="Test Pipeline",
            status=PipelineStatus.RUNNING,
            progress_pct=50.0,
        )
        assert pipeline.pipeline_id == "pipe-001"
        assert pipeline.status == PipelineStatus.RUNNING
        assert pipeline.progress_pct == 50.0


class TestAlertInfo:
    """Tests for AlertInfo model."""

    def test_alert_info(self) -> None:
        """Test alert info construction."""
        alert = AlertInfo(
            alert_id="alert-001",
            title="Test Alert",
            message="Test message",
            severity=AlertSeverity.WARNING,
            source="test",
            created_at="2024-01-01T00:00:00Z",
        )
        assert alert.alert_id == "alert-001"
        assert alert.severity == AlertSeverity.WARNING
        assert alert.acknowledged is False


# =============================================================================
# Unit Tests - Role-based Access Control
# =============================================================================


class TestGetAllowedSections:
    """Tests for get_allowed_sections function."""

    def test_admin_gets_all_sections(self, mock_admin_user: MagicMock) -> None:
        """Admin users should see all sections."""
        sections = get_allowed_sections(mock_admin_user)
        assert DashboardSection.HEALTH in sections
        assert DashboardSection.ML in sections
        assert DashboardSection.BUSINESS in sections
        assert DashboardSection.ALERTS in sections

    def test_business_user_gets_business_only(self, mock_business_user: MagicMock) -> None:
        """Business users should only see business metrics."""
        sections = get_allowed_sections(mock_business_user)
        assert DashboardSection.BUSINESS in sections
        assert DashboardSection.HEALTH not in sections
        assert DashboardSection.ML not in sections
        assert DashboardSection.ALERTS not in sections

    def test_guest_gets_nothing(self, mock_guest_user: MagicMock) -> None:
        """Guest users should not see any sections."""
        sections = get_allowed_sections(mock_guest_user)
        assert len(sections) == 0


# =============================================================================
# Unit Tests - Data Fetchers
# =============================================================================


class TestFetchSystemHealth:
    """Tests for fetch_system_health function."""

    @pytest.mark.asyncio
    async def test_returns_system_health_section(self) -> None:
        """Test that function returns proper SystemHealthSection."""
        result = await fetch_system_health()

        assert isinstance(result, SystemHealthSection)
        assert result.overall_status in ["healthy", "degraded", "unhealthy"]
        assert len(result.services) > 0
        assert result.uptime_pct >= 0
        assert result.last_updated is not None


class TestFetchMLPipelines:
    """Tests for fetch_ml_pipelines function."""

    @pytest.mark.asyncio
    async def test_returns_ml_pipelines_section(self) -> None:
        """Test that function returns proper MLPipelinesSection."""
        result = await fetch_ml_pipelines()

        assert isinstance(result, MLPipelinesSection)
        assert result.total_pipelines >= 0
        assert result.running >= 0
        assert result.completed >= 0
        assert result.failed >= 0
        assert result.pending >= 0
        assert result.last_updated is not None


class TestFetchActiveAlerts:
    """Tests for fetch_active_alerts function."""

    @pytest.mark.asyncio
    async def test_returns_alerts_section(self) -> None:
        """Test that function returns proper AlertsSection."""
        result = await fetch_active_alerts()

        assert isinstance(result, AlertsSection)
        assert result.total_alerts >= 0
        assert result.critical >= 0
        assert result.warning >= 0
        assert result.info >= 0
        assert result.last_updated is not None


class TestFetchBusinessMetrics:
    """Tests for fetch_business_metrics function."""

    @pytest.mark.asyncio
    async def test_returns_business_section(
        self,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test that function returns proper BusinessSection."""
        # Mock database query result
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.order_count = 100
        mock_row.total_revenue = 15000.0
        mock_row.avg_order_value = 150.0
        mock_row.unique_customers = 85
        mock_result.one.return_value = mock_row
        mock_db_session.execute.return_value = mock_result

        result = await fetch_business_metrics(mock_db_session, period_days=30)

        assert isinstance(result, BusinessSection)
        assert result.period_days == 30
        assert result.last_updated is not None

    @pytest.mark.asyncio
    async def test_handles_database_error(
        self,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test that function handles database errors gracefully."""
        mock_db_session.execute.side_effect = Exception("Database error")

        result = await fetch_business_metrics(mock_db_session, period_days=30)

        # Should return empty metrics on error
        assert isinstance(result, BusinessSection)
        assert result.total_revenue.value == 0
        assert result.order_count.value == 0


# =============================================================================
# Unit Tests - Cache
# =============================================================================


class TestDashboardCache:
    """Tests for DashboardCache class."""

    def test_generate_key(self) -> None:
        """Test cache key generation."""
        cache = DashboardCache()
        key = cache._generate_key("health", "user123")

        assert key.startswith("dashboard:health:")
        assert len(key) > len("dashboard:health:")

    @pytest.mark.asyncio
    async def test_set_and_get_in_memory(self) -> None:
        """Test in-memory cache set and get."""
        cache = DashboardCache()
        test_data = {"status": "healthy"}

        await cache.set("health", "user123", test_data, ttl=60)
        result = await cache.get("health", "user123")

        assert result == test_data

    @pytest.mark.asyncio
    async def test_cache_expiry(self) -> None:
        """Test that cached values expire."""
        cache = DashboardCache()
        test_data = {"status": "healthy"}

        # Set with very short TTL
        await cache.set("health", "user123", test_data, ttl=0)

        # Should be expired immediately
        result = await cache.get("health", "user123")
        assert result is None


# =============================================================================
# Integration Tests - Dashboard Summary Endpoint
# =============================================================================


class TestGetDashboardSummary:
    """Tests for GET /analytics/dashboard/summary endpoint."""

    @pytest.mark.asyncio
    async def test_admin_gets_all_sections(
        self,
        mock_admin_user: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """Admin should receive all sections in response."""
        # Mock database query
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.order_count = 100
        mock_row.total_revenue = 15000.0
        mock_row.avg_order_value = 150.0
        mock_row.unique_customers = 85
        mock_result.one.return_value = mock_row
        mock_db_session.execute.return_value = mock_result

        response = await get_dashboard_summary(
            sections=None,
            period_days=30,
            user=mock_admin_user,
            db=mock_db_session,
        )

        assert response.status == "success"
        assert response.user_role == "admin"
        assert response.system_health is not None
        assert response.ml_pipelines is not None
        assert response.business is not None
        assert response.active_alerts is not None

    @pytest.mark.asyncio
    async def test_business_user_gets_business_only(
        self,
        mock_business_user: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """Business user should only receive business section."""
        # Mock database query
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.order_count = 50
        mock_row.total_revenue = 5000.0
        mock_row.avg_order_value = 100.0
        mock_row.unique_customers = 40
        mock_result.one.return_value = mock_row
        mock_db_session.execute.return_value = mock_result

        response = await get_dashboard_summary(
            sections=None,
            period_days=30,
            user=mock_business_user,
            db=mock_db_session,
        )

        assert response.status == "success"
        assert response.user_role == "api_user"
        assert response.system_health is None
        assert response.ml_pipelines is None
        assert response.business is not None
        assert response.active_alerts is None

    @pytest.mark.asyncio
    async def test_section_filtering(
        self,
        mock_admin_user: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test that sections parameter filters response."""
        response = await get_dashboard_summary(
            sections="health,alerts",
            period_days=30,
            user=mock_admin_user,
            db=mock_db_session,
        )

        assert response.status == "success"
        assert response.system_health is not None
        assert response.active_alerts is not None
        assert response.ml_pipelines is None
        assert response.business is None

    @pytest.mark.asyncio
    async def test_guest_access_denied(
        self,
        mock_guest_user: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """Guest users should be denied access."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_dashboard_summary(
                sections=None,
                period_days=30,
                user=mock_guest_user,
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_invalid_sections_ignored(
        self,
        mock_admin_user: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """Invalid section names should be ignored."""
        response = await get_dashboard_summary(
            sections="health,invalid_section,alerts",
            period_days=30,
            user=mock_admin_user,
            db=mock_db_session,
        )

        assert response.status == "success"
        assert "health" in response.requested_sections
        assert "alerts" in response.requested_sections
        assert "invalid_section" not in response.requested_sections


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_sections_uses_allowed(
        self,
        mock_admin_user: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """Empty sections parameter should return all allowed sections."""
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.order_count = 0
        mock_row.total_revenue = None
        mock_row.avg_order_value = None
        mock_row.unique_customers = 0
        mock_result.one.return_value = mock_row
        mock_db_session.execute.return_value = mock_result

        response = await get_dashboard_summary(
            sections="",
            period_days=30,
            user=mock_admin_user,
            db=mock_db_session,
        )

        # Empty string should be treated as no filter (all allowed sections)
        assert response.status == "success"

    @pytest.mark.asyncio
    async def test_period_days_custom_value(
        self,
        mock_admin_user: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test custom period_days value."""
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.order_count = 0
        mock_row.total_revenue = None
        mock_row.avg_order_value = None
        mock_row.unique_customers = 0
        mock_result.one.return_value = mock_row
        mock_db_session.execute.return_value = mock_result

        response = await get_dashboard_summary(
            sections="business",
            period_days=7,
            user=mock_admin_user,
            db=mock_db_session,
        )

        assert response.status == "success"
        assert response.business is not None
        assert response.business.period_days == 7
