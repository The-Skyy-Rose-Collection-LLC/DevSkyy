"""
Architecture module for Grade A+ implementation
Contains CQRS and Event Sourcing patterns
"""

from .cqrs import command_bus, query_bus, Command, Query, CommandHandler, QueryHandler
from .event_sourcing import event_store, DomainEvent, EventStore, AggregateRoot

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
