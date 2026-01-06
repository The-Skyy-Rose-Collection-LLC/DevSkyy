# SQLAlchemy ORM Models Documentation

**Version**: 1.0.0
**Last Updated**: 2026-01-06
**Status**: Production

---

## Overview

This document describes the SQLAlchemy ORM models for the DevSkyy platform. All models are defined in `/agents/models.py` and are linked to Alembic for automated database migrations.

### Key Features

- **UUID Primary Keys**: All models use PostgreSQL UUID with automatic generation
- **Timezone-Aware Timestamps**: All timestamps include timezone information
- **JSONB Metadata**: Flexible metadata fields for extensibility
- **Proper Indexing**: Strategic indexes for query performance
- **Auto-Updated Timestamps**: Database triggers maintain `updated_at` fields
- **Type Safety**: Full type hints and Pydantic compatibility

---

## Models

### 1. User Model

**Table**: `users`
**Purpose**: Authentication, authorization, and user management

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, Auto-generated | Primary key |
| `email` | String(255) | NOT NULL, UNIQUE, Indexed | Email address |
| `username` | String(100) | NOT NULL, UNIQUE | Username |
| `password_hash` | String(255) | NOT NULL | Bcrypt/Argon2 hash |
| `full_name` | String(255) | NULL | User's full name |
| `role` | String(50) | Default: 'customer', Indexed | User role |
| `is_active` | Boolean | Default: true | Account active status |
| `is_verified` | Boolean | Default: false | Email verified status |
| `created_at` | TIMESTAMP(TZ) | Default: CURRENT_TIMESTAMP | Creation time |
| `updated_at` | TIMESTAMP(TZ) | Default: CURRENT_TIMESTAMP, Auto-updated | Last update time |
| `last_login` | TIMESTAMP(TZ) | NULL | Last login time |
| `metadata` | JSONB | Default: {} | Additional user data |

#### Relationships

- `orders`: One-to-Many relationship with Order model
- `tool_executions`: One-to-Many relationship with ToolExecution model

#### Example Usage

```python
from agents.models import User
from sqlalchemy.ext.asyncio import AsyncSession

# Create a new user
async def create_user(session: AsyncSession, email: str, username: str, password_hash: str):
    user = User(
        email=email,
        username=username,
        password_hash=password_hash,
        role="customer",
        metadata={"signup_source": "web", "preferences": {}}
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

# Query users
async def get_user_by_email(session: AsyncSession, email: str):
    from sqlalchemy import select

    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
```

---

### 2. Product Model

**Table**: `products`
**Purpose**: E-commerce product catalog

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, Auto-generated | Primary key |
| `sku` | String(100) | NOT NULL, UNIQUE, Indexed | Stock keeping unit |
| `name` | String(500) | NOT NULL | Product name |
| `description` | Text | NULL | Product description |
| `category` | String(100) | NULL | Product category |
| `price` | DECIMAL(10, 2) | NOT NULL | Current price |
| `inventory_quantity` | Integer | Default: 0 | Stock level |
| `status` | String(50) | Default: 'draft', Indexed | Product status |
| `tags` | ARRAY(Text) | NULL | Search/filter tags |
| `created_at` | TIMESTAMP(TZ) | Default: CURRENT_TIMESTAMP | Creation time |
| `updated_at` | TIMESTAMP(TZ) | Default: CURRENT_TIMESTAMP, Auto-updated | Last update time |
| `metadata` | JSONB | Default: {} | Variants, specs, etc. |

#### Valid Statuses

- `draft`: Not published
- `published`: Live on store
- `archived`: No longer available

#### Example Usage

```python
from agents.models import Product
from decimal import Decimal

async def create_product(session: AsyncSession, sku: str, name: str, price: Decimal):
    product = Product(
        sku=sku,
        name=name,
        price=price,
        category="Jewelry",
        tags=["premium", "luxury"],
        status="draft",
        inventory_quantity=10,
        metadata={
            "variants": [
                {"size": "small", "sku": f"{sku}-S"},
                {"size": "medium", "sku": f"{sku}-M"}
            ],
            "dimensions": {"weight": "10g", "length": "5cm"}
        }
    )
    session.add(product)
    await session.commit()
    return product
```

