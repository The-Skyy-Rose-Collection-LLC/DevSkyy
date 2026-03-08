"""
Gemini Image Generation Sub-Agent
====================================

Wraps the Gemini image generation logic from skyyrose_imagery_agent.py.

Parent: Imagery Core Agent
Capabilities: AI image generation via Google Gemini (Flash/Pro).
"""

from __future__ import annotations

from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent


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

    system_prompt = (
        "You are the AI Image Generation specialist for SkyyRose luxury fashion. "
        "You create detailed image generation prompts for product renders, theme imagery, "
        "and scene compositions using Gemini Flash/Pro. Brand aesthetic: dark luxury, "
        "rose gold accents (#B76E79), dramatic lighting, editorial fashion photography style. "
        "Return structured prompts with style, composition, lighting, and mood directives."
    )

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        return await self._llm_execute(task)


__all__ = ["GeminiImageSubAgent"]
