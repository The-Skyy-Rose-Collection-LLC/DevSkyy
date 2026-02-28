#!/usr/bin/env python3
"""
Nano Banana 2 — SkyyRose Product Image Generator

Uses Gemini's image generation (gemini-2.5-flash-preview-image-generation)
to create front + back model shots for all SkyyRose products.

Usage:
    source .venv-imagery/bin/activate
    python scripts/nano-banana-vton.py --dry-run
    python scripts/nano-banana-vton.py --sku br-001
    python scripts/nano-banana-vton.py --step all
"""

import argparse
import io
import json
import logging
import os
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("nano-banana-vton")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = (
    PROJECT_ROOT
    / "wordpress-theme"
    / "skyyrose-flagship"
    / "assets"
    / "images"
    / "products"
)
CANONICAL_MAP = (
    PROJECT_ROOT
    / "wordpress-theme"
    / "skyyrose-flagship"
    / "data"
    / "canonical-images.json"
)

MODEL_ID = "gemini-2.5-flash-preview-image-generation"
MIN_FILE_SIZE_KB = 50
MAX_RETRIES = 3
RETRY_DELAY_SEC = 5

# -- Product catalog ---------------------------------------------------------

PRODUCT_CATALOG = {
    "br-001": {"name": "BLACK Rose Crewneck", "collection": "black-rose"},
    "br-002": {"name": "BLACK Rose Joggers", "collection": "black-rose"},
    "br-003": {"name": "BLACK is Beautiful Jersey", "collection": "black-rose"},
    "br-004": {"name": "BLACK Rose Hoodie", "collection": "black-rose"},
    "br-005": {"name": "BLACK Rose Hoodie — Signature Edition", "collection": "black-rose"},
    "br-006": {"name": "BLACK Rose Sherpa Jacket", "collection": "black-rose"},
    "br-007": {"name": "BLACK Rose x Love Hurts Basketball Shorts", "collection": "black-rose"},
    "br-008": {"name": "Women's BLACK Rose Hooded Dress", "collection": "black-rose"},
    "lh-001": {"name": "The Fannie Pack", "collection": "love-hurts"},
    "lh-002": {"name": "Love Hurts Joggers", "collection": "love-hurts"},
    "lh-003": {"name": "Love Hurts Basketball Shorts", "collection": "love-hurts"},
    "lh-004": {"name": "Love Hurts Varsity Jacket", "collection": "love-hurts"},
    "lh-005": {"name": "Love Hurts Windbreaker", "collection": "love-hurts"},
    "sg-001": {"name": "The Bay Set", "collection": "signature"},
    "sg-002": {"name": "Stay Golden Tee", "collection": "signature"},
    "sg-003": {"name": "The Signature Tee (Orchid)", "collection": "signature"},
    "sg-004": {"name": "The Signature Hoodie", "collection": "signature"},
    "sg-005": {"name": "Stay Golden Tee (Classic)", "collection": "signature"},
    "sg-006": {"name": "Mint & Lavender Hoodie", "collection": "signature"},
    "sg-007": {"name": "The Signature Beanie", "collection": "signature"},
    "sg-008": {"name": "Signature Crop Hoodie", "collection": "signature"},
    "sg-009": {"name": "The Sherpa Jacket", "collection": "signature"},
    "sg-010": {"name": "The Bridge Series Shorts", "collection": "signature"},
    "sg-011": {"name": "Original Label Tee (White)", "collection": "signature"},
    "sg-012": {"name": "Original Label Tee (Orchid)", "collection": "signature"},
}

# SKUs that are accessories (not wearable on a model)
ACCESSORY_SKUS = {"lh-001", "sg-007"}


def find_source_image(sku: str) -> Path | None:
    """Find the best available source image for a SKU."""
    # Try canonical names first (from canonical-images.json)
    candidates = list(PRODUCTS_DIR.glob(f"{sku}*.webp")) + list(
        PRODUCTS_DIR.glob(f"{sku}*.jpg")
    )
    # Filter out model shots and back images — we want flat-lay/product only
    source_candidates = [
        p
        for p in candidates
        if "-front-model" not in p.stem
        and "-back-model" not in p.stem
        and "-back" not in p.stem
    ]
    if not source_candidates:
        return None
    # Prefer .webp over .jpg, then prefer shorter filenames (less likely to be variants)
    source_candidates.sort(key=lambda p: (p.suffix != ".webp", len(p.name)))
    return source_candidates[0]


