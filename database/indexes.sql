-- =============================================================================
-- Performance Indexes for DevSkyy
-- =============================================================================
--
-- Run with: psql $DATABASE_URL -f database/indexes.sql
--
-- All indexes use CONCURRENTLY to avoid locking production tables.
-- Safe to run on a live database (requires PostgreSQL).
--
-- SQLite note: CONCURRENTLY is not supported; run without it in dev.
-- =============================================================================

-- Products: primary lookup patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_sku
    ON products(sku);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_collection_active
    ON products(collection, is_active)
    WHERE is_active = TRUE;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_created_desc
    ON products(created_at DESC);

-- Products: partial index for active-only queries (most common case)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_active_only
    ON products(id, sku, collection)
    WHERE is_active = TRUE;

-- Products: full-text search on name + description
-- Enables fast LIKE/ILIKE queries and semantic search
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_fts
    ON products
    USING GIN(to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(description, '')));

-- Orders: user order history (most common query pattern)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_user_created
    ON orders(user_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_status_created
    ON orders(status, created_at DESC);

-- Orders: composite for dashboard queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_user_status
    ON orders(user_id, status);

-- AuditLogs: time-based queries (compliance reports)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_timestamp
    ON audit_logs(timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user_action
    ON audit_logs(user_id, action, timestamp DESC);

-- AgentTask: job queue lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_tasks_status_created
    ON agent_tasks(status, created_at DESC)
    WHERE status IN ('pending', 'running');
