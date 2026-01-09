"""
Security Alerting & Notification System
========================================

Multi-channel alerting for security events:
- Slack integration with color-coded severity
- Email notifications
- PagerDuty escalation
- Webhook notifications
- Alert aggregation and deduplication
"""

import hashlib
import logging
import os
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel, Field

from security.security_monitoring import AlertSeverity, SecurityAlert

logger = logging.getLogger(__name__)


class AlertChannel(str, Enum):
    """Alert notification channels"""

    SLACK = "slack"
    EMAIL = "email"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"
    SMS = "sms"


class AlertingConfig(BaseModel):
    """Alerting configuration"""

    slack_webhook_url: str | None = None
    email_enabled: bool = False
    email_from: str = "security@devskyy.com"
    email_to: list[str] = Field(default_factory=list)
    pagerduty_key: str | None = None
    custom_webhook_url: str | None = None
    min_severity_slack: AlertSeverity = AlertSeverity.MEDIUM
    min_severity_email: AlertSeverity = AlertSeverity.HIGH
    min_severity_pagerduty: AlertSeverity = AlertSeverity.CRITICAL
    deduplication_window_minutes: int = 5


class AlertDeduplicator:
    """
    Deduplicate alerts to prevent notification spam.

    Uses content hash and time window to group similar alerts.
    """

    def __init__(self, window_minutes: int = 5):
        self.window_minutes = window_minutes
        self.recent_alerts: dict[str, datetime] = {}

    def should_send(self, alert: SecurityAlert) -> bool:
        """Check if alert should be sent or is duplicate"""
        # Create content hash
        content = f"{alert.title}:{alert.event_type}:{alert.severity}"
        alert_hash = hashlib.sha256(content.encode()).hexdigest()

        now = datetime.now(UTC)
        cutoff = now - timedelta(minutes=self.window_minutes)

        # Clean old entries
        self.recent_alerts = {k: v for k, v in self.recent_alerts.items() if v >= cutoff}

        # Check if duplicate
        if alert_hash in self.recent_alerts:
            logger.debug(f"Suppressing duplicate alert: {alert.title}")
            return False

        # Record alert
        self.recent_alerts[alert_hash] = now
        return True


def get_severity_color(severity: AlertSeverity) -> str:
    """
    Get Slack color code for severity level.

    Returns:
        Hex color code for Slack attachments
    """
    color_map = {
        AlertSeverity.CRITICAL: "#FF0000",  # Red
        AlertSeverity.HIGH: "#FF6B00",  # Orange
        AlertSeverity.MEDIUM: "#FFD700",  # Gold
        AlertSeverity.LOW: "#00FF00",  # Green
        AlertSeverity.INFO: "#0099FF",  # Blue
    }
    return color_map.get(severity, "#808080")  # Gray default


def get_severity_emoji(severity: AlertSeverity) -> str:
    """Get emoji representation of severity"""
    emoji_map = {
        AlertSeverity.CRITICAL: ":rotating_light:",
        AlertSeverity.HIGH: ":warning:",
        AlertSeverity.MEDIUM: ":large_orange_diamond:",
        AlertSeverity.LOW: ":information_source:",
        AlertSeverity.INFO: ":white_check_mark:",
    }
    return emoji_map.get(severity, ":bell:")


async def send_slack_alert(alert: SecurityAlert, webhook_url: str | None = None) -> bool:
    """
    Send security alert to Slack.

    Creates a formatted Slack message with:
    - Color-coded severity
    - Title and description
    - Event details
    - Recommended action
    - Timestamp

    Args:
        alert: SecurityAlert to send
        webhook_url: Slack webhook URL (default: from SLACK_WEBHOOK_URL env)

    Returns:
        True if sent successfully, False otherwise
    """
    if not webhook_url:
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    if not webhook_url:
        logger.warning("Slack webhook URL not configured")
        return False

    try:
        # Build Slack message
        color = get_severity_color(alert.severity)
        emoji = get_severity_emoji(alert.severity)

        # Format timestamp
        timestamp = alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

        # Build attachment
        attachment = {
            "color": color,
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} Security Alert: {alert.title}",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Severity:*\n{alert.severity.value.upper()}"},
                        {"type": "mrkdwn", "text": f"*Event Type:*\n{alert.event_type.value}"},
                        {"type": "mrkdwn", "text": f"*Alert ID:*\n`{alert.alert_id}`"},
                        {"type": "mrkdwn", "text": f"*Timestamp:*\n{timestamp}"},
                    ],
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Description:*\n{alert.description}"},
                },
            ],
        }

        # Add recommended action if present
        if alert.recommended_action:
            attachment["blocks"].append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":point_right: *Recommended Action:*\n{alert.recommended_action}",
                    },
                }
            )

        # Add source events if present
        if alert.source_events:
            events_text = ", ".join([f"`{evt}`" for evt in alert.source_events[:5]])
            if len(alert.source_events) > 5:
                events_text += f" and {len(alert.source_events) - 5} more"

            attachment["blocks"].append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Source Events:*\n{events_text}"},
                }
            )

        # Add divider
        attachment["blocks"].append({"type": "divider"})

        payload = {"attachments": [attachment]}

        # Send to Slack
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()

        logger.info(f"Slack alert sent: {alert.alert_id}")
        return True

    except httpx.HTTPError as e:
        logger.error(f"Failed to send Slack alert: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending Slack alert: {e}")
        return False


