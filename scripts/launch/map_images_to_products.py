"""Phase 1: Map WordPress media images to product catalog SKUs.

Reads:
  - data/product-catalog.csv (34 products)
  - wordpress/webp_image_mapping.json (74 uploaded WP images)

Outputs:
  - scripts/launch/sku_image_map.json

Algorithm:
  1. Prefix match: br-* → BR_, lh-* → LH_, sg-* → SIG_
  2. Name tokenization + word overlap scoring
  3. Best match per product above confidence threshold
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CATALOG_CSV = ROOT / "data" / "product-catalog.csv"
IMAGE_MAP_JSON = ROOT / "wordpress" / "webp_image_mapping.json"
OUTPUT_JSON = ROOT / "scripts" / "launch" / "sku_image_map.json"

# SKU prefix → image key prefix
PREFIX_MAP = {
    "br": "BR",
    "lh": "LH",
    "sg": "SIG",
    "kids": "KIDS",
}

# Known manual overrides (from data analysis)
MANUAL_OVERRIDES: dict[str, str] = {
    # Black Rose
    "br-001": "BR_000_20230616_170635_main",
    "br-002": "BR_003_20230616_170635_main",
    "br-003": "BR_266AD7B0_88A6_4489_AA58_AB72A5_main",
    "br-003-oakland": "BR_5A8946B1_B51F_4144_BCBB_F02846_main",
    "br-003-giants": "BR_DEC_18_2023_6_09_21_PM_2_main",
    "br-003-white": "BR_WOMENS_BLACK_ROSE_HOODED_DRESS_main",
    "br-004": "BR_007_20230616_170635_1_main",
    "br-005": "BR_THE_BLACK_ROSE_SHERPA_main",
    "br-006": "BR_BLACK_ROSE_SHERPA_main",
    "br-007": "LH_003_20221110_200039_main",
    "br-008": "LH_PROD_0D142A63_main",
    "br-009": "LH_PROD_309E1DFA_main",
    "br-010": "LH_PROD_DE5753FB_main",
    "br-011": "LH_PROD_8E0B9D57_main",
    # Love Hurts
    "lh-002": "LH_SINCERELY_HEARTED_JOGGERS_BLAC_main",
    "lh-003": "LH_PROD_2B35D56E_main",
    "lh-004": "LH_MEN_WINDBREAKER_JACKET_1_main",
    "lh-006": "LH_FANNIE_PACK_FRONT_2_main",
    # Signature
    "sg-001": "SIG_THE_SIGNATURE_SHORTS_main",
    "sg-002": "SIG_STAY_GOLDEN_TEE_main",
    "sg-003": "SIG_SIGNATURE_SHORTS1_main",
    "sg-004": "SIG_HOODIE_main",
    "sg-005": "SIG_000_20231221_222005_main",
    "sg-006": "LH_THE_MINT_AND_LAVENDER_HOODIE_main",
    "sg-007": "SIG_LAVENDER_ROSE_BEANIE_main",
    "sg-009": "SIG_THE_SHERPA_3_main",
    "sg-011": "SIG_ORIGINAL_LABEL_TEE_WHITE_main",
    "sg-012": "SIG_ORIGINAL_LABEL_TEE_ORCHID_main",
    "sg-013": "SIG_THE_PINK_SMOKE_CREWNECK_main",
    "sg-014": "SIG_THE_MINT_N_LAVENDER_WOMEN_HOOD_main",
    # Kids
    "kids-001": "SIG_SIGNATURE_COLLECTION_RED_ROSE__main",
    "kids-002": "SIG_PROD_FCCB8B16_main",
}

# Product name keywords → image key keywords mapping
KEYWORD_MAP: dict[str, list[str]] = {
    "crewneck": ["CREWNECK"],
    "joggers": ["JOGGERS", "SINCERELY_HEARTED_JOGGERS"],
    "hoodie": ["HOODIE", "HOODED"],
    "jersey": ["JERSEY", "BEAUTIFUL"],
    "sherpa": ["SHERPA"],
    "shorts": ["SHORTS", "BASKETBALL"],
    "beanie": ["BEANIE", "ROSE_BEANIE"],
    "varsity": ["VARSITY"],
    "fannie": ["FANNIE", "FANNIE_PACK"],
    "tee": ["TEE", "LABEL_TEE"],
    "shirt": ["TEE", "SHIRT"],
    "sweatpants": ["SWEATPANTS"],
    "jacket": ["JACKET", "SHERPA", "WINDBREAKER"],
    "dress": ["DRESS", "HOODED_DRESS"],
    "set": ["SET", "COLORBLOCK"],
}


def tokenize(text: str) -> set[str]:
    """Normalize and tokenize a string into comparable words."""
    text = text.upper()
    text = re.sub(r"[^A-Z0-9]", " ", text)
    return {w for w in text.split() if len(w) > 2}


def score_match(product_name: str, product_slug: str, image_key: str) -> float:
    """Score how well an image key matches a product.

    Returns a float 0.0-1.0 representing match confidence.
    """
    product_tokens = tokenize(product_name) | tokenize(product_slug)
    image_tokens = tokenize(image_key)

    if not product_tokens or not image_tokens:
        return 0.0

    # Word overlap
    overlap = product_tokens & image_tokens
    if not overlap:
        # Try keyword expansion
        for keyword, expansions in KEYWORD_MAP.items():
            if keyword.upper() in product_tokens:
                for exp in expansions:
                    if exp in image_key.upper():
                        overlap.add(exp)

    if not overlap:
        return 0.0

    # Score = overlap / max(both sets) — weighted toward product tokens
    score = len(overlap) / max(len(product_tokens), 1)
    return min(score, 1.0)


def map_images() -> dict[str, dict]:
    """Build SKU → image mapping."""
    # Load catalog
    products: list[dict] = []
    with open(CATALOG_CSV, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append(row)

    # Load image mapping
    with open(IMAGE_MAP_JSON) as f:
        images: dict[str, dict] = json.load(f)

    print(f"Catalog: {len(products)} products")
    print(f"Images:  {len(images)} uploaded to WordPress")
    print()

    result: dict[str, dict] = {}
    unmatched: list[str] = []
    used_images: set[str] = set()

    for product in products:
        sku = product["sku"].strip().strip('"')
        name = product["name"].strip().strip('"')
        slug = product.get("render_output_slug", "").strip()
        collection_slug = product.get("collection_slug", "").strip()

        # Check manual overrides first
        if sku in MANUAL_OVERRIDES:
            override_key = MANUAL_OVERRIDES[sku]
            if override_key in images:
                img = images[override_key]
                result[sku] = {
                    "image_id": img["fallback_id"],
                    "image_url": img["fallback_url"],
                    "webp_id": img["webp_id"],
                    "webp_url": img["webp_url"],
                    "match_key": override_key,
                    "confidence": 1.0,
                    "method": "manual_override",
                }
                used_images.add(override_key)
                print(f"  ✓ {sku:18s} → {override_key:45s} [MANUAL]")
                continue

        # Determine expected prefix
        sku_prefix = sku.split("-")[0]
        img_prefix = PREFIX_MAP.get(sku_prefix, "")

        # Filter images by prefix
        candidates = {
            k: v for k, v in images.items() if k.startswith(img_prefix) and k not in used_images
        }

        if not candidates:
            # Try all images as fallback
            candidates = {k: v for k, v in images.items() if k not in used_images}

        # Score each candidate
        best_key = ""
        best_score = 0.0
        for img_key in candidates:
            s = score_match(name, slug, img_key)
            if s > best_score:
                best_score = s
                best_key = img_key

        if best_score >= 0.15 and best_key:
            img = images[best_key]
            result[sku] = {
                "image_id": img["fallback_id"],
                "image_url": img["fallback_url"],
                "webp_id": img["webp_id"],
                "webp_url": img["webp_url"],
                "match_key": best_key,
                "confidence": round(best_score, 3),
                "method": "auto_match",
            }
            used_images.add(best_key)
            conf_label = "HIGH" if best_score >= 0.4 else "MED" if best_score >= 0.25 else "LOW"
            print(f"  ✓ {sku:18s} → {best_key:45s} [{conf_label} {best_score:.2f}]")
        else:
            unmatched.append(sku)
            print(f"  ✗ {sku:18s} → NO MATCH (best: {best_key} @ {best_score:.2f})")

    # Save output
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w") as f:
        json.dump(result, f, indent=2)

    # Summary
    print()
    print("=" * 60)
    print(f"MATCHED:   {len(result)}/{len(products)} products")
    print(f"UNMATCHED: {len(unmatched)} — {', '.join(unmatched)}")
    print(f"OUTPUT:    {OUTPUT_JSON}")
    print("=" * 60)

    return result


if __name__ == "__main__":
    map_images()
