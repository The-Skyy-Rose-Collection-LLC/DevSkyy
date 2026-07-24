"""
Tripo 3D Sub-Agent
====================

Planning-only wrapper in the CoreAgent/Orchestrator hierarchy (see agents/CLAUDE.md
"Two parallel hierarchies"). It does NOT call the real Tripo3D API — execute() routes
the free-text task through an LLM (_llm_execute) and returns a generation *plan*
(prompt engineering, format recommendations), never a downloaded 3D asset.

This is the same pattern used by every sibling in agents/core/imagery/sub_agents/
(gemini_image, fashn_vton, meshy_3d, hf_spaces all do `return await self._llm_execute(task)`)
and is asserted by tests/test_sub_agents.py::TestSubAgentExecute — Tripo3dSubAgent is NOT
in that test's _CUSTOM_EXECUTE_AGENTS exemption, so LLM-only execution is the intended,
tested contract for this class, not an oversight.

Real Tripo3D generation (actual API calls, downloaded GLB/GLTF/OBJ files) happens via a
separate, already-correctly-wired path that this sub-agent is NOT part of:
    api/v1/media.py::_run_3d_generation_background()
        -> agents.tripo_agent.TripoAssetAgent()
        -> agent._tool_generate_from_text() / agent._tool_generate_from_image()
That path receives structured params (product_name, collection, garment_type, image_path)
from a validated request body. This sub-agent only ever receives a free-text `task` string
from Orchestrator.route()/ImageryCoreAgent.execute() — there is no structured input here to
bridge to TripoAssetAgent.run() without fabricating a parser, so callers that need a real
3D asset must go through api/v1/media.py, not through this sub-agent.

Parent: Imagery Core Agent
Capabilities: Generation *planning* only (prompt engineering for text-to-3D / image-to-3D).
"""

from __future__ import annotations

import logging
from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent

logger = logging.getLogger(__name__)


class Tripo3dSubAgent(SubAgent):
    """LLM-based 3D generation *planner* — does not call the real Tripo3D API.

    See module docstring for the real generation path (api/v1/media.py -> TripoAssetAgent).
    """

    name = "tripo_3d"
    parent_type = CoreAgentType.IMAGERY
    description = (
        "3D generation planning (text-to-3D, image-to-3D prompt engineering) — "
        "LLM plan only, does not call the Tripo3D API. Real generation: "
        "api/v1/media.py -> agents.tripo_agent.TripoAssetAgent"
    )
    capabilities = [
        "text_to_3d_planning",
        "image_to_3d_planning",
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
        """Return an LLM-generated 3D generation plan for `task`.

        This does NOT call the real Tripo3D API and returns no downloaded asset —
        see module docstring for the real generation path (api/v1/media.py ->
        agents.tripo_agent.TripoAssetAgent). Callers needing an actual 3D asset
        must not treat this result as one.
        """
        logger.warning(
            "[%s] execute() returns an LLM-generated plan only — no real Tripo3D "
            "API call is made here. Real 3D generation: api/v1/media.py -> "
            "agents.tripo_agent.TripoAssetAgent.",
            self.name,
        )
        return await self._llm_execute(task)


__all__ = ["Tripo3dSubAgent"]