---

### 3. Order Model

**Table**: `orders`
**Purpose**: E-commerce order transactions

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, Auto-generated | Primary key |
| `order_number` | String(50) | NOT NULL, UNIQUE | Order number |
| `user_id` | UUID | FK(users.id), Indexed, NULL | Customer (null for guests) |
| `status` | String(50) | Default: 'pending', Indexed | Order status |
| `total_price` | DECIMAL(10, 2) | NOT NULL | Total with taxes/shipping |
| `subtotal` | DECIMAL(10, 2) | NOT NULL | Subtotal before extras |
| `created_at` | TIMESTAMP(TZ) | Default: CURRENT_TIMESTAMP | Order time |
| `updated_at` | TIMESTAMP(TZ) | Default: CURRENT_TIMESTAMP, Auto-updated | Last update |
| `metadata` | JSONB | Default: {} | Items, shipping, payment |

#### Valid Statuses

- `pending`: Awaiting payment
- `processing`: Payment received, fulfilling
- `completed`: Shipped/delivered
- `cancelled`: Order cancelled

#### Relationships

- `user`: Many-to-One relationship with User model

#### Example Usage

```python
from agents.models import Order
from decimal import Decimal
import uuid

async def create_order(session: AsyncSession, user_id: uuid.UUID, items: list):
    order = Order(
        order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
        user_id=user_id,
        subtotal=Decimal("100.00"),
        total_price=Decimal("115.00"),  # Including tax/shipping
        status="pending",
        metadata={
            "items": items,
            "shipping_address": {...},
            "payment_method": "stripe"
        }
    )
    session.add(order)
    await session.commit()
    return order
```

---

### 4. LLMRoundTableResult Model

**Table**: `llm_round_table_results`
**Purpose**: Store LLM Round Table competition results

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, Auto-generated | Primary key |
| `result_id` | String(100) | NOT NULL, UNIQUE | Result identifier |
| `prompt` | Text | NOT NULL | Original prompt |
| `task_category` | String(100) | Indexed | Task type |
| `winner_provider` | String(50) | NULL | Winning LLM |
| `winner_response` | Text | NULL | Winning response |
| `participants` | JSONB | NOT NULL | All results |
| `created_at` | TIMESTAMP(TZ) | Default: CURRENT_TIMESTAMP | Competition time |
| `metadata` | JSONB | Default: {} | Scores, metrics |

#### Task Categories

- `reasoning`: Chain-of-thought tasks
- `creative`: Creative writing/generation
- `classification`: Classification tasks
- `qa`: Question answering
- `code`: Code generation

#### Example Usage

```python
from agents.models import LLMRoundTableResult

async def save_round_table_result(session: AsyncSession, result_data: dict):
    result = LLMRoundTableResult(
        result_id=result_data["result_id"],
        prompt=result_data["prompt"],
        task_category="reasoning",
        winner_provider="anthropic",
        winner_response="...",
        participants=[
            {"provider": "anthropic", "response": "...", "score": 0.95},
            {"provider": "openai", "response": "...", "score": 0.87}
        ],
        metadata={"test_config": {...}}
    )
    session.add(result)
    await session.commit()
    return result
```

---

### 5. AgentExecution Model

**Table**: `agent_executions`
**Purpose**: Audit log for SuperAgent executions

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, Auto-generated | Primary key |
| `execution_id` | String(100) | NOT NULL, UNIQUE | Execution identifier |
| `agent_name` | String(100) | NOT NULL, Indexed | Agent name |
| `prompt` | Text | NOT NULL | User task/prompt |
| `status` | String(50) | Default: 'running', Indexed | Execution status |
| `result` | JSONB | NULL | Execution result |
| `tokens_used` | Integer | NULL | Total tokens |
| `duration_ms` | Integer | NULL | Duration (ms) |
| `created_at` | TIMESTAMP(TZ) | Default: CURRENT_TIMESTAMP | Start time |
| `metadata` | JSONB | Default: {} | Plan, tools, etc. |

