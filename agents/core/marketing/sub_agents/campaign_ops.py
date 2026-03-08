"""
Campaign Operations Sub-Agent (Consolidated)
================================================

Consolidates: campaign_manager, ab_testing.
Wraps agents/marketing_agent.py into the new hierarchy.

Parent: Marketing Core Agent
Capabilities: Campaign lifecycle, A/B testing, audience segmentation.
"""

from __future__ import annotations

from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent


class CampaignOpsSubAgent(SubAgent):
    """Campaign management and A/B testing."""

    name = "campaign_ops"
    parent_type = CoreAgentType.MARKETING
    description = "Campaign lifecycle, A/B testing, audience segmentation"
    capabilities = [
        # campaign_manager
        "create_campaign",
        "schedule_campaign",
        "campaign_analytics",
        "audience_segment",
        # ab_testing
        "create_test",
        "evaluate_test",
        "winner_selection",
    ]

    ALIASES = ("campaign_manager", "ab_testing")

    system_prompt = (
        "You are the Campaign Operations specialist for SkyyRose luxury fashion. "
        "You plan marketing campaigns, design A/B tests, segment audiences, and "
        "analyze campaign performance. Target demographics: 18-35, fashion-forward, "
        "urban luxury enthusiasts. Return structured campaign plans with timelines, "
        "budgets, KPIs, and audience segments."
    )

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        return await self._llm_execute(task)


__all__ = ["CampaignOpsSubAgent"]
