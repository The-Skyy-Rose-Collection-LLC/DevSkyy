# Database Migrations Guide

Production-ready database migration management for DevSkyy using Alembic and SQLAlchemy.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Common Commands](#common-commands)
- [Creating Migrations](#creating-migrations)
- [Best Practices](#best-practices)
- [Migration Workflow](#migration-workflow)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

## Overview

DevSkyy uses **Alembic** for database schema migrations with support for:

- SQLite (development)
- PostgreSQL (production - Neon, Supabase)
- MySQL (PlanetScale)

**Key Features:**

- Async SQLAlchemy support
- Auto-generation from model changes
- Reversible migrations (upgrade/downgrade)
- Environment-based configuration
- Multi-database backend support

## Quick Start

### Check Current Migration Status

```bash
# View current migration version
alembic current

# View migration history
alembic history --verbose

# Show pending migrations
alembic heads
```

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply migrations up to specific revision
alembic upgrade <revision_id>

# Apply next migration only
alembic upgrade +1
```

### Rollback Migrations

```bash
# Rollback to previous migration
alembic downgrade -1

# Rollback all migrations
alembic downgrade base

# Rollback to specific revision
alembic downgrade <revision_id>
```

## Common Commands

### View Migration Information

```bash
# Show current migration version
alembic current

# Show migration history
alembic history

# Show detailed migration history
alembic history --verbose

# Show SQL that would be executed (dry run)
alembic upgrade head --sql
```

### Create New Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add user_roles table"

# Create empty migration (manual)
alembic revision -m "Add custom index"
```

### Apply/Revert Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific number of migrations
alembic upgrade +2

# Revert last migration
alembic downgrade -1

# Revert to specific revision
alembic downgrade abc123def456

# Revert all migrations
alembic downgrade base
```

### Stamp Database

```bash
# Mark database as being at specific revision (without running migrations)
alembic stamp head

# Useful for marking existing databases
alembic stamp <revision_id>
```

## Creating Migrations

### Auto-Generate from Models

**Step 1: Update your SQLAlchemy models**

Edit `models_sqlalchemy.py`:

```python
class NewModel(Base):
    __tablename__ = "new_table"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Step 2: Generate migration**

```bash
alembic revision --autogenerate -m "Add new_table"
```

**Step 3: Review generated migration**

Check `alembic/versions/YYYYMMDD_HHMM_<revision>_add_new_table.py`:

```python
def upgrade() -> None:
    op.create_table('new_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('new_table')
```

**Step 4: Apply migration**

```bash
alembic upgrade head
```

### Manual Migrations

For complex changes, create manual migrations:

```bash
alembic revision -m "Add composite index"
```

Edit the generated file:

```python
def upgrade() -> None:
    """Add composite index for query optimization."""
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.create_index(
            'ix_orders_customer_status',
            ['customer_id', 'status'],
            unique=False
        )

def downgrade() -> None:
    """Remove composite index."""
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_index('ix_orders_customer_status')
```

## Best Practices

### 1. Always Review Auto-Generated Migrations

Auto-generated migrations may not capture all requirements:

- Verify column types and constraints
- Check indexes are created correctly
- Ensure foreign keys have proper ON DELETE behavior
- Add CHECK constraints where needed

### 2. Test Migrations Before Production

```bash
# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade -1

# Test full cycle
alembic downgrade base && alembic upgrade head
```

### 3. Write Safe Migrations

**Safe Operations:**
- Adding nullable columns
- Creating indexes
- Adding tables

**Risky Operations:**
- Dropping columns (data loss)
- Changing column types (potential data loss)
- Adding NOT NULL constraints to existing columns

**Example: Safe Column Addition**

```python
def upgrade() -> None:
    # Add column as nullable first
    op.add_column('users',
        sa.Column('phone_number', sa.String(20), nullable=True)
    )

    # Optionally backfill data
    # op.execute("UPDATE users SET phone_number = '000-000-0000' WHERE phone_number IS NULL")

    # Then make non-nullable in a future migration
```

### 4. Always Implement Downgrade

Never leave downgrade() empty:

```python
def downgrade() -> None:
    # GOOD: Proper rollback
    op.drop_column('users', 'phone_number')

    # BAD: No rollback
    # pass
```

### 5. Use Descriptive Migration Messages

```bash
# Good
alembic revision --autogenerate -m "Add user_roles table for RBAC"
alembic revision -m "Add index on orders.created_at for performance"

# Bad
alembic revision --autogenerate -m "update"
alembic revision -m "fix"
```

### 6. Multi-Phase Migrations for Breaking Changes

**Phase 1: Add new column (nullable)**

```python
def upgrade():
    op.add_column('users', sa.Column('new_field', sa.String(100), nullable=True))
```

**Phase 2: Backfill data (separate deployment)**

```python
def upgrade():
    op.execute("UPDATE users SET new_field = old_field WHERE new_field IS NULL")
```

**Phase 3: Make non-nullable, drop old column**

```python
def upgrade():
    op.alter_column('users', 'new_field', nullable=False)
    op.drop_column('users', 'old_field')
```

## Migration Workflow

### Development Environment

1. **Update models** in `models_sqlalchemy.py`
2. **Generate migration**: `alembic revision --autogenerate -m "description"`
3. **Review migration** in `alembic/versions/`
4. **Test migration**: `alembic upgrade head`
5. **Verify changes**: Check database schema
6. **Test rollback**: `alembic downgrade -1`
7. **Commit migration file** to git

### Staging Environment

1. **Pull latest code** with migration files
2. **Review pending migrations**: `alembic current` and `alembic heads`
3. **Backup database** (if production data)
4. **Apply migrations**: `alembic upgrade head`
5. **Verify application** works correctly
6. **Test rollback** procedure (on test database)

### Production Deployment

1. **Backup database** (critical!)
2. **Enable maintenance mode** (optional, for zero-downtime)
3. **Pull latest code**
4. **Apply migrations**: `alembic upgrade head`
5. **Verify migration**: `alembic current`
6. **Test application** health checks
7. **Monitor for errors** (30 minutes)
8. **Rollback if needed**: `alembic downgrade <revision>`

## Troubleshooting

### Migration Fails with "Table already exists"

**Cause:** Database is out of sync with Alembic version tracking.

**Solution 1: Stamp database**

```bash
# Mark database as being at current model state
alembic stamp head
```

**Solution 2: Manual fix**

```bash
# Show current version
alembic current

# Manually drop conflicting tables
# Then rerun migration
alembic upgrade head
```

### Auto-generate detects no changes

**Cause:** Models not imported in `alembic/env.py`

**Solution:** Check `alembic/env.py` imports all models:

```python
from models_sqlalchemy import (
    User,
    Product,
    Customer,
    Order,
    AgentLog,
    BrandAsset,
    Campaign,
)
```

### SQLite foreign key errors

**Issue:** SQLite has limited ALTER TABLE support for foreign keys.

**Solution:** Use batch mode in migrations:

```python
with op.batch_alter_table('orders', schema=None) as batch_op:
    batch_op.create_foreign_key(
        'fk_orders_customer_id',
        'customers',
        ['customer_id'],
        ['id'],
        ondelete='SET NULL'
    )
```

### Database URL not found

**Cause:** Environment variables not set.

**Solution:** Set DATABASE_URL in `.env`:

```bash
# SQLite (development)
DATABASE_URL=sqlite+aiosqlite:///./devskyy.db

# PostgreSQL (production)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/database

# Or use Neon/Supabase URLs
NEON_DATABASE_URL=postgresql://user:pass@endpoint.neon.tech/database
```

### Migration creates duplicate indexes

**Cause:** Alembic detects indexes that already exist.

**Solution:** Drop old indexes manually before migration:

```bash
# View migration SQL without applying
alembic upgrade head --sql > migration.sql

# Review and remove duplicate CREATE INDEX statements
# Then apply cleaned migration
```

## Advanced Topics

### Branching and Merging Migrations

If multiple developers create migrations simultaneously:

```bash
# Check for multiple heads
alembic heads

# Merge branches
alembic merge -m "Merge feature branches" <rev1> <rev2>
```

### Custom Migration Templates

Edit `alembic/script.py.mako` to customize migration file template:

```python
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

Safety: <LOW|MEDIUM|HIGH> RISK - <reason>
Performance: <impact description>
"""
```

### Data Migrations

For migrating data during schema changes:

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade():
    # Define table representation
    users = table('users',
        column('id', sa.Integer),
        column('old_field', sa.String),
        column('new_field', sa.String)
    )

    # Migrate data
    op.execute(
        users.update().values(
            new_field=sa.func.upper(users.c.old_field)
        )
    )
```

### PostgreSQL-Specific Features

**Full-text search index:**

```python
def upgrade():
    op.execute("""
        CREATE INDEX idx_products_search
        ON products
        USING GIN (to_tsvector('english', name || ' ' || description))
    """)

def downgrade():
    op.drop_index('idx_products_search', table_name='products')
```

**Partial indexes:**

```python
def upgrade():
    op.create_index(
        'ix_orders_pending',
        'orders',
        ['created_at'],
        postgresql_where=sa.text("status = 'pending'")
    )
```

### Migration Validation Script

Create `.claude/scripts/validate_migration.py`:

```python
import sys
from alembic.config import Config
from alembic.script import ScriptDirectory

def validate_migration(revision_id):
    """Validate migration safety."""
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    revision = script.get_revision(revision_id)

    if not revision:
        print(f"ERROR: Revision {revision_id} not found")
        sys.exit(1)

    # Check for downgrade
    source = open(revision.path).read()
    if 'pass' in source and 'def downgrade' in source:
        print("WARNING: Empty downgrade() function detected")

    # Check for dangerous operations
    dangerous = ['drop_table', 'drop_column']
    for op in dangerous:
        if f'op.{op}' in source:
            print(f"WARNING: Dangerous operation detected: {op}")

    print("Validation complete")

if __name__ == '__main__':
    validate_migration('head')
```

## Environment Variables

Set in `.env` file:

```bash
# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./devskyy.db

# Or for PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/devskyy

# Or use provider-specific URLs
NEON_DATABASE_URL=postgresql://user:pass@endpoint.neon.tech/devskyy
SUPABASE_DATABASE_URL=postgresql://user:pass@db.supabase.co:5432/postgres

# Database Pool Configuration
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Environment
ENVIRONMENT=development  # or production
```

## Migration Files

### Location

- Configuration: `/home/user/DevSkyy/alembic.ini`
- Environment: `/home/user/DevSkyy/alembic/env.py`
- Migrations: `/home/user/DevSkyy/alembic/versions/`

### File Naming

Format: `YYYYMMDD_HHMM_<revision>_<description>.py`

Example: `20251116_0432_3d4bb411af09_initial_schema_baseline_7_core_models.py`

## Truth Protocol Compliance

### Migration Safety Checklist

Before applying migrations to production:

- [ ] Downgrade() function implemented
- [ ] Migration tested on staging
- [ ] Database backup completed
- [ ] No data loss risk identified
- [ ] Performance impact assessed
- [ ] Rollback procedure documented
- [ ] Migration peer-reviewed
- [ ] Monitoring alerts configured

### Security Considerations

- Never include credentials in migration files
- Use environment variables for database URLs
- Encrypt sensitive data at column level
- Add CHECK constraints for data validation
- Implement row-level security (PostgreSQL)

## Resources

- **Alembic Documentation**: https://alembic.sqlalchemy.org/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **DevSkyy Models**: `/home/user/DevSkyy/models_sqlalchemy.py`
- **Database Config**: `/home/user/DevSkyy/database_config.py`

## Support

For migration issues:

1. Check `alembic current` and `alembic history`
2. Review migration file in `alembic/versions/`
3. Test on development database first
4. Consult this guide's troubleshooting section
5. Check Alembic logs for detailed error messages

---

**Last Updated:** 2025-11-16
**Version:** 1.0.0
**Maintained by:** DevSkyy Platform Team
