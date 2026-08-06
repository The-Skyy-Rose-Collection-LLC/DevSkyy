#!/usr/bin/env python3
"""Compatibility entrypoint for the canonical ``scripts.sot.lookbook`` component."""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.sot import lookbook as _lookbook

# Preserve the previous importable API while keeping all implementation in the
# canonical component module.
parse_args = _lookbook.parse_lookbook_from_sot_args
esc = _lookbook.esc
resolve_asset = _lookbook.resolve_asset
product_cover = _lookbook.product_cover
render_collection = _lookbook.render_collection
build_html = _lookbook.build_html
normalize_collection_entries = _lookbook.normalize_collection_entries
build_title = _lookbook.build_title
build_lookbook_html = _lookbook.build_lookbook_html
DEFAULT_SOT_PATH = _lookbook.DEFAULT_SOT_PATH
DEFAULT_ASSET_BASE = _lookbook.DEFAULT_ASSET_BASE


def main() -> int:
    args = parse_args()
    count, output = _lookbook.run_build_lookbook_from_sot(
        Path(args.sot),
        out_path=Path(args.out),
        asset_base=args.asset_base,
    )
    print(f"Wrote {output} ({count} collections)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
