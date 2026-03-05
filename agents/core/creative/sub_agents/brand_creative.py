"""
Brand & Creative Sub-Agent (Consolidated)
============================================

Consolidates: design_system, brand_guardian, asset_generator, quality_checker.
Wraps agents/creative_agent.py into the new hierarchy.

Parent: Creative Core Agent
Capabilities: Design tokens, brand enforcement, asset generation, QA.
"""

from __future__ import annotations

from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent


class BrandCreativeSubAgent(SubAgent):
    """Design system, brand enforcement, asset generation, and quality checks."""

    name = "brand_creative"
    parent_type = CoreAgentType.CREATIVE
    description = "Design tokens, brand guidelines, asset generation, visual QA"
    capabilities = [
        # design_system
        "design_tokens",
        "color_palette",
        "typography",
        "spacing_grid",
        # brand_guardian
        "brand_check",
        "logo_usage",
        "voice_tone",
        "style_audit",
        # asset_generator
        "generate_asset",
        "resize_asset",
        "format_convert",
        # quality_checker
        "visual_qa",
        "consistency_check",
        "contrast_check",
    ]

    ALIASES = ("design_system", "brand_guardian", "asset_generator", "quality_checker")

    system_prompt = (
        "You are the Brand & Creative Director for SkyyRose luxury fashion. "
        "Design system: primary #B76E79 (rose gold), accent #1a1a2e (deep navy), "
        "font: Playfair Display (headings) + Inter (body). "
        "You enforce brand guidelines, generate design token specs, review visual "
        "consistency, and create asset briefs. Always maintain luxury aesthetic standards."
    )

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        return await self._llm_execute(task)


__all__ = ["BrandCreativeSubAgent"]
