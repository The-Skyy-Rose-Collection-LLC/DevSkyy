"""Per-collection and per-product fidelity configuration.

Every SKU's expected color palette, garment type, and validation thresholds
are defined here. The fidelity gate uses these to validate AI-generated images
against real product specs — rejecting anything that doesn't match.

Color palettes are extracted from real garment analysis (Gemini vision)
stored in ``skyyrose/assets/data/garment-analysis.json``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from config.collections import Collection


class FidelityLevel(StrEnum):
    """How strict the fidelity gate is for a product."""

    STRICT = "strict"  # Flagship / hero products — no tolerance
    STANDARD = "standard"  # Core catalog — normal tolerance
    RELAXED = "relaxed"  # Accessories / sets — more tolerance


@dataclass(frozen=True)
class CollectionFidelityConfig:
    """Fidelity gate configuration for a collection."""

    collection: Collection
    threshold: float  # 0-100, overall score must meet this
    silhouette_weight: float = 0.60  # IoU contribution to overall score
    color_weight: float = 0.40  # Color ΔE contribution to overall score
    min_silhouette_iou: float = 0.80  # Hard floor for silhouette match
    max_color_delta_e: float = 15.0  # Hard ceiling for color distance
    required_angles: tuple[str, ...] = ("front",)
    min_reference_resolution: int = 1024  # px, shortest edge
    brand_palette: tuple[str, ...] = ()  # Hex values for brand colors


# ── Per-collection configs ──────────────────────────────────────────────────


BLACK_ROSE_CONFIG = CollectionFidelityConfig(
    collection=Collection.BLACK_ROSE,
    threshold=85.0,
    min_silhouette_iou=0.82,
    max_color_delta_e=12.0,
    required_angles=("front", "back"),
    brand_palette=(
        "#000000",  # jet black (base)
        "#303331",  # dark charcoal heather
        "#FFFFFF",  # white trim/accents
        "#F8F8F8",  # cream white
        "#FF6600",  # vibrant orange (Giants variant)
        "#224D2D",  # forest green (Oakland variant)
        "#FCDD09",  # vibrant yellow (Oakland accent)
        "#800080",  # purple/pink branding
        "#CCAACC",  # mauve-pink SR monogram
        "#B76E79",  # rose gold (brand)
        "#00B1BF",  # bright cyan/aqua (hockey jersey — br-011 garment analysis)
        "#DC143C",  # crimson (brand)
    ),
)


LOVE_HURTS_CONFIG = CollectionFidelityConfig(
    collection=Collection.LOVE_HURTS,
    threshold=82.0,
    min_silhouette_iou=0.78,
    max_color_delta_e=14.0,
    required_angles=("front",),
    brand_palette=(
        "#000000",  # black base
        "#FFFFFF",  # white panels/stripes
        "#DC143C",  # crimson red
        "#FF4500",  # orange-red roses
        "#B76E79",  # rose gold (brand)
        "#8B0000",  # dark red
    ),
)


SIGNATURE_CONFIG = CollectionFidelityConfig(
    collection=Collection.SIGNATURE,
    threshold=80.0,
    min_silhouette_iou=0.75,
    max_color_delta_e=15.0,
    required_angles=("front",),
    brand_palette=(
        "#000000",  # black
        "#FFFFFF",  # white
        "#D4AF37",  # gold (brand)
        "#B76E79",  # rose gold (brand)
        "#98FB98",  # mint green
        "#E6E6FA",  # lavender
        "#C0C0C0",  # silver
        "#F5F5DC",  # beige/cream
    ),
)


_COLLECTION_CONFIGS: dict[Collection, CollectionFidelityConfig] = {
    Collection.BLACK_ROSE: BLACK_ROSE_CONFIG,
    Collection.LOVE_HURTS: LOVE_HURTS_CONFIG,
    Collection.SIGNATURE: SIGNATURE_CONFIG,
}


# ── Per-product expected color palettes ──────────────────────────────────────
# Hex values from garment-analysis.json (Gemini vision) + source photos.
# The fidelity gate checks generated images against these exact colors.

PRODUCT_COLOR_PALETTES: dict[str, tuple[str, ...]] = {
    # ── Black Rose ─────────────────────────────────────────────────────────
    "br-001": ("#000000", "#F8F8F8", "#FFFFFF", "#CCAACC"),  # Crewneck: black/cream/white/mauve
    "br-002": ("#303331", "#FFFFFF", "#706C6C"),  # Joggers: charcoal heather/white/grey
    "br-003": ("#000000", "#FFFFFF", "#FF6600"),  # Jersey black: black/white/orange trim
    "br-003-oakland": ("#224D2D", "#FCDD09", "#FFFFFF"),  # Oakland: green/yellow/white
    "br-003-giants": ("#000000", "#FF6600", "#FFFFFF"),  # Giants: black/orange/white
    "br-003-white": ("#F8F8F8", "#000000", "#FFFFFF"),  # White: cream/black/white
    "br-004": ("#000000", "#303331", "#FFFFFF"),  # Hoodie: black/charcoal/white embroidery
    "br-005": ("#303331", "#FFFFFF", "#CCAACC"),  # Hoodie Sig: charcoal/white/mauve-pink
    "br-006": ("#000000", "#1A1A1F", "#F5F5DC"),  # Sherpa: black satin/dark/sherpa lining
    "br-007": ("#000000", "#FFFFFF", "#4169E1"),  # Shorts: black mesh/white panels/blue clouds
    "br-008": (
        "#DC001C",
        "#FFFFFF",
        "#000000",
        "#B76E79",
    ),  # SF Football Jersey: red/white/black/rose gold
    # ── Black Rose Pre-Order Jerseys ───────────────────────────────────────
    "br-009": (
        "#FFFFFF",
        "#000000",
        "#C0C0C0",
        "#B76E79",
    ),  # LAST OAKLAND: white/black/silver/rose gold
    "br-010": (
        "#FFFFFF",
        "#000000",
        "#D4AF37",
        "#B76E79",
    ),  # THE BAY basketball tank: white/black/gold/rose gold
    "br-011": (
        "#0A0A0A",
        "#00B1BF",
        "#FFFFFF",
        "#008189",
    ),  # THE ROSE hockey jersey: black/cyan/white/teal
    # ── Love Hurts ─────────────────────────────────────────────────────────
    "lh-006": ("#1A1A1A", "#F8F8F8", "#800000"),  # The Fannie: dark/cream/burgundy
    "lh-002": ("#000000", "#FFFFFF", "#DC143C"),  # Joggers: black/white stripes/crimson
    "lh-003": ("#FFFFFF", "#FF4500", "#000000", "#DC143C"),  # Shorts: white mesh/orange/black/red
    "lh-004": (
        "#000000",
        "#FFFFFF",
        "#DC143C",
        "#B76E79",
    ),  # Varsity: black/white/crimson/rose gold
    "lh-005": (
        "#000000",
        "#DC143C",
        "#FFFFFF",
    ),  # Windbreaker: black/crimson/white (brand palette — no garment analysis yet)
    # ── Signature ──────────────────────────────────────────────────────────
    "sg-001": ("#000000", "#D4AF37", "#B76E79"),  # Bay Set: black/gold/rose gold
    "sg-002": ("#000000", "#D4AF37", "#FFFFFF"),  # Stay Golden: black/gold/white
    "sg-003": (
        "#4B247C",
        "#D1A03F",
        "#FFFFFF",
    ),  # Stay Golden Shorts: deep indigo/golden yellow/white (sublimation)
    "sg-004": ("#303331", "#D4AF37", "#B76E79"),  # Sig Hoodie: charcoal/gold/rose gold
    "sg-005": ("#FFFFFF", "#D4AF37", "#000000"),  # Stay Golden Classic: white/gold/black
    "sg-006": ("#98FB98", "#E6E6FA", "#FFFFFF"),  # Mint & Lavender: mint/lavender/white
    "sg-009": ("#000000", "#B76E79", "#C0C0C0"),  # Sherpa: black/rose gold/silver
    # sg-010 DELETED (purged Mar 11) — do not add back
    "sg-011": ("#FFFFFF", "#000000", "#B76E79"),  # Label Tee White: white/black/rose gold
    "sg-012": ("#DA70D6", "#000000", "#B76E79"),  # Label Tee Orchid: orchid/black/rose gold
    # ── Signature Accessories / New ────────────────────────────────────────
    "sg-007": (
        "#212C26",
        "#343434",
        "#CC2F2F",
        "#E0E0E0",
    ),  # Signature Beanie: dark green/charcoal/red/silver
    "sg-013": ("#8ADCD0", "#C9B6E1", "#5F5F5F"),  # Mint & Lavender Crewneck: mint/lavender/grey
    "sg-014": ("#A7DED5", "#B9A1E0", "#9A8AD9"),  # Mint & Lavender Sweatpants: mint/lavender/purple
    # ── Kids Capsule ───────────────────────────────────────────────────────
    "kids-001": ("#CC0000", "#000000", "#FFFFFF"),  # Kids Red Set: red/black/white
    "kids-002": ("#800080", "#000000", "#FFFFFF"),  # Kids Purple Set: purple/black/white
}


# ── Per-product garment types (for silhouette matching) ──────────────────────

PRODUCT_GARMENT_TYPES: dict[str, str] = {
    "br-001": "crewneck",
    "br-002": "joggers",
    "br-003": "baseball jersey",
    "br-003-oakland": "baseball jersey",
    "br-003-giants": "baseball jersey",
    "br-003-white": "baseball jersey",
    "br-004": "hoodie",
    "br-005": "hoodie",
    "br-006": "sherpa jacket",
    "br-007": "basketball shorts",
    "br-008": "football jersey",
    "br-009": "football jersey",
    "br-010": "basketball tank",
    "br-011": "hockey jersey",
    "lh-006": "fanny pack",
    "lh-002": "joggers",
    "lh-003": "basketball shorts",
    "lh-004": "varsity jacket",
    "lh-005": "windbreaker",
    "sg-001": "matching set",
    "sg-002": "t-shirt",
    "sg-003": "athletic shorts",
    "sg-004": "hoodie",
    "sg-005": "t-shirt",
    "sg-006": "hoodie",
    "sg-009": "sherpa jacket",
    "sg-011": "t-shirt",
    "sg-012": "t-shirt",
    "sg-007": "beanie",
    "sg-013": "crewneck",
    "sg-014": "sweatpants",
    "kids-001": "kids matching set",
    "kids-002": "kids matching set",
}


# ── Per-product fidelity level overrides ─────────────────────────────────────

PRODUCT_FIDELITY_LEVELS: dict[str, FidelityLevel] = {
    # Flagship / hero products — strictest validation
    "br-006": FidelityLevel.STRICT,  # Sherpa Jacket — hero product
    "br-004": FidelityLevel.STRICT,  # Hoodie — hero pre-order
    "br-005": FidelityLevel.STRICT,  # Hoodie Sig Ed — hero pre-order
    "lh-004": FidelityLevel.STRICT,  # Varsity Jacket — hero
    "sg-009": FidelityLevel.STRICT,  # Sherpa Jacket — hero
    # Accessories — more tolerance for shape
    "lh-006": FidelityLevel.RELAXED,  # The Fannie fanny pack — accessory, not wearable
    "sg-007": FidelityLevel.RELAXED,  # Signature Beanie — accessory, not wearable
    # Everything else is STANDARD (default)
}


# ── Public API ───────────────────────────────────────────────────────────────


def get_fidelity_config(collection: Collection) -> CollectionFidelityConfig:
    """Return the fidelity config for a collection.

    Raises:
        ValueError: If no config registered for the collection.
    """
    config = _COLLECTION_CONFIGS.get(collection)
    if config is None:
        raise ValueError(
            f"No fidelity config for collection {collection!r}. "
            f"Registered: {list(_COLLECTION_CONFIGS.keys())}"
        )
    return config


def get_fidelity_threshold(sku: str, collection: Collection) -> float:
    """Return the effective fidelity threshold for a SKU.

    Accounts for per-product fidelity level overrides:
    - STRICT: collection threshold + 5%
    - STANDARD: collection threshold (default)
    - RELAXED: collection threshold - 5%
    """
    config = get_fidelity_config(collection)
    level = PRODUCT_FIDELITY_LEVELS.get(sku, FidelityLevel.STANDARD)

    if level == FidelityLevel.STRICT:
        return min(config.threshold + 5.0, 100.0)
    elif level == FidelityLevel.RELAXED:
        return max(config.threshold - 5.0, 50.0)
    return config.threshold


def get_product_palette(sku: str) -> tuple[str, ...]:
    """Return the expected color palette for a SKU.

    Returns an empty tuple if no palette is registered (validation
    will skip color checks in that case).
    """
    return PRODUCT_COLOR_PALETTES.get(sku, ())


def get_garment_type(sku: str) -> str | None:
    """Return the garment type for a SKU, or None if unknown."""
    return PRODUCT_GARMENT_TYPES.get(sku)


__all__ = [
    "CollectionFidelityConfig",
    "FidelityLevel",
    "BLACK_ROSE_CONFIG",
    "LOVE_HURTS_CONFIG",
    "SIGNATURE_CONFIG",
    "PRODUCT_COLOR_PALETTES",
    "PRODUCT_GARMENT_TYPES",
    "PRODUCT_FIDELITY_LEVELS",
    "get_fidelity_config",
    "get_fidelity_threshold",
    "get_product_palette",
    "get_garment_type",
]
