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
    """Build ``sku -> product`` from every collection's ``sot.json`` (cached).

    The verified asset hub's overrides are baked into ``sot.json`` upstream by
    ``build-collection-sot.py`` (the single seam), so this resolver — and every
    surface it feeds (Python ``resolve_image``, the PHP theme via ``sot.json``, the
    dashboard via ``data/sot-images.json``) — honors the hub verdict uniformly
    without a parallel override here.
    """
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


def _validated_path(raw: str, sku: str) -> str:
    """Enforce the theme-relative contract — reject absolute paths / ``..`` escapes.

    The SOT is repo-tracked and generated, so this is defense-in-depth (matching
    ``paths.golden_path`` / ``paths.wp_product_path``): a consumer that ``open()``s
    or serves the returned path must never receive one that climbs out of the tree.
    """
    if raw.startswith("/") or ".." in Path(raw).parts:
        raise ValueError(f"sot.json image path escapes the assets tree for {sku!r}: {raw!r}")
    return raw


def _first_path(images: dict, keys: tuple[str, ...], sku: str) -> str | None:
    """First present, validated ``path`` among ``keys`` — the front-first fallback.

    Single authority for the fallback loop (used by both :func:`resolve_image` and
    :func:`build_manifest`).
    """
    for key in keys:
        entry = images.get(key)
        if isinstance(entry, dict) and entry.get("path"):
            return _validated_path(entry["path"], sku)
    return None


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
    return _first_path(prod.get("images", {}), _ROLE_KEYS.get(role, ()), sku)


def resolve_model_3d(sku: str) -> dict | None:
    """Return the approved 3D model entry for a SKU, or ``None``.

    Sibling to :func:`resolve_image`, reading the ``model_3d`` key that
    ``scripts/promote_model3d_sot.py`` bakes into ``sot.json`` for SKUs with an
    APPROVED ``Model3DReview`` — the same "hub verdict baked in upstream, resolver
    honors it uniformly" seam this module's own index already applies to 2D
    imagery. Returns ``None`` when the SKU is unknown or carries no ``model_3d``
    key (nothing approved yet) — never invents a value.

    Unlike :func:`resolve_image`'s theme-relative contract, the returned
    ``path`` is REPO_ROOT-relative: generated 3D models live under
    ``assets/3d-models-generated/`` (outside the WordPress theme tree), so
    ``skyyrose.core.paths.REPO_ROOT`` — not ``THEME_ROOT`` — is the tree a
    caller joins the path onto. The escape/absolute-path guard is identical
    either way (:func:`_validated_path` only checks the raw string, it is not
    tree-specific), so it is reused as-is.

    Args:
        sku: Canonical SKU (e.g. ``"br-011"``).

    Returns:
        ``{"path": str, "format": str, "task_id": str, "approved_at": str}``,
        or ``None``.
    """
    if not sku:
        return None
    prod = _index().get(sku)
    if not prod:
        return None
    entry = prod.get("model_3d")
    if not isinstance(entry, dict) or not entry.get("path"):
        return None
    return {**entry, "path": _validated_path(entry["path"], sku)}


def has_render(sku: str) -> bool:
    """True when the SOT has an actual on-model FRONT render (``front_model_image``).

    Distinct from ``resolve_image(sku, "front") is not None`` — that falls back to the
    flat ``image`` packshot so a card always shows *something*. ``has_render`` answers
    the narrower "is there a real render", so it must NOT honor the packshot fallback.
    """
    prod = _index().get(sku)
    if not prod:
        return False
    entry = prod.get("images", {}).get("front_model_image")
    return isinstance(entry, dict) and bool(entry.get("path"))


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
            path = _first_path(images, keys, sku)
            if path:
                entry[role] = path
        if entry:
            manifest[sku] = entry
    return manifest


# Default emit location: repo-root data/sot-images.json (a generated artifact
# both systems can read without cross-wiring the WP theme tree).
MANIFEST_PATH: Path = REPO_ROOT / "data" / "sot-images.json"


def serialize_manifest(manifest: dict | None = None) -> str:
    """Canonical serialized bytes of the SOT imagery manifest.

    The SINGLE byte-authority for ``data/sot-images.json``: both
    :func:`write_manifest` and the catalog validator's ``sot_images_current`` drift
    guard call this, so the committed file and the CI check can never disagree on
    formatting (the way two independent serializers would). Pass a pre-built
    ``manifest`` to avoid rebuilding it.
    """
    payload = {
        "_generated_by": "skyyrose.core.sot_images.write_manifest — DO NOT EDIT. "
        "Regenerate after build-collection-sot.py.",
        "_authority": "SOT product-imagery contract. Front-first fallback "
        "(on-model render before flat packshot).",
        "images": build_manifest() if manifest is None else manifest,
    }
    return json.dumps(payload, indent=2) + "\n"


def write_manifest(out_path: Path | None = None, manifest: dict | None = None) -> Path:
    """Write the manifest to ``out_path`` (default :data:`MANIFEST_PATH`).

    Pass an already-built ``manifest`` to avoid rebuilding it (e.g. when the caller
    also needs the count); otherwise it is built here.
    """
    out = out_path or MANIFEST_PATH
    # Never let a caller-supplied out_path write outside the repo.
    if out_path is not None and not str(out.resolve()).startswith(str(REPO_ROOT)):
        raise ValueError(f"write_manifest: out_path must be within the repo: {out_path}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(serialize_manifest(manifest))
    return out


if __name__ == "__main__":
    images = build_manifest()
    p = write_manifest(manifest=images)
    print(f"wrote {p} ({len(images)} skus)")
