#!/usr/bin/env python3
"""Backfill JSON sidecars for existing brand centroid .npz files.

Reads every ``brand_centroid*.npz`` under ``--data-dir`` and writes a
``brand_centroid*.metadata.json`` next to each, recording the centroid's
provenance fields (encoder, model_id, sample_count, threshold, etc.).

Centroids built before this script existed have an empty ``sample_paths``
field by default. Pass ``--sample-glob PATTERN`` to recover the path list
when you know which files were originally used. The expanded glob's count
must match ``centroid.sample_count`` for each centroid being updated.

Future centroids built via ``build_centroid()`` carry their sample paths
through and the sidecar fills in automatically.

Usage:
    python3 scripts/regenerate_centroid_sidecars.py
    python3 scripts/regenerate_centroid_sidecars.py --data-dir skyyrose/elite_studio/data
    python3 scripts/regenerate_centroid_sidecars.py \\
        --sample-glob 'wordpress-theme/skyyrose-flagship/assets/images/products/*-front-model.webp'
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from skyyrose.elite_studio.quality.brand_centroid import (
    IMAGE_EXTS,
    load_centroid,
    write_metadata_sidecar,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _default_data_dir() -> Path:
    return REPO_ROOT / "skyyrose" / "elite_studio" / "data"


def _expand_sample_glob(pattern: str, repo_root: Path) -> list[str]:
    """Expand a glob pattern relative to repo_root, returning sorted
    repo-relative POSIX strings filtered to IMAGE_EXTS."""
    matches = sorted(repo_root.glob(pattern))
    images = [p for p in matches if p.suffix.lower() in IMAGE_EXTS]
    return [p.relative_to(repo_root).as_posix() for p in images]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=_default_data_dir(),
        help="Directory containing brand_centroid*.npz files",
    )
    parser.add_argument(
        "--sample-glob",
        type=str,
        default=None,
        help="Glob pattern (relative to --repo-root) for sample paths to "
        "stamp into each sidecar's sample_paths field. Use to backfill "
        "legacy centroids whose .npz predates the sample_paths field.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Root for resolving --sample-glob and computing relative paths.",
    )
    args = parser.parse_args()

    if not args.data_dir.is_dir():
        print(f"FATAL: data dir not found: {args.data_dir}", file=sys.stderr)
        return 1

    sample_paths: list[str] | None = None
    if args.sample_glob:
        sample_paths = _expand_sample_glob(args.sample_glob, args.repo_root)
        if not sample_paths:
            print(
                f"FATAL: --sample-glob {args.sample_glob!r} matched no images "
                f"under {args.repo_root}",
                file=sys.stderr,
            )
            return 1
        print(f"Resolved --sample-glob to {len(sample_paths)} image(s)")

    npz_files = sorted(args.data_dir.glob("brand_centroid*.npz"))
    if not npz_files:
        print(f"No brand_centroid*.npz files in {args.data_dir}")
        return 0

    print(f"Regenerating sidecars for {len(npz_files)} centroid file(s):")
    exit_code = 0
    for npz_path in npz_files:
        centroid = load_centroid(npz_path)
        if sample_paths is not None:
            if len(sample_paths) != centroid.sample_count:
                print(
                    f"  {npz_path.name}: SKIP path backfill — glob has "
                    f"{len(sample_paths)} files but centroid was built from "
                    f"{centroid.sample_count}",
                    file=sys.stderr,
                )
                exit_code = 1
            else:
                centroid.sample_paths = list(sample_paths)
        sidecar = write_metadata_sidecar(centroid, npz_path)
        backfilled = (
            " (paths backfilled)" if sample_paths is not None and centroid.sample_paths else ""
        )
        print(
            f"  {npz_path.name}: "
            f"encoder={'dino' if 'dino' in centroid.model_id.lower() else 'clip'} "
            f"samples={centroid.sample_count} "
            f"threshold={centroid.threshold:.4f}{backfilled} "
            f"-> {sidecar.name}"
        )
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
