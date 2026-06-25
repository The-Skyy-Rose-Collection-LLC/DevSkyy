#!/usr/bin/env python3
"""Generate per-collection SOT: data/collections/<slug>/sot.json + a global _orphans.json.

Canon source = data/collections/<slug>/identity.json (via sot_common, schema-validated).
The masters (catalog CSV, visual-manifest.json, logo-registry.json) remain authoritative
for their domain; sot.json is a GENERATED VIEW — DO NOT hand-edit it.

Orphans = every image file in the scanned tree registered to NO manifest entry, catalog
product, or logo (naming-independent set-difference). Manifest entries are expanded across
their declared `formats`, so format siblings (avif/png of a webp role) count as registered.

USAGE: python3 build-collection-sot.py [--updated YYYY-MM-DD]
"""

import argparse
import json
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

DATA = Path(__file__).resolve().parent
sys.path.insert(0, str(DATA))
sys.path.insert(0, str(DATA.parents[2]))
import sot_common  # noqa: E402

from skyyrose.core.catalog_loader import bool_col, read_catalog_rows  # noqa: E402

ASSETS = sot_common.ASSETS
IMG_EXTS = sot_common.IMG_EXTS
OUT = DATA / "collections"
TREE_SCAN_DIRS = [
    "branding",
    "images/lockups",
    "branding/vectorized",
    "branding/hero",
    "images/hero-overlays",
    "images/logos",
    "images/lookbook",
    "images/immersive",
    "images",
]


def manifest_entry(entry: Any) -> dict | None:
    if not isinstance(entry, dict):
        return None
    raw = entry.get("path", "")
    return {
        "path": raw,
        "resolved": sot_common.resolve_asset(raw),
        "kind": entry.get("kind"),
        "status": entry.get("status"),
        "notes": entry.get("notes"),
    }


def load_products_by_collection() -> dict[str, list]:
    by_col: dict[str, list] = {}
    for row in read_catalog_rows():
        imgs = {}
        for col in ("image", "front_model_image", "back_image", "back_model_image"):
            v = (row.get(col) or "").strip()
            if v:
                imgs[col] = {"path": v, "resolved": sot_common.resolve_asset(v)}
        dslug = (row.get("dossier_slug") or "").strip()
        by_col.setdefault(row.get("collection", ""), []).append(
            {
                "sku": row["sku"],
                "name": row["name"],
                "price": row.get("price"),
                "is_preorder": bool_col(row, "is_preorder"),
                "published": bool_col(row, "published"),
                "images": imgs,
                "dossier": f"data/dossiers/{dslug}.md" if dslug else None,
                "dossier_exists": bool(dslug) and (DATA / "dossiers" / f"{dslug}.md").is_file(),
            }
        )
    return by_col


def scan_tree() -> set[str]:
    found = set()
    for d in TREE_SCAN_DIRS:
        dd = ASSETS / d
        if not dd.is_dir():
            continue
        for f in dd.iterdir():
            if f.is_file() and f.suffix.lower() in IMG_EXTS:
                found.add(str(f.relative_to(ASSETS)))
    return found


