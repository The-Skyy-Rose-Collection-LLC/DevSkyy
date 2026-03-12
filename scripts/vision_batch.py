#!/usr/bin/env python3
"""
Vision Batch — Run garment analysis on all products, output to JSON.

Runs Gemini Flash vision on every product's source image, then writes
the results to skyyrose/assets/data/garment-analysis.json.

This is step 1 of the render pipeline:
  1. vision_batch.py  → garment-analysis.json (THIS SCRIPT)
  2. nano-banana-vton.py --all  → front/back model renders

Usage:
    python scripts/vision_batch.py                  # All products
    python scripts/vision_batch.py --sku br-006     # Single product
    python scripts/vision_batch.py --collection black-rose  # One collection
    python scripts/vision_batch.py --dry-run        # Show what would run
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# Load environment
_ROOT = Path(__file__).parent.parent
_ENV_FILES = [_ROOT / ".env", _ROOT / ".env.hf", _ROOT / "gemini" / ".env"]
for env_file in _ENV_FILES:
    if env_file.exists():
        load_dotenv(env_file, override=True)

# Import product catalog from nano-banana (hyphenated filename needs importlib)
import importlib.util

_nb_spec = importlib.util.spec_from_file_location(
    "nano_banana_vton", _ROOT / "scripts" / "nano-banana-vton.py"
)
_nb_mod = importlib.util.module_from_spec(_nb_spec)
_nb_spec.loader.exec_module(_nb_mod)
PRODUCT_CATALOG = _nb_mod.PRODUCT_CATALOG
ACCESSORY_SKUS = _nb_mod.ACCESSORY_SKUS

# Paths
PRODUCTS_DIR = _ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products"
GA_OUTPUT = _ROOT / "skyyrose" / "assets" / "data" / "garment-analysis.json"
SOURCE_DIR = _ROOT / "skyyrose" / "assets" / "images" / "source-products"

# ---------------------------------------------------------------------------
# Source image resolution (same logic as nano-banana find_source_image)
# ---------------------------------------------------------------------------


def find_source_image(sku: str) -> Path | None:
    """Find the best source image for a product."""
    info = PRODUCT_CATALOG.get(sku, {})

    # Check explicit source override
    if "source_override" in info:
        for base_dir in [PRODUCTS_DIR, SOURCE_DIR]:
            override_path = base_dir / info["source_override"]
            if override_path.exists():
                return override_path

    # Fall back to output_slug-based glob
    slug = info.get("output_slug", sku)
    for base_dir in [PRODUCTS_DIR, SOURCE_DIR]:
        for ext in (".webp", ".jpg", ".jpeg", ".png"):
            candidates = list(base_dir.glob(f"{slug}*{ext}"))
            source_only = [
                p
                for p in candidates
                if "-front-model" not in p.stem
                and "-back-model" not in p.stem
                and "-branding" not in p.stem
            ]
            if source_only:
                source_only.sort(
                    key=lambda p: (
                        "source" not in p.stem
                        and "techflat" not in p.stem
                        and "product" not in p.stem,
                        len(p.name),
                    )
                )
                return source_only[0]

    # Last resort: use existing front-model render
    slug = info.get("output_slug", sku)
    for base_dir in [PRODUCTS_DIR, SOURCE_DIR]:
        front = base_dir / f"{slug}-front-model.webp"
        if front.exists():
            return front

    return None


# ---------------------------------------------------------------------------
# Vision analysis
# ---------------------------------------------------------------------------


def analyze_product(sku: str, image_path: Path, client) -> dict:
    """Run Gemini Flash vision analysis on a product image."""
    info = PRODUCT_CATALOG.get(sku, {})
    name = info.get("name", sku)
    collection = info.get("collection", "unknown")

    # Read and encode image
    image_bytes = image_path.read_bytes()
    mime = "image/webp" if image_path.suffix == ".webp" else "image/jpeg"

    prompt = f"""You are a luxury fashion garment analysis AI for SkyyRose.

PRODUCT: {name}
SKU: {sku}
COLLECTION: {collection}

Analyze this product image with EXTREME technical detail:

1. **GARMENT TYPE** — Exact type (hoodie, jersey, joggers, jacket, etc.), silhouette, cut
2. **BASE COLOR** — Primary color with hex approximation
3. **SECONDARY COLORS** — All accent colors with hex values
4. **FIT** — Relaxed, oversized, tailored, athletic, etc.
5. **GRAPHICS** — Every graphic element: location, content, style, colors, size relative to garment
6. **TEXT** — All readable text: content, font style, color, placement, size
7. **LOGOS & BRANDING** — Every logo/label: location, technique (embroidered/printed/patch/woven), colors
8. **HARDWARE** — Buttons, zippers, drawstrings, grommets — material, color, placement
9. **FABRIC TEXTURE** — Material type, weight, finish (matte/glossy/heathered), texture (smooth/ribbed/mesh)
10. **SPECIAL DETAILS** — Collar type, cuffs, hem, pockets, linings, trim, panels, contrast stitching

