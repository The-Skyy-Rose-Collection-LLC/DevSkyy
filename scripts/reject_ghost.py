#!/usr/bin/env python3
"""reject-ghost {sku} "{reason}" — log rejection; leave file; no CSV change.

Phase 17 (REV-03). Business logic in skyyrose.core.review.reject().

Exit codes:
    0 — rejection logged
    1 — review failure (no file, empty reason, IO error)
    2 — argparse usage error
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from skyyrose.core.review import ReviewError, reject  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reject-ghost",
        description=(
            "Reject a ghost-mannequin front image. Appends "
            "{sku, reason, timestamp} to renders/ghost-mannequin/rejections.json. "
            "File stays in review dir; CSV untouched."
        ),
    )
    parser.add_argument("sku", help="Catalog SKU (e.g. br-001)")
    parser.add_argument("reason", help="Rejection reason (non-empty)")
    parser.add_argument(
        "--root",
        default=None,
        help="Repo root override (defaults to detected root from this script's path)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = reject(args.sku, args.reason, root=args.root)
    except ReviewError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"unexpected error: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"rejected: {result.sku}")
    print(f"  reason: {result.reason}")
    print(f"  file  : {result.file_path} (unchanged)")
    print(f"  at    : {result.timestamp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
