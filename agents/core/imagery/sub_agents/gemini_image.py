"""
Gemini Image Generation Sub-Agent
====================================

Wraps the Gemini image generation logic from skyyrose_imagery_agent.py.

Parent: Imagery Core Agent
Capabilities: AI image generation via Google Gemini (Flash/Pro).
"""

from __future__ import annotations

import logging
from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent

logger = logging.getLogger(__name__)


class GeminiImageSubAgent(SubAgent):
    """AI image generation via Google Gemini."""

    name = "gemini_image"
    parent_type = CoreAgentType.IMAGERY
    description = "AI image generation using Gemini Flash/Pro"
    capabilities = [
        "product_render",
        "theme_imagery",
        "mascot_generation",
        "scene_generation",
    ]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._legacy_agent: Any = None

    def _get_legacy(self) -> Any:
        if self._legacy_agent is None:
            try:
                from agents.skyyrose_imagery_agent import SkyyRoseImageryAgent
                from adk.base import AgentConfig

                config = AgentConfig(name="imagery", description="Image generation")
                self._legacy_agent = SkyyRoseImageryAgent(config)
            except ImportError:
                logger.warning("[%s] Legacy SkyyRoseImageryAgent unavailable", self.name)
        return self._legacy_agent

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        legacy = self._get_legacy()
        if legacy and hasattr(legacy, "execute"):
            result = await legacy.execute(task, **kwargs)
            return {"success": True, "result": result}
        return {"success": False, "error": "SkyyRoseImageryAgent not available"}


__all__ = ["GeminiImageSubAgent"]
