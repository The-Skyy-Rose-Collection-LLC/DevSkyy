#!/usr/bin/env python3
"""approve-ghost {sku} — move reviewed image to approved/ and update CSV.

Phase 17 (REV-01, REV-02). All business logic lives in
skyyrose.core.review.approve() so this stays a thin CLI shell.

Exit codes:
    0 — approval committed (file moved, CSV updated, audit logged)
    1 — review failure (no file, sku missing, already approved, IO error)
    2 — argparse usage error
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from skyyrose.core.review import ReviewError, approve  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="approve-ghost",
        description=(
            "Approve a ghost-mannequin front image. Moves "
            "renders/ghost-mannequin/{sku}-ghost-front.webp into approved/ "
            "and atomically updates front_model_image in the catalog CSV."
        ),
    )
    parser.add_argument("sku", help="Catalog SKU (e.g. br-001)")
    parser.add_argument(
        "--root",
        default=None,
        help="Repo root override (defaults to detected root from this script's path)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = approve(args.sku, root=args.root)
    except ReviewError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"unexpected error: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"approved: {result.sku}")
    print(f"  moved : {result.approved_path}")
    print(f"  csv   : {result.csv_path} (front_model_image updated)")
    print(f"  at    : {result.timestamp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