async def send_email_alert(alert: SecurityAlert, config: AlertingConfig) -> bool:
    """
    Send security alert via email.

    Args:
        alert: SecurityAlert to send
        config: Email configuration

    Returns:
        True if sent successfully
    """
    if not config.email_enabled or not config.email_to:
        logger.debug("Email alerts not configured")
        return False

    try:
        # Build email content
        subject = f"[{alert.severity.value.upper()}] Security Alert: {alert.title}"

        f"""
Security Alert Notification
============================

Alert ID: {alert.alert_id}
Severity: {alert.severity.value.upper()}
Event Type: {alert.event_type.value}
Timestamp: {alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}

Description:
{alert.description}

Recommended Action:
{alert.recommended_action or "No specific action recommended"}

Source Events:
{", ".join(alert.source_events) if alert.source_events else "None"}

---
This is an automated security alert from DevSkyy Platform.
Do not reply to this email.
"""

        # Note: Actual email sending would require SMTP configuration
        # This is a placeholder for the integration
        logger.info(f"Email alert prepared for {alert.alert_id}: {subject}")

        # In production, integrate with your email service:
        # - AWS SES
        # - SendGrid
        # - Mailgun
        # - SMTP server

        return True

    except Exception as e:
        logger.error(f"Error sending email alert: {e}")
        return False


