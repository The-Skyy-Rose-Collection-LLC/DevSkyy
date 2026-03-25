"""
WordPress Bridge Sub-Agent
============================

Bridges WooCommerce product sync between DevSkyy and WordPress.
Distinct from wordpress_assets (media uploads) — this handles product data sync.

Parent: Commerce Core Agent
Capabilities: WooCommerce product sync, category mapping, variant management.
"""

from __future__ import annotations

from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent


class WordPressBridgeSubAgent(SubAgent):
    """WooCommerce product data sync and category mapping."""

    name = "wordpress_bridge"
    parent_type = CoreAgentType.COMMERCE
    description = "WooCommerce product sync, category mapping, variant management"
    capabilities = [
        "sync_products",
        "map_categories",
        "manage_variants",
        "update_woo_fields",
    ]

    system_prompt = (
        "You are the WooCommerce Bridge specialist for SkyyRose. You handle product "
        "data sync between the DevSkyy backend and WordPress/WooCommerce. You map "
        "categories, manage product variants (sizes, colors), and sync inventory/pricing. "
        "Use WooCommerce REST API v3 patterns. Return structured sync plans."
    )

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        return await self._llm_execute(task)


__all__ = ["WordPressBridgeSubAgent"]
