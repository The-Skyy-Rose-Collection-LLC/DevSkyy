"""
Tripo 3D Sub-Agent
====================

Wraps agents/tripo_agent.py into the new hierarchy.

Parent: Imagery Core Agent
Capabilities: Text-to-3D, image-to-3D via Tripo3D API.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent

logger = logging.getLogger(__name__)


class Tripo3dSubAgent(SubAgent):
    """3D model generation via Tripo3D API."""

    name = "tripo_3d"
    parent_type = CoreAgentType.IMAGERY
    description = "3D model generation (text-to-3D, image-to-3D) via Tripo3D"
    capabilities = [
        "text_to_3d",
        "image_to_3d",
        "mesh_quality_validation",
    ]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._legacy_agent: Any = None

    def _get_legacy(self) -> Any:
        if self._legacy_agent is None:
            try:
                from agents.tripo_agent import TripoAssetAgent

                self._legacy_agent = TripoAssetAgent()
            except ImportError:
                logger.warning("[%s] Legacy TripoAssetAgent unavailable", self.name)
        return self._legacy_agent

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        legacy = self._get_legacy()
        if legacy and hasattr(legacy, "execute"):
            result = await legacy.execute(task, **kwargs)
            return {"success": True, "result": result}
        return {"success": False, "error": "TripoAssetAgent not available"}


__all__ = ["Tripo3dSubAgent"]
