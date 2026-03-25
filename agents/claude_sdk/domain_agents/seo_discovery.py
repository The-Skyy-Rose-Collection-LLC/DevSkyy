"""
SDK SEO & Discovery Domain Agent
====================================

SDK-powered agent for organic discovery optimization —
beyond on-page SEO into full search ecosystem strategy:
SERP analysis, content gap detection, backlink profiling,
and multi-platform discovery (Google, Pinterest, TikTok).

Complements the SDKSeoWriterAgent (on-page meta/schema) with
off-page strategy and competitive search landscape analysis.

Agent:
    SDKSEODiscoveryAgent — SERP analysis, content gaps, discovery strategy
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agents.claude_sdk.sdk_sub_agent import SDKSubAgent
from agents.claude_sdk.tool_bridge import ToolProfile
from agents.core.base import CoreAgentType


class SDKSEODiscoveryAgent(SDKSubAgent):
    """SEO and multi-platform discovery strategist with web access.

    Analyzes search landscapes, identifies content gaps,
    profiles competitor backlinks, and optimizes for discovery
    across Google, Pinterest, TikTok, and visual search.
    """

    name = "sdk_seo_discovery"
    parent_type = CoreAgentType.CONTENT
    description = "SERP analysis, content gaps, and multi-platform discovery"
    capabilities = [
        "serp_analyze",
        "content_gap",
        "backlink_profile",
        "keyword_cluster",
        "visual_search_optimize",
        "discovery_strategy",
    ]
    sdk_tools = ToolProfile.RESEARCH
    sdk_model = "sonnet"
    sdk_output_base = Path("data/sdk_sessions/seo_discovery")

    def _sdk_default_prompt(self) -> str:
        return (
            "You are the DevSkyy SEO & Discovery strategist for SkyyRose.\n\n"
            "Discovery landscape:\n"
            "- Google: 'luxury streetwear', 'Bay Area fashion brand', "
            "'limited edition jerseys'\n"
            "- Pinterest: visual search for outfit inspiration, mood boards\n"
            "- TikTok: #streetwearfashion, #luxurystreet, #bayareafashion\n"
            "- Instagram: explore page, hashtag discovery, reels\n\n"
            "Your role (COMPLEMENTS SDKSeoWriterAgent):\n"
            "- SDKSeoWriterAgent handles on-page: meta tags, schema.org, headings\n"
            "- YOU handle off-page: SERP landscape, content gaps, backlinks, "
            "multi-platform discovery strategy\n\n"
            "You analyze:\n"
            "- SERP features for target keywords (featured snippets, "
            "image packs, shopping results)\n"
            "- Content gaps: topics competitors rank for that SkyyRose doesn't\n"
            "- Backlink opportunities: fashion blogs, press, directories\n"
            "- Keyword clusters: group related terms into content pillars\n"
            "- Visual search optimization: image alt text, Pinterest SEO, "
            "product image discoverability\n"
            "- Platform-specific discovery: TikTok SEO, YouTube shorts, "
            "Pinterest rich pins\n\n"
            "Competitors to benchmark:\n"
            "- Fear of God, Rhude, Amiri (premium streetwear)\n"
            "- Off-White, BAPE (street luxury crossover)\n"
            "- Essentials, Stussy (accessible streetwear)\n\n"
            "Always use web search to verify current SERP state. "
            "Never assume rankings — check live results."
        )

    def _build_task_prompt(self, task: str, **kwargs: Any) -> str:
        """Enrich with keyword or platform context."""
        base = super()._build_task_prompt(task, **kwargs)
        keyword = kwargs.get("keyword")
        platform = kwargs.get("platform")
        if keyword:
            base += f"\n\nTarget keyword/topic: {keyword}\n"
        if platform:
            base += f"Discovery platform: {platform}\n"
        return base

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        """Execute with web research — no LLM fallback."""
        prompt = self._build_task_prompt(task, **kwargs)
        result = await self._sdk_execute(prompt, label="seo_discovery")

        if result.success:
            return {
                "success": True,
                "result": result.response,
                "agent": self.name,
                "execution_mode": "sdk",
                "metrics": result.metrics,
            }

        return {
            "success": False,
            "result": "",
            "agent": self.name,
            "error": result.error,
            "execution_mode": "failed",
        }


__all__ = [
    "SDKSEODiscoveryAgent",
]
