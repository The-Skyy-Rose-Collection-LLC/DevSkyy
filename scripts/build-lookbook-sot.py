#!/usr/bin/env python3
"""Compatibility entrypoint for the canonical ``scripts.sot.lookbook`` component."""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.sot import lookbook as _lookbook

# Preserve the previous importable API while keeping all implementation in the
# canonical component module.
parse_args = _lookbook.parse_lookbook_sot_args
load_manifest_sources = _lookbook.load_manifest_sources
load_collections_from_manifest = _lookbook.load_collections_from_manifest
load_collections_from_dir = _lookbook.load_collections_from_dir
build_lookbook_payload = _lookbook.build_lookbook_payload
serialize = _lookbook.serialize
DEFAULT_COLLECTIONS_DIR = _lookbook.DEFAULT_COLLECTIONS_DIR
DEFAULT_MANIFEST_PATH = _lookbook.DEFAULT_MANIFEST_PATH
DEFAULT_OUT = _lookbook.DEFAULT_LOOKBOOK_SOT_OUT


def main() -> int:
    args = parse_args()
    try:
        payload, output = _lookbook.run_build_lookbook_sot(
            Path(args.manifest) if args.manifest else None,
            domain=args.domain,
            component=args.component,
            out_path=Path(args.out),
            collections_dir=Path(args.collections_dir) if args.collections_dir else None,
        )
    except FileNotFoundError:
        if args.collections_dir is None:
            raise
        payload, output = _lookbook.run_build_lookbook_sot(
            None,
            domain=args.domain,
            component=args.component,
            out_path=Path(args.out),
            collections_dir=Path(args.collections_dir),
        )
    except RuntimeError:
        if args.collections_dir is None:
            if args.manifest:
                raise SystemExit(f"No collection SOTs found from manifest: {args.manifest}")
            raise
        payload, output = _lookbook.run_build_lookbook_sot(
            None,
            domain=args.domain,
            component=args.component,
            out_path=Path(args.out),
            collections_dir=Path(args.collections_dir),
        )
    print(f"Wrote {output} ({len(payload['collections'])} collections)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
