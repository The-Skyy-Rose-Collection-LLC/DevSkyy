# PRD: Admin Dashboard Analytics

## Overview

Implement comprehensive analytics API endpoints for the DevSkyy admin dashboard, providing both technical admins and business stakeholders with real-time and historical insights. The system will track system health, SkyyRose business metrics, and ML pipeline performance with configurable alerting across multiple notification channels.

## Goals

- Provide unified analytics API for system health, business metrics, and ML pipeline monitoring
- Support both real-time metrics (via Prometheus) and historical analysis (via database)
- Enable configurable alerting with multi-channel notifications (email, Slack, in-app, SMS)
- Deliver collection-level business insights (Black Rose, Love Hurts, Signature)
- Track ML provider performance with cost and success rate breakdowns
- Implement hybrid data aggregation (real-time raw + scheduled rollups)

## Quality Gates

These commands must pass for every user story:
- `pytest -v` - All tests pass
- `isort .` - Import sorting
- `ruff check --fix` - Linting
- `black .` - Code formatting

## User Stories

### US-001: Analytics Database Schema and Migrations
**Description:** As a developer, I want database tables for analytics data so that historical metrics can be stored and queried efficiently.

**Acceptance Criteria:**
- [ ] Create `analytics_events` table for raw event storage
- [ ] Create `analytics_rollups` table for pre-computed aggregations (hourly/daily/weekly)
- [ ] Create `alert_configs` table for threshold configurations
- [ ] Create `alert_history` table for triggered alerts
- [ ] Add indexes for common query patterns (timestamp, event_type, provider)
- [ ] Alembic migration file created at `alembic/versions/003_add_analytics_tables.py`

### US-002: Analytics Event Collector Service
**Description:** As a system, I want to collect and store analytics events so that metrics can be aggregated for historical analysis.

**Acceptance Criteria:**
- [ ] Create `services/analytics/event_collector.py`
- [ ] Implement `AnalyticsEventCollector` class with async event ingestion
- [ ] Support event types: `api_request`, `ml_job`, `order`, `error`, `alert`
- [ ] Buffer events and batch insert for performance
- [ ] Include correlation_id tracking for request tracing
- [ ] Unit tests at `tests/services/analytics/test_event_collector.py`

### US-003: Scheduled Rollup Aggregation Service
**Description:** As a system, I want scheduled jobs to pre-compute metric rollups so that historical queries are fast.

**Acceptance Criteria:**
- [ ] Create `services/analytics/rollup_scheduler.py`
- [ ] Implement hourly rollup job (runs every hour, aggregates last hour)
- [ ] Implement daily rollup job (runs at midnight UTC)
- [ ] Implement weekly rollup job (runs Sunday midnight UTC)
- [ ] Rollups include: count, sum, avg, min, max, p50, p95, p99
- [ ] Automatic cleanup of raw events older than 7 days
- [ ] Unit tests at `tests/services/analytics/test_rollup_scheduler.py`

### US-004: System Health Metrics API
**Description:** As an admin, I want API endpoints for system health metrics so that I can monitor platform performance.

**Acceptance Criteria:**
- [ ] Create `api/v1/analytics/health.py` router
- [ ] `GET /analytics/health/overview` - Current system status (uptime, error rate, latency)
- [ ] `GET /analytics/health/api` - API endpoint performance (latency by endpoint, error rates)
- [ ] `GET /analytics/health/database` - Database health (connection pool, query latency)
- [ ] `GET /analytics/health/timeseries` - Historical health metrics with time range params
- [ ] Support `?range=1h|24h|7d|30d` query parameter
- [ ] Pull real-time data from Prometheus `/metrics` endpoint
- [ ] Unit tests at `tests/api/analytics/test_health_analytics.py`

### US-005: ML Pipeline Analytics API
**Description:** As an admin, I want API endpoints for ML pipeline metrics so that I can monitor AI service usage and costs.

**Acceptance Criteria:**
- [ ] Create `api/v1/analytics/ml_pipelines.py` router
- [ ] `GET /analytics/ml/overview` - Summary across all pipelines
- [ ] `GET /analytics/ml/3d` - 3D generation metrics (jobs, success rate, duration)
- [ ] `GET /analytics/ml/descriptions` - Image description metrics
- [ ] `GET /analytics/ml/assets` - Asset processing metrics (ingestion, versioning, approval)
- [ ] `GET /analytics/ml/providers` - Provider-level breakdown (Replicate, Tripo, HuggingFace, Gemini)
- [ ] Include cost estimates per provider where available
- [ ] Support time range and provider filters
- [ ] Unit tests at `tests/api/analytics/test_ml_analytics.py`

### US-006: Business Metrics API (SkyyRose)
**Description:** As a business stakeholder, I want API endpoints for e-commerce metrics so that I can track SkyyRose sales performance.

**Acceptance Criteria:**
- [ ] Create `api/v1/analytics/business.py` router
- [ ] `GET /analytics/business/overview` - Revenue, orders, AOV summary
- [ ] `GET /analytics/business/sales` - Sales timeseries with breakdown
- [ ] `GET /analytics/business/products` - Product performance (views, conversions, inventory)
- [ ] `GET /analytics/business/collections` - Collection-level metrics (Black Rose, Love Hurts, Signature)
- [ ] `GET /analytics/business/funnel` - Conversion funnel (traffic → cart → checkout → complete)
- [ ] Support comparison periods (vs previous period, vs same period last year)
- [ ] Unit tests at `tests/api/analytics/test_business_analytics.py`

### US-007: Alert Configuration API
**Description:** As an admin, I want to configure alert thresholds so that I'm notified when metrics exceed limits.

