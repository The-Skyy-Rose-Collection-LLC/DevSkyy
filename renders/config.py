"""Renders pipeline config — bundle resolver + product catalog list.

Delegates to skyyrose.core.catalog_loader for CSV reads. Exposes:
  PRODUCT_CATALOG   — list[dict], one entry per canonical SKU, includes
                      'existing_front' pointing at the resolved bundle
                      techflat-front path (or None).
  PRODUCTS_DIR      — absolute Path to wordpress-theme products image dir.
  _find_bundle_dir  — resolves a bundle directory by scanning manifest.json
                      files for a matching SKU (INFRA-02).
"""

from __future__ import annotations

import json
from pathlib import Path

from skyyrose.core.catalog_loader import CATALOG_CSV, read_catalog_rows

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PRODUCTS_DIR = (
    PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products"
)

_BUNDLES_DIR = PROJECT_ROOT / "data" / "product-bundles"


def _find_bundle_dir(sku: str) -> Path | None:
    """Find bundle dir by scanning manifest.json for matching SKU (INFRA-02).

    Scans every subdirectory of data/product-bundles/, reads manifest.json,
    and returns the directory whose manifest "sku" field matches the given sku.
    Returns None if no match is found or if the bundles directory does not exist.

    Note: directory names are NOT used for resolution — they don't map reliably
    to SKUs. Only the manifest.json "sku" field is authoritative.
    """
    if not _BUNDLES_DIR.is_dir():
        return None
    for d in _BUNDLES_DIR.iterdir():
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


def _resolve_existing_front(bundle: Path | None) -> str | None:
    """Return string path to techflat-front.* inside the bundle, or None."""
    if bundle is None:
        return None
    for ext in ("jpeg", "jpg", "webp", "png"):
        candidate = bundle / f"techflat-front.{ext}"
        if candidate.exists():
            return str(candidate)
    # Fallback: glob for any techflat-front.*
    for candidate in bundle.glob("techflat-front.*"):
        if candidate.is_file():
            return str(candidate)
    return None


def _build_product_catalog() -> list[dict[str, object]]:
    """Load canonical catalog rows + attach bundle resolution per SKU.

    Returns [] immediately if _BUNDLES_DIR does not exist, so the module
    can be imported in stripped CI environments or test environments that
    have not set up the bundles directory.
    """
    if not _BUNDLES_DIR.is_dir():
        return []
    rows = read_catalog_rows(CATALOG_CSV)
    products: list[dict[str, object]] = []
    for row in rows:
        product: dict[str, object] = dict(row)
        bundle = _find_bundle_dir(row.get("sku", ""))
        product["existing_front"] = _resolve_existing_front(bundle)
        products.append(product)
    return products


PRODUCT_CATALOG: list[dict[str, object]] = _build_product_catalog()
