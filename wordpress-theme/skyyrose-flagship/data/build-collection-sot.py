#!/usr/bin/env python3
"""Generate per-collection Source-Of-Truth files: data/collections/<slug>.json.

WHY THIS EXISTS
---------------
A collection's assets were spread across three masters that don't cross-check:
  - skyyrose-catalog.csv   (products + their imagery)
  - visual-manifest.json   (non-product imagery: lockups, scenes, lookbook, hero)
  - logo-registry.json     (logos, monograms, per-SKU branding placements)
...plus many near-duplicate lockup/logo files in the asset tree with no authority.
Answering "what is Black Rose's lockup?" meant crossing 3 files and guessing among
duplicates -> repeated wrong-file pick-ups. This script collapses all of that into
ONE verified file per collection.

CONTRACT
--------
- The three masters remain authoritative for their domain. This is a GENERATED VIEW.
- DO NOT hand-edit data/collections/*.json. Fix the master, then regenerate.
- Every emitted path is existence-checked (with format-sibling fallback). A role that
  cannot resolve to a real file is emitted as null, never guessed.
- `other_collection_files` lists every other tree file that name-matches the collection
  but is NOT a chosen role -> the trap list. Treat as "do not use unless promoted here."

USAGE: python3 build-collection-sot.py [--updated YYYY-MM-DD]
"""

import json
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent
# Single path authority + canonical catalog reader (feedback_single_asset_tree /
# feedback_canonical_sources_only): never hardcode the asset root or hand-roll CSV reads.
sys.path.insert(0, str(DATA.parents[2]))
from skyyrose.core.catalog_loader import bool_col, read_catalog_rows  # noqa: E402
from skyyrose.core.paths import WP_ASSETS_DIR  # noqa: E402

ASSETS = WP_ASSETS_DIR
OUT = DATA / "collections"
MANIFEST = DATA / "visual-manifest.json"
LOGO_REG = DATA / "logo-registry.json"

# accent + display_font mirror assets/css/design-tokens.css [data-collection="<slug>"]
# (--skyyrose-accent / --skyyrose-font-display) — keep in sync if those tokens change.
COLLECTIONS = {
    "black-rose": {
        "key": "black_rose",
        "name": "Black Rose",
        "accent": "#C0C0C0",
        "display_font": "Cinzel",
        "match": r"black[-_ ]?rose|^br-|black-roses|br-brand|br-patch",
    },
    "love-hurts": {
        "key": "love_hurts",
        "name": "Love Hurts",
        "accent": "#DC143C",
        "display_font": "Playfair Display",
        "match": r"love[-_ ]?hurts|lh-logo|love-lettering|hurts-lettering|red-roses|heart-rose",
    },
    "signature": {
        "key": "signature",
        "name": "Signature",
        "accent": "#D4AF37",
        "display_font": "Playfair Display",
        "match": r"signature|sig-brand|rose-gold-rose|skyy-rose",
    },
    "kids-capsule": {
        "key": "kids_capsule",
        "name": "Kids Capsule",
        "accent": "#B76E79",
        "display_font": "Playfair Display",
        "match": r"kids-|kids-capsule|kid-black-rose",
    },
}
BODY_FONT = "Cormorant Garamond"

# Display + vector lockups are NOT hardcoded here — they are read from
# visual-manifest.json (lockup_display / lockup_svg_master per collection),
# which is the canonical imagery authority. Register a new lockup there.

IMG_EXTS = (".webp", ".avif", ".png", ".jpg", ".jpeg", ".svg", ".mp4", ".webm")
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


def exists(rel: str) -> str | None:
    """Resolve an assets-relative path (possibly extension-less) to a real file, else None."""
    if not rel:
        return None
    rel = rel.replace("assets/", "", 1) if rel.startswith("assets/") else rel
    p = ASSETS / rel
    if p.is_file():
        return rel
    # Extension-less manifest path: prefer an exact-extension sibling (base.ext),
    # then fall back to a "formats" sibling (base-480w.webp etc.).
    parent = p.parent
    if parent.is_dir():
        for pat in (p.name + ".*", p.name + "*"):
            for f in sorted(parent.glob(pat)):
                if f.is_file() and f.suffix.lower() in IMG_EXTS:
                    return str(f.relative_to(ASSETS))
    return None


def manifest_entry(entry):
    """One visual-manifest asset dict -> {path, resolved, kind, status, notes}."""
    if not isinstance(entry, dict):
        return None
    raw = entry.get("path", "")
    return {
        "path": raw,
        "resolved": exists(raw),
        "kind": entry.get("kind"),
        "status": entry.get("status"),
        "notes": entry.get("notes"),
    }


def load_products_by_collection():
    """Partition the canonical catalog into {collection: [product dict]} in one read."""
    by_col: dict[str, list] = {}
    for row in read_catalog_rows():
        imgs = {}
        for col in ("image", "front_model_image", "back_image", "back_model_image"):
            v = (row.get(col) or "").strip()
            if v:
                imgs[col] = {"path": v, "resolved": exists(v)}
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


