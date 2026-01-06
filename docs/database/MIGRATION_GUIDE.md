# SQLAlchemy ORM Migration Guide

**Version**: 1.0.0
**Last Updated**: 2026-01-06
**Audience**: Developers migrating from raw SQL to SQLAlchemy ORM

---

## Overview

This guide helps you convert existing raw SQL code to use SQLAlchemy ORM models for improved type safety, maintainability, and developer experience.

---

## Why Migrate?

### Problems with Raw SQL

❌ **No Type Safety**: Easy to make typos, wrong column names
❌ **SQL Injection Risk**: Manual parameter binding required
❌ **No IDE Support**: No autocomplete, no refactoring tools
❌ **Hard to Test**: Requires actual database for testing
❌ **Boilerplate Code**: Repetitive query building and error handling
❌ **No Relationship Handling**: Manual JOIN queries for related data

### Benefits of ORM

✅ **Type Safety**: Compile-time error detection, IDE autocomplete
✅ **SQL Injection Protection**: Automatic parameterization
✅ **Developer Experience**: Relationships, eager loading, transactions
✅ **Easy Testing**: In-memory SQLite for fast unit tests
✅ **Less Code**: ORM handles common patterns automatically
✅ **Migration Support**: Automatic schema change detection

---

## Migration Patterns

### 1. Simple SELECT

**Before (Raw SQL)**:
```python
async def get_user_by_email(conn, email: str):
    result = await conn.fetchrow(
        "SELECT * FROM users WHERE email = $1",
        email
    )
    return dict(result) if result else None
```

**After (ORM)**:
```python
from sqlalchemy import select
from agents.models import User

async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
```

**Benefits**:
- Type hints on return value
- IDE autocomplete for `User` attributes
- No manual dictionary conversion
- Clearer intent

---

### 2. INSERT

**Before (Raw SQL)**:
```python
async def create_user(conn, email: str, username: str, password_hash: str):
    user_id = await conn.fetchval(
        """
        INSERT INTO users (email, username, password_hash, role, is_active)
        VALUES ($1, $2, $3, 'customer', true)
        RETURNING id
        """,
        email, username, password_hash
    )
    return user_id
```

**After (ORM)**:
```python
from agents.models import User

async def create_user(
    session: AsyncSession,
    email: str,
    username: str,
    password_hash: str
) -> User:
    user = User(
        email=email,
        username=username,
        password_hash=password_hash,
        role="customer",  # Default value, could be omitted
        is_active=True     # Default value, could be omitted
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)  # Loads server-generated values
    return user
```

**Benefits**:
- Returns full User object, not just ID
- Server defaults applied automatically
- Type-safe attribute access
- No SQL string concatenation

---

### 3. UPDATE

**Before (Raw SQL)**:
```python
async def update_product_price(conn, sku: str, new_price: Decimal):
    await conn.execute(
        "UPDATE products SET price = $1, updated_at = CURRENT_TIMESTAMP WHERE sku = $2",
        new_price, sku
    )
```

**After (ORM)**:
```python
from sqlalchemy import update
from agents.models import Product
from decimal import Decimal

async def update_product_price(session: AsyncSession, sku: str, new_price: Decimal):
    stmt = update(Product).where(Product.sku == sku).values(price=new_price)
    await session.execute(stmt)
    await session.commit()
    # updated_at is automatically updated by database trigger
```

**Alternative (Instance-based)**:
```python
from sqlalchemy import select

async def update_product_price(session: AsyncSession, sku: str, new_price: Decimal):
    # Get product
    stmt = select(Product).where(Product.sku == sku)
    result = await session.execute(stmt)
    product = result.scalar_one()

    # Update attribute
    product.price = new_price

    # Commit (no need for explicit update statement)
    await session.commit()
```

**Benefits**:
- `updated_at` handled by trigger (no manual update needed)
- Type checking on `new_price`
- Instance-based approach allows validation before commit

---

### 4. DELETE

**Before (Raw SQL)**:
```python
async def delete_user(conn, user_id: UUID):
    await conn.execute("DELETE FROM users WHERE id = $1", user_id)
```

**After (ORM)**:
```python
from sqlalchemy import delete
from agents.models import User
from uuid import UUID

async def delete_user(session: AsyncSession, user_id: UUID):
    stmt = delete(User).where(User.id == user_id)
    await session.execute(stmt)
    await session.commit()
```

