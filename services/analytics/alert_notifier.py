# services/analytics/alert_notifier.py
"""
Alert Notification Service for DevSkyy Analytics.

Multi-channel notification service for sending alerts via email, Slack, SMS, and in-app.
Supports user preferences, severity-based routing, and quiet hours.

Features:
- Multi-channel support: email, Slack, SMS, in-app
- Severity-based channel routing
- User notification preferences
- Quiet hours support
- Statistics tracking
- Correlation ID tracking for debugging

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

import httpx
from pydantic import BaseModel, Field

from errors.production_errors import (
    DevSkyError,
    DevSkyErrorCode,
    DevSkyErrorSeverity,
)

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

SEVERITY_ORDER = ["info", "low", "medium", "high", "critical"]


# =============================================================================
# Enums
# =============================================================================


class NotificationChannel(str, Enum):
    """Notification delivery channels."""

    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    IN_APP = "in_app"


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationStatus(str, Enum):
    """Notification status values."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    READ = "read"


# =============================================================================
# Models
# =============================================================================


class AlertNotifierConfig(BaseModel):
    """Configuration for alert notifier."""

    slack_webhook_url: str = ""
    slack_default_channel: str = "#alerts"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""

    @classmethod
    def from_env(cls) -> AlertNotifierConfig:
        """Load configuration from environment variables."""
        return cls(
            slack_webhook_url=os.environ.get("SLACK_WEBHOOK_URL", ""),
            slack_default_channel=os.environ.get("SLACK_DEFAULT_CHANNEL", "#alerts"),
            twilio_account_sid=os.environ.get("TWILIO_ACCOUNT_SID", ""),
            twilio_auth_token=os.environ.get("TWILIO_AUTH_TOKEN", ""),
            twilio_from_number=os.environ.get("TWILIO_FROM_NUMBER", ""),
        )

    @property
    def slack_configured(self) -> bool:
        """Check if Slack is configured."""
        return bool(self.slack_webhook_url)

    @property
    def sms_configured(self) -> bool:
        """Check if SMS is configured."""
        return bool(self.twilio_account_sid and self.twilio_auth_token and self.twilio_from_number)


class AlertNotification(BaseModel):
    """Model for an alert notification."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    alert_id: str
    title: str
    message: str
    severity: AlertSeverity
    channels: list[NotificationChannel] = Field(default_factory=list)
    user_ids: list[uuid.UUID] = Field(default_factory=list)
    team_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        """Pydantic config."""

        use_enum_values = True


class NotificationPreferences(BaseModel):
    """User notification preferences."""

    user_id: uuid.UUID | None = None
    email_enabled: bool = True
    slack_enabled: bool = True
    sms_enabled: bool = False
    in_app_enabled: bool = True
    min_severity_email: AlertSeverity = AlertSeverity.MEDIUM
    min_severity_slack: AlertSeverity = AlertSeverity.MEDIUM
    min_severity_sms: AlertSeverity = AlertSeverity.CRITICAL
    min_severity_in_app: AlertSeverity = AlertSeverity.INFO
    quiet_hours_start: int | None = None  # 0-23
    quiet_hours_end: int | None = None  # 0-23
    email_address: str | None = None
    phone_number: str | None = None
    slack_user_id: str | None = None

    class Config:
        """Pydantic config."""

        use_enum_values = True


class InAppNotification(BaseModel):
    """Model for an in-app notification."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    alert_id: str
    title: str
    message: str
    severity: AlertSeverity = AlertSeverity.INFO
    status: NotificationStatus = NotificationStatus.PENDING
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    read_at: datetime | None = None

    class Config:
        """Pydantic config."""

        use_enum_values = True


class NotificationResult(BaseModel):
    """Result of sending a notification."""

    channel: NotificationChannel
    success: bool
    error_message: str | None = None
    sent_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        """Pydantic config."""

        use_enum_values = True


# =============================================================================
# Errors
# =============================================================================