def scan_tree():
    """All image files under the scan dirs, once, as a set of assets-relative paths."""
    found = set()
    for d in TREE_SCAN_DIRS:
        dd = ASSETS / d
        if not dd.is_dir():
            continue
        for f in dd.iterdir():
            if f.is_file() and f.suffix.lower() in IMG_EXTS:
                found.add(str(f.relative_to(ASSETS)))
    return found


def imagery_lockup(imagery):
    """Group the lockup roles into one block (the #1 source of mix-ups)."""
    return {
        "display_webp": imagery["lockup_display"],
        "svg_master": imagery["lockup_svg_master"],
        "source_art": imagery["lockup_source_art"],
        "alt": imagery["lockup_alt"],
        "rule": "Use display_webp for web/homepage. svg_master only when infinite scale/recolor needed. source_art is the raw master the others derive from — not for direct placement. The lockup IS the collection name; never type-render it.",
    }


def collect_resolved(obj, into):
    """Recursively add every 'resolved' value found in obj to the set `into`."""
    if isinstance(obj, dict):
        if obj.get("resolved"):
            into.add(obj["resolved"])
        for v in obj.values():
            collect_resolved(v, into)
    elif isinstance(obj, list):
        for v in obj:
            collect_resolved(v, into)


def build_collection(slug, meta, manifest, logo_reg, products, all_tree, updated):
    mkey = meta["key"]
    mc = manifest.get(mkey, {})

    logos = []
    for lid, l in logo_reg.get("logos", {}).items():
        lcol = l.get("collection") or ""
        if mkey in lcol or slug in lcol:
            logos.append(
                {
                    "id": lid,
                    "file": l.get("file"),
                    "resolved": exists(f"images/logos/{l.get('file', '')}")
                    or exists(l.get("file", "")),
                    "primary_color": l.get("primary_color"),
                    "notes": (l.get("description") or "")[:160],
                }
            )

    def lst(key):
        v = mc.get(key)
        return [manifest_entry(e) for e in v] if isinstance(v, list) else []

    imagery = {
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

    chosen: set[str] = set()
    collect_resolved(imagery, chosen)
    collect_resolved(logos, chosen)
    collect_resolved(products, chosen)
    rx = re.compile(meta["match"], re.IGNORECASE)
    not_in_sot = sorted(f for f in all_tree if rx.search(Path(f).name) and f not in chosen)

    return {
        "_generated_by": "data/build-collection-sot.py — DO NOT EDIT BY HAND. Fix the master (catalog.csv / visual-manifest.json / logo-registry.json) and regenerate.",
        "_authority": f"Single Source of Truth for the {meta['name']} collection. Resolves products + imagery + logos to ONE verified file per role. Every 'resolved' path is existence-checked.",
        "collection": slug,
        "name": meta["name"],
        "updated": updated,
        "palette": {"accent": meta["accent"], "dark": "#0A0A0A", "rose_gold": "#B76E79"},
        "fonts": {"display": meta["display_font"], "body": BODY_FONT},
        "masters": {
            "products": "data/skyyrose-catalog.csv",
            "imagery": "data/visual-manifest.json",
            "logos": "data/logo-registry.json",
        },
        "lockup": imagery_lockup(imagery),
        "imagery": {k: v for k, v in imagery.items() if not k.startswith("lockup")},
        "logos": logos,
        "products": products,
        "unresolved_product_images": [
            {"sku": p["sku"], "column": col, "path": im["path"]}
            for p in products
            for col, im in p["images"].items()
            if not im.get("resolved")
        ],
        "other_collection_files": {
            "_note": "Files in the asset tree whose name matches this collection but which are NOT assigned a canonical role above. Audit before use: some are legitimate (nav/thumb logos, format siblings), some are duplicates/superseded source art to retire. Never grab one of these for a role the SOT already fills.",
            "files": not_in_sot,
        },
    }


def main():
    updated = "GENERATED"
    if "--updated" in sys.argv:
        updated = sys.argv[sys.argv.index("--updated") + 1]
    manifest = json.load(open(MANIFEST))
    logo_reg = json.load(open(LOGO_REG))
    products_by_col = load_products_by_collection()
    all_tree = scan_tree()
    OUT.mkdir(exist_ok=True)

    for slug, meta in COLLECTIONS.items():
        products = products_by_col.get(slug, [])
        sot = build_collection(slug, meta, manifest, logo_reg, products, all_tree, updated)
        out = OUT / f"{slug}.json"
        out.write_text(json.dumps(sot, indent=2) + "\n")
        n_unres = len(sot["unresolved_product_images"])
        print(
            f"{slug}: {len(products)} products ({n_unres} unresolved imgs), "
            f"{len(sot['logos'])} logos, {len(sot['other_collection_files']['files'])} trap files "
            f"-> {out.relative_to(DATA.parent.parent)}"
        )


if __name__ == "__main__":
    main()
