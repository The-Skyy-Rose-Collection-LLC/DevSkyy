"""
Meshy 3D Sub-Agent
====================

Wraps agents/meshy_agent.py into the new hierarchy.

Parent: Imagery Core Agent
Capabilities: 3D model generation via Meshy API (fallback to Tripo).
"""

from __future__ import annotations

import logging
from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent

logger = logging.getLogger(__name__)


class Meshy3dSubAgent(SubAgent):
    """3D model generation via Meshy API."""

    name = "meshy_3d"
    parent_type = CoreAgentType.IMAGERY
    description = "3D model generation via Meshy (fallback provider to Tripo)"
    capabilities = [
        "text_to_3d",
        "image_to_3d",
        "format_validation",
    ]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._legacy_agent: Any = None

    def _get_legacy(self) -> Any:
        if self._legacy_agent is None:
            try:
                from agents.meshy_agent import get_meshy_agent

                self._legacy_agent = get_meshy_agent()
            except ImportError:
                logger.warning("[%s] Legacy MeshyAgent unavailable", self.name)
        return self._legacy_agent

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        legacy = self._get_legacy()
        if legacy and hasattr(legacy, "execute"):
            result = await legacy.execute(task, **kwargs)
            return {"success": True, "result": result}
        return {"success": False, "error": "MeshyAgent not available"}


__all__ = ["Meshy3dSubAgent"]
