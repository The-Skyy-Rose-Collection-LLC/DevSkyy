"""Scaffold per-SKU asset bundles under skyyrose/elite_studio/assets/golden/.

For every catalog SKU, ensures the per-SKU folder contains a structured
bundle of inputs the render pipeline can consume directly:

    golden/{sku}/
    ├── front.jpg                ← uploader-written (UNCHANGED — do not touch)
    ├── back.jpg                 ← optional uploads (existing)
    ├── reference.jpg            ← optional visual-regression baseline
    ├── flatlays/                ← empty stub — drop flat-laid photos here
    ├── techflat/
    │   ├── front.<ext>          → symlink to product-references techflat
    │   └── back.<ext>           → symlink to real-back photo (until true back-techflat exists)
    ├── logos/
    │   └── <filename>           → symlinks to applied logos for this SKU
    └── placement.md             ← generated brief (NOT canonical — re-derive any time)

All asset files are SYMLINKS into the canonical sources
(``data/product-references/``, ``assets/images/logos/``) so editing the
source updates every per-SKU bundle in lockstep. ``placement.md`` is a
generated derivative of CSV + dossier + logo-registry — re-running the
scaffolder regenerates it from current canon.

Idempotent: re-running with no canon changes produces zero diffs. Existing
symlinks are replaced atomically; orphan symlinks (pointing at files that
no longer exist) are pruned.

Usage:
    .venv/bin/python scripts/scaffold_sku_asset_folders.py
    .venv/bin/python scripts/scaffold_sku_asset_folders.py --sku br-007
    .venv/bin/python scripts/scaffold_sku_asset_folders.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

# Bootstrap project root for standalone-script imports.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skyyrose.core.catalog_loader import read_catalog_rows  # noqa: E402
from skyyrose.core.dossier_loader import get_product_with_dossier  # noqa: E402
from skyyrose.core.paths import (  # noqa: E402
    GOLDEN_DIR,
    THEME_ROOT,
    WP_LOGOS_DIR,
    WP_PRODUCTS_DIR,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

PRODUCT_REFERENCES_DIR = THEME_ROOT / "data" / "product-references"
LOGO_REGISTRY_JSON = THEME_ROOT / "data" / "logo-registry.json"

SUBDIRS = ("flatlays", "techflat", "logos")


@dataclass
class ScaffoldResult:
    sku: str
    created_dirs: int = 0
    created_symlinks: int = 0
    pruned_symlinks: int = 0
    wrote_placement: bool = False
    missing: list[str] = None

    def __post_init__(self) -> None:
        if self.missing is None:
            self.missing = []


def _atomic_symlink(target: Path, link: Path, *, dry_run: bool) -> bool:
    """Create or replace a symlink at ``link`` pointing to ``target``.

    Returns True if the symlink was created or updated, False if it already
    pointed at the same target.

    Uses ``Path.symlink_to`` after ``unlink`` for atomicity-as-best-effort.
    The link is written as a relative path so the repo remains portable.
    """
    if not target.exists():
        raise FileNotFoundError(f"symlink target does not exist: {target}")
    relative = Path(
        *[".."] * (len(link.parent.relative_to(_REPO_ROOT).parts))
    ) / target.relative_to(_REPO_ROOT)
    if link.is_symlink() or link.exists():
        if link.is_symlink() and link.readlink() == relative:
            return False
        if dry_run:
            logger.info(f"[dry-run] would replace symlink {link} -> {relative}")
            return True
        link.unlink()
    if dry_run:
        logger.info(f"[dry-run] would create symlink {link} -> {relative}")
        return True
    link.symlink_to(relative)
    return True


def _find_techflat_source(sku: str) -> Path | None:
    """Find the FRONT techflat file for a SKU under data/product-references/.

    Resolution order:
        1. {sku}-techflat-front.*   (split output — preferred, view-accurate)
        2. {sku}*-techflat.*        (combined/single techflat, not yet split)

    Returns the first match (sorted for stability).
    """
    if not PRODUCT_REFERENCES_DIR.is_dir():
        return None
    front = sorted(PRODUCT_REFERENCES_DIR.glob(f"{sku}-techflat-front.*"))
    if front:
        return front[0]
    # Fall back to a combined/single techflat for SKUs not yet split.
    # Exclude already-split -front/-back files (handled above / below).
    candidates = [
        p
        for p in sorted(PRODUCT_REFERENCES_DIR.glob(f"{sku}*-techflat.*"))
        if "-techflat-front" not in p.name and "-techflat-back" not in p.name
    ]
    return candidates[0] if candidates else None


def _find_real_back_source(sku: str) -> Path | None:
    """Find the BACK techflat for a SKU.

    Resolution order:
        1. {sku}-techflat-back.*    (split output — preferred)
        2. {sku}*-real-back.*       (real back photo, stand-in)
        3. {sku}*-back.*            (any back image)
    """
    if not PRODUCT_REFERENCES_DIR.is_dir():
        return None
    back = sorted(PRODUCT_REFERENCES_DIR.glob(f"{sku}-techflat-back.*"))
    if back:
        return back[0]
    candidates = sorted(PRODUCT_REFERENCES_DIR.glob(f"{sku}*-real-back.*"))
    if candidates:
        return candidates[0]
    candidates = [
        p
        for p in sorted(PRODUCT_REFERENCES_DIR.glob(f"{sku}*-back.*"))
        if "-techflat-back" not in p.name
    ]
    return candidates[0] if candidates else None


def _find_logo_file(logo_id: str, registry: dict, sku: str) -> Path | None:
    """Resolve a logo_id to a file on disk for a given SKU.

    Two resolution paths:
    1. ``co_located_per_sku`` logos (sport patches) live at
       ``products/<sku_folders[sku]>/<filename>`` — NOT in images/logos/.
       These are SKU-specific, so the resolution needs the SKU's folder
       mapping from the registry's ``sku_folders`` block.
    2. Centralized logos live in ``assets/images/logos/`` keyed by
       ``filename`` (or a logo_id glob fallback).
    """
    logo = (registry.get("logos") or {}).get(logo_id, {})
    filename = logo.get("filename") or logo.get("file") or ""

    if logo.get("co_located_per_sku"):
        folder = (registry.get("sku_folders") or {}).get(sku)
        if folder and filename:
            candidate = WP_PRODUCTS_DIR / folder / filename
            if candidate.is_file():
                return candidate
        # Co-located logo with no folder mapping or missing file — unresolvable.
        return None

    if filename:
        candidate = WP_LOGOS_DIR / filename
        if candidate.is_file():
            return candidate
    matches = sorted(WP_LOGOS_DIR.glob(f"{logo_id}.*"))
    return matches[0] if matches else None


def _prune_orphan_symlinks(directory: Path, *, dry_run: bool) -> int:
    """Remove symlinks whose targets no longer exist. Returns count pruned."""
    if not directory.is_dir():
        return 0
    pruned = 0
    for entry in directory.iterdir():
        if entry.is_symlink() and not entry.exists():
            if dry_run:
                logger.info(f"[dry-run] would prune orphan symlink {entry}")
            else:
                entry.unlink()
            pruned += 1
    return pruned


def _build_placement_md(sku: str, product: dict, registry: dict) -> str:
    """Generate the per-SKU placement brief from canonical sources only."""
    name = product.get("name", "")
    collection = product.get("collection", "")
    branding_spec = (product.get("branding_spec") or "").strip()
    dossier = product.get("dossier") or product.get("_dossier") or {}
    garment_lock = (dossier.get("garment_type_lock") or "").strip()
    scene_pose = (dossier.get("scene_pose") or "").strip()
    scene_setting = (dossier.get("scene_setting") or "").strip()
    negative = (dossier.get("negative_block") or "").strip()

    sku_logos = (registry.get("sku_logos") or {}).get(sku, {})
    placements = sku_logos.get("placements") or []
    front_text = sku_logos.get("front_text", "")
    front_text_technique = sku_logos.get("front_text_technique", "")

    lines = [
        f"# {sku} — {name}",
        f"_Collection: {collection}_",
        "",
        "## Branding spec (one-line)",
        branding_spec if branding_spec else "_None recorded._",
        "",
        "## Garment silhouette lock",
        garment_lock if garment_lock else "_None recorded._",
        "",
        "## Logo placements",
    ]
    if placements:
        for i, p in enumerate(placements, 1):
            logo_id = p.get("logo_id", "?")
            position = p.get("position", "?")
            technique = p.get("technique", "?")
            size = p.get("size_inches")
            notes = (p.get("notes") or "").strip()
            entry = f"{i}. **{logo_id}** — position: `{position}`, technique: `{technique}`"
            if size:
                entry += f", size: {size}″"
            lines.append(entry)
            if notes:
                lines.append(f"   - {notes}")
    else:
        lines.append("_No logo placements registered for this SKU._")

    if front_text:
        lines += [
            "",
            "## Front text",
            f"**{front_text}** — technique: `{front_text_technique or 'unspecified'}`",
        ]

    lines += [
        "",
        "## Render scene context (dossier)",
        f"**Pose:** {scene_pose}" if scene_pose else "**Pose:** _not specified_",
        f"**Setting:** {scene_setting}" if scene_setting else "**Setting:** _not specified_",
        "",
        "## Do NOT render",
        negative if negative else "_No negative constraints recorded._",
        "",
        "---",
        "_This file is auto-generated from the canonical sources_",
        "_(catalog CSV + dossier + logo-registry.json) by_",
        "_`scripts/scaffold_sku_asset_folders.py`. Edit those sources, not this file._",
        "",
    ]
    return "\n".join(lines)


def scaffold_sku(
    sku: str,
    product: dict,
    registry: dict,
    *,
    dry_run: bool = False,
) -> ScaffoldResult:
    """Build the asset bundle for one SKU. Returns counts of writes."""
    result = ScaffoldResult(sku=sku)
    sku_dir = GOLDEN_DIR / sku

    if not dry_run:
        sku_dir.mkdir(parents=True, exist_ok=True)
    for sub in SUBDIRS:
        d = sku_dir / sub
        if not d.exists():
            if not dry_run:
                d.mkdir(parents=True, exist_ok=True)
            result.created_dirs += 1

    techflat_front = _find_techflat_source(sku)
    if techflat_front:
        link = sku_dir / "techflat" / f"front{techflat_front.suffix}"
        if _atomic_symlink(techflat_front, link, dry_run=dry_run):
            result.created_symlinks += 1
    else:
        result.missing.append("techflat/front")

    techflat_back = _find_real_back_source(sku)
    if techflat_back:
        link = sku_dir / "techflat" / f"back{techflat_back.suffix}"
        if _atomic_symlink(techflat_back, link, dry_run=dry_run):
            result.created_symlinks += 1
    else:
        result.missing.append("techflat/back")

    placements = (registry.get("sku_logos") or {}).get(sku, {}).get("placements") or []
    seen_logo_ids: set[str] = set()
    for p in placements:
        logo_id = p.get("logo_id", "")
        if not logo_id or logo_id in seen_logo_ids:
            continue
        seen_logo_ids.add(logo_id)
        logo_file = _find_logo_file(logo_id, registry, sku)
        if not logo_file:
            result.missing.append(f"logo/{logo_id}")
            continue
        link = sku_dir / "logos" / logo_file.name
        if _atomic_symlink(logo_file, link, dry_run=dry_run):
            result.created_symlinks += 1

    result.pruned_symlinks += _prune_orphan_symlinks(sku_dir / "techflat", dry_run=dry_run)
    result.pruned_symlinks += _prune_orphan_symlinks(sku_dir / "logos", dry_run=dry_run)
    result.pruned_symlinks += _prune_orphan_symlinks(sku_dir / "flatlays", dry_run=dry_run)

    placement_md = sku_dir / "placement.md"
    new_content = _build_placement_md(sku, product, registry)
    if placement_md.exists():
        existing = placement_md.read_text(encoding="utf-8")
    else:
        existing = ""
    if existing != new_content:
        if not dry_run:
            placement_md.write_text(new_content, encoding="utf-8")
        result.wrote_placement = True

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--sku", help="Scaffold a single SKU only.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without modifying disk.",
    )
    args = parser.parse_args()

    if not LOGO_REGISTRY_JSON.is_file():
        logger.error(f"missing logo registry: {LOGO_REGISTRY_JSON}")
        return 2
    registry = json.loads(LOGO_REGISTRY_JSON.read_text(encoding="utf-8"))

    rows = read_catalog_rows()
    if args.sku:
        rows = [r for r in rows if r["sku"] == args.sku]
        if not rows:
            logger.error(f"sku {args.sku!r} not in catalog")
            return 2

    total_dirs = 0
    total_links = 0
    total_placements = 0
    total_missing = 0
    for row in rows:
        sku = row["sku"]
        try:
            product = get_product_with_dossier(sku)
        except Exception as exc:
            logger.warning(f"  {sku}: dossier load failed ({exc}) — skipping")
            continue
        result = scaffold_sku(sku, product, registry, dry_run=args.dry_run)
        total_dirs += result.created_dirs
        total_links += result.created_symlinks
        if result.wrote_placement:
            total_placements += 1
        total_missing += len(result.missing)
        prefix = "[dry-run] " if args.dry_run else ""
        miss = f" missing={result.missing}" if result.missing else ""
        logger.info(
            f"{prefix}{sku}: dirs+{result.created_dirs} links+{result.created_symlinks} "
            f"pruned={result.pruned_symlinks} placement={'Y' if result.wrote_placement else '.'}{miss}"
        )

    logger.info("")
    logger.info(
        f"{'[dry-run] ' if args.dry_run else ''}TOTAL: {len(rows)} skus, "
        f"+{total_dirs} dirs, +{total_links} symlinks, {total_placements} placement.md, "
        f"{total_missing} missing slots"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
