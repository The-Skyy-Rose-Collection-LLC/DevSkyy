#!/usr/bin/env python3
"""Verify the generated SOT + tokens against canon and reality. Exit 0 clean, 1 on hard fail.

Per collection asserts: catalog SKU coverage; every declared resolved path is a real file;
every identity font woff2 resolves; the generated design-tokens region matches a fresh
generation (staleness gate); broken catalog product refs are reported (non-fatal).

The staleness gate regenerates design-tokens.css to compare, then restores the original
bytes on mismatch — so verify never leaves a net change in the working tree.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

DATA = Path(__file__).resolve().parent
sys.path.insert(0, str(DATA))
sys.path.insert(0, str(DATA.parents[2]))
import sot_common  # noqa: E402

from skyyrose.core.catalog_loader import read_catalog_rows  # noqa: E402

OUT = DATA / "collections"
CSS = DATA.parent / "assets/css/design-tokens.css"


def catalog_skus() -> dict[str, set]:
    by: dict[str, set] = {}
    for row in read_catalog_rows():
        by.setdefault(row["collection"], set()).add(row["sku"])
    return by


def walk_resolved(obj: Any, slug: str, hard: list) -> None:
    if isinstance(obj, dict):
        p, r = obj.get("path"), obj.get("resolved")
        if p and "resolved" in obj and (not r or not (sot_common.ASSETS / r).is_file()):
            hard.append(f"{slug}: declared path does not resolve: {p}")
        for v in obj.values():
            walk_resolved(v, slug, hard)
    elif isinstance(obj, list):
        for v in obj:
            walk_resolved(v, slug, hard)


def main() -> int:
    idents = sot_common.load_identity()  # raises IdentityError on bad canon
    cat = catalog_skus()
    hard, warn = [], []

    before = CSS.read_text()
    subprocess.run([sys.executable, str(DATA / "gen-design-tokens.py")], check=True)
    if CSS.read_text() != before:
        CSS.write_text(before)  # verify is net read-only: undo the regen, just report staleness
        hard.append(
            "design-tokens.css collection region is STALE — run gen-design-tokens.py and commit"
        )

    for slug, ident in idents.items():
        fp = OUT / slug / "sot.json"
        if not fp.is_file():
            hard.append(f"{slug}: sot.json missing")
            continue
        sot = json.loads(fp.read_text())
        sot_skus = {p["sku"] for p in sot.get("products", [])}
        expected = cat.get(slug, set())
        if miss := expected - sot_skus:
            hard.append(f"{slug}: catalog SKUs missing from SOT: {sorted(miss)}")
        if extra := sot_skus - expected:
            hard.append(f"{slug}: SOT SKUs not in catalog: {sorted(extra)}")
        for role, font in ident["fonts"].items():
            w = font["woff2"]
            if w and not sot_common.resolve_asset(w):
                hard.append(f"{slug}: font {role} woff2 missing: {w}")
        walk_resolved(sot.get("lockup", {}), slug, hard)
        walk_resolved(sot.get("imagery", {}), slug, hard)
        walk_resolved(sot.get("logos", []), slug, hard)
        for u in sot.get("unresolved_product_images", []):
            warn.append(f"{slug}: {u['sku']} {u['column']} -> {u['path']} (missing file)")
        print(
            f"{slug}: {len(sot_skus)}/{len(expected)} SKUs, "
            f"{len(sot.get('unresolved_product_images', []))} broken product refs"
        )

    if warn:
        print("\nWARNINGS (fix in skyyrose-catalog.csv):")
        for w in warn:
            print("  ⚠ " + w)
    if hard:
        print("\nHARD FAILURES:")
        for h in hard:
            print("  ✗ " + h)
        return 1
    print("\n✓ all per-collection SOT files + tokens verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
