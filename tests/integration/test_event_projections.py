"""Integration tests for CQRS event projections."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.events.event_handlers import ProductEventHandler
from core.events.event_store import Event


@pytest.fixture
def handler():
    return ProductEventHandler()


@pytest.fixture
def mock_product():
    """A mock Product ORM instance."""
    product = MagicMock()
    product.sku = "br-001"
    product.name = "Black Rose Crewneck"
    product.price = 79.99
    product.collection = "black-rose"
    product.is_active = True
    product.images_json = "[]"
    return product


@pytest.fixture
def mock_session(mock_product):
    """Async session that returns mock_product on .get()."""
    session = AsyncMock()
    session.get = AsyncMock(return_value=mock_product)
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_db(mock_session):
    """Mock DatabaseManager singleton with working async context manager."""
    db = MagicMock()

    # Make db.session() return an async context manager yielding mock_session
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock_session)
    cm.__aexit__ = AsyncMock(return_value=False)
    db.session.return_value = cm
    return db


# Patch at the SOURCE module (database.db.DatabaseManager) since event_handlers
# imports it lazily inside method bodies with `from database.db import DatabaseManager`.
PATCH_DB = "database.db.DatabaseManager"
PATCH_CACHE = "core.events.event_handlers.ProductEventHandler._invalidate_cache"


class TestProductCreatedProjection:
    @pytest.mark.asyncio
    async def test_upsert_creates_product(self, handler, mock_db, mock_session):
        """ProductCreated event should upsert into products table."""
        # Return None on .get() so it creates a new product
        mock_session.get = AsyncMock(return_value=None)

        event = Event(
            event_type="ProductCreated",
            aggregate_id="prod-001",
            data={
                "sku": "br-001",
                "name": "Black Rose Crewneck",
                "price": 79.99,
                "collection": "black-rose",
                "is_active": True,
                "images": ["img1.jpg", "img2.jpg"],
            },
        )

        with patch(PATCH_DB, return_value=mock_db), patch(PATCH_CACHE, new_callable=AsyncMock):
            await handler.handle(event)

        # Verify a new product was added to the session
        mock_session.add.assert_called_once()


class TestProductPriceChangedProjection:
    @pytest.mark.asyncio
    async def test_price_update(self, handler, mock_db, mock_product):
        """ProductPriceChanged should update price column."""
        event = Event(
            event_type="ProductPriceChanged",
            aggregate_id="prod-001",
            data={"new_price": 89.99},
        )

        with patch(PATCH_DB, return_value=mock_db), patch(PATCH_CACHE, new_callable=AsyncMock):
            await handler.handle(event)

        assert mock_product.price == 89.99


class TestProductDeactivatedProjection:
    @pytest.mark.asyncio
    async def test_deactivation(self, handler, mock_db, mock_product):
        """ProductDeactivated should set is_active=False."""
        mock_product.is_active = True

        event = Event(
            event_type="ProductDeactivated",
            aggregate_id="prod-001",
            data={},
        )

        with patch(PATCH_DB, return_value=mock_db), patch(PATCH_CACHE, new_callable=AsyncMock):
            await handler.handle(event)

        assert mock_product.is_active is False


class TestProductActivatedProjection:
    @pytest.mark.asyncio
    async def test_activation(self, handler, mock_db, mock_product):
        """ProductActivated should set is_active=True."""
        mock_product.is_active = False

        event = Event(
            event_type="ProductActivated",
            aggregate_id="prod-001",
            data={},
        )

        with patch(PATCH_DB, return_value=mock_db), patch(PATCH_CACHE, new_callable=AsyncMock):
            await handler.handle(event)

        assert mock_product.is_active is True


class TestProductNameChangedProjection:
    @pytest.mark.asyncio
    async def test_name_update(self, handler, mock_db, mock_product):
        """ProductNameChanged should update name field."""
        event = Event(
            event_type="ProductNameChanged",
            aggregate_id="prod-001",
            data={"name": "New Name"},
        )

        with patch(PATCH_DB, return_value=mock_db), patch(PATCH_CACHE, new_callable=AsyncMock):
            await handler.handle(event)

        assert mock_product.name == "New Name"


class TestFieldWhitelist:
    @pytest.mark.asyncio
    async def test_rejects_disallowed_field(self, handler):
        """_update_product_field should reject fields not in whitelist."""
        # Should log a warning and NOT execute any DB query
        await handler._update_product_field("prod-001", "hashed_password", "evil")
        # No error raised, but no DB call either

    @pytest.mark.asyncio
    async def test_accepts_allowed_field(self, handler, mock_db, mock_product):
        """_update_product_field should accept whitelisted fields."""
        with patch(PATCH_DB, return_value=mock_db), patch(PATCH_CACHE, new_callable=AsyncMock):
            await handler._update_product_field("prod-001", "description", "New desc")

        assert mock_product.description == "New desc"


class TestUnknownEventType:
    @pytest.mark.asyncio
    async def test_unknown_event_ignored(self, handler):
        """Unknown event types should be silently ignored."""
        event = Event(
            event_type="SomeNewEventType",
            aggregate_id="prod-001",
            data={},
        )
        await handler.handle(event)
        # No error raised
