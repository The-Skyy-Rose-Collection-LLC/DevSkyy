#!/usr/bin/env python3
"""Detect near-duplicate SKUs by CLIP embedding similarity.

Usage:
    python3 scripts/check_catalog_duplicates.py \\
        --embeddings wordpress-theme/skyyrose-flagship/data/product-embeddings.json \\
        --threshold 0.98

Exits 0 if no duplicates found, 1 if duplicates exist (suitable for CI/pre-commit).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skyyrose.core.catalog_dedup import find_duplicates  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.98)
    args = parser.parse_args()

    if not args.embeddings.exists():
        print(f"FATAL: embeddings file not found: {args.embeddings}", file=sys.stderr)
        return 2

    duplicates = find_duplicates(args.embeddings, threshold=args.threshold)

    if not duplicates:
        print(f"OK — no duplicates above threshold {args.threshold}")
        return 0

    print(f"FOUND {len(duplicates)} duplicate pair(s) at threshold {args.threshold}:")
    for d in duplicates:
        print(f"  {d.score:.4f}  {d.sku_a:<14} [{d.collection_a:<12}] {d.name_a}")
        print(f"           {d.sku_b:<14} [{d.collection_b:<12}] {d.name_b}")
        print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