**Alternative (Instance-based)**:
```python
async def delete_user(session: AsyncSession, user_id: UUID):
    user = await session.get(User, user_id)
    if user:
        await session.delete(user)
        await session.commit()
```

---

### 5. JOIN Queries

**Before (Raw SQL)**:
```python
async def get_orders_with_users(conn):
    rows = await conn.fetch(
        """
        SELECT
            o.id, o.order_number, o.total_price,
            u.id as user_id, u.email, u.username
        FROM orders o
        LEFT JOIN users u ON o.user_id = u.id
        WHERE o.status = 'completed'
        """
    )
    return [dict(row) for row in rows]
```

**After (ORM)**:
```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from agents.models import Order, User

async def get_orders_with_users(session: AsyncSession) -> list[Order]:
    stmt = (
        select(Order)
        .options(selectinload(Order.user))  # Eager load relationship
        .where(Order.status == "completed")
    )
    result = await session.execute(stmt)
    orders = result.scalars().all()

    # Access user via relationship
    for order in orders:
        if order.user:
            print(f"Order by {order.user.email}")

    return orders
```

**Benefits**:
- No manual JOIN syntax
- Relationship traversal via `order.user`
- Eager loading prevents N+1 queries
- Returns typed objects, not dictionaries

---

### 6. Complex WHERE Clauses

**Before (Raw SQL)**:
```python
async def search_products(
    conn,
    category: str = None,
    min_price: Decimal = None,
    max_price: Decimal = None
):
    conditions = ["status = 'published'"]
    params = []

    if category:
        params.append(category)
        conditions.append(f"category = ${len(params)}")
    if min_price:
        params.append(min_price)
        conditions.append(f"price >= ${len(params)}")
    if max_price:
        params.append(max_price)
        conditions.append(f"price <= ${len(params)}")

    query = f"SELECT * FROM products WHERE {' AND '.join(conditions)}"
    rows = await conn.fetch(query, *params)
    return [dict(row) for row in rows]
```

**After (ORM)**:
```python
from sqlalchemy import select
from agents.models import Product
from decimal import Decimal

async def search_products(
    session: AsyncSession,
    category: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None
) -> list[Product]:
    stmt = select(Product).where(Product.status == "published")

    if category:
        stmt = stmt.where(Product.category == category)
    if min_price:
        stmt = stmt.where(Product.price >= min_price)
    if max_price:
        stmt = stmt.where(Product.price <= max_price)

    result = await session.execute(stmt)
    return result.scalars().all()
```

**Benefits**:
- No manual parameter counting
- Clearer logic flow
- Type-safe comparisons
- No SQL string concatenation

---

### 7. Aggregations

**Before (Raw SQL)**:
```python
async def get_order_stats(conn, user_id: UUID):
    row = await conn.fetchrow(
        """
        SELECT
            COUNT(*) as total_orders,
            SUM(total_price) as total_spent,
            AVG(total_price) as avg_order_value
        FROM orders
        WHERE user_id = $1
        """,
        user_id
    )
    return dict(row)
```

**After (ORM)**:
```python
from sqlalchemy import select, func
from agents.models import Order
from uuid import UUID

async def get_order_stats(session: AsyncSession, user_id: UUID) -> dict:
    stmt = select(
        func.count(Order.id).label("total_orders"),
        func.sum(Order.total_price).label("total_spent"),
        func.avg(Order.total_price).label("avg_order_value")
    ).where(Order.user_id == user_id)

    result = await session.execute(stmt)
    row = result.one()

    return {
        "total_orders": row.total_orders,
        "total_spent": float(row.total_spent or 0),
        "avg_order_value": float(row.avg_order_value or 0)
    }
```

---

### 8. Pagination

**Before (Raw SQL)**:
```python
async def get_products_page(conn, page: int, per_page: int):
    offset = (page - 1) * per_page
    rows = await conn.fetch(
        """
        SELECT * FROM products
        WHERE status = 'published'
        ORDER BY created_at DESC
        LIMIT $1 OFFSET $2
        """,
        per_page, offset
    )
    return [dict(row) for row in rows]
```

