#!/usr/bin/env python3
"""Build complete product bundles — assemble every available asset per product.

Each bundle contains ALL reference material for one product:
  - Techflat front + back (split from composites)
  - Real product photos (source/flatlay)
  - Previous renders (model shots, composites, branding)
  - Logo close-ups
  - Material detail shots
  - Vision analysis JSON
  - LOGO_TREATMENTS text spec

Output: data/product-bundles/{sku}/
  ├── techflat-front.jpeg
  ├── techflat-back.jpeg
  ├── real-photo-1.jpg
  ├── real-photo-2.jpg
  ├── logo-ref.png
  ├── model-front.webp (previous render, if good)
  ├── model-back.webp
  ├── composite-front.webp
  ├── branding.webp
  ├── detail-*.jpg
  ├── vision.json
  └── spec.txt (LOGO_TREATMENTS + product metadata)

The generation pipeline reads from these bundles instead of scattered files.
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
DESKTOP_DIR = Path.home() / "Desktop" / "products copy"
VISION_DIR = PROJECT_ROOT / "data" / "product-vision"


def build_bundle(sku: str, product: dict) -> dict:
    """Assemble all available assets for one product into a bundle directory."""
    bundle_path = BUNDLE_DIR / sku
    bundle_path.mkdir(parents=True, exist_ok=True)

    name = product.get("name", sku)
    collection = product.get("collection", "")
    assets = {"sku": sku, "name": name, "collection": collection, "files": {}}

    # 1. Split techflats
    col_map = {
        "black-rose": "black-rose",
        "love-hurts": "love-hurts",
        "signature": "signature",
        "kids-capsule": "kids-capsule",
    }
    col_dir = col_map.get(collection, "")
    if col_dir:
        for pattern in [f"*{sku}*", f"*{sku.replace('-', '*')}*"]:
            for f in (SPLIT_DIR / col_dir).glob(pattern):
                tag = (
                    "techflat-front"
                    if "front" in f.name
                    else "techflat-back"
                    if "back" in f.name
                    else f"techflat-{f.stem}"
                )
                dest = bundle_path / f"{tag}{f.suffix}"
                shutil.copy2(f, dest)
                assets["files"][tag] = str(dest)

    # 2. Product photos from theme
    for f in PRODUCTS_DIR.glob(f"*{sku}*"):
        if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
            tag = _classify_file(f.name)
            dest = bundle_path / f"{tag}{f.suffix}"
            shutil.copy2(f, dest)
            assets["files"][tag] = str(dest)

    # Also check by product name patterns
    slug = product.get("output_slug", sku)
    for f in PRODUCTS_DIR.glob(f"*{slug}*"):
        if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
            tag = _classify_file(f.name)
            if tag not in assets["files"]:
                dest = bundle_path / f"{tag}{f.suffix}"
                shutil.copy2(f, dest)
                assets["files"][tag] = str(dest)

    # 3. Desktop assets (previous renders, model shots, composites)
    if DESKTOP_DIR.exists():
        for f in DESKTOP_DIR.glob(f"{sku}*"):
            if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                tag = _classify_file(f.name)
                if tag not in assets["files"]:
                    dest = bundle_path / f"{tag}{f.suffix}"
                    shutil.copy2(f, dest)
                    assets["files"][tag] = str(dest)

    # 4. Logo reference
    from nano_banana.logo_refs import get_logo_reference

    logo = get_logo_reference(sku, collection)
    if logo and logo.exists():
        dest = bundle_path / f"logo-ref{logo.suffix}"
        shutil.copy2(logo, dest)
        assets["files"]["logo-ref"] = str(dest)

    # 5. Vision analysis
    vision_file = VISION_DIR / f"{sku}-vision.json"
    if vision_file.exists():
        shutil.copy2(vision_file, bundle_path / "vision.json")
        assets["files"]["vision"] = str(bundle_path / "vision.json")

    # 6. Product spec (LOGO_TREATMENTS + metadata)
    from nano_banana.prompts import LOGO_TREATMENTS

    treatment = LOGO_TREATMENTS.get(sku, "No treatment specified")
    spec_text = f"""PRODUCT: {name}
SKU: {sku}
COLLECTION: {collection}

BRANDING SPECIFICATION:
{treatment}

GARMENT TYPE: {product.get("garment_type", "N/A")}
PRICE: ${product.get("price", "N/A")}
EDITION SIZE: {product.get("edition_size", "N/A")}
"""
    (bundle_path / "spec.txt").write_text(spec_text)
    assets["files"]["spec"] = str(bundle_path / "spec.txt")

    # Save bundle manifest
    (bundle_path / "manifest.json").write_text(json.dumps(assets, indent=2))

    return assets


def _classify_file(filename: str) -> str:
    """Classify a file by its content type from its name."""
    name = filename.lower()
    if "composite" in name:
        return (
            "composite-front"
            if "front" in name
            else "composite-back"
            if "back" in name
            else "composite"
        )
    if "model-f" in name:
        return "model-female"
    if "model-m" in name:
        return "model-male"
    if "front-model" in name:
        return "model-front"
    if "back-model" in name:
        return "model-back"
    if "branding" in name:
        return "branding"
    if "render" in name:
        if "front" in name:
            return "render-front"
        if "back" in name:
            return "render-back"
        return "render"
    if "techflat" in name or "tech-flat" in name:
        return "techflat-source"
    if "source" in name:
        return "real-photo"
    if "product" in name:
        return "product-photo"
    if "photo" in name:
        return "photo"
    if "detail" in name or "interior" in name or "lining" in name:
        return "detail"
    if "hoodie" in name and "alt" in name:
        return "alt-angle"
    return f"asset-{Path(filename).stem}"


def main():
    from nano_banana.catalog import load_catalog, load_products

    catalog = load_catalog()
    products = load_products(catalog)

    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Building product bundles for {len(products)} products...")
    print(f"Output: {BUNDLE_DIR}")
    print("=" * 60)

    total_files = 0
    for product in products:
        sku = product["sku"]
        assets = build_bundle(sku, product)
        count = len(assets["files"])
        total_files += count
        print(f"  {sku:20s} {product['name']:40s} {count:3d} files")

    print("=" * 60)
    print(f"COMPLETE: {len(products)} bundles, {total_files} total files")
    print(f"Location: {BUNDLE_DIR}")


if __name__ == "__main__":
    main()
