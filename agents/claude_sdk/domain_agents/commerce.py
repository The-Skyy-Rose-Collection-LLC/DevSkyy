"""
SDK Commerce Domain Agents
=============================

SDK-powered sub-agents for the Commerce core domain.
These agents can read product catalogs, query files,
analyze pricing data, and manage catalog operations.

Agents:
    SDKCatalogManagerAgent — Read/update product catalog data
    SDKPriceOptimizerAgent — Analyze pricing with real data access
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agents.claude_sdk.sdk_sub_agent import SDKSubAgent
from agents.claude_sdk.tool_bridge import ToolProfile
from agents.core.base import CoreAgentType


class SDKCatalogManagerAgent(SDKSubAgent):
    """Product catalog manager with file access.

    Can read the product catalog source files, verify SKUs,
    cross-reference collections, and generate catalog reports.
    """

    name = "sdk_catalog_manager"
    parent_type = CoreAgentType.COMMERCE
    description = "Manage product catalog with file access and verification"
    capabilities = [
        "catalog_read",
        "sku_verify",
        "collection_audit",
        "inventory_report",
        "product_export",
    ]
    sdk_tools = ToolProfile.COMMERCE
    sdk_model = "sonnet"
    sdk_output_base = Path("data/sdk_sessions/commerce/catalog")

    def _sdk_default_prompt(self) -> str:
        return (
            "You are the DevSkyy Catalog Manager for SkyyRose.\n\n"
            "Product data sources (READ THESE — never invent SKUs):\n"
            "- data/product-catalog.csv → canonical product catalog\n"
            "- skyyrose/assets/data/garment-analysis.json → colors\n\n"
            "Collections:\n"
            "- Black Rose: br-001 through br-011 (11 products)\n"
            "- Love Hurts: lh-002 through lh-006 (5 products, "
            "lh-001 DELETED)\n"
            "- Signature: sg-001 through sg-014 (13 products, "
            "sg-008 DELETED)\n"
            "- Kids Capsule: kids-001, kids-002 (2 products)\n\n"
            "Rules:\n"
            "- NEVER fabricate SKU IDs or product names\n"
            "- NEVER guess prices — read from source\n"
            "- Always cross-reference catalog before reporting\n"
            "- Pre-order status is authoritative from the catalog\n"
            "- 31 total products across 4 collections"
        )


class SDKPriceOptimizerAgent(SDKSubAgent):
    """Pricing analyst with data access and research.

    Can read current pricing, research competitor prices,
    analyze margins, and recommend pricing strategies.
    """

    name = "sdk_price_optimizer"
    parent_type = CoreAgentType.COMMERCE
    description = "Pricing analysis with catalog access and market research"
    capabilities = [
        "price_analysis",
        "margin_calculate",
        "competitor_compare",
        "bundle_pricing",
        "discount_strategy",
    ]
    sdk_tools = ToolProfile.COMMERCE + ["WebSearch", "WebFetch"]
    sdk_model = "sonnet"
    sdk_output_base = Path("data/sdk_sessions/commerce/pricing")

    def _sdk_default_prompt(self) -> str:
        return (
            "You are the DevSkyy Price Optimizer for SkyyRose.\n\n"
            "Current price ranges:\n"
            "- Black Rose: $35-$115\n"
            "- Love Hurts: $45-$265\n"
            "- Signature: $25-$195\n"
            "- Kids Capsule: $40\n\n"
            "You can:\n"
            "- Read current pricing from scripts/nano-banana-vton.py\n"
            "- Research competitor pricing via web search\n"
            "- Calculate margins and optimize price points\n"
            "- Recommend bundle pricing strategies\n"
            "- Analyze price elasticity based on market data\n\n"
            "Always read current prices from the catalog first. "
            "Never guess — verify from the source file."
        )

    def _build_task_prompt(self, task: str, **kwargs: Any) -> str:
        """Enrich with collection context for targeted analysis."""
        base = super()._build_task_prompt(task, **kwargs)
        collection = kwargs.get("collection")
        if collection:
            base += (
                f"\n\nFocus on: {collection} collection\n"
                "Read scripts/nano-banana-vton.py to get current "
                "prices for all products in this collection."
            )
        return base


__all__ = [
    "SDKCatalogManagerAgent",
    "SDKPriceOptimizerAgent",
]
