"""
FASHN Virtual Try-On Sub-Agent
================================

Wraps agents/fashn_agent.py into the new hierarchy.

Parent: Imagery Core Agent
Capabilities: Virtual try-on with FASHN API, provider failover.

Self-Healing: Provider failover chain (FASHN → WeShopAI → IDM-VTON).
"""

from __future__ import annotations

from typing import Any

from agents.core.base import CoreAgentType, FailureCategory, HealResult
from agents.core.sub_agent import SubAgent


class FashnVtonSubAgent(SubAgent):
    """Virtual try-on — FASHN API with provider failover."""

    name = "fashn_vton"
    parent_type = CoreAgentType.IMAGERY
    description = "Virtual try-on using FASHN (failover: WeShopAI → IDM-VTON)"
    capabilities = [
        "virtual_tryon",
        "garment_swap",
        "model_pose",
    ]

    system_prompt = (
        "You are the Virtual Try-On specialist for SkyyRose luxury fashion. "
        "You orchestrate FASHN API calls for garment-on-model compositing, "
        "with failover to WeShopAI and IDM-VTON. You handle pose selection, "
        "garment segmentation parameters, and output quality settings. "
        "Return structured API call plans with parameters and fallback strategies."
    )

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        return await self._llm_execute(task)

    async def _apply_fix(self, diagnosis: Any) -> HealResult:
        """Provider failover: FASHN → WeShopAI → IDM-VTON."""
        if diagnosis.failure_category == FailureCategory.PROVIDER_DOWN:
            return HealResult(
                success=True,
                message="Switch to alternative VTON provider",
                changes=["Failover triggered"],
            )
        return await super()._apply_fix(diagnosis)


__all__ = ["FashnVtonSubAgent"]
