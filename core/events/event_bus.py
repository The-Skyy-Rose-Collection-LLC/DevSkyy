"""
In-Process Event Bus
=====================

Lightweight pub/sub for broadcasting domain events to handlers
within the same process. For cross-process messaging, integrate
with Kafka/Redis Streams.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Callable, Coroutine, Any

logger = logging.getLogger(__name__)

HandlerFn = Callable[..., Coroutine[Any, Any, None]]


class EventBus:
    """
    In-process event bus using asyncio.

    Handlers are called sequentially after each event is persisted.
    Errors in handlers are logged but do not roll back the event.

    Failed events are collected in _dead_letters so operators can
    identify which events need to be replayed after a handler fix.
    """

    def __init__(self) -> None:
        self._handlers: list[HandlerFn] = []
        # Dead-letter queue: (event, exception) pairs for failed handler calls.
        # Bounded at 1,000 entries to prevent memory growth during outages.
        self._dead_letters: list[tuple[Any, Exception]] = []
        self._max_dead_letters = 1_000

    def subscribe(self, handler: HandlerFn) -> None:
        """Register a handler to receive all published events."""
        self._handlers.append(handler)

    async def publish(self, event: Any) -> None:
        """
        Deliver event to all registered handlers.

        Handler errors are logged and swallowed — event sourcing assumes
        the event is already persisted (the source of truth).
        Failed events are appended to dead_letters for later replay.
        """
        for handler in self._handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(
                    f"Event handler error for {event.event_type}: {e}",
                    exc_info=True,
                )
                if len(self._dead_letters) < self._max_dead_letters:
                    self._dead_letters.append((event, e))

    def get_dead_letters(self) -> list[tuple[Any, Exception]]:
        """
        Return failed (event, exception) pairs for investigation and replay.

        Call this from an admin endpoint or health check to detect
        read-model divergence from the event store.
        """
        return list(self._dead_letters)

    def clear_dead_letters(self) -> int:
        """Clear dead letters after successful replay. Returns count cleared."""
        count = len(self._dead_letters)
        self._dead_letters.clear()
        return count


# Singleton bus shared across the process
event_bus = EventBus()
