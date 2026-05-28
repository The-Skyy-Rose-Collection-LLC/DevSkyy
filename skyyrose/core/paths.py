"""Canonical filesystem paths for SkyyRose product data + imagery.

Single import surface for every directory and per-SKU file the pipeline
touches. Memory rots; the CSV doesn't. Code that hardcodes paths drifts;
this module gets one update and every consumer follows.

All paths derive from ``PROJECT_ROOT`` so absolute paths are stable
regardless of caller cwd. Importing this module is cheap — no I/O at
import time, just ``Path`` objects.

Canonical product-data sources (enforced by
``feedback_canonical_sources_only.md``)::

    CATALOG_CSV    wordpress-theme/.../data/skyyrose-catalog.csv
    DOSSIERS_DIR   wordpress-theme/.../data/dossiers/*.md

Canonical golden-image source (uploader writes here, pipeline reads here)::

    GOLDEN_DIR     skyyrose/elite_studio/assets/golden/{sku}/{angle}.jpg

Render OUTPUT target (NOT an input source)::

    WP_PRODUCTS_DIR  wordpress-theme/.../assets/images/products/

Do not add new paths to this module unless they share the same DNA:
project-canonical, shared by two or more modules, and stable across the
project's lifetime.
"""

from __future__ import annotations

from pathlib import Path

from skyyrose.core.catalog_loader import CATALOG_CSV, PROJECT_ROOT
from skyyrose.core.dossier_loader import DOSSIERS_DIR

# ─── Roots ─────────────────────────────────────────────────────────────
REPO_ROOT: Path = PROJECT_ROOT

# ─── WordPress theme tree ──────────────────────────────────────────────
THEME_ROOT: Path = CATALOG_CSV.parent.parent
WP_ASSETS_DIR: Path = THEME_ROOT / "assets"
WP_PRODUCTS_DIR: Path = WP_ASSETS_DIR / "images" / "products"
WP_LOGOS_DIR: Path = WP_ASSETS_DIR / "images" / "logos"

# ─── Elite Studio canonical inputs ─────────────────────────────────────
ELITE_STUDIO_ROOT: Path = REPO_ROOT / "skyyrose" / "elite_studio"
GOLDEN_DIR: Path = ELITE_STUDIO_ROOT / "assets" / "golden"

# ─── Uploader endpoint (write target for goldens) ──────────────────────
UPLOADER_URL: str = "http://127.0.0.1:8765"


def golden_path(sku: str, angle: str = "front", ext: str = "jpg") -> Path:
    """Return absolute path to a SKU's golden image.

    The uploader writes here exclusively. Production pipelines (rasterize
    Stage D, visual regression, vision-agent reference lookup) read here
    exclusively.

    Args:
        sku: Canonical SKU. Validated to reject path-traversal payloads.
        angle: ``'front'`` (default) | ``'back'`` | ``'reference'`` | ``'logo'``.
            The uploader currently writes only ``'front'``; other angles are
            reserved for future uploader endpoints.
        ext: File extension WITHOUT a leading dot. Defaults to ``'jpg'``
            since the uploader re-encodes to JPEG quality 95.

    Returns:
        Absolute :class:`~pathlib.Path`. Caller checks ``.exists()`` if
        existence matters.

    Raises:
        ValueError: SKU is empty or contains path-traversal characters.
    """
    if not sku or "/" in sku or ".." in sku or "\\" in sku:
        raise ValueError(f"invalid sku for golden_path: {sku!r}")
    return GOLDEN_DIR / sku / f"{angle}.{ext}"


def wp_product_path(filename: str) -> Path:
    """Return absolute path under the WordPress products image dir.

    Used for rendered outputs (composites, model shots) that ship to the
    live theme. NOT a source-of-truth lookup — source goldens live under
    :data:`GOLDEN_DIR`.

    Args:
        filename: Relative filename or subpath under :data:`WP_PRODUCTS_DIR`.

    Returns:
        Absolute :class:`~pathlib.Path`.

    Raises:
        ValueError: ``filename`` is absolute or contains ``..`` traversal.
    """
    if filename.startswith("/") or ".." in Path(filename).parts:
        raise ValueError(f"invalid filename for wp_product_path: {filename!r}")
    return WP_PRODUCTS_DIR / filename


__all__ = [
    "CATALOG_CSV",
    "DOSSIERS_DIR",
    "ELITE_STUDIO_ROOT",
    "GOLDEN_DIR",
    "PROJECT_ROOT",
    "REPO_ROOT",
    "THEME_ROOT",
    "UPLOADER_URL",
    "WP_ASSETS_DIR",
    "WP_LOGOS_DIR",
    "WP_PRODUCTS_DIR",
    "golden_path",
    "wp_product_path",
]
