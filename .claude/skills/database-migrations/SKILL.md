---
name: database-migrations
description: Safe schema and data migrations — expand/contract, concurrent indexes, batched backfills, rollback strategy — across PostgreSQL/MySQL and Alembic (this repo's canonical tool), Prisma, Drizzle, Kysely, Django, golang-migrate. Use when a model/table/column/index changes, a backfill is needed, or migration tooling is being set up or repaired. Do NOT use for query tuning and index *selection* on an unchanged schema (that is postgres-patterns), for Redis key/TTL design (redis-patterns), or for bringing the DB container up (docker-patterns).
origin: ECC
---

# Database Migration Patterns

Safe, reversible database schema changes for production systems.

## When to use

- Creating or altering database tables
- Adding/removing columns or indexes
- Running data migrations (backfill, transform)
- Planning zero-downtime schema changes
- Setting up migration tooling for a new project

**When NOT to use:**

- The schema is fine and a query is slow → `postgres-patterns` (EXPLAIN, index choice, RLS).
- Cache/session/rate-limit storage → `redis-patterns`; Redis has no migrations, only key contracts.
- The database will not start / compose won't parse → `docker-patterns` first; you cannot migrate
  a DB you cannot reach.
- WooCommerce/WordPress product data on skyyrose.co — that lives in the WP MySQL DB behind the WC
  REST API and is **not** managed by this repo's Alembic tree. Never point an Alembic revision at it.

## Inputs

**Absent input = STOP. A migration authored against an unknown current schema is a guess that runs
DDL on real data.**

1. **`DATABASE_URL`** for the target environment. `alembic/env.py:22` overrides `sqlalchemy.url`
   from this env var (loaded via `dotenv`) `[repo]`; `alembic.ini` ships it blank so secrets never
   enter version control. Unset → Alembic falls back to the empty ini value and fails; do not
   hardcode a URL to get moving.
2. **The current head, read from the database, not from memory** — `alembic current` (online) or
   `alembic heads` (tree only). If the two disagree, the environment is behind or diverged; resolve
   before authoring.
3. **A models import that reaches ALL models** — autogenerate diffs `Base.metadata` against the DB.
   A lazily-imported model is invisible, and autogenerate will happily emit a DROP for a table it
   simply did not see.
4. **Row-count expectations for any backfill.** "Works on 100 rows" is not evidence for 10M; a
   backfill without a batch size is an outage waiting for its turn.
5. **Explicit approval before running against production.** Applying a migration to a real database
   is irreversible-data territory — STOP-AND-SHOW with the exact revision id and target host.

## Procedure

Project rule for this repo: **model change + Alembic revision ship in the SAME commit.** Never
alter a production database by hand; never edit a revision that has already been applied anywhere.

1. Read the current state: `alembic current` (needs DB) and `alembic heads` (offline, tree only).
2. Change the SQLAlchemy model.
3. Generate: `alembic revision --autogenerate -m "<what changed>"`.
4. **Read the generated file before applying.** Autogenerate misses `CONCURRENTLY`, triggers,
   views, check constraints, and all data migrations — see "Autogenerate — What It Catches".
5. Split DDL from DML: schema change in one revision, backfill in the next, batched.
6. Dry-run the SQL without touching any database: `alembic upgrade head --sql` (Verification
   check 1).
7. Apply to dev: `alembic upgrade head`; confirm `alembic current` advanced (check 2).
8. Prove reversibility: `alembic downgrade -1` then `alembic upgrade head` (check 3). A revision
   whose `downgrade()` was never executed is an untested rollback plan.
9. For production: expand → migrate → contract, one deploy per phase (see Zero-Downtime section).

## Verification

Static reading of a revision file proves nothing about what it will do — these checks execute it.
An `alembic` command that aborted mid-run leaves the DB in a partially-migrated state: its error
output is an artifact, not a verdict (bug-230). Re-read `alembic current` before concluding
anything. Nothing here should ever run against production without explicit approval.

```bash
DATABASE_URL="postgresql://offline:offline@localhost/offline" alembic upgrade head --sql | head -20
```
**PASS:** exits 0 and emits the DDL you expect, wrapped in `BEGIN;`. This never connects, so it is
safe anywhere — and it catches "the revision doesn't even compile" before any real database sees
it. Observed 2026-07-28 from the repo root `[repro]`:
`INFO [alembic.runtime.migration] Generating static SQL` … `BEGIN;` … `CREATE TABLE alembic_version (…)`.

```bash
alembic heads && alembic current
```
**PASS:** exactly ONE head (multiple heads = a diverged tree, resolve with `alembic merge heads`
before doing anything else), and after an upgrade `alembic current` equals that head. Observed
2026-07-28: `003 (head)` with history `<base> -> 001 -> 002 -> 003` `[repro]`.

```bash
alembic upgrade head && alembic downgrade -1 && alembic upgrade head && alembic current
```
**PASS:** all four steps exit 0 and `current` returns to the head. This is the only evidence that
`downgrade()` actually works — an unexecuted downgrade is a comment, not a rollback plan. Run it in
dev, never in production. `[repro]`

```bash
docker exec devskyy-postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc \
  "SELECT count(*) FROM information_schema.columns WHERE table_name='"'"'<table>'"'"' AND column_name='"'"'<new_col>'"'"';"'
```
**PASS:** returns `1` for a column you added (`0` for one you dropped). Asserting the *database*
changed, not that a file exists, is the difference between `[repo]` and `[repro]` evidence.

Prove the checks can fail (rule 3): once, point check 4 at a column name that does not exist and
confirm it returns `0`. A schema assertion that returns success for a column you never added is
checking nothing.

Attribute before claiming (rule 4): to tell your migration's effect from pre-existing drift, run
the same assertions against a pristine tree extracted with
`git archive HEAD alembic | tar -x -C <scratch>` — **never `git stash`**, the stack is shared
across worktrees.

## Worked example

Real invocation in this repo, 2026-07-28:

```bash
cd /Users/theceo/DevSkyy/.claude/worktrees/glimmering-crafting-shannon
/Users/theceo/DevSkyy/.venv/bin/alembic heads
/Users/theceo/DevSkyy/.venv/bin/alembic history | head -3
DATABASE_URL="postgresql://offline:offline@localhost/offline" \
  /Users/theceo/DevSkyy/.venv/bin/alembic upgrade head --sql | head -8
```

Observed `[repro]`:

```
003 (head)

002 -> 003 (head), Add analytics tables for US-001: Analytics Database Schema.
001 -> 002, Add brand assets tables for US-013.
<base> -> 001, baseline schema

INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Generating static SQL
INFO  [alembic.runtime.migration] Will assume transactional DDL.
BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
```

Three things this proves, and one it deliberately does not. It proves the tree is linear with a
single head (`003`), that all three revisions in `alembic/versions/` compile and render, and that
the offline `--sql` path works without a database — so the whole check runs safely in CI. What it
does **not** prove is that production is at `003`: `--sql` and `heads` are both `[repo]`-scope
evidence about files. Claiming "prod is migrated" requires `alembic current` against the real
`DATABASE_URL` (`[repro]`/`[live]`). Reporting file state as deployment state is exactly the scope
jump bug-287 exists to prevent.

Checking the database separately is what makes that concrete. Same session:

```bash
docker exec devskyy-postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT version_num FROM alembic_version;"'
docker exec devskyy-postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT count(*) FROM information_schema.tables WHERE table_schema='"'"'public'"'"';"'
```

Observed `[repro]`:

```
ERROR:  relation "alembic_version" does not exist
7
```

That is a real drift finding, invisible to every file-side check: the running dev database holds 7
public tables but has **no `alembic_version` table**, so it was provisioned by something other than
Alembic (`create_all` or a seed script) and Alembic has no record of it. Consequences to respect
before writing anything: `alembic current` returns nothing to compare against `003`,
`alembic upgrade head` would attempt to create tables that already exist and fail, and
`--autogenerate` run against this database would diff `Base.metadata` against an unmanaged schema
and bake the drift into a revision file. Reconcile deliberately — verify the live schema matches
`001` and `alembic stamp` it, or rebuild the dev DB from migrations — rather than generating a
revision on top of an unknown base. (Also note the interpreter: this worktree has no `.venv`; the
Python environment lives at `/Users/theceo/DevSkyy/.venv`.)

## Core Principles

1. **Every change is a migration** — never alter production databases manually
2. **Migrations are forward-only in production** — rollbacks use new forward migrations
3. **Schema and data migrations are separate** — never mix DDL and DML in one migration
4. **Test migrations against production-sized data** — a migration that works on 100 rows may lock on 10M
5. **Migrations are immutable once deployed** — never edit a migration that has run in production

## Migration Safety Checklist

Before applying any migration:

- [ ] Migration has both UP and DOWN (or is explicitly marked irreversible)
- [ ] No full table locks on large tables (use concurrent operations)
- [ ] New columns have defaults or are nullable (never add NOT NULL without default)
- [ ] Indexes created concurrently (not inline with CREATE TABLE for existing tables)
- [ ] Data backfill is a separate migration from schema change
- [ ] Tested against a copy of production data
- [ ] Rollback plan documented

## PostgreSQL Patterns

### Adding a Column Safely

```sql
-- GOOD: Nullable column, no lock
ALTER TABLE users ADD COLUMN avatar_url TEXT;

-- GOOD: Column with default (Postgres 11+ is instant, no rewrite)
ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true;

-- BAD: NOT NULL without default on existing table (requires full rewrite)
ALTER TABLE users ADD COLUMN role TEXT NOT NULL;
-- This locks the table and rewrites every row
```

### Adding an Index Without Downtime

```sql
-- BAD: Blocks writes on large tables
CREATE INDEX idx_users_email ON users (email);

-- GOOD: Non-blocking, allows concurrent writes
CREATE INDEX CONCURRENTLY idx_users_email ON users (email);

-- Note: CONCURRENTLY cannot run inside a transaction block
-- Most migration tools need special handling for this
```

### Renaming a Column (Zero-Downtime)

Never rename directly in production. Use the expand-contract pattern:

```sql
-- Step 1: Add new column (migration 001)
ALTER TABLE users ADD COLUMN display_name TEXT;

-- Step 2: Backfill data (migration 002, data migration)
UPDATE users SET display_name = username WHERE display_name IS NULL;

-- Step 3: Update application code to read/write both columns
-- Deploy application changes

-- Step 4: Stop writing to old column, drop it (migration 003)
ALTER TABLE users DROP COLUMN username;
```

### Removing a Column Safely

```sql
-- Step 1: Remove all application references to the column
-- Step 2: Deploy application without the column reference
-- Step 3: Drop column in next migration
ALTER TABLE orders DROP COLUMN legacy_status;

-- For Django: use SeparateDatabaseAndState to remove from model
-- without generating DROP COLUMN (then drop in next migration)
```

### Large Data Migrations

```sql
-- BAD: Updates all rows in one transaction (locks table)
UPDATE users SET normalized_email = LOWER(email);

-- GOOD: Batch update with progress
DO $$
DECLARE
  batch_size INT := 10000;
  rows_updated INT;
BEGIN
  LOOP
    UPDATE users
    SET normalized_email = LOWER(email)
    WHERE id IN (
      SELECT id FROM users
      WHERE normalized_email IS NULL
      LIMIT batch_size
      FOR UPDATE SKIP LOCKED
    );
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    RAISE NOTICE 'Updated % rows', rows_updated;
    EXIT WHEN rows_updated = 0;
    COMMIT;
  END LOOP;
END $$;
```

## Prisma (TypeScript/Node.js)

### Workflow

```bash
# Create migration from schema changes
npx prisma migrate dev --name add_user_avatar

# Apply pending migrations in production
npx prisma migrate deploy

# Reset database (dev only)
npx prisma migrate reset

# Generate client after schema changes
npx prisma generate
```

### Schema Example

```prisma
model User {
  id        String   @id @default(cuid())
  email     String   @unique
  name      String?
  avatarUrl String?  @map("avatar_url")
  createdAt DateTime @default(now()) @map("created_at")
  updatedAt DateTime @updatedAt @map("updated_at")
  orders    Order[]

  @@map("users")
  @@index([email])
}
```

### Custom SQL Migration

For operations Prisma cannot express (concurrent indexes, data backfills):

```bash
# Create empty migration, then edit the SQL manually
npx prisma migrate dev --create-only --name add_email_index
```

```sql
-- migrations/20240115_add_email_index/migration.sql
-- Prisma cannot generate CONCURRENTLY, so we write it manually
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users (email);
```

## Drizzle (TypeScript/Node.js)

### Workflow

```bash
# Generate migration from schema changes
npx drizzle-kit generate

# Apply migrations
npx drizzle-kit migrate

# Push schema directly (dev only, no migration file)
npx drizzle-kit push
```

### Schema Example

```typescript
import { pgTable, text, timestamp, uuid, boolean } from "drizzle-orm/pg-core";

export const users = pgTable("users", {
  id: uuid("id").primaryKey().defaultRandom(),
  email: text("email").notNull().unique(),
  name: text("name"),
  isActive: boolean("is_active").notNull().default(true),
  createdAt: timestamp("created_at").notNull().defaultNow(),
  updatedAt: timestamp("updated_at").notNull().defaultNow(),
});
```

## Kysely (TypeScript/Node.js)

### Workflow (kysely-ctl)

```bash
# Initialize config file (kysely.config.ts)
kysely init

# Create a new migration file
kysely migrate make add_user_avatar

# Apply all pending migrations
kysely migrate latest

# Rollback last migration
kysely migrate down

# Show migration status
kysely migrate list
```

### Migration File

```typescript
// migrations/2024_01_15_001_create_user_profile.ts
import { type Kysely, sql } from 'kysely'

// IMPORTANT: Always use Kysely<any>, not your typed DB interface.
// Migrations are frozen in time and must not depend on current schema types.
export async function up(db: Kysely<any>): Promise<void> {
  await db.schema
    .createTable('user_profile')
    .addColumn('id', 'serial', (col) => col.primaryKey())
    .addColumn('email', 'varchar(255)', (col) => col.notNull().unique())
    .addColumn('avatar_url', 'text')
    .addColumn('created_at', 'timestamp', (col) =>
      col.defaultTo(sql`now()`).notNull()
    )
    .execute()

  await db.schema
    .createIndex('idx_user_profile_avatar')
    .on('user_profile')
    .column('avatar_url')
    .execute()
}

export async function down(db: Kysely<any>): Promise<void> {
  await db.schema.dropTable('user_profile').execute()
}
```

### Programmatic Migrator

```typescript
import { Migrator, FileMigrationProvider } from 'kysely'
import { promises as fs } from 'fs'
import * as path from 'path'
// ESM only — CJS can use __dirname directly
import { fileURLToPath } from 'url'
const migrationFolder = path.join(
  path.dirname(fileURLToPath(import.meta.url)),
  './migrations',
)

// `db` is your Kysely<any> database instance
const migrator = new Migrator({
  db,
  provider: new FileMigrationProvider({
    fs,
    path,
    migrationFolder,
  }),
  // WARNING: Only enable in development. Disables timestamp-ordering
  // validation, which can cause schema drift between environments.
  // allowUnorderedMigrations: true,
})

const { error, results } = await migrator.migrateToLatest()

results?.forEach((it) => {
  if (it.status === 'Success') {
    console.log(`migration "${it.migrationName}" executed successfully`)
  } else if (it.status === 'Error') {
    console.error(`failed to execute migration "${it.migrationName}"`)
  }
})

if (error) {
  console.error('migration failed', error)
  process.exit(1)
}
```

## Django (Python)

### Workflow

```bash
# Generate migration from model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Generate empty migration for custom SQL
python manage.py makemigrations --empty app_name -n description
```

### Data Migration

```python
from django.db import migrations

def backfill_display_names(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    batch_size = 5000
    users = User.objects.filter(display_name="")
    while users.exists():
        batch = list(users[:batch_size])
        for user in batch:
            user.display_name = user.username
        User.objects.bulk_update(batch, ["display_name"], batch_size=batch_size)

def reverse_backfill(apps, schema_editor):
    pass  # Data migration, no reverse needed

class Migration(migrations.Migration):
    dependencies = [("accounts", "0015_add_display_name")]

    operations = [
        migrations.RunPython(backfill_display_names, reverse_backfill),
    ]
```

### SeparateDatabaseAndState

Remove a column from the Django model without dropping it from the database immediately:

```python
class Migration(migrations.Migration):
    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(model_name="user", name="legacy_field"),
            ],
            database_operations=[],  # Don't touch the DB yet
        ),
    ]
```

## golang-migrate (Go)

### Workflow

```bash
# Create migration pair
migrate create -ext sql -dir migrations -seq add_user_avatar

# Apply all pending migrations
migrate -path migrations -database "$DATABASE_URL" up

# Rollback last migration
migrate -path migrations -database "$DATABASE_URL" down 1

# Force version (fix dirty state)
migrate -path migrations -database "$DATABASE_URL" force VERSION
```

### Migration Files

```sql
-- migrations/000003_add_user_avatar.up.sql
ALTER TABLE users ADD COLUMN avatar_url TEXT;
CREATE INDEX CONCURRENTLY idx_users_avatar ON users (avatar_url) WHERE avatar_url IS NOT NULL;

-- migrations/000003_add_user_avatar.down.sql
DROP INDEX IF EXISTS idx_users_avatar;
ALTER TABLE users DROP COLUMN IF EXISTS avatar_url;
```

## Alembic (Python / SQLAlchemy) — Project Canonical Tool

SkyyRose Python backend uses SQLAlchemy + Alembic. **Every model change ships its Alembic migration in the same commit — no exceptions.**

### Project Rule

```
Model change + alembic revision --autogenerate + alembic upgrade head
→ committed together in a single atomic commit.
```

Never alter the production database manually. Never edit a revision file that has already been applied in any environment.

### Initialize

```bash
# Standard layout (creates alembic/ directory + alembic.ini)
alembic init alembic

# Alternative: keep migrations alongside the app
alembic init migrations
```

Generated layout:

```
alembic/
├── env.py          # Migration environment — wire Base.metadata here
├── script.py.mako  # Template for new revision files
└── versions/       # Generated revision files live here
alembic.ini         # Config: sqlalchemy.url goes in here (or env.py)
```

Set `sqlalchemy.url` in `alembic.ini` or override it in `env.py` from an environment variable (preferred for secrets):

```ini
# alembic.ini — leave the url blank and override in env.py
sqlalchemy.url =
```

### env.py — Async Engine Wiring (FastAPI / asyncio apps)

The app uses an async SQLAlchemy engine. Alembic's built-in runner is synchronous, so use `connection.run_sync` to bridge the two:

```python
# alembic/env.py
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# ------------------------------------------------------------------
# Import the declarative Base so Alembic sees all mapped models.
# Adjust the import path to match your project structure.
# ------------------------------------------------------------------
from database.base import Base  # noqa: E402  (import after sys.path is set)

# this is the Alembic Config object
config = context.config

# Override sqlalchemy.url from environment variable so secrets stay
# out of alembic.ini and version control.
import os
config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Tell Alembic which metadata to compare against for --autogenerate.
target_metadata = Base.metadata


# ------------------------------------------------------------------ #
# Offline mode — emit SQL to stdout without a live DB connection.     #
# ------------------------------------------------------------------ #
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# ------------------------------------------------------------------ #
# Online mode — connect to the live DB and apply migrations.          #
# ------------------------------------------------------------------ #
def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # migrations don't need a pool
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Daily Workflow

```bash
# 1. Generate a new revision from model changes (autogenerate compares
#    Base.metadata to the current DB schema and writes the diff).
alembic revision --autogenerate -m "add avatar_url to users"

# 2. Review the generated file in alembic/versions/ — ALWAYS review
#    before applying. Autogenerate misses some things (e.g. CONCURRENTLY).

# 3. Apply all pending migrations to the database.
alembic upgrade head

# 4. Roll back the most recent migration.
alembic downgrade -1

# 5. Roll back to a specific revision.
alembic downgrade ae1027a6acf

# 6. Show current revision and pending migrations.
alembic current
alembic history --verbose

# 7. Emit SQL without touching the DB (dry run / CI validation).
alembic upgrade head --sql
```

### Revision File Anatomy

```python
# alembic/versions/20240115_001_add_avatar_url_to_users.py
"""add avatar_url to users

Revision ID: ae1027a6acf
Revises: 1975ea83b712
Create Date: 2024-01-15 10:22:04.831247
"""

from alembic import op
import sqlalchemy as sa

revision = "ae1027a6acf"
down_revision = "1975ea83b712"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_url", sa.Text(), nullable=True))
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_column("users", "avatar_url")
```

### Common op Operations

```python
from alembic import op
import sqlalchemy as sa

# --- Column operations ---
op.add_column("products", sa.Column("slug", sa.String(255), nullable=True))
op.alter_column("products", "price", type_=sa.Numeric(10, 2), nullable=False)
op.drop_column("products", "legacy_sku")
op.rename_table("old_name", "new_name")

# --- Index operations ---
# Standard index
op.create_index("ix_products_slug", "products", ["slug"], unique=True)
# Partial index (PostgreSQL)
op.create_index(
    "ix_orders_pending",
    "orders",
    ["created_at"],
    postgresql_where=sa.text("status = 'pending'"),
)
op.drop_index("ix_products_slug", table_name="products")

# --- Constraint operations ---
op.create_unique_constraint("uq_users_email", "users", ["email"])
op.create_foreign_key(
    "fk_orders_user_id",
    "orders", "users",
    ["user_id"], ["id"],
    ondelete="CASCADE",
)
op.drop_constraint("uq_users_email", "users", type_="unique")

# --- Raw SQL for operations Alembic cannot express ---
# Use for CONCURRENTLY indexes — cannot run inside a transaction block.
op.execute("COMMIT")  # close the implicit transaction first
op.execute(
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_products_slug ON products (slug)"
)
```

### Batch Mode — Required for SQLite

SQLite does not support `ALTER TABLE ... ADD COLUMN NOT NULL`, `DROP COLUMN`, or `RENAME COLUMN` directly. Use batch mode to work around these limitations (Alembic copies, alters, and renames the table atomically):

```python
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # batch_alter_table creates a temp table, copies data, drops original,
    # renames temp → original. Always required for SQLite structural changes.
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("display_name", sa.String(120), nullable=True))
        batch_op.alter_column(
            "email",
            existing_type=sa.String(200),
            type_=sa.String(255),
            nullable=False,
        )
        batch_op.drop_column("legacy_field")
        batch_op.create_index("ix_users_display_name", ["display_name"])

