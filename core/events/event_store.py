"""
Event Store — Immutable Append-Only Log
=========================================

Core of the event sourcing pattern. Every state change is recorded as an
immutable Event. Current state is rebuilt by replaying events in order.

Key properties:
- Append-only: events are never updated or deleted
- Ordered: events are stored and retrieved in chronological order
- Replayable: any point-in-time state can be reconstructed
- Auditable: complete history of every change

Usage:
    store = EventStore()

    # Record a product creation
    event = Event(
        event_type="ProductCreated",
        aggregate_id="prod-123",
        data={"sku": "br-001", "name": "Black Rose Crewneck", "price": 79.99},
    )
    await store.append(event)

    # Replay to get current state
    state = await store.replay("prod-123")
    # state == {"sku": "br-001", "name": "Black Rose Crewneck", "price": 79.99}
"""

from __future__ import annotations

import copy
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


class Event:
    """
    Domain event — an immutable fact that something happened.

    Attributes:
        event_id: Unique identifier (UUID4)
        event_type: What happened ("ProductCreated", "OrderPlaced", etc.)
        aggregate_id: ID of the entity this event belongs to
        aggregate_type: Entity type name ("Product", "Order", etc.)
        data: Snapshot of relevant data at the time of the event
        timestamp: When the event occurred (UTC)
        version: Sequence number within the aggregate (for optimistic locking)
        user_id: Who triggered the event (None for system events)
        correlation_id: Links to the originating command/request
    """

    __slots__ = (
        "event_id",
        "event_type",
        "aggregate_id",
        "aggregate_type",
        "data",
        "timestamp",
        "version",
        "user_id",
        "correlation_id",
    )

    def __init__(
        self,
        event_type: str,
        aggregate_id: str,
        data: dict[str, Any],
        aggregate_type: str = "unknown",
        version: int = 1,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        self.event_id = str(uuid.uuid4())
        self.event_type = event_type
        self.aggregate_id = aggregate_id
        self.aggregate_type = aggregate_type
        self.data = copy.deepcopy(data)  # Immutable copy — mutations don't affect the event
        self.timestamp = datetime.now(UTC)
        self.version = version
        self.user_id = user_id
        self.correlation_id = correlation_id or str(uuid.uuid4())

    def __repr__(self) -> str:
        return (
            f"Event(type={self.event_type!r}, "
            f"aggregate={self.aggregate_id!r}, "
            f"ts={self.timestamp.isoformat()})"
        )


# ---------------------------------------------------------------------------
# State applicators — how each event type mutates aggregate state
# ---------------------------------------------------------------------------

_EVENT_APPLICATORS: dict[str, Any] = {
    "ProductCreated": lambda state, data: {**state, **data},
    "ProductPriceChanged": lambda state, data: {**state, "price": data["new_price"]},
    "ProductActivated": lambda state, _: {**state, "is_active": True},
    "ProductDeactivated": lambda state, _: {**state, "is_active": False},
    "ProductDeleted": lambda state, _: {**state, "deleted": True},
    "ProductNameChanged": lambda state, data: {**state, "name": data["name"]},
    # Orders
    "OrderPlaced": lambda state, data: {**state, **data},
    "OrderStatusChanged": lambda state, data: {**state, "status": data["status"]},
    "OrderCancelled": lambda state, _: {**state, "status": "cancelled"},
}


def apply_event(state: dict[str, Any], event: Event) -> dict[str, Any]:
    """
    Apply a single event to the current state, returning new state.

    Uses functional (immutable) style — the input state is not mutated.
    Unknown event types are ignored (forwards compatibility).
    """
    applicator = _EVENT_APPLICATORS.get(event.event_type)
    if applicator is None:
        logger.debug(f"No applicator for event type {event.event_type!r} — skipping")
        return state
    return applicator(state, event.data)


class EventStore:
    """
    Append-only event store backed by the database.

    For production use, calls DatabaseManager to persist events.
    For tests, the _persist and _load_records methods are mocked.
    """

    def __init__(self) -> None:
        from core.events.event_bus import event_bus as _bus

        self._event_bus = _bus

    async def append(self, event: Event) -> Event:
        """
        Persist event and broadcast to handlers.

        Steps:
        1. Write event to database (source of truth)
        2. Publish to in-process event bus (handler projections)

        The event is returned unchanged for chaining.
        """
        await self._persist(event)
        await self._publish(event)
        return event

    async def _persist(self, event: Event) -> None:
        """Write event to database. Override in tests to avoid DB calls."""
        from database.db import DatabaseManager, EventRecord

        db = DatabaseManager()
        async with db.session() as session:
            record = EventRecord(
                event_id=event.event_id,
                event_type=event.event_type,
                aggregate_id=event.aggregate_id,
                aggregate_type=event.aggregate_type,
                data_json=json.dumps(event.data, default=str),
                timestamp=event.timestamp,
                version=event.version,
                user_id=event.user_id,
                correlation_id=event.correlation_id,
            )
            session.add(record)
            # Session commit is handled by the context manager in DatabaseManager

    async def _publish(self, event: Event) -> None:
        """Publish event to in-process handlers."""
        await self._event_bus.publish(event)

    async def _load_records(
        self, aggregate_id: str, event_type: Optional[str] = None
    ) -> list[Any]:
        """Load EventRecords from database. Override in tests."""
        from sqlalchemy import select

        from database.db import DatabaseManager, EventRecord

        db = DatabaseManager()
        async with db.session() as session:
            query = (
                select(EventRecord)
                .where(EventRecord.aggregate_id == aggregate_id)
                .order_by(EventRecord.timestamp.asc())
            )
            if event_type:
                query = query.where(EventRecord.event_type == event_type)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_events(
        self, aggregate_id: str, event_type: Optional[str] = None
    ) -> list[Event]:
        """
        Retrieve all events for an aggregate in chronological order.

        Args:
            aggregate_id: The entity's identifier
            event_type: Optional filter to only return events of this type

        Returns:
            List of Events, oldest first
        """
        records = await self._load_records(aggregate_id, event_type)

        events: list[Event] = []
        for record in records:
            try:
                data = json.loads(record.data_json)
            except (json.JSONDecodeError, AttributeError):
                data = {}

            event = Event(
                event_type=record.event_type,
                aggregate_id=record.aggregate_id,
                data=data,
            )
            # Restore persisted fields
            object.__setattr__(event, "event_id", record.event_id)
            object.__setattr__(event, "timestamp", record.timestamp)
            object.__setattr__(event, "version", record.version)
            events.append(event)

        return events

    async def replay(self, aggregate_id: str) -> dict[str, Any]:
        """
        Rebuild current state by replaying all events for an aggregate.

        This is how event sourcing recovers current state:
        Start from empty state {} and apply each event in order.

        Args:
            aggregate_id: The entity to replay

        Returns:
            Current state dict, or {} if no events exist
        """
        events = await self.get_events(aggregate_id)
        state: dict[str, Any] = {}
        for event in events:
            state = apply_event(state, event)
        return state