**Acceptance Criteria:**
- [ ] Create `api/v1/analytics/alerts.py` router
- [ ] `GET /analytics/alerts/configs` - List all alert configurations
- [ ] `POST /analytics/alerts/configs` - Create alert config
- [ ] `PUT /analytics/alerts/configs/{id}` - Update alert config
- [ ] `DELETE /analytics/alerts/configs/{id}` - Delete alert config
- [ ] Support metric types: `threshold_above`, `threshold_below`, `rate_of_change`, `anomaly`
- [ ] Support severity levels: `info`, `warning`, `critical`
- [ ] Validate threshold values and metric names
- [ ] Unit tests at `tests/api/analytics/test_alert_configs.py`

### US-008: Alert Evaluation Engine
**Description:** As a system, I want an alert evaluation engine so that configured alerts are checked against current metrics.

**Acceptance Criteria:**
- [ ] Create `services/analytics/alert_engine.py`
- [ ] Implement `AlertEvaluationEngine` class
- [ ] Evaluate alerts on configurable schedule (default: every minute)
- [ ] Support all threshold types (above, below, rate_of_change)
- [ ] Implement alert cooldown to prevent notification spam
- [ ] Record alert history with trigger details
- [ ] Unit tests at `tests/services/analytics/test_alert_engine.py`

### US-009: Multi-Channel Alert Notifications
**Description:** As an admin, I want alerts sent via multiple channels so that I never miss critical issues.

**Acceptance Criteria:**
- [ ] Create `services/analytics/alert_notifier.py`
- [ ] Implement `AlertNotifier` with channel support:
  - [ ] Email via existing `EmailNotificationService`
  - [ ] Slack webhook integration
  - [ ] In-app notifications (stored in database)
  - [ ] SMS via Twilio for critical alerts
- [ ] Channel routing based on alert severity
- [ ] Support notification preferences per user/team
- [ ] Unit tests at `tests/services/analytics/test_alert_notifier.py`

### US-010: Alert History and Acknowledgment API
**Description:** As an admin, I want to view and acknowledge alerts so that I can track incident response.

**Acceptance Criteria:**
- [ ] `GET /analytics/alerts/history` - List triggered alerts with filters
- [ ] `GET /analytics/alerts/active` - Currently active (unacknowledged) alerts
- [ ] `POST /analytics/alerts/{id}/acknowledge` - Acknowledge alert
- [ ] `POST /analytics/alerts/{id}/resolve` - Mark alert resolved
- [ ] Include alert metadata: trigger time, metric value, threshold, notifications sent
- [ ] Support bulk acknowledgment
- [ ] Unit tests at `tests/api/analytics/test_alert_history.py`

### US-011: Analytics Dashboard Summary API
**Description:** As a dashboard consumer, I want a unified summary endpoint so that the dashboard can load all key metrics in one call.

**Acceptance Criteria:**
- [ ] `GET /analytics/dashboard/summary` - Unified dashboard data
- [ ] Include sections: system_health, ml_pipelines, business, active_alerts
- [ ] Support role-based response (admins see all, business users see business metrics)
- [ ] Implement response caching (1-minute TTL for real-time section)
- [ ] Support `?sections=health,ml,business,alerts` to request specific sections
- [ ] Unit tests at `tests/api/analytics/test_dashboard_summary.py`

### US-012: Register Analytics Routers in Main App
**Description:** As a developer, I want analytics routers registered so that endpoints are accessible.

**Acceptance Criteria:**
- [ ] Update `api/v1/__init__.py` to include analytics routers
- [ ] Update `main_enterprise.py` to register analytics routes under `/api/v1/analytics`
- [ ] Add analytics endpoints to OpenAPI schema with proper tags
- [ ] Verify all endpoints accessible via `/docs`

## Functional Requirements

- FR-1: All analytics endpoints must require authentication via JWT
- FR-2: Business metrics endpoints must check user role (admin or business_viewer)
- FR-3: Real-time metrics must be fetched from Prometheus with <500ms latency
- FR-4: Historical queries must use pre-computed rollups for ranges >24h
- FR-5: Alert evaluation must run at minimum every 60 seconds
- FR-6: Critical alerts must trigger SMS within 30 seconds of detection
- FR-7: All analytics events must include correlation_id for tracing
- FR-8: Dashboard summary must respond in <1 second with caching

## Non-Goals

- Custom dashboard UI (using existing admin UI)
- Real-time WebSocket streaming (future enhancement)
- Machine learning anomaly detection (v2 feature)
- Multi-tenant analytics isolation (single-tenant for now)
- Data export to external BI tools (future enhancement)
- Custom report builder (future enhancement)

## Technical Considerations

- **Prometheus Integration:** Use existing `/metrics` endpoint and `prometheus_client` library
- **Database:** Use existing PostgreSQL with new analytics tables
- **Caching:** Use Redis for dashboard summary caching
- **Background Jobs:** Use existing task queue for rollup scheduling
- **SMS:** Requires Twilio credentials in environment (`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`)
- **Slack:** Requires webhook URL in environment (`SLACK_ANALYTICS_WEBHOOK`)

## Success Metrics

- All 12 user stories implemented with passing tests
- API response times <500ms for real-time, <2s for historical queries
- Alert notifications delivered within SLA (30s critical, 5m warning)
- Zero data loss in analytics event collection
- Dashboard summary loads in <1 second

## Open Questions

1. Should we implement rate limiting on analytics endpoints?
2. What retention period for raw analytics events (currently 7 days)?
3. Should alert configs be exportable/importable for backup?
4. Do we need audit logging for alert config changes?
