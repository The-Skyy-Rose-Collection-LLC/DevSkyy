#!/usr/bin/env python3
"""Curate golden reference images for visual-regression scoring.

Validates an input image (resolution + format), then writes it to the canonical
golden path ``skyyrose/elite_studio/assets/golden/{sku}/{angle}.jpg``. Honors
CLAUDE.md STOP-AND-SHOW: prompts before overwriting an existing golden.

Usage:
  python scripts/capture_goldens.py --sku br-001 --angle front \\
      --image /path/to/approved.jpg

  # Bulk-add multiple angles for a SKU at once:
  python scripts/capture_goldens.py --sku br-001 \\
      --front /path/to/front.jpg --back /path/to/back.jpg

Exit:
  0 on success
  1 on validation failure or user abort
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skyyrose.core.catalog_loader import read_catalog_rows  # noqa: E402
from skyyrose.elite_studio.quality.visual_regression import (  # noqa: E402
    CANONICAL_ANGLES,
    VisualRegressionTester,
)

_MIN_DIM = 2048


def _validate_image(path: Path) -> str | None:
    """Return None if valid, an error message otherwise."""
    if not path.is_file():
        return f"file not found: {path}"
    if path.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
        return f"unsupported format: {path.suffix} (require jpg/png/webp)"
    try:
        from PIL import Image
    except ImportError:
        return "Pillow not installed; cannot validate dimensions"
    try:
        with Image.open(path) as img:
            short = min(img.size)
            if short < _MIN_DIM:
                return (
                    f"image too small ({img.size[0]}x{img.size[1]} px); "
                    f"shortest side must be ≥{_MIN_DIM}px"
                )
    except Exception as exc:
        return f"could not read image: {exc}"
    return None


def _confirm(prompt: str) -> bool:
    """STOP-AND-SHOW prompt — explicit y/N."""
    answer = input(f"{prompt} [y/N] ").strip().lower()
    return answer in ("y", "yes")


def _capture_one(sku: str, angle: str, image: Path, *, force: bool) -> int:
    err = _validate_image(image)
    if err:
        print(f"  ✗ {sku}/{angle}: {err}", file=sys.stderr)
        return 1

    tester = VisualRegressionTester()
    existing = tester.coverage_for(sku).get(angle, False)
    if existing and not force:
        print(f"  ! {sku}/{angle} golden already exists.")
        if not _confirm(f"  overwrite {sku}/{angle}?"):
            print(f"  ✗ {sku}/{angle}: skipped by user")
            return 1

    dest = tester.set_golden(sku, str(image), angle=angle)
    print(f"  ✓ {sku}/{angle} → {dest.relative_to(ROOT)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Curate golden references")
    parser.add_argument("--sku", required=True, help="SKU (must exist in catalog)")
    parser.add_argument("--angle", help="Single angle to capture")
    parser.add_argument("--image", type=Path, help="Source image (required with --angle)")
    parser.add_argument("--force", action="store_true", help="Skip overwrite confirmation")
    # Per-angle convenience flags for bulk capture
    for ang in CANONICAL_ANGLES:
        parser.add_argument(f"--{ang.replace('_', '-')}", type=Path, help=f"Source for {ang}")
    args = parser.parse_args()

    valid_skus = {row["sku"] for row in read_catalog_rows() if row.get("sku")}
    if args.sku not in valid_skus:
        print(
            f"✗ {args.sku} is not in the canonical catalog. Add it to skyyrose-catalog.csv first.",
            file=sys.stderr,
        )
        return 1

    captures: list[tuple[str, Path]] = []
    if args.angle:
        if not args.image:
            print("✗ --angle requires --image", file=sys.stderr)
            return 1
        captures.append((args.angle, args.image))
    for ang in CANONICAL_ANGLES:
        attr = ang.replace("-", "_")
        path = getattr(args, attr, None)
        if path is not None:
            captures.append((ang, path))

    if not captures:
        print(
            "✗ no captures specified — pass --angle/--image or one of --front/--back/...",
            file=sys.stderr,
        )
        return 1

    print(f"Capturing {len(captures)} golden(s) for {args.sku}:")
    failed = 0
    for angle, image in captures:
        if _capture_one(args.sku, angle, image, force=args.force) != 0:
            failed += 1
    if failed:
        print(f"\n✗ {failed} capture(s) failed", file=sys.stderr)
        return 1
    print(f"\n✓ all {len(captures)} captures complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