def load_products(sku_filter: str | None = None) -> list[dict]:
    """Load product catalog, resolve source images, apply filter."""
    products = []
    skus = [sku_filter] if sku_filter else sorted(PRODUCT_CATALOG.keys())

    for sku in skus:
        if sku not in PRODUCT_CATALOG:
            log.error("Unknown SKU: %s", sku)
            continue

        info = PRODUCT_CATALOG[sku]
        src = find_source_image(sku)
        is_accessory = sku in ACCESSORY_SKUS

        products.append(
            {
                "sku": sku,
                "name": info["name"],
                "collection": info["collection"],
                "source_image": src,
                "is_accessory": is_accessory,
            }
        )

    return products


# -- Prompt templates --------------------------------------------------------

FRONT_PROMPT = (
    "A professional fashion model wearing this EXACT garment, front-facing, "
    "full body shot, luxury streetwear editorial photography, studio lighting, "
    "clean white background. The garment must be 100% identical to the "
    "reference image — same colors, same cut, same details, same logo "
    "placement, same fabric texture. The model should have a confident, "
    "editorial pose. High fashion photography style."
)

BACK_PROMPT = (
    "A professional fashion model wearing this EXACT garment, BACK-FACING "
    "(showing the back of the garment), full body shot, luxury streetwear "
    "editorial photography, studio lighting, clean white background. The "
    "garment must be 100% identical to the reference — same colors, same "
    "cut, same back details, same logo placement. The model is turned away "
    "from camera showing the back of the outfit. High fashion photography."
)

ENHANCED_PROMPT_SUFFIX = (
    " CRITICAL: The garment in the output MUST be pixel-accurate to the "
    "reference. Do not change any colors, patterns, logos, or design "
    "elements. This is a luxury fashion brand — accuracy is everything."
)

ACCESSORY_PROMPT = (
    "A professional fashion model wearing/holding this EXACT accessory, "
    "front-facing, luxury streetwear editorial photography, studio lighting, "
    "clean white background. The accessory must be 100% identical to the "
    "reference image. High fashion photography style."
)


# -- Image generation --------------------------------------------------------


def generate_model_shot(
    client,
    source_image_path: Path,
    prompt: str,
    attempt: int = 1,
) -> bytes | None:
    """Generate a single model shot using Gemini image generation.

    Returns WebP image bytes on success, None on failure.
    """
    from google.genai import types
    from PIL import Image

    src_img = Image.open(source_image_path)

    # Add enhanced prompt on retries
    full_prompt = prompt
    if attempt > 1:
        full_prompt += ENHANCED_PROMPT_SUFFIX

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[full_prompt, src_img],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="3:4",
                    person_generation="allow_all",
                ),
            ),
        )
    except Exception as exc:
        log.error("API call failed (attempt %d): %s", attempt, exc)
        return None

    # Extract image from response
    if not response or not response.parts:
        log.warning("Empty response from API (attempt %d)", attempt)
        return None

    for part in response.parts:
        if part.inline_data:
            img = part.as_image()
            buf = io.BytesIO()
            img.save(buf, format="WEBP", quality=90)
            return buf.getvalue()

    log.warning("No image in response parts (attempt %d)", attempt)
    return None


def quality_gate(image_bytes: bytes, sku: str, view: str) -> bool:
    """Check if generated image passes quality requirements."""
    size_kb = len(image_bytes) / 1024
    if size_kb < MIN_FILE_SIZE_KB:
        log.warning(
            "REJECT %s %s: %.1fKB < %dKB minimum",
            sku,
            view,
            size_kb,
            MIN_FILE_SIZE_KB,
        )
        return False
    log.info("PASS %s %s: %.1fKB", sku, view, size_kb)
    return True


def process_product(
    client, product: dict, views: list[str]
) -> dict:
    """Generate model shots for a single product. Returns results dict."""
    sku = product["sku"]
    name = product["name"]
    src = product["source_image"]
    results = {"sku": sku, "name": name, "views": {}}

    if not src:
        log.warning("SKIP %s (%s): no source image found", sku, name)
        results["status"] = "no_source"
        return results

    if product["is_accessory"]:
        log.info("ACCESSORY %s (%s): using accessory prompt", sku, name)

    for view in views:
        if product["is_accessory"] and view == "back":
            log.info("SKIP %s back view (accessory)", sku)
            results["views"][view] = "skipped_accessory"
            continue

        if product["is_accessory"]:
            prompt = ACCESSORY_PROMPT
        elif view == "front":
            prompt = FRONT_PROMPT
        else:
            prompt = BACK_PROMPT

        out_name = f"{sku}-{view}-model.webp"
        out_path = PRODUCTS_DIR / out_name

        log.info("Generating %s %s (%s)...", sku, view, name)

        success = False
        for attempt in range(1, MAX_RETRIES + 1):
            image_bytes = generate_model_shot(client, src, prompt, attempt)

            if image_bytes and quality_gate(image_bytes, sku, view):
                out_path.write_bytes(image_bytes)
                log.info("SAVED %s (%.1fKB)", out_path.name, len(image_bytes) / 1024)
                results["views"][view] = "success"
                success = True
                break

            if attempt < MAX_RETRIES:
                log.info("Retry %d/%d for %s %s...", attempt + 1, MAX_RETRIES, sku, view)
                time.sleep(RETRY_DELAY_SEC)

        if not success:
            log.error("FAILED %s %s after %d attempts", sku, view, MAX_RETRIES)
            results["views"][view] = "failed"

        # Rate limiting between API calls
        time.sleep(2)

    results["status"] = (
        "success"
        if all(v == "success" or v == "skipped_accessory" for v in results["views"].values())
        else "partial" if any(v == "success" for v in results["views"].values())
        else "failed"
    )
    return results


