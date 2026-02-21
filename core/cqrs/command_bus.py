"""
Command Bus — CQRS Write Side
================================

Commands represent the *intent* to change system state.
Each command has exactly one handler that:
1. Validates the command
2. Performs business logic
3. Returns domain Events (which are then persisted)

This strict separation means the write path is optimized for
consistency and validation, while the read path (QueryBus) is
optimized for speed.

Usage:
    bus = CommandBus()

    # Register handlers
    bus.register_handler("CreateProduct", create_product_handler)
    bus.register_handler("UpdatePrice", update_price_handler)

    # Execute a command
    cmd = Command(
        command_type="CreateProduct",
        data={"sku": "br-001", "name": "Black Rose Crewneck", "price": 79.99},
        user_id="user-123",
    )
    await bus.execute(cmd)
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Optional

# SKU format: 2–5 lowercase letters, hyphen, 3 digits (e.g. br-001, sg-014)
_SKU_RE = re.compile(r"^[a-z]{2,5}-\d{3}$")

from core.events.event_store import EventStore

logger = logging.getLogger(__name__)

HandlerFn = Callable[..., Coroutine[Any, Any, list]]


@dataclass
class Command:
    """
    Represents an intent to change system state.

    Attributes:
        command_type: What action to perform ("CreateProduct", "PlaceOrder", etc.)
        data: Input data for the command
        user_id: Who is issuing the command
        correlation_id: For distributed tracing — auto-generated if not provided
    """

    command_type: str
    data: dict[str, Any]
    user_id: str
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class CommandBus:
    """
    Routes commands to their registered handlers and persists resulting events.

    The command-event cycle:
    1. Command arrives
    2. Handler validates + executes business logic
    3. Handler returns list of Events
    4. CommandBus persists all events to EventStore
    5. EventStore publishes events to handlers (projections, side effects)
    """

    def __init__(self) -> None:
        self._handlers: dict[str, HandlerFn] = {}

    def register_handler(self, command_type: str, handler: HandlerFn) -> None:
        """
        Register a handler for a command type.
        Overwrites any previously registered handler for the same type.
        """
        self._handlers[command_type] = handler

    async def execute(self, command: Command) -> None:
        """
        Execute a command:
        1. Find the registered handler
        2. Call handler — it validates and returns events
        3. Persist all events to EventStore

        Raises:
            ValueError: If no handler is registered for the command type,
                        or if the handler raises ValueError (validation failure).
        """
        handler = self._handlers.get(command.command_type)
        if handler is None:
            raise ValueError(f"No handler for {command.command_type}")

        # Handler may raise ValueError on validation failure — let it propagate
        events = await handler(command)

        # Persist all returned events
        if events:
            store = EventStore()
            for event in events:
                await store.append(event)

        logger.debug(
            f"Command {command.command_type!r} executed "
            f"by user={command.user_id!r}, events={len(events or [])}"
        )


# ---------------------------------------------------------------------------
# Built-in command handlers
# ---------------------------------------------------------------------------


async def create_product_handler(command: Command) -> list:
    """
    Handle CreateProduct command.

    Validates required fields then emits ProductCreated event.
    """
    from core.events.event_store import Event

    data = command.data

    # SKU — required, format-validated
    sku = data.get("sku", "")
    if not sku:
        raise ValueError("sku is required")
    if not _SKU_RE.match(str(sku)):
        raise ValueError("sku must match format: xx-000 (e.g. br-001, sg-014)")

    # Name — required, max length
    name = data.get("name", "")
    if not name:
        raise ValueError("name is required")
    if len(str(name)) > 200:
        raise ValueError("name must be 200 characters or fewer")

    # Price — non-negative, bounded (sanity check against runaway values)
    price = data.get("price", -1)
    try:
        price = float(price)
    except (TypeError, ValueError):
        raise ValueError("price must be a number")
    if price < 0:
        raise ValueError("price must be non-negative")
    if price > 100_000:
        raise ValueError("price must not exceed 100,000")

    # Compare price — if provided, must be non-negative
    compare_price = data.get("compare_price")
    if compare_price is not None:
        try:
            compare_price = float(compare_price)
        except (TypeError, ValueError):
            raise ValueError("compare_price must be a number")
        if compare_price < 0:
            raise ValueError("compare_price must be non-negative")

    # Description — max length to prevent stored-XSS via admin dashboards
    description = data.get("description", "")
    if len(str(description)) > 5_000:
        raise ValueError("description must be 5,000 characters or fewer")

    # Images — bounded list
    images = data.get("images", [])
    if not isinstance(images, list):
        raise ValueError("images must be a list")
    if len(images) > 20:
        raise ValueError("maximum 20 images allowed per product")

    return [
        Event(
            event_type="ProductCreated",
            aggregate_id=data.get("id", str(uuid.uuid4())),
            data=data,
            user_id=command.user_id,
            correlation_id=command.correlation_id,
        )
    ]
