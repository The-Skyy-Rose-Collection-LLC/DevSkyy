"""
WordPress Assets Sub-Agent
============================

Wraps agents/wordpress_asset_agent.py into the new hierarchy.

Parent: Commerce Core Agent
Capabilities: WordPress media upload, product asset management, gallery creation.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent

logger = logging.getLogger(__name__)


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

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._legacy_agent: Any = None

    def _get_legacy(self) -> Any:
        if self._legacy_agent is None:
            try:
                from agents.wordpress_asset_agent import WordPressAssetAgent

                self._legacy_agent = WordPressAssetAgent()
            except ImportError:
                logger.warning("[%s] Legacy WordPressAssetAgent unavailable", self.name)
        return self._legacy_agent

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        legacy = self._get_legacy()
        if legacy and hasattr(legacy, "execute"):
            result = await legacy.execute(task, **kwargs)
            return {"success": True, "result": result}
        return {"success": False, "error": "WordPressAssetAgent not available"}


__all__ = ["WordPressAssetsSubAgent"]
