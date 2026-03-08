"""
Tripo 3D Sub-Agent
====================

Wraps agents/tripo_agent.py into the new hierarchy.

Parent: Imagery Core Agent
Capabilities: Text-to-3D, image-to-3D via Tripo3D API.
"""

from __future__ import annotations

from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent


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

    system_prompt = (
        "You are the 3D Model Generation specialist (Tripo3D) for SkyyRose. "
        "You handle text-to-3D and image-to-3D generation for product visualizations, "
        "AR try-on assets, and 3D immersive collection experiences. "
        "Output formats: GLB, GLTF, OBJ. Return structured generation plans "
        "with prompt engineering for optimal 3D quality."
    )

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        return await self._llm_execute(task)


__all__ = ["Tripo3dSubAgent"]
