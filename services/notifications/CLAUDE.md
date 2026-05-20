# services/notifications/ — Notification Services

**Email + alerting transports.** Consumed by `services/analytics/alert_notifier.py` and approval workflow.

## Public Surface (`services/notifications/__init__.py`)

| Symbol | Purpose | Source |
|--------|---------|--------|
| `EmailNotificationService` | async email sender | `email_notifications.py` |
| `EmailConfig` | SMTP / provider config (Pydantic) | `email_notifications.py` |
| `EmailTemplate` | template enum (approval, alert, etc.) | `email_notifications.py` |
| `NotificationError` | base error | `email_notifications.py` |
| `get_email_service()` | process-level singleton accessor | `email_notifications.py` |

## Hard Rules

- **`get_email_service()` returns process-level singleton** — tests must mock or reset between cases
- All sends are async — `await email_service.send(...)`. Synchronous wrappers do not exist
- Templates live in `EmailTemplate` enum — never inline HTML in service code. New templates: add enum value + template file
- Email config from env vars (`SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`) — never hardcode
- Failed sends raise `NotificationError` — caller decides retry policy. Do not retry silently inside the service
- Subject line must include `[SkyyRose]` prefix for spam-filter consistency

## Consumers

- `services/analytics/alert_notifier.py` — `AlertNotifier` email channel
- `services/approval_queue_manager.py` — approval-pending notifications
- `agents/core/operations/*` — admin notifications

## Not Yet Implemented

- SMS / Slack / Discord channels — wire under `services/notifications/` if needed, follow same `*NotificationService` + `get_*_service()` pattern
