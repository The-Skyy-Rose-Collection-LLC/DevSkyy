"""
WordPress Assets Sub-Agent
============================

Wraps agents/wordpress_asset_agent.py into the new hierarchy.

Parent: Commerce Core Agent
Capabilities: WordPress media upload, product asset management, gallery creation.
"""

from __future__ import annotations

from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent


class WordPressAssetsSubAgent(SubAgent):
    """WordPress media and asset management."""

    name = "wordpress_assets"
    parent_type = CoreAgentType.COMMERCE
    description = "WordPress media upload, product assets, gallery management"
    capabilities = [
        "upload_media",
        "manage_gallery",
        "product_images",
        "3d_model_upload",
    ]

    system_prompt = (
        "You are the WordPress Assets specialist for SkyyRose luxury fashion. "
        "You manage media uploads, product image galleries, and 3D model assets "
        "on the WordPress/WooCommerce site (skyyrose.co). You know WordPress REST API "
        "media endpoints and gallery shortcodes. Respond with actionable steps and API calls."
    )

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        return await self._llm_execute(task)


__all__ = ["WordPressAssetsSubAgent"]
