"""
Social Media Sub-Agent
=======================

Wraps agents/social_media_agent.py into the new hierarchy.

Parent: Marketing Core Agent
Capabilities: Post scheduling, engagement tracking, content generation, analytics.
"""

from __future__ import annotations

from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent


class SocialMediaSubAgent(SubAgent):
    """Social media management — scheduling, engagement, content."""

    name = "social_media"
    parent_type = CoreAgentType.MARKETING
    description = "Post scheduling, engagement tracking, content generation"
    capabilities = [
        "schedule_post",
        "track_engagement",
        "generate_content",
        "analyze_performance",
    ]

    system_prompt = (
        "You are the Social Media specialist for SkyyRose luxury fashion. "
        "Platforms: Instagram (primary), TikTok, Pinterest, X/Twitter. "
        "Brand voice: aspirational yet authentic, street luxury meets haute couture. "
        "You create post captions, schedule content calendars, analyze engagement metrics, "
        "and generate hashtag strategies. Always include visual direction notes."
    )

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        return await self._llm_execute(task)


__all__ = ["SocialMediaSubAgent"]
