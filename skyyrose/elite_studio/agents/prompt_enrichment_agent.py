"""Rule-based prompt enrichment for SkyyRose Elite Studio imagery pipeline."""

from __future__ import annotations

import logging

from skyyrose.elite_studio.models import EnrichedPrompt

logger = logging.getLogger(__name__)

_COLLECTION_DNA: dict[str, str] = {
    "br": (
        "black-rose collection | Oakland street luxury aesthetic | "
        "Luxury Grows from Concrete | concrete textures | urban night atmosphere"
    ),
    "lh": (
        "love-hurts collection | gothic cathedral atmosphere | enchanted rose dome | "
        "passionate romantic darkness | Beauty and the Beast perspective"
    ),
    "sg": (
        "signature collection | Golden Gate Bridge San Francisco | "
        "golden hour runway fashion | Bay Area refined luxury | fog through cables"
    ),
    "kids": (
        "kids-capsule collection | playful vibrant energy | bright optimistic palette | "
        "youthful luxury streetwear"
    ),
}

_STYLE_MODIFIERS = (
    "editorial lighting",
    "luxury brand aesthetic",
    "SkyyRose brand DNA",
)


class PromptEnrichmentAgent:
    """Enrich a vision spec with collection DNA and global style modifiers."""

    def enrich(self, sku: str, vision_spec: str, style: str = "flat_lay") -> EnrichedPrompt:
        """Return an enriched prompt or a failure result if internal logic raises."""
        try:
            return self._enrich(sku, vision_spec, style)
        except Exception as exc:  # noqa: BLE001
            logger.exception("PromptEnrichmentAgent._enrich failed for sku=%s", sku)
            return EnrichedPrompt(success=False, original_spec=vision_spec, error=str(exc))

    def _enrich(self, sku: str, vision_spec: str, style: str) -> EnrichedPrompt:
        prefix = sku.split("-")[0].lower()
        additions: list[str] = []

        dna = _COLLECTION_DNA.get(prefix)
        if dna:
            additions.append(f"collection_dna:{dna}")

        for modifier in _STYLE_MODIFIERS:
            additions.append(f"style_modifier:{modifier}")

        parts = [f"[SKU: {sku}]"]
        if vision_spec:
            parts.append(vision_spec)
        if dna:
            parts.append(dna)
        for modifier in _STYLE_MODIFIERS:
            parts.append(modifier)

        enriched = " | ".join(parts)

        return EnrichedPrompt(
            success=True,
            original_spec=vision_spec,
            enriched_spec=enriched,
            additions=tuple(additions),
        )
