"""Product catalog loader — reads from data/product-catalog.csv.

Single source of truth for all product metadata. No hardcoded catalogs.
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PRODUCTS_DIR = (
    PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products"
)
SOURCE_DIR = PROJECT_ROOT / "skyyrose" / "assets" / "images" / "source-products"
CATALOG_CSV = PROJECT_ROOT / "data" / "product-catalog.csv"
SPECS_JSON = PROJECT_ROOT / "data" / "product-specs.json"


def load_catalog() -> dict[str, dict]:
    """Load product catalog from CSV. Returns dict keyed by SKU."""
    catalog: dict[str, dict] = {}
    with CATALOG_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if not sku:
                continue
            entry: dict = {
                "name": row["name"].strip(),
                "collection": row["collection_slug"].strip(),
                "is_preorder": row["is_preorder"].strip() == "1",
                "output_slug": row["render_output_slug"].strip() or sku,
                "is_tech_flat": row["render_is_tech_flat"].strip() == "1",
                "is_accessory": row["render_is_accessory"].strip() == "1",
            }
            if row["render_source_override"].strip():
                entry["source_override"] = row["render_source_override"].strip()
            if row["render_back_source_override"].strip():
                entry["back_source_override"] = row["render_back_source_override"].strip()
            if row["render_variant_of"].strip():
                entry["variant_of"] = row["render_variant_of"].strip()
            catalog[sku] = entry
    return catalog


def find_source_image(sku: str, catalog: dict[str, dict]) -> Path | None:
    """Find the best available source image for a SKU.

    Priority: source_map (authoritative) → CSV override → glob fallback.
    """
    from nano_banana.source_map import get_source_map

    # 1. Authoritative source map — single source of truth
    smap = get_source_map()
    if sku in smap:
        front = smap[sku].get("front")
        if front and front.exists():
            return front

    info = catalog.get(sku, {})

    # 2. Explicit CSV source override
    if "source_override" in info:
        path = PRODUCTS_DIR / info["source_override"]
        if path.exists():
            return path
        log.warning("source_override %s not found for %s", info["source_override"], sku)

    # 3. Glob fallback by output_slug
    slug = info.get("output_slug", sku)
    candidates = []
    for ext in (".webp", ".jpg", ".jpeg", ".png"):
        candidates.extend(PRODUCTS_DIR.glob(f"{slug}*{ext}"))

    # Filter out generated model shots
    source_candidates = [
        p
        for p in candidates
        if "-front-model" not in p.stem
        and "-back-model" not in p.stem
        and "-branding" not in p.stem
        and "-composite" not in p.stem
    ]

    if source_candidates:
        source_candidates.sort(key=lambda p: p.stat().st_size, reverse=True)
        return source_candidates[0]

    return None


def find_back_source(sku: str, catalog: dict[str, dict]) -> Path | None:
    """Find back-specific source image. Crops 2-panel techflats automatically."""
    import tempfile

    from nano_banana.source_map import get_source_map

    # 1. Authoritative source map
    smap = get_source_map()
    if sku in smap:
        back = smap[sku].get("back")
        if back and back.exists():
            return back

    # 2. CSV override fallback
    info = catalog.get(sku, {})
    back_override = info.get("back_source_override")
    if not back_override:
        return None

    back_path = PRODUCTS_DIR / back_override
    if not back_path.exists():
        back_path = SOURCE_DIR / back_override
    if not back_path.exists():
        log.warning("back_source_override %s not found for %s", back_override, sku)
        return None

    # Auto-crop right half of 2-panel techflats
    try:
        from PIL import Image

        img = Image.open(back_path)
        w, h = img.size
        if w > h * 1.1:
            right_half = img.crop((w // 2, 0, w, h))
            tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            right_half.save(tmp.name, format="JPEG", quality=95)
            tmp.close()
            return Path(tmp.name)
    except Exception as exc:
        log.warning("Could not crop back source %s: %s", back_override, exc)

    return back_path


def load_products(
    catalog: dict[str, dict],
    sku_filter: str | None = None,
    collection_filter: str | None = None,
) -> list[dict]:
    """Build product list with resolved source images.

    Args:
        catalog: Full catalog dict keyed by SKU.
        sku_filter: Process only this single SKU.
        collection_filter: Process only SKUs in this collection slug
            (e.g. "black-rose", "signature", "love-hurts", "kids-capsule").

    Returns list of dicts with sku, name, collection, source_image, etc.
    """
    products = []
    skus = [sku_filter] if sku_filter else sorted(catalog.keys())

    for sku in skus:
        if sku not in catalog:
            log.warning("SKU %s not in catalog", sku)
            continue
        info = catalog[sku]

        if collection_filter and info["collection"] != collection_filter:
            continue

        source = find_source_image(sku, catalog)
        products.append(
            {
                "sku": sku,
                "name": info["name"],
                "collection": info["collection"],
                "is_accessory": info["is_accessory"],
                "is_tech_flat": info["is_tech_flat"],
                "output_slug": info["output_slug"],
                "source_image": source,
            }
        )

    return products


def load_specs() -> dict[str, dict]:
    """Load product specs from the single source of truth (product-specs.json).

    Returns the 'products' dict keyed by SKU. Each entry has:
        name, collection, branding, fabric, texture, patch
    """
    if not SPECS_JSON.exists():
        return {}
    data = json.loads(SPECS_JSON.read_text())
    return data.get("products", {})


def get_material_spec(sku: str) -> str:
    """Get fabric + texture description for a SKU to inject into prompts.

    Loads from data/product-specs.json (single source of truth).
    Returns empty string if no specs for this SKU.
    """
    specs = load_specs()
    entry = specs.get(sku, {})
    if not entry:
        return ""

    parts = []
    if entry.get("fabric"):
        parts.append(f"Material: {entry['fabric']}")
    if entry.get("texture"):
        parts.append(f"Texture: {entry['texture']}")

    return " | ".join(parts) if parts else ""
