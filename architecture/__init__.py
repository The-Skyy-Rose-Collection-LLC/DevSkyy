"""
Architecture module for Grade A+ implementation
Contains CQRS and Event Sourcing patterns
"""

from .cqrs import Command, CommandHandler, Query, QueryHandler, command_bus, query_bus
from .event_sourcing import AggregateRoot, DomainEvent, EventStore, event_store

__all__ = [
    "command_bus",
    "query_bus",
    "Command",
    "Query",
    "CommandHandler",
    "QueryHandler",
    "event_store",
    "DomainEvent",
    "EventStore",
    "AggregateRoot",
]
