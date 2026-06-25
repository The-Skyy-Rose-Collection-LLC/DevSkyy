#!/usr/bin/env python3
"""Generate ``assets/products/manifest.json`` — the content-hashed SKU→asset map.

Resolves every SKU's assets through the *same* authority the render pipeline
uses (``scripts/oai_render/references.py``), so the manifest can never describe
a different reality than the renderer. For each catalog SKU it records the
front/back garment source, the logo/sport-patch reference, and the dossier, each
pinned to a SHA-256.

Usage::

    python scripts/build_asset_manifest.py            # write manifest.json
    python scripts/build_asset_manifest.py --check     # exit 1 if drift vs committed
    python scripts/build_asset_manifest.py --report    # print catalog↔tree drift

``--check`` is the CI gate: it regenerates the manifest in memory and diffs it
against the committed file. A file renamed/replaced without regenerating, or a
manifest edited by hand, fails the build.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Repo root on sys.path so ``skyyrose`` and ``scripts`` import cleanly.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.oai_render import references  # noqa: E402
from skyyrose.core import paths  # noqa: E402
from skyyrose.core.asset_manifest import (  # noqa: E402
    AssetManifest,
    AssetRecord,
    SkuAssets,
    hash_if_present,
    to_repo_relative,
)
from skyyrose.core.catalog_loader import read_catalog_rows  # noqa: E402
from skyyrose.core.hashing import sha256_of_file  # noqa: E402


def _catalog_rows() -> dict[str, dict]:
    """SKU → {name, collection, garment_type} via the shared catalog loader."""
    return {
        row["sku"].strip(): {
            "name": (row.get("name") or "").strip(),
            "collection": (row.get("collection") or "").strip(),
            "garment_type": (row.get("garment_type_lock") or "").strip(),
        }
        for row in read_catalog_rows()
        if (row.get("sku") or "").strip()
    }


def _record(role: str, path: Path | None) -> AssetRecord | None:
    """Hash an optional asset path into an AssetRecord (None when no path given)."""
    if path is None:
        return None
    return AssetRecord(role=role, path=to_repo_relative(path), sha256=hash_if_present(path))


def build() -> AssetManifest:
    catalog = _catalog_rows()
    dossier_index = references.build_dossier_index()

    manifest = AssetManifest()
    manifest.catalog_sha = sha256_of_file(paths.CATALOG_CSV)

    # Record every asset the renderer ACTUALLY resolves (build_references applies
    # the real-photo / flatlay rescue), not the raw source-map dict — so the
    # manifest is the exact truth of every file each paid render consumes. The
    # ref's own kind (garment / garment-back / logo / patch) is the role; the
    # dossier is recorded separately. Multiple garment refs (flatlay + techflat)
    # are each pinned so a change to either is caught.
    for sku, info in catalog.items():
        records: list[AssetRecord] = []
        try:
            resolved = references.build_references(sku, info["collection"])
        except references.MissingReferenceError:
            resolved = []
        seen: set[str] = set()
        for ref in resolved:
            rel = to_repo_relative(ref.path)
            if rel in seen:
                continue
            seen.add(rel)
            rec = _record(ref.kind, ref.path)
            if rec is not None:
                records.append(rec)
        dossier_rec = _record("dossier", dossier_index.get(sku))
        if dossier_rec is not None:
            records.append(dossier_rec)
        manifest.skus[sku] = SkuAssets(
            sku=sku,
            name=info["name"],
            collection=info["collection"],
            garment_type=info["garment_type"],
            assets=records,
        )
    return manifest


def report() -> int:
    """Print catalog↔tree drift: catalog SKUs with no garment source, and asset
    files whose embedded SKU is not in the catalog. Read-only; always exits 0."""
    catalog = _catalog_rows()
    source_map = references.get_source_map()

    print("== catalog SKUs missing a garment source ==")
    missing = [s for s in catalog if s not in source_map or source_map[s].get("front") is None]
    for s in missing:
        print(f"  {s:<18} {catalog[s]['name']}")
    print(f"  ({len(missing)} of {len(catalog)})")

    print("\n== source-map SKUs not in catalog (phantom / retired) ==")
    phantom = [s for s in source_map if s not in catalog]
    for s in phantom:
        print(f"  {s}")
    print(f"  ({len(phantom)})")

    print("\n== source files that exist but hash-verify nothing (broken paths) ==")
    broken = 0
    for sku, garment in source_map.items():
        for role in ("front", "back"):
            p = garment.get(role)
            if p is not None and not p.exists():
                print(f"  {sku:<18} {role:<5} -> {to_repo_relative(p)}  MISSING")
                broken += 1
    print(f"  ({broken})")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--check", action="store_true", help="exit 1 if regenerated manifest != committed"
    )
    ap.add_argument("--report", action="store_true", help="print catalog↔tree drift, write nothing")
    args = ap.parse_args(argv[1:])

    if args.report:
        return report()

    fresh = build()
    if args.check:
        committed = AssetManifest.load()
        if committed.to_payload()["skus"] != fresh.to_payload()["skus"]:
            print(
                "asset manifest drift: regenerated manifest differs from the committed "
                "assets/products/manifest.json.\nRun `python scripts/build_asset_manifest.py` "
                "and commit the result.",
                file=sys.stderr,
            )
            return 1
        print("asset manifest: in sync with the tree.")
        return 0

    out = fresh.save()
    n_assets = sum(len(sa.assets) for sa in fresh.skus.values())
    print(f"wrote {out} — {len(fresh.skus)} SKUs, {n_assets} hashed assets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
