"""
PromptEnrichmentAgent — Phase 16 Legendary Prompt Architect.

Promoted to ADK SuperAgent for comprehensive "Back Data" (telemetry) and 
spec-primacy prompt enrichment.

Inherits from BaseSuperAgent to leverage standardized enterprise tools
and observability via Google ADK.
"""

from __future__ import annotations

import logging
from typing import Any

from adk.super_agents import BaseSuperAgent
from adk.base import AgentConfig, ADKProvider
from ..catalog import Catalog
from ..models import EnrichedPrompt

logger = logging.getLogger(__name__)

_SPEC_PRIMACY = (
    "SPEC IS AUTHORITATIVE: Use the reference photo for fabric texture and color ONLY. "
    "For garment type, silhouette, and branding placement, trust the REQUIRED BRANDING "
    "block below. If the reference photo and branding spec disagree on garment type, "
    "the spec is authoritative — ignore the reference photo's garment type."
)

_GHOST_MANNEQUIN_STYLE = (
    "PHOTOGRAPHY STYLE: Professional ghost-mannequin (invisible mannequin / hollow man) "
    "product photography. The garment appears worn by an invisible body — NO mannequin "
    "visible. Pure white background (#FFFFFF). Garment has natural 3D volume and drape. "
    "Neck-in view: interior collar/neckline visible through the neckline opening. "
    "Clean e-commerce product shot, studio lighting, photorealistic."
)

_FLAT_LAY_STYLE = (
    "PHOTOGRAPHY STYLE: Professional flat-lay product photography. Garment laid flat on "
    "pure white background, overhead 90-degree angle, studio lighting, no wrinkles, "
    "all details visible, photorealistic."
)


class PromptEnrichmentAgent(BaseSuperAgent):
    """Rule-based spec-primacy prompt enrichment promoted to ADK SuperAgent."""

    def __init__(self, config: AgentConfig | None = None) -> None:
        if config is None:
            config = AgentConfig(
                name="legendary_prompt_architect",
                provider=ADKProvider.GOOGLE,
                model="gemini-2.0-flash",
                system_prompt="You are the Legendary Prompt Architect for SkyyRose. You synthesize perfect technical instructions."
            )
        super().__init__(config)

    async def enrich(self, sku: str, vision_spec: str, style: str = "flat_lay") -> EnrichedPrompt:
        """Enrich generation spec with full ADK observability."""
        # Trigger ADK for observability
        adk_prompt = f"ENRICHMENT TASK: SKU={sku}, STYLE={style}, VISION_SPEC={vision_spec}"
        logger.info(f"Running Legendary Prompt Enrichment for {sku} via ADK...")
        adk_result = await self.execute(adk_prompt)

        try:
            cat = Catalog.load()
            product = cat.require(sku)
            name = product.name
            branding = product.branding_summary
            collection = product.collection
        except Exception as exc:
            return EnrichedPrompt(success=False, error=f"Catalog load failed: {exc}")

        style_block = _GHOST_MANNEQUIN_STYLE if style == "ghost_mannequin" else _FLAT_LAY_STYLE

        enriched = (
            f"{_SPEC_PRIMACY}\n\n"
            f"PRODUCT: {name} (SKU: {sku}, Collection: {collection})\n\n"
            f"REQUIRED BRANDING:\n{branding}\n\n"
            f"{style_block}\n\n"
            f"REFERENCE ANALYSIS (texture/color reference only):\n{vision_spec}"
        )

        additions = [
            "spec_primacy_clause",
            f"style:{style}",
            f"branding_spec_from_csv",
        ]

        return EnrichedPrompt(
            success=True,
            original_spec=vision_spec,
            enriched_spec=enriched,
            additions=tuple(additions),
        )
