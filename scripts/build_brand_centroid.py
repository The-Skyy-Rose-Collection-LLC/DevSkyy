#!/usr/bin/env python3
"""Build the SkyyRose brand-style centroid from approved hero shots.

Usage:
    python3 scripts/build_brand_centroid.py \\
        --approved-dir wordpress-theme/skyyrose-flagship/assets/images/products \\
        --output skyyrose/elite_studio/data/brand_centroid.npz \\
        --threshold-percentile 10

Re-run whenever the approved-shot set changes.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skyyrose.elite_studio.quality.brand_centroid import (  # noqa: E402
    build_centroid,
    save_centroid,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approved-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threshold-percentile", type=float, default=10.0)
    parser.add_argument(
        "--encoder",
        choices=("clip", "dino"),
        default="clip",
        help="Vision encoder: 'clip' (CLIP-base, default) or 'dino' (DINOv2, "
        "stronger image-only similarity).",
    )
    args = parser.parse_args()

    if not args.approved_dir.is_dir():
        print(f"FATAL: approved-dir not found: {args.approved_dir}", file=sys.stderr)
        return 1

    print(f"Building {args.encoder} centroid from {args.approved_dir}...")
    centroid = build_centroid(
        args.approved_dir,
        threshold_percentile=args.threshold_percentile,
        encoder=args.encoder,
    )
    save_centroid(centroid, args.output)
    print(
        f"Wrote centroid ({centroid.sample_count} samples, model={centroid.model_id}, "
        f"threshold={centroid.threshold:.4f}) -> {args.output}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
