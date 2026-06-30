"""Canonical asset-hub resolver — the single authority for ALL SkyyRose imagery.

``assets/hub/manifest.json`` is the unified manifest superseding the scattered
5-tree product sprawl and two legacy per-collection SOT manifests.  Every surface
that consumes brand imagery — agents, dashboard, WordPress sync — resolves through
here once an asset is promoted to the hub.

Manifest entries are keyed as ``"<sku>-<face>"`` (e.g. ``"br-010-back"``),
``"scene-<slug>"``, ``"lockup-<slug>"``, or ``"logos-<stem>"``.  Only
``verdict == "verified"`` assets with a non-null ``path`` are servable; pending
and flagged entries are visible for queue inspection but never returned as live
paths.

Path values in the manifest are relative to ``assets/hub/`` (the hub root).
``verify_integrity()`` confirms every verified+pathed entry resolves to a real
file on disk.
"""

from __future__ import annotations

import functools
import json
from pathlib import Path

from skyyrose.core.paths import REPO_ROOT

# Hub root — all manifest ``path`` values are relative to this directory.
HUB_DIR: Path = REPO_ROOT / "assets" / "hub"
_MANIFEST_PATH: Path = HUB_DIR / "manifest.json"


@functools.lru_cache(maxsize=1)
def _manifest() -> dict[str, dict]:
    """Load and cache the hub manifest's ``assets`` dict.

    Returns the ``assets`` sub-dict (keyed by asset-id) so callers work
    directly with ``{asset_id: entry}`` without traversing the top-level
    metadata keys.  Call :func:`refresh` to drop the cache after a manifest
    rebuild.
    """
    data = json.loads(_MANIFEST_PATH.read_text())
    return data.get("assets", {})


def manifest() -> dict[str, dict]:
    """Return the cached hub assets dict (``{asset_id: entry}``)."""
    return _manifest()


def refresh() -> None:
    """Drop the cached manifest (call after ``build_hub.py`` regenerates it)."""
    _manifest.cache_clear()


def _validated_path(raw: str, asset_id: str) -> str:
    """Enforce the hub-relative contract — reject absolute paths / ``..`` escapes.

    Defense-in-depth mirroring ``sot_images._validated_path``: a consumer that
    ``open()``s or serves the returned path must never receive one that climbs
    out of ``assets/hub/``.
    """
    if raw.startswith("/") or ".." in Path(raw).parts:
        raise ValueError(f"manifest path escapes the hub assets tree for {asset_id!r}: {raw!r}")
    return raw


def resolve(sku: str, face: str = "front") -> str | None:
    """Return the hub-relative path of the VERIFIED asset for ``sku`` + ``face``.

    Returns ``None`` when the asset is unknown, pending, flagged, or carries a
    null path.  Never returns a non-servable entry.

    Args:
        sku:  Canonical SKU (e.g. ``"br-010"``).
        face: Asset face (``"front"`` default | ``"back"`` | …).

    Returns:
        Hub-relative path string (e.g.
        ``"collections/black-rose/products/br-010/back.jpg"``), or ``None``.
    """
    if not sku:
        return None
    asset_id = f"{sku}-{face}"
    entry = _manifest().get(asset_id)
    if entry is None:
        return None
    if entry.get("verdict") != "verified":
        return None
    raw = entry.get("path")
    if not raw:
        return None
    return _validated_path(raw, asset_id)


# Theme tree prefix for entries whose source already serves from WordPress.
_THEME_PREFIX = "wordpress-theme/skyyrose-flagship/"
# Where off-theme verified renders are staged by ``scripts/sync_hub_to_theme.py``.
_HUB_THEME_SUBDIR = "assets/images/products/hub"