def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index("ix_users_display_name")
        batch_op.add_column(sa.Column("legacy_field", sa.Text(), nullable=True))
        batch_op.alter_column(
            "email",
            existing_type=sa.String(255),
            type_=sa.String(200),
            nullable=True,
        )
        batch_op.drop_column("display_name")
```

Enable batch mode globally in `env.py` so autogenerate uses it automatically for SQLite:

```python
# In do_run_migrations(), add render_as_batch when on SQLite:
context.configure(
    connection=connection,
    target_metadata=target_metadata,
    render_as_batch=connection.dialect.name == "sqlite",
)
```

### Autogenerate — What It Catches and What It Misses

**Caught automatically:**
- Table additions and removals
- Column additions, removals, and type changes
- Nullable changes
- Index additions and removals (named indexes only)
- Basic constraint changes

**NOT caught — write by hand:**
- `CREATE INDEX CONCURRENTLY` (requires manual `op.execute`)
- Sequence changes
- Stored procedures / functions / triggers / views
- `CHECK` constraints (partially supported; verify output)
- Data migrations (backfills) — always write these by hand

### Data Migrations (Backfills)

Keep DDL and DML in separate revision files. A data migration that touches millions of rows should never share a transaction with a schema change.

```python
# alembic/versions/20240116_002_backfill_display_name.py
"""backfill display_name from username

Revision ID: bf3c19d44e01
Revises: ae1027a6acf
"""

