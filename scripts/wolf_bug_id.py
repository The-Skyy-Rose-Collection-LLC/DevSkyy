#!/usr/bin/env python3
"""Allocate the next .wolf/buglog.json bug ID; detect ID collisions.

Manual bug-ID allocation (per .wolf/OPENWOLF.md "Bug Logging") caused 9
cross-session collisions -- parallel sessions guessed the same next ID.

Usage:
    python scripts/wolf_bug_id.py               # print next free ID (e.g. bug-189)
    python scripts/wolf_bug_id.py --check        # exit 1 if any duplicate IDs exist
    python scripts/wolf_bug_id.py --path FILE    # use an alternate buglog.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ID_RE = re.compile(r"^bug-(\d+)$")
DEFAULT_BUGLOG = Path(__file__).resolve().parent.parent / ".wolf" / "buglog.json"


def load_ids(path: Path) -> list[str]:
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise ValueError(f"{path}: expected a JSON array, got {type(data).__name__}")
    return [entry.get("id", "") for entry in data]


def next_id(ids: list[str]) -> str:
    numbers = [int(m.group(1)) for i in ids if (m := ID_RE.match(i))]
    return f"bug-{(max(numbers) + 1) if numbers else 1:03d}"


def find_duplicates(ids: list[str]) -> dict[str, int]:
    return {k: v for k, v in Counter(ids).items() if v > 1}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=DEFAULT_BUGLOG)
    parser.add_argument("--check", action="store_true", help="exit 1 on duplicate IDs")
    args = parser.parse_args(argv)

    if not args.path.exists():
        print(f"error: {args.path} not found", file=sys.stderr)
        return 2

    ids = load_ids(args.path)

    if args.check:
        dups = find_duplicates(ids)
        if dups:
            print(f"duplicate bug IDs found: {dups}", file=sys.stderr)
            return 1
        print(f"ok: {len(ids)} bug IDs, no duplicates")
        return 0

    print(next_id(ids))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
