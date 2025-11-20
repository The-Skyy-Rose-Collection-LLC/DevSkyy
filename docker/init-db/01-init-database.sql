-- ============================================================================
-- DevSkyy Enterprise Platform - Database Initialization
-- PostgreSQL 15+ | Truth Protocol Compliant
-- ============================================================================
-- This script runs automatically when PostgreSQL container starts
-- It creates the database schema, extensions, and initial configuration
-- ============================================================================

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search optimization

-- Set timezone
SET timezone = 'UTC';

-- Create schema for application
CREATE SCHEMA IF NOT EXISTS devskyy;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA devskyy TO devskyy;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA devskyy TO devskyy;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA devskyy TO devskyy;

-- ============================================================================
-- Performance Configuration
-- ============================================================================

-- Increase statement timeout for long-running queries (30 seconds)
ALTER DATABASE devskyy SET statement_timeout = '30000';

-- Set work memory for sorting and hashing operations
ALTER DATABASE devskyy SET work_mem = '32MB';

-- Set maintenance work memory for vacuum and index operations
ALTER DATABASE devskyy SET maintenance_work_mem = '128MB';

-- Enable parallel query execution
ALTER DATABASE devskyy SET max_parallel_workers_per_gather = 2;

-- ============================================================================
-- Security Configuration (Truth Protocol Rule #13)
-- ============================================================================

-- Disable insecure functions
ALTER DATABASE devskyy SET lo_compat_privileges = off;

-- Log all DDL statements
ALTER DATABASE devskyy SET log_statement = 'ddl';

-- Log queries taking longer than 1 second
ALTER DATABASE devskyy SET log_min_duration_statement = 1000;

-- ============================================================================
-- Monitoring Tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS devskyy.database_health (
    id SERIAL PRIMARY KEY,
    check_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    connection_count INTEGER,
    active_queries INTEGER,
    database_size_mb DECIMAL(10,2),
    status VARCHAR(20)
);

-- ============================================================================
-- Success Message
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'DevSkyy database initialized successfully';
    RAISE NOTICE 'Extensions: uuid-ossp, pgcrypto, pg_trgm';
    RAISE NOTICE 'Schema: devskyy';
    RAISE NOTICE 'Performance tuning applied';
    RAISE NOTICE 'Security baseline configured (Truth Protocol Rule #13)';
END $$;
