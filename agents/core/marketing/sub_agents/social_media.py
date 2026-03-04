"""
Social Media Sub-Agent
=======================

Wraps agents/social_media_agent.py into the new hierarchy.

Parent: Marketing Core Agent
Capabilities: Post scheduling, engagement tracking, content generation, analytics.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent

logger = logging.getLogger(__name__)


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

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._legacy_agent: Any = None

    def _get_legacy(self) -> Any:
        if self._legacy_agent is None:
            try:
                from agents.social_media_agent import SocialMediaAgent
                from adk.base import AgentConfig

                config = AgentConfig(name="social_media", description="Social media ops")
                self._legacy_agent = SocialMediaAgent(config)
            except ImportError:
                logger.warning("[%s] Legacy SocialMediaAgent unavailable", self.name)
        return self._legacy_agent

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        legacy = self._get_legacy()
        if legacy and hasattr(legacy, "execute"):
            result = await legacy.execute(task, **kwargs)
            return {"success": True, "result": result}
        return {"success": False, "error": "SocialMediaAgent not available"}


__all__ = ["SocialMediaSubAgent"]