def served_theme_path(sku: str, face: str = "front") -> str | None:
    """Theme-relative path a VERIFIED canonical ``<sku>-<face>`` serves from, or ``None``.

    This is the seam that lets the hub's verdict override the catalog-derived SOT
    (consumed by :mod:`skyyrose.core.sot_images`):

    - source already under the theme tree → that theme-relative path (serves as-is);
    - off-theme verified render (oai / gemini / pipeline) → the staged projection
      ``assets/images/products/hub/<sku>-<face><ext>`` (present once
      ``scripts/sync_hub_to_theme.py`` has staged it).

    Returns ``None`` for pending / flagged / unknown ids and for usage-variant ids
    (only the canonical front/back product face is a SOT role). The caller confirms
    the returned path exists under the theme before honoring it.
    """
    if not sku:
        return None
    entry = _manifest().get(f"{sku}-{face}")
    if entry is None or entry.get("verdict") != "verified":
        return None
    src = entry.get("source") or ""
    if src.startswith(_THEME_PREFIX):
        return src[len(_THEME_PREFIX) :]
    if not (entry.get("path") or src):
        return None
    # Off-theme render → the staged projection. ``scripts/sync_hub_to_theme.py`` always
    # transcodes to ``.webp`` (the theme's served format; PNG is .gitignore'd), so the
    # served extension is webp regardless of the original render's format.
    return f"{_HUB_THEME_SUBDIR}/{sku}-{face}.webp"


def by_usage(usage: str, scope: str | None = None) -> list[dict]:
    """All VERIFIED assets whose ``usage[]`` list contains ``usage``.

    Optionally filtered to a collection ``scope`` (e.g. ``"black-rose"``,
    ``"kids-capsule"``, ``"love-hurts"``, ``"signature"``, ``"site"``).

    Note: does NOT require a non-null ``path`` — hub metadata (e.g. logotypes
    with a null path) is still valid verified metadata.  Use :func:`resolve`
    when you need a servable file path.

    Args:
        usage: Usage tag to filter on (e.g. ``"product-card"``, ``"web-hero"``).
        scope: Optional collection scope string to narrow results.

    Returns:
        List of matching asset entry dicts (each includes ``"_id"`` injected
        for caller convenience).
    """
    result: list[dict] = []
    for asset_id, entry in _manifest().items():
        if entry.get("verdict") != "verified":
            continue
        if usage not in entry.get("usage", []):
            continue
        if scope is not None and entry.get("scope") != scope:
            continue
        result.append({**entry, "_id": asset_id})
    return result


def pending() -> list[dict]:
    """All entries with ``verdict == "pending"`` (the re-render / promotion queue).

    Returns:
        List of pending asset entry dicts, each with ``"_id"`` injected.
    """
    return [
        {**entry, "_id": asset_id}
        for asset_id, entry in _manifest().items()
        if entry.get("verdict") == "pending"
    ]


def verify_integrity() -> list[str]:
    """Audit every ``verdict == "verified"`` entry for path validity.

    A problem is recorded when:
    - ``path`` is ``null`` / absent (verified but unpromoted), OR
    - The file ``assets/hub/<path>`` does not exist on disk.

    Returns:
        List of human-readable problem strings.  Empty list means every
        verified entry has a real file on disk.
    """
    problems: list[str] = []
    for asset_id, entry in _manifest().items():
        if entry.get("verdict") != "verified":
            continue
        raw = entry.get("path")
        if not raw:
            problems.append(f"{asset_id}: verdict='verified' but path is null (unpromoted)")
            continue
        try:
            validated = _validated_path(raw, asset_id)
        except ValueError as exc:
            problems.append(f"{asset_id}: {exc}")
            continue
        full = HUB_DIR / validated
        if not full.exists():
            problems.append(f"{asset_id}: verified path does not exist on disk: {validated}")
    return problems


if __name__ == "__main__":
    assets = manifest()
    verified = [e for e in assets.values() if e.get("verdict") == "verified"]
    pend = pending()
    problems = verify_integrity()

    print(f"Hub manifest: {len(assets)} total entries")
    print(f"  verified : {len(verified)}")
    print(f"  pending  : {len(pend)}")
    print()
    if problems:
        print(f"verify_integrity(): {len(problems)} problem(s)")
        for p in problems:
            print(f"  {p}")
    else:
        print("verify_integrity(): OK — all verified paths exist on disk")
