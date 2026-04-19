"""
Prompt Enrichment Agent — Rule-Based Spec Enhancement

Enriches vision specs with brand/collection DNA and style modifiers.
No LLM call — pure deterministic rule application.
"""

from __future__ import annotations

from ..models import EnrichedPrompt

# ---------------------------------------------------------------------------
# Brand and collection DNA (sourced from compositor_agent.SCENE_LOOKBOOK)
# ---------------------------------------------------------------------------

_COLLECTION_DNA: dict[str, str] = {
    "black-rose": (
        "Oakland East Bay luxury streetwear, night ambiance, urban concrete aesthetic, "
        "gothic rose motifs, silver and dark palette, 'Luxury Grows from Concrete' ethos"
    ),
    "love-hurts": (
        "gothic cathedral rose chamber, enchanted Beauty and the Beast atmosphere, "
        "passionate crimson palette, dramatic editorial tension, beast's perspective"
    ),
    "signature": (
        "San Francisco Golden Gate Bridge golden hour, fog through cables, "
        "fashion runway energy, gold and rose-gold palette, Bay Area luxury"
    ),
    "kids-capsule": (
        "vibrant playful luxury, rose gold accent, joyful editorial energy, "
        "premium kids fashion, clean bright studio"
    ),
}

_SCENE_TO_COLLECTION: dict[str, str] = {
    "black-rose-rooftop-garden": "black-rose",
    "love-hurts-cathedral-rose-chamber": "love-hurts",
    "signature-golden-gate-showroom": "signature",
}

_SKU_PREFIX_TO_COLLECTION: dict[str, str] = {
    "br-": "black-rose",
    "lh-": "love-hurts",
    "sg-": "signature",
    "kids-": "kids-capsule",
}

# Style modifiers appended to every enriched spec
_STYLE_MODIFIERS: tuple[str, ...] = (
    "editorial lighting: soft directional high-fashion",
    "luxury brand aesthetic: premium materials, precise detailing",
    "model type: professional fashion editorial model, confident pose",
    "SkyyRose brand DNA: rose gold #B76E79 accent, dark #0A0A0A base",
    "output quality: 4K, high fidelity, no hallucinations",
)


def _resolve_collection(sku: str) -> str:
    """Derive collection name from SKU prefix."""
    sku_lower = sku.lower()
    for prefix, collection in _SKU_PREFIX_TO_COLLECTION.items():
        if sku_lower.startswith(prefix):
            return collection
    return ""


class PromptEnrichmentAgent:
    """Rule-based prompt enrichment for Elite Studio specs.

    Prepends collection DNA and appends style modifiers to the
    vision spec. No external API calls — deterministic and free.
    """

    def enrich(self, sku: str, vision_spec: str) -> EnrichedPrompt:
        """Enrich a vision spec with brand and collection context.

        Args:
            sku: Product SKU (e.g., 'br-001')
            vision_spec: Raw spec from VisionAgent

        Returns:
            EnrichedPrompt with enriched_spec and list of additions.
        """
        try:
            return self._enrich(sku, vision_spec)
        except Exception as exc:
            return EnrichedPrompt(
                success=False,
                original_spec=vision_spec,
                error=str(exc),
            )

    def _enrich(self, sku: str, vision_spec: str) -> EnrichedPrompt:
        collection = _resolve_collection(sku)
        additions: list[str] = []

        parts: list[str] = []

        # Prepend: SKU + collection identity
        sku_header = f"SKU: {sku}"
        parts.append(sku_header)
        additions.append(f"sku_header: {sku_header}")

        # Prepend: collection DNA block
        if collection:
            dna = _COLLECTION_DNA[collection]
            collection_block = f"Collection ({collection}): {dna}"
            parts.append(collection_block)
            additions.append(f"collection_dna: {collection}")

        # Core spec
        parts.append(vision_spec)

        # Append: style modifiers
        modifier_block = "Style modifiers: " + " | ".join(_STYLE_MODIFIERS)
        parts.append(modifier_block)
        for mod in _STYLE_MODIFIERS:
            additions.append(f"style_modifier: {mod}")

        enriched = "\n\n".join(parts)

        return EnrichedPrompt(
            success=True,
            original_spec=vision_spec,
            enriched_spec=enriched,
            additions=tuple(additions),
        )
