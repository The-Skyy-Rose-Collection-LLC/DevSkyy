# database/ — Async SQLAlchemy 2.0 Layer

**Single shared `Base` metadata across all model files.** Connection pooling, repository pattern, query optimizer, performance indexes. Alembic migrations live in repo-root `alembic/`, not here.

## Architecture (2 model locations, 1 Base)

| Location | Models | Why |
|----------|--------|-----|
| `db.py` (legacy monolith) | `User`, `Product`, `Order`, `OrderItem`, `AuditLog`, `AgentTask`, `EventRecord` | Original schema; shipped before multi-tenancy split |
| `models/*.py` (per-model files) | `Tenant`, `TenantUser` | New multi-tenancy. Imports `Base` from `database.db` — same metadata, same migrations |

**Rule**: new models go in `models/<name>.py` as separate files. Do not extend `db.py` further — it's already 700+ lines. The monolith stays for backwards compatibility; new work splits.

## Public Surface (`database/__init__.py`)

| Symbol | Source |
|--------|--------|
| `db_manager` (singleton), `DatabaseManager`, `DatabaseConfig`, `get_db()` | `db.py` |
| `Base` — shared declarative metadata | `db.py` |
| `User`, `Product`, `Order`, `OrderItem`, `AuditLog`, `AgentTask` | `db.py` |
| `BaseRepository[T]`, `UserRepository`, `ProductRepository`, `OrderRepository`, `AuditLogRepository` | `db.py` |

**Not exported from `__init__.py`**: `EventRecord`, `Tenant`, `TenantUser`, `TimestampMixin`. Import directly from source path.

## Hard Rules

### Connection + Pool

- **`DatabaseManager` is a singleton** (`db.py:275-282`) — `__new__` pattern, `_instance` class attr. Tests must clear or use a fresh process
- **Pool class auto-selected by URL** (`db.py:298-303`):
  - `:memory:` → `StaticPool` (keeps single connection alive across sessions)
  - file SQLite → `NullPool` (allows multi-process access)
  - PostgreSQL → `QueuePool` with `pool_pre_ping=True`
- `expire_on_commit=False` — model instances survive commit. Don't re-fetch after write
- Config from env: `DATABASE_URL`, `DB_POOL_SIZE` (10), `DB_MAX_OVERFLOW` (20), `DB_POOL_TIMEOUT` (30), `DB_POOL_RECYCLE` (1800), `DB_ECHO` (false)

### Schema Bootstrap

- **`initialize()` calls `Base.metadata.create_all`** (`db.py:338`). Convenient for dev / SQLite, but **dangerous with Alembic** — running `create_all` after a migration on an empty DB skips Alembic version tracking
- **Production rule**: rely on Alembic migrations exclusively. `db.py:initialize()` is safe in prod only because `create_all` skips existing tables — but new tables added via Alembic still appear in `Base.metadata`, so this is a foot-gun if you ever roll back a migration
- If you add a new model file under `models/`: import it in `database/models/__init__.py` so `Base.metadata` knows about it. Otherwise Alembic autogenerate misses it

### Sessions + Transactions

- **Use `db_manager.session()` for read+write** (auto-commit on success, rollback on exception, close on exit)
- **Use `db_manager.transaction()` for explicit transaction boundary** (wraps `session.begin()`)
- **Use `get_db()` as FastAPI dependency** for request-scoped sessions
- Never instantiate `AsyncSession` directly — always go through `db_manager`

### Identity + Indexing

- **All primary keys are `String(36)`** — UUID strings. Never use integer PKs. New models follow this
- **Composite indexes via `__table_args__`** for common query patterns (e.g., `ix_users_email_active`, `ix_orders_user_status`)
- **Selectin eager-loading**: `User.orders`, `Order.items` use `lazy="selectin"` to prevent N+1
- For deeper N+1 prevention: use `QueryOptimizer.optimize_product_query()` (`query_optimizer.py:45-65`)
- Extra performance indexes live in `indexes.sql` — `CREATE INDEX CONCURRENTLY` (Postgres only). Includes GIN full-text on products + partial indexes on `is_active = TRUE` / `status IN ('pending', 'running')`

### EventRecord Is Append-Only

- `EventRecord` table (`db.py:231-256`) backs `core.events.EventBus` persistence
- **NEVER update or delete EventRecord rows** — it's an event-sourced log. State is rebuilt by replaying events in `timestamp` order
- Mutation breaks the audit trail AND any aggregate reconstruction that depends on the log
- Indexed by `(aggregate_id, timestamp)` and `(event_type, timestamp)` for replay efficiency

### JSON Columns Use Text + Helper

- JSON-typed data is stored as `Text` with explicit `json.dumps()` / `json.loads()` helpers (e.g., `Tenant.get_settings()` / `set_settings()` at `models/tenant.py:60-69`)
- Why: SQLite < 3.45 lacks JSON1 by default; this keeps the schema portable. PostgreSQL JSONB migration would be a separate ADR
- Consistent suffix: `*_json` field name (`metadata_json`, `variants_json`, `images_json`, `seo_json`, `parameters_json`, `result_json`, `details_json`, `data_json`, `shipping_address_json`, `billing_address_json`, `variant_json`, `settings`)

### Repository Pattern

- `BaseRepository[T: Base]` generic — extend per model
- All repository methods async. Receive `AsyncSession`, never own it
- Standard CRUD: `get_by_id`, `get_all`, `create`, `update`, `delete`. Use specialized repository methods (`UserRepository.get_by_email`, etc.) for indexed queries

## Module Index

| Module | Purpose |
|--------|---------|
| `db.py` | DatabaseManager singleton, Base, 7 legacy models, 5 repositories — the monolith (~700+ lines) |
| `models/` | New per-model files (currently Tenant + TenantUser for multi-tenancy) |
| `query_optimizer.py` | N+1 prevention helpers, `EXPLAIN ANALYZE` diagnostics (Postgres only) |
| `indexes.sql` | Performance indexes (`CREATE INDEX CONCURRENTLY` — Postgres) |
| `seed_admin.py` | Seed admin user from env vars |
| `seed_catalog.py` | Seed SkyyRose product catalog from `wordpress-theme/.../skyyrose-catalog.csv` |

## Consumers

- `api/v1/*`, `api/v2/*` — `Depends(get_db)` for request-scoped sessions
- `core/repositories/interfaces.py` — `IRepository`, `IUserRepository`, etc. are abstract contracts; this module implements them
- `alembic/` (repo root) — migrations target `database.db.Base.metadata`
- `core/events.event_store` — persists events via `EventRecord`
- `agents/*` — task tracking via `AgentTask`
- `services/analytics/*` — event collector + audit log writes

## Related

- Alembic migrations: `alembic/` (repo root, not here)
- Multi-tenancy models: `database/models/` (has own CLAUDE.md)
- Stripe customer linkage: `Tenant.stripe_customer_id` + `Tenant.stripe_subscription_id` consumed by `billing/`
- Brand-canon catalog source: `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` → seeded via `seed_catalog.py`
