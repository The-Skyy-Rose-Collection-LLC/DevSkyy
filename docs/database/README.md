# Database Documentation

**Version**: 1.0.0
**Last Updated**: 2026-01-06
**Status**: Production

---

## Overview

This directory contains comprehensive documentation for the DevSkyy database layer, including:

- **SQLAlchemy ORM models** (`agents/models.py`)
- **Alembic migrations** (`alembic/versions/`)
- **Database schemas** and best practices

---

## Quick Links

- [ORM Models Documentation](./ORM_MODELS.md) - Detailed model reference
- [Alembic Configuration](/alembic/) - Migration management
- [Baseline Schema](/alembic/versions/001_baseline_schema.py) - Initial database setup

---

## Database Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Database** | PostgreSQL | 14+ | Primary data store |
| **ORM** | SQLAlchemy | 2.0+ | Object-relational mapping |
| **Migrations** | Alembic | 1.13+ | Schema version control |
| **Connection Pool** | asyncpg | 0.29+ | Async PostgreSQL driver |

---

## Quick Start

### 1. Setup Database

```bash
# Install PostgreSQL (macOS)
brew install postgresql@14
brew services start postgresql@14

# Create database
createdb devskyy_dev
createdb devskyy_test

# Set environment variable
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/devskyy_dev"
```

### 2. Run Migrations

```bash
# Install dependencies
pip install sqlalchemy alembic asyncpg

# Run migrations
alembic upgrade head

# Verify
alembic current
```

### 3. Test ORM Models

```bash
# Run test script
python test_orm_alembic.py

# Expected output:
# ✅ Successfully imported all ORM models
# ✅ Base.metadata contains all 7 expected tables
# ✅ All tests passed!
```

---

## Architecture

### Schema Design Principles

1. **UUID Primary Keys**: All models use PostgreSQL UUID with `uuid_generate_v4()`
2. **Timezone-Aware Timestamps**: All timestamps include timezone (`TIMESTAMP(timezone=True)`)
3. **JSONB for Flexibility**: Metadata fields use JSONB for extensibility
4. **Strategic Indexing**: Indexes on frequently queried columns
5. **Foreign Key Constraints**: Referential integrity with `ON DELETE` actions
6. **Auto-Updated Timestamps**: Database triggers maintain `updated_at` fields

### Entity-Relationship Diagram

```
┌─────────────┐         ┌──────────────┐         ┌─────────────────────┐
│    User     │◄────────│    Order     │         │   ToolExecution     │
│             │         │              │         │                     │
│ id (PK)     │         │ id (PK)      │         │ id (PK)             │
│ email       │         │ user_id (FK) │         │ user_id (FK)        │
│ username    │         │ order_number │         │ tool_name           │
│ role        │         │ status       │         │ correlation_id      │
│ is_active   │         │ total_price  │         │ status              │
└─────────────┘         └──────────────┘         └─────────────────────┘

┌─────────────┐         ┌──────────────────────────┐
│   Product   │         │  LLMRoundTableResult     │
│             │         │                          │
│ id (PK)     │         │ id (PK)                  │
│ sku         │         │ result_id                │
│ name        │         │ prompt                   │
│ price       │         │ winner_provider          │
│ status      │         │ participants (JSONB)     │
└─────────────┘         └──────────────────────────┘

┌──────────────────┐    ┌────────────────────┐
│ AgentExecution   │    │   RAGDocument      │
│                  │    │                    │
│ id (PK)          │    │ id (PK)            │
│ execution_id     │    │ document_id        │
│ agent_name       │    │ content            │
│ status           │    │ content_hash       │
│ result (JSONB)   │    │ embedding_model    │
└──────────────────┘    └────────────────────┘
```

---

## Models Overview

### Core E-Commerce Models

1. **User** (`users`)
   - Authentication and authorization
   - Customer accounts
   - Relationships: orders, tool_executions

2. **Product** (`products`)
   - Product catalog
   - Inventory management
   - Pricing and metadata

3. **Order** (`orders`)
   - Transaction records
   - Order status tracking
   - Customer relationship

### AI/Agent Models

4. **LLMRoundTableResult** (`llm_round_table_results`)
   - Multi-LLM competition results
   - Performance metrics
   - Task categorization

5. **AgentExecution** (`agent_executions`)
   - SuperAgent audit logs
   - Execution tracking
   - Performance monitoring

6. **ToolExecution** (`tool_executions`)
   - Tool call audit trail
   - Security and compliance
   - Distributed tracing

### Knowledge Base Models

7. **RAGDocument** (`rag_documents`)
   - Document storage for RAG
   - Chunking and embeddings
   - Content deduplication

---

## Common Operations

### Creating Records

```python
from agents.models import User, Product, Order
from sqlalchemy.ext.asyncio import AsyncSession

async def create_user(session: AsyncSession):
    user = User(
        email="customer@example.com",
        username="customer123",
        password_hash="hashed_password",
        role="customer"
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
```

### Querying Records

```python
from sqlalchemy import select

async def get_active_users(session: AsyncSession):
    stmt = select(User).where(User.is_active == True)
    result = await session.execute(stmt)
    return result.scalars().all()
```

### Updating Records

```python
from sqlalchemy import update

async def update_product_price(session: AsyncSession, sku: str, new_price: Decimal):
    stmt = (
        update(Product)
        .where(Product.sku == sku)
        .values(price=new_price)
    )
    await session.execute(stmt)
    await session.commit()
```

### Using Relationships

