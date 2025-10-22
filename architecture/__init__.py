"""
Architecture module for Grade A+ implementation
Contains CQRS and Event Sourcing patterns
"""

from .cqrs import Command, command_bus, CommandHandler, Query, query_bus, QueryHandler
from .event_sourcing import AggregateRoot, DomainEvent, event_store, EventStore

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
