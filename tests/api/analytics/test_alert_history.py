"""Tests for Alert History and Acknowledgment API endpoints.

Tests cover:
- GET /analytics/alerts/history
- GET /analytics/alerts/active
- POST /analytics/alerts/{id}/acknowledge
- POST /analytics/alerts/{id}/resolve
- POST /analytics/alerts/bulk-acknowledge

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from api.v1.analytics.alerts import (
    AcknowledgeRequest,
    ActiveAlertsResponse,
    AlertHistoryItem,
    AlertHistoryResponse,
    AlertMetadata,
    AlertSeverity,
    AlertStatus,
    BulkAcknowledgeRequest,
    BulkAcknowledgeResponse,
    BulkAcknowledgeResult,
    NotificationRecord,
    ResolveRequest,
    build_alert_metadata,
    parse_json_field,
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
def sample_alert_row() -> MagicMock:
    """Sample alert row from database."""
    row = MagicMock()
    row.id = "alert-123"
    row.alert_config_id = "config-456"
    row.status = "triggered"
    row.severity = "warning"
    row.title = "High Error Rate"
    row.message = "Error rate exceeded threshold"
    row.metric_value = 15.5
    row.threshold_value = 10.0
    row.context_json = '{"source": "api-gateway"}'
    row.triggered_at = datetime.now(UTC)
    row.resolved_at = None
    row.acknowledged_at = None
    row.acknowledged_by = None
    row.acknowledge_note = None
    row.notifications_sent_json = (
        '[{"channel": "slack", "sent_at": "2024-01-01T00:00:00", "status": "sent"}]'
    )
    row.alert_name = "API Error Rate Alert"
    row.condition_type = "threshold"
    row.condition_operator = "gt"
    row.window_duration_seconds = 300
    return row


# =============================================================================
# Unit Tests - Helper Functions
# =============================================================================


class TestParseJsonField:
    """Tests for parse_json_field helper function."""

    def test_parse_valid_json(self) -> None:
        """Test parsing valid JSON."""
        result = parse_json_field('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_empty_string(self) -> None:
        """Test parsing empty string."""
        result = parse_json_field("")
        assert result == {}

    def test_parse_none(self) -> None:
        """Test parsing None."""
        result = parse_json_field(None)
        assert result == {}

    def test_parse_invalid_json(self) -> None:
        """Test parsing invalid JSON."""
        result = parse_json_field("not valid json")
        assert result == {}

    def test_parse_json_array(self) -> None:
        """Test parsing JSON array."""
        result = parse_json_field("[1, 2, 3]")
        assert result == [1, 2, 3]


class TestBuildAlertMetadata:
    """Tests for build_alert_metadata helper function."""

    def test_build_metadata_with_all_fields(self) -> None:
        """Test building metadata with all fields."""
        triggered_at = datetime.now(UTC)
        notifications_json = (
            '[{"channel": "slack", "sent_at": "2024-01-01T00:00:00", "status": "sent"}]'
        )
        context_json = '{"source": "api"}'

        class MockConfig:
            condition_type = "threshold"
            condition_operator = "gt"
            window_duration_seconds = 300

        metadata = build_alert_metadata(
            triggered_at=triggered_at,
            metric_value=15.5,
            threshold_value=10.0,
            notifications_sent_json=notifications_json,
            context_json=context_json,
            alert_config=MockConfig(),
        )

        assert metadata.metric_value == 15.5
        assert metadata.threshold_value == 10.0
        assert metadata.condition_type == "threshold"
        assert metadata.condition_operator == "gt"
        assert metadata.window_duration_seconds == 300
        assert len(metadata.notifications_sent) == 1
        assert metadata.notifications_sent[0].channel == "slack"
        assert metadata.context == {"source": "api"}

    def test_build_metadata_with_none_config(self) -> None:
        """Test building metadata without config."""
        triggered_at = datetime.now(UTC)
        metadata = build_alert_metadata(
            triggered_at=triggered_at,
            metric_value=None,
            threshold_value=None,
            notifications_sent_json=None,
            context_json=None,
            alert_config=None,
        )

        assert metadata.metric_value is None
        assert metadata.condition_type is None
        assert metadata.notifications_sent == []
        assert metadata.context == {}


# =============================================================================
# Unit Tests - Pydantic Models
# =============================================================================


class TestAlertStatus:
    """Tests for AlertStatus enum."""

    def test_status_values(self) -> None:
        """Test AlertStatus enum values."""
        assert AlertStatus.TRIGGERED.value == "triggered"
        assert AlertStatus.ACKNOWLEDGED.value == "acknowledged"
        assert AlertStatus.RESOLVED.value == "resolved"


class TestAlertSeverity:
    """Tests for AlertSeverity enum."""

    def test_severity_values(self) -> None:
        """Test AlertSeverity enum values."""
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.CRITICAL.value == "critical"


class TestNotificationRecord:
    """Tests for NotificationRecord model."""

    def test_notification_record(self) -> None:
        """Test notification record construction."""
        record = NotificationRecord(
            channel="slack",
            sent_at="2024-01-01T00:00:00",
            status="sent",
            recipient="#alerts",
        )
        assert record.channel == "slack"
        assert record.status == "sent"
        assert record.recipient == "#alerts"
        assert record.error is None


class TestAlertMetadata:
    """Tests for AlertMetadata model."""

    def test_alert_metadata_minimal(self) -> None:
        """Test alert metadata with minimal fields."""
        metadata = AlertMetadata(trigger_time="2024-01-01T00:00:00")
        assert metadata.trigger_time == "2024-01-01T00:00:00"
        assert metadata.metric_value is None
        assert metadata.notifications_sent == []

    def test_alert_metadata_full(self) -> None:
        """Test alert metadata with all fields."""
        metadata = AlertMetadata(
            trigger_time="2024-01-01T00:00:00",
            metric_value=15.5,
            threshold_value=10.0,
            condition_type="threshold",
            condition_operator="gt",
            window_duration_seconds=300,
            notifications_sent=[
                NotificationRecord(channel="slack", sent_at="2024-01-01T00:00:00", status="sent")
            ],
            context={"source": "api"},
        )
        assert metadata.metric_value == 15.5
        assert len(metadata.notifications_sent) == 1


class TestAlertHistoryItem:
    """Tests for AlertHistoryItem model."""

    def test_alert_history_item(self) -> None:
        """Test alert history item construction."""
        metadata = AlertMetadata(trigger_time="2024-01-01T00:00:00")
        item = AlertHistoryItem(
            id="alert-123",
            alert_config_id="config-456",
            status=AlertStatus.TRIGGERED,
            severity=AlertSeverity.WARNING,
            title="High Error Rate",
            triggered_at="2024-01-01T00:00:00",
            metadata=metadata,
        )
        assert item.id == "alert-123"
        assert item.status == AlertStatus.TRIGGERED
        assert item.severity == AlertSeverity.WARNING
        assert item.acknowledged_at is None


class TestAcknowledgeRequest:
    """Tests for AcknowledgeRequest model."""

    def test_acknowledge_request_with_note(self) -> None:
        """Test acknowledge request with note."""
        request = AcknowledgeRequest(note="Investigating the issue")
        assert request.note == "Investigating the issue"

    def test_acknowledge_request_without_note(self) -> None:
        """Test acknowledge request without note."""
        request = AcknowledgeRequest()
        assert request.note is None


class TestBulkAcknowledgeRequest:
    """Tests for BulkAcknowledgeRequest model."""

    def test_bulk_acknowledge_request(self) -> None:
        """Test bulk acknowledge request."""
        request = BulkAcknowledgeRequest(
            alert_ids=["alert-1", "alert-2", "alert-3"],
            note="Bulk acknowledgment for maintenance",
        )
        assert len(request.alert_ids) == 3
        assert request.note == "Bulk acknowledgment for maintenance"


class TestAlertHistoryResponse:
    """Tests for AlertHistoryResponse model."""

    def test_alert_history_response(self) -> None:
        """Test alert history response construction."""
        metadata = AlertMetadata(trigger_time="2024-01-01T00:00:00")
        item = AlertHistoryItem(
            id="alert-123",
            alert_config_id="config-456",
            status=AlertStatus.TRIGGERED,
            severity=AlertSeverity.WARNING,
            title="Test Alert",
            triggered_at="2024-01-01T00:00:00",
            metadata=metadata,
        )

        response = AlertHistoryResponse(
            status="success",
            timestamp="2024-01-01T00:00:00",
            total=1,
            page=1,
            page_size=50,
            alerts=[item],
        )

        assert response.status == "success"
        assert response.total == 1
        assert len(response.alerts) == 1


class TestActiveAlertsResponse:
    """Tests for ActiveAlertsResponse model."""

    def test_active_alerts_response(self) -> None:
        """Test active alerts response construction."""
        response = ActiveAlertsResponse(
            status="success",
            timestamp="2024-01-01T00:00:00",
            total=5,
            critical_count=2,
            warning_count=2,
            info_count=1,
            alerts=[],
        )

        assert response.total == 5
        assert response.critical_count == 2
        assert response.warning_count == 2


class TestBulkAcknowledgeResponse:
    """Tests for BulkAcknowledgeResponse model."""

    def test_bulk_acknowledge_response_success(self) -> None:
        """Test bulk acknowledge response with all success."""
        response = BulkAcknowledgeResponse(
            status="success",
            timestamp="2024-01-01T00:00:00",
            total_requested=2,
            total_succeeded=2,
            total_failed=0,
            results=[
                BulkAcknowledgeResult(alert_id="alert-1", success=True),
                BulkAcknowledgeResult(alert_id="alert-2", success=True),
            ],
        )

        assert response.status == "success"
        assert response.total_succeeded == 2
        assert response.total_failed == 0

    def test_bulk_acknowledge_response_partial(self) -> None:
        """Test bulk acknowledge response with partial success."""
        response = BulkAcknowledgeResponse(
            status="partial",
            timestamp="2024-01-01T00:00:00",
            total_requested=2,
            total_succeeded=1,
            total_failed=1,
            results=[
                BulkAcknowledgeResult(alert_id="alert-1", success=True),
                BulkAcknowledgeResult(alert_id="alert-2", success=False, error="Not found"),
            ],
        )

        assert response.status == "partial"
        assert response.total_succeeded == 1
        assert response.total_failed == 1


# =============================================================================
# Integration Tests - API Endpoints
# =============================================================================


class TestGetAlertHistory:
    """Tests for GET /analytics/alerts/history endpoint."""

    @pytest.mark.asyncio
    async def test_history_success(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
        sample_alert_row: MagicMock,
    ) -> None:
        """Test successful alert history retrieval."""
        # Mock count query result
        count_result = MagicMock()
        count_result.scalar.return_value = 1

        # Mock data query result
        data_result = MagicMock()
        data_result.fetchall.return_value = [sample_alert_row]

        mock_db_session.execute.side_effect = [count_result, data_result]

        from api.v1.analytics.alerts import get_alert_history

        response = await get_alert_history(
            page=1,
            page_size=50,
            status_filter=None,
            severity_filter=None,
            alert_config_id=None,
            start_date=None,
            end_date=None,
            user=mock_user,
            db=mock_db_session,
        )

        assert response.status == "success"
        assert response.total == 1
        assert response.page == 1
        assert len(response.alerts) == 1
        assert response.alerts[0].title == "High Error Rate"

    @pytest.mark.asyncio
    async def test_history_with_filters(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
        sample_alert_row: MagicMock,
    ) -> None:
        """Test alert history with filters."""
        count_result = MagicMock()
        count_result.scalar.return_value = 1

        data_result = MagicMock()
        data_result.fetchall.return_value = [sample_alert_row]

        mock_db_session.execute.side_effect = [count_result, data_result]

        from api.v1.analytics.alerts import get_alert_history

        response = await get_alert_history(
            page=1,
            page_size=50,
            status_filter=AlertStatus.TRIGGERED,
            severity_filter=AlertSeverity.WARNING,
            alert_config_id=None,
            start_date=None,
            end_date=None,
            user=mock_user,
            db=mock_db_session,
        )

        assert response.status == "success"
        assert len(response.alerts) == 1

    @pytest.mark.asyncio
    async def test_history_empty(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test alert history with no results."""
        count_result = MagicMock()
        count_result.scalar.return_value = 0

        data_result = MagicMock()
        data_result.fetchall.return_value = []

        mock_db_session.execute.side_effect = [count_result, data_result]

        from api.v1.analytics.alerts import get_alert_history

        response = await get_alert_history(
            page=1,
            page_size=50,
            status_filter=None,
            severity_filter=None,
            alert_config_id=None,
            start_date=None,
            end_date=None,
            user=mock_user,
            db=mock_db_session,
        )

        assert response.status == "success"
        assert response.total == 0
        assert len(response.alerts) == 0


