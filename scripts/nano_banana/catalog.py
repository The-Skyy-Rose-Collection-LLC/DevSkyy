"""nano_banana catalog shim — delegates to skyyrose.core.catalog_loader.

Provides the legacy nano_banana API surface (load_catalog, load_products,
load_specs, get_material_spec, find_source_image) over the canonical CSV.
All data now flows from a single source: skyyrose-catalog.csv.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from skyyrose.core.catalog_loader import CATALOG_CSV as _CANONICAL_CSV
from skyyrose.core.catalog_loader import bool_col, read_catalog_rows

logger = logging.getLogger(__name__)

# Project root = two parents up from this file (scripts/nano_banana/ → scripts/ → root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Env-var overridable CSV path (matches skyyrose.elite_studio.catalog pattern)
CATALOG_CSV = Path(os.getenv("SKYYROSE_CATALOG_PATH") or _CANONICAL_CSV)

# Material / branding specs live in a separate JSON file (not the CSV)
SPECS_JSON = PROJECT_ROOT / "data" / "product-specs.json"


def load_catalog(path: Path | None = None) -> dict[str, dict[str, Any]]:
    """Load catalog as dict keyed by SKU.

    Maps canonical CSV columns to the nano_banana API contract:
        name, collection, is_preorder, output_slug, is_tech_flat,
        is_accessory, garment_type, source_override (optional)
    """
    rows = read_catalog_rows(path or CATALOG_CSV)
    catalog: dict[str, dict[str, Any]] = {}
    for row in rows:
        sku = row["sku"]
        entry: dict[str, Any] = {
            "name": row["name"],
            "collection": row["collection"],
            "is_preorder": bool_col(row, "is_preorder"),
            "output_slug": row.get("render_output_slug") or sku,
            "is_tech_flat": bool_col(row, "render_is_tech_flat"),
            "is_accessory": bool_col(row, "render_is_accessory"),
            "garment_type": (row.get("garment_type_lock") or "").strip(),
        }
        override = (row.get("render_source_override") or "").strip()
        if override:
            entry["source_override"] = override
        catalog[sku] = entry
    return catalog


def load_specs(path: Path | None = None) -> dict[str, Any]:
    """Load product-specs.json. Returns {} silently if the file is missing.

    If the JSON has a top-level "products" key, unwrap it so callers get a
    flat SKU-keyed dict (e.g. {"br-001": {...}, "lh-004": {...}}).
    """
    spec_path = path or SPECS_JSON
    try:
        with open(spec_path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Failed to load %s: %s", spec_path, exc)
        return {}

    # Unwrap nested {"products": {...}} structure if present
    if isinstance(data, dict) and "products" in data and isinstance(data["products"], dict):
        return data["products"]
    return data


def get_material_spec(sku: str, specs: dict[str, Any] | None = None) -> str:
    """Return a formatted material spec string for a SKU, or '' if not found.

    Format:
        Material: <fabric>
        Texture: <texture>
        Branding: <branding>
        [Patch: <patch>]
    """
    s = specs if specs is not None else load_specs()
    if not isinstance(s, dict):
        return ""
    entry = s.get(sku)
    if not entry or not isinstance(entry, dict):
        return ""

    lines: list[str] = []
    if entry.get("fabric"):
        lines.append(f"Material: {entry['fabric']}")
    if entry.get("texture"):
        lines.append(f"Texture: {entry['texture']}")
    if entry.get("branding"):
        lines.append(f"Branding: {entry['branding']}")
    if entry.get("patch"):
        lines.append(f"Patch: {entry['patch']}")

    return "\n".join(lines)


def find_source_image(
    sku: str,
    catalog_entry: dict[str, Any],
    products_dir: Path | None = None,
) -> Path | None:
    """Resolve the source techflat / product image for a SKU.

    Precedence:
      1. `source_override` in catalog_entry (absolute or relative to products_dir)
      2. Bundle directory `data/product-bundles/*/techflat-front.*` via manifest.json SKU match
      3. None (caller decides how to handle)
    """
    # 1. Explicit override
    override = catalog_entry.get("source_override")
    if override:
        override_path = Path(override)
        if not override_path.is_absolute() and products_dir is not None:
            override_path = products_dir / override_path
        if override_path.exists():
            return override_path

    # 2. Bundle manifest.json scan
    bundle = _bundle_dir_for_sku(sku)
    if bundle is not None:
        for ext in ("jpeg", "jpg", "webp", "png"):
            candidate = bundle / f"techflat-front.{ext}"
            if candidate.exists():
                return candidate

    return None


def _bundle_dir_for_sku(sku: str) -> Path | None:
    """Scan data/product-bundles/ for a bundle whose manifest.json has matching SKU."""
    bundles_root = PROJECT_ROOT / "data" / "product-bundles"
    if not bundles_root.is_dir():
        return None
    for d in bundles_root.iterdir():
        if not d.is_dir():
            continue
        manifest = d / "manifest.json"
        if not manifest.exists():
            continue
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("sku") == sku:
            return d
    return None


def load_products(
    catalog: dict[str, dict[str, Any]] | None = None,
    *,
    sku_filter: str | None = None,
    collection_filter: str | None = None,
    include_accessories: bool = True,
    include_preorders: bool = True,
) -> list[dict[str, Any]]:
    """Return filtered list of product dicts (each with 'sku' key + source_path).

    Args:
        catalog: Pre-loaded catalog dict. If None, loads from canonical CSV.
        sku_filter: If set, only include this single SKU.
        collection_filter: If set, only include products in this collection slug.
        include_accessories: Whether to include accessories (default True).
        include_preorders: Whether to include pre-order items (default True).
    """
    cat = catalog if catalog is not None else load_catalog()
    products: list[dict[str, Any]] = []
    for sku, entry in cat.items():
        if sku_filter is not None and sku != sku_filter:
            continue
        if collection_filter is not None and entry.get("collection") != collection_filter:
            continue
        if not include_accessories and entry.get("is_accessory"):
            continue
        if not include_preorders and entry.get("is_preorder"):
            continue
        product = dict(entry)
        product["sku"] = sku
        product["source_path"] = find_source_image(sku, entry)
        products.append(product)
    return products
