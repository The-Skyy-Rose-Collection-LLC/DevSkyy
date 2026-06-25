"""
VariantAgent — Phase 16 Legendary Variant Architect.

Promoted to ADK SuperAgent for comprehensive "Back Data" (telemetry) and
high-fidelity dual-agent variant generation.

Inherits from BaseSuperAgent to leverage standardized enterprise tools
and observability via Google ADK.
"""

from __future__ import annotations

import logging

from adk.base import ADKProvider, AgentConfig
from adk.super_agents import BaseSuperAgent
from llm.model_ids import GEMINI_FLASH_2_MODEL

from ..models import VariantResult

logger = logging.getLogger(__name__)


class VariantAgent(BaseSuperAgent):
    """Dual-agent variant generator promoted to ADK SuperAgent."""

    def __init__(self, config: AgentConfig | None = None) -> None:
        if config is None:
            config = AgentConfig(
                name="legendary_variant_architect",
                provider=ADKProvider.GOOGLE,
                model=GEMINI_FLASH_2_MODEL,
                system_prompt="You are the Legendary Variant Architect for SkyyRose. You create diverse, hyper-accurate product variations.",
            )
        super().__init__(config)

    async def generate_variants(
        self,
        sku: str,
        base_image_path: str,
        variant_specs: list[str],
    ) -> list[VariantResult]:
        """Execute variant generation with full ADK observability."""
        # Trigger ADK for observability
        adk_prompt = f"VARIANT TASK: SKU={sku}, BASE={base_image_path}, VARIANTS={variant_specs}"
        logger.info(f"Running Legendary Variant Generation for {sku} via ADK...")
        adk_result = await self.execute(adk_prompt)

        # P1 #7: Pass-through stub. Phase B2 best-of-N logic not wired yet.
        # success=False so callers don't consume base image as a "variant".
        logger.warning(
            "VariantAgent.generate_variants is a stub: returning base image as only variant. "
            "Wire to Claude Sonnet + GPT-4o best-of-N before relying on output."
        )
        metadata = adk_result.to_dict() if hasattr(adk_result, "to_dict") else {}

        return [
            VariantResult(
                success=False,
                variant_name="default",
                output_path=base_image_path,
                metadata={**metadata, "stub": True, "reason": "variants_not_implemented"},
            )
        ]
