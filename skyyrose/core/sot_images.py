"""Canonical SOT product-imagery resolver — the single authority for
"what image represents this SKU".

Every surface that shows a product image — pipelines, MCP tools, subagents, the
WordPress theme, and the dashboard (via the generated ``data/sot-images.json``
manifest) — resolves product imagery through here, never through ad-hoc paths.
Hardcoding ``assets/images/products/<sku>...`` anywhere else is a drift bug
(``tests/test_sot_no_adhoc_imagery.py`` guards against it).

Source of truth = the per-collection SOT view
``wordpress-theme/skyyrose-flagship/data/collections/<slug>/sot.json`` (itself
generated from ``identity.json`` + the catalog CSV + ``visual-manifest.json`` by
``data/build-collection-sot.py`` — do not hand-edit it).

The front-first fallback chain mirrors the WordPress theme's
``template-parts/product-card-holo.php`` rule exactly: the on-model render
(``front_model_image``) is shown first; the flat studio packshot (``image``) is
the last resort, never the default. This is the rule the dead prototype bundler
violated (it bound cards to the flat ``image``), producing the flatlay/wrong-item
previews this module exists to prevent.
"""

from __future__ import annotations

import functools
import json
from pathlib import Path
from typing import Literal

# Anchor on the canonical path registry (skyyrose.core.paths) — never recompute
# repo/theme roots locally (paths.py is the single place that answers "where").
from skyyrose.core.paths import REPO_ROOT, THEME_ROOT

COLLECTIONS_DIR: Path = THEME_ROOT / "data" / "collections"

Role = Literal["front", "back", "packshot"]

# role -> ordered SOT image keys. On-model render first, flat packshot last —
# the same precedence product-card-holo.php applies. Order matters.
_ROLE_KEYS: dict[str, tuple[str, ...]] = {
    "front": ("front_model_image", "image"),
    "back": ("back_model_image", "back_image"),
    "packshot": ("image",),
}


@functools.lru_cache(maxsize=1)
def _index() -> dict[str, dict]:
    """Build ``sku -> product`` from every collection's ``sot.json`` (cached)."""
    idx: dict[str, dict] = {}
    # Enumerate collections from the filesystem so a newly-added collection is
    # picked up automatically — never a hardcoded slug list that silently omits it.
    for sot_path in sorted(COLLECTIONS_DIR.glob("*/sot.json")):
        slug = sot_path.parent.name
        sot = json.loads(sot_path.read_text())
        for prod in sot.get("products", []):
            sku = prod.get("sku")
            if sku:
                idx[sku] = {**prod, "collection": slug}
    return idx


def refresh() -> None:
    """Drop the cached index (call after regenerating ``sot.json``)."""
    _index.cache_clear()


def all_skus() -> list[str]:
    """Every SKU present in the SOT, sorted."""
    return sorted(_index())


def resolve_image(sku: str, role: Role = "front") -> str | None:
    """Return the theme-relative path (``assets/images/products/...``) for a SKU's
    image in ``role``, applying the front-first fallback chain.

    Returns ``None`` when the SKU is unknown or the SOT carries no image for the
    role — callers fall back to their own placeholder. Never invents a path.

    Args:
        sku: Canonical SKU (e.g. ``"br-004"``).
        role: ``"front"`` (on-model, default) | ``"back"`` | ``"packshot"`` (flat).
    """
    if not sku:
        return None
    prod = _index().get(sku)
    if not prod:
        return None
    images = prod.get("images", {})
    for key in _ROLE_KEYS.get(role, ()):
        entry = images.get(key)
        if isinstance(entry, dict) and entry.get("path"):
            return entry["path"]
    return None


def has_render(sku: str) -> bool:
    """True when the SOT has at least a front image for this SKU."""
    return resolve_image(sku, "front") is not None


def build_manifest() -> dict[str, dict[str, str]]:
    """Flat ``{sku: {front, back?, packshot?}}`` map of theme-relative paths.

    The serialized form (``data/sot-images.json``) is the SOT imagery contract for
    non-Python surfaces (the Next.js dashboard, any JS/PHP consumer). Generated —
    regenerate via :func:`write_manifest`; never hand-edit.
    """
    # Single pass over the cached index, reusing the same _ROLE_KEYS fallback
    # chain resolve_image() applies (one authority for the front-first rule).
    manifest: dict[str, dict[str, str]] = {}
    for sku, prod in sorted(_index().items()):
        images = prod.get("images", {})
        entry: dict[str, str] = {}
        for role, keys in _ROLE_KEYS.items():
            for key in keys:
                e = images.get(key)
                if isinstance(e, dict) and e.get("path"):
                    entry[role] = e["path"]
                    break
        if entry:
            manifest[sku] = entry
    return manifest


# Default emit location: repo-root data/sot-images.json (a generated artifact
# both systems can read without cross-wiring the WP theme tree).
MANIFEST_PATH: Path = REPO_ROOT / "data" / "sot-images.json"


def write_manifest(out_path: Path | None = None, manifest: dict | None = None) -> Path:
    """Write the manifest to ``out_path`` (default :data:`MANIFEST_PATH`).

    Pass an already-built ``manifest`` to avoid rebuilding it (e.g. when the caller
    also needs the count); otherwise it is built here.
    """
    out = out_path or MANIFEST_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "_generated_by": "skyyrose.core.sot_images.write_manifest — DO NOT EDIT. "
        "Regenerate after build-collection-sot.py.",
        "_authority": "SOT product-imagery contract. Front-first fallback "
        "(on-model render before flat packshot).",
        "images": build_manifest() if manifest is None else manifest,
    }
    out.write_text(json.dumps(payload, indent=2) + "\n")
    return out


if __name__ == "__main__":
    images = build_manifest()
    p = write_manifest(manifest=images)
    print(f"wrote {p} ({len(images)} skus)")
