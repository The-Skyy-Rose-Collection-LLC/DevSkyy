#!/usr/bin/env python3
"""Build a single aggregated lookbook SOT from per-collection SOT files.

Output schema:
{
  "domain": "wordpress-theme",
  "component": "lookbook",
  "collections": [
    {"collection": "black-rose", ...},
    ...
  ]
}

This script intentionally emits one authoritative file so downstream tools can
consume a single SOT source. To avoid scanning large trees, source collections
are read from an explicit manifest by default.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_COLLECTIONS_DIR = ROOT / "wordpress-theme" / "skyyrose-flagship" / "data" / "collections"
DEFAULT_MANIFEST_PATH = ROOT / "scripts" / "lookbook-manifest.json"
DEFAULT_OUT = ROOT / "wordpress-theme" / "skyyrose-flagship" / "data" / "lookbook-sot.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a single lookbook SOT by merging per-collection SOT files."
    )
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST_PATH),
        help="Manifest with explicit list of source collection SOT files.",
    )
    parser.add_argument(
        "--collections-dir",
        default=None,
        help="Fallback: directory containing data/collections/<slug>/sot.json files.",
    )
    parser.add_argument(
        "--domain",
        default=None,
        help="Domain identifier stored in the aggregated SOT.",
    )
    parser.add_argument(
        "--component",
        default=None,
        help="Component identifier stored in the aggregated SOT.",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUT),
        help="Output path for aggregated lookbook SOT.",
    )
    return parser.parse_args()


def load_manifest_sources(
    manifest_file: Path,
) -> tuple[str | None, str | None, list[dict[str, Any]]]:
    """Load and validate a compact explicit ordered manifest.

    This keeps lookbook rebuild deterministic and avoids expensive directory scans,
    especially with large repository trees.
    """
    if not manifest_file.exists():
        raise FileNotFoundError(f"Manifest missing: {manifest_file}")

    raw: Any = json.loads(manifest_file.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Manifest must be an object with sources.")
    sources = raw.get("sources")
    if not isinstance(sources, list):
        raise ValueError("Manifest sources must be an array.")

    collections: list[dict[str, Any]] = []
    for idx, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            raise TypeError(f"Manifest source #{idx} must be an object.")

        slug = (source.get("slug") or source.get("collection") or "").strip()
        sot_ref = (source.get("sot") or source.get("path") or "").strip()
        if not slug:
            raise ValueError(f"Manifest source #{idx} missing slug/collection.")
        if not sot_ref:
            raise ValueError(f"Manifest source #{idx} ({slug}) missing sot/path.")

        sot_file = Path(sot_ref)
        if not sot_file.is_absolute():
            sot_file = ROOT / sot_file
        if not sot_file.exists():
            raise FileNotFoundError(f"Manifest source #{idx} SOT missing: {sot_file}")

        payload: Any = json.loads(sot_file.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise TypeError(f"Manifest source #{idx} did not contain JSON object: {sot_file}")

        payload = dict(payload)
        payload["collection"] = slug
        collections.append(payload)

    return raw.get("domain"), raw.get("component"), collections


def load_collections_from_manifest(
    manifest_file: Path,
) -> tuple[str | None, str | None, list[dict[str, Any]]]:
    # Maintain compatibility with existing call sites.
    return load_manifest_sources(manifest_file)


def load_collections_from_dir(collections_dir: Path) -> list[dict[str, Any]]:
    if not collections_dir.exists():
        raise FileNotFoundError(f"Collections directory missing: {collections_dir}")

    out: list[dict[str, Any]] = []
    for folder in sorted(p for p in collections_dir.iterdir() if p.is_dir()):
        sot_file = folder / "sot.json"
        if not sot_file.exists():
            continue
        payload: Any = json.loads(sot_file.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise TypeError(f"Invalid SOT payload in {sot_file}")
        payload = dict(payload)
        payload["collection"] = folder.name
        out.append(payload)
    return out


def build_lookbook_payload(
    manifest_file: Path | None,
    domain: str | None = None,
    component: str | None = None,
    collections_dir: Path | None = None,
) -> dict[str, Any]:
    """Build an aggregated payload in memory for deterministic byte-comparison."""
    manifest_domain = manifest_component = None
    collections: list[dict[str, Any]] = []

    if manifest_file is not None:
        manifest_domain, manifest_component, collections = load_manifest_sources(manifest_file)

    if not collections and collections_dir is not None:
        collections = load_collections_from_dir(collections_dir)

    if not collections:
        raise RuntimeError("No collection SOTs found to aggregate.")

    return {
        "domain": domain or manifest_domain or "wordpress-theme/skyyrose-flagship",
        "component": component or manifest_component or "lookbook",
        "collections": collections,
    }


def serialize(payload: dict[str, Any]) -> str:
    """Single byte-authority format for emitted lookbook-sot.json."""
    return json.dumps(payload, indent=2) + "\n"


def main() -> int:
    args = parse_args()
    out = Path(args.out)

    manifest_path = Path(args.manifest) if args.manifest else None
    collections_dir = Path(args.collections_dir) if args.collections_dir else None

    try:
        payload = build_lookbook_payload(
            manifest_file=manifest_path,
            domain=args.domain,
            component=args.component,
            collections_dir=collections_dir,
        )
    except FileNotFoundError:
        if collections_dir is None:
            raise
        payload = build_lookbook_payload(
            manifest_file=None,
            domain=args.domain,
            component=args.component,
            collections_dir=collections_dir,
        )
    except RuntimeError:
        if collections_dir is None and manifest_path is not None:
            raise SystemExit(f"No collection SOTs found from manifest: {manifest_path}")
        if collections_dir is None:
            raise
        payload = build_lookbook_payload(
            manifest_file=None,
            domain=args.domain,
            component=args.component,
            collections_dir=collections_dir,
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(serialize(payload), encoding="utf-8")
    print(f"Wrote {out} ({len(payload['collections'])} collections)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
