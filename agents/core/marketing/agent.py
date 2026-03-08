"""
Marketing Core Agent
=====================

Domain: Campaigns, social media, audience growth.
Sub-agents: Social Media, Campaign Manager, A/B Testing.

Wraps the existing MarketingAgent with CoreAgent base.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.core.base import CoreAgent, CoreAgentType

logger = logging.getLogger(__name__)


class MarketingCoreAgent(CoreAgent):
    """
    Marketing Core Agent — campaigns, social, audience growth.

    Delegates to sub-agents:
    - social_media: Post scheduling, engagement tracking, content generation
    - campaign_manager: Campaign lifecycle, budget allocation, auto-pause
    - ab_testing: Experiment design, statistical significance, winner selection
    """

    core_type = CoreAgentType.MARKETING
    name = "marketing_core"
    description = "Campaigns, social media, audience growth"

    def __init__(self, *, correlation_id: str | None = None, **kwargs: Any) -> None:
        super().__init__(correlation_id=correlation_id, **kwargs)
        self._legacy_agent: Any = None
        self._register_sub_agents()

    def _register_sub_agents(self) -> None:
        """Auto-register consolidated sub-agents with aliases."""
        try:
            from agents.core.marketing.sub_agents.social_media import (
                SocialMediaSubAgent,
            )

            self.register_sub_agent("social_media", SocialMediaSubAgent())
        except ImportError:
            logger.debug("[%s] SocialMediaSubAgent unavailable", self.name)

        try:
            from agents.core.marketing.sub_agents.campaign_ops import (
                CampaignOpsSubAgent,
            )

            agent = CampaignOpsSubAgent()
            self.register_sub_agent("campaign_ops", agent)
            for alias in CampaignOpsSubAgent.ALIASES:
                self.register_sub_agent(alias, agent)
        except ImportError:
            logger.debug("[%s] CampaignOpsSubAgent unavailable", self.name)

    def _get_legacy_agent(self) -> Any:
        if self._legacy_agent is None:
            try:
                from adk.base import AgentConfig
                from agents.marketing_agent import MarketingAgent

                config = AgentConfig(name="marketing", description="Marketing operations")
                self._legacy_agent = MarketingAgent(config)
            except ImportError:
                logger.warning("[%s] Legacy MarketingAgent unavailable", self.name)
        return self._legacy_agent

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["social", "post", "instagram", "twitter", "tiktok"]):
            if "social_media" in self._sub_agents:
                return await self.delegate("social_media", task, **kwargs)

        if any(kw in task_lower for kw in ["campaign", "email", "newsletter", "audience"]):
            if "campaign_manager" in self._sub_agents:
                return await self.delegate("campaign_manager", task, **kwargs)

        if any(kw in task_lower for kw in ["a/b", "test", "experiment", "variant"]):
            if "ab_testing" in self._sub_agents:
                return await self.delegate("ab_testing", task, **kwargs)

        legacy = self._get_legacy_agent()
        if legacy and hasattr(legacy, "execute"):
            result = await legacy.execute(task, **kwargs)
            return {"success": True, "result": result}

        return {"success": False, "error": f"No handler for marketing task: {task[:100]}"}


__all__ = ["MarketingCoreAgent"]