Be EXTREMELY specific. This spec will be used to generate AI model shots — every detail matters."""

    from google.genai import types as genai_types

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            prompt,
            genai_types.Part(inline_data=genai_types.Blob(mime_type=mime, data=image_bytes)),
        ],
    )

    return {
        "id": sku,
        "name": name,
        "collection": collection.upper().replace("-", " "),
        "refs": [str(image_path.relative_to(_ROOT))],
        "setting": _collection_setting(collection),
        "garmentAnalysis": response.text,
    }


def _collection_setting(collection: str) -> str:
    """Default scene setting per collection."""
    settings = {
        "black-rose": "Moonlit gothic garden, wrought-iron gates, rose vines, atmospheric fog",
        "love-hurts": "Gothic cathedral interior, crimson lighting, stone arches, rose petals",
        "signature": "Golden Gate Bridge at golden hour, Bay Area skyline, warm light",
        "kids-capsule": "Bright playful studio, colorful backdrop, warm natural light",
    }
    return settings.get(collection, "Studio lighting, neutral backdrop")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Vision batch — garment analysis for all products")
    parser.add_argument("--sku", help="Analyze single SKU")
    parser.add_argument(
        "--collection", help="Analyze one collection (black-rose, love-hurts, signature)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would run without calling APIs"
    )
    parser.add_argument(
        "--delay", type=int, default=3, help="Seconds between API calls (default: 3)"
    )
    args = parser.parse_args()

    # Validate API key
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key and not args.dry_run:
        print("Missing GOOGLE_API_KEY or GEMINI_API_KEY", file=sys.stderr)
        sys.exit(1)

    # Build SKU list
    if args.sku:
        skus = [args.sku]
    elif args.collection:
        skus = [
            sku
            for sku, info in sorted(PRODUCT_CATALOG.items())
            if info.get("collection") == args.collection
        ]
    else:
        skus = sorted(PRODUCT_CATALOG.keys())

    # Resolve source images
    work = []
    for sku in skus:
        src = find_source_image(sku)
        work.append((sku, src))

    # Show plan
    print(f"\n{'=' * 60}")
    print("  SkyyRose Vision Batch — Garment Analysis")
    print(f"  Products: {len(work)}  |  Output: {GA_OUTPUT.name}")
    print(f"{'=' * 60}\n")

    for sku, src in work:
        status = f"  {src.name}" if src else "  NO SOURCE IMAGE"
        print(f"  {sku:15s} {status}")

    no_source = [sku for sku, src in work if src is None]
    if no_source:
        print(f"\n  ⚠ {len(no_source)} products have no source image — will be skipped")

    if args.dry_run:
        print("\n  [DRY RUN] No API calls made.")
        return

    # Initialize Gemini client
    from google import genai as google_genai

    client = google_genai.Client(api_key=api_key)

    # Load existing garment analysis (preserve products we're not re-analyzing)
    if GA_OUTPUT.exists():
        ga = json.loads(GA_OUTPUT.read_text(encoding="utf-8"))
    else:
        ga = {"_meta": {}, "products": {}}

    # Run vision on each product
    total = len([w for w in work if w[1] is not None])
    done = 0
    errors = []

    for sku, src in work:
        if src is None:
            continue

        done += 1
        print(f"\n[{done}/{total}] {sku} — {src.name}")

        try:
            result = analyze_product(sku, src, client)
            ga["products"][sku] = result
            chars = len(result["garmentAnalysis"])
            print(f"  ✓ {chars:,} chars of analysis")
        except Exception as exc:
            print(f"  ✗ ERROR: {exc}")
            errors.append((sku, str(exc)))

        if done < total:
            time.sleep(args.delay)

    # Update meta
    ga["_meta"][
        "description"
    ] = "SkyyRose garment analysis catalog. Generated by Gemini 2.5 Flash vision."
    ga["_meta"]["models_used"] = {"analysis": "gemini-2.5-flash"}
    ga["_meta"]["total_products"] = len(ga["products"])

    # Write output
    GA_OUTPUT.write_text(json.dumps(ga, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\n{'=' * 60}")
    print(f"  ✅ Complete: {done - len(errors)}/{total} analyzed")
    if errors:
        print(f"  ❌ Errors: {len(errors)}")
        for sku, err in errors:
            print(f"     {sku}: {err}")
    print(f"  📄 Output: {GA_OUTPUT}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