def walk_manifest_entries(obj: Any) -> Iterator[dict]:
    if isinstance(obj, dict):
        if "path" in obj:
            yield obj
        for v in obj.values():
            yield from walk_manifest_entries(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_manifest_entries(v)


def expand_formats(entry: dict) -> set[str]:
    out = set()
    base = entry.get("path", "")
    if not base:
        return out
    for fmt in entry.get("formats", []) or []:
        # Plain extensions ("webp") join with a dot; responsive width tokens
        # ("480w.webp") are dash-suffixed on disk (base-480w.webp).
        sep = "-" if fmt[:1].isdigit() else "."
        cand = f"{base}{sep}{fmt}"
        if (ASSETS / cand).is_file():
            out.add(cand)
    r = sot_common.resolve_asset(base)
    if r:
        out.add(r)
    return out


def registered_files(manifest: Any, logo_reg: Any, products_by_col: dict[str, list]) -> set[str]:
    reg: set[str] = set()
    for entry in walk_manifest_entries(manifest):
        reg |= expand_formats(entry)
    for _lid, lg in logo_reg.get("logos", {}).items():
        for cand in (
            sot_common.resolve_asset(f"images/logos/{lg.get('file', '')}"),
            sot_common.resolve_asset(lg.get("file", "")),
        ):
            if cand:
                reg.add(cand)
    for prods in products_by_col.values():
        for p in prods:
            for im in p["images"].values():
                if im.get("resolved"):
                    reg.add(im["resolved"])
    return reg


def imagery_block(mc: dict) -> dict:
    def lst(key):
        v = mc.get(key)
        return [manifest_entry(e) for e in v] if isinstance(v, list) else []

    return {
        "lockup_display": manifest_entry(mc.get("lockup_display")),
        "lockup_svg_master": manifest_entry(mc.get("lockup_svg_master")),
        "lockup_source_art": manifest_entry(mc.get("lockup_primary")),
        "lockup_alt": manifest_entry(mc.get("lockup_alt")),
        "scene_portrait": next(
            (
                manifest_entry(e)
                for e in mc.get("atmospherics", [])
                if isinstance(e, dict) and e.get("kind") == "collection-portrait"
            ),
            None,
        ),
        "hero_backdrop": (lst("hero_backdrops") or [None])[0],
        "atmospherics": [
            e for e in lst("atmospherics") if e and e.get("kind") != "collection-portrait"
        ],
        "patches": lst("patches"),
        "lettering_alt": lst("lettering_alt"),
        "lockup_parts": lst("lockup_parts"),
        "lookbook": lst("lookbook"),
    }


def logos_for(slug: str, key: str, logo_reg: Any) -> list[dict]:
    out = []
    for lid, lg in logo_reg.get("logos", {}).items():
        lcol = lg.get("collection") or ""
        if key in lcol or slug in lcol:
            out.append(
                {
                    "id": lid,
                    "file": lg.get("file"),
                    "resolved": sot_common.resolve_asset(f"images/logos/{lg.get('file', '')}")
                    or sot_common.resolve_asset(lg.get("file", "")),
                    "primary_color": lg.get("primary_color"),
                    "notes": (lg.get("description") or "")[:160],
                }
            )
    return out


def build_collection(
    slug: str,
    ident: dict,
    manifest: Any,
    logo_reg: Any,
    products: list,
    updated: str,
) -> dict:
    key = ident["key"]
    mc = manifest.get(key, {})
    full = imagery_block(mc)
    lockup = {
        "canonical": sot_common.resolve_asset(ident["lockup"]["ref"]),
        "display_webp": full["lockup_display"],
        "svg_master": full["lockup_svg_master"],
        "source_art": full["lockup_source_art"],
        "alt": full["lockup_alt"],
        "rule": "The lockup IS the collection name; never type-render it.",
    }
    lockup_keys = {"lockup_display", "lockup_svg_master", "lockup_source_art", "lockup_alt"}
    imagery = {k: v for k, v in full.items() if k not in lockup_keys}
    # Resolve imagery.hero from identity.json (collection-specific canonical hub slot).
    ident_hero_raw = (ident.get("imagery") or {}).get("hero")
    if ident_hero_raw:
        h_path = ident_hero_raw.get("path", "")
        imagery["hero"] = {
            "path": h_path,
            "resolved": sot_common.resolve_asset(h_path),
            "kind": ident_hero_raw.get("kind"),
            "status": ident_hero_raw.get("status"),
            "notes": ident_hero_raw.get("notes"),
        }
    else:
        imagery["hero"] = None
    return {
        "_generated_by": "data/build-collection-sot.py — DO NOT EDIT. Fix identity.json / the masters, then regenerate.",
        "_authority": f"Single Source of Truth view for {ident['name']}. Canon = identity.json.",
        "collection": slug,
        "name": ident["name"],
        "updated": updated,
        "story": ident["story"],
        "palette": ident["palette"],
        "fonts": ident["fonts"],
        "masters": {
            "identity": f"data/collections/{slug}/identity.json",
            "products": "data/skyyrose-catalog.csv",
            "imagery": "data/visual-manifest.json",
            "logos": "data/logo-registry.json",
        },
        "lockup": lockup,
        "imagery": imagery,
        "logos": logos_for(slug, key, logo_reg),
        "products": products,
        "unresolved_product_images": [
            {"sku": p["sku"], "column": col, "path": im["path"]}
            for p in products
            for col, im in p["images"].items()
            if not im.get("resolved")
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate per-collection SOT JSON + the global _orphans.json."
    )
    parser.add_argument(
        "--updated",
        default="GENERATED",
        help="Value for each sot.json 'updated' field, e.g. 2026-06-14.",
    )
    updated = parser.parse_args().updated
    idents = sot_common.load_identity()
    manifest = sot_common.load_manifest()
    logo_reg = sot_common.load_logo_registry()
    products_by_col = load_products_by_collection()
    tree = scan_tree()
    reg = registered_files(manifest, logo_reg, products_by_col)

    for slug, ident in idents.items():
        products = products_by_col.get(slug, [])
        sot = build_collection(slug, ident, manifest, logo_reg, products, updated)
        folder = OUT / slug
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "sot.json").write_text(json.dumps(sot, indent=2) + "\n")
        print(
            f"{slug}: {len(products)} products, {len(sot['logos'])} logos "
            f"({len(sot['unresolved_product_images'])} unresolved imgs)"
        )

    known = set()
    for ident in idents.values():
        known |= set(ident.get("known_orphans", []))
    orphans = sorted(tree - reg - known)
    (OUT / "_orphans.json").write_text(
        json.dumps(
            {
                "_note": "Image files in the asset tree registered to NO manifest entry, product, or logo. "
                "Audit before use; add legit non-role files to a collection identity.json known_orphans[].",
                "count": len(orphans),
                "orphans": orphans,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        f"_orphans.json: {len(orphans)} unregistered (of {len(tree)} scanned, {len(reg)} registered)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
