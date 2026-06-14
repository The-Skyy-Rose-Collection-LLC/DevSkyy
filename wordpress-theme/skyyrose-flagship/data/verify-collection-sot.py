#!/usr/bin/env python3
"""Verify the generated per-collection SOT files against reality.

Asserts, for each data/collections/<slug>.json:
  - every catalog SKU for that collection is present (no dropped products)
  - any declared lockup display_webp resolves to a real file
  - no imagery/logo role declares a path that fails to resolve
  - reports (non-fatal) any unresolved product-image columns = broken catalog refs

Whether a collection HAS a display lockup is derived from the SOT itself
(display_webp present and non-null) — the manifest is the single authority, so
this verifier never maintains a parallel list of which collections have one.

Exit 0 = clean. Exit 1 = at least one hard failure. Mirrors verify-visual-manifest.py
so it can run in the same pre-commit / CI gate.
"""

import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent
sys.path.insert(0, str(DATA.parents[2]))
from skyyrose.core.catalog_loader import read_catalog_rows  # noqa: E402
from skyyrose.core.paths import WP_ASSETS_DIR  # noqa: E402

ASSETS = WP_ASSETS_DIR
COLL = DATA / "collections"
SLUGS = ["black-rose", "love-hurts", "signature", "kids-capsule"]


def catalog_skus():
    by_col: dict[str, set] = {}
    for row in read_catalog_rows():
        by_col.setdefault(row["collection"], set()).add(row["sku"])
    return by_col


def resolves(rel: str) -> bool:
    if not rel:
        return False
    rel = rel.removeprefix("assets/")
    return (ASSETS / rel).is_file()


def walk_roles(obj, slug, hard):
    """Every dict carrying a declared path must resolve."""
    if isinstance(obj, dict):
        p, r = obj.get("path"), obj.get("resolved")
        if p and "resolved" in obj and (not r or not resolves(r)):
            hard.append(f"{slug}: role path declared but unresolved: {p}")
        for v in obj.values():
            walk_roles(v, slug, hard)
    elif isinstance(obj, list):
        for v in obj:
            walk_roles(v, slug, hard)


def main():
    cat = catalog_skus()
    hard, warn = [], []
    for slug in SLUGS:
        fp = COLL / f"{slug}.json"
        if not fp.is_file():
            hard.append(f"{slug}: SOT file missing ({fp})")
            continue
        sot = json.loads(fp.read_text())

        # 1. SKU coverage
        sot_skus = {p["sku"] for p in sot.get("products", [])}
        expected = cat.get(slug, set())
        if missing := expected - sot_skus:
            hard.append(f"{slug}: SKUs in catalog but missing from SOT: {sorted(missing)}")
        if extra := sot_skus - expected:
            hard.append(f"{slug}: SKUs in SOT not in catalog: {sorted(extra)}")

        # 2. canonical display lockup — only when the SOT declares one
        disp = (sot.get("lockup", {}).get("display_webp") or {}).get("resolved")
        has_display = disp is not None
        lockup_ok = not has_display or resolves(disp)
        if has_display and not lockup_ok:
            hard.append(f"{slug}: declared display lockup does not resolve ({disp})")

        # 3. every declared role path resolves
        walk_roles(sot.get("lockup", {}), slug, hard)
        walk_roles(sot.get("imagery", {}), slug, hard)
        walk_roles(sot.get("logos", []), slug, hard)

        # 4. broken catalog product refs (non-fatal — a data bug to fix in the CSV)
        for u in sot.get("unresolved_product_images", []):
            warn.append(f"{slug}: {u['sku']} {u['column']} -> {u['path']} (missing file)")

        print(
            f"{slug}: {len(sot_skus)}/{len(expected)} SKUs, "
            f"lockup {'ok' if lockup_ok else 'FAIL'}, "
            f"{len(sot.get('unresolved_product_images', []))} broken product refs"
        )

    if warn:
        print("\nWARNINGS (broken catalog refs — fix in skyyrose-catalog.csv):")
        for w in warn:
            print("  ⚠ " + w)
    if hard:
        print("\nHARD FAILURES:")
        for h in hard:
            print("  ✗ " + h)
        sys.exit(1)
    print("\n✓ all per-collection SOT files verified")


if __name__ == "__main__":
    main()
