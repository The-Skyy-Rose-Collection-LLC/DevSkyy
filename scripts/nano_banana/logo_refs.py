"""Logo reference images — maps collections and SKUs to logo files.

When generating, we send BOTH the techflat (garment reference) AND
the logo image (branding reference) to the model. Two-reference generation
dramatically improves logo accuracy.

The generation prompt explicitly labels each image:
  IMAGE 1: Full garment tech flat (overall shape, colors, construction)
  IMAGE 2: Logo/branding close-up (exact graphic to reproduce)
"""

from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OVERLAYS_DIR = PROJECT_ROOT / "assets" / "techflats" / "hero-overlays"
TECHFLATS_DIR = PROJECT_ROOT / "assets" / "techflats"


# ── Collection-level logo references ─────────────────────────────────────────
# Default logo for each collection — used when no SKU-specific logo exists.

COLLECTION_LOGOS = {
    "black-rose": OVERLAYS_DIR / "br-brand-script.png",
    "love-hurts": OVERLAYS_DIR / "lh-logo-combined.png",
    "signature": OVERLAYS_DIR / "sig-brand-skyy-rose-gold.png",
}

# ── SKU-specific logo overrides ──────────────────────────────────────────────
# Some products have unique graphics that differ from the collection logo.

SKU_LOGO_REFS = {
    # Black Rose jerseys — sport patches
    "br-008": OVERLAYS_DIR / "br-patch-nfl-football.png",
    "br-009": OVERLAYS_DIR / "br-patch-nfl-football.png",
    "br-010": OVERLAYS_DIR / "br-patch-nba-basketball.png",
    "br-011": OVERLAYS_DIR / "br-patch-hockey.png",
    "br-012": OVERLAYS_DIR / "br-patch-mlb-baseball.png",
    "br-014": OVERLAYS_DIR / "br-patch-mlb-baseball.png",
    "br-013": OVERLAYS_DIR / "br-patch-mlb-baseball.png",
    # Love Hurts — graffiti script logos
    "lh-004": TECHFLATS_DIR / "love-hurts" / "logo-love.jpeg",  # varsity has "Love Hurts" script
    # Signature — gold script
    "sg-011": TECHFLATS_DIR / "signature" / "brand-skyy-rose-collection-gold.jpeg",
    "sg-012": TECHFLATS_DIR / "signature" / "brand-skyy-rose-collection-gold.jpeg",
}


def get_logo_reference(sku: str, collection: str) -> Path | None:
    """Get the logo reference image for a product.

    Priority: SKU-specific override > collection default > None
    Returns the path if it exists, None otherwise.
    """
    # Check SKU-specific first
    if sku in SKU_LOGO_REFS:
        path = SKU_LOGO_REFS[sku]
        if path.exists():
            log.info("Logo ref for %s: %s (SKU-specific)", sku, path.name)
            return path
        log.warning("Logo ref missing for %s: %s", sku, path)

    # Fall back to collection default
    if collection in COLLECTION_LOGOS:
        path = COLLECTION_LOGOS[collection]
        if path.exists():
            log.info("Logo ref for %s: %s (collection default)", sku, path.name)
            return path
        log.warning("Collection logo missing for %s: %s", collection, path)

    return None


def find_flatlay_photo(sku: str, catalog: dict | None = None) -> Path | None:
    """Find a real flatlay/source photo for a product (not the techflat illustration).

    These are actual photographs of the garment laid flat — they show real fabric,
    real logos, real colors. Most valuable reference for generation accuracy.
    """
    products_dir = (
        PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products"
    )

    if not products_dir.exists():
        return None

    # Check catalog for explicit source image
    if catalog and sku in catalog:
        for key in ("front_model_image", "image"):
            img = catalog[sku].get(key, "")
            if img and "source" in img.lower():
                path = PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / img
                if path.exists():
                    return path

    # Search by naming convention: *-source.*, *-product.*, *-real.*
    slug = sku.replace("-", "*")
    for pattern in [f"*{slug}*source*", f"*{slug}*product*", f"*{slug}*real*"]:
        matches = list(products_dir.glob(pattern))
        if matches:
            return matches[0]

    return None


def get_all_references(
    sku: str,
    collection: str,
    source_path: Path,
    catalog: dict | None = None,
) -> list[tuple[str, Path]]:
    """Get all reference images for a generation call.

    Up to 3 references sent to the model:
      1. Garment tech flat (design illustration — shape, layout)
      2. Logo/branding close-up (exact graphic to reproduce)
      3. Real flatlay photo (actual fabric, colors, material — GROUND TRUTH)

    The real photo is the most authoritative reference — if it exists,
    the model should prioritize its colors and textures over the techflat.
    """
    refs = []
    ref_num = 1

    # Real flatlay photo FIRST (if available) — this is ground truth
    flatlay = find_flatlay_photo(sku, catalog)
    if flatlay:
        refs.append(
            (
                f"REFERENCE IMAGE {ref_num} — REAL PRODUCT PHOTO (GROUND TRUTH): "
                "This is an actual photograph of the real garment. "
                "The REAL fabric texture, REAL colors, and REAL logo appearance are shown here. "
                "This image is the ultimate authority — match its colors and material exactly.",
                flatlay,
            )
        )
        ref_num += 1

    # Tech flat (design illustration)
    if source_path and source_path.exists():
        refs.append(
            (
                f"REFERENCE IMAGE {ref_num} — GARMENT TECH FLAT: "
                "Design illustration showing overall shape, panel layout, and graphic placement. "
                "Use this for silhouette and construction details."
                + (" Defer to the REAL PHOTO for colors and textures." if flatlay else ""),
                source_path,
            )
        )
        ref_num += 1

    # Logo close-up
    logo = get_logo_reference(sku, collection)
    if logo:
        refs.append(
            (
                f"REFERENCE IMAGE {ref_num} — LOGO/BRANDING CLOSE-UP: "
                "This is the EXACT logo/graphic that appears on the garment. "
                "Reproduce it at the EXACT position and size shown in the tech flat. "
                "Do NOT resize, reposition, duplicate, or alter it in any way.",
                logo,
            )
        )

    log.info(
        "References for %s: %d images (%s)",
        sku,
        len(refs),
        ", ".join(
            "flatlay" if "GROUND TRUTH" in r[0] else "techflat" if "TECH FLAT" in r[0] else "logo"
            for r in refs
        ),
    )

    return refs