**After (ORM)**:
```python
from sqlalchemy import select
from agents.models import Product

async def get_products_page(
    session: AsyncSession,
    page: int,
    per_page: int
) -> list[Product]:
    offset = (page - 1) * per_page

    stmt = (
        select(Product)
        .where(Product.status == "published")
        .order_by(Product.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )

    result = await session.execute(stmt)
    return result.scalars().all()
```

---

### 9. Transactions

**Before (Raw SQL)**:
```python
async def create_order_with_items(conn, user_id: UUID, items: list):
    async with conn.transaction():
        # Create order
        order_id = await conn.fetchval(
            """
            INSERT INTO orders (order_number, user_id, subtotal, total_price, status)
            VALUES ($1, $2, $3, $4, 'pending')
            RETURNING id
            """,
            generate_order_number(), user_id, subtotal, total
        )

        # Create order items
        for item in items:
            await conn.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES ($1, $2, $3, $4)",
                order_id, item['product_id'], item['quantity'], item['price']
            )

        return order_id
```

**After (ORM)**:
```python
from agents.models import Order
from uuid import UUID

async def create_order_with_items(
    session: AsyncSession,
    user_id: UUID,
    items: list,
    subtotal: Decimal,
    total: Decimal
) -> Order:
    # Transaction is implicit with session
    order = Order(
        order_number=generate_order_number(),
        user_id=user_id,
        subtotal=subtotal,
        total_price=total,
        status="pending",
        metadata={"items": items}  # Store items in JSONB
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order
```

**Note**: If you need a separate `order_items` table, create the model first, then use relationships.

---

### 10. Error Handling

**Before (Raw SQL)**:
```python
from asyncpg.exceptions import UniqueViolationError

async def create_user_safe(conn, email: str, username: str):
    try:
        user_id = await conn.fetchval(
            "INSERT INTO users (email, username, password_hash) VALUES ($1, $2, $3) RETURNING id",
            email, username, "hash"
        )
        return user_id
    except UniqueViolationError:
        raise ValueError("User already exists")
```

**After (ORM)**:
```python
from sqlalchemy.exc import IntegrityError
from agents.models import User

async def create_user_safe(
    session: AsyncSession,
    email: str,
    username: str
) -> User:
    try:
        user = User(email=email, username=username, password_hash="hash")
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    except IntegrityError:
        await session.rollback()
        raise ValueError("User already exists")
```

---

## Connection Management

### Before (asyncpg)

```python
import asyncpg

# Create pool
pool = await asyncpg.create_pool(
    host='localhost',
    port=5432,
    user='user',
    password='password',
    database='devskyy'
)

# Use connection
async with pool.acquire() as conn:
    result = await conn.fetch("SELECT * FROM users")
```

### After (SQLAlchemy)

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Create engine
engine = create_async_engine(
    "postgresql+asyncpg://user:password@localhost/devskyy",
    pool_size=20,
    max_overflow=10
)

# Create session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Use session
async with AsyncSessionLocal() as session:
    from sqlalchemy import select
    from agents.models import User

    stmt = select(User)
    result = await session.execute(stmt)
    users = result.scalars().all()
```

---

## FastAPI Integration

### Before (asyncpg)

```python
from fastapi import FastAPI, Depends
import asyncpg

app = FastAPI()

# Database pool
pool: asyncpg.Pool = None

@app.on_event("startup")
async def startup():
    global pool
    pool = await asyncpg.create_pool(database_url)

async def get_db():
    async with pool.acquire() as conn:
        yield conn

@app.get("/users")
async def list_users(conn = Depends(get_db)):
    rows = await conn.fetch("SELECT * FROM users")
    return [dict(row) for row in rows]
```

### After (SQLAlchemy)

```python
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

# Session dependency
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

