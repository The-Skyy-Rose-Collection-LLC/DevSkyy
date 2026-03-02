#!/usr/bin/env python3
"""
Nano Banana 2 — SkyyRose Product Image Generator

Uses Gemini image generation to create front + back model shots and
branding/editorial photos for all SkyyRose products.

Outputs:
  {sku}-front-model.webp   — Model wearing garment, front-facing
  {sku}-back-model.webp    — Model wearing garment, back-facing
  {sku}-branding.webp      — Lifestyle/editorial shot matching collection aesthetic

Usage:
    source .venv-imagery/bin/activate
    python scripts/nano-banana-vton.py --dry-run
    python scripts/nano-banana-vton.py --sku br-001
    python scripts/nano-banana-vton.py --step all
    python scripts/nano-banana-vton.py --step branding
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

MODEL_ID = "gemini-2.5-flash-image"
MIN_FILE_SIZE_KB = 50
MAX_RETRIES = 3
RETRY_DELAY_SEC = 5

# -- Product catalog ---------------------------------------------------------

PRODUCT_CATALOG = {
    "br-001": {"name": "BLACK Rose Crewneck", "collection": "black-rose"},
    "br-002": {"name": "BLACK Rose Joggers", "collection": "black-rose", "source_override": "br-002-joggers-source.jpg"},
    "br-003": {"name": "BLACK is Beautiful Jersey", "collection": "black-rose"},
    "br-004": {"name": "BLACK Rose Hoodie", "collection": "black-rose", "source_override": "br-004-hoodie-source.jpg"},
    "br-005": {"name": "BLACK Rose Hoodie — Signature Edition", "collection": "black-rose", "source_override": "br-005-hoodie-ltd-source.jpg"},
    "br-006": {"name": "BLACK Rose Sherpa Jacket", "collection": "black-rose"},
    "br-007": {"name": "BLACK Rose x Love Hurts Basketball Shorts", "collection": "black-rose"},
    "br-008": {"name": "Women's BLACK Rose Hooded Dress", "collection": "black-rose"},
    # New BR design mockups — use render3d step to generate 3D product shots
    "br-d01": {
        "name": "BLACK is Beautiful Hockey Jersey (Teal)",
        "collection": "black-rose",
        "source_override": "br-design-hockey-jersey.jpg",
    },
    "br-d02": {
        "name": "BLACK is Beautiful Football Jersey (Red #80)",
        "collection": "black-rose",
        "source_override": "br-design-football-jersey-red.jpg",
    },
    "br-d03": {
        "name": "BLACK is Beautiful Football Jersey (White #32)",
        "collection": "black-rose",
        "source_override": "br-design-football-jersey-white.jpg",
    },
    "br-d04": {
        "name": "BLACK is Beautiful Basketball Jersey",
        "collection": "black-rose",
        "source_override": "br-design-basketball-jersey.jpg",
    },
    "lh-001": {"name": "The Fannie Pack", "collection": "love-hurts"},
    "lh-002": {"name": "Love Hurts Joggers (Black)", "collection": "love-hurts"},
    "lh-003": {"name": "Love Hurts Basketball Shorts", "collection": "love-hurts"},
    "lh-004": {"name": "Love Hurts Varsity Jacket", "collection": "love-hurts"},
    "lh-005": {"name": "Love Hurts Windbreaker", "collection": "love-hurts"},
    "sg-001": {"name": "The Bay Set", "collection": "signature"},
    "sg-002": {"name": "Stay Golden Set", "collection": "signature"},
    "sg-003": {"name": "The Signature Tee (Orchid)", "collection": "signature"},
    "sg-004": {"name": "Signature Tee (White)", "collection": "signature"},
    "sg-005": {"name": "Stay Golden Tee", "collection": "signature"},
    "sg-006": {"name": "Mint & Lavender Hoodie", "collection": "signature"},
    "sg-007": {"name": "The Signature Beanie (Red)", "collection": "signature"},
    "sg-008": {"name": "The Signature Beanie", "collection": "signature"},
    "sg-009": {"name": "The Sherpa Jacket", "collection": "signature"},
    "sg-010": {"name": "The Bridge Series Shorts", "collection": "signature"},
    "sg-011": {"name": "Original Label Tee (White)", "collection": "signature"},
    "sg-012": {"name": "Original Label Tee (Orchid)", "collection": "signature"},
}

# SKUs that are accessories (not wearable on a model's body)
ACCESSORY_SKUS = {"lh-001", "sg-007", "sg-008"}

# SKUs with known bad source images (AI-generated VTON or wrong product photo).
# These are skipped by default. Remove a SKU once a real flat-lay photo is available.
BAD_SOURCE_SKUS = {
    "br-001",   # Source is a beanie, should be crewneck
    "lh-003",   # Source is AI-generated VTON (not flat-lay)
    "sg-002",   # Source is AI-generated VTON (not flat-lay)
    "sg-003",   # Source is AI-generated VTON (not flat-lay)
    "sg-004",   # Source shows blue shorts, should be white tee
    "sg-008",   # Source shows crop hoodie, should be beanie
}


def find_source_image(sku: str) -> Path | None:
    """Find the best available source image for a SKU."""
    # Check for explicit source override in catalog
    info = PRODUCT_CATALOG.get(sku, {})
    if "source_override" in info:
        override_path = PRODUCTS_DIR / info["source_override"]
        if override_path.exists():
            return override_path
        log.warning("source_override %s not found for %s", info["source_override"], sku)
        return None

    candidates = list(PRODUCTS_DIR.glob(f"{sku}*.webp")) + list(
        PRODUCTS_DIR.glob(f"{sku}*.jpg")
    )
    # Filter out generated shots — we want flat-lay/product source only
    source_candidates = [
        p
        for p in candidates
        if "-front-model" not in p.stem
        and "-back-model" not in p.stem
        and "-branding" not in p.stem
        and "-back" not in p.stem
        and "-render" not in p.stem
    ]
    if not source_candidates:
        return None
    # Prefer .webp over .jpg, then shorter filenames
    source_candidates.sort(key=lambda p: (p.suffix != ".webp", len(p.name)))
    return source_candidates[0]


def load_products(sku_filter: str | None = None, include_bad: bool = False) -> list[dict]:
    """Load product catalog, resolve source images, apply filter.

    By default skips SKUs in BAD_SOURCE_SKUS. Pass --include-bad or
    a specific --sku to override.
    """
    products = []
    skus = [sku_filter] if sku_filter else sorted(PRODUCT_CATALOG.keys())

    for sku in skus:
        if sku not in PRODUCT_CATALOG:
            log.error("Unknown SKU: %s", sku)
            continue

        # Skip known-bad source images unless explicitly requested
        if sku in BAD_SOURCE_SKUS and not include_bad and not sku_filter:
            log.info("SKIP %s: bad source image (use --include-bad to override)", sku)
            continue

        info = PRODUCT_CATALOG[sku]
        src = find_source_image(sku)

        products.append(
            {
                "sku": sku,
                "name": info["name"],
                "collection": info["collection"],
                "source_image": src,
                "is_accessory": sku in ACCESSORY_SKUS,
            }
        )

    return products


def get_api_key() -> str:
    """Load Google API key from config/settings.py or environment."""
    # Try the project's central settings first
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from config.settings import GOOGLE_API_KEY

        if GOOGLE_API_KEY:
            log.info("Loaded GOOGLE_API_KEY from config/settings.py")
            return GOOGLE_API_KEY
    except (ImportError, Exception) as exc:
        log.debug("Could not import config.settings: %s", exc)

    # Fall back to env vars
    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if key:
        log.info("Loaded API key from environment variable")
        return key

    log.error(
        "No Google API key found. Set GOOGLE_API_KEY in .env / .env.hf "
        "or export GOOGLE_API_KEY / GEMINI_API_KEY"
    )
    sys.exit(1)


# -- Prompt templates --------------------------------------------------------
# All prompts are functions that take the product name so the model knows
# EXACTLY what garment it's looking at (not just "this garment").


def front_prompt(name: str) -> str:
    return (
        f"The reference image shows a {name}. Generate a professional fashion "
        f"model wearing this EXACT {name}, front-facing, full body shot, "
        "luxury streetwear editorial photography, studio lighting, clean white "
        "background. The garment must be 100% identical to the reference "
        "image — same colors, same cut, same details, same logo placement, "
        "same fabric texture. Do NOT change the garment type. "
        "The model should have a confident, editorial pose."
    )


def back_prompt(name: str) -> str:
    return (
        f"The reference image shows a {name}. Generate a professional fashion "
        f"model wearing this EXACT {name}, BACK-FACING (showing the back of "
        "the garment), full body shot, luxury streetwear editorial photography, "
        "studio lighting, clean white background. The garment must be 100% "
        "identical to the reference — same colors, same cut, same back details, "
        "same logo placement. Do NOT change the garment type. "
        "The model is turned away from camera showing the back of the outfit."
    )


def accessory_prompt(name: str) -> str:
    return (
        f"The reference image shows a {name}. Generate a professional fashion "
        f"model wearing/holding this EXACT {name}, front-facing, luxury "
        "streetwear editorial photography, studio lighting, clean white "
        "background. The accessory must be 100% identical to the reference "
        "image. Do NOT change the item type."
    )


BRANDING_TEMPLATES = {
    "black-rose": (
        "The reference image shows a {name}. Generate a fashion model wearing "
        "this EXACT {name} in a dark, moody editorial setting — black marble "
        "surfaces, dramatic shadows, rose gold accent lighting. Gothic luxury "
        "aesthetic. The {name} must be 100% identical to the reference — same "
        "colors, same cut, same logos. Do NOT change the garment type. Deep "
        "blacks, dramatic contrast, cathedral of fashion. Rose gold (#B76E79) "
        "tones in the lighting. Cinematic composition, 3/4 body shot."
    ),
    "love-hurts": (
        "The reference image shows a {name}. Generate a fashion model wearing "
        "this EXACT {name} in a passionate, romantic editorial setting — red "
        "roses, velvet textures, warm dramatic lighting. The {name} must be "
        "100% identical to the reference — same colors, same cut, same logos. "
        "Do NOT change the garment type. Rich reds and deep burgundy tones, "
        "luxury castle backdrop. Rose petals, silk fabric in background. "
        "Cinematic composition, 3/4 body shot."
    ),
    "signature": (
        "The reference image shows a {name}. Generate a fashion model wearing "
        "this EXACT {name} in a Bay Area urban editorial setting — golden hour "
        "light, city skyline or Golden Gate Bridge silhouette in background. "
        "The {name} must be 100% identical to the reference — same colors, "
        "same cut, same logos. Do NOT change the garment type. Warm golden "
        "tones, California luxury vibes. Golden (#D4AF37) accent lighting. "
        "Cinematic composition, 3/4 body shot."
    ),
}

ACCESSORY_BRANDING_TEMPLATES = {
    "love-hurts": (
        "The reference image shows a {name}. Display this EXACT {name} in a "
        "passionate, romantic editorial setting — red roses, velvet textures, "
        "warm dramatic lighting. The {name} must be 100% identical to the "
        "reference. Do NOT change the item type. Product photography meets "
        "luxury editorial. Cinematic lighting."
    ),
    "signature": (
        "The reference image shows a {name}. Display this EXACT {name} in a "
        "Bay Area urban editorial setting — golden hour light, warm golden "
        "tones. The {name} must be 100% identical to the reference. Do NOT "
        "change the item type. California luxury vibes, premium product "
        "photography. Golden (#D4AF37) accents."
    ),
}

ENHANCED_PROMPT_SUFFIX = (
    " CRITICAL: The item in the output MUST be pixel-accurate to the "
    "reference. Do not change any colors, patterns, logos, or design "
    "elements. Do NOT substitute a different garment type. "
    "This is a luxury fashion brand — accuracy is everything."
)


def render3d_front_prompt(name: str) -> str:
    """Prompt for photorealistic 3D product render — front view."""
    return (
        f"The reference image is a flat design mockup of a {name}. "
        f"Convert this EXACT design into a photorealistic 3D product render "
        f"of the {name}, FRONT VIEW. The garment should appear as a "
        "professional e-commerce product shot on an invisible mannequin / "
        "ghost mannequin, showing the natural 3D shape and drape of the "
        "fabric. Light gray (#E8E8E8) studio background with subtle floor "
        "reflection. Professional product photography lighting — soft key "
        "light from upper-left, fill light from right, slight rim light. "
        "Every detail from the design mockup MUST be preserved exactly: "
        "same colors, same logos, same numbers, same text, same stripes, "
        "same patches, same patterns. Do NOT change ANY design element. "
        "The output should look like a real photograph of this garment "
        "on a mannequin form, ready for an e-commerce product page."
    )


def render3d_back_prompt(name: str) -> str:
    """Prompt for photorealistic 3D product render — back view."""
    return (
        f"The reference image shows both front and back views of a {name}. "
        f"Convert the BACK VIEW of this EXACT design into a photorealistic "
        f"3D product render of the {name}, BACK VIEW. The garment should "
        "appear as a professional e-commerce product shot on an invisible "
        "mannequin / ghost mannequin, showing the natural 3D shape and "
        "drape of the fabric. Light gray (#E8E8E8) studio background with "
        "subtle floor reflection. Professional product photography lighting. "
        "Every detail from the back of the design MUST be preserved exactly: "
        "same colors, same logos, same numbers, same text, same stripes. "
        "Do NOT change ANY design element. Show the BACK of the garment."
    )


def render3d_branding_prompt(name: str, collection: str) -> str:
    """Prompt for 3D product render with branding context."""
    collection_vibe = {
        "black-rose": (
            "Dark, moody studio background — black marble surface, "
            "dramatic shadows, rose gold accent lighting (#B76E79). "
            "Gothic luxury aesthetic."
        ),
        "love-hurts": (
            "Warm romantic studio — deep red velvet backdrop, "
            "rose gold and burgundy accent lighting."
        ),
        "signature": (
            "Golden hour California studio — warm golden backdrop, "
            "Bay Area luxury vibes, gold (#D4AF37) accent lighting."
        ),
    }
    vibe = collection_vibe.get(collection, collection_vibe["black-rose"])
    return (
        f"The reference image is a flat design mockup of a {name}. "
        f"Convert this EXACT design into a photorealistic 3D product render. "
        f"The garment on an invisible mannequin with natural 3D shape. "
        f"{vibe} "
        f"Every detail MUST be preserved exactly from the design: colors, "
        f"logos, numbers, text, stripes, patches. Do NOT change anything. "
        f"Cinematic product photography, slight floor reflection."
    )


# -- Image enhancement -------------------------------------------------------

ENHANCE_TARGET_PX = 1536  # Upscale short edge to this for a crisp reference


def enhance_source_image(image_path: Path):
    """Upscale, sharpen, and boost contrast on the source image.

    Returns a PIL Image ready to be sent as reference.
    """
    from PIL import Image, ImageEnhance, ImageFilter

    img = Image.open(image_path).convert("RGB")

    # Upscale so the short edge is at least ENHANCE_TARGET_PX
    w, h = img.size
    short_edge = min(w, h)
    if short_edge < ENHANCE_TARGET_PX:
        scale = ENHANCE_TARGET_PX / short_edge
        new_w, new_h = int(w * scale), int(h * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        log.debug("Upscaled %s: %dx%d -> %dx%d", image_path.name, w, h, new_w, new_h)

    # Sharpen to bring out logo/print details
    img = img.filter(ImageFilter.SHARPEN)

    # Slight contrast boost so colors pop in the reference
    img = ImageEnhance.Contrast(img).enhance(1.15)

    # Slight color saturation boost
    img = ImageEnhance.Color(img).enhance(1.1)

    return img


# -- Image generation --------------------------------------------------------


def generate_image(
    client,
    source_image_path: Path,
    prompt: str,
    attempt: int = 1,
) -> bytes | None:
    """Generate a single image using Gemini.

    Returns WebP image bytes on success, None on failure.
    """
    from google.genai import types

    src_img = enhance_source_image(source_image_path)

    full_prompt = prompt
    if attempt > 1:
        full_prompt += ENHANCED_PROMPT_SUFFIX

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[
                "REFERENCE PHOTO of the exact product (study every detail):",
                src_img,
                full_prompt,
            ],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="3:4",
                ),
            ),
        )
    except Exception as exc:
        log.error("API call failed (attempt %d): %s", attempt, exc)
        return None

    if not response or not response.parts:
        log.warning("Empty response from API (attempt %d)", attempt)
        return None

    for part in response.parts:
        if part.inline_data:
            # as_image() returns a genai Image — .save() takes a file path
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as tmp:
                tmp_path = tmp.name
            part.as_image().save(tmp_path)
            data = Path(tmp_path).read_bytes()
            Path(tmp_path).unlink(missing_ok=True)
            return data

    log.warning("No image in response parts (attempt %d)", attempt)
    return None


def quality_gate(image_bytes: bytes, sku: str, view: str) -> bool:
    """Check if generated image passes quality requirements."""
    size_kb = len(image_bytes) / 1024
    if size_kb < MIN_FILE_SIZE_KB:
        log.warning(
            "REJECT %s %s: %.1fKB < %dKB minimum",
            sku, view, size_kb, MIN_FILE_SIZE_KB,
        )
        return False
    log.info("PASS %s %s: %.1fKB", sku, view, size_kb)
    return True


def get_prompt(product: dict, view: str) -> str:
    """Select the right prompt for a product + view combination."""
    is_accessory = product["is_accessory"]
    collection = product["collection"]
    name = product["name"]

    # 3D product render mode
    if view == "render3d_front":
        return render3d_front_prompt(name)
    if view == "render3d_back":
        return render3d_back_prompt(name)
    if view == "render3d_branding":
        return render3d_branding_prompt(name, collection)

    if view == "branding":
        if is_accessory:
            tpl = ACCESSORY_BRANDING_TEMPLATES.get(
                collection, BRANDING_TEMPLATES[collection]
            )
            return tpl.format(name=name)
        return BRANDING_TEMPLATES[collection].format(name=name)

    if is_accessory:
        return accessory_prompt(name)

    if view == "front":
        return front_prompt(name)
    return back_prompt(name)


def get_output_filename(sku: str, view: str) -> str:
    """Map view to output filename."""
    if view.startswith("render3d_"):
        suffix = view.replace("render3d_", "")
        return f"{sku}-render-{suffix}.webp"
    return f"{sku}-{view}-model.webp" if view != "branding" else f"{sku}-branding.webp"


def process_product(client, product: dict, views: list[str]) -> dict:
    """Generate images for a single product. Returns results dict."""
    sku = product["sku"]
    name = product["name"]
    src = product["source_image"]
    results = {"sku": sku, "name": name, "views": {}}

    if not src:
        log.warning("SKIP %s (%s): no source image found", sku, name)
        results["status"] = "no_source"
        return results

    for view in views:
        # Accessories skip back-model view
        if product["is_accessory"] and view == "back":
            log.info("SKIP %s back view (accessory)", sku)
            results["views"][view] = "skipped_accessory"
            continue

        prompt = get_prompt(product, view)
        out_path = PRODUCTS_DIR / get_output_filename(sku, view)

        log.info("Generating %s %s (%s)...", sku, view, name)

        success = False
        for attempt in range(1, MAX_RETRIES + 1):
            image_bytes = generate_image(client, src, prompt, attempt)

            if image_bytes and quality_gate(image_bytes, sku, view):
                out_path.write_bytes(image_bytes)
                log.info("SAVED %s (%.1fKB)", out_path.name, len(image_bytes) / 1024)
                results["views"][view] = "success"
                success = True
                break

            if attempt < MAX_RETRIES:
                log.info(
                    "Retry %d/%d for %s %s...",
                    attempt + 1, MAX_RETRIES, sku, view,
                )
                time.sleep(RETRY_DELAY_SEC)

        if not success:
            log.error("FAILED %s %s after %d attempts", sku, view, MAX_RETRIES)
            results["views"][view] = "failed"

        # Rate limiting between API calls
        time.sleep(2)

    skippable = {"skipped_accessory"}
    view_statuses = list(results["views"].values())
    if all(v == "success" or v in skippable for v in view_statuses):
        results["status"] = "success"
    elif any(v == "success" for v in view_statuses):
        results["status"] = "partial"
    else:
        results["status"] = "failed"

    return results


# -- CLI commands ------------------------------------------------------------


def resolve_views(step: str) -> list[str]:
    """Map --step argument to list of views."""
    mapping = {
        "front": ["front"],
        "back": ["back"],
        "branding": ["branding"],
        "models": ["front", "back"],
        "all": ["front", "back", "branding"],
        "render3d": ["render3d_front", "render3d_back", "render3d_branding"],
        "render3d_front": ["render3d_front"],
        "render3d_back": ["render3d_back"],
    }
    return mapping[step]


def cmd_dry_run(args):
    """List all products and their source images."""
    products = load_products(args.sku, include_bad=args.include_bad)
    views = resolve_views(args.step)

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
            src_str = "---"
            status = "NO SOURCE"
            missing += 1

        print(f"{p['sku']:<10} {p['name']:<45} {src_str:<40} {status}")

    # Count actual images to generate
    img_count = 0
    for p in products:
        if not p["source_image"]:
            continue
        for v in views:
            if p["is_accessory"] and v == "back":
                continue
            img_count += 1

    print(f"\nTotal: {len(products)} | Ready: {found} | Missing source: {missing}")
    print(f"Views: {', '.join(views)}")
    print(f"Images to generate: {img_count}")


def cmd_generate(args):
    """Generate images."""
    from google import genai

    api_key = get_api_key()
    client = genai.Client(api_key=api_key)
    products = load_products(args.sku, include_bad=args.include_bad)
    views = resolve_views(args.step)

    log.info(
        "Starting generation: %d products, views=%s, model=%s",
        len(products), views, MODEL_ID,
    )

    all_results = []
    for i, product in enumerate(products, 1):
        if not product["source_image"]:
            log.warning(
                "[%d/%d] SKIP %s: no source image",
                i, len(products), product["sku"],
            )
            all_results.append(
                {"sku": product["sku"], "name": product["name"], "status": "no_source"}
            )
            continue

        log.info(
            "[%d/%d] Processing %s (%s)",
            i, len(products), product["sku"], product["name"],
        )
        result = process_product(client, product, views)
        all_results.append(result)

        # Rate limit between products
        if i < len(products):
            time.sleep(3)

    # -- Summary --
    print("\n" + "=" * 80)
    print("GENERATION SUMMARY")
    print("=" * 80)

    counts = {}
    for r in all_results:
        s = r.get("status", "unknown")
        counts[s] = counts.get(s, 0) + 1

    parts = [f"{k.title()}: {v}" for k, v in sorted(counts.items())]
    print(" | ".join(parts))
    print()

    for r in all_results:
        icon = {
            "success": "OK", "partial": "PARTIAL",
            "failed": "FAIL", "no_source": "SKIP",
        }.get(r.get("status", "?"), "?")
        views_str = ""
        if "views" in r:
            views_str = " | ".join(f"{v}={s}" for v, s in r["views"].items())
        print(f"  [{icon:>7}] {r['sku']:<10} {r['name']:<40} {views_str}")

    # Save results log
    log_path = PROJECT_ROOT / "scripts" / "nano-banana-results.json"
    with open(log_path, "w") as f:
        json.dump(
            {
                "model": MODEL_ID,
                "step": args.step,
                "total": len(all_results),
                "results": all_results,
            },
            f,
            indent=2,
        )
    print(f"\nResults saved to {log_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Nano Banana 2 — Generate product images for SkyyRose"
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
        choices=["front", "back", "branding", "models", "all", "render3d", "render3d_front", "render3d_back"],
        default="all",
        help="What to generate: front, back, branding, models (front+back), all, render3d (3D product shots)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override Gemini model ID",
    )
    parser.add_argument(
        "--include-bad",
        action="store_true",
        help="Include SKUs with known bad source images (normally skipped)",
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
