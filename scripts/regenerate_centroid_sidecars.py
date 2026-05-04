#!/usr/bin/env python3
"""Backfill JSON sidecars for existing brand centroid .npz files.

Reads every ``brand_centroid*.npz`` under ``--data-dir`` and writes a
``brand_centroid*.metadata.json`` next to each, recording the centroid's
provenance fields (encoder, model_id, sample_count, threshold, etc.).

Centroids built before this script existed will have an empty
``sample_paths`` field — there's no recovering that information from the
binary alone. Future centroids built via ``build_centroid()`` carry their
sample paths through and the sidecar fills in.

Usage:
    python3 scripts/regenerate_centroid_sidecars.py
    python3 scripts/regenerate_centroid_sidecars.py --data-dir skyyrose/elite_studio/data
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from skyyrose.elite_studio.quality.brand_centroid import (
    load_centroid,
    write_metadata_sidecar,
)


def _default_data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "skyyrose" / "elite_studio" / "data"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=_default_data_dir(),
        help="Directory containing brand_centroid*.npz files",
    )
    args = parser.parse_args()

    if not args.data_dir.is_dir():
        print(f"FATAL: data dir not found: {args.data_dir}", file=sys.stderr)
        return 1

    npz_files = sorted(args.data_dir.glob("brand_centroid*.npz"))
    if not npz_files:
        print(f"No brand_centroid*.npz files in {args.data_dir}")
        return 0

    print(f"Regenerating sidecars for {len(npz_files)} centroid file(s):")
    for npz_path in npz_files:
        centroid = load_centroid(npz_path)
        sidecar = write_metadata_sidecar(centroid, npz_path)
        print(
            f"  {npz_path.name}: "
            f"encoder={'dino' if 'dino' in centroid.model_id.lower() else 'clip'} "
            f"samples={centroid.sample_count} "
            f"threshold={centroid.threshold:.4f} "
            f"-> {sidecar.name}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
