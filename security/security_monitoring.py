"""
Security Monitoring & Logging System
=====================================

Comprehensive security monitoring for DevSkyy Platform:
- Security event logging
- Intrusion detection
- Audit trails
- Security metrics
- Real-time alerting
- Threat intelligence
"""

import logging
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SecurityEventType(str, Enum):
    """Types of security events"""

    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    MFA_FAILED = "mfa_failed"

    # Authorization events
    ACCESS_DENIED = "access_denied"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    ROLE_CHANGE = "role_change"

    # Security threats
    BRUTE_FORCE_DETECTED = "brute_force_detected"
    INJECTION_ATTEMPT = "injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    CSRF_ATTEMPT = "csrf_attempt"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

    # Data events
    DATA_ACCESS = "data_access"
    DATA_EXPORT = "data_export"
    DATA_DELETION = "data_deletion"
    PII_ACCESS = "pii_access"

    # System events
    CONFIG_CHANGE = "config_change"
    KEY_ROTATION = "key_rotation"
    CERTIFICATE_EXPIRY = "certificate_expiry"
    SYSTEM_ERROR = "system_error"


class AlertSeverity(str, Enum):
    """Alert severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SecurityEvent(BaseModel):
    """Security event record"""

    event_id: str
    event_type: SecurityEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    severity: AlertSeverity = AlertSeverity.INFO
    user_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    resource: str | None = None
    action: str | None = None
    outcome: str = "success"  # success, failure, blocked
    details: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None


class SecurityAlert(BaseModel):
    """Security alert for notification"""

    alert_id: str
    title: str
    description: str
    severity: AlertSeverity
    event_type: SecurityEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_events: list[str] = Field(default_factory=list)
    recommended_action: str = ""
    is_acknowledged: bool = False
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None


class ThreatIndicator(BaseModel):
    """Threat indicator for detection"""

    indicator_type: str  # ip, user, pattern
    value: str
    threat_score: int  # 0-100
    first_seen: datetime
    last_seen: datetime
    event_count: int = 1
    is_blocked: bool = False


class SecurityMonitor:
    """
    Comprehensive security monitoring system.

    Features:
    - Real-time security event logging
    - Intrusion detection with pattern analysis
    - Automated alerting
    - Threat intelligence tracking
    - Security metrics and reporting
    - Audit trail management
    """

    def __init__(self):
        self.events: list[SecurityEvent] = []
        self.alerts: list[SecurityAlert] = []
        self.threat_indicators: dict[str, ThreatIndicator] = {}
        self.alert_handlers: list[Callable[[SecurityAlert], None]] = []

        # Detection thresholds
        self.thresholds = {
            "failed_logins_per_hour": 5,
            "rate_limit_violations_per_hour": 10,
            "injection_attempts_per_hour": 3,
            "suspicious_ips_threshold": 50,
        }

        # Event counters for detection
        self.event_counters: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

        # Blocked entities
        self.blocked_ips: set[str] = set()
        self.blocked_users: set[str] = set()

    def generate_event_id(self) -> str:
        """Generate unique event ID"""
        import secrets

        timestamp = int(datetime.now(UTC).timestamp() * 1000)
        random_suffix = secrets.token_hex(4)
        return f"evt_{timestamp}_{random_suffix}"

    def log_event(self, event: SecurityEvent) -> str:
        """Log a security event"""
        if not event.event_id:
            event.event_id = self.generate_event_id()

        # Store event
        self.events.append(event)

        # Update counters for detection
        self._update_counters(event)

        # Check for threats
        self._detect_threats(event)

        # Log to standard logger
        log_level = self._get_log_level(event.severity)
        logger.log(
            log_level, f"Security event: {event.event_type.value} - {event.model_dump_json()}"
        )

        return event.event_id

    def _update_counters(self, event: SecurityEvent):
        """Update event counters for detection"""
        hour_key = datetime.now(UTC).strftime("%Y-%m-%d-%H")

        # Count by event type
        self.event_counters[hour_key][event.event_type.value] += 1

        # Count by IP
        if event.ip_address:
            self.event_counters[hour_key][f"ip:{event.ip_address}"] += 1

        # Count by user
        if event.user_id:
            self.event_counters[hour_key][f"user:{event.user_id}"] += 1

    def _detect_threats(self, event: SecurityEvent):
        """Detect potential threats based on event patterns"""
        hour_key = datetime.now(UTC).strftime("%Y-%m-%d-%H")

        # Brute force detection
        if event.event_type == SecurityEventType.LOGIN_FAILED and event.ip_address:
            ip_key = f"ip:{event.ip_address}"
            if self.event_counters[hour_key][ip_key] >= self.thresholds["failed_logins_per_hour"]:
                self._create_alert(
                    title="Brute Force Attack Detected",
                    description=f"Multiple failed login attempts from IP {event.ip_address}",
                    severity=AlertSeverity.HIGH,
                    event_type=SecurityEventType.BRUTE_FORCE_DETECTED,
                    source_events=[event.event_id],
                    recommended_action=f"Block IP {event.ip_address}",
                )
                self._add_threat_indicator("ip", event.ip_address, 80)

        # Injection attempt detection
        if event.event_type == SecurityEventType.INJECTION_ATTEMPT and event.ip_address:
            self._add_threat_indicator("ip", event.ip_address, 90)
            self._create_alert(
                title="Injection Attack Detected",
                description=f"SQL/Command injection attempt from IP {event.ip_address}",
                severity=AlertSeverity.CRITICAL,
                event_type=SecurityEventType.INJECTION_ATTEMPT,
                source_events=[event.event_id],
                recommended_action="Block IP and investigate",
            )

        # Rate limit abuse
        if event.event_type == SecurityEventType.RATE_LIMIT_EXCEEDED and event.ip_address:
            ip_key = f"ip:{event.ip_address}"
            if (
                self.event_counters[hour_key][ip_key]
                >= self.thresholds["rate_limit_violations_per_hour"]
            ):
                self._add_threat_indicator("ip", event.ip_address, 60)
                self._create_alert(
                    title="Rate Limit Abuse Detected",
                    description=f"Excessive rate limit violations from IP {event.ip_address}",
                    severity=AlertSeverity.MEDIUM,
                    event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
                    source_events=[event.event_id],
                    recommended_action="Consider temporary IP block",
                )

    def _add_threat_indicator(self, indicator_type: str, value: str, threat_score: int):
        """Add or update threat indicator"""
        key = f"{indicator_type}:{value}"

        if key in self.threat_indicators:
            indicator = self.threat_indicators[key]
            indicator.last_seen = datetime.now(UTC)
            indicator.event_count += 1
            indicator.threat_score = max(indicator.threat_score, threat_score)
        else:
            self.threat_indicators[key] = ThreatIndicator(
                indicator_type=indicator_type,
                value=value,
                threat_score=threat_score,
                first_seen=datetime.now(UTC),
                last_seen=datetime.now(UTC),
            )

        # Auto-block high threat indicators
        if self.threat_indicators[key].threat_score >= 80:
            if indicator_type == "ip":
                self.blocked_ips.add(value)
            elif indicator_type == "user":
                self.blocked_users.add(value)

    def _create_alert(
        self,
        title: str,
        description: str,
        severity: AlertSeverity,
        event_type: SecurityEventType,
        source_events: list[str],
        recommended_action: str,
    ):
        """Create and dispatch security alert"""
        import secrets

        alert = SecurityAlert(
            alert_id=f"alert_{secrets.token_hex(8)}",
            title=title,
            description=description,
            severity=severity,
            event_type=event_type,
            source_events=source_events,
            recommended_action=recommended_action,
        )

        self.alerts.append(alert)

        # Dispatch to handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")

        # Log alert
        logger.warning(f"Security alert: {alert.title} - {alert.description}")

    def _get_log_level(self, severity: AlertSeverity) -> int:
        """Get logging level for severity"""
        mapping = {
            AlertSeverity.CRITICAL: logging.CRITICAL,
            AlertSeverity.HIGH: logging.ERROR,
            AlertSeverity.MEDIUM: logging.WARNING,
            AlertSeverity.LOW: logging.INFO,
            AlertSeverity.INFO: logging.DEBUG,
        }
        return mapping.get(severity, logging.INFO)

    def register_alert_handler(self, handler: Callable[[SecurityAlert], None]):
        """Register alert handler for notifications"""
        self.alert_handlers.append(handler)

    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        return ip in self.blocked_ips

    def is_user_blocked(self, user_id: str) -> bool:
        """Check if user is blocked"""
        return user_id in self.blocked_users

    def get_security_metrics(self, hours: int = 24) -> dict[str, Any]:
        """Get security metrics for specified period"""
        cutoff = datetime.now(UTC) - timedelta(hours=hours)

        recent_events = [e for e in self.events if e.timestamp >= cutoff]
        recent_alerts = [a for a in self.alerts if a.timestamp >= cutoff]

        # Count by type
        event_counts = defaultdict(int)
        severity_counts = defaultdict(int)

        for event in recent_events:
            event_counts[event.event_type.value] += 1
            severity_counts[event.severity.value] += 1

        return {
            "period_hours": hours,
            "total_events": len(recent_events),
            "total_alerts": len(recent_alerts),
            "events_by_type": dict(event_counts),
            "events_by_severity": dict(severity_counts),
            "blocked_ips": len(self.blocked_ips),
            "blocked_users": len(self.blocked_users),
            "active_threats": len(
                [t for t in self.threat_indicators.values() if t.threat_score >= 50]
            ),
            "unacknowledged_alerts": len([a for a in recent_alerts if not a.is_acknowledged]),
        }

    def get_audit_trail(self, user_id: str = None, hours: int = 24) -> list[SecurityEvent]:
        """Get audit trail for user or all users"""
        cutoff = datetime.now(UTC) - timedelta(hours=hours)

        events = [e for e in self.events if e.timestamp >= cutoff]

        if user_id:
            events = [e for e in events if e.user_id == user_id]

        return sorted(events, key=lambda e: e.timestamp, reverse=True)


# Global instance
security_monitor = SecurityMonitor()
