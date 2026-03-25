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

import json
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

    async def handle(self, event: Event) -> None:
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

    async def _on_product_created(self, event: Event) -> None:
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

    async def _on_product_price_changed(self, event: Event) -> None:
        """Update price field in read model."""
        new_price = event.data.get("new_price", 0.0)
        await self._update_product_price(event.aggregate_id, new_price)

    async def _on_product_deleted(self, event: Event) -> None:
        """Soft-delete product from read model."""
        await self._deactivate_product(event.aggregate_id)

    async def _on_product_activated(self, event: Event) -> None:
        """Mark product as active in read model."""
        await self._set_product_active(event.aggregate_id, is_active=True)

    async def _on_product_deactivated(self, event: Event) -> None:
        """Mark product as inactive in read model."""
        await self._set_product_active(event.aggregate_id, is_active=False)

    async def _on_product_name_changed(self, event: Event) -> None:
        """Update product name in read model."""
        await self._update_product_field(event.aggregate_id, "name", event.data.get("name", ""))

    def subscribe(self) -> None:
        """Register this handler with the global event bus."""
        event_bus.subscribe(self.handle)

    # ---------------------------------------------------------------------------
    # Read model persistence helpers — override in tests
    # ---------------------------------------------------------------------------

    _ALLOWED_FIELDS: set[str] = {
        "name",
        "description",
        "price",
        "collection",
        "category",
        "sku",
    }

    async def _invalidate_cache(self) -> None:
        """Invalidate product caches after a write. Best-effort, never raises."""
        try:
            from core.caching.multi_tier_cache import MultiTierCache

            cache = MultiTierCache()
            await cache.invalidate_pattern("products")
        except Exception:
            logger.debug("Cache invalidation skipped")

    async def _upsert_product_view(self, data: dict[str, Any]) -> None:
        """
        Create or update denormalized product view.

        Uses upsert (INSERT ON CONFLICT UPDATE) for idempotency —
        safe to call multiple times with the same data.
        """
        from database.db import DatabaseManager, Product

        product_id = data.get("aggregate_id", "")
        images_json = json.dumps(data.get("images", []))

        db = DatabaseManager()
        async with db.session() as session:
            existing = await session.get(Product, product_id)
            if existing:
                existing.sku = data.get("sku", existing.sku)
                existing.name = data.get("name", existing.name)
                existing.price = data.get("price", existing.price)
                existing.collection = data.get("collection", existing.collection)
                existing.is_active = data.get("is_active", existing.is_active)
                existing.images_json = images_json
            else:
                product = Product(
                    id=product_id,
                    sku=data.get("sku", ""),
                    name=data.get("name", ""),
                    price=data.get("price", 0.0),
                    collection=data.get("collection"),
                    is_active=data.get("is_active", True),
                    images_json=images_json,
                )
                session.add(product)

        logger.debug(f"Upsert product view: {data.get('sku')}")
        await self._invalidate_cache()

    async def _update_product_price(self, aggregate_id: str, new_price: float) -> None:
        """Update only the price column in the read model."""
        from database.db import DatabaseManager, Product

        db = DatabaseManager()
        async with db.session() as session:
            product = await session.get(Product, aggregate_id)
            if product:
                product.price = new_price

        logger.debug(f"Update price for {aggregate_id}: {new_price}")
        await self._invalidate_cache()

    async def _deactivate_product(self, aggregate_id: str) -> None:
        """Set is_active=False in read model."""
        from database.db import DatabaseManager, Product

        db = DatabaseManager()
        async with db.session() as session:
            product = await session.get(Product, aggregate_id)
            if product:
                product.is_active = False

        logger.debug(f"Deactivate product: {aggregate_id}")
        await self._invalidate_cache()

    async def _set_product_active(self, aggregate_id: str, is_active: bool) -> None:
        """Set is_active in read model."""
        from database.db import DatabaseManager, Product

        db = DatabaseManager()
        async with db.session() as session:
            product = await session.get(Product, aggregate_id)
            if product:
                product.is_active = is_active

        logger.debug(f"Set is_active={is_active} for {aggregate_id}")
        await self._invalidate_cache()

    async def _update_product_field(self, aggregate_id: str, field: str, value: Any) -> None:
        """
        Update a single field in the read model.

        CRITICAL: Only whitelisted fields are allowed to prevent injection.
        """
        if field not in self._ALLOWED_FIELDS:
            logger.warning(f"Rejected update for disallowed field {field!r} on {aggregate_id}")
            return

        from database.db import DatabaseManager, Product

        db = DatabaseManager()
        async with db.session() as session:
            product = await session.get(Product, aggregate_id)
            if product:
                setattr(product, field, value)

        logger.debug(f"Update {field}={value!r} for {aggregate_id}")
        await self._invalidate_cache()
