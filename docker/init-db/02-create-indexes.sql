-- ============================================================================
-- DevSkyy Enterprise Platform - Database Indexes
-- PostgreSQL 15+ | Performance Optimization
-- ============================================================================
-- This script creates indexes for common query patterns
-- Per Truth Protocol Rule #12: P95 < 200ms SLO
-- ============================================================================

-- Note: Specific table indexes will be created by SQLAlchemy migrations
-- This file contains general-purpose indexes and monitoring utilities

-- ============================================================================
-- Monitoring Queries (For Performance Tracking)
-- ============================================================================

-- Function to check database health
CREATE OR REPLACE FUNCTION devskyy.check_database_health()
RETURNS TABLE (
    metric VARCHAR(50),
    value TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 'connection_count'::VARCHAR(50),
           COUNT(*)::TEXT
    FROM pg_stat_activity

    UNION ALL

    SELECT 'active_queries'::VARCHAR(50),
           COUNT(*)::TEXT
    FROM pg_stat_activity
    WHERE state = 'active'

    UNION ALL

    SELECT 'database_size_mb'::VARCHAR(50),
           ROUND((pg_database_size(current_database()) / 1024.0 / 1024.0)::NUMERIC, 2)::TEXT

    UNION ALL

    SELECT 'cache_hit_ratio'::VARCHAR(50),
           ROUND((100.0 * sum(blks_hit) / NULLIF(sum(blks_hit) + sum(blks_read), 0))::NUMERIC, 2)::TEXT
    FROM pg_stat_database
    WHERE datname = current_database();
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Slow Query Detection
-- ============================================================================

-- View for monitoring slow queries
CREATE OR REPLACE VIEW devskyy.slow_queries AS
SELECT
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query,
    state,
    wait_event_type,
    wait_event
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '1 seconds'
  AND state != 'idle'
ORDER BY duration DESC;

-- ============================================================================
-- Database Statistics
-- ============================================================================

-- View for table statistics
CREATE OR REPLACE VIEW devskyy.table_stats AS
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(format('%I.%I', schemaname, tablename)::regclass)) AS size,
    n_live_tup AS row_count,
    n_dead_tup AS dead_rows,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(format('%I.%I', schemaname, tablename)::regclass) DESC;

-- ============================================================================
-- Success Message
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Database monitoring utilities created successfully';
    RAISE NOTICE 'Functions: check_database_health()';
    RAISE NOTICE 'Views: slow_queries, table_stats';
    RAISE NOTICE 'Use: SELECT * FROM devskyy.check_database_health();';
END $$;
