"""Tests for database models, repositories, and seeding.

Covers: User, Product, Order models, repository CRUD,
and catalog/admin seeding.
"""

from __future__ import annotations

import json
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.db import (
    Base,
    DatabaseConfig,
    Product,
    ProductRepository,
    User,
    UserRepository,
)


@pytest.fixture
async def db():
    """Create an in-memory SQLite database for testing (bypasses singleton)."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as session:
        yield session

    await engine.dispose()


# =============================================================================
# Model Creation Tests
# =============================================================================


class TestUserModel:
    """Tests for User ORM model."""

    @pytest.mark.asyncio
    async def test_create_user(self, db):
        user = User(
            id=str(uuid.uuid4()),
            email="test@skyyrose.co",
            username="testuser",
            hashed_password="$argon2id$v=19$m=65536,t=3,p=4$hash",
            role="api_user",
        )
        db.add(user)
        await db.flush()
        assert user.id is not None
        assert user.is_active is True
        assert user.is_verified is False

    @pytest.mark.asyncio
    async def test_user_has_lockout_fields(self, db):
        user = User(
            id=str(uuid.uuid4()),
            email="lock@test.co",
            username="lockuser",
            hashed_password="hash",
            role="api_user",
            failed_login_attempts=3,
        )
        db.add(user)
        await db.flush()
        assert user.failed_login_attempts == 3
        assert user.locked_until is None


class TestProductModel:
    """Tests for Product ORM model."""

    @pytest.mark.asyncio
    async def test_create_product(self, db):
        product = Product(
            id=str(uuid.uuid4()),
            sku="br-001",
            name="BLACK Rose Crewneck",
            price=35.00,
            collection="black-rose",
            category="Crewnecks",
            quantity=250,
        )
        db.add(product)
        await db.flush()
        assert product.sku == "br-001"
        assert product.is_active is True

    @pytest.mark.asyncio
    async def test_product_with_variants(self, db):
        variants = json.dumps({"sizes": ["S", "M", "L"], "color": "Black"})
        product = Product(
            id=str(uuid.uuid4()),
            sku="test-v1",
            name="Variant Test",
            price=10.0,
            variants_json=variants,
        )
        db.add(product)
        await db.flush()
        parsed = json.loads(product.variants_json)
        assert parsed["sizes"] == ["S", "M", "L"]


# =============================================================================
# Repository Tests
# =============================================================================


class TestUserRepository:
    """Tests for UserRepository data access."""

    @pytest.mark.asyncio
    async def test_get_by_email(self, db):
        uid = str(uuid.uuid4())
        user = User(
            id=uid,
            email="repo@test.co",
            username="repouser",
            hashed_password="hash",
            role="api_user",
        )
        db.add(user)
        await db.flush()

        repo = UserRepository(db)
        found = await repo.get_by_email("repo@test.co")
        assert found is not None
        assert found.id == uid

    @pytest.mark.asyncio
    async def test_get_by_username(self, db):
        uid = str(uuid.uuid4())
        user = User(
            id=uid,
            email="uname@test.co",
            username="unameuser",
            hashed_password="hash",
            role="api_user",
        )
        db.add(user)
        await db.flush()

        repo = UserRepository(db)
        found = await repo.get_by_username("unameuser")
        assert found is not None
        assert found.username == "unameuser"

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, db):
        repo = UserRepository(db)
        found = await repo.get_by_email("nonexistent@test.co")
        assert found is None

    @pytest.mark.asyncio
    async def test_get_by_username_not_found(self, db):
        repo = UserRepository(db)
        found = await repo.get_by_username("nobody")
        assert found is None


class TestProductRepository:
    """Tests for ProductRepository data access."""

    @pytest.mark.asyncio
    async def test_get_by_sku(self, db):
        pid = str(uuid.uuid4())
        product = Product(
            id=pid,
            sku="test-sku-1",
            name="Test Product",
            price=25.0,
            collection="signature",
            category="Tees",
        )
        db.add(product)
        await db.flush()

        repo = ProductRepository(db)
        found = await repo.get_by_sku("test-sku-1")
        assert found is not None
        assert found.name == "Test Product"

    @pytest.mark.asyncio
    async def test_get_by_sku_not_found(self, db):
        repo = ProductRepository(db)
        found = await repo.get_by_sku("nonexistent")
        assert found is None

    @pytest.mark.asyncio
    async def test_get_by_collection(self, db):
        for i in range(3):
            db.add(
                Product(
                    id=str(uuid.uuid4()),
                    sku=f"col-{i}",
                    name=f"Collection Item {i}",
                    price=10.0 + i,
                    collection="black-rose",
                    category="Tees",
                )
            )
        await db.flush()

        repo = ProductRepository(db)
        items = await repo.get_by_collection("black-rose")
        assert len(items) == 3

    @pytest.mark.asyncio
    async def test_get_by_category(self, db):
        db.add(
            Product(
                id=str(uuid.uuid4()),
                sku="cat-1",
                name="Hoodie 1",
                price=50.0,
                collection="signature",
                category="Hoodies",
            )
        )
        await db.flush()

        repo = ProductRepository(db)
        items = await repo.get_by_category("Hoodies")
        assert len(items) >= 1


# =============================================================================
# DatabaseConfig Tests
# =============================================================================


class TestDatabaseConfig:
    def test_default_config(self):
        config = DatabaseConfig()
        assert "sqlite" in config.url or "postgres" in config.url
        assert config.pool_size == 10

    def test_custom_config(self):
        config = DatabaseConfig(url="sqlite+aiosqlite:///:memory:", pool_size=5)
        assert config.pool_size == 5
