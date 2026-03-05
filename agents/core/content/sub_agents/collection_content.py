"""
Collection Content Sub-Agent
==============================

Wraps agents/collection_content_agent.py into the new hierarchy.

Parent: Content Core Agent
Capabilities: Collection page sections, product descriptions, hero content.
"""

from __future__ import annotations

from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent


class CollectionContentSubAgent(SubAgent):
    """Collection content — page sections, product copy, hero banners."""

    name = "collection_content"
    parent_type = CoreAgentType.CONTENT
    description = "Collection page sections, product descriptions, hero content"
    capabilities = [
        "generate_section",
        "product_description",
        "hero_content",
        "collection_overview",
    ]

    system_prompt = (
        "You are the Collection Content specialist for SkyyRose luxury fashion. "
        "Collections: Black Rose (gothic cathedral aesthetic), Love Hurts (dark castle romance), "
        "Signature (urban city tour), Kids Capsule (junior luxury). "
        "You generate collection page sections, hero banners, product descriptions, "
        "and overview copy. Brand voice: bold, poetic, street luxury."
    )

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        return await self._llm_execute(task)


__all__ = ["CollectionContentSubAgent"]
