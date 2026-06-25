"""Intelligent model router — picks the best generation model per product.

Routes based on garment features extracted by vision_describe.py:
- Has visible text/logos → GPT Image 1.5 (best text accuracy)
- Complex fabric (satin, sherpa, mesh, velvet) → Gemini 3 Pro (best material physics)
- Plain garments / volume → FLUX 2 Pro via fal.ai (best value)
- Logo refinement → FLUX Kontext Pro (reference-guided editing)
- Editorial/branding → Gemini 3 Pro (best scene composition)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from llm.model_ids import NANO_BANANA_PRO_MODEL, OPENAI_IMAGE_15_MODEL

log = logging.getLogger(__name__)

COST_TABLE = {
    "gemini-pro": 0.04,  # NB Pro (gemini-3-pro-image-preview) — 4K luxury tier
    "gemini-flash": 0.04,  # NB Pro everywhere as of 2026-05-06 (Option A — luxury default)
    "gpt-image": 0.08,
    "flux-pro": 0.075,  # observed actual cost from multi-SKU validator runs
    "flux-kontext": 0.04,
}

ENGINE_CAPABILITIES = {
    "gemini-pro": "Best fabric texture, material physics, scene composition. Supports 8 reference images, native 4K.",
    "gemini-flash": "Fast, good quality. Best for vision analysis and QA judging.",
    "gpt-image": "Best text/logo rendering (96%+ accuracy). Premium commercial aesthetics.",
    "flux-pro": "Highest raw photorealism at best cost. 98% quality at 26% of premium price.",
    "flux-kontext": "Reference-guided editing. Fix logos/text on existing renders without regenerating.",
}

COMPLEX_FABRICS = frozenset(
    {
        "satin",
        "sherpa",
        "velvet",
        "mesh",
        "silk",
        "leather",
        "quilted",
        "fleece",
        "terry",
        "french terry",
        "corduroy",
        "wool",
        "cashmere",
        "suede",
    }
)

TEXT_INDICATORS = frozenset(
    {
        "black is beautiful",
        "love hurts",
        "the bay",
        "oakland",
        "skyy rose",
        "skyyrose",
        "the skyrose collection",
        "wordmark",
        "script",
        "text",
        "lettering",
        "foil",
    }
)


@dataclass(frozen=True)
class RouteDecision:
    engine: str
    model_id: str
    reason: str
    estimated_cost: float
    priority: int


def _has_text_graphics(vision_desc: dict, sku: str) -> bool:
    """Check if product has significant text/logo that needs accurate rendering."""
    # Check vision description graphics
    for g in vision_desc.get("graphics", []):
        content = str(g.get("content", "")).lower()
        gtype = str(g.get("type", "")).lower()
        if any(ind in content for ind in TEXT_INDICATORS):
            return True
        if gtype in ("screen print", "tackle-twill", "foil"):
            return True

    # Check LOGO_TREATMENTS metadata
    from nano_banana.prompts import LOGO_TREATMENTS

    treatment = LOGO_TREATMENTS.get(sku, "").lower()
    return any(ind in treatment for ind in TEXT_INDICATORS)


def _has_complex_fabric(vision_desc: dict) -> bool:
    """Check if product has complex fabric that benefits from Gemini Pro."""
    fabric = str(vision_desc.get("fabric_appearance", "")).lower()
    return any(f in fabric for f in COMPLEX_FABRICS)


def route_product(
    product: dict,
    vision_desc: dict,
    view: str = "front",
) -> list[RouteDecision]:
    """Return ordered list of model choices for this product + view.

    First item is the primary choice, second is fallback.
    """
    sku = product.get("sku", "")
    is_accessory = product.get("is_accessory", False)
    has_text = _has_text_graphics(vision_desc, sku)
    has_complex = _has_complex_fabric(vision_desc)

    # Editorial/branding views — always Gemini Pro for scene composition
    if view == "branding":
        return [
            RouteDecision(
                "gemini-pro",
                NANO_BANANA_PRO_MODEL,
                "Editorial scene composition — Gemini Pro excels at cinematic environments",
                COST_TABLE["gemini-pro"],
                1,
            ),
            RouteDecision(
                "gpt-image",
                OPENAI_IMAGE_15_MODEL,
                "Fallback for editorial — strong commercial aesthetics",
                COST_TABLE["gpt-image"],
                2,
            ),
        ]

    # Text/logo-heavy products — GPT Image for text accuracy
    if has_text:
        return [
            RouteDecision(
                "gpt-image",
                OPENAI_IMAGE_15_MODEL,
                f"Text/logo product ({sku}) — GPT Image has 96%+ text accuracy",
                COST_TABLE["gpt-image"],
                1,
            ),
            RouteDecision(
                "gemini-pro",
                NANO_BANANA_PRO_MODEL,
                "Fallback — good text rendering with superior fabric physics",
                COST_TABLE["gemini-pro"],
                2,
            ),
        ]

    # Complex fabric — Gemini Pro for material physics
    if has_complex:
        fabric = vision_desc.get("fabric_appearance", "complex")
        return [
            RouteDecision(
                "gemini-pro",
                NANO_BANANA_PRO_MODEL,
                f"Complex fabric ({fabric}) — Gemini Pro best at material physics",
                COST_TABLE["gemini-pro"],
                1,
            ),
            RouteDecision(
                "flux-pro",
                "fal-ai/flux-pro/v1.1",
                "Fallback — high photorealism at lower cost",
                COST_TABLE["flux-pro"],
                2,
            ),
        ]

    # Accessories — FLUX for efficiency
    if is_accessory:
        return [
            RouteDecision(
                "flux-pro",
                "fal-ai/flux-pro/v1.1",
                "Accessory — FLUX Pro best value for simple items",
                COST_TABLE["flux-pro"],
                1,
            ),
            RouteDecision(
                "gemini-pro",
                NANO_BANANA_PRO_MODEL,
                "Fallback — premium quality",
                COST_TABLE["gemini-pro"],
                2,
            ),
        ]

    # Default — plain garments, standard cotton/fleece
    return [
        RouteDecision(
            "flux-pro",
            "fal-ai/flux-pro/v1.1",
            "Standard garment — FLUX Pro best value (98% quality, 26% cost)",
            COST_TABLE["flux-pro"],
            1,
        ),
        RouteDecision(
            "gemini-pro",
            NANO_BANANA_PRO_MODEL,
            "Fallback — premium quality for retries",
            COST_TABLE["gemini-pro"],
            2,
        ),
    ]


def estimate_batch_cost(
    products: list[dict],
    views: list[str],
    vision_descs: dict[str, dict] | None = None,
) -> dict:
    """Estimate total cost for a batch generation run."""
    total = 0.0
    breakdown = {}

    for product in products:
        sku = product.get("sku", "unknown")
        desc = (vision_descs or {}).get(sku, {})
        for view in views:
            decisions = route_product(product, desc, view)
            if decisions:
                cost = decisions[0].estimated_cost
                total += cost
                engine = decisions[0].engine
                breakdown[engine] = breakdown.get(engine, 0) + cost

    return {
        "total_usd": round(total, 2),
        "per_engine": {k: round(v, 2) for k, v in breakdown.items()},
        "image_count": len(products) * len(views),
    }
