"""
Event Handlers — Read Model Projections
=========================================

Handlers consume Events and update denormalized read models (projections).
Read models are optimized for query patterns, not normalized for writes.

Key principle: handlers must be IDEMPOTENT — replaying the same event
twice must produce the same state (critical for system recovery).

Architecture note:
  Events (write side) → EventHandlers (bridge) → Read Models (query side)
  This is the "projection" step in CQRS.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from core.events.event_bus import event_bus

if TYPE_CHECKING:
    from core.events.event_store import Event

logger = logging.getLogger(__name__)


class ProductEventHandler:
    """
    Handles product domain events and keeps read models in sync.

    Subscribes to all events and dispatches to specific handlers
    based on event_type. Unknown types are silently ignored to
    support schema evolution.
    """

    async def handle(self, event: "Event") -> None:
        """
        Dispatch event to the appropriate handler method.

        This is the single entry point for all product events.
        Unknown event types are ignored (forward compatibility).
        """
        dispatch = {
            "ProductCreated": self._on_product_created,
            "ProductPriceChanged": self._on_product_price_changed,
            "ProductDeleted": self._on_product_deleted,
            "ProductActivated": self._on_product_activated,
            "ProductDeactivated": self._on_product_deactivated,
            "ProductNameChanged": self._on_product_name_changed,
        }
        handler = dispatch.get(event.event_type)
        if handler is None:
            logger.debug(f"No handler for event type {event.event_type!r} — ignoring")
            return
        await handler(event)

    async def _on_product_created(self, event: "Event") -> None:
        """Create denormalized product read view from ProductCreated event."""
        await self._upsert_product_view(
            {
                "aggregate_id": event.aggregate_id,
                "sku": event.data.get("sku", ""),
                "name": event.data.get("name", ""),
                "price": event.data.get("price", 0.0),
                "collection": event.data.get("collection"),
                "is_active": event.data.get("is_active", True),
                "images": event.data.get("images", []),
            }
        )

    async def _on_product_price_changed(self, event: "Event") -> None:
        """Update price field in read model."""
        new_price = event.data.get("new_price", 0.0)
        await self._update_product_price(event.aggregate_id, new_price)

    async def _on_product_deleted(self, event: "Event") -> None:
        """Soft-delete product from read model."""
        await self._deactivate_product(event.aggregate_id)

    async def _on_product_activated(self, event: "Event") -> None:
        """Mark product as active in read model."""
        await self._set_product_active(event.aggregate_id, is_active=True)

    async def _on_product_deactivated(self, event: "Event") -> None:
        """Mark product as inactive in read model."""
        await self._set_product_active(event.aggregate_id, is_active=False)

    async def _on_product_name_changed(self, event: "Event") -> None:
        """Update product name in read model."""
        await self._update_product_field(
            event.aggregate_id, "name", event.data.get("name", "")
        )

    def subscribe(self) -> None:
        """Register this handler with the global event bus."""
        event_bus.subscribe(self.handle)

    # ---------------------------------------------------------------------------
    # Read model persistence helpers — override in tests
    # ---------------------------------------------------------------------------

    async def _upsert_product_view(self, data: dict[str, Any]) -> None:
        """
        Create or update denormalized product view.

        Uses upsert (INSERT ON CONFLICT UPDATE) for idempotency —
        safe to call multiple times with the same data.
        """
        # In production: upsert into a product_views table or search index
        # For now, log the operation (can be extended to PostgreSQL or Elasticsearch)
        logger.debug(f"Upsert product view: {data.get('sku')}")

    async def _update_product_price(self, aggregate_id: str, new_price: float) -> None:
        """Update only the price column in the read model."""
        logger.debug(f"Update price for {aggregate_id}: {new_price}")

    async def _deactivate_product(self, aggregate_id: str) -> None:
        """Set is_active=False in read model."""
        logger.debug(f"Deactivate product: {aggregate_id}")

    async def _set_product_active(self, aggregate_id: str, is_active: bool) -> None:
        """Set is_active in read model."""
        logger.debug(f"Set is_active={is_active} for {aggregate_id}")

    async def _update_product_field(
        self, aggregate_id: str, field: str, value: Any
    ) -> None:
        """Update a single field in the read model."""
        logger.debug(f"Update {field}={value!r} for {aggregate_id}")