class TestGetActiveAlerts:
    """Tests for GET /analytics/alerts/active endpoint."""

    @pytest.mark.asyncio
    async def test_active_alerts_success(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
        sample_alert_row: MagicMock,
    ) -> None:
        """Test successful active alerts retrieval."""
        data_result = MagicMock()
        data_result.fetchall.return_value = [sample_alert_row]

        mock_db_session.execute.return_value = data_result

        from api.v1.analytics.alerts import get_active_alerts

        response = await get_active_alerts(
            severity_filter=None,
            user=mock_user,
            db=mock_db_session,
        )

        assert response.status == "success"
        assert response.total == 1
        assert response.warning_count == 1
        assert response.critical_count == 0

    @pytest.mark.asyncio
    async def test_active_alerts_with_severity_filter(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
        sample_alert_row: MagicMock,
    ) -> None:
        """Test active alerts with severity filter."""
        sample_alert_row.severity = "critical"
        data_result = MagicMock()
        data_result.fetchall.return_value = [sample_alert_row]

        mock_db_session.execute.return_value = data_result

        from api.v1.analytics.alerts import get_active_alerts

        response = await get_active_alerts(
            severity_filter=AlertSeverity.CRITICAL,
            user=mock_user,
            db=mock_db_session,
        )

        assert response.status == "success"
        assert response.critical_count == 1


