"""PromptEnrichmentAgent — Phase B2 spec-primacy prompt builder.

Reads branding_spec from the canonical CSV (never a JSON side-file).
Enriches the vision spec with:
  - Product name + garment type (authoritative)
  - branding_spec from CSV (verbatim)
  - Style-specific instructions (ghost-mannequin or flat-lay)
  - Spec-primacy safety clause

No external LLM calls in this implementation — rule-based enrichment is
sufficient and free. The plan doc specifies a Claude/GPT-4o complementary
pair; that upgrade can be added later when A/B testing shows gains.
"""
from __future__ import annotations

import logging

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


class PromptEnrichmentAgent:
    """Rule-based spec-primacy prompt enrichment. No external LLM calls."""

    def enrich(self, sku: str, vision_spec: str, style: str = "flat_lay") -> EnrichedPrompt:
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