class AlertNotifierError(DevSkyError):
    """Error raised by the alert notifier."""

    def __init__(
        self,
        message: str,
        *,
        channel: NotificationChannel | None = None,
        correlation_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        ctx = context or {}
        if channel:
            ctx["channel"] = channel.value if isinstance(channel, NotificationChannel) else channel
        super().__init__(
            message,
            code=DevSkyErrorCode.INTERNAL_ERROR,
            severity=DevSkyErrorSeverity.ERROR,
            correlation_id=correlation_id,
            context=ctx,
        )


# =============================================================================
# Helper Functions
# =============================================================================


def severity_meets_threshold(
    severity: AlertSeverity | str,
    threshold: AlertSeverity | str,
) -> bool:
    """Check if severity meets or exceeds threshold."""
    sev = severity.value if isinstance(severity, AlertSeverity) else severity
    thresh = threshold.value if isinstance(threshold, AlertSeverity) else threshold

    sev_idx = SEVERITY_ORDER.index(sev) if sev in SEVERITY_ORDER else 0
    thresh_idx = SEVERITY_ORDER.index(thresh) if thresh in SEVERITY_ORDER else 0

    return sev_idx >= thresh_idx


# =============================================================================
# Alert Notifier
# =============================================================================


class AlertNotifier:
    """
    Multi-channel alert notification service.

    Features:
    - Email via existing EmailNotificationService
    - Slack webhook integration
    - SMS via Twilio
    - In-app notifications stored in PostgreSQL
    - Severity-based channel routing
    - User preferences support
    """

    def __init__(
        self,
        session_factory: Callable[[], Any] | None = None,
        *,
        config: AlertNotifierConfig | None = None,
        email_service: Any | None = None,
    ) -> None:
        """
        Initialize the alert notifier.

        Args:
            session_factory: Factory for creating database sessions.
            config: Notifier configuration.
            email_service: Optional email service instance.
        """
        self._session_factory = session_factory
        self._config = config or AlertNotifierConfig.from_env()
        self._email_service = email_service
        self._http_client: httpx.AsyncClient | None = None
        self._preferences_cache: dict[uuid.UUID, NotificationPreferences] = {}
        self._stats = {
            "total_notifications": 0,
            "email_sent": 0,
            "email_failed": 0,
            "slack_sent": 0,
            "slack_failed": 0,
            "sms_sent": 0,
            "sms_failed": 0,
            "in_app_sent": 0,
            "in_app_failed": 0,
        }

    @property
    def stats(self) -> dict[str, Any]:
        """Get current notifier statistics."""
        return {**self._stats}

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    def get_channels_for_severity(
        self,
        severity: AlertSeverity | str,
    ) -> list[NotificationChannel]:
        """Get default channels based on severity."""
        sev = severity.value if isinstance(severity, AlertSeverity) else severity

        if sev == "critical":
            return [
                NotificationChannel.EMAIL,
                NotificationChannel.SLACK,
                NotificationChannel.SMS,
                NotificationChannel.IN_APP,
            ]
        elif sev == "high":
            return [
                NotificationChannel.EMAIL,
                NotificationChannel.SLACK,
                NotificationChannel.IN_APP,
            ]
        elif sev == "medium":
            return [
                NotificationChannel.SLACK,
                NotificationChannel.IN_APP,
            ]
        elif sev == "low":
            return [NotificationChannel.IN_APP]
        else:  # info
            return [NotificationChannel.IN_APP]

    async def send_alert(
        self,
        alert_id: str,
        title: str,
        message: str,
        severity: AlertSeverity | str,
        *,
        channels: list[NotificationChannel] | None = None,
        correlation_id: str | None = None,
    ) -> list[NotificationResult]:
        """
        Send an alert notification.

        Args:
            alert_id: Unique alert identifier.
            title: Alert title.
            message: Alert message.
            severity: Alert severity.
            channels: Specific channels to use (optional).
            correlation_id: Correlation ID for tracing.

        Returns:
            List of notification results.
        """
        sev = AlertSeverity(severity) if isinstance(severity, str) else severity

        notification = AlertNotification(
            alert_id=alert_id,
            title=title,
            message=message,
            severity=sev,
            channels=channels or self.get_channels_for_severity(sev),
            correlation_id=correlation_id,
        )

        results: list[NotificationResult] = []
        self._stats["total_notifications"] += 1

        for channel in notification.channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    success = await self._send_email(notification)
                elif channel == NotificationChannel.SLACK:
                    success = await self._send_slack(notification)
                elif channel == NotificationChannel.SMS:
                    success = await self._send_sms(notification, to=None)
                elif channel == NotificationChannel.IN_APP:
                    success = await self._store_in_app_notification(
                        notification,
                        user_id=None,
                    )
                else:
                    success = False

                results.append(
                    NotificationResult(
                        channel=channel,
                        success=success,
                    )
                )
            except Exception as e:
                logger.exception("Error sending %s notification: %s", channel.value, e)
                results.append(
                    NotificationResult(
                        channel=channel,
                        success=False,
                        error_message=str(e),
                    )
                )

        return results

    async def send_alert_to_users(
        self,
        alert_id: str,
        title: str,
        message: str,
        severity: AlertSeverity | str,
        user_ids: list[uuid.UUID],
        *,
        respect_preferences: bool = True,
        correlation_id: str | None = None,
    ) -> list[NotificationResult]:
        """
        Send alert to specific users.

        Args:
            alert_id: Unique alert identifier.
            title: Alert title.
            message: Alert message.
            severity: Alert severity.
            user_ids: List of user IDs to notify.
            respect_preferences: Whether to respect user preferences.
            correlation_id: Correlation ID for tracing.

        Returns:
            List of notification results.
        """
        results: list[NotificationResult] = []
        sev = AlertSeverity(severity) if isinstance(severity, str) else severity

        notification = AlertNotification(
            alert_id=alert_id,
            title=title,
            message=message,
            severity=sev,
            user_ids=user_ids,
            correlation_id=correlation_id,
        )

        for user_id in user_ids:
            user_results = await self._send_to_user(
                notification,
                user_id,
                respect_preferences=respect_preferences,
            )
            results.extend(user_results)

        return results

    async def _send_to_user(
        self,
        notification: AlertNotification,
        user_id: uuid.UUID,
        *,
        respect_preferences: bool = True,
    ) -> list[NotificationResult]:
        """Send notification to a single user."""
        results: list[NotificationResult] = []
        prefs = await self.get_user_preferences(user_id)

        # Check quiet hours
        if self._is_in_quiet_hours(prefs):
            # Only send in-app during quiet hours
            success = await self._store_in_app_notification(notification, user_id)
            return [NotificationResult(channel=NotificationChannel.IN_APP, success=success)]

        channels = self._get_channels_for_user(
            (
                AlertSeverity(notification.severity)
                if isinstance(notification.severity, str)
                else notification.severity
            ),
            prefs,
            respect_preferences=respect_preferences,
        )

        for channel in channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    success = await self._send_email(notification, to=prefs.email_address)
                elif channel == NotificationChannel.SLACK:
                    success = await self._send_slack(notification)
                elif channel == NotificationChannel.SMS:
                    success = await self._send_sms(notification, to=prefs.phone_number)
                elif channel == NotificationChannel.IN_APP:
                    success = await self._store_in_app_notification(notification, user_id)
                else:
                    success = False

                results.append(NotificationResult(channel=channel, success=success))
            except Exception as e:
                logger.exception("Error sending to user %s via %s: %s", user_id, channel, e)
                results.append(
                    NotificationResult(
                        channel=channel,
                        success=False,
                        error_message=str(e),
                    )
                )

        return results

    def _get_channels_for_user(
        self,
        severity: AlertSeverity,
        prefs: NotificationPreferences,
        *,
        respect_preferences: bool = True,
    ) -> list[NotificationChannel]:
        """Get channels for a user based on severity and preferences."""
        if not respect_preferences:
            return self.get_channels_for_severity(severity)

        channels: list[NotificationChannel] = []
        sev = severity.value if isinstance(severity, AlertSeverity) else severity

        if prefs.email_enabled and severity_meets_threshold(sev, prefs.min_severity_email):
            channels.append(NotificationChannel.EMAIL)

        if prefs.slack_enabled and severity_meets_threshold(sev, prefs.min_severity_slack):
            channels.append(NotificationChannel.SLACK)

        if prefs.sms_enabled and severity_meets_threshold(sev, prefs.min_severity_sms):
            channels.append(NotificationChannel.SMS)

        if prefs.in_app_enabled and severity_meets_threshold(sev, prefs.min_severity_in_app):
            channels.append(NotificationChannel.IN_APP)

        return channels

    def _is_in_quiet_hours(self, prefs: NotificationPreferences) -> bool:
        """Check if currently in quiet hours."""
        if prefs.quiet_hours_start is None or prefs.quiet_hours_end is None:
            return False

        current_hour = datetime.now(UTC).hour

        # Handle overnight quiet hours (e.g., 22-06)
        if prefs.quiet_hours_start > prefs.quiet_hours_end:
            return current_hour >= prefs.quiet_hours_start or current_hour < prefs.quiet_hours_end

        # Normal range (e.g., 09-17)
        return prefs.quiet_hours_start <= current_hour < prefs.quiet_hours_end

    async def _send_email(
        self,
        notification: AlertNotification,
        *,
        to: str | None = None,
    ) -> bool:
        """Send email notification."""
        if not self._email_service or not self._email_service.is_configured:
            self._stats["email_failed"] += 1
            return False

        try:
            recipients = [to] if to else self._email_service._config.approval_recipients

            severity = (
                notification.severity
                if isinstance(notification.severity, str)
                else notification.severity.value
            )
            html_body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: #B76E79; color: white; padding: 20px; text-align: center;">
                    <h1 style="margin: 0;">DevSkyy Alert</h1>
                </div>
                <div style="padding: 20px; background: #f8f9fa;">
                    <h2 style="color: #1A1A1A;">{notification.title}</h2>
                    <p style="color: #666;">{notification.message}</p>
                    <p style="color: #999; font-size: 12px;">
                        Severity: {severity.upper()} | Alert ID: {notification.alert_id}
                    </p>
                </div>
            </div>
            """

            await self._email_service.send_email(
                to=recipients,
                subject=f"[{severity.upper()}] {notification.title}",
                html_body=html_body,
                text_body=f"{notification.title}\n\n{notification.message}",
                correlation_id=notification.correlation_id,
            )
            self._stats["email_sent"] += 1
            return True

        except Exception as e:
            logger.exception("Failed to send email: %s", e)
            self._stats["email_failed"] += 1
            return False

    async def _send_slack(self, notification: AlertNotification) -> bool:
        """Send Slack notification."""
        if not self._config.slack_configured:
            self._stats["slack_failed"] += 1
            return False

        try:
            client = await self._get_http_client()
            severity = (
                notification.severity
                if isinstance(notification.severity, str)
                else notification.severity.value
            )

            # Color based on severity
            colors = {
                "critical": "#dc3545",
                "high": "#fd7e14",
                "medium": "#ffc107",
                "low": "#17a2b8",
                "info": "#6c757d",
            }

            payload = {
                "channel": self._config.slack_default_channel,
                "attachments": [
                    {
                        "color": colors.get(severity, "#6c757d"),
                        "title": notification.title,
                        "text": notification.message,
                        "fields": [
                            {"title": "Severity", "value": severity.upper(), "short": True},
                            {"title": "Alert ID", "value": notification.alert_id, "short": True},
                        ],
                        "footer": "DevSkyy Alert System",
                        "ts": int(notification.created_at.timestamp()),
                    }
                ],
            }

            response = await client.post(
                self._config.slack_webhook_url,
                json=payload,
            )
            response.raise_for_status()
            self._stats["slack_sent"] += 1
            return True

        except Exception as e:
            logger.exception("Failed to send Slack notification: %s", e)
            self._stats["slack_failed"] += 1
            return False

    async def _send_sms(
        self,
        notification: AlertNotification,
        *,
        to: str | None,
    ) -> bool:
        """Send SMS notification via Twilio."""
        if not self._config.sms_configured or not to:
            self._stats["sms_failed"] += 1
            return False

        try:
            client = await self._get_http_client()
            severity = (
                notification.severity
                if isinstance(notification.severity, str)
                else notification.severity.value
            )

            message = f"[{severity.upper()}] {notification.title}\n{notification.message[:100]}"

            response = await client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{self._config.twilio_account_sid}/Messages.json",
                data={
                    "To": to,
                    "From": self._config.twilio_from_number,
                    "Body": message,
                },
                auth=(self._config.twilio_account_sid, self._config.twilio_auth_token),
            )
            response.raise_for_status()
            self._stats["sms_sent"] += 1
            return True

        except Exception as e:
            logger.exception("Failed to send SMS: %s", e)
            self._stats["sms_failed"] += 1
            return False

    async def _store_in_app_notification(
        self,
        notification: AlertNotification,
        user_id: uuid.UUID | None,
    ) -> bool:
        """Store in-app notification in database."""
        if not self._session_factory:
            self._stats["in_app_failed"] += 1
            return False

        try:
            from sqlalchemy import text

            # If no user_id, skip (in-app requires a target user)
            if user_id is None:
                self._stats["in_app_sent"] += 1  # Consider it success for broadcast
                return True

            async with self._session_factory() as session:
                severity = (
                    notification.severity
                    if isinstance(notification.severity, str)
                    else notification.severity.value
                )
                await session.execute(
                    text("""
                        INSERT INTO in_app_notifications (
                            id, user_id, alert_id, title, message,
                            severity, status, metadata, created_at
                        ) VALUES (
                            :id, :user_id, :alert_id, :title, :message,
                            :severity, :status, :metadata::jsonb, :created_at
                        )
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "user_id": str(user_id),
                        "alert_id": notification.alert_id,
                        "title": notification.title,
                        "message": notification.message,
                        "severity": severity,
                        "status": NotificationStatus.PENDING.value,
                        "metadata": "{}",
                        "created_at": datetime.now(UTC),
                    },
                )
                await session.commit()

            self._stats["in_app_sent"] += 1
            return True

        except Exception as e:
            logger.exception("Failed to store in-app notification: %s", e)
            self._stats["in_app_failed"] += 1
            return False

    async def get_user_preferences(
        self,
        user_id: uuid.UUID,
    ) -> NotificationPreferences:
        """Get user notification preferences."""
        # Check cache
        if user_id in self._preferences_cache:
            return self._preferences_cache[user_id]

        # Return default preferences
        prefs = NotificationPreferences(user_id=user_id)
        self._preferences_cache[user_id] = prefs
        return prefs

    async def set_user_preferences(
        self,
        user_id: uuid.UUID,
        prefs: NotificationPreferences,
    ) -> None:
        """Set user notification preferences."""
        prefs.user_id = user_id
        self._preferences_cache[user_id] = prefs

    async def get_in_app_notifications(
        self,
        user_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[InAppNotification]:
        """Get in-app notifications for a user."""
        if not self._session_factory:
            return []

        try:
            from sqlalchemy import text

            async with self._session_factory() as session:
                result = await session.execute(
                    text("""
                        SELECT id, user_id, alert_id, title, message,
                               severity, status, metadata, created_at, read_at
                        FROM in_app_notifications
                        WHERE user_id = :user_id
                        ORDER BY created_at DESC
                        LIMIT :limit
                    """),
                    {"user_id": str(user_id), "limit": limit},
                )
                rows = result.fetchall()

                notifications = []
                for row in rows:
                    notifications.append(
                        InAppNotification(
                            id=uuid.UUID(row[0]) if isinstance(row[0], str) else row[0],
                            user_id=uuid.UUID(row[1]) if isinstance(row[1], str) else row[1],
                            alert_id=row[2],
                            title=row[3],
                            message=row[4],
                            severity=AlertSeverity(row[5]) if row[5] else AlertSeverity.INFO,
                            status=(
                                NotificationStatus(row[6]) if row[6] else NotificationStatus.PENDING
                            ),
                            metadata=row[7] if isinstance(row[7], dict) else {},
                            created_at=row[8] if row[8] else datetime.now(UTC),
                            read_at=row[9],
                        )
                    )
                return notifications

        except Exception as e:
            logger.exception("Failed to get in-app notifications: %s", e)
            return []

    async def mark_notification_read(
        self,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """Mark an in-app notification as read."""
        if not self._session_factory:
            return False

        try:
            from sqlalchemy import text

            async with self._session_factory() as session:
                await session.execute(
                    text("""
                        UPDATE in_app_notifications
                        SET status = 'read', read_at = NOW()
                        WHERE id = :id AND user_id = :user_id
                    """),
                    {"id": str(notification_id), "user_id": str(user_id)},
                )
                await session.commit()
            return True

        except Exception as e:
            logger.exception("Failed to mark notification as read: %s", e)
            return False


# =============================================================================
# Module Singleton
# =============================================================================

_alert_notifier: AlertNotifier | None = None


def get_alert_notifier(
    session_factory: Callable[[], Any] | None = None,
) -> AlertNotifier:
    """Get or create the alert notifier singleton."""
    global _alert_notifier
    if _alert_notifier is None:
        _alert_notifier = AlertNotifier(session_factory)
    return _alert_notifier


__all__ = [
    "AlertNotifier",
    "AlertNotifierConfig",
    "AlertNotifierError",
    "AlertNotification",
    "AlertSeverity",
    "InAppNotification",
    "NotificationChannel",
    "NotificationPreferences",
    "NotificationResult",
    "NotificationStatus",
    "get_alert_notifier",
    "severity_meets_threshold",
]
