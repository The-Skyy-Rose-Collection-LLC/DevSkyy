"""
HuggingFace Spaces Sub-Agent
===============================

Wraps agents/skyyrose_spaces_orchestrator.py into the new hierarchy.

Parent: Imagery Core Agent
Capabilities: HF Spaces orchestration, quota management, health checks.
"""

from __future__ import annotations

from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent


class HfSpacesSubAgent(SubAgent):
    """HuggingFace Spaces orchestration and quota management."""

    name = "hf_spaces"
    parent_type = CoreAgentType.IMAGERY
    description = "HuggingFace Spaces orchestration, health checks, quota management"
    capabilities = [
        "run_space",
        "check_quota",
        "health_check",
    ]

    system_prompt = (
        "You are the HuggingFace Spaces orchestrator for SkyyRose/DevSkyy. "
        "You manage GPU-accelerated inference spaces for image generation, VTON, "
        "and 3D model creation. You handle quota management, space health checks, "
        "and workload routing across HF Spaces. Return structured orchestration "
        "plans with space IDs, GPU requirements, and fallback strategies."
    )

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        return await self._llm_execute(task)


__all__ = ["HfSpacesSubAgent"]
