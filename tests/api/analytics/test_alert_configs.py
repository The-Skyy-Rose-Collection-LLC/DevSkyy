"""Tests for Alert Configuration API endpoints.

Tests cover:
- GET /analytics/alert-configs - List with pagination/filtering
- POST /analytics/alert-configs - Create new config
- GET /analytics/alert-configs/{id} - Get single config
- PUT /analytics/alert-configs/{id} - Update config
- DELETE /analytics/alert-configs/{id} - Delete config

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from api.v1.analytics.alert_configs import (
    AlertConfigBase,
    AlertConfigCreate,
    AlertConfigCreateResponse,
    AlertConfigDeleteResponse,
    AlertConfigListResponse,
    AlertConfigResponse,
    AlertConfigUpdate,
    ConditionOperator,
    ConditionType,
    NotificationChannel,
    SeverityLevel,
    parse_json_field,
    parse_notification_channels,
    row_to_response,
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
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def sample_config_row() -> MagicMock:
    """Sample alert config row from database."""
    row = MagicMock()
    row.id = "config-123"
    row.name = "High Error Rate Alert"
    row.description = "Alerts when error rate exceeds threshold"
    row.metric_name = "api.error_rate"
    row.condition_type = "threshold"
    row.condition_operator = "gt"
    row.threshold_value = Decimal("0.05")
    row.threshold_unit = "percentage"
    row.window_duration_seconds = 300
    row.evaluation_interval_seconds = 60
    row.cooldown_seconds = 300
    row.severity = "warning"
    row.is_enabled = True
    row.notification_channels = ["slack", "email"]
    row.notification_config = {"slack": {"channel": "#alerts"}}
    row.filters = {"source": "api-gateway"}
    row.created_by = "user-456"
    row.updated_by = "user-456"
    row.created_at = datetime.now(UTC)
    row.updated_at = datetime.now(UTC)
    return row


# =============================================================================
# Unit Tests - Enums
# =============================================================================


class TestConditionType:
    """Tests for ConditionType enum."""

    def test_condition_type_values(self) -> None:
        """Test ConditionType enum values."""
        assert ConditionType.THRESHOLD.value == "threshold"
        assert ConditionType.ANOMALY.value == "anomaly"
        assert ConditionType.RATE.value == "rate"


class TestConditionOperator:
    """Tests for ConditionOperator enum."""

    def test_condition_operator_values(self) -> None:
        """Test ConditionOperator enum values."""
        assert ConditionOperator.GT.value == "gt"
        assert ConditionOperator.LT.value == "lt"
        assert ConditionOperator.GTE.value == "gte"
        assert ConditionOperator.LTE.value == "lte"
        assert ConditionOperator.EQ.value == "eq"
        assert ConditionOperator.NEQ.value == "neq"


class TestSeverityLevel:
    """Tests for SeverityLevel enum."""

    def test_severity_level_values(self) -> None:
        """Test SeverityLevel enum values."""
        assert SeverityLevel.INFO.value == "info"
        assert SeverityLevel.WARNING.value == "warning"
        assert SeverityLevel.CRITICAL.value == "critical"


class TestNotificationChannel:
    """Tests for NotificationChannel enum."""

    def test_notification_channel_values(self) -> None:
        """Test NotificationChannel enum values."""
        assert NotificationChannel.EMAIL.value == "email"
        assert NotificationChannel.SLACK.value == "slack"
        assert NotificationChannel.SMS.value == "sms"
        assert NotificationChannel.IN_APP.value == "in_app"


# =============================================================================
# Unit Tests - Helper Functions
# =============================================================================


class TestParseNotificationChannels:
    """Tests for parse_notification_channels helper."""

    def test_parse_list(self) -> None:
        """Test parsing list of channels."""
        result = parse_notification_channels(["slack", "email"])
        assert result == ["slack", "email"]

    def test_parse_none(self) -> None:
        """Test parsing None."""
        result = parse_notification_channels(None)
        assert result == []

    def test_parse_empty_list(self) -> None:
        """Test parsing empty list."""
        result = parse_notification_channels([])
        assert result == []


class TestParseJsonField:
    """Tests for parse_json_field helper."""

    def test_parse_dict(self) -> None:
        """Test parsing dict."""
        result = parse_json_field({"key": "value"})
        assert result == {"key": "value"}

    def test_parse_none(self) -> None:
        """Test parsing None."""
        result = parse_json_field(None)
        assert result == {}

    def test_parse_non_dict(self) -> None:
        """Test parsing non-dict."""
        result = parse_json_field("not a dict")
        assert result == {}


class TestRowToResponse:
    """Tests for row_to_response helper."""

    def test_convert_full_row(self, sample_config_row: MagicMock) -> None:
        """Test converting a full row."""
        response = row_to_response(sample_config_row)

        assert response.id == "config-123"
        assert response.name == "High Error Rate Alert"
        assert response.metric_name == "api.error_rate"
        assert response.condition_type == ConditionType.THRESHOLD
        assert response.condition_operator == ConditionOperator.GT
        assert response.threshold_value == Decimal("0.05")
        assert response.severity == SeverityLevel.WARNING
        assert response.is_enabled is True
        assert response.notification_channels == ["slack", "email"]


# =============================================================================
# Unit Tests - Pydantic Models
# =============================================================================


class TestAlertConfigBase:
    """Tests for AlertConfigBase model."""

    def test_create_with_defaults(self) -> None:
        """Test creating config with defaults."""
        config = AlertConfigBase(
            name="Test Alert",
            metric_name="test.metric",
        )

        assert config.name == "Test Alert"
        assert config.metric_name == "test.metric"
        assert config.condition_type == ConditionType.THRESHOLD
        assert config.condition_operator == ConditionOperator.GT
        assert config.window_duration_seconds == 300
        assert config.evaluation_interval_seconds == 60
        assert config.cooldown_seconds == 300
        assert config.severity == SeverityLevel.WARNING
        assert config.is_enabled is True
        assert config.notification_channels == []

    def test_create_with_all_fields(self) -> None:
        """Test creating config with all fields."""
        config = AlertConfigBase(
            name="Critical Alert",
            description="Critical system alert",
            metric_name="system.cpu",
            condition_type=ConditionType.THRESHOLD,
            condition_operator=ConditionOperator.GTE,
            threshold_value=Decimal("90.0"),
            threshold_unit="percentage",
            window_duration_seconds=600,
            evaluation_interval_seconds=30,
            cooldown_seconds=600,
            severity=SeverityLevel.CRITICAL,
            is_enabled=True,
            notification_channels=["slack", "sms"],
            notification_config={"slack": {"channel": "#critical"}},
            filters={"environment": "production"},
        )

        assert config.name == "Critical Alert"
        assert config.severity == SeverityLevel.CRITICAL
        assert config.notification_channels == ["slack", "sms"]


class TestAlertConfigCreate:
    """Tests for AlertConfigCreate model."""

    def test_create_request(self) -> None:
        """Test create request model."""
        request = AlertConfigCreate(
            name="New Alert",
            metric_name="api.latency",
            threshold_value=Decimal("1.0"),
        )

        assert request.name == "New Alert"
        assert request.threshold_value == Decimal("1.0")


class TestAlertConfigUpdate:
    """Tests for AlertConfigUpdate model."""

    def test_update_partial(self) -> None:
        """Test partial update request."""
        update = AlertConfigUpdate(
            name="Updated Name",
            is_enabled=False,
        )

        assert update.name == "Updated Name"
        assert update.is_enabled is False
        assert update.severity is None

    def test_update_empty(self) -> None:
        """Test empty update request."""
        update = AlertConfigUpdate()

        assert update.name is None
        assert update.severity is None


class TestAlertConfigResponse:
    """Tests for AlertConfigResponse model."""

    def test_response_model(self) -> None:
        """Test response model construction."""
        response = AlertConfigResponse(
            id="config-123",
            name="Test Alert",
            description=None,
            metric_name="test.metric",
            condition_type=ConditionType.THRESHOLD,
            condition_operator=ConditionOperator.GT,
            threshold_value=Decimal("10.0"),
            threshold_unit=None,
            window_duration_seconds=300,
            evaluation_interval_seconds=60,
            cooldown_seconds=300,
            severity=SeverityLevel.WARNING,
            is_enabled=True,
            notification_channels=["slack"],
            notification_config={},
            filters={},
            created_by="user-123",
            updated_by="user-123",
            created_at="2024-01-01T00:00:00+00:00",
            updated_at="2024-01-01T00:00:00+00:00",
        )

        assert response.id == "config-123"
        assert response.severity == SeverityLevel.WARNING


class TestAlertConfigListResponse:
    """Tests for AlertConfigListResponse model."""

    def test_list_response(self) -> None:
        """Test list response model."""
        response = AlertConfigListResponse(
            status="success",
            timestamp="2024-01-01T00:00:00+00:00",
            total=1,
            page=1,
            page_size=50,
            configs=[],
        )

        assert response.status == "success"
        assert response.total == 1


class TestAlertConfigCreateResponse:
    """Tests for AlertConfigCreateResponse model."""

    def test_create_response(self) -> None:
        """Test create response model."""
        config = AlertConfigResponse(
            id="config-123",
            name="Test",
            description=None,
            metric_name="test",
            condition_type=ConditionType.THRESHOLD,
            condition_operator=ConditionOperator.GT,
            threshold_value=None,
            threshold_unit=None,
            window_duration_seconds=300,
            evaluation_interval_seconds=60,
            cooldown_seconds=300,
            severity=SeverityLevel.WARNING,
            is_enabled=True,
            notification_channels=[],
            notification_config={},
            filters={},
            created_by=None,
            updated_by=None,
            created_at="",
            updated_at="",
        )

        response = AlertConfigCreateResponse(
            status="success",
            message="Created successfully",
            config=config,
        )

        assert response.status == "success"
        assert response.config.id == "config-123"


class TestAlertConfigDeleteResponse:
    """Tests for AlertConfigDeleteResponse model."""

    def test_delete_response(self) -> None:
        """Test delete response model."""
        response = AlertConfigDeleteResponse(
            status="success",
            message="Deleted successfully",
            deleted_id="config-123",
        )

        assert response.status == "success"
        assert response.deleted_id == "config-123"


# =============================================================================
# Integration Tests - API Endpoints
# =============================================================================


class TestListAlertConfigs:
    """Tests for GET /analytics/alert-configs endpoint."""

    @pytest.mark.asyncio
    async def test_list_success(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
        sample_config_row: MagicMock,
    ) -> None:
        """Test successful config listing."""
        count_result = MagicMock()
        count_result.scalar.return_value = 1

        data_result = MagicMock()
        data_result.fetchall.return_value = [sample_config_row]

        mock_db_session.execute.side_effect = [count_result, data_result]

        from api.v1.analytics.alert_configs import list_alert_configs

        response = await list_alert_configs(
            page=1,
            page_size=50,
            severity=None,
            is_enabled=None,
            metric_name=None,
            search=None,
            user=mock_user,
            db=mock_db_session,
        )

        assert response.status == "success"
        assert response.total == 1
        assert len(response.configs) == 1
        assert response.configs[0].name == "High Error Rate Alert"

    @pytest.mark.asyncio
    async def test_list_with_filters(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
        sample_config_row: MagicMock,
    ) -> None:
        """Test listing with filters."""
        count_result = MagicMock()
        count_result.scalar.return_value = 1

        data_result = MagicMock()
        data_result.fetchall.return_value = [sample_config_row]

        mock_db_session.execute.side_effect = [count_result, data_result]

        from api.v1.analytics.alert_configs import list_alert_configs

        response = await list_alert_configs(
            page=1,
            page_size=50,
            severity=SeverityLevel.WARNING,
            is_enabled=True,
            metric_name=None,
            search="error",
            user=mock_user,
            db=mock_db_session,
        )

        assert response.status == "success"

    @pytest.mark.asyncio
    async def test_list_empty(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test empty config list."""
        count_result = MagicMock()
        count_result.scalar.return_value = 0

        data_result = MagicMock()
        data_result.fetchall.return_value = []

        mock_db_session.execute.side_effect = [count_result, data_result]

        from api.v1.analytics.alert_configs import list_alert_configs

        response = await list_alert_configs(
            page=1,
            page_size=50,
            severity=None,
            is_enabled=None,
            metric_name=None,
            search=None,
            user=mock_user,
            db=mock_db_session,
        )

        assert response.status == "success"
        assert response.total == 0
        assert len(response.configs) == 0


