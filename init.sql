-- DevSkyy Database Initialization (PostgreSQL 15+)
-- ============================================================================
-- EXTENSIONS ONLY. The application owns its schema: database/db.py creates all
-- tables from the SQLAlchemy models on startup (create_all). A hand-maintained
-- table schema here drifts from the models and conflicts on FK types
-- (e.g. order_items.order_id vs a UUID orders.id) — which aborts app startup.
-- Keep this file to the extensions the models rely on; let the app build tables.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
