"""Garment-aware knowledge & prompt construction.

TRELLIS generates better meshes when given context about the garment category
(tops drape differently from bottoms; hoodies need shoulder-seam geometry;
shoes need sole separation). This module encodes that knowledge.

It also classifies an uploaded image into a garment category using a tiny
visual heuristic (aspect ratio + simple color stats) — sufficient as a
defensive default when no metadata is provided. For higher accuracy plug in
``services/ml/visual_feature_extractor.py`` upstream.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class GarmentCategory(StrEnum):
    """Coarse garment categories supported by the pipeline."""

    TEE = "tee"
    HOODIE = "hoodie"
    SWEATSHIRT = "sweatshirt"
    JACKET = "jacket"
    DRESS = "dress"
    PANTS = "pants"
    SHORTS = "shorts"
    SKIRT = "skirt"
    SHOE = "shoe"
    HAT = "hat"
    BAG = "bag"
    ACCESSORY = "accessory"
    UNKNOWN = "unknown"


# =============================================================================
# Per-category geometry hints
# =============================================================================


@dataclass(frozen=True, slots=True)
class GarmentKnowledge:
    """Domain knowledge for a garment category.

    These hints are spliced into the TRELLIS text prompt to bias mesh
    generation toward category-appropriate topology.

    Attributes:
        category: The category this knowledge applies to.
        prompt_suffix: Text appended to the TRELLIS prompt for this category.
        polycount_hint: Recommended target polycount (mesh complexity).
        symmetry: ``"x"`` if the garment is mirror-symmetric across X axis.
        canonical_aspect: Expected ``height / width`` after isolation.
    """

    category: GarmentCategory
    prompt_suffix: str
    polycount_hint: int
    symmetry: str | None
    canonical_aspect: float


_KNOWLEDGE: dict[GarmentCategory, GarmentKnowledge] = {
    GarmentCategory.TEE: GarmentKnowledge(
        category=GarmentCategory.TEE,
        prompt_suffix=(
            "soft-knit t-shirt, short sleeves, ribbed crew neckline, "
            "natural fabric drape, clean shoulder seams, studio lighting"
        ),
        polycount_hint=60_000,
        symmetry="x",
        canonical_aspect=1.25,
    ),
    GarmentCategory.HOODIE: GarmentKnowledge(
        category=GarmentCategory.HOODIE,
        prompt_suffix=(
            "heavyweight cotton hoodie, raised hood with drawstrings, "
            "ribbed cuffs and hem, kangaroo pocket, soft fabric folds"
        ),
        polycount_hint=120_000,
        symmetry="x",
        canonical_aspect=1.35,
    ),
    GarmentCategory.SWEATSHIRT: GarmentKnowledge(
        category=GarmentCategory.SWEATSHIRT,
        prompt_suffix=(
            "crewneck sweatshirt, brushed fleece interior, ribbed cuffs and hem, "
            "soft drape, even shoulder seam"
        ),
        polycount_hint=90_000,
        symmetry="x",
        canonical_aspect=1.30,
    ),
    GarmentCategory.JACKET: GarmentKnowledge(
        category=GarmentCategory.JACKET,
        prompt_suffix=(
            "structured jacket, defined collar and lapels, full zipper or buttons, "
            "lining geometry, sleeve volume, hem stiffness"
        ),
        polycount_hint=140_000,
        symmetry="x",
        canonical_aspect=1.30,
    ),
    GarmentCategory.DRESS: GarmentKnowledge(
        category=GarmentCategory.DRESS,
        prompt_suffix=(
            "flowing dress silhouette, defined waistline, hemline drape, "
            "smooth bodice geometry, fabric folds along the skirt"
        ),
        polycount_hint=130_000,
        symmetry="x",
        canonical_aspect=1.85,
    ),
    GarmentCategory.PANTS: GarmentKnowledge(
        category=GarmentCategory.PANTS,
        prompt_suffix=(
            "tailored pants, defined waistband, two distinct leg tubes, "
            "inseam visible, hem cuff, no model body inside"
        ),
        polycount_hint=110_000,
        symmetry="x",
        canonical_aspect=1.70,
    ),
    GarmentCategory.SHORTS: GarmentKnowledge(
        category=GarmentCategory.SHORTS,
        prompt_suffix=(
            "casual shorts, distinct leg openings, elastic or button waistband, "
            "soft fabric drape"
        ),
        polycount_hint=70_000,
        symmetry="x",
        canonical_aspect=0.95,
    ),
    GarmentCategory.SKIRT: GarmentKnowledge(
        category=GarmentCategory.SKIRT,
        prompt_suffix=(
            "skirt with defined waistband, A-line or pleated silhouette, "
            "hemline drape, fabric movement"
        ),
        polycount_hint=80_000,
        symmetry="x",
        canonical_aspect=1.10,
    ),
    GarmentCategory.SHOE: GarmentKnowledge(
        category=GarmentCategory.SHOE,
        prompt_suffix=(
            "athletic sneaker, distinct sole and upper, laces, tongue, heel counter, "
            "midsole foam detail, clean rubber outsole"
        ),
        polycount_hint=100_000,
        symmetry=None,
        canonical_aspect=0.45,
    ),
    GarmentCategory.HAT: GarmentKnowledge(
        category=GarmentCategory.HAT,
        prompt_suffix=(
            "structured hat, defined crown and brim, sweatband visible inside, "
            "consistent radial geometry"
        ),
        polycount_hint=40_000,
        symmetry="x",
        canonical_aspect=0.55,
    ),
    GarmentCategory.BAG: GarmentKnowledge(
        category=GarmentCategory.BAG,
        prompt_suffix=(
            "handbag, defined body and straps, clean stitching lines, "
            "hardware detail, structural form"
        ),
        polycount_hint=80_000,
        symmetry=None,
        canonical_aspect=1.10,
    ),
    GarmentCategory.ACCESSORY: GarmentKnowledge(
        category=GarmentCategory.ACCESSORY,
        prompt_suffix="fashion accessory, clean form, no body parts visible",
        polycount_hint=50_000,
        symmetry=None,
        canonical_aspect=1.0,
    ),
    GarmentCategory.UNKNOWN: GarmentKnowledge(
        category=GarmentCategory.UNKNOWN,
        prompt_suffix="fashion garment, clean silhouette, studio lighting",
        polycount_hint=80_000,
        symmetry=None,
        canonical_aspect=1.0,
    ),
}


def knowledge_for(category: GarmentCategory) -> GarmentKnowledge:
    """Return :class:`GarmentKnowledge` for ``category`` (falls back to UNKNOWN)."""
    return _KNOWLEDGE.get(category, _KNOWLEDGE[GarmentCategory.UNKNOWN])


# =============================================================================
# Brand prompt context
# =============================================================================


@dataclass(frozen=True, slots=True)
class BrandPromptContext:
    """Brand styling hints — currently tuned for SkyyRose collections."""

    collection: str | None
    accent: str | None
    aesthetic: str | None


_COLLECTION_CONTEXT: dict[str, BrandPromptContext] = {
    "signature": BrandPromptContext(
        collection="signature",
        accent="rose gold trim",
        aesthetic="elevated luxury streetwear, refined silhouette",
    ),
    "black_rose": BrandPromptContext(
        collection="black_rose",
        accent="silver chrome accents",
        aesthetic="dark gothic streetwear, sharp angular details",
    ),
    "love_hurts": BrandPromptContext(
        collection="love_hurts",
        accent="crimson red trim",
        aesthetic="emotional luxury streetwear, expressive lines",
    ),
    "kids_capsule": BrandPromptContext(
        collection="kids_capsule",
        accent="soft rose gold",
        aesthetic="playful luxury kids streetwear, rounded comfortable shapes",
    ),
}


def brand_context(collection: str | None) -> BrandPromptContext | None:
    """Resolve a brand collection slug into context hints."""
    if not collection:
        return None
    return _COLLECTION_CONTEXT.get(collection.lower().replace("-", "_"))


# =============================================================================
# Prompt construction
# =============================================================================


def build_clothing_prompt(
    *,
    product_name: str | None,
    category: GarmentCategory,
    collection: str | None = None,
    user_prompt: str | None = None,
    extra_keywords: list[str] | None = None,
) -> str:
    """Compose a TRELLIS-ready clothing prompt from structured inputs.

    Args:
        product_name: Display name of the SKU, e.g. "Black Rose Hoodie".
        category: Garment category — drives geometry hints.
        collection: SkyyRose collection slug ("signature", "black_rose", ...).
        user_prompt: Free-form user description, treated as the highest priority.
        extra_keywords: Additional descriptors merged into the prompt.

    Returns:
        A single newline-joined prompt string optimized for TRELLIS text-to-3D.
        Order: product → user description → category geometry → brand aesthetic
        → technical render hints.
    """
    parts: list[str] = []

    if product_name:
        parts.append(product_name.strip())

    if user_prompt:
        parts.append(user_prompt.strip())

    knowledge = knowledge_for(category)
    parts.append(knowledge.prompt_suffix)

    brand = brand_context(collection)
    if brand:
        if brand.accent:
            parts.append(brand.accent)
        if brand.aesthetic:
            parts.append(brand.aesthetic)

    if extra_keywords:
        parts.extend(k.strip() for k in extra_keywords if k.strip())

    # Universal render hints
    parts.append("photorealistic, evenly lit studio render, neutral background")

    # Deduplicate while preserving order
    seen: set[str] = set()
    uniq: list[str] = []
    for p in parts:
        key = p.lower()
        if key and key not in seen:
            uniq.append(p)
            seen.add(key)

    return ", ".join(uniq)


# =============================================================================
# Classification (lightweight default)
# =============================================================================


def classify_garment(
    *,
    image_path: str | None = None,
    image_size: tuple[int, int] | None = None,
    declared_category: str | None = None,
    product_name: str | None = None,
) -> GarmentCategory:
    """Best-effort garment classification.

    Prefers explicit signals in order:

    1. ``declared_category`` argument (highest trust).
    2. Substring match in ``product_name``.
    3. Aspect-ratio heuristic over ``image_size``.

    Returns :attr:`GarmentCategory.UNKNOWN` when no signal is available — the
    pipeline will still run with neutral geometry hints.

    Args:
        image_path: Optional path; only used for size detection if ``image_size``
            is not provided and PIL is available.
        image_size: ``(width, height)`` of the input — preferred over reading
            the file (cheaper).
        declared_category: Explicit category string from the caller / catalog.
        product_name: Display name; scanned for category keywords.
    """
    if declared_category:
        try:
            return GarmentCategory(declared_category.lower().strip())
        except ValueError:
            pass

    name_hit = _classify_by_name(product_name)
    if name_hit is not GarmentCategory.UNKNOWN:
        return name_hit

    size = image_size or _safe_image_size(image_path)
    if size:
        return _classify_by_aspect(size)

    return GarmentCategory.UNKNOWN


_NAME_KEYWORDS: dict[GarmentCategory, tuple[str, ...]] = {
    GarmentCategory.TEE: ("tee", "t-shirt", "tshirt"),
    GarmentCategory.HOODIE: ("hoodie", "hood"),
    GarmentCategory.SWEATSHIRT: ("sweatshirt", "crewneck"),
    GarmentCategory.JACKET: ("jacket", "blazer", "coat", "outerwear"),
    GarmentCategory.DRESS: ("dress", "gown"),
    GarmentCategory.PANTS: ("pants", "trouser", "jeans", "denim"),
    GarmentCategory.SHORTS: ("short",),
    GarmentCategory.SKIRT: ("skirt",),
    GarmentCategory.SHOE: ("shoe", "sneaker", "boot", "heel"),
    GarmentCategory.HAT: ("hat", "cap", "beanie"),
    GarmentCategory.BAG: ("bag", "tote", "purse", "backpack"),
    GarmentCategory.ACCESSORY: ("scarf", "belt", "glove"),
}


def _classify_by_name(product_name: str | None) -> GarmentCategory:
    if not product_name:
        return GarmentCategory.UNKNOWN
    lowered = product_name.lower()
    for category, keywords in _NAME_KEYWORDS.items():
        if any(k in lowered for k in keywords):
            return category
    return GarmentCategory.UNKNOWN


def _classify_by_aspect(size: tuple[int, int]) -> GarmentCategory:
    width, height = size
    if width <= 0 or height <= 0:
        return GarmentCategory.UNKNOWN

    aspect = height / width
    if aspect >= 1.65:
        return GarmentCategory.DRESS
    if aspect >= 1.40:
        return GarmentCategory.PANTS
    if aspect >= 1.15:
        return GarmentCategory.TEE
    if aspect >= 0.85:
        return GarmentCategory.SHORTS
    if aspect >= 0.50:
        return GarmentCategory.HAT
    return GarmentCategory.SHOE


def _safe_image_size(image_path: str | None) -> tuple[int, int] | None:
    if not image_path or not Path(image_path).exists():
        return None
    try:
        from PIL import Image

        with Image.open(image_path) as im:
            return im.size
    except Exception:  # noqa: BLE001 — defensive default
        return None


# =============================================================================
# Convenience aggregate
# =============================================================================


@dataclass(frozen=True, slots=True)
class GarmentPrompt:
    """Bundle of (category, prompt, knowledge) used downstream."""

    category: GarmentCategory
    prompt: str
    knowledge: GarmentKnowledge
    extra: dict[str, str] = field(default_factory=dict)


def build_garment_prompt_bundle(
    *,
    image_path: str | None = None,
    image_size: tuple[int, int] | None = None,
    product_name: str | None = None,
    declared_category: str | None = None,
    collection: str | None = None,
    user_prompt: str | None = None,
    extra_keywords: list[str] | None = None,
) -> GarmentPrompt:
    """Classify + build prompt + attach knowledge in one call."""
    category = classify_garment(
        image_path=image_path,
        image_size=image_size,
        declared_category=declared_category,
        product_name=product_name,
    )
    prompt = build_clothing_prompt(
        product_name=product_name,
        category=category,
        collection=collection,
        user_prompt=user_prompt,
        extra_keywords=extra_keywords,
    )
    return GarmentPrompt(
        category=category,
        prompt=prompt,
        knowledge=knowledge_for(category),
        extra={
            "collection": collection or "",
            "product_name": product_name or "",
        },
    )


__all__ = [
    "GarmentCategory",
    "GarmentKnowledge",
    "BrandPromptContext",
    "GarmentPrompt",
    "knowledge_for",
    "brand_context",
    "build_clothing_prompt",
    "build_garment_prompt_bundle",
    "classify_garment",
]
