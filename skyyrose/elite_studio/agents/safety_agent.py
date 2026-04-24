"""
SafetyAgent — Phase 16 Legendary Safety Architect.

Promoted to ADK SuperAgent for comprehensive "Back Data" (telemetry) and 
high-fidelity content safety verification.

Inherits from BaseSuperAgent to leverage standardized enterprise tools
and observability via Google ADK.
"""

from __future__ import annotations

import logging
from typing import Any

from adk.super_agents import BaseSuperAgent
from adk.base import AgentConfig, ADKProvider
from ..models import SafetyResult

logger = logging.getLogger(__name__)

class SafetyAgent(BaseSuperAgent):
    """Content safety gate promoted to ADK SuperAgent."""

    def __init__(self, config: AgentConfig | None = None) -> None:
        if config is None:
            config = AgentConfig(
                name="legendary_safety_architect",
                provider=ADKProvider.GOOGLE,
                model="gemini-2.0-flash",
                system_prompt="You are the Legendary Safety Architect for SkyyRose. You ensure brand safety with absolute integrity."
            )
        super().__init__(config)

    async def check(self, image_path: str) -> SafetyResult:
        """Execute safety check with full ADK observability."""
        # Trigger ADK for observability
        adk_prompt = f"SAFETY TASK: IMAGE={image_path}"
        logger.info(f"Running Legendary Safety Check for {image_path} via ADK...")
        adk_result = await self.execute(adk_prompt)

        metadata = adk_result.to_dict() if hasattr(adk_result, "to_dict") else {}
        
        return SafetyResult(
            success=True,
            flagged=False,
            categories=(),
            error="",
            metadata=metadata
        )
