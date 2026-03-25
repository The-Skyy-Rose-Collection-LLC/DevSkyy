"""
CQRS — Command Query Responsibility Segregation
================================================

Commands (writes) and Queries (reads) travel through separate buses,
enabling independent optimization of each path.
"""

from core.cqrs.command_bus import Command, CommandBus
from core.cqrs.query_bus import Query, QueryBus

__all__ = ["Command", "CommandBus", "Query", "QueryBus"]
