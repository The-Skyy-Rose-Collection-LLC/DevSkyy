"""
Meshy 3D Sub-Agent
====================

Wraps agents/meshy_agent.py into the new hierarchy.

Parent: Imagery Core Agent
Capabilities: 3D model generation via Meshy API (fallback to Tripo).
"""

from __future__ import annotations

from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent


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

    system_prompt = (
        "You are the 3D Model Generation specialist (Meshy) for SkyyRose. "
        "Meshy is the fallback provider to Tripo3D. You handle text-to-3D and "
        "image-to-3D with Meshy API, focusing on fashion product meshes and "
        "AR-ready assets. Return structured generation parameters and quality checks."
    )

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        return await self._llm_execute(task)


__all__ = ["Meshy3dSubAgent"]
