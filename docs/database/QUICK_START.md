# Database ORM Quick Start Guide

**Version**: 1.0.0
**Last Updated**: 2026-01-06

---

## 5-Minute Quick Start

### 1. Import Models

```python
from agents.models import (
    User,
    Product,
    Order,
    LLMRoundTableResult,
    AgentExecution,
    ToolExecution,
    RAGDocument,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from uuid import UUID
from decimal import Decimal
```

### 2. Setup Database Connection

```python
# Create async engine
engine = create_async_engine(
    "postgresql+asyncpg://user:password@localhost/devskyy",
    echo=True,  # Set to False in production
    pool_size=20,
    max_overflow=10
)

# Create session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency for FastAPI
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

### 3. Create Records

```python
async def create_user(session: AsyncSession):
    user = User(
        email="customer@example.com",
        username="customer123",
        password_hash="hashed_password",
        full_name="Jane Doe",
        role="customer",
        metadata={"preferences": {"theme": "dark"}}
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
```

### 4. Query Records

```python
from sqlalchemy import select

async def get_user_by_email(session: AsyncSession, email: str):
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_active_products(session: AsyncSession):
    stmt = select(Product).where(Product.status == "published")
    result = await session.execute(stmt)
    return result.scalars().all()
```

### 5. Update Records

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

### 6. Delete Records

```python
from sqlalchemy import delete

async def delete_user(session: AsyncSession, user_id: UUID):
    stmt = delete(User).where(User.id == user_id)
    await session.execute(stmt)
    await session.commit()
```

---

## Common Patterns

### Create with Relationship

```python
async def create_order_with_user(session: AsyncSession, user_email: str):
    # Get user
    user = await get_user_by_email(session, user_email)

    # Create order
    order = Order(
        order_number="ORD-12345",
        user_id=user.id,
        subtotal=Decimal("100.00"),
        total_price=Decimal("110.00"),
        status="pending",
        metadata={
            "items": [{"sku": "SKU-001", "quantity": 2}],
            "shipping_address": {...}
        }
    )
    session.add(order)
    await session.commit()
    return order
```

### Query with Relationship (Eager Loading)

```python
from sqlalchemy.orm import selectinload

async def get_user_with_orders(session: AsyncSession, user_id: UUID):
    stmt = (
        select(User)
        .options(selectinload(User.orders))
        .where(User.id == user_id)
    )
    result = await session.execute(stmt)
    user = result.scalar_one()

    # Access orders without additional queries
    for order in user.orders:
        print(f"Order: {order.order_number} - ${order.total_price}")

    return user
```

### Pagination

```python
async def get_products_paginated(
    session: AsyncSession,
    page: int = 1,
    per_page: int = 20
):
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

### Search with Filters

```python
async def search_products(
    session: AsyncSession,
    category: str = None,
    min_price: Decimal = None,
    max_price: Decimal = None,
    status: str = "published"
):
    stmt = select(Product).where(Product.status == status)

    if category:
        stmt = stmt.where(Product.category == category)
    if min_price:
        stmt = stmt.where(Product.price >= min_price)
    if max_price:
        stmt = stmt.where(Product.price <= max_price)

    result = await session.execute(stmt)
    return result.scalars().all()
```

### Count Records

```python
from sqlalchemy import func

async def count_active_users(session: AsyncSession) -> int:
    stmt = select(func.count(User.id)).where(User.is_active == True)
    result = await session.execute(stmt)
    return result.scalar()
```

### Aggregation

```python
async def get_order_statistics(session: AsyncSession):
    stmt = select(
        func.count(Order.id).label("total_orders"),
        func.sum(Order.total_price).label("total_revenue"),
        func.avg(Order.total_price).label("avg_order_value")
    )
    result = await session.execute(stmt)
    row = result.one()

    return {
        "total_orders": row.total_orders,
        "total_revenue": float(row.total_revenue or 0),
        "avg_order_value": float(row.avg_order_value or 0)
    }
```

---

## FastAPI Integration

### Complete Example

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal

app = FastAPI()

# Pydantic schemas
class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    full_name: str | None = None

class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    full_name: str | None
    role: str
    is_active: bool

    class Config:
        from_attributes = True

# Endpoints
@app.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
    password_hash = pwd_context.hash(user_data.password)

    user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=password_hash,
        full_name=user_data.full_name,
        role="customer"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select

    stmt = select(User).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
```

---

## Testing Patterns

### Pytest Fixture

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from agents.models import Base

@pytest.fixture
async def db_session():
    """Create in-memory database for testing."""
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

---

## Error Handling

### Duplicate Key

```python
from sqlalchemy.exc import IntegrityError

async def create_user_safe(session: AsyncSession, email: str, username: str):
    try:
        user = User(
            email=email,
            username=username,
            password_hash="hash"
        )
        session.add(user)
        await session.commit()
        return user
    except IntegrityError:
        await session.rollback()
        raise ValueError("User with this email or username already exists")
```

### Not Found

```python
from sqlalchemy.exc import NoResultFound

async def get_user_required(session: AsyncSession, user_id: UUID):
    from sqlalchemy import select

    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)

    try:
        return result.scalar_one()
    except NoResultFound:
        raise ValueError(f"User {user_id} not found")
