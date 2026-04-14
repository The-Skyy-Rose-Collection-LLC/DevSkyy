#!/usr/bin/env python3
"""Build complete product bundles — assemble every available asset per product.

Each bundle directory is named by PRODUCT NAME (slugified), not SKU.
Only files that verifiably belong to the product are included.

Output: data/product-bundles/{Product Name}/
  ├── techflat-front.jpeg     (from split techflats)
  ├── techflat-back.jpeg
  ├── source-photo.jpg        (real product photo)
  ├── logo-ref.png            (collection logo)
  ├── patch-ref.jpg           (sport-specific patch, jerseys only)
  ├── spec.txt                (LOGO_TREATMENTS + metadata)
  └── manifest.json           (index of all files + SKU mapping)
"""

import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

BUNDLE_DIR = PROJECT_ROOT / "data" / "product-bundles"
SPLIT_DIR = PROJECT_ROOT / "assets" / "techflats" / "split"
PRODUCTS_DIR = (
    PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products"
)
PATCHES_DIR = PROJECT_ROOT / "data" / "patches"


def slugify(name: str) -> str:
    """Convert product name to filesystem-safe directory name."""
    return name.replace("—", "-").replace("'", "").replace('"', "").strip()


def _copy(src: Path, dest: Path, files: dict, tag: str) -> None:
    """Copy src to dest if src exists, record in files dict."""
    if src.exists():
        shutil.copy2(src, dest)
        files[tag] = dest.name


def build_bundle(sku: str, product: dict, source_map: dict) -> dict:
    """Assemble verified assets for one product."""
    from nano_banana.prompts import LOGO_TREATMENTS

    name = product.get("name", sku)
    collection = product.get("collection", "")
    dirname = slugify(name)
    bundle_path = BUNDLE_DIR / dirname
    bundle_path.mkdir(parents=True, exist_ok=True)

    files: dict[str, str] = {}

    # 1. Source images from authoritative source_map
    smap_entry = source_map.get(sku, {})
    front_src = smap_entry.get("front")
    back_src = smap_entry.get("back")

    if front_src and Path(front_src).exists():
        _copy(
            Path(front_src),
            bundle_path / f"techflat-front{Path(front_src).suffix}",
            files,
            "techflat-front",
        )
    if back_src and Path(back_src).exists():
        _copy(
            Path(back_src),
            bundle_path / f"techflat-back{Path(back_src).suffix}",
            files,
            "techflat-back",
        )

    # 2. Real product photo (from CSV source_override)
    output_slug = product.get("output_slug", sku)
    source_override = product.get("source_override")
    if source_override:
        src_path = PRODUCTS_DIR / source_override
        if src_path.exists():
            _copy(src_path, bundle_path / f"source-photo{src_path.suffix}", files, "source-photo")

    # 3. Logo reference
    try:
        from nano_banana.logo_refs import get_logo_reference

        logo = get_logo_reference(sku, collection)
        if logo and logo.exists():
            _copy(logo, bundle_path / f"logo-ref{logo.suffix}", files, "logo-ref")
    except ImportError:
        pass

    # 4. Sport-specific patch (jerseys only)
    patch_map = {
        "br-003": "patch-baseball.jpg",
        "br-003-oakland": "patch-baseball.jpg",
        "br-003-giants": "patch-baseball.jpg",
        "br-003-white": "patch-baseball.jpg",
        "br-008": "patch-nfl-football.jpg",
        "br-009": "patch-nfl-football.jpg",
        "br-010": "patch-nba-basketball.jpg",
        "br-011": "patch-hockey.jpg",
    }
    if sku in patch_map:
        patch_file = PATCHES_DIR / patch_map[sku]
        if patch_file.exists():
            _copy(patch_file, bundle_path / f"patch-ref{patch_file.suffix}", files, "patch-ref")

    # 5. Spec text
    treatment = LOGO_TREATMENTS.get(sku, "No treatment specified")
    spec_text = (
        f"PRODUCT: {name}\n"
        f"SKU: {sku}\n"
        f"COLLECTION: {collection}\n"
        f"\n"
        f"BRANDING SPECIFICATION:\n"
        f"{treatment}\n"
    )
    spec_path = bundle_path / "spec.txt"
    spec_path.write_text(spec_text)
    files["spec"] = "spec.txt"

    # 6. Write manifest
    manifest = {
        "sku": sku,
        "name": name,
        "dirname": dirname,
        "collection": collection,
        "files": files,
    }
    (bundle_path / "manifest.json").write_text(json.dumps(manifest, indent=2))

    return manifest


def verify_bundles() -> list[str]:
    """Verify every bundle has correct files. Returns list of issues."""
    issues = []
    for bundle_dir in sorted(BUNDLE_DIR.iterdir()):
        if not bundle_dir.is_dir():
            continue
        manifest_path = bundle_dir / "manifest.json"
        if not manifest_path.exists():
            issues.append(f"{bundle_dir.name}: NO MANIFEST")
            continue

        manifest = json.loads(manifest_path.read_text())
        sku = manifest.get("sku", "?")
        files = manifest.get("files", {})

        # Check all listed files exist
        for tag, filename in files.items():
            if tag == "spec":
                continue
            full_path = bundle_dir / filename
            if not full_path.exists():
                issues.append(f"{bundle_dir.name} ({sku}): MISSING {tag} -> {filename}")

        # Check no unlisted files (except manifest.json and spec.txt)
        actual_files = {
            f.name for f in bundle_dir.iterdir() if f.name not in ("manifest.json", "spec.txt")
        }
        listed_files = {v for k, v in files.items() if k != "spec"}
        orphans = actual_files - listed_files
        if orphans:
            issues.append(f"{bundle_dir.name} ({sku}): ORPHAN FILES {orphans}")

    return issues


def main():
    from nano_banana.catalog import load_catalog, load_products
    from nano_banana.source_map import get_source_map

    catalog = load_catalog()
    products = load_products(catalog)
    source_map = get_source_map()

    # Convert source_map Path values to strings for consistency
    smap = {}
    for sku, paths in source_map.items():
        smap[sku] = {
            "front": str(paths["front"]) if paths.get("front") else None,
            "back": str(paths["back"]) if paths.get("back") else None,
        }

    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Building product bundles for {len(products)} products...")
    print(f"Output: {BUNDLE_DIR}")
    print("=" * 60)

    for product in products:
        sku = product["sku"]
        info = catalog.get(sku, {})
        product_data = {**product, **info}
        manifest = build_bundle(sku, product_data, smap)
        count = len(manifest["files"])
        print(f"  {manifest['dirname']:50s} ({sku:15s}) {count:2d} files")

    print("=" * 60)

    # Verify
    print("\nVerifying bundles...")
    issues = verify_bundles()
    if issues:
        print(f"\n{len(issues)} ISSUES FOUND:")
        for issue in issues:
            print(f"  !! {issue}")
    else:
        print("ALL BUNDLES VERIFIED — no issues found.")

    print(f"\nDone: {len(products)} bundles in {BUNDLE_DIR}")


if __name__ == "__main__":
    main()