```python
# Get user with all orders (eager loading)
from sqlalchemy.orm import selectinload

stmt = select(User).options(selectinload(User.orders)).where(User.id == user_id)
result = await session.execute(stmt)
user = result.scalar_one()

# Access orders
for order in user.orders:
    print(f"Order {order.order_number}: ${order.total_price}")
```

---

## Migration Workflow

### Creating Migrations

```bash
# 1. Modify models in agents/models.py
# 2. Generate migration
alembic revision --autogenerate -m "Add email_verified column to users"

# 3. Review generated migration in alembic/versions/
# 4. Test migration
alembic upgrade head

# 5. Test rollback
alembic downgrade -1
alembic upgrade head
```

### Migration Best Practices

1. **Always Review**: Never apply auto-generated migrations without review
2. **Test Rollbacks**: Ensure `downgrade()` works correctly
3. **Data Migrations**: Separate schema and data migrations
4. **Backup First**: Always backup production before migrations
5. **Small Batches**: Keep migrations focused and atomic

### Common Migration Commands

```bash
# View migration history
alembic history --verbose

# Show current version
alembic current

# Upgrade to specific version
alembic upgrade <revision>

# Downgrade to specific version
alembic downgrade <revision>

# Show SQL without executing
alembic upgrade head --sql
```

---

## Testing

### Unit Tests

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from agents.models import Base, User

@pytest.fixture
async def db_session():
    """Create in-memory SQLite database for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()

@pytest.mark.asyncio
async def test_create_user(db_session):
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash="hashed"
    )
    db_session.add(user)
    await db_session.commit()

    assert user.id is not None
    assert user.email == "test@example.com"
```

### Integration Tests

```python
@pytest.mark.integration
async def test_user_order_relationship(db_session):
    # Create user
    user = User(email="test@example.com", username="test", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    # Create order
    order = Order(
        order_number="ORD-12345",
        user_id=user.id,
        subtotal=Decimal("100.00"),
        total_price=Decimal("110.00")
    )
    db_session.add(order)
    await db_session.commit()

    # Test relationship
    await db_session.refresh(user)
    assert len(user.orders) == 1
    assert user.orders[0].order_number == "ORD-12345"
```

---

## Performance Optimization

### Connection Pooling

```python
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

# Production configuration
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/devskyy",
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False  # Disable in production
)
```

### Query Optimization

```python
# ❌ Bad: N+1 queries
users = await session.execute(select(User))
for user in users.scalars():
    # Each iteration triggers a separate query
    print(len(user.orders))

# ✅ Good: Eager loading
from sqlalchemy.orm import selectinload

stmt = select(User).options(selectinload(User.orders))
users = await session.execute(stmt)
for user in users.scalars():
    print(len(user.orders))  # No additional queries
```

### Indexing Strategy

```python
# Define custom indexes in models
from sqlalchemy import Index

class User(Base):
    __tablename__ = "users"
    # ... columns ...

    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_created', 'created_at'),
    )
```

---

## Security Considerations

### 1. SQL Injection Prevention

```python
# ✅ Safe: Parameterized queries
stmt = select(User).where(User.email == email_input)

# ❌ Unsafe: String concatenation
# stmt = text(f"SELECT * FROM users WHERE email = '{email_input}'")
```

### 2. Password Hashing

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Hash password
password_hash = pwd_context.hash("user_password")

# Store in database
user = User(
    email="user@example.com",
    password_hash=password_hash
)
```

### 3. Sensitive Data

```python
# Never log sensitive fields
class User(Base):
    password_hash = Column(String(255), nullable=False)

    def __repr__(self):
        # Exclude password_hash from representation
        return f"<User(id={self.id}, email={self.email})>"
```

---

## Troubleshooting

### Common Issues

#### 1. "uuid_generate_v4() does not exist"

**Solution**: Enable PostgreSQL extension

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

Or in Alembic migration:

```python
op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
```

#### 2. "Target metadata is None"

**Solution**: Update `alembic/env.py`:

```python
from agents.models import Base
target_metadata = Base.metadata
```

#### 3. "Import Error: No module named agents"

**Solution**: Ensure project root is in Python path:

```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/DevSkyy"
# Or
pip install -e .
```

#### 4. Timezone Issues

**Solution**: Always use timezone-aware timestamps:

```python
from datetime import datetime, timezone

# ✅ Correct
now = datetime.now(timezone.utc)

# ❌ Incorrect
# now = datetime.now()
```

---

## Environment Variables

### Required

```bash
# PostgreSQL connection URL
DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/devskyy_dev"
```

### Optional

```bash
# Database pool size
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Enable SQL logging (development only)
DB_ECHO=false

# Connection timeout
DB_POOL_TIMEOUT=30
```

---

## Production Checklist

- [ ] Enable connection pooling
- [ ] Configure proper pool sizes based on load
- [ ] Disable SQL echo logging
- [ ] Set up read replicas for scaling
- [ ] Configure automated backups
- [ ] Enable slow query logging
- [ ] Set up monitoring and alerting
- [ ] Test migration rollback procedures
- [ ] Document disaster recovery plan
- [ ] Encrypt sensitive data at rest
- [ ] Use SSL/TLS for connections

---

## References

### Internal Documentation

- [ORM Models Reference](./ORM_MODELS.md)
- [Architecture Overview](/docs/architecture/DEVSKYY_MASTER_PLAN.md)
- [Security Best Practices](/docs/security/)

### External Resources

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)

---

## Support

**Questions?** Check the troubleshooting section or contact the DevSkyy platform team.

**Found a bug?** Create an issue with the `database` label.

**Last Reviewed**: 2026-01-06
**Maintained By**: DevSkyy Platform Team
