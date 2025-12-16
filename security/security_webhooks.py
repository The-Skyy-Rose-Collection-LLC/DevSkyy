"""
Security Webhook Integration
============================

Integrates security monitoring with the webhook system to provide
real-time security event notifications.

Features:
- Security event webhooks
- Intrusion detection alerts
- Authentication failure notifications
- Rate limit breach alerts
- Suspicious activity reports
- Compliance violation notifications

Author: DevSkyy Security Team
Version: 1.0.0
"""

import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SecurityEventType(str, Enum):
    """Security-specific webhook event types"""

    # Authentication Events
    AUTH_LOGIN_SUCCESS = "security.auth.login.success"
    AUTH_LOGIN_FAILED = "security.auth.login.failed"
    AUTH_LOGOUT = "security.auth.logout"
    AUTH_MFA_ENABLED = "security.auth.mfa.enabled"
    AUTH_MFA_DISABLED = "security.auth.mfa.disabled"
    AUTH_PASSWORD_CHANGED = "security.auth.password.changed"
    AUTH_ACCOUNT_LOCKED = "security.auth.account.locked"

    # Intrusion Detection
    INTRUSION_DETECTED = "security.intrusion.detected"
    INTRUSION_BLOCKED = "security.intrusion.blocked"
    SUSPICIOUS_ACTIVITY = "security.suspicious.activity"
    BRUTE_FORCE_ATTEMPT = "security.brute_force.attempt"

    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "security.rate_limit.exceeded"
    RATE_LIMIT_WARNING = "security.rate_limit.warning"

    # Data Protection
    DATA_BREACH_DETECTED = "security.data.breach.detected"
    ENCRYPTION_FAILURE = "security.encryption.failure"
    PII_ACCESS = "security.pii.access"
    PII_EXPORT = "security.pii.export"

    # Compliance
    GDPR_REQUEST = "security.gdpr.request"
    GDPR_DELETION = "security.gdpr.deletion"
    COMPLIANCE_VIOLATION = "security.compliance.violation"

    # System Security
    VULNERABILITY_DETECTED = "security.vulnerability.detected"
    SECURITY_UPDATE_REQUIRED = "security.update.required"
    CERTIFICATE_EXPIRING = "security.certificate.expiring"

    # Access Control
    PERMISSION_DENIED = "security.permission.denied"
    ROLE_CHANGED = "security.role.changed"
    PRIVILEGE_ESCALATION = "security.privilege.escalation"


class SecurityEventSeverity(str, Enum):
    """Security event severity levels"""

    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"  # Urgent attention needed
    MEDIUM = "medium"  # Should be addressed soon
    LOW = "low"  # Informational
    INFO = "info"  # General information


class SecurityWebhookEvent(BaseModel):
    """Security webhook event payload"""

    id: str = Field(..., description="Unique event ID")
    type: SecurityEventType = Field(..., description="Event type")
    severity: SecurityEventSeverity = Field(..., description="Event severity")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Event details
    title: str = Field(..., description="Human-readable event title")
    description: str = Field(..., description="Detailed event description")

    # Context
    user_id: str | None = Field(None, description="User ID if applicable")
    ip_address: str | None = Field(None, description="Source IP address")
    user_agent: str | None = Field(None, description="User agent string")
    endpoint: str | None = Field(None, description="API endpoint affected")

    # Additional data
    data: dict[str, Any] = Field(default_factory=dict, description="Event-specific data")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    # Actions
    actions_taken: list[str] = Field(default_factory=list, description="Automated actions taken")
    recommended_actions: list[str] = Field(
        default_factory=list, description="Recommended manual actions"
    )

    # Tracking
    correlation_id: str | None = Field(None, description="Correlation ID for related events")
    alert_id: str | None = Field(None, description="Alert ID if this triggered an alert")