class TestAcknowledgeAlert:
    """Tests for POST /analytics/alerts/{id}/acknowledge endpoint."""

    @pytest.mark.asyncio
    async def test_acknowledge_success(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test successful alert acknowledgment."""
        # Mock check query result
        check_result = MagicMock()
        check_row = MagicMock()
        check_row.id = "alert-123"
        check_row.status = "triggered"
        check_result.fetchone.return_value = check_row

        mock_db_session.execute.return_value = check_result

        from api.v1.analytics.alerts import acknowledge_alert

        response = await acknowledge_alert(
            alert_id="alert-123",
            request=AcknowledgeRequest(note="Looking into it"),
            user=mock_user,
            db=mock_db_session,
        )

        assert response.status == "success"
        assert response.alert_id == "alert-123"
        assert response.acknowledged_by == "test-user-123"
        assert response.note == "Looking into it"

    @pytest.mark.asyncio
    async def test_acknowledge_not_found(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test acknowledge alert not found."""
        check_result = MagicMock()
        check_result.fetchone.return_value = None

        mock_db_session.execute.return_value = check_result

        from fastapi import HTTPException

        from api.v1.analytics.alerts import acknowledge_alert

        with pytest.raises(HTTPException) as exc_info:
            await acknowledge_alert(
                alert_id="nonexistent",
                request=AcknowledgeRequest(),
                user=mock_user,
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_acknowledge_already_acknowledged(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test acknowledge already acknowledged alert."""
        check_result = MagicMock()
        check_row = MagicMock()
        check_row.id = "alert-123"
        check_row.status = "acknowledged"
        check_result.fetchone.return_value = check_row

        mock_db_session.execute.return_value = check_result

        from fastapi import HTTPException

        from api.v1.analytics.alerts import acknowledge_alert

        with pytest.raises(HTTPException) as exc_info:
            await acknowledge_alert(
                alert_id="alert-123",
                request=AcknowledgeRequest(),
                user=mock_user,
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 400


class TestResolveAlert:
    """Tests for POST /analytics/alerts/{id}/resolve endpoint."""

    @pytest.mark.asyncio
    async def test_resolve_success(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test successful alert resolution."""
        check_result = MagicMock()
        check_row = MagicMock()
        check_row.id = "alert-123"
        check_row.status = "acknowledged"
        check_result.fetchone.return_value = check_row

        mock_db_session.execute.return_value = check_result

        from api.v1.analytics.alerts import resolve_alert

        response = await resolve_alert(
            alert_id="alert-123",
            request=ResolveRequest(resolution_note="Issue fixed"),
            user=mock_user,
            db=mock_db_session,
        )

        assert response.status == "success"
        assert response.alert_id == "alert-123"
        assert response.resolved_by == "test-user-123"

    @pytest.mark.asyncio
    async def test_resolve_already_resolved(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test resolve already resolved alert."""
        check_result = MagicMock()
        check_row = MagicMock()
        check_row.id = "alert-123"
        check_row.status = "resolved"
        check_result.fetchone.return_value = check_row

        mock_db_session.execute.return_value = check_result

        from fastapi import HTTPException

        from api.v1.analytics.alerts import resolve_alert

        with pytest.raises(HTTPException) as exc_info:
            await resolve_alert(
                alert_id="alert-123",
                request=ResolveRequest(),
                user=mock_user,
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 400


class TestBulkAcknowledge:
    """Tests for POST /analytics/alerts/bulk-acknowledge endpoint."""

    @pytest.mark.asyncio
    async def test_bulk_acknowledge_all_success(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test successful bulk acknowledgment."""

        # Mock for each alert check
        def create_check_result(alert_id: str) -> MagicMock:
            result = MagicMock()
            row = MagicMock()
            row.id = alert_id
            row.status = "triggered"
            result.fetchone.return_value = row
            return result

        mock_db_session.execute.side_effect = [
            create_check_result("alert-1"),
            MagicMock(),  # Update result
            create_check_result("alert-2"),
            MagicMock(),  # Update result
        ]

        from api.v1.analytics.alerts import bulk_acknowledge_alerts

        response = await bulk_acknowledge_alerts(
            request=BulkAcknowledgeRequest(
                alert_ids=["alert-1", "alert-2"],
                note="Bulk ack",
            ),
            user=mock_user,
            db=mock_db_session,
        )

        assert response.status == "success"
        assert response.total_requested == 2
        assert response.total_succeeded == 2
        assert response.total_failed == 0

    @pytest.mark.asyncio
    async def test_bulk_acknowledge_partial(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test partial bulk acknowledgment."""
        # First alert succeeds, second not found
        success_result = MagicMock()
        success_row = MagicMock()
        success_row.id = "alert-1"
        success_row.status = "triggered"
        success_result.fetchone.return_value = success_row

        not_found_result = MagicMock()
        not_found_result.fetchone.return_value = None

        mock_db_session.execute.side_effect = [
            success_result,
            MagicMock(),  # Update result
            not_found_result,
        ]

        from api.v1.analytics.alerts import bulk_acknowledge_alerts

        response = await bulk_acknowledge_alerts(
            request=BulkAcknowledgeRequest(
                alert_ids=["alert-1", "alert-2"],
            ),
            user=mock_user,
            db=mock_db_session,
        )

        assert response.status == "partial"
        assert response.total_succeeded == 1
        assert response.total_failed == 1


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_invalid_date_format(
        self,
        mock_user: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        """Test invalid date format handling."""
        from fastapi import HTTPException

        from api.v1.analytics.alerts import get_alert_history

        with pytest.raises(HTTPException) as exc_info:
            await get_alert_history(
                page=1,
                page_size=50,
                status_filter=None,
                severity_filter=None,
                alert_config_id=None,
                start_date="invalid-date",
                end_date=None,
                user=mock_user,
                db=mock_db_session,
            )

        assert exc_info.value.status_code == 400
        assert "Invalid start_date format" in str(exc_info.value.detail)

    def test_response_models_serialization(self) -> None:
        """Test response models can be serialized."""
        metadata = AlertMetadata(trigger_time="2024-01-01T00:00:00")
        item = AlertHistoryItem(
            id="alert-123",
            alert_config_id="config-456",
            status=AlertStatus.TRIGGERED,
            severity=AlertSeverity.WARNING,
            title="Test Alert",
            triggered_at="2024-01-01T00:00:00",
            metadata=metadata,
        )

        response = AlertHistoryResponse(
            status="success",
            timestamp="2024-01-01T00:00:00",
            total=1,
            page=1,
            page_size=50,
            alerts=[item],
        )

        # Verify can be converted to dict (JSON serializable)
        response_dict = response.model_dump()
        assert response_dict["status"] == "success"
        assert len(response_dict["alerts"]) == 1
