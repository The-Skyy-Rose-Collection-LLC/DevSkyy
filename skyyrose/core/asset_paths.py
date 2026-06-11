"""Single authority for every on-disk asset location in DevSkyy.

Two canonical roots, by founder decision (2026-06-10):

* ``PRODUCT_ASSETS``  — ``assets/products/`` — ALL product source assets
  (techflats, reference photos, source photos). Pipeline inputs live here
  and nowhere else.
* ``THEME_ASSETS``    — ``wordpress-theme/skyyrose-flagship/assets/`` — ALL
  web-served assets. WordPress deploys this tree; nothing source-only
  belongs in it.

Every script resolves asset paths through this module. Hardcoding an asset
path anywhere else is a defect — fix the call site, not this module.
"""

from __future__ import annotations

from pathlib import Path


def _find_repo_root() -> Path:
    """Walk up from this file to the repo root (.git marker; worktree-safe)."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path(__file__).resolve().parents[2]


REPO_ROOT = _find_repo_root()

# ── Product source assets (pipeline inputs) ─────────────────────────────────
PRODUCT_ASSETS = REPO_ROOT / "assets" / "products"
PRODUCT_TECHFLATS = PRODUCT_ASSETS / "techflats"  # split/, hero-overlays/ …
PRODUCT_REFERENCES = PRODUCT_ASSETS / "references"  # merged product refs
PRODUCT_SOURCE_PHOTOS = PRODUCT_ASSETS / "source-photos"  # per-collection photos

# ── Theme (web-served, deployed to skyyrose.co) ─────────────────────────────
THEME_ROOT = REPO_ROOT / "wordpress-theme" / "skyyrose-flagship"
THEME_ASSETS = THEME_ROOT / "assets"
THEME_PRODUCT_IMAGES = THEME_ASSETS / "images" / "products"

# ── Theme data (catalog + canon, versioned with the theme) ──────────────────
THEME_DATA = THEME_ROOT / "data"
CATALOG_CSV = THEME_DATA / "skyyrose-catalog.csv"
DOSSIER_DIR = THEME_DATA / "dossiers"
BRAND_LOGOS = THEME_DATA / "brand-logos"
