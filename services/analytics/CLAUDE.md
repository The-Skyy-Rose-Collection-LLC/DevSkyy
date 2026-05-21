# services/analytics/ — Admin Dashboard Analytics

**Event collection → rollup → alert evaluation → notification.** Backs the read-only admin analytics surface in `api/v1/analytics/`.

## Public Surface (`services/analytics/__init__.py`)

| Group | Symbols | Source |
|-------|---------|--------|
| Event collection | `AnalyticsEvent`, `AnalyticsEventCollector`, `EventType`, `EventCollectorError` | `event_collector.py` |
| Rollup scheduler | `RollupDimension`, `RollupGranularity`, `RollupResult`, `RollupScheduler`, `RollupSchedulerError` | `rollup_scheduler.py` |
| Alert engine | `AlertConfig`, `AlertEvaluationEngine`, `AlertStatus`, `AlertTrigger`, `ConditionOperator`, `ConditionType`, `MetricProvider`, `MetricValue`, `EngineAlertSeverity`, `get_alert_engine` | `alert_engine.py` |
| Alert notifier | `AlertNotification`, `AlertNotifier`, `AlertNotifierConfig`, `InAppNotification`, `NotificationChannel`, `NotificationPreferences`, `NotificationResult`, `NotificationStatus`, `NotifierAlertSeverity`, `get_alert_notifier`, `severity_meets_threshold` | `alert_notifier.py` |

## Hard Rules

- **`AlertSeverity` is re-exported with two aliases** — `EngineAlertSeverity` (alert_engine) and `NotifierAlertSeverity` (alert_notifier). They are distinct enums; do not pass one where the other is required. Use `severity_meets_threshold()` to compare across boundaries
- `get_alert_engine()` and `get_alert_notifier()` return **process-level singletons** — tests must reset or mock the underlying state
- Event collection is async — `AnalyticsEventCollector.collect()` MUST be awaited. Fire-and-forget patterns drop events silently
- Rollup scheduler runs as background task; do not invoke synchronously from request handlers (use `RollupScheduler.schedule()`)
- **Alert evaluation is read-only** — never mutate `AlertConfig` inside an evaluation pass. Build a new config and replace
- Notification channels are pluggable — register new channels via `NotificationChannel` enum, implement in `alert_notifier.py`

## Consumers

- `api/v1/analytics/*` — read-only dashboard endpoints query rollups + alerts
- `services/notifications/email_notifications.py` — `EmailNotificationService` consumed by `AlertNotifier` for email channel
- Background workers — `RollupScheduler` cron job aggregates raw events into time-bucketed rollups


<claude-mem-context>

</claude-mem-context>