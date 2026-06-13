# alembic/ — Database migration management

Alembic migration environment for DevSkyy's SQLAlchemy database. Manages schema evolution for the FastAPI backend's PostgreSQL database.

## Key files

- `env.py` — Alembic runtime config. Imports `Base` metadata from `database/models/` and reads `DATABASE_URL` from the environment. Edit this file only to add new metadata targets or offline migration support.
- `script.py.mako` — Template for generated migration scripts. Includes standard `upgrade()` / `downgrade()` scaffold. Do not modify — changes affect all future `alembic revision` outputs.
- `versions/001_baseline_schema.py` — Initial schema: all core tables from the baseline FastAPI app.
- `versions/002_add_brand_assets.py` — Adds `brand_assets` table for tracking uploaded media metadata.
- `versions/003_add_analytics_tables.py` — Adds analytics event tables consumed by `agents/analytics_agent.py`.

## Conventions

- Run migrations from the repo root: `alembic upgrade head`. Never run from `alembic/` directly — `env.py` resolves `Base` relative to the repo root.
- New migrations: `alembic revision --autogenerate -m "short_description"`. Review the generated file before applying — autogenerate misses check constraints and partial indexes.
- Migration files are numbered `NNN_description.py` — never rename after merging to `main`. The revision chain is version-controlled by the hash in the migration file, not the filename.
- Every migration must implement `downgrade()` — even if it just raises `NotImplementedError`, document why. Prefer reversible schema changes.
- Do not use `op.execute()` with raw SQL strings for DDL — use `op.create_table()`, `op.add_column()`, etc. to stay database-agnostic.

## Don't

- Don't run `alembic downgrade` on the production database without an explicit user confirmation — schema rollbacks are destructive.
- Don't delete or modify existing migration files in `versions/` — Alembic's revision chain depends on stable file hashes. Instead, write a new migration that reverts unwanted changes.
- Don't import application-layer code (agents, services) from inside migration scripts — only `database/models/` is safe to import.

## Related

- `database/` — SQLAlchemy models (`Base` metadata imported by `env.py`)
- `database/seed_catalog.py` — Seed script for catalog data (runs after `alembic upgrade head`)
- `main_enterprise.py` — FastAPI startup checks DB connectivity and migration state before serving
