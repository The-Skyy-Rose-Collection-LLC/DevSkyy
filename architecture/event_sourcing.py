from datetime import datetime, timezone

from pydantic import BaseModel

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import uuid

"""
Event Sourcing Pattern for Grade A+ Architecture
Stores state changes as a sequence of events for audit and replay
"""

# ============================================================================
# EVENT BASE CLASSES
# ============================================================================


class DomainEvent(BaseModel):
    """Base class for all domain events"""

    event_id: str
    event_type: str
    aggregate_id: str
    aggregate_type: str
    timestamp: datetime
    data: Dict[str, Any]
    version: int
    metadata: Optional[Dict[str, Any]] = None

    def __init__(self, **data):
        if "event_id" not in data:
            data["event_id"] = str(uuid.uuid4())
        if "timestamp" not in data:
            data["timestamp"] = datetime.now(timezone.utc)
        if "event_type" not in data:
            data["event_type"] = self.__class__.__name__
        super().__init__(**data)


# ============================================================================
# EVENT STORE
# ============================================================================


class EventStore:
    """
    In-memory event store for storing and retrieving domain events
    In production, this would be backed by a database
    """

    def __init__(self):
        self._events: Dict[str, List[DomainEvent]] = {}
        self._snapshots: Dict[str, Dict[str, Any]] = {}

    async def save_event(self, event: DomainEvent) -> bool:
        """
        Save event to store

        Args:
            event: Domain event to save

        Returns:
            True if saved successfully
        """
        aggregate_id = event.aggregate_id

        if aggregate_id not in self._events:
            self._events[aggregate_id] = []

        self._events[aggregate_id].append(event)
        return True

    async def save_events(self, events: List[DomainEvent]) -> bool:
        """
        Save multiple events atomically

        Args:
            events: List of domain events to save

        Returns:
            True if all saved successfully
        """
        for event in events:
            await self.save_event(event)
        return True

    async def get_events(
        self, aggregate_id: str, from_version: int = 0, to_version: Optional[int] = None
    ) -> List[DomainEvent]:
        """
        Get events for an aggregate

        Args:
            aggregate_id: ID of the aggregate
            from_version: Start version (inclusive)
            to_version: End version (inclusive), None for all

        Returns:
            List of domain events
        """
        if aggregate_id not in self._events:
            return []

        events = self._events[aggregate_id]

        # Filter by version
        filtered = [e for e in events if e.version >= from_version]
        if to_version is not None:
            filtered = [e for e in filtered if e.version <= to_version]

        return filtered

    async def get_all_events(self) -> List[DomainEvent]:
        """
        Get all events across all aggregates

        Returns:
            List of all domain events
        """
        all_events = []
        for events in self._events.values():
            all_events.extend(events)
        return sorted(all_events, key=lambda e: e.timestamp)

    async def save_snapshot(self, aggregate_id: str, state: Dict[str, Any], version: int):
        """
        Save snapshot of aggregate state for faster reconstruction

        Args:
            aggregate_id: ID of the aggregate
            state: Current state of the aggregate
            version: Version number of the snapshot
        """
        self._snapshots[aggregate_id] = {
            "state": state,
            "version": version,
            "timestamp": datetime.now(timezone.utc),
        }

    async def get_snapshot(self, aggregate_id: str) -> Optional[Dict[str, Any]]:
        """
        Get latest snapshot for an aggregate

        Args:
            aggregate_id: ID of the aggregate

        Returns:
            Snapshot data or None if no snapshot exists
        """
        return self._snapshots.get(aggregate_id)


# ============================================================================
# AGGREGATE ROOT
# ============================================================================


class AggregateRoot(ABC):
    """
    Base class for aggregate roots in event sourcing
    Aggregates are the main entry point for commands and event application
    """

    def __init__(self, aggregate_id: str):
        self.aggregate_id = aggregate_id
        self.version = 0
        self.uncommitted_events: List[DomainEvent] = []

    @abstractmethod
    def apply_event(self, event: DomainEvent):
        """
        Apply event to update aggregate state

        Args:
            event: Domain event to apply
        """

    def raise_event(self, event: DomainEvent):
        """
        Raise a new domain event

        Args:
            event: Domain event to raise
        """
        event.version = self.version + 1
        self.apply_event(event)
        self.uncommitted_events.append(event)
        self.version = event.version

    async def load_from_history(self, events: List[DomainEvent]):
        """
        Reconstruct aggregate state from event history

        Args:
            events: List of historical events
        """
        for event in events:
            self.apply_event(event)
            self.version = event.version

    def get_uncommitted_events(self) -> List[DomainEvent]:
        """
        Get events that haven't been persisted

        Returns:
            List of uncommitted events
        """
        return self.uncommitted_events.copy()

    def mark_events_as_committed(self):
        """Mark all uncommitted events as committed"""
        self.uncommitted_events.clear()


# ============================================================================
# EXAMPLE DOMAIN EVENTS
# ============================================================================


class AgentCreatedEvent(DomainEvent):
    """Event raised when an agent is created"""


class AgentUpdatedEvent(DomainEvent):
    """Event raised when an agent is updated"""


class AgentDeletedEvent(DomainEvent):
    """Event raised when an agent is deleted"""


# ============================================================================
# EXAMPLE AGGREGATE
# ============================================================================


class AgentAggregate(AggregateRoot):
    """
    Example aggregate for Agent domain entity
    """

    def __init__(self, aggregate_id: str):
        super().__init__(aggregate_id)
        self.name: Optional[str] = None
        self.agent_type: Optional[str] = None
        self.status: str = "inactive"
        self.capabilities: Dict[str, Any] = {}

    def apply_event(self, event: DomainEvent):
        """Apply event to update agent state"""
        if isinstance(event, AgentCreatedEvent):
            self.name = event.data.get("name")
            self.agent_type = event.data.get("type")
            self.status = "active"
            self.capabilities = event.data.get("capabilities", {})

        elif isinstance(event, AgentUpdatedEvent):
            if "name" in event.data:
                self.name = event.data["name"]
            if "capabilities" in event.data:
                self.capabilities.update(event.data["capabilities"])

        elif isinstance(event, AgentDeletedEvent):
            self.status = "deleted"

    def create(self, name: str, agent_type: str, capabilities: Dict[str, Any]):
        """Create new agent"""
        event = AgentCreatedEvent(
            aggregate_id=self.aggregate_id,
            aggregate_type="Agent",
            version=self.version + 1,
            data={"name": name, "type": agent_type, "capabilities": capabilities},
        )
        self.raise_event(event)

    def update(self, **updates):
        """Update agent properties"""
        event = AgentUpdatedEvent(
            aggregate_id=self.aggregate_id,
            aggregate_type="Agent",
            version=self.version + 1,
            data=updates,
        )
        self.raise_event(event)

    def delete(self):
        """Mark agent as deleted"""
        event = AgentDeletedEvent(
            aggregate_id=self.aggregate_id,
            aggregate_type="Agent",
            version=self.version + 1,
            data={"deleted_at": datetime.now(timezone.utc).isoformat()},
        )
        self.raise_event(event)


# ============================================================================
# GLOBAL EVENT STORE INSTANCE
# ============================================================================

event_store = EventStore()
