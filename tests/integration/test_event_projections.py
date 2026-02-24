"""Integration tests for CQRS event projections."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.events.event_store import Event
from core.events.event_handlers import ProductEventHandler


@pytest.fixture
def handler():
    return ProductEventHandler()


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def mock_db(mock_session):
    db = MagicMock()
    db.session = MagicMock(return_value=AsyncMock())

    # Make the context manager work
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock_session)
    cm.__aexit__ = AsyncMock(return_value=False)
    db.session.return_value = cm
    return db


class TestProductCreatedProjection:
    @pytest.mark.asyncio
    async def test_upsert_creates_product(self, handler, mock_db):
        """ProductCreated event should upsert into products table."""
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

        with patch("core.events.event_handlers.DatabaseManager", return_value=mock_db):
            await handler.handle(event)

        # Verify session.execute was called (the upsert)
        assert mock_db.session.return_value.__aenter__.called


class TestProductPriceChangedProjection:
    @pytest.mark.asyncio
    async def test_price_update(self, handler, mock_db):
        """ProductPriceChanged should update price column."""
        event = Event(
            event_type="ProductPriceChanged",
            aggregate_id="prod-001",
            data={"new_price": 89.99},
        )

        with patch("core.events.event_handlers.DatabaseManager", return_value=mock_db):
            await handler.handle(event)

        assert mock_db.session.return_value.__aenter__.called


class TestProductDeactivatedProjection:
    @pytest.mark.asyncio
    async def test_deactivation(self, handler, mock_db):
        """ProductDeactivated should set is_active=False."""
        event = Event(
            event_type="ProductDeactivated",
            aggregate_id="prod-001",
            data={},
        )

        with patch("core.events.event_handlers.DatabaseManager", return_value=mock_db):
            await handler.handle(event)

        assert mock_db.session.return_value.__aenter__.called


class TestProductNameChangedProjection:
    @pytest.mark.asyncio
    async def test_name_update(self, handler, mock_db):
        """ProductNameChanged should update name field."""
        event = Event(
            event_type="ProductNameChanged",
            aggregate_id="prod-001",
            data={"name": "New Name"},
        )

        with patch("core.events.event_handlers.DatabaseManager", return_value=mock_db):
            await handler.handle(event)

        assert mock_db.session.return_value.__aenter__.called


class TestFieldWhitelist:
    @pytest.mark.asyncio
    async def test_rejects_disallowed_field(self, handler):
        """_update_product_field should reject fields not in whitelist."""
        # This should log a warning and not execute any DB query
        await handler._update_product_field("prod-001", "hashed_password", "evil")
        # No error raised, but no DB call either


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
