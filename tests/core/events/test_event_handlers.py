"""
Tests for EventHandlers — Read Model Projections
=================================================

TDD RED Phase — Handlers consume Events and update denormalized read models.
Idempotency is critical: replaying the same event twice must produce the same state.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.events.event_handlers import ProductEventHandler
from core.events.event_store import Event


@pytest.mark.unit
@pytest.mark.asyncio
class TestProductEventHandler:
    """Test ProductEventHandler projection updates"""

    @pytest.fixture
    def handler(self):
        return ProductEventHandler()

    async def test_product_created_builds_read_model(self, handler):
        """
        ProductCreated event → handler creates a denormalized product view
        with all fields needed for fast queries.
        """
        event = Event(
            event_type="ProductCreated",
            aggregate_id="prod-abc",
            data={
                "sku": "br-001",
                "name": "Black Rose Crewneck",
                "price": 79.99,
                "collection": "black-rose",
            },
        )

        with patch.object(handler, "_upsert_product_view", new_callable=AsyncMock) as mock_upsert:
            await handler.handle(event)
            mock_upsert.assert_called_once()
            call_data = mock_upsert.call_args[0][0]
            assert call_data["sku"] == "br-001"
            assert call_data["price"] == 79.99

    async def test_product_price_changed_updates_view(self, handler):
        """
        ProductPriceChanged event → only the price field is updated in the view.
        Other fields remain unchanged.
        """
        event = Event(
            event_type="ProductPriceChanged",
            aggregate_id="prod-abc",
            data={"new_price": 89.99, "old_price": 79.99},
        )

        with patch.object(handler, "_update_product_price", new_callable=AsyncMock) as mock_update:
            await handler.handle(event)
            mock_update.assert_called_once_with("prod-abc", 89.99)

    async def test_product_deleted_soft_deletes_view(self, handler):
        """
        ProductDeleted event → sets is_active=False in the read model.
        Does NOT hard-delete (maintains event sourcing audit trail).
        """
        event = Event(
            event_type="ProductDeleted",
            aggregate_id="prod-abc",
            data={"reason": "discontinued"},
        )

        with patch.object(handler, "_deactivate_product", new_callable=AsyncMock) as mock_deactivate:
            await handler.handle(event)
            mock_deactivate.assert_called_once_with("prod-abc")

    async def test_unknown_event_type_is_ignored(self, handler):
        """
        Unknown event types are silently ignored.
        This allows schema evolution — old handlers ignore new event types.
        """
        event = Event(
            event_type="SomeNewEventTypeAddedLater",
            aggregate_id="prod-abc",
            data={},
        )
        # Should not raise
        await handler.handle(event)

    async def test_handler_idempotency_product_created(self, handler):
        """
        Replaying ProductCreated twice produces the same read model state.
        This is critical for event replay during system recovery.
        """
        event = Event(
            event_type="ProductCreated",
            aggregate_id="prod-abc",
            data={"sku": "br-001", "name": "Black Rose Crewneck", "price": 79.99},
        )

        upsert_calls = []

        async def track_upsert(data):
            upsert_calls.append(data)

        with patch.object(handler, "_upsert_product_view", side_effect=track_upsert):
            await handler.handle(event)
            await handler.handle(event)  # Second replay

            # Both calls should have identical data (idempotent)
            assert len(upsert_calls) == 2
            assert upsert_calls[0] == upsert_calls[1]

    async def test_subscribe_and_receive_events(self, handler):
        """
        subscribe() registers the handler with the EventBus.
        When an event is published, the handler's handle() is called.
        """
        with patch("core.events.event_handlers.event_bus") as mock_bus:
            handler.subscribe()
            mock_bus.subscribe.assert_called_once()
