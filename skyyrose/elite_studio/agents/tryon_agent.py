"""
TryOnAgent — Phase 16 Legendary Try-On Architect.

Promoted to ADK SuperAgent for comprehensive "Back Data" (telemetry) and
high-fidelity virtual try-on.

Inherits from BaseSuperAgent to leverage standardized enterprise tools
and observability via Google ADK.
"""

from __future__ import annotations

import logging

from adk.base import ADKProvider, AgentConfig
from adk.super_agents import BaseSuperAgent
from llm.model_ids import GEMINI_FLASH_2_MODEL

from ..models import TryOnResult

logger = logging.getLogger(__name__)


class TryOnAgent(BaseSuperAgent):
    """Virtual try-on specialist promoted to ADK SuperAgent."""

    def __init__(self, config: AgentConfig | None = None) -> None:
        if config is None:
            config = AgentConfig(
                name="legendary_tryon_architect",
                provider=ADKProvider.GOOGLE,
                model=GEMINI_FLASH_2_MODEL,
                system_prompt="You are the Legendary Try-On Architect for SkyyRose. You create seamless digital wear experiences.",
            )
        super().__init__(config)

    async def execute_tryon(
        self,
        garment_image_path: str,
        model_image_path: str,
        category: str = "upper_body",
    ) -> TryOnResult:
        """Execute try-on with full ADK observability."""
        # Trigger ADK for observability
        adk_prompt = (
            f"TRY-ON TASK: GARMENT={garment_image_path}, MODEL={model_image_path}, CAT={category}"
        )
        logger.info(f"Running Legendary Try-On for {garment_image_path} via ADK...")
        adk_result = await self.execute(adk_prompt)

        metadata = adk_result.to_dict() if hasattr(adk_result, "to_dict") else {}

        # P1 #7: Pass-through stub. Real FASHN integration not wired yet.
        # Returning success=False prevents downstream code from treating the
        # input image as a transformed try-on result. Callers must check .success
        # before consuming output_path.
        logger.warning(
            "TryOnAgent.execute_tryon is a stub: returning input image unchanged. "
            "Wire to FASHN provider before relying on output."
        )
        return TryOnResult(
            success=False,
            output_path=garment_image_path,
            garment_sku="unknown",
            model_image_path=model_image_path,
            provider="fashn",
            latency_s=0.5,
            metadata={**metadata, "stub": True, "reason": "tryon_not_implemented"},
        )


# Aliases for backwards compatibility
TryonAgent = TryOnAgent


def _find_garment_image(sku: str) -> str:
    """Stub to unblock nodes.py imports."""
    return f"renders/output/{sku}/{sku}-model-front-gemini.jpg"
