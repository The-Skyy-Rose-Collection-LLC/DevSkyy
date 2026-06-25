#!/usr/bin/env python3
"""Verify every entry in visual-manifest.json resolves to real files on disk.

Walks all asset entries (any dict with 'path' + 'formats'), checks each
path.format combination under assets/, and reports missing files and
needs-founder-review entries. Exit 1 on any missing file.

Usage: python3 verify-visual-manifest.py
"""

import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
ASSETS = DATA_DIR.parent / "assets"
MANIFEST = DATA_DIR / "visual-manifest.json"


def iter_assets(node, trail=""):
    if isinstance(node, dict):
        if "path" in node and "formats" in node:
            yield trail, node
        else:
            for k, v in node.items():
                yield from iter_assets(v, f"{trail}.{k}" if trail else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from iter_assets(v, f"{trail}[{i}]")


def main() -> int:
    manifest = json.loads(MANIFEST.read_text())
    missing, review, checked = [], [], 0
    for trail, entry in iter_assets(manifest):
        for fmt in entry["formats"]:
            # formats are either bare extensions ("webp") or
            # suffix+extension responsive variants ("960w.webp").
            sep = "-" if fmt[0].isdigit() else "."
            f = ASSETS / f"{entry['path']}{sep}{fmt}"
            checked += 1
            if not f.is_file():
                missing.append(str(f.relative_to(ASSETS)))
        if entry.get("status") == "needs-founder-review":
            review.append(f"{trail}: {entry['path']}")

    print(f"checked {checked} files")
    if review:
        print(f"\nneeds-founder-review ({len(review)}):")
        for r in review:
            print(f"  - {r}")
    if missing:
        print(f"\nMISSING ({len(missing)}):")
        for m in missing:
            print(f"  - {m}")
        return 1
    print("\nall manifest paths verified on disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