#### Valid Statuses

- `running`: In progress
- `completed`: Successfully finished
- `failed`: Error occurred

#### Example Usage

```python
from agents.models import AgentExecution

async def log_agent_execution(
    session: AsyncSession,
    execution_id: str,
    agent_name: str,
    prompt: str
):
    execution = AgentExecution(
        execution_id=execution_id,
        agent_name=agent_name,
        prompt=prompt,
        status="running",
        metadata={"plan": {...}}
    )
    session.add(execution)
    await session.commit()
    return execution

async def complete_execution(session: AsyncSession, execution_id: str, result: dict):
    from sqlalchemy import select, update

    stmt = (
        update(AgentExecution)
        .where(AgentExecution.execution_id == execution_id)
        .values(
            status="completed",
            result=result,
            tokens_used=result.get("tokens_used"),
            duration_ms=result.get("duration_ms")
        )
    )
    await session.execute(stmt)
    await session.commit()
```

---

### 6. ToolExecution Model

**Table**: `tool_executions`
**Purpose**: Comprehensive audit trail for all tool executions

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, Auto-generated | Primary key |
| `correlation_id` | String(64) | NOT NULL, Indexed | Correlation ID |
| `tool_name` | String(128) | NOT NULL, Indexed | Tool name |
| `agent_id` | String(100) | NULL | Invoking agent |
| `user_id` | UUID | FK(users.id), NULL | Invoking user |
| `inputs` | JSONB | NOT NULL | Tool inputs |
| `output` | JSONB | NULL | Tool output |
| `status` | String(50) | NOT NULL, Indexed | Execution status |
| `duration_ms` | Integer | NULL | Duration (ms) |
| `error_message` | Text | NULL | Error details |
| `created_at` | TIMESTAMP(TZ) | Default: CURRENT_TIMESTAMP | Execution time |
| `metadata` | JSONB | Default: {} | Permissions, context |

#### Valid Statuses

- `success`: Completed successfully
- `failed`: Error occurred
- `timeout`: Execution timeout

#### Relationships

- `user`: Many-to-One relationship with User model

#### Example Usage

```python
from agents.models import ToolExecution

async def log_tool_execution(
    session: AsyncSession,
    correlation_id: str,
    tool_name: str,
    inputs: dict,
    agent_id: str = None,
    user_id: uuid.UUID = None
):
    execution = ToolExecution(
        correlation_id=correlation_id,
        tool_name=tool_name,
        agent_id=agent_id,
        user_id=user_id,
        inputs=inputs,
        status="success",  # or "failed"
        duration_ms=150,
        metadata={"permissions": ["READ"]}
    )
    session.add(execution)
    await session.commit()
    return execution
```

---

### 7. RAGDocument Model

**Table**: `rag_documents`
**Purpose**: Knowledge base for Retrieval-Augmented Generation

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, Auto-generated | Primary key |
| `document_id` | String(100) | NOT NULL, UNIQUE | Document identifier |
| `source_path` | String(500) | Indexed | File path/URL |
| `content` | Text | NOT NULL | Document content |
| `content_hash` | String(64) | NOT NULL, Indexed | SHA-256 hash |
| `chunk_index` | Integer | NULL | Chunk index |
| `total_chunks` | Integer | NULL | Total chunks |
| `embedding_model` | String(100) | NULL | Embedding model |
| `metadata` | JSONB | Default: {} | Author, tags, etc. |
| `created_at` | TIMESTAMP(TZ) | Default: CURRENT_TIMESTAMP | Ingestion time |
| `updated_at` | TIMESTAMP(TZ) | Default: CURRENT_TIMESTAMP, Auto-updated | Last update |

#### Example Usage

