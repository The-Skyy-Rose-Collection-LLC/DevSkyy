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