class SecurityWebhookManager:
    """
    Manages security event webhooks

    Integrates with the main webhook system to send security-specific events.
    """

    def __init__(self, webhook_manager=None):
        """
        Initialize security webhook manager

        Args:
            webhook_manager: WebhookManager instance (imported from api.webhooks)
        """
        self.webhook_manager = webhook_manager
        self._event_history: list[SecurityWebhookEvent] = []
        self._max_history = 1000

    async def send_security_event(
        self,
        event_type: SecurityEventType,
        severity: SecurityEventSeverity,
        title: str,
        description: str,
        user_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        endpoint: str | None = None,
        data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        actions_taken: list[str] | None = None,
        recommended_actions: list[str] | None = None,
        correlation_id: str | None = None,
    ) -> list[str] | None:
        """
        Send a security event webhook

        Args:
            event_type: Type of security event
            severity: Event severity level
            title: Human-readable event title
            description: Detailed description
            user_id: User ID if applicable
            ip_address: Source IP address
            user_agent: User agent string
            endpoint: API endpoint affected
            data: Event-specific data
            metadata: Additional metadata
            actions_taken: List of automated actions taken
            recommended_actions: List of recommended manual actions
            correlation_id: Correlation ID for related events

        Returns:
            List of delivery IDs if webhooks were sent, None otherwise
        """
        import secrets

        event = SecurityWebhookEvent(
            id=f"sec_evt_{secrets.token_urlsafe(16)}",
            type=event_type,
            severity=severity,
            title=title,
            description=description,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            data=data or {},
            metadata=metadata or {},
            actions_taken=actions_taken or [],
            recommended_actions=recommended_actions or [],
            correlation_id=correlation_id,
        )

        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # Log the event
        log_level = {
            SecurityEventSeverity.CRITICAL: logging.CRITICAL,
            SecurityEventSeverity.HIGH: logging.ERROR,
            SecurityEventSeverity.MEDIUM: logging.WARNING,
            SecurityEventSeverity.LOW: logging.INFO,
            SecurityEventSeverity.INFO: logging.INFO,
        }.get(severity, logging.INFO)

        logger.log(log_level, f"Security Event: {title} ({event_type.value}) - {description}")

        # Send webhook if manager is available
        if self.webhook_manager:
            try:
                delivery_ids = await self.webhook_manager.publish(
                    event_type=event_type.value,
                    data=event.model_dump(),
                    metadata={"severity": severity.value, "security_event": True},
                )
                return delivery_ids
            except Exception as e:
                logger.error(f"Failed to send security webhook: {e}")
                return None

        return None

    def get_event_history(
        self,
        event_type: SecurityEventType | None = None,
        severity: SecurityEventSeverity | None = None,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[SecurityWebhookEvent]:
        """
        Get security event history with filters

        Args:
            event_type: Filter by event type
            severity: Filter by severity
            user_id: Filter by user ID
            limit: Maximum number of events to return

        Returns:
            List of security events
        """
        events = self._event_history.copy()

        if event_type:
            events = [e for e in events if e.type == event_type]
        if severity:
            events = [e for e in events if e.severity == severity]
        if user_id:
            events = [e for e in events if e.user_id == user_id]

        # Sort by timestamp descending
        events.sort(key=lambda e: e.timestamp, reverse=True)

        return events[:limit]

    def get_critical_events(self, hours: int = 24) -> list[SecurityWebhookEvent]:
        """
        Get critical security events from the last N hours

        Args:
            hours: Number of hours to look back

        Returns:
            List of critical events
        """
        from datetime import timedelta

        cutoff = datetime.now(UTC) - timedelta(hours=hours)

        return [
            e
            for e in self._event_history
            if e.severity == SecurityEventSeverity.CRITICAL and e.timestamp >= cutoff
        ]


# Global instance
security_webhook_manager = SecurityWebhookManager()


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "SecurityEventType",
    "SecurityEventSeverity",
    "SecurityWebhookEvent",
    "SecurityWebhookManager",
    "security_webhook_manager",
]
