"""
Query Bus — CQRS Read Side
=============================

Queries fetch data from read-optimized projections (not the write DB).
This separation enables:
- Read replicas / caching without affecting write consistency
- Different data models for reads vs writes
- Independent scaling

Usage:
    bus = QueryBus()
    bus.register_handler("GetProduct", get_product_handler)
    bus.register_handler("ListProducts", list_products_handler)

    product = await bus.execute(Query("GetProduct", {"sku": "br-001"}))
    products = await bus.execute(Query("ListProducts", {"collection": "black-rose"}))
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Optional

logger = logging.getLogger(__name__)

HandlerFn = Callable[..., Coroutine[Any, Any, Any]]


@dataclass
class Query:
    """
    Represents a read request — no side effects allowed.

    Attributes:
        query_type: What to fetch ("GetProduct", "ListProducts", etc.)
        filters: Query parameters (sku, collection, limit, offset, etc.)
    """

    query_type: str
    filters: dict[str, Any] = field(default_factory=dict)


class QueryBus:
    """
    Routes queries to their registered handlers.

    Handlers should read from projections / caches, not the write DB.
    This enables the read side to scale independently of writes.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, HandlerFn] = {}

    def register_handler(self, query_type: str, handler: HandlerFn) -> None:
        """Register a handler for a query type. Overwrites existing."""
        self._handlers[query_type] = handler

    async def execute(self, query: Query) -> Any:
        """
        Execute a query and return its result.

        Returns:
            Whatever the handler returns (a single record, list, or None).

        Raises:
            ValueError: If no handler is registered for the query type.
        """
        handler = self._handlers.get(query.query_type)
        if handler is None:
            raise ValueError(f"No handler for {query.query_type}")

        result = await handler(query)
        logger.debug(f"Query {query.query_type!r} executed, result type={type(result).__name__}")
        return result