class TestCreateAlertConfig:
    """Tests for POST /analytics/alert-configs endpoint."""

    @pytest.mark.asyncio
    async def test_create_success(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
        sample_config_row: MagicMock,
    ) -> None:
        """Test successful config creation."""
        insert_result = MagicMock()
        insert_result.fetchone.return_value = sample_config_row

        mock_db_session.execute.return_value = insert_result

        from api.v1.analytics.alert_configs import create_alert_config

        response = await create_alert_config(
            request=AlertConfigCreate(
                name="New Alert",
                metric_name="api.latency",
                threshold_value=Decimal("1.0"),
            ),
            user=mock_user,
            db=mock_db_session,
        )

        assert response.status == "success"
        assert "created successfully" in response.message


class TestGetAlertConfig:
    """Tests for GET /analytics/alert-configs/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_success(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
        sample_config_row: MagicMock,
    ) -> None:
        """Test successful config retrieval."""
        result = MagicMock()
        result.fetchone.return_value = sample_config_row

        mock_db_session.execute.return_value = result

        from api.v1.analytics.alert_configs import get_alert_config

        response = await get_alert_config(
            config_id="config-123",
            user=mock_user,
            db=mock_db_session,
        )

        assert response.id == "config-123"
        assert response.name == "High Error Rate Alert"

    @pytest.mark.asyncio
    async def test_get_not_found(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test config not found."""
        result = MagicMock()
        result.fetchone.return_value = None

        mock_db_session.execute.return_value = result

        from fastapi import HTTPException

        from api.v1.analytics.alert_configs import get_alert_config

        with pytest.raises(HTTPException) as exc_info:
            await get_alert_config(
                config_id="nonexistent",
                user=mock_user,
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 404


class TestUpdateAlertConfig:
    """Tests for PUT /analytics/alert-configs/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_success(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
        sample_config_row: MagicMock,
    ) -> None:
        """Test successful config update."""
        # Check exists
        check_result = MagicMock()
        check_row = MagicMock()
        check_row.id = "config-123"
        check_result.fetchone.return_value = check_row

        # Update result
        update_result = MagicMock()
        sample_config_row.name = "Updated Name"
        update_result.fetchone.return_value = sample_config_row

        mock_db_session.execute.side_effect = [check_result, update_result]

        from api.v1.analytics.alert_configs import update_alert_config

        response = await update_alert_config(
            config_id="config-123",
            request=AlertConfigUpdate(name="Updated Name"),
            user=mock_user,
            db=mock_db_session,
        )

        assert response.status == "success"
        assert "updated successfully" in response.message

    @pytest.mark.asyncio
    async def test_update_not_found(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test update config not found."""
        result = MagicMock()
        result.fetchone.return_value = None

        mock_db_session.execute.return_value = result

        from fastapi import HTTPException

        from api.v1.analytics.alert_configs import update_alert_config

        with pytest.raises(HTTPException) as exc_info:
            await update_alert_config(
                config_id="nonexistent",
                request=AlertConfigUpdate(name="Test"),
                user=mock_user,
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 404


class TestDeleteAlertConfig:
    """Tests for DELETE /analytics/alert-configs/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_success(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test successful config deletion."""
        check_result = MagicMock()
        check_row = MagicMock()
        check_row.id = "config-123"
        check_row.name = "Test Alert"
        check_result.fetchone.return_value = check_row

        mock_db_session.execute.side_effect = [check_result, MagicMock()]

        from api.v1.analytics.alert_configs import delete_alert_config

        response = await delete_alert_config(
            config_id="config-123",
            user=mock_user,
            db=mock_db_session,
        )

        assert response.status == "success"
        assert response.deleted_id == "config-123"
        assert "deleted successfully" in response.message

    @pytest.mark.asyncio
    async def test_delete_not_found(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test delete config not found."""
        result = MagicMock()
        result.fetchone.return_value = None

        mock_db_session.execute.return_value = result

        from fastapi import HTTPException

        from api.v1.analytics.alert_configs import delete_alert_config

        with pytest.raises(HTTPException) as exc_info:
            await delete_alert_config(
                config_id="nonexistent",
                user=mock_user,
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 404


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and validation."""

    def test_model_serialization(self) -> None:
        """Test models can be serialized."""
        config = AlertConfigResponse(
            id="test-123",
            name="Test",
            description=None,
            metric_name="test",
            condition_type=ConditionType.THRESHOLD,
            condition_operator=ConditionOperator.GT,
            threshold_value=Decimal("10.5"),
            threshold_unit="ms",
            window_duration_seconds=300,
            evaluation_interval_seconds=60,
            cooldown_seconds=300,
            severity=SeverityLevel.WARNING,
            is_enabled=True,
            notification_channels=["slack"],
            notification_config={"slack": {"channel": "#alerts"}},
            filters={"env": "prod"},
            created_by="user-1",
            updated_by="user-1",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )

        # Verify can be serialized to dict
        config_dict = config.model_dump()
        assert config_dict["id"] == "test-123"
        assert config_dict["notification_config"]["slack"]["channel"] == "#alerts"

    def test_default_values(self) -> None:
        """Test default values are applied correctly."""
        config = AlertConfigBase(
            name="Test",
            metric_name="test.metric",
        )

        assert config.window_duration_seconds == 300
        assert config.evaluation_interval_seconds == 60
        assert config.cooldown_seconds == 300
        assert config.severity == SeverityLevel.WARNING
        assert config.is_enabled is True
        assert config.notification_channels == []
        assert config.notification_config == {}
        assert config.filters == {}
