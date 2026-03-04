"""
Collection Content Sub-Agent
==============================

Wraps agents/collection_content_agent.py into the new hierarchy.

Parent: Content Core Agent
Capabilities: Collection page sections, product descriptions, hero content.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent

logger = logging.getLogger(__name__)


class CollectionContentSubAgent(SubAgent):
    """Collection content — page sections, product copy, hero banners."""

    name = "collection_content"
    parent_type = CoreAgentType.CONTENT
    description = "Collection page sections, product descriptions, hero content"
    capabilities = [
        "generate_section",
        "product_description",
        "hero_content",
        "collection_overview",
    ]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._legacy_agent: Any = None

    def _get_legacy(self) -> Any:
        if self._legacy_agent is None:
            try:
                from agents.collection_content_agent import CollectionContentAgent

                self._legacy_agent = CollectionContentAgent()
            except ImportError:
                logger.warning("[%s] Legacy CollectionContentAgent unavailable", self.name)
        return self._legacy_agent

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        legacy = self._get_legacy()
        if legacy and hasattr(legacy, "execute"):
            result = await legacy.execute(task, **kwargs)
            return {"success": True, "result": result}
        return {"success": False, "error": "CollectionContentAgent not available"}


__all__ = ["CollectionContentSubAgent"]
