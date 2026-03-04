"""
Commerce Core Agent
====================

Domain: All revenue-generating operations.
Sub-agents: Product Manager, Pricing Engine, Inventory Tracker, Order Processor, WordPress Bridge.

Wraps the existing CommerceAgent (agents/commerce_agent.py) with:
- CoreAgent base (self-healing, circuit breaker, escalation)
- Sub-agent delegation for specialized tasks
- 3D portal integration
"""

from __future__ import annotations

import logging
from typing import Any

from agents.core.base import CoreAgent, CoreAgentType

logger = logging.getLogger(__name__)


class CommerceCoreAgent(CoreAgent):
    """
    Commerce Core Agent — manages all revenue-generating operations.

    Delegates to sub-agents:
    - product_manager: Product CRUD, validation, image checks
    - pricing_engine: Dynamic pricing, competitor analysis
    - inventory_tracker: Stock sync, oversell prevention
    - order_processor: Order lifecycle, payment gateway
    - wordpress_bridge: WooCommerce sync, product push
    """

    core_type = CoreAgentType.COMMERCE
    name = "commerce_core"
    description = "All revenue-generating operations: products, orders, pricing, inventory"

    def __init__(self, *, correlation_id: str | None = None, **kwargs: Any) -> None:
        super().__init__(correlation_id=correlation_id, **kwargs)

        # Lazy-load the existing CommerceAgent to preserve backward compat
        self._legacy_agent: Any = None

    def _get_legacy_agent(self) -> Any:
        """Lazy-load the existing CommerceAgent."""
        if self._legacy_agent is None:
            try:
                from agents.commerce_agent import CommerceAgent
                from adk.base import AgentConfig

                config = AgentConfig(
                    name="commerce",
                    description="Commerce operations",
                )
                self._legacy_agent = CommerceAgent(config)
            except ImportError:
                logger.warning("[%s] Legacy CommerceAgent unavailable", self.name)
        return self._legacy_agent

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        """
        Execute a commerce task.

        Routes to sub-agents based on task type, falls back to legacy agent.
        """
        task_lower = task.lower()

        # Route to sub-agents
        if any(kw in task_lower for kw in ["product", "catalog", "sku"]):
            if "product_manager" in self._sub_agents:
                return await self.delegate("product_manager", task, **kwargs)

        if any(kw in task_lower for kw in ["price", "pricing", "discount"]):
            if "pricing_engine" in self._sub_agents:
                return await self.delegate("pricing_engine", task, **kwargs)

        if any(kw in task_lower for kw in ["inventory", "stock", "quantity"]):
            if "inventory_tracker" in self._sub_agents:
                return await self.delegate("inventory_tracker", task, **kwargs)

        if any(kw in task_lower for kw in ["order", "checkout", "payment"]):
            if "order_processor" in self._sub_agents:
                return await self.delegate("order_processor", task, **kwargs)

        if any(kw in task_lower for kw in ["wordpress", "woocommerce", "sync"]):
            if "wordpress_bridge" in self._sub_agents:
                return await self.delegate("wordpress_bridge", task, **kwargs)

        # Fallback to legacy agent
        legacy = self._get_legacy_agent()
        if legacy and hasattr(legacy, "execute"):
            result = await legacy.execute(task, **kwargs)
            return {"success": True, "result": result}

        return {
            "success": False,
            "error": f"No handler for commerce task: {task[:100]}",
        }


__all__ = ["CommerceCoreAgent"]
