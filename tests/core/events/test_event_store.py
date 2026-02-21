"""
Tests for EventStore — Immutable Append-Only Event Log
=======================================================

TDD RED Phase — tests describe expected behavior before implementation.

Key concepts tested:
- Append-only: events are never updated or deleted
- Ordered: get_events() returns events in chronological order
- Replayable: replay() rebuilds current state from event history
- Versioned: optimistic locking via version field
"""

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.events.event_store import Event, EventStore


@pytest.mark.unit
@pytest.mark.asyncio
class TestEvent:
    """Test the Event dataclass"""

    def test_event_auto_generates_id(self):
        """Every event gets a unique UUID"""
        e1 = Event(event_type="ProductCreated", aggregate_id="p-1", data={"name": "Hoodie"})
        e2 = Event(event_type="ProductCreated", aggregate_id="p-2", data={"name": "Tee"})
        assert e1.event_id != e2.event_id
        assert len(e1.event_id) == 36  # UUID format

    def test_event_has_timestamp(self):
        """Event timestamp is set at creation"""
        before = datetime.now(UTC)
        event = Event(event_type="Test", aggregate_id="agg-1", data={})
        after = datetime.now(UTC)
        assert before <= event.timestamp <= after

    def test_event_data_immutable_copy(self):
        """Mutating original data dict doesn't affect event"""
        data = {"price": 79.99}
        event = Event(event_type="ProductCreated", aggregate_id="p-1", data=data)
        data["price"] = 999.0  # Mutate original
        assert event.data["price"] == 79.99  # Event data unchanged


@pytest.mark.unit
@pytest.mark.asyncio
class TestEventStore:
    """Test EventStore append, query, and replay operations"""

    @pytest.fixture
    def store(self):
        return EventStore()

    async def test_append_stores_event(self, store):
        """
        append() persists the event and returns it with assigned fields

        Expected: event is saved to DB with all fields intact
        """
        event = Event(
            event_type="ProductCreated",
            aggregate_id="prod-abc",
            data={"sku": "br-001", "name": "Black Rose Crewneck", "price": 79.99},
        )

        with patch.object(store, "_persist", new_callable=AsyncMock) as mock_persist:
            mock_persist.return_value = None

            result = await store.append(event)

            mock_persist.assert_called_once_with(event)
            assert result.event_type == "ProductCreated"
            assert result.aggregate_id == "prod-abc"
            assert result.data["sku"] == "br-001"

    async def test_append_publishes_to_event_bus(self, store):
        """
        After persisting, the event is published to the in-process bus
        so handlers can update read models
        """
        event = Event(event_type="ProductCreated", aggregate_id="p-1", data={})

        with patch.object(store, "_persist", new_callable=AsyncMock), \
             patch.object(store, "_publish", new_callable=AsyncMock) as mock_publish:
            await store.append(event)
            mock_publish.assert_called_once_with(event)

    async def test_get_events_returns_chronological_order(self, store):
        """
        get_events(aggregate_id) returns all events for that entity,
        sorted oldest-first (for correct replay order)
        """
        agg_id = "prod-xyz"
        ts1 = datetime(2026, 2, 1, 12, 0, 0, tzinfo=UTC)
        ts2 = datetime(2026, 2, 1, 12, 1, 0, tzinfo=UTC)
        ts3 = datetime(2026, 2, 1, 12, 2, 0, tzinfo=UTC)

        mock_records = [
            MagicMock(
                event_id=str(uuid.uuid4()),
                event_type="ProductCreated",
                aggregate_id=agg_id,
                data_json='{"price": 79.99}',
                timestamp=ts1,
                version=1,
            ),
            MagicMock(
                event_id=str(uuid.uuid4()),
                event_type="ProductPriceChanged",
                aggregate_id=agg_id,
                data_json='{"new_price": 89.99}',
                timestamp=ts2,
                version=2,
            ),
            MagicMock(
                event_id=str(uuid.uuid4()),
                event_type="ProductActivated",
                aggregate_id=agg_id,
                data_json='{}',
                timestamp=ts3,
                version=3,
            ),
        ]

        with patch.object(store, "_load_records", new_callable=AsyncMock) as mock_load:
            mock_load.return_value = mock_records

            events = await store.get_events(agg_id)

            assert len(events) == 3
            assert events[0].event_type == "ProductCreated"
            assert events[1].event_type == "ProductPriceChanged"
            assert events[2].event_type == "ProductActivated"
            # Verify chronological order
            assert events[0].timestamp < events[1].timestamp < events[2].timestamp

    async def test_get_events_empty_for_unknown_aggregate(self, store):
        """Unknown aggregate_id returns empty list, no error"""
        with patch.object(store, "_load_records", new_callable=AsyncMock) as mock_load:
            mock_load.return_value = []
            events = await store.get_events("nonexistent-id")
            assert events == []

    async def test_replay_rebuilds_product_state(self, store):
        """
        replay() applies events in order to build current state.

        ProductCreated → state = {name, price, is_active: False}
        ProductPriceChanged → state.price updated
        ProductActivated → state.is_active = True
        """
        agg_id = "prod-123"

        mock_events = [
            MagicMock(
                event_type="ProductCreated",
                aggregate_id=agg_id,
                data={"name": "Black Rose Crewneck", "price": 79.99, "sku": "br-001"},
                timestamp=datetime(2026, 2, 1, tzinfo=UTC),
            ),
            MagicMock(
                event_type="ProductPriceChanged",
                aggregate_id=agg_id,
                data={"new_price": 89.99},
                timestamp=datetime(2026, 2, 2, tzinfo=UTC),
            ),
        ]

        with patch.object(store, "get_events", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_events

            state = await store.replay(agg_id)

            assert state["name"] == "Black Rose Crewneck"
            assert state["price"] == 89.99  # Updated by second event
            assert state["sku"] == "br-001"

    async def test_replay_empty_aggregate_returns_empty_state(self, store):
        """Replaying an aggregate with no events returns empty dict"""
        with patch.object(store, "get_events", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = []
            state = await store.replay("empty-agg")
            assert state == {}

    async def test_get_events_filtered_by_type(self, store):
        """
        get_events(aggregate_id, event_type="ProductPriceChanged") filters
        to only return events of that type
        """
        agg_id = "prod-456"
        mock_records = [
            MagicMock(
                event_id=str(uuid.uuid4()),
                event_type="ProductPriceChanged",
                aggregate_id=agg_id,
                data_json='{"new_price": 89.99}',
                timestamp=datetime(2026, 2, 1, tzinfo=UTC),
                version=1,
            ),
        ]

        with patch.object(store, "_load_records", new_callable=AsyncMock) as mock_load:
            mock_load.return_value = mock_records

            events = await store.get_events(agg_id, event_type="ProductPriceChanged")
            assert all(e.event_type == "ProductPriceChanged" for e in events)
