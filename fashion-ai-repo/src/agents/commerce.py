"""Commerce Agent - Product listings, pricing, and SKU management."""

import time
from pathlib import Path
from typing import Any, Dict, List

from .base import BaseAgent


class CommerceAgent(BaseAgent):
    """Agent responsible for managing product catalog and commerce operations."""

    def __init__(self, *args, **kwargs):
        """
        Create a CommerceAgent and prepare its on-disk catalog directory.
        
        Sets the instance attribute `self.catalog_path` to `self.io_path / "catalog"` and ensures that directory exists on disk (creates parent directories if needed).
        """
        super().__init__(name="CommerceAgent", *args, **kwargs)
        self.catalog_path = self.io_path / "catalog"
        self.catalog_path.mkdir(parents=True, exist_ok=True)

    def get_supported_tasks(self) -> List[str]:
        """
        List the commerce task types this agent supports.
        
        Returns:
            List[str]: The supported task type strings: "list_sku", "update_pricing", "sync_inventory", and "process_order".
        """
        return ["list_sku", "update_pricing", "sync_inventory", "process_order"]

    async def process_task(self, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route a commerce task to the handler corresponding to task_type.
        
        Parameters:
            task_type (str): One of "list_sku", "update_pricing", "sync_inventory", or "process_order".
            payload (Dict[str, Any]): Task-specific parameters required by the chosen handler.
        
        Returns:
            Dict[str, Any]: The task-specific result (e.g., listing data, pricing update summary, inventory sync summary, or order result).
        
        Raises:
            ValueError: If task_type is not a supported task.
        """
        if task_type == "list_sku":
            return await self._list_sku(payload)
        elif task_type == "update_pricing":
            return await self._update_pricing(payload)
        elif task_type == "sync_inventory":
            return await self._sync_inventory(payload)
        elif task_type == "process_order":
            return await self._process_order(payload)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")

    async def _list_sku(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a product SKU listing from a design payload and notify MarketingAgent.
        
        Parameters:
            payload (Dict[str, Any]): Design information. Expected keys:
                - design_id (str): Identifier of the design (required).
                - style (str, optional): Style name, defaults to "modern".
                - color (str, optional): Color name, defaults to "neutral".
        
        Returns:
            Dict[str, Any]: SKU listing with keys:
                - sku (str): Generated SKU identifier.
                - design_id (str): Echoed design identifier.
                - name (str): Human-readable product name.
                - description (str): Short product description.
                - price_cents (int): Price in cents.
                - currency (str): Currency code (e.g., "USD").
                - inventory_count (int): Available inventory quantity.
                - status (str): Listing status (e.g., "active").
                - created_at (float): Creation timestamp (seconds since epoch).
        """
        self.logger.info(f"Creating SKU listing for design: {payload.get('design_id')}")

        design_id = payload.get("design_id")
        style = payload.get("style", "modern")
        color = payload.get("color", "neutral")

        # Generate SKU
        sku = f"SKU-{design_id.upper()}-{int(time.time())}"

        # Calculate base price (placeholder logic)
        base_price = 12000  # cents ($120.00)

        listing = {
            "sku": sku,
            "design_id": design_id,
            "name": f"{style.title()} {color.title()} Collection",
            "description": f"Exclusive AI-generated {style} design in {color}",
            "price_cents": base_price,
            "currency": "USD",
            "inventory_count": 100,
            "status": "active",
            "created_at": time.time(),
        }

        self.logger.info(f"SKU created: {sku}")

        # Notify Marketing Agent
        self.send_message(
            target_agent="MarketingAgent",
            task_type="announce",
            payload=listing,
        )

        return listing

    async def _update_pricing(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a pricing update for a SKU and return the recorded update details.
        
        Parameters:
            payload (Dict[str, Any]): Mapping with pricing update fields:
                - sku (str): Target SKU identifier.
                - price_cents (int): New price in cents.
                - reason (str, optional): Reason for the update; defaults to "manual_update".
        
        Returns:
            Dict[str, Any]: A dictionary containing:
                - sku (str): The SKU that was updated.
                - old_price_cents (int): Previous price in cents (placeholder value).
                - new_price_cents (int): Updated price in cents.
                - reason (str): Reason for the update.
                - updated_at (float): Unix timestamp when the update was recorded.
        """
        self.logger.info(f"Updating pricing for SKU: {payload.get('sku')}")

        sku = payload.get("sku")
        new_price = payload.get("price_cents")
        reason = payload.get("reason", "manual_update")

        result = {
            "sku": sku,
            "old_price_cents": 12000,  # Placeholder
            "new_price_cents": new_price,
            "reason": reason,
            "updated_at": time.time(),
        }

        self.logger.info(f"Pricing updated for {sku}")
        return result

    async def _sync_inventory(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronizes inventory levels and returns a summary of the synchronization.
        
        Parameters:
            payload (Dict[str, Any]): Optional parameters controlling the sync (for example source identifiers or filters); may be empty.
        
        Returns:
            dict: Summary of the sync with keys:
                - synced_count (int): Number of items synchronized.
                - items (List[Dict[str, Any]]): Details of each synchronized item.
                - synced_at (float): Unix timestamp when the sync completed.
        """
        self.logger.info("Synchronizing inventory")

        # Placeholder for inventory sync logic
        synced_items = []

        result = {
            "synced_count": len(synced_items),
            "items": synced_items,
            "synced_at": time.time(),
        }

        self.logger.info(f"Inventory synced: {len(synced_items)} items")
        return result

    async def _process_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a customer order, compute its total, mark it confirmed, and record the ledger.
        
        Parameters:
            payload (dict): Order data. Expected keys:
                - order_id: Identifier for the order.
                - items (list): List of item dicts; each item should include `price_cents` (int) and optional `quantity` (int, defaults to 1).
        
        Returns:
            dict: Order processing result containing:
                - order_id: The provided order identifier.
                - status: Order status, set to "confirmed".
                - total_cents: Sum of item price_cents multiplied by quantity.
                - processed_at: Unix timestamp when the order was processed.
        """
        self.logger.info(f"Processing order: {payload.get('order_id')}")

        order_id = payload.get("order_id")
        items = payload.get("items", [])

        # Calculate total
        total_cents = sum(item.get("price_cents", 0) * item.get("quantity", 1) for item in items)

        order_result = {
            "order_id": order_id,
            "status": "confirmed",
            "total_cents": total_cents,
            "processed_at": time.time(),
        }

        self.logger.info(f"Order processed: {order_id}")

        # Send to Finance Agent
        self.send_message(
            target_agent="FinanceAgent",
            task_type="record_ledger",
            payload=order_result,
        )

        return order_result