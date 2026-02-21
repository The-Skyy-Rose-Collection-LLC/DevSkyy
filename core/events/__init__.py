"""
Event Sourcing Infrastructure
==============================

Immutable append-only event store + in-process event bus.
"""

from core.events.event_store import Event, EventStore
from core.events.event_bus import EventBus, event_bus

__all__ = ["Event", "EventStore", "EventBus", "event_bus"]
