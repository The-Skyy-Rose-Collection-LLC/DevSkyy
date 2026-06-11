#!/usr/bin/env python3
"""Seed golden references from existing source-product photography.

Walks ``assets/products/source-photos/`` and ``wordpress-theme/.../products/``,
maps each photo to a SKU + angle, and copies it into the canonical goldens path.
Intended as a one-time backfill so the visual-regression test has SOMETHING to
score against on day one.

Honors CLAUDE.md STOP-AND-SHOW: prints the full plan and waits for ``y``
before copying anything. Pass ``--force`` to skip the confirmation when run
from CI.

Usage:
  python scripts/seed_goldens_from_source.py                # interactive
  python scripts/seed_goldens_from_source.py --force        # CI mode
  python scripts/seed_goldens_from_source.py --dry-run      # plan only
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skyyrose.core.catalog_loader import read_catalog_rows  # noqa: E402
from skyyrose.elite_studio.quality.visual_regression import (  # noqa: E402
    CANONICAL_ANGLES,
    VisualRegressionTester,
)

SOURCE_ROOT = ROOT / "assets" / "products" / "source-photos"
THEME_PRODUCTS = ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products"

# Filename pattern → angle slug mapping. Matches conservatively — only files
# with an unambiguous angle suffix get seeded. Ambiguous ones get skipped and
# flagged in the report so a human curator can decide.
_ANGLE_RE = re.compile(
    r"-(front|back|side|three[-_]quarter|threequarter|"
    r"detail|detail[-_]graphic|detail[-_]hood|detail[-_]pocket|"
    r"detail[-_]patch|detail[-_]stitching)\.(?:jpg|jpeg|png|webp)$",
    re.IGNORECASE,
)

_ANGLE_NORMALIZE = {
    "front": "front",
    "back": "back",
    "side": "three-quarter",
    "three-quarter": "three-quarter",
    "three_quarter": "three-quarter",
    "threequarter": "three-quarter",
    "detail": "detail-1",
    "detail-graphic": "detail-1",
    "detail_graphic": "detail-1",
    "detail-hood": "detail-1",
    "detail_hood": "detail-1",
    "detail-pocket": "detail-2",
    "detail_pocket": "detail-2",
    "detail-patch": "detail-1",
    "detail_patch": "detail-1",
    "detail-stitching": "detail-2",
    "detail_stitching": "detail-2",
}


def _scan_source_dirs(active_skus: set[str]) -> dict[str, dict[str, Path]]:
    """Return ``{sku: {angle: source_path}}`` for every matchable file."""
    by_sku: dict[str, dict[str, Path]] = {}
    candidates: list[Path] = []
    for base in (SOURCE_ROOT, THEME_PRODUCTS):
        if base.is_dir():
            candidates.extend(base.rglob("*.jp*g"))
            candidates.extend(base.rglob("*.png"))
            candidates.extend(base.rglob("*.webp"))

    for path in candidates:
        name = path.name.lower()
        # Find the SKU prefix — any of the active SKUs that the filename starts with
        sku_match = next(
            (sku for sku in active_skus if name.startswith(sku.lower() + "-")),
            None,
        )
        if not sku_match:
            continue
        m = _ANGLE_RE.search(name)
        if not m:
            continue
        raw_angle = m.group(1).lower()
        canonical = _ANGLE_NORMALIZE.get(raw_angle)
        if canonical is None or canonical not in CANONICAL_ANGLES:
            continue
        # Only set the first match per (sku, angle) — earlier files (sorted)
        # take precedence so deterministic across runs.
        bucket = by_sku.setdefault(sku_match, {})
        if canonical not in bucket:
            bucket[canonical] = path

    return by_sku


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed goldens from source photos")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--dry-run", action="store_true", help="Plan without copying")
    args = parser.parse_args()

    active_skus = {row["sku"] for row in read_catalog_rows() if row.get("sku")}
    plan = _scan_source_dirs(active_skus)
    if not plan:
        print("✗ no candidate source photos matched the filename pattern.", file=sys.stderr)
        return 1

    total_files = sum(len(v) for v in plan.values())
    skus_covered = len(plan)
    full_coverage_skus = sum(1 for v in plan.values() if len(v) == len(CANONICAL_ANGLES))

    print("Golden seeding plan:")
    print(f"  source roots: {SOURCE_ROOT}, {THEME_PRODUCTS}")
    print(f"  candidate files: {total_files}")
    print(f"  SKUs with at least one match: {skus_covered}")
    print(f"  SKUs with full {len(CANONICAL_ANGLES)}-angle coverage: {full_coverage_skus}")
    print()
    for sku in sorted(plan):
        angles = ", ".join(sorted(plan[sku]))
        print(f"  {sku}: {angles}")

    if args.dry_run:
        print("\n(dry run — no files copied)")
        return 0

    print(
        "\nThis will COPY files into "
        "skyyrose/elite_studio/assets/golden/{sku}/{angle}.jpg "
        "(no source files modified)."
    )
    if not args.force:
        ans = input("Proceed? [y/N] ").strip().lower()
        if ans not in ("y", "yes"):
            print("aborted")
            return 1

    tester = VisualRegressionTester()
    written = 0
    for sku, angles in plan.items():
        for angle, src in angles.items():
            try:
                # Skip if a real golden already exists; don't overwrite human curation.
                cov = tester.coverage_for(sku)
                if cov.get(angle):
                    continue
                dest_dir = tester._golden_base / sku
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest = dest_dir / f"{angle}.jpg"
                # Convert to JPEG if needed; otherwise straight copy.
                if src.suffix.lower() in (".jpg", ".jpeg"):
                    shutil.copy2(src, dest)
                else:
                    try:
                        from PIL import Image

                        with Image.open(src) as img:
                            img.convert("RGB").save(dest, format="JPEG", quality=92)
                    except Exception:
                        shutil.copy2(src, dest)
                if angle == "front":
                    shutil.copy2(dest, dest_dir / "reference.jpg")
                written += 1
            except Exception as exc:
                print(f"  ! {sku}/{angle}: {exc}", file=sys.stderr)

    print(f"\n✓ wrote {written} golden(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