```

---

## Performance Tips

### 1. Use Eager Loading

```python
# ❌ Bad: N+1 queries
users = await session.execute(select(User))
for user in users.scalars():
    print(len(user.orders))  # Each iteration queries database

# ✅ Good: Single query
from sqlalchemy.orm import selectinload

stmt = select(User).options(selectinload(User.orders))
users = await session.execute(stmt)
for user in users.scalars():
    print(len(user.orders))  # No additional queries
```

### 2. Batch Operations

```python
# ❌ Bad: Multiple commits
for i in range(100):
    product = Product(sku=f"SKU-{i}", name=f"Product {i}", price=Decimal("10.00"))
    session.add(product)
    await session.commit()  # Slow!

# ✅ Good: Single commit
for i in range(100):
    product = Product(sku=f"SKU-{i}", name=f"Product {i}", price=Decimal("10.00"))
    session.add(product)
await session.commit()  # Fast!
```

### 3. Use Indexes

```python
# Queries on indexed columns are fast
stmt = select(User).where(User.email == "test@example.com")  # ✅ Indexed
stmt = select(Product).where(Product.sku == "SKU-001")  # ✅ Indexed

# Queries on non-indexed columns are slow
stmt = select(User).where(User.full_name == "Jane Doe")  # ❌ Not indexed
```

---

## Common Mistakes

### 1. Forgetting await

```python
# ❌ Wrong
result = session.execute(stmt)  # Returns coroutine

# ✅ Correct
result = await session.execute(stmt)
```

### 2. Not Committing

```python
# ❌ Wrong: Changes not saved
user = User(email="test@example.com", ...)
session.add(user)
# Missing: await session.commit()

# ✅ Correct
user = User(email="test@example.com", ...)
session.add(user)
await session.commit()
```

### 3. Accessing Relationships Without Loading

```python
# ❌ Wrong: Raises error in async
user = await session.get(User, user_id)
orders = user.orders  # Error: relationship not loaded

# ✅ Correct: Use eager loading
stmt = select(User).options(selectinload(User.orders)).where(User.id == user_id)
result = await session.execute(stmt)
user = result.scalar_one()
orders = user.orders  # Works!
```

---

## Cheat Sheet

### CRUD Operations

```python
# Create
obj = Model(...)
session.add(obj)
await session.commit()

# Read (by primary key)
obj = await session.get(Model, primary_key)

# Read (with query)
stmt = select(Model).where(Model.field == value)
result = await session.execute(stmt)
obj = result.scalar_one_or_none()

# Update (instance)
obj.field = new_value
await session.commit()

# Update (bulk)
stmt = update(Model).where(Model.field == value).values(field=new_value)
await session.execute(stmt)
await session.commit()

# Delete (instance)
await session.delete(obj)
await session.commit()

# Delete (bulk)
stmt = delete(Model).where(Model.field == value)
await session.execute(stmt)
await session.commit()
```

### Querying

```python
# Select all
stmt = select(Model)
result = await session.execute(stmt)
objects = result.scalars().all()

# Select with filter
stmt = select(Model).where(Model.field == value)

# Multiple filters (AND)
stmt = select(Model).where(Model.field1 == value1, Model.field2 == value2)

# OR condition
from sqlalchemy import or_
stmt = select(Model).where(or_(Model.field1 == value1, Model.field2 == value2))

# Order by
stmt = select(Model).order_by(Model.created_at.desc())

# Limit and offset
stmt = select(Model).offset(10).limit(20)

# Count
from sqlalchemy import func
stmt = select(func.count(Model.id))
result = await session.execute(stmt)
count = result.scalar()
```

---

## Next Steps

1. Read [ORM Models Documentation](./ORM_MODELS.md) for detailed model reference
2. Review [Database README](./README.md) for architecture overview
3. Run `python test_orm_alembic.py` to verify setup
4. Try examples in this guide
5. Build your first feature using ORM models

---

**Need Help?** See [Troubleshooting](./README.md#troubleshooting) or [ORM Models Documentation](./ORM_MODELS.md).
