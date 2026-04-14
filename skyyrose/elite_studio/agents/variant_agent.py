"""
Variant Agent — Multi-Angle / Multi-Colorway Generation

Generates alternate product image variants (back_view, side_view, etc.)
by calling GeneratorAgent with modified prompts for each variant.
Partial success is allowed — each variant is attempted independently.
"""

from __future__ import annotations

from .generator_agent import GeneratorAgent
from ..models import VariantResult

# Prompt modifiers keyed by variant name
_VARIANT_PROMPT_MODIFIERS: dict[str, str] = {
    "back_view": (
        "View: BACK angle — show full back of garment, "
        "any back branding/logos, back neckline details, rear drape"
    ),
    "side_view": (
        "View: SIDE angle — 90-degree profile, "
        "side seams, side pocket details, silhouette from the side"
    ),
    "detail_shot": (
        "View: DETAIL close-up — tight macro shot of key branding element, "
        "stitching, logo patch, or texture detail"
    ),
    "flat_lay": (
        "View: FLAT LAY — garment laid flat on clean neutral surface, "
        "overhead 90-degree angle, no model, studio lighting"
    ),
    "lifestyle": (
        "View: LIFESTYLE shot — model in a contextual environment "
        "matching the collection aesthetic, movement and energy"
    ),
}


def _get_prompt_modifier(variant_name: str) -> str:
    """Return prompt modifier for a variant name, with a generic fallback."""
    return _VARIANT_PROMPT_MODIFIERS.get(
        variant_name,
        f"View: {variant_name.replace('_', ' ').upper()} angle",
    )


class VariantAgent:
    """Generates image variants using GeneratorAgent with modified prompts.

    Each variant is attempted independently. A failure in one variant
    does not stop the others (partial success is allowed).
    """

    def generate_variants(
        self,
        sku: str,
        base_image_path: str,
        spec: str,
        variants: list[str],
    ) -> list[VariantResult]:
        """Generate multiple product image variants.

        Args:
            sku: Product SKU (e.g., 'br-001')
            base_image_path: Path to the base generated image (unused in prompt
                but recorded for reference)
            spec: Base generation spec (will be modified per variant)
            variants: List of variant names (e.g., ['back_view', 'side_view'])

        Returns:
            List of VariantResult, one per requested variant.
            Each result is independent — partial success is allowed.
        """
        if not variants:
            return []

        results: list[VariantResult] = []
        for variant_name in variants:
            result = self._generate_one(sku, spec, variant_name)
            results.append(result)

        return results

    def _generate_one(self, sku: str, spec: str, variant_name: str) -> VariantResult:
        """Generate a single variant. Returns VariantResult(success=False) on error."""
        try:
            modifier = _get_prompt_modifier(variant_name)
            enriched_spec = f"{spec}\n\n{modifier}"

            agent = GeneratorAgent()
            gen_result = agent.generate(
                sku=sku,
                view=variant_name,
                generation_spec=enriched_spec,
            )

            if not gen_result.success:
                return VariantResult(
                    success=False,
                    variant_name=variant_name,
                    error=gen_result.error,
                )

            return VariantResult(
                success=True,
                variant_name=variant_name,
                output_path=gen_result.output_path,
            )

        except Exception as exc:
            return VariantResult(
                success=False,
                variant_name=variant_name,
                error=str(exc),
            )
