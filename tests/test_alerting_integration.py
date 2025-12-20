"""
Tests for Security Alerting Integration
========================================

Tests the complete alerting pipeline:
- Slack message formatting
- Multi-channel routing
- Alert deduplication
- Severity-based channel selection
"""

import os

import pytest

from security.alerting import (
    AlertChannel,
    AlertingConfig,
    AlertingIntegration,
    get_severity_color,
    get_severity_emoji,
    send_slack_alert,
)
from security.security_monitoring import AlertSeverity, SecurityAlert, SecurityEventType


class TestSeverityHelpers:
    """Test severity helper functions"""

    def test_get_severity_color(self):
        """Test color code mapping"""
        assert get_severity_color(AlertSeverity.CRITICAL) == "#FF0000"
        assert get_severity_color(AlertSeverity.HIGH) == "#FF6B00"
        assert get_severity_color(AlertSeverity.MEDIUM) == "#FFD700"
        assert get_severity_color(AlertSeverity.LOW) == "#00FF00"
        assert get_severity_color(AlertSeverity.INFO) == "#0099FF"

    def test_get_severity_emoji(self):
        """Test emoji mapping"""
        assert get_severity_emoji(AlertSeverity.CRITICAL) == ":rotating_light:"
        assert get_severity_emoji(AlertSeverity.HIGH) == ":warning:"
        assert get_severity_emoji(AlertSeverity.MEDIUM) == ":large_orange_diamond:"
        assert get_severity_emoji(AlertSeverity.LOW) == ":information_source:"
        assert get_severity_emoji(AlertSeverity.INFO) == ":white_check_mark:"


class TestAlertingConfig:
    """Test alerting configuration"""

    def test_default_config(self):
        """Test default configuration values"""
        config = AlertingConfig()
        assert config.slack_webhook_url is None
        assert config.email_enabled is False
        assert config.min_severity_slack == AlertSeverity.MEDIUM
        assert config.min_severity_email == AlertSeverity.HIGH
        assert config.min_severity_pagerduty == AlertSeverity.CRITICAL
        assert config.deduplication_window_minutes == 5

    def test_custom_config(self):
        """Test custom configuration"""
        config = AlertingConfig(
            slack_webhook_url="https://hooks.slack.com/test",
            email_enabled=True,
            email_to=["test@example.com"],
            min_severity_slack=AlertSeverity.LOW,
        )
        assert config.slack_webhook_url == "https://hooks.slack.com/test"
        assert config.email_enabled is True
        assert config.min_severity_slack == AlertSeverity.LOW


class TestAlertingIntegration:
    """Test alerting integration"""

    def setup_method(self):
        """Set up test fixtures"""
        self.config = AlertingConfig(
            slack_webhook_url="https://hooks.slack.com/test",
            email_enabled=True,
            pagerduty_key="test_key",
            custom_webhook_url="https://example.com/webhook",
        )
        self.alerting = AlertingIntegration(self.config)

    def test_initialization(self):
        """Test alerting integration initialization"""
        assert self.alerting.config == self.config
        assert len(self.alerting.stats) > 0
        assert self.alerting.stats["total_alerts"] == 0

    def test_severity_based_channel_selection(self):
        """Test automatic channel selection by severity"""
        # CRITICAL - all channels
        channels = self.alerting._select_channels_by_severity(AlertSeverity.CRITICAL)
        assert AlertChannel.SLACK in channels
        assert AlertChannel.EMAIL in channels
        assert AlertChannel.PAGERDUTY in channels
        assert AlertChannel.WEBHOOK in channels

        # HIGH - slack, email, webhook
        channels = self.alerting._select_channels_by_severity(AlertSeverity.HIGH)
        assert AlertChannel.SLACK in channels
        assert AlertChannel.EMAIL in channels
        assert AlertChannel.PAGERDUTY not in channels

        # MEDIUM - slack, webhook
        channels = self.alerting._select_channels_by_severity(AlertSeverity.MEDIUM)
        assert AlertChannel.SLACK in channels
        assert AlertChannel.EMAIL not in channels
        assert AlertChannel.PAGERDUTY not in channels

    def test_stats_tracking(self):
        """Test statistics tracking"""
        stats = self.alerting.get_stats()
        assert "total_alerts" in stats
        assert "deduplicated" in stats
        assert "slack_sent" in stats
        assert "failures" in stats

    def test_stats_reset(self):
        """Test resetting statistics"""
        self.alerting.stats["total_alerts"] = 10
        self.alerting.reset_stats()
        assert self.alerting.stats["total_alerts"] == 0


