"""
SDK Marketing Domain Agents
==============================

SDK-powered sub-agents for the Marketing core domain.
These agents can research competitors, analyze trends via web search,
and generate data-backed campaign strategies.

Agents:
    SDKCampaignAnalystAgent  — Analyze campaigns with real data access
    SDKCompetitiveIntelAgent — Web research on competitor brands
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agents.claude_sdk.sdk_sub_agent import SDKSubAgent
from agents.claude_sdk.tool_bridge import ToolProfile
from agents.core.base import CoreAgentType


class SDKCampaignAnalystAgent(SDKSubAgent):
    """Campaign analyst with data and web access.

    Can read campaign data files, research market trends,
    analyze performance metrics, and generate optimization plans.
    """

    name = "sdk_campaign_analyst"
    parent_type = CoreAgentType.MARKETING
    description = "Campaign analysis with data access and web research"
    capabilities = [
        "campaign_analyze",
        "audience_research",
        "trend_research",
        "kpi_dashboard",
        "channel_optimize",
    ]
    sdk_tools = ToolProfile.MARKETING
    sdk_model = "sonnet"
    sdk_output_base = Path("data/sdk_sessions/marketing/campaigns")

    def _sdk_default_prompt(self) -> str:
        return (
            "You are the DevSkyy Campaign Analyst for SkyyRose.\n\n"
            "Target demographics:\n"
            "- Age: 18-35, fashion-forward, urban luxury\n"
            "- Bay Area roots, streetwear-meets-haute-couture\n"
            "- Pre-order model (most products are pre-order)\n\n"
            "You can:\n"
            "- Read campaign data and analytics files\n"
            "- Research market trends and competitor campaigns\n"
            "- Analyze social media engagement patterns\n"
            "- Generate data-backed campaign recommendations\n\n"
            "Always ground recommendations in data. Include "
            "specific metrics, benchmarks, and timelines. "
            "Reference competitor examples when relevant."
        )


class SDKCompetitiveIntelAgent(SDKSubAgent):
    """Competitive intelligence with web search capabilities.

    Researches competitor brands, pricing strategies, social media
    presence, and market positioning via web search.
    """

    name = "sdk_competitive_intel"
    parent_type = CoreAgentType.MARKETING
    description = "Competitor research via web search and analysis"
    capabilities = [
        "competitor_research",
        "price_benchmark",
        "social_analysis",
        "market_positioning",
        "trend_forecast",
    ]
    sdk_tools = ToolProfile.RESEARCH
    sdk_model = "sonnet"
    sdk_output_base = Path("data/sdk_sessions/marketing/intel")

    def _sdk_default_prompt(self) -> str:
        return (
            "You are the DevSkyy Competitive Intelligence agent.\n\n"
            "SkyyRose positioning:\n"
            "- Luxury streetwear, Bay Area roots\n"
            "- Price range: $25-$265\n"
            "- Competitors: Fear of God, Rhude, Amiri, Off-White, "
            "BAPE (streetwear luxury segment)\n\n"
            "You research:\n"
            "- Competitor pricing and product strategies\n"
            "- Social media presence and engagement rates\n"
            "- Market trends in luxury streetwear\n"
            "- Drop/collection strategies\n"
            "- Customer sentiment and reviews\n\n"
            "Use web search to gather current data. Save research "
            "notes to the session directory. Always cite sources."
        )

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        """Execute with web research — no LLM fallback."""
        prompt = self._build_task_prompt(task, **kwargs)
        result = await self._sdk_execute(prompt, label="intel")

        if result.success:
            return {
                "success": True,
                "result": result.response,
                "agent": self.name,
                "execution_mode": "sdk",
                "metrics": result.metrics,
            }

        # Competitive intel needs web access — no text-only fallback
        return {
            "success": False,
            "result": "",
            "agent": self.name,
            "error": result.error,
            "execution_mode": "failed",
        }


__all__ = [
    "SDKCampaignAnalystAgent",
    "SDKCompetitiveIntelAgent",
]
