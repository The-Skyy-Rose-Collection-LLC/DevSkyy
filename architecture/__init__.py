from .cqrs import Command, command_bus, CommandHandler, Query, query_bus, QueryHandler
from .event_sourcing import AggregateRoot, DomainEvent, event_store, EventStore

"""
Architecture module for Grade A+ implementation
Contains CQRS and Event Sourcing patterns
"""


__all__ = [
    "AggregateRoot",
    "Command",
    "CommandHandler",
    "DomainEvent",
    "EventStore",
    "Query",
    "QueryHandler",
    "command_bus",
    "event_store",
    "query_bus",
]