class TestAlertDeduplication:
    """Test alert deduplication"""

    def setup_method(self):
        """Set up test fixtures"""
        self.alerting = AlertingIntegration()

    def test_deduplication_same_alert(self):
        """Test that identical alerts are deduplicated"""
        alert1 = SecurityAlert(
            alert_id="test_001",
            title="Test Alert",
            description="Test description",
            severity=AlertSeverity.HIGH,
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
        )

        alert2 = SecurityAlert(
            alert_id="test_002",  # Different ID
            title="Test Alert",  # Same title
            description="Test description",
            severity=AlertSeverity.HIGH,  # Same severity
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,  # Same type
        )

        # First alert should be allowed
        should_send_1 = self.alerting.deduplicator.should_send(alert1)
        assert should_send_1 is True

        # Second alert should be deduplicated
        should_send_2 = self.alerting.deduplicator.should_send(alert2)
        assert should_send_2 is False

    def test_different_alerts_not_deduplicated(self):
        """Test that different alerts are not deduplicated"""
        alert1 = SecurityAlert(
            alert_id="test_001",
            title="Alert 1",
            description="Description 1",
            severity=AlertSeverity.HIGH,
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
        )

        alert2 = SecurityAlert(
            alert_id="test_002",
            title="Alert 2",  # Different title
            description="Description 2",
            severity=AlertSeverity.HIGH,
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
        )

        should_send_1 = self.alerting.deduplicator.should_send(alert1)
        should_send_2 = self.alerting.deduplicator.should_send(alert2)

        assert should_send_1 is True
        assert should_send_2 is True


class TestSlackAlertFormatting:
    """Test Slack alert message formatting"""

    @pytest.mark.asyncio
    async def test_slack_alert_without_webhook(self):
        """Test Slack alert fails gracefully without webhook"""
        alert = SecurityAlert(
            alert_id="test_001",
            title="Test Alert",
            description="Test description",
            severity=AlertSeverity.HIGH,
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
        )

        # Should return False when webhook not configured
        result = await send_slack_alert(alert, webhook_url=None)
        assert result is False

    def test_alert_has_required_fields(self):
        """Test alert model validation"""
        alert = SecurityAlert(
            alert_id="test_001",
            title="Test Alert",
            description="Test description",
            severity=AlertSeverity.HIGH,
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            recommended_action="Take immediate action",
            source_events=["evt_001", "evt_002"],
        )

        assert alert.alert_id == "test_001"
        assert alert.title == "Test Alert"
        assert alert.severity == AlertSeverity.HIGH
        assert len(alert.source_events) == 2
        assert alert.recommended_action == "Take immediate action"


@pytest.mark.integration
class TestFullAlertingPipeline:
    """Integration tests for full alerting pipeline"""

    @pytest.mark.asyncio
    async def test_send_alert_without_config(self):
        """Test sending alert without configuration"""
        alerting = AlertingIntegration()

        alert = SecurityAlert(
            alert_id="test_integration",
            title="Integration Test Alert",
            description="Testing full pipeline",
            severity=AlertSeverity.MEDIUM,
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
        )

        # Should handle gracefully when no channels configured
        results = await alerting.send_alert(alert)
        assert isinstance(results, dict)

    @pytest.mark.asyncio
    async def test_manual_channel_selection(self):
        """Test manual channel selection"""
        alerting = AlertingIntegration()

        alert = SecurityAlert(
            alert_id="test_manual",
            title="Manual Channel Test",
            description="Testing manual channel selection",
            severity=AlertSeverity.LOW,
            event_type=SecurityEventType.SYSTEM_ERROR,
        )

        # Specify channels manually
        channels = [AlertChannel.SLACK]
        results = await alerting.send_alert(alert, channels=channels)

        assert isinstance(results, dict)
        # May be empty if webhook not configured, but should not error


@pytest.mark.skipif(not os.getenv("SLACK_WEBHOOK_URL"), reason="SLACK_WEBHOOK_URL not set")
class TestLiveSlackIntegration:
    """Live integration tests with actual Slack webhook"""

    @pytest.mark.asyncio
    async def test_send_live_slack_alert(self):
        """Test sending actual Slack alert (requires SLACK_WEBHOOK_URL)"""
        alert = SecurityAlert(
            alert_id="live_test",
            title="Live Slack Integration Test",
            description="This is a test alert from the test suite",
            severity=AlertSeverity.INFO,
            event_type=SecurityEventType.SYSTEM_ERROR,
            recommended_action="No action required - this is a test",
        )

        result = await send_slack_alert(alert)
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