from alembic import op
import sqlalchemy as sa

revision = "bf3c19d44e01"
down_revision = "ae1027a6acf"
branch_labels = None
depends_on = None

# Use ad-hoc table reflection — never import ORM models in migrations.
users = sa.table(
    "users",
    sa.column("id", sa.Integer),
    sa.column("username", sa.String),
    sa.column("display_name", sa.String),
)


def upgrade() -> None:
    conn = op.get_bind()
    # Batch in chunks to avoid long-running locks.
    batch_size = 5_000
    while True:
        subq = (
            sa.select(users.c.id)
            .where(users.c.display_name == None)  # noqa: E711
            .limit(batch_size)
            .with_for_update(skip_locked=True)
            .scalar_subquery()
        )
        result = conn.execute(
            sa.update(users)
            .where(users.c.id.in_(subq))
            .values(display_name=users.c.username)
            .returning(users.c.id)
        )
        if result.rowcount == 0:
            break


def downgrade() -> None:
    # Data migrations are typically irreversible — document why.
    pass  # display_name values cannot be reliably reverted to None
```

### Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Import ORM models in migration file | Use `sa.table` / `sa.column` ad-hoc reflection instead; models evolve and break old revisions |
| `alembic upgrade head` fails with "Target database is not up to date" | Run `alembic current` to find diverged heads; resolve with `alembic merge heads` |
| `autogenerate` shows no changes but schema drifted | Confirm `target_metadata = Base.metadata` imports ALL models (some projects lazy-import) |
| Concurrent index creation fails inside a transaction | Call `op.execute("COMMIT")` first, then `op.execute("CREATE INDEX CONCURRENTLY ...")` |
| SQLite `ALTER TABLE` error | Wrap in `op.batch_alter_table` — SQLite requires table-copy approach |
| Revision applied in prod but not in dev | Always run `alembic upgrade head` in every environment after pulling; never skip |

## Zero-Downtime Migration Strategy

For critical production changes, follow the expand-contract pattern:

```
Phase 1: EXPAND
  - Add new column/table (nullable or with default)
  - Deploy: app writes to BOTH old and new
  - Backfill existing data

Phase 2: MIGRATE
  - Deploy: app reads from NEW, writes to BOTH
  - Verify data consistency

Phase 3: CONTRACT
  - Deploy: app only uses NEW
  - Drop old column/table in separate migration
```

### Timeline Example

```
Day 1: Migration adds new_status column (nullable)
Day 1: Deploy app v2 — writes to both status and new_status
Day 2: Run backfill migration for existing rows
Day 3: Deploy app v3 — reads from new_status only
Day 7: Migration drops old status column
```

## Anti-Patterns

| Anti-Pattern | Why It Fails | Better Approach |
|-------------|-------------|-----------------|
| Manual SQL in production | No audit trail, unrepeatable | Always use migration files |
| Editing deployed migrations | Causes drift between environments | Create new migration instead |
| NOT NULL without default | Locks table, rewrites all rows | Add nullable, backfill, then add constraint |
| Inline index on large table | Blocks writes during build | CREATE INDEX CONCURRENTLY |
| Schema + data in one migration | Hard to rollback, long transactions | Separate migrations |
| Dropping column before removing code | Application errors on missing column | Remove code first, drop column next deploy |