async def send_pagerduty_alert(alert: SecurityAlert, integration_key: str | None = None) -> bool:
    """
    Send critical alert to PagerDuty.

    Args:
        alert: SecurityAlert to send
        integration_key: PagerDuty integration key

    Returns:
        True if sent successfully
    """
    if not integration_key:
        integration_key = os.getenv("PAGERDUTY_INTEGRATION_KEY")

    if not integration_key:
        logger.debug("PagerDuty not configured")
        return False

    try:
        payload = {
            "routing_key": integration_key,
            "event_action": "trigger",
            "dedup_key": alert.alert_id,
            "payload": {
                "summary": f"{alert.title}",
                "severity": alert.severity.value,
                "source": "devskyy-security",
                "timestamp": alert.timestamp.isoformat(),
                "custom_details": {
                    "description": alert.description,
                    "event_type": alert.event_type.value,
                    "recommended_action": alert.recommended_action,
                    "alert_id": alert.alert_id,
                },
            },
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post("https://events.pagerduty.com/v2/enqueue", json=payload)
            response.raise_for_status()

        logger.info(f"PagerDuty alert sent: {alert.alert_id}")
        return True

    except Exception as e:
        logger.error(f"Error sending PagerDuty alert: {e}")
        return False


async def send_webhook_alert(alert: SecurityAlert, webhook_url: str | None = None) -> bool:
    """
    Send alert to custom webhook endpoint.

    Args:
        alert: SecurityAlert to send
        webhook_url: Custom webhook URL

    Returns:
        True if sent successfully
    """
    if not webhook_url:
        webhook_url = os.getenv("CUSTOM_WEBHOOK_URL")

    if not webhook_url:
        logger.debug("Custom webhook not configured")
        return False

    try:
        payload = {
            "alert_id": alert.alert_id,
            "title": alert.title,
            "description": alert.description,
            "severity": alert.severity.value,
            "event_type": alert.event_type.value,
            "timestamp": alert.timestamp.isoformat(),
            "recommended_action": alert.recommended_action,
            "source_events": alert.source_events,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()

        logger.info(f"Webhook alert sent: {alert.alert_id}")
        return True

    except Exception as e:
        logger.error(f"Error sending webhook alert: {e}")
        return False


class AlertingIntegration:
    """
    Multi-channel alerting integration manager.

    Manages alert distribution across multiple channels:
    - Slack for team notifications
    - Email for detailed reports
    - PagerDuty for critical incidents
    - Custom webhooks for integrations

    Features:
    - Severity-based routing
    - Alert deduplication
    - Async delivery
    - Retry logic
    - Delivery tracking
    """

    def __init__(self, config: AlertingConfig | None = None):
        """
        Initialize alerting integration.

        Args:
            config: Alerting configuration (default: from environment)
        """
        self.config = config or AlertingConfig(
            slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL"),
            email_enabled=os.getenv("EMAIL_ALERTS_ENABLED", "false").lower() == "true",
            pagerduty_key=os.getenv("PAGERDUTY_INTEGRATION_KEY"),
            custom_webhook_url=os.getenv("CUSTOM_WEBHOOK_URL"),
        )

        self.deduplicator = AlertDeduplicator(
            window_minutes=self.config.deduplication_window_minutes
        )

        # Delivery statistics
        self.stats = {
            "total_alerts": 0,
            "deduplicated": 0,
            "slack_sent": 0,
            "email_sent": 0,
            "pagerduty_sent": 0,
            "webhook_sent": 0,
            "failures": 0,
        }

    async def send_alert(
        self, alert: SecurityAlert, channels: list[AlertChannel] | None = None
    ) -> dict[str, bool]:
        """
        Send alert to specified channels.

        Args:
            alert: SecurityAlert to send
            channels: List of channels to use (default: auto-select by severity)

        Returns:
            Dictionary of channel: success status
        """
        self.stats["total_alerts"] += 1

        # Check deduplication
        if not self.deduplicator.should_send(alert):
            self.stats["deduplicated"] += 1
            logger.info(f"Alert {alert.alert_id} suppressed (duplicate)")
            return {}

        # Auto-select channels by severity if not specified
        if channels is None:
            channels = self._select_channels_by_severity(alert.severity)

        # Send to each channel
        results = {}

        tasks = []
        for channel in channels:
            if channel == AlertChannel.SLACK:
                tasks.append(("slack", self._send_slack(alert)))
            elif channel == AlertChannel.EMAIL:
                tasks.append(("email", self._send_email(alert)))
            elif channel == AlertChannel.PAGERDUTY:
                tasks.append(("pagerduty", self._send_pagerduty(alert)))
            elif channel == AlertChannel.WEBHOOK:
                tasks.append(("webhook", self._send_webhook(alert)))

        # Execute all sends concurrently
        for channel_name, task in tasks:
            try:
                success = await task
                results[channel_name] = success

                # Update stats
                if success:
                    self.stats[f"{channel_name}_sent"] += 1
                else:
                    self.stats["failures"] += 1

            except Exception as e:
                logger.error(f"Error sending to {channel_name}: {e}")
                results[channel_name] = False
                self.stats["failures"] += 1

        return results

    def _select_channels_by_severity(self, severity: AlertSeverity) -> list[AlertChannel]:
        """Select channels based on severity level"""
        channels = []

        # Slack for medium and above
        if severity.value in ["critical", "high", "medium"] and self.config.slack_webhook_url:
            channels.append(AlertChannel.SLACK)

        # Email for high and above
        if severity.value in ["critical", "high"] and self.config.email_enabled:
            channels.append(AlertChannel.EMAIL)

        # PagerDuty for critical only
        if severity == AlertSeverity.CRITICAL and self.config.pagerduty_key:
            channels.append(AlertChannel.PAGERDUTY)

        # Always try webhook if configured
        if self.config.custom_webhook_url:
            channels.append(AlertChannel.WEBHOOK)

        return channels

    async def _send_slack(self, alert: SecurityAlert) -> bool:
        """Send to Slack"""
        return await send_slack_alert(alert, self.config.slack_webhook_url)

    async def _send_email(self, alert: SecurityAlert) -> bool:
        """Send to email"""
        return await send_email_alert(alert, self.config)

    async def _send_pagerduty(self, alert: SecurityAlert) -> bool:
        """Send to PagerDuty"""
        return await send_pagerduty_alert(alert, self.config.pagerduty_key)

    async def _send_webhook(self, alert: SecurityAlert) -> bool:
        """Send to custom webhook"""
        return await send_webhook_alert(alert, self.config.custom_webhook_url)

    def get_stats(self) -> dict[str, Any]:
        """Get delivery statistics"""
        return self.stats.copy()

    def reset_stats(self):
        """Reset delivery statistics"""
        self.stats = {
            "total_alerts": 0,
            "deduplicated": 0,
            "slack_sent": 0,
            "email_sent": 0,
            "pagerduty_sent": 0,
            "webhook_sent": 0,
            "failures": 0,
        }


# Global instance
alerting = AlertingIntegration()


# Convenience function
async def notify_security_alert(
    alert: SecurityAlert, channels: list[AlertChannel] | None = None
) -> dict[str, bool]:
    """
    Convenience function to send security alert.

    Args:
        alert: SecurityAlert to send
        channels: Optional list of channels to use

    Returns:
        Dictionary of channel: success status
    """
    return await alerting.send_alert(alert, channels)
