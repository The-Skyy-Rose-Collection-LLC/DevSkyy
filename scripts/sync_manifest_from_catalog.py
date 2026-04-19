#!/usr/bin/env python3
"""Sync manifest.json from catalog.yaml.

catalog.yaml is the single source of truth. manifest.json is a DERIVED
artifact maintained for backward compatibility with code paths that import
`skyyrose.elite_studio.master_registry.Manifest`.

Retired SKUs are excluded from manifest.json (active-only).

Usage:
    python scripts/sync_manifest_from_catalog.py
    python scripts/sync_manifest_from_catalog.py --check        # exit 1 if out of sync
    python scripts/sync_manifest_from_catalog.py --output /tmp/manifest.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dataclasses import asdict  # noqa: E402

from skyyrose.elite_studio.catalog import Catalog  # noqa: E402
from skyyrose.elite_studio.master_registry import MasterEntry  # noqa: E402

DEFAULT_MANIFEST_PATH = _REPO_ROOT / "assets" / "product-masters" / "manifest.json"


def build_manifest(cat: Catalog) -> dict[str, Any]:
    """Translate a Catalog into the manifest.json shape read by Manifest.load().

    Builds MasterEntry instances (not raw dicts) so field drift is caught at
    instantiation — MasterEntry.__init__ rejects unknown kwargs, so any schema
    change in master_registry.py will surface here immediately.
    """
    masters: dict[str, Any] = {}
    for sku in cat.list_skus(active_only=True):
        p = cat.require(sku)
        master = p.master or {}
        entry = MasterEntry(
            sku=sku,
            master_path=master.get("path") or "",
            master_hash=master.get("hash"),
            master_source=master.get("source", "pending"),
            status="locked" if p.is_locked else "pending",
            collection=p.collection,
            alpha_path=master.get("alpha_path"),
            alpha_hash=master.get("alpha_hash"),
            color_spec=dict(p.color_spec),
            text_spec=list(p.text_spec),
            photographed_at=master.get("photographed_at"),
            locked_at_version=master.get("locked_at_version"),
            notes=p.notes,
        )
        masters[sku] = asdict(entry)

    return {
        "version": 1,
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_from": "catalog.yaml via scripts/sync_manifest_from_catalog.py",
        "masters": masters,
    }


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(_REPO_ROOT))
    except ValueError:
        return str(p)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 without writing if manifest.json would change (CI use)",
    )
    args = parser.parse_args(argv)

    cat = Catalog.load()
    new_manifest = build_manifest(cat)
    new_text = json.dumps(new_manifest, indent=2, default=str)

    if args.check:
        if not args.output.is_file():
            print(f"ERROR: {_rel(args.output)} does not exist — run without --check to create it")
            return 1
        try:
            current = json.loads(args.output.read_text())
        except Exception as e:
            print(f"ERROR: {_rel(args.output)} is not valid JSON: {e}")
            return 1
        # Compare only the `masters` dict (timestamps will always differ)
        if current.get("masters") == new_manifest["masters"]:
            print(
                f"OK: {_rel(args.output)} is in sync with catalog.yaml "
                f"({len(new_manifest['masters'])} active SKUs)"
            )
            return 0
        print(f"DIFF: {_rel(args.output)} would change — re-run without --check to sync")
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(new_text)
    print(
        f"Wrote {_rel(args.output)} "
        f"({len(new_manifest['masters'])} active SKUs derived from catalog.yaml)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
