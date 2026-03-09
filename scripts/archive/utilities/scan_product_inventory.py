#!/usr/bin/env python3
"""Scan all Desktop collection folders and create comprehensive product inventory JSON.

Scans:
1. _Signature Collection_/
2. BLACK_Rose_Extracted/
3. Love_Hurts_Extracted/
4. Signature_Collection_Extracted/

Excludes:
- Non-image files (.pkg, .dmg, .pdf, .mov, .mp4, node-v*, etc.)
- Hidden files (starts with .)
"""

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# Valid image extensions (case-insensitive)
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic"}


def is_product_image(path: Path) -> bool:
    """Check if file is a valid product image.

    Args:
        path: File path to check

    Returns:
        True if valid product image, False otherwise
    """
    # Check extension
    if path.suffix.lower() not in IMAGE_EXTS:
        return False

    # Exclude non-product files
    exclude_patterns = [
        "node-v",
        ".pkg",
        ".dmg",
        ".pdf",
        ".mov",
        ".mp4",
        "installer",
        "certificate",
    ]

    name_lower = path.name.lower()
    for pattern in exclude_patterns:
        if pattern in name_lower:
            return False

    # Exclude hidden files
    return not path.name.startswith(".")


def scan_collection(collection_dir: Path) -> list[dict[str, Any]]:
    """Scan collection directory for product images.

    Args:
        collection_dir: Directory to scan

    Returns:
        List of product dictionaries with metadata
    """
    if not collection_dir.exists():
        print(f"⚠ Directory not found: {collection_dir}")
        return []

    products = []

    # Recursively find all image files
    for item in collection_dir.rglob("*"):
        if item.is_file() and is_product_image(item):
            products.append(
                {
                    "path": str(item),
                    "name": item.stem,
                    "collection": collection_dir.name,
                    "extension": item.suffix.lower(),
                    "size_bytes": item.stat().st_size,
                }
            )

    return products


def main() -> int:
    """Scan all collections and create inventory JSON."""
    desktop = Path.home() / "Desktop"
    project_root = Path(__file__).parent.parent

    # Collection directories to scan
    collection_dirs = [
        desktop / "_Signature Collection_",
        desktop / "BLACK_Rose_Extracted",
        desktop / "Love_Hurts_Extracted",
        desktop / "Signature_Collection_Extracted",
    ]

    print("=" * 60)
    print("SkyyRose Product Inventory Scanner")
    print("=" * 60 + "\n")

    all_products = []

    for collection_dir in collection_dirs:
        products = scan_collection(collection_dir)
        all_products.extend(products)
        print(f"✓ {collection_dir.name:<40} {len(products):>4} products")

    # Save inventory
    output_path = project_root / "datasets" / "product_inventory.json"
    output_path.parent.mkdir(exist_ok=True, parents=True)

    with output_path.open("w") as f:
        json.dump(all_products, f, indent=2)

    # Summary statistics
    print("\n" + "=" * 60)
    print(f"✓ Total products found: {len(all_products)}")
    print(f"✓ Inventory saved: {output_path}")

    # Breakdown by collection
    print("\nBreakdown by collection:")
    counts = Counter(p["collection"] for p in all_products)
    for collection, count in sorted(counts.items()):
        print(f"  - {collection:<40} {count:>4}")

    # Breakdown by extension
    print("\nBreakdown by file type:")
    ext_counts = Counter(p["extension"] for p in all_products)
    for ext, count in sorted(ext_counts.items()):
        print(f"  - {ext:<10} {count:>4}")

    # Total size
    total_size_mb = sum(p["size_bytes"] for p in all_products) / (1024 * 1024)
    print(f"\nTotal size: {total_size_mb:.2f} MB")

    print("=" * 60)

    if len(all_products) == 0:
        print("❌ No products found. Check collection directories.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
