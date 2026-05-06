"""Analytics services for DevSkyy admin dashboard."""

from services.analytics.alert_engine import (
    AlertConfig,
    AlertConfigNotFoundError,
    AlertEngineError,
    AlertEvaluationEngine,
    AlertStatus,
    AlertTrigger,
    ConditionOperator,
    ConditionType,
    MetricProvider,
    MetricValue,
    get_alert_engine,
)
from services.analytics.alert_notifier import (
    AlertNotification,
    AlertNotifier,
    AlertNotifierConfig,
    AlertNotifierError,
    InAppNotification,
    NotificationChannel,
    NotificationPreferences,
    NotificationResult,
    NotificationStatus,
    get_alert_notifier,
    severity_meets_threshold,
)
from services.analytics.event_collector import (
    AnalyticsEvent,
    AnalyticsEventCollector,
    EventCollectorError,
    EventType,
)
from services.analytics.rollup_scheduler import (
    RollupDimension,
    RollupGranularity,
    RollupResult,
    RollupScheduler,
    RollupSchedulerError,
)

# Single canonical AlertSeverity — both engine and notifier now import from
# services.analytics.severity, so this is the same class object everywhere.
from services.analytics.severity import AlertSeverity

__all__ = [
    # Shared types
    "AlertSeverity",
    # Event Collector
    "AnalyticsEvent",
    "AnalyticsEventCollector",
    "EventCollectorError",
    "EventType",
    # Rollup Scheduler
    "RollupDimension",
    "RollupGranularity",
    "RollupResult",
    "RollupScheduler",
    "RollupSchedulerError",
    # Alert Engine
    "AlertConfig",
    "AlertConfigNotFoundError",
    "AlertEngineError",
    "AlertEvaluationEngine",
    "AlertStatus",
    "AlertTrigger",
    "ConditionOperator",
    "ConditionType",
    "MetricProvider",
    "MetricValue",
    "get_alert_engine",
    # Alert Notifier
    "AlertNotification",
    "AlertNotifier",
    "AlertNotifierConfig",
    "AlertNotifierError",
    "InAppNotification",
    "NotificationChannel",
    "NotificationPreferences",
    "NotificationResult",
    "NotificationStatus",
    "get_alert_notifier",
    "severity_meets_threshold",
]