# -- CLI ---------------------------------------------------------------------


def cmd_dry_run(args):
    """List all products and their source images."""
    products = load_products(args.sku)
    print(f"\n{'SKU':<10} {'Name':<45} {'Source Image':<40} {'Status'}")
    print("-" * 120)

    found = 0
    missing = 0
    for p in products:
        src = p["source_image"]
        if src:
            src_str = src.name
            status = "ACCESSORY" if p["is_accessory"] else "READY"
            found += 1
        else:
            src_str = "—"
            status = "NO SOURCE"
            missing += 1

        print(f"{p['sku']:<10} {p['name']:<45} {src_str:<40} {status}")

    print(f"\nTotal: {len(products)} | Ready: {found} | Missing source: {missing}")
    print(f"Images to generate: {found * 2} (front + back)")


def cmd_generate(args):
    """Generate model shots."""
    from google import genai

    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        log.error("Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    products = load_products(args.sku)
    views = []
    if args.step in ("front", "all"):
        views.append("front")
    if args.step in ("back", "all"):
        views.append("back")

    log.info(
        "Starting generation: %d products, views=%s, model=%s",
        len(products),
        views,
        MODEL_ID,
    )

    all_results = []
    for i, product in enumerate(products, 1):
        if not product["source_image"]:
            log.warning(
                "[%d/%d] SKIP %s: no source image",
                i,
                len(products),
                product["sku"],
            )
            all_results.append(
                {"sku": product["sku"], "name": product["name"], "status": "no_source"}
            )
            continue

        log.info(
            "[%d/%d] Processing %s (%s)",
            i,
            len(products),
            product["sku"],
            product["name"],
        )
        result = process_product(client, product, views)
        all_results.append(result)

        # Longer delay between products to avoid rate limits
        if i < len(products):
            time.sleep(3)

    # Summary
    print("\n" + "=" * 80)
    print("GENERATION SUMMARY")
    print("=" * 80)
    success = sum(1 for r in all_results if r.get("status") == "success")
    partial = sum(1 for r in all_results if r.get("status") == "partial")
    failed = sum(1 for r in all_results if r.get("status") == "failed")
    skipped = sum(1 for r in all_results if r.get("status") == "no_source")

    print(f"Success: {success} | Partial: {partial} | Failed: {failed} | Skipped: {skipped}")
    print()

    for r in all_results:
        status_icon = {
            "success": "OK",
            "partial": "PARTIAL",
            "failed": "FAIL",
            "no_source": "SKIP",
        }.get(r.get("status", "?"), "?")
        views_str = ""
        if "views" in r:
            views_str = " | ".join(f"{v}={s}" for v, s in r["views"].items())
        print(f"  [{status_icon}] {r['sku']:<10} {r['name']:<40} {views_str}")

    # Save results log
    log_path = PROJECT_ROOT / "scripts" / "nano-banana-results.json"
    with open(log_path, "w") as f:
        json.dump(
            {"model": MODEL_ID, "total": len(all_results), "results": all_results},
            f,
            indent=2,
        )
    print(f"\nResults saved to {log_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Nano Banana 2 — Generate model shots for SkyyRose products"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List products and source images without generating",
    )
    parser.add_argument(
        "--sku",
        type=str,
        default=None,
        help="Process a single SKU (e.g. br-001)",
    )
    parser.add_argument(
        "--step",
        type=str,
        choices=["front", "back", "all"],
        default="all",
        help="Which views to generate (default: all)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override model ID (default: %(default)s)",
    )

    args = parser.parse_args()

    global MODEL_ID
    if args.model:
        MODEL_ID = args.model

    if args.dry_run:
        cmd_dry_run(args)
    else:
        cmd_generate(args)


if __name__ == "__main__":
    main()
