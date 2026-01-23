# Ralph Progress Log

This file tracks progress across iterations. It's automatically updated
after each iteration and included in agent prompts for context.

## Codebase Patterns (Study These First)

### Alembic Migration Pattern
- Use PostgreSQL-specific types from `sqlalchemy.dialects.postgresql` (UUID, JSONB, ARRAY)
- Always provide both `upgrade()` and `downgrade()` functions
- Create indexes for common query patterns (timestamp, event_type, foreign keys)
- Use composite indexes for frequently combined query conditions
- Add `updated_at` triggers using `update_updated_at_column()` function
- Import order: `sqlalchemy as sa`, `sqlalchemy.dialects.postgresql`, then `alembic import op`

---

## 2026-01-22 - US-001
- **What was implemented:** Analytics database schema with 4 tables: `analytics_events` (raw event storage), `analytics_rollups` (pre-computed aggregations), `alert_configs` (threshold configurations), `alert_history` (triggered alerts)
- **Files changed:** `alembic/versions/003_add_analytics_tables.py`
- **Learnings:**
  - PostgreSQL UUID type requires `uuid_generate_v4()` server default
  - JSONB columns should have `server_default=sa.text("'{}'::jsonb")` for empty object default
  - Unique constraints need explicit naming for reliable downgrade
  - Composite indexes significantly improve query performance for multi-column filters
  - `update_updated_at_column()` trigger function must exist (from prior migrations)
---

## 2026-01-22 - US-002
- **What was implemented:** Analytics Event Collector Service with async buffered event ingestion
- **Files changed:**
  - `services/analytics/__init__.py`
  - `services/analytics/event_collector.py`
  - `tests/services/analytics/__init__.py`
  - `tests/services/analytics/test_event_collector.py`
- **Learnings:**
  - `DevSkyError` uses `context` not `details` for extra error info
  - Use `contextlib.suppress(asyncio.CancelledError)` instead of try/except/pass (ruff SIM105)
  - Pydantic models with `use_enum_values = True` serialize enums as their values
  - Background flush tasks need proper cancellation handling in `stop()`
  - Batch inserts with raw SQL are faster than ORM for high-volume analytics
---