@app.get("/users")
async def list_users(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from agents.models import User

    stmt = select(User)
    result = await db.execute(stmt)
    return result.scalars().all()
```

---

## Testing Migration

### Before (asyncpg with real database)

```python
import pytest
import asyncpg

@pytest.fixture
async def db_conn():
    conn = await asyncpg.connect("postgresql://localhost/test_db")
    yield conn
    await conn.close()

@pytest.mark.asyncio
async def test_create_user(db_conn):
    await db_conn.execute(
        "INSERT INTO users (email, username, password_hash) VALUES ($1, $2, $3)",
        "test@example.com", "testuser", "hash"
    )
    row = await db_conn.fetchrow("SELECT * FROM users WHERE email = $1", "test@example.com")
    assert row['email'] == "test@example.com"
```

### After (SQLAlchemy with in-memory SQLite)

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from agents.models import Base, User

@pytest.fixture
async def db_session():
    # In-memory SQLite - no real database needed!
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()

@pytest.mark.asyncio
async def test_create_user(db_session):
    user = User(email="test@example.com", username="testuser", password_hash="hash")
    db_session.add(user)
    await db_session.commit()

    from sqlalchemy import select
    stmt = select(User).where(User.email == "test@example.com")
    result = await db_session.execute(stmt)
    found_user = result.scalar_one()

    assert found_user.email == "test@example.com"
```

**Benefits**:
- No PostgreSQL server needed for tests
- Tests run faster (in-memory)
- No cleanup required
- Isolated test data

---

## Step-by-Step Migration Process

### Phase 1: Setup

1. ✅ Install dependencies: `sqlalchemy`, `alembic`, `asyncpg`
2. ✅ Create ORM models in `agents/models.py`
3. ✅ Link to Alembic in `alembic/env.py`
4. ✅ Run migrations: `alembic upgrade head`

### Phase 2: Create New Code with ORM

5. Write all NEW features using ORM models
6. Write tests using in-memory SQLite
7. Verify performance is acceptable

### Phase 3: Migrate Existing Code

8. Identify modules with raw SQL (grep for `conn.fetch`, `conn.execute`)
9. For each module:
   - Write ORM equivalent
   - Add tests
   - Run both versions in parallel (canary)
   - Switch to ORM version
   - Remove raw SQL

### Phase 4: Cleanup

10. Remove asyncpg pool management
11. Remove raw SQL helpers
12. Update documentation
13. Train team on ORM patterns

---

## Common Pitfalls

### 1. Forgetting to Commit

```python
# ❌ Wrong - changes not saved
user = User(email="test@example.com", ...)
session.add(user)
# Missing: await session.commit()

# ✅ Correct
user = User(email="test@example.com", ...)
session.add(user)
await session.commit()
```

### 2. N+1 Queries

```python
# ❌ Wrong - queries database for each user's orders
users = await session.execute(select(User))
for user in users.scalars():
    print(len(user.orders))  # N+1 query!

# ✅ Correct - single query with eager loading
from sqlalchemy.orm import selectinload
stmt = select(User).options(selectinload(User.orders))
users = await session.execute(stmt)
for user in users.scalars():
    print(len(user.orders))  # No additional queries
```

### 3. Accessing Lazy Relationships

```python
# ❌ Wrong - relationship not loaded in async
user = await session.get(User, user_id)
orders = user.orders  # Error in async!

# ✅ Correct - use eager loading
stmt = select(User).options(selectinload(User.orders)).where(User.id == user_id)
result = await session.execute(stmt)
user = result.scalar_one()
orders = user.orders  # Works!
```

---

## Performance Comparison

### Raw SQL (asyncpg)

✅ Slightly faster for simple queries
✅ Lower memory overhead
❌ More code to write
❌ Error-prone
❌ Hard to maintain

### ORM (SQLAlchemy)

✅ Type-safe and maintainable
✅ Less code
✅ Easy to test
✅ Relationship handling
❌ Slight overhead (~5-10% slower)
❌ Learning curve

**Recommendation**: Use ORM unless you have proven performance issues. For critical hot paths, you can still use raw SQL via `session.execute(text("SELECT ..."))`.

---

## Gradual Migration Strategy

You don't have to migrate everything at once! Use this strategy:

1. **Coexist**: Keep asyncpg pool alongside SQLAlchemy
2. **New Code**: All new features use ORM
3. **Hot Paths**: Keep raw SQL for proven bottlenecks
4. **Gradually Migrate**: Convert old code module by module
5. **Measure**: Compare performance before/after
6. **Remove**: Remove asyncpg when migration complete

---

## Need Help?

- **ORM Basics**: See [Quick Start Guide](./QUICK_START.md)
- **Model Reference**: See [ORM Models Documentation](./ORM_MODELS.md)
- **Database Patterns**: See [Database README](./README.md)
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/en/20/

---

**Last Updated**: 2026-01-06
**Maintained By**: DevSkyy Platform Team