```python
from agents.models import RAGDocument
import hashlib

async def ingest_document(
    session: AsyncSession,
    document_id: str,
    source_path: str,
    content: str,
    chunk_index: int,
    total_chunks: int
):
    content_hash = hashlib.sha256(content.encode()).hexdigest()

    doc = RAGDocument(
        document_id=f"{document_id}-chunk-{chunk_index}",
        source_path=source_path,
        content=content,
        content_hash=content_hash,
        chunk_index=chunk_index,
        total_chunks=total_chunks,
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        metadata={
            "author": "DevSkyy",
            "tags": ["documentation", "api"],
            "parent_doc_id": document_id
        }
    )
    session.add(doc)
    await session.commit()
    return doc
```

---

## Database Triggers

### Auto-Update Triggers

The following tables have automatic `updated_at` triggers:

- `users`
- `products`
- `orders`
- `rag_documents`

**Function**: `update_updated_at_column()`

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

---

## Alembic Integration

### Configuration

The ORM models are linked to Alembic via `alembic/env.py`:

```python
from agents.models import Base
target_metadata = Base.metadata
```

### Running Migrations

```bash
# Generate a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1

# View migration history
alembic history --verbose

# View current version
alembic current
```

### Auto-Generate Migrations

Alembic can automatically detect schema changes:

```bash
# Make changes to models in agents/models.py
# Then run:
alembic revision --autogenerate -m "Add new column to users"

# Review the generated migration in alembic/versions/
# Then apply:
alembic upgrade head
```

---

## Best Practices

### 1. Always Use Async Sessions

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

engine = create_async_engine("postgresql+asyncpg://...")
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

### 2. Use Context Managers

```python
async with AsyncSessionLocal() as session:
    async with session.begin():
        # Your database operations
        user = User(email="test@example.com", ...)
        session.add(user)
        # Commit happens automatically
```

### 3. Leverage Relationships

```python
# Instead of manual joins
user = await session.get(User, user_id)
orders = user.orders  # Lazy-loaded relationship

# Eager loading for better performance
from sqlalchemy.orm import selectinload

stmt = select(User).options(selectinload(User.orders)).where(User.id == user_id)
result = await session.execute(stmt)
user = result.scalar_one()
```

### 4. Use Type Hints

```python
from typing import List
from agents.models import User

async def get_active_users(session: AsyncSession) -> List[User]:
    stmt = select(User).where(User.is_active == True)
    result = await session.execute(stmt)
    return result.scalars().all()
```

### 5. Handle Metadata Properly

```python
# JSONB metadata should be valid JSON
user = User(
    email="test@example.com",
    metadata={
        "preferences": {"theme": "dark"},
        "tags": ["premium", "verified"]
    }
)

# Access metadata
theme = user.metadata.get("preferences", {}).get("theme")
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
        password_hash="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()

    assert user.id is not None
    assert user.is_active is True
    assert user.role == "customer"
```

---

## Troubleshooting

### Common Issues

1. **Import Error**: Ensure `agents/` is in Python path
2. **Alembic Not Detecting Changes**: Check that `target_metadata = Base.metadata` in `env.py`
3. **UUID Generation**: Requires PostgreSQL extension `uuid-ossp`
4. **Timezone Issues**: Always use `TIMESTAMP(timezone=True)`

### Debug Queries

```python
from sqlalchemy import event
from sqlalchemy.engine import Engine
import logging

logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

# Will print all SQL queries
```

---

## Migration Checklist

When adding/modifying models:

- [ ] Update model in `agents/models.py`
- [ ] Add proper type hints and docstrings
- [ ] Run `alembic revision --autogenerate -m "Description"`
- [ ] Review generated migration
- [ ] Test migration: `alembic upgrade head`
- [ ] Test rollback: `alembic downgrade -1`
- [ ] Update this documentation
- [ ] Write tests for new functionality

---

## References

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [PostgreSQL Data Types](https://www.postgresql.org/docs/current/datatype.html)
- [DevSkyy Architecture Docs](/docs/architecture/DEVSKYY_MASTER_PLAN.md)

---

**Last Reviewed**: 2026-01-06
**Maintained By**: DevSkyy Platform Team
