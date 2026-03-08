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
from services.analytics.alert_engine import AlertSeverity as EngineAlertSeverity
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
from services.analytics.alert_notifier import AlertSeverity as NotifierAlertSeverity
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

__all__ = [
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
    "EngineAlertSeverity",
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
    "NotifierAlertSeverity",
    "get_alert_notifier",
    "severity_meets_threshold",
]
