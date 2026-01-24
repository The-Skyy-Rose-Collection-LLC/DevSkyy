# tests/services/analytics/test_alert_notifier.py
"""
Unit tests for AlertNotifier.

Tests cover:
- Multi-channel alert sending (email, Slack, SMS, in-app)
- Severity-based channel routing
- User notification preferences
- Quiet hours handling
- Statistics tracking
- Error handling

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.analytics.alert_notifier import (
    AlertNotification,
    AlertNotifier,
    AlertNotifierConfig,
    AlertNotifierError,
    AlertSeverity,
    InAppNotification,
    NotificationChannel,
    NotificationPreferences,
    NotificationResult,
    NotificationStatus,
    severity_meets_threshold,
)

# =============================================================================
# Fixtures
# =============================================================================


class MockSession:
    """Mock async session for testing."""

    def __init__(self) -> None:
        self.executed: list[tuple[Any, Any]] = []
        self.committed = False

    async def execute(self, query: Any, params: Any = None) -> MagicMock:
        self.executed.append((query, params))
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_result.fetchall.return_value = []
        return mock_result

    async def commit(self) -> None:
        self.committed = True


class MockSessionContextManager:
    """Context manager wrapper for mock session."""

    def __init__(self, session: MockSession) -> None:
        self.session = session

    async def __aenter__(self) -> MockSession:
        return self.session

    async def __aexit__(self, *args: Any) -> None:
        pass


class MockSessionFactory:
    """Mock session factory for testing."""

    def __init__(self, session: MockSession | None = None) -> None:
        self.session = session or MockSession()
        self.call_count = 0

    def __call__(self) -> MockSessionContextManager:
        self.call_count += 1
        return MockSessionContextManager(self.session)


class MockEmailService:
    """Mock email service for testing."""

    def __init__(self, is_configured: bool = True) -> None:
        self._is_configured = is_configured
        self._config = MagicMock()
        self._config.approval_recipients = ["test@example.com"]
        self.send_count = 0

    @property
    def is_configured(self) -> bool:
        return self._is_configured

    async def send_email(
        self,
        to: list[str],
        subject: str,
        html_body: str,
        text_body: str,
        *,
        correlation_id: str | None = None,
    ) -> bool:
        self.send_count += 1
        return True


@pytest.fixture
def mock_session() -> MockSession:
    """Create a mock database session."""
    return MockSession()


@pytest.fixture
def mock_session_factory(mock_session: MockSession) -> MockSessionFactory:
    """Create a mock session factory."""
    return MockSessionFactory(mock_session)


@pytest.fixture
def mock_email_service() -> MockEmailService:
    """Create a mock email service."""
    return MockEmailService()


@pytest.fixture
def config() -> AlertNotifierConfig:
    """Create test configuration."""
    return AlertNotifierConfig(
        slack_webhook_url="https://hooks.slack.com/test",
        slack_default_channel="#test-alerts",
        twilio_account_sid="test_sid",
        twilio_auth_token="test_token",
        twilio_from_number="+15555555555",
    )


@pytest.fixture
def notifier(
    mock_session_factory: MockSessionFactory,
    mock_email_service: MockEmailService,
    config: AlertNotifierConfig,
) -> AlertNotifier:
    """Create an alert notifier for testing."""
    return AlertNotifier(
        mock_session_factory,
        config=config,
        email_service=mock_email_service,
    )


# =============================================================================
# Model Tests
# =============================================================================


class TestAlertNotification:
    """Tests for AlertNotification model."""

    def test_create_notification_with_defaults(self) -> None:
        """Test creating notification with minimal fields."""
        notification = AlertNotification(
            alert_id="alert_123",
            title="Test Alert",
            message="Test message",
            severity=AlertSeverity.HIGH,
        )

        assert notification.id is not None
        assert notification.alert_id == "alert_123"
        assert notification.title == "Test Alert"
        assert notification.message == "Test message"
        assert notification.severity == AlertSeverity.HIGH
        assert notification.channels == []
        assert notification.created_at is not None

    def test_create_notification_with_all_fields(self) -> None:
        """Test creating notification with all fields."""
        user_id = uuid.uuid4()
        notification = AlertNotification(
            alert_id="alert_456",
            title="Full Alert",
            message="Full message",
            severity=AlertSeverity.CRITICAL,
            channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
            user_ids=[user_id],
            team_ids=["team_1"],
            metadata={"key": "value"},
            correlation_id="corr_123",
        )

        assert notification.channels == [NotificationChannel.EMAIL, NotificationChannel.SLACK]
        assert notification.user_ids == [user_id]
        assert notification.metadata["key"] == "value"


class TestNotificationPreferences:
    """Tests for NotificationPreferences model."""

    def test_default_preferences(self) -> None:
        """Test default preference values."""
        prefs = NotificationPreferences()

        assert prefs.email_enabled is True
        assert prefs.slack_enabled is True
        assert prefs.in_app_enabled is True
        assert prefs.sms_enabled is False
        assert prefs.min_severity_email == AlertSeverity.MEDIUM
        assert prefs.min_severity_sms == AlertSeverity.CRITICAL

    def test_custom_preferences(self) -> None:
        """Test custom preference values."""
        user_id = uuid.uuid4()
        prefs = NotificationPreferences(
            user_id=user_id,
            email_enabled=False,
            sms_enabled=True,
            min_severity_email=AlertSeverity.HIGH,
            quiet_hours_start=22,
            quiet_hours_end=6,
            email_address="user@example.com",
            phone_number="+15551234567",
        )

        assert prefs.user_id == user_id
        assert prefs.email_enabled is False
        assert prefs.sms_enabled is True
        assert prefs.quiet_hours_start == 22


class TestInAppNotification:
    """Tests for InAppNotification model."""

    def test_create_in_app_notification(self) -> None:
        """Test creating in-app notification."""
        user_id = uuid.uuid4()
        notification = InAppNotification(
            user_id=user_id,
            alert_id="alert_789",
            title="In-App Alert",
            message="Check your dashboard",
            severity=AlertSeverity.MEDIUM,
        )

        assert notification.user_id == user_id
        assert notification.status == NotificationStatus.PENDING
        assert notification.read_at is None


# =============================================================================
# Severity Tests
# =============================================================================


class TestSeverityMeetsThreshold:
    """Tests for severity_meets_threshold function."""

    def test_critical_meets_all(self) -> None:
        """Critical meets all thresholds."""
        assert severity_meets_threshold(AlertSeverity.CRITICAL, AlertSeverity.CRITICAL)
        assert severity_meets_threshold(AlertSeverity.CRITICAL, AlertSeverity.HIGH)
        assert severity_meets_threshold(AlertSeverity.CRITICAL, AlertSeverity.MEDIUM)
        assert severity_meets_threshold(AlertSeverity.CRITICAL, AlertSeverity.LOW)
        assert severity_meets_threshold(AlertSeverity.CRITICAL, AlertSeverity.INFO)

    def test_low_only_meets_low_and_info(self) -> None:
        """Low only meets low and info thresholds."""
        assert not severity_meets_threshold(AlertSeverity.LOW, AlertSeverity.CRITICAL)
        assert not severity_meets_threshold(AlertSeverity.LOW, AlertSeverity.HIGH)
        assert not severity_meets_threshold(AlertSeverity.LOW, AlertSeverity.MEDIUM)
        assert severity_meets_threshold(AlertSeverity.LOW, AlertSeverity.LOW)
        assert severity_meets_threshold(AlertSeverity.LOW, AlertSeverity.INFO)

    def test_info_only_meets_info(self) -> None:
        """Info only meets info threshold."""
        assert not severity_meets_threshold(AlertSeverity.INFO, AlertSeverity.LOW)
        assert severity_meets_threshold(AlertSeverity.INFO, AlertSeverity.INFO)


# =============================================================================
# AlertNotifier Tests
# =============================================================================


class TestAlertNotifier:
    """Tests for AlertNotifier class."""

    def test_get_channels_for_severity(self, notifier: AlertNotifier) -> None:
        """Test severity-based channel routing."""
        # Critical should include all channels
        critical_channels = notifier.get_channels_for_severity(AlertSeverity.CRITICAL)
        assert NotificationChannel.EMAIL in critical_channels
        assert NotificationChannel.SLACK in critical_channels
        assert NotificationChannel.IN_APP in critical_channels
        assert NotificationChannel.SMS in critical_channels

        # High should not include SMS
        high_channels = notifier.get_channels_for_severity(AlertSeverity.HIGH)
        assert NotificationChannel.EMAIL in high_channels
        assert NotificationChannel.SLACK in high_channels
        assert NotificationChannel.SMS not in high_channels

        # Info should only include in-app
        info_channels = notifier.get_channels_for_severity(AlertSeverity.INFO)
        assert info_channels == [NotificationChannel.IN_APP]

    @pytest.mark.asyncio
    async def test_send_alert_returns_results(self, notifier: AlertNotifier) -> None:
        """Test that send_alert returns results for each channel."""
        with patch.object(notifier, "_send_email", new_callable=AsyncMock, return_value=True):
            with patch.object(notifier, "_send_slack", new_callable=AsyncMock, return_value=True):
                results = await notifier.send_alert(
                    alert_id="alert_test",
                    title="Test Alert",
                    message="Test message",
                    severity=AlertSeverity.HIGH,
                )

        assert len(results) > 0
        assert all(isinstance(r, NotificationResult) for r in results)

    @pytest.mark.asyncio
    async def test_send_alert_with_specific_channels(self, notifier: AlertNotifier) -> None:
        """Test sending to specific channels only."""
        with patch.object(
            notifier, "_send_email", new_callable=AsyncMock, return_value=True
        ) as mock_email:
            results = await notifier.send_alert(
                alert_id="alert_test",
                title="Test Alert",
                message="Test message",
                severity=AlertSeverity.INFO,
                channels=[NotificationChannel.EMAIL],
            )

        mock_email.assert_called_once()
        assert len(results) == 1
        assert results[0].channel == NotificationChannel.EMAIL

    @pytest.mark.asyncio
    async def test_stats_tracking(self, notifier: AlertNotifier) -> None:
        """Test that statistics are tracked correctly."""
        initial_stats = notifier.stats
        assert initial_stats["total_notifications"] == 0

        # Create a mock that updates stats like the real method would
        async def mock_send_slack(notification: AlertNotification) -> bool:
            notifier._stats["slack_sent"] += 1
            return True

        with patch.object(notifier, "_send_slack", side_effect=mock_send_slack):
            await notifier.send_alert(
                alert_id="alert_stats",
                title="Stats Alert",
                message="Testing stats",
                severity=AlertSeverity.MEDIUM,
                channels=[NotificationChannel.SLACK],
            )

        stats = notifier.stats
        assert stats["total_notifications"] == 1
        assert stats["slack_sent"] == 1

    @pytest.mark.asyncio
    async def test_get_user_preferences_returns_defaults(self, notifier: AlertNotifier) -> None:
        """Test that default preferences are returned for unknown user."""
        user_id = uuid.uuid4()
        prefs = await notifier.get_user_preferences(user_id)

        assert prefs.user_id == user_id
        assert prefs.email_enabled is True

    @pytest.mark.asyncio
    async def test_set_user_preferences_caches(self, notifier: AlertNotifier) -> None:
        """Test that set_user_preferences caches preferences."""
        user_id = uuid.uuid4()
        prefs = NotificationPreferences(
            email_enabled=False,
            sms_enabled=True,
        )

        await notifier.set_user_preferences(user_id, prefs)

        # Should be in cache
        cached = await notifier.get_user_preferences(user_id)
        assert cached.email_enabled is False
        assert cached.sms_enabled is True


class TestAlertNotifierChannels:
    """Tests for individual channel implementations."""

    @pytest.mark.asyncio
    async def test_send_email_not_configured(
        self,
        mock_session_factory: MockSessionFactory,
        config: AlertNotifierConfig,
    ) -> None:
        """Test email fails gracefully when not configured."""
        mock_email = MockEmailService(is_configured=False)
        notifier = AlertNotifier(
            mock_session_factory,
            config=config,
            email_service=mock_email,
        )

        notification = AlertNotification(
            alert_id="alert_email",
            title="Email Test",
            message="Test",
            severity=AlertSeverity.HIGH,
        )

        result = await notifier._send_email(notification)
        assert result is False
        assert notifier.stats["email_failed"] == 1

    @pytest.mark.asyncio
    async def test_send_slack_not_configured(
        self,
        mock_session_factory: MockSessionFactory,
        mock_email_service: MockEmailService,
    ) -> None:
        """Test Slack fails gracefully when not configured."""
        config = AlertNotifierConfig()  # No Slack URL
        notifier = AlertNotifier(
            mock_session_factory,
            config=config,
            email_service=mock_email_service,
        )

        notification = AlertNotification(
            alert_id="alert_slack",
            title="Slack Test",
            message="Test",
            severity=AlertSeverity.HIGH,
        )

        result = await notifier._send_slack(notification)
        assert result is False
        assert notifier.stats["slack_failed"] == 1

    @pytest.mark.asyncio
    async def test_send_sms_not_configured(
        self,
        mock_session_factory: MockSessionFactory,
        mock_email_service: MockEmailService,
    ) -> None:
        """Test SMS fails gracefully when not configured."""
        config = AlertNotifierConfig()  # No Twilio config
        notifier = AlertNotifier(
            mock_session_factory,
            config=config,
            email_service=mock_email_service,
        )

        notification = AlertNotification(
            alert_id="alert_sms",
            title="SMS Test",
            message="Test",
            severity=AlertSeverity.CRITICAL,
        )

        result = await notifier._send_sms(notification, to="+15551234567")
        assert result is False
        assert notifier.stats["sms_failed"] == 1

    @pytest.mark.asyncio
    async def test_send_sms_no_phone(self, notifier: AlertNotifier) -> None:
        """Test SMS fails when no phone number provided."""
        notification = AlertNotification(
            alert_id="alert_sms_nophone",
            title="SMS Test",
            message="Test",
            severity=AlertSeverity.CRITICAL,
        )

        result = await notifier._send_sms(notification, to=None)
        assert result is False

    @pytest.mark.asyncio
    async def test_store_in_app_no_session(
        self,
        mock_email_service: MockEmailService,
        config: AlertNotifierConfig,
    ) -> None:
        """Test in-app notification fails when no session factory."""
        notifier = AlertNotifier(
            None,  # No session factory
            config=config,
            email_service=mock_email_service,
        )

        notification = AlertNotification(
            alert_id="alert_inapp",
            title="In-App Test",
            message="Test",
            severity=AlertSeverity.LOW,
        )

        result = await notifier._store_in_app_notification(notification, uuid.uuid4())
        assert result is False
        assert notifier.stats["in_app_failed"] == 1


class TestQuietHours:
    """Tests for quiet hours functionality."""

    def test_not_in_quiet_hours_when_not_set(self, notifier: AlertNotifier) -> None:
        """Test returns False when quiet hours not set."""
        prefs = NotificationPreferences()
        assert notifier._is_in_quiet_hours(prefs) is False

    def test_in_quiet_hours_normal_range(self, notifier: AlertNotifier) -> None:
        """Test quiet hours with normal range (e.g., 9-17)."""
        prefs = NotificationPreferences(
            quiet_hours_start=9,
            quiet_hours_end=17,
        )

        # Mock current hour to be within range
        with patch("services.analytics.alert_notifier.datetime") as mock_dt:
            mock_now = MagicMock()
            mock_now.hour = 12
            mock_dt.now.return_value = mock_now
            assert notifier._is_in_quiet_hours(prefs) is True

            mock_now.hour = 20
            mock_dt.now.return_value = mock_now
            assert notifier._is_in_quiet_hours(prefs) is False

    def test_in_quiet_hours_overnight_range(self, notifier: AlertNotifier) -> None:
        """Test quiet hours with overnight range (e.g., 22-06)."""
        prefs = NotificationPreferences(
            quiet_hours_start=22,
            quiet_hours_end=6,
        )

        # Mock current hour
        with patch("services.analytics.alert_notifier.datetime") as mock_dt:
            mock_now = MagicMock()
            mock_now.hour = 23
            mock_dt.now.return_value = mock_now
            assert notifier._is_in_quiet_hours(prefs) is True

            mock_now.hour = 3
            mock_dt.now.return_value = mock_now
            assert notifier._is_in_quiet_hours(prefs) is True

            mock_now.hour = 12
            mock_dt.now.return_value = mock_now
            assert notifier._is_in_quiet_hours(prefs) is False


class TestAlertNotifierError:
    """Tests for AlertNotifierError."""

    def test_error_creation(self) -> None:
        """Test creating an AlertNotifierError."""
        error = AlertNotifierError(
            "Test error",
            channel=NotificationChannel.SLACK,
            correlation_id="corr_123",
            context={"key": "value"},
        )

        assert "Test error" in str(error)
        assert error.context["channel"] == "slack"
        assert error.context["key"] == "value"


class TestSendAlertToUsers:
    """Tests for send_alert_to_users functionality."""

    @pytest.mark.asyncio
    async def test_send_to_multiple_users(self, notifier: AlertNotifier) -> None:
        """Test sending alerts to multiple users."""
        user1 = uuid.uuid4()
        user2 = uuid.uuid4()

        with patch.object(notifier, "_send_to_user", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = [
                NotificationResult(channel=NotificationChannel.IN_APP, success=True)
            ]

            results = await notifier.send_alert_to_users(
                alert_id="alert_multi",
                title="Multi User Alert",
                message="Test",
                severity=AlertSeverity.MEDIUM,
                user_ids=[user1, user2],
            )

        assert mock_send.call_count == 2
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_respects_user_preferences(self, notifier: AlertNotifier) -> None:
        """Test that user preferences are respected."""
        user_id = uuid.uuid4()

        # Set preferences to disable email
        prefs = NotificationPreferences(
            email_enabled=False,
            slack_enabled=True,
            in_app_enabled=True,
            email_address="test@example.com",
        )
        await notifier.set_user_preferences(user_id, prefs)

        channels = notifier._get_channels_for_user(
            AlertSeverity.HIGH, prefs, respect_preferences=True
        )

        assert NotificationChannel.EMAIL not in channels
        assert NotificationChannel.SLACK in channels

    @pytest.mark.asyncio
    async def test_ignores_preferences_when_disabled(self, notifier: AlertNotifier) -> None:
        """Test that preferences are ignored when respect_preferences=False."""
        prefs = NotificationPreferences(
            email_enabled=False,
            slack_enabled=False,
        )

        channels = notifier._get_channels_for_user(
            AlertSeverity.HIGH, prefs, respect_preferences=False
        )

        # Should use default channels for HIGH severity
        assert NotificationChannel.EMAIL in channels
        assert NotificationChannel.SLACK in channels


class TestAlertNotifierConfig:
    """Tests for AlertNotifierConfig."""

    def test_from_env_defaults(self) -> None:
        """Test config loads defaults when env vars not set."""
        with patch.dict("os.environ", {}, clear=True):
            config = AlertNotifierConfig.from_env()

        assert config.slack_webhook_url == ""
        assert config.slack_default_channel == "#alerts"
        assert config.slack_configured is False
        assert config.sms_configured is False

    def test_slack_configured(self) -> None:
        """Test slack_configured property."""
        config = AlertNotifierConfig(slack_webhook_url="https://hooks.slack.com/test")
        assert config.slack_configured is True

        config = AlertNotifierConfig()
        assert config.slack_configured is False

    def test_sms_configured(self) -> None:
        """Test sms_configured property."""
        config = AlertNotifierConfig(
            twilio_account_sid="sid",
            twilio_auth_token="token",
            twilio_from_number="+15555555555",
        )
        assert config.sms_configured is True

        config = AlertNotifierConfig(twilio_account_sid="sid")
        assert config.sms_configured is False
