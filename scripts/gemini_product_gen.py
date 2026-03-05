#!/usr/bin/env python3
"""
Gemini Product Image Generator — SkyyRose v5

Uses Gemini image generation with tech flat reference images to produce:
  1. Photorealistic flat lay product photos
  2. Model shots (person wearing the product)
  3. Multiple angle/background variants for training data

Each tech flat is analyzed in detail, then used as a visual reference
for Gemini to generate accurate product imagery.

Usage:
    source .venv-imagery/bin/activate
    python scripts/gemini_product_gen.py --mode flat
    python scripts/gemini_product_gen.py --mode model
    python scripts/gemini_product_gen.py --mode both
    python scripts/gemini_product_gen.py --sku br-d02 --mode both
    python scripts/gemini_product_gen.py --variants 5 --mode flat
"""

import argparse
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
log = logging.getLogger("gemini-product-gen")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load env
for env_file in [PROJECT_ROOT / ".env", PROJECT_ROOT / ".env.hf"]:
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    value = value.strip().strip('"').strip("'")
                    if value:
                        os.environ.setdefault(key.strip(), value)

MODEL_ID = "gemini-2.5-flash-image"
MIN_FILE_SIZE_KB = 30
MAX_RETRIES = 3
RETRY_DELAY_SEC = 5

# Tech flat source directory (from LoRA v4 dataset)
TECHFLAT_DIR = PROJECT_ROOT / "datasets" / "skyyrose_lora_v4" / "images"
OUTPUT_DIR = PROJECT_ROOT / "datasets" / "skyyrose_v5_gemini"

# ── Product catalog with DETAILED descriptions for Gemini ──────────────────
# Each product has exhaustive visual details extracted from analyzing the tech flats.
# This is the key difference from LoRA — Gemini gets explicit instructions about
# every design element rather than trying to learn them from 1-3 images.

PRODUCTS = {
    "br-001": {
        "name": "Black Rose Crewneck Set",
        "collection": "black-rose",
        "techflat": "br-001-techflat.jpg",
        "description": (
            "Two-piece set: black crewneck sweatshirt + matching black jogger pants. "
            "Front of crewneck has a large white and gray rose graphic — two roses "
            "growing from a cloud/concrete base, with thorny stems and leaves. "
            "White ribbed crew neckline, white band at hem and cuffs. "
            "Back of crewneck has a smaller version of the same rose logo on upper back. "
            "Jogger pants are plain black with a small rose-from-concrete logo on left thigh, "
            "white drawstring waistband, ribbed ankle cuffs with white trim."
        ),
    },
    "br-003-giants": {
        "name": "Black Is Beautiful Baseball Jersey (Giants)",
        "collection": "black-rose",
        "techflat": "br-003-giants-techflat.jpg",
        "description": (
            "Black short-sleeve button-front baseball jersey with SF Giants-inspired colorway. "
            "Front: 'BLACK IS BEAUTIFUL' in arched orange text across chest, V-neck with "
            "white inner collar, orange piping along button placket and neckline, 5 black "
            "buttons, small Black Rose Collection patch at bottom-left hem. "
            "Orange trim on sleeve hems and bottom hem. "
            "Back: large white and gray rose-from-concrete graphic centered, "
            "small 'SR' monogram at upper back neckline, orange piping along shoulders."
        ),
    },
    "br-d02": {
        "name": "Black Is Beautiful Football Jersey (Red #80)",
        "collection": "black-rose",
        "techflat": "br-d02-techflat.jpg",
        "description": (
            "Red football jersey, number 80. V-neck with black and white striped collar. "
            "Front: large '80' numbers — CRITICAL DETAIL: the left '8' has alternating "
            "rose-fill pattern (grayscale rose graphic inside the number), right '0' is "
            "plain white with black outline. Three white stripes with red gaps on each sleeve. "
            "Small Black Rose Collection patch at bottom-left hem. "
            "Back: '80' numbers — alternating rose fill pattern reversed (right number "
            "has rose fill, left is plain). 'BLACK IS BEAUTIFUL' text arched above numbers. "
            "Same arm stripes. Red base fabric throughout."
        ),
    },
    "br-d03": {
        "name": "Black Is Beautiful Football Jersey (White #32)",
        "collection": "black-rose",
        "techflat": "br-d03-techflat.jpg",
        "description": (
            "White football jersey, number 32. V-neck with black collar. "
            "Front: large '32' numbers — the '3' has dark grayscale rose-fill pattern "
            "(rose graphic inside the number shape), '2' has similar treatment. "
            "Small numbers on each sleeve. Two black stripes on each sleeve. "
            "Back: '32' numbers with dark grayscale rose fill, 'BLACK IS BEAUTIFUL' "
            "text arched above numbers in dark text. Small 'SR' logo at upper back. "
            "White base fabric throughout, clean minimalist design."
        ),
    },
    "br-d04": {
        "name": "The Bay Basketball Jersey",
        "collection": "black-rose",
        "techflat": "br-d04-techflat.jpg",
        "description": (
            "White sleeveless basketball jersey with V-neck. "
            "Front: 'THE BAY' text in gold/yellow outlined letters across upper chest, "
            "circular rose-from-concrete medallion below text with thorny border ring, "
            "bottom half of jersey has large grayscale rose gradient — roses fading from "
            "dark gray/black at bottom to light gray, covering lower 40% of jersey. "
            "Small Black Rose Collection patch at bottom-left. "
            "Back: 'BLACK IS BEAUTIFUL' in gold/yellow stacked text, same grayscale "
            "rose gradient on bottom half. Small 'SR' logo at upper back neckline."
        ),
    },
    "lh-002": {
        "name": "Love Hurts Varsity Jacket",
        "collection": "love-hurts",
        "techflat": "lh-002-techflat.jpg",
        "description": (
            "Hooded varsity/bomber jacket — white body, black raglan sleeves. "
            "Front: 'Love Hurts' in red cursive script on left chest, snap button "
            "closure, two welt pockets, hood has heart pattern lining (visible when up). "
            "Red and black striped ribbing at hem, cuffs, and waistband. "
            "Back: large red roses bouquet with red anatomical heart — roses growing "
            "through/around a bleeding heart graphic, very detailed. "
            "Hood is black on outside. Overall shape is a classic varsity jacket "
            "with raglan sleeves, NOT a crewneck or pullover."
        ),
    },
    "lh-003": {
        "name": "Love Hurts Track Pants",
        "collection": "love-hurts",
        "techflat": "lh-003-techflat.jpg",
        "description": (
            "Track pants shown in TWO colorways — white version and black version. "
            "Both have: contrasting side panel stripe running full length of each leg, "
            "small red rose embroidery on left thigh area, drawstring waistband, "
            "tapered jogger-style ankle cuffs. "
            "White version: white body, black side panels. "
            "Black version: black body, white side panels. "
            "Sizing info shown: S through 3XL. Clean athletic streetwear design."
        ),
    },
    "lh-004": {
        "name": "Love Hurts Rose Shorts",
        "collection": "love-hurts",
        "techflat": "lh-004-techflat.jpg",
        "description": (
            "White athletic shorts with all-over repeating red rose bouquet pattern — "
            "small rose clusters in a grid pattern across entire fabric. "
            "'Love Hurts' in red cursive script on right thigh area, with red "
            "heart-and-dagger graphic. Black waistband with white drawstrings. "
            "Black and red chevron/diamond side panels on each leg (like basketball "
            "shorts design). 'Love Hurts' script repeated in smaller size on side panels. "
            "Black mesh side vents. Mid-thigh length."
        ),
    },
    "sg-002": {
        "name": "Signature Purple Rose Tee + Bridge Shorts Set",
        "collection": "signature",
        "techflat": "sg-002-techflat.jpg",
        "description": (
            "Two-piece set: white crewneck tee + purple Golden Gate Bridge shorts. "
            "Tee front: purple/pink rose graphic (rose growing from concrete/cloud base) "
            "centered on chest. Tee back: plain white with small 'SR' logo at neckline. "
            "Shorts: full photographic print of Golden Gate Bridge at night in purple/twilight "
            "tones — the bridge reflection in water visible, purple sky, warm orange bridge "
            "lights. Lightning bolt detail on left leg. Small rose logo on right leg. "
            "Black waistband on shorts. The shorts are the statement piece."
        ),
    },
    "sg-007": {
        "name": "Signature Beanie (Black)",
        "collection": "signature",
        "techflat": "sg-007-008-techflat.jpg",
        "description": (
            "Black ribbed knit beanie with fold-over cuff. "
            "Rectangular woven patch on front cuff featuring the SkyyRose rose logo "
            "(rose growing from concrete base). Multiple variants exist: "
            "purple rose patch, white/gray rose patch, red rose patch, and "
            "larger red bouquet patch. Standard beanie shape, ribbed knit texture, "
            "clean streetwear accessory design."
        ),
    },
    "sg-d01": {
        "name": "Pastel V-Chevron Windbreaker Set",
        "collection": "signature",
        "techflat": "sg-d01-techflat.jpg",
        "description": (
            "Two-piece windbreaker set: zip-up hooded jacket + matching pants. "
            "Jacket: white base with V-shaped chevron color blocks across chest — "
            "pink, green, yellow, and lavender/purple stripes forming a V pattern. "
            "Pink hood. Full zip front, two front zip pockets with pink pulls. "
            "Cuffs have matching pastel striped ribbing (pink/green/yellow/purple). "
            "Small pink rose logo on left chest. "
            "Back: plain white with small 'SR' logo at upper back. "
            "Pants: white base with same V-chevron pattern at hips, "
            "pink drawstring waistband, matching pastel striped ribbing at ankles."
        ),
    },
    "sg-d03": {
        "name": "Mint Green Crewneck Set",
        "collection": "signature",
        "techflat": "sg-d03-techflat.jpg",
        "description": (
            "Two-piece set: mint green crewneck sweatshirt + matching mint green jogger pants. "
            "Crewneck front: purple/lavender and pink rose graphic (rose growing from "
            "concrete/cloud base) centered on chest — same SkyyRose signature rose but "
            "in purple/pink colorway instead of white/gray. "
            "Crewneck back: smaller version of purple rose logo on upper back. "
            "Jogger pants: mint green with small purple rose logo on left thigh, "
            "drawstring waistband, ribbed ankle cuffs. "
            "The mint green is a bright seafoam/mint tone throughout."
        ),
    },
    "sg-d04": {
        "name": "Mint Green Hooded Dress",
        "collection": "signature",
        "techflat": "sg-d04-techflat.jpg",
        "description": (
            "Knee-length hooded sweatshirt dress in mint green. "
            "Hood with purple drawstrings. Front: purple/lavender rose graphic "
            "(rose growing from dark concrete/cloud base) centered on upper chest. "
            "Kangaroo/muff pocket below the graphic. Long sleeves with ribbed cuffs. "
            "Dress falls to approximately knee length, straight cut silhouette. "
            "Meant as a women's piece — casual luxury streetwear dress. "
            "Same mint green tone as sg-d03 set."
        ),
    },
}

# ── Prompt templates ────────────────────────────────────────────────────────

FLAT_PROMPTS = [
    # Variant 1: Clean white background flat lay
    (
        "flat-white",
        "Generate a photorealistic product flat lay photograph of this {name}. "
        "The garment is laid flat on a pure white background, shot from directly above. "
        "Professional e-commerce product photography, even studio lighting, no shadows. "
        "CRITICAL — the product must match these EXACT details: {description} "
        "Every color, pattern, logo, text, stripe, and design element must be "
        "pixel-accurate to the reference image. Do NOT change any detail. "
        "Clean, sharp, high-resolution product photo."
    ),
    # Variant 2: Light gray studio
    (
        "flat-gray",
        "Generate a photorealistic product photograph of this {name}. "
        "The garment is displayed on a light gray (#E8E8E8) studio background, "
        "slightly angled as if on an invisible mannequin giving it natural 3D shape. "
        "Professional product photography with soft studio lighting. "
        "CRITICAL — the product must match these EXACT details: {description} "
        "Every color, pattern, logo, text, and design element must be identical "
        "to the reference image. Premium e-commerce quality."
    ),
    # Variant 3: Lifestyle flat lay (styled)
    (
        "flat-styled",
        "Generate a styled flat lay photograph of this {name}. "
        "The garment is artfully arranged on a dark surface (black marble or dark wood) "
        "with subtle styling props — a small plant, sunglasses, or watch nearby. "
        "Overhead shot, luxury lifestyle product photography. "
        "CRITICAL — the product must match these EXACT details: {description} "
        "The garment is the hero of the shot. Premium brand aesthetic."
    ),
]

MODEL_PROMPTS = {
    "black-rose": [
        (
            "model-studio",
            "Generate a professional fashion model wearing this EXACT {name}. "
            "Full body shot, front-facing, confident editorial pose. "
            "Studio lighting, clean white background. "
            "The garment must match these EXACT details: {description} "
            "Do NOT change the garment type, colors, patterns, or any design element. "
            "Luxury streetwear editorial photography. The model should complement "
            "the dark, bold aesthetic of the Black Rose Collection."
        ),
        (
            "model-editorial",
            "Generate a fashion model wearing this EXACT {name} in a dark, moody "
            "editorial setting — concrete walls, dramatic shadows, rose gold accent lighting. "
            "Gothic luxury aesthetic. 3/4 body shot. "
            "The garment must match these EXACT details: {description} "
            "Do NOT change ANY design element. Cinematic composition, deep blacks, "
            "dramatic contrast. The model exudes confidence and edge."
        ),
    ],
    "love-hurts": [
        (
            "model-studio",
            "Generate a professional fashion model wearing this EXACT {name}. "
            "Full body shot, front-facing, passionate editorial pose. "
            "Studio lighting, clean white background. "
            "The garment must match these EXACT details: {description} "
            "Do NOT change the garment type, colors, patterns, or any design element. "
            "Luxury streetwear editorial photography."
        ),
        (
            "model-editorial",
            "Generate a fashion model wearing this EXACT {name} in a romantic "
            "editorial setting — red roses, warm dramatic lighting, rich textures. "
            "3/4 body shot. "
            "The garment must match these EXACT details: {description} "
            "Do NOT change ANY design element. Cinematic composition, "
            "passionate energy. Deep reds and warm tones."
        ),
    ],
    "signature": [
        (
            "model-studio",
            "Generate a professional fashion model wearing this EXACT {name}. "
            "Full body shot, front-facing, relaxed California cool pose. "
            "Studio lighting, clean white background. "
            "The garment must match these EXACT details: {description} "
            "Do NOT change the garment type, colors, patterns, or any design element. "
            "Luxury streetwear editorial photography."
        ),
        (
            "model-editorial",
            "Generate a fashion model wearing this EXACT {name} in a Bay Area "
            "urban setting — Golden Gate Bridge or city skyline in background, "
            "golden hour lighting. 3/4 body shot. "
            "The garment must match these EXACT details: {description} "
            "Do NOT change ANY design element. California luxury vibes, "
            "warm golden tones. Cinematic street style."
        ),
    ],
}

# ── Image generation ────────────────────────────────────────────────────────


def get_client():
    """Initialize Gemini client."""
    from google import genai
    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        log.error("No GOOGLE_API_KEY found. Set in .env or .env.hf")
        sys.exit(1)
    return genai.Client(api_key=key)


def enhance_source(image_path: Path):
    """Upscale and sharpen source tech flat for better Gemini reference."""
    from PIL import Image, ImageEnhance, ImageFilter
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    short_edge = min(w, h)
    if short_edge < 1536:
        scale = 1536 / short_edge
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    img = img.filter(ImageFilter.SHARPEN)
    img = ImageEnhance.Contrast(img).enhance(1.15)
    img = ImageEnhance.Color(img).enhance(1.1)
    return img


def generate_image(client, source_img, prompt: str, attempt: int = 1) -> bytes | None:
    """Generate a single image using Gemini with reference image."""
    from google.genai import types

    suffix = ""
    if attempt > 1:
        suffix = (
            " CRITICAL: The item in the output MUST be pixel-accurate to the "
            "reference. Do not change any colors, patterns, logos, or design "
            "elements. Do NOT substitute a different garment type."
        )

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[
                "REFERENCE IMAGE — study every detail of this exact product:",
                source_img,
                prompt + suffix,
            ],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="3:4",
                ),
            ),
        )
    except Exception as exc:
        log.error("API error (attempt %d): %s", attempt, exc)
        return None

    if not response or not response.parts:
        log.warning("Empty response (attempt %d)", attempt)
        return None

    for part in response.parts:
        if part.inline_data:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as tmp:
                tmp_path = tmp.name
            part.as_image().save(tmp_path)
            data = Path(tmp_path).read_bytes()
            Path(tmp_path).unlink(missing_ok=True)
            return data

    log.warning("No image in response (attempt %d)", attempt)
    return None


def process_product(client, sku: str, product: dict, modes: list[str], num_variants: int):
    """Generate all requested images for a single product."""
    techflat_path = TECHFLAT_DIR / product["techflat"]
    if not techflat_path.exists():
        log.warning("SKIP %s: tech flat not found at %s", sku, techflat_path)
        return {}

    src_img = enhance_source(techflat_path)
    results = {}
    sku_dir = OUTPUT_DIR / sku
    sku_dir.mkdir(parents=True, exist_ok=True)

    # Flat lay variants
    if "flat" in modes:
        flat_prompts = FLAT_PROMPTS[:num_variants]
        for variant_name, prompt_tpl in flat_prompts:
            prompt = prompt_tpl.format(
                name=product["name"],
                description=product["description"],
            )
            out_path = sku_dir / f"{sku}-{variant_name}.webp"
            log.info("  [FLAT] %s %s...", sku, variant_name)

            for attempt in range(1, MAX_RETRIES + 1):
                img_bytes = generate_image(client, src_img, prompt, attempt)
                if img_bytes and len(img_bytes) / 1024 >= MIN_FILE_SIZE_KB:
                    out_path.write_bytes(img_bytes)
                    size_kb = len(img_bytes) / 1024
                    log.info("  SAVED %s (%.0f KB)", out_path.name, size_kb)
                    results[variant_name] = {"status": "success", "size_kb": round(size_kb)}
                    break
                if attempt < MAX_RETRIES:
                    log.info("  Retry %d/%d...", attempt + 1, MAX_RETRIES)
                    time.sleep(RETRY_DELAY_SEC)
            else:
                results[variant_name] = {"status": "failed"}

            time.sleep(2)  # Rate limit

    # Model shot variants
    if "model" in modes:
        collection = product["collection"]
        model_prompts = MODEL_PROMPTS.get(collection, MODEL_PROMPTS["signature"])
        model_prompts = model_prompts[:num_variants]
        for variant_name, prompt_tpl in model_prompts:
            prompt = prompt_tpl.format(
                name=product["name"],
                description=product["description"],
            )
            out_path = sku_dir / f"{sku}-{variant_name}.webp"
            log.info("  [MODEL] %s %s...", sku, variant_name)

            for attempt in range(1, MAX_RETRIES + 1):
                img_bytes = generate_image(client, src_img, prompt, attempt)
                if img_bytes and len(img_bytes) / 1024 >= MIN_FILE_SIZE_KB:
                    out_path.write_bytes(img_bytes)
                    size_kb = len(img_bytes) / 1024
                    log.info("  SAVED %s (%.0f KB)", out_path.name, size_kb)
                    results[variant_name] = {"status": "success", "size_kb": round(size_kb)}
                    break
                if attempt < MAX_RETRIES:
                    log.info("  Retry %d/%d...", attempt + 1, MAX_RETRIES)
                    time.sleep(RETRY_DELAY_SEC)
            else:
                results[variant_name] = {"status": "failed"}

            time.sleep(2)  # Rate limit

    return results


def main():
    parser = argparse.ArgumentParser(description="Gemini product image generator for SkyyRose")
    parser.add_argument("--sku", help="Specific SKU to generate (default: all)")
    parser.add_argument("--mode", choices=["flat", "model", "both"], default="both",
                        help="Generation mode")
    parser.add_argument("--variants", type=int, default=2,
                        help="Number of variants per mode (1-3, default: 2)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be generated without calling API")
    args = parser.parse_args()

    modes = ["flat", "model"] if args.mode == "both" else [args.mode]
    num_variants = min(max(args.variants, 1), 3)

    # Filter products
    if args.sku:
        if args.sku not in PRODUCTS:
            log.error("Unknown SKU: %s. Available: %s", args.sku, ", ".join(sorted(PRODUCTS)))
            return 1
        skus = [args.sku]
    else:
        skus = sorted(PRODUCTS.keys())

    # Calculate totals
    total_per_product = 0
    if "flat" in modes:
        total_per_product += min(num_variants, len(FLAT_PROMPTS))
    if "model" in modes:
        total_per_product += min(num_variants, 2)
    total_images = len(skus) * total_per_product

    print("=" * 70)
    print("  SKYYROSE GEMINI PRODUCT GENERATOR")
    print(f"  Model: {MODEL_ID}")
    print(f"  Products: {len(skus)} | Modes: {', '.join(modes)} | "
          f"Variants: {num_variants} | Total: ~{total_images} images")
    print("=" * 70)

    if args.dry_run:
        for sku in skus:
            product = PRODUCTS[sku]
            techflat = TECHFLAT_DIR / product["techflat"]
            exists = "OK" if techflat.exists() else "MISSING"
            print(f"  {sku}: {product['name']} [{exists}]")
            if "flat" in modes:
                for name, _ in FLAT_PROMPTS[:num_variants]:
                    print(f"    -> {sku}-{name}.webp")
            if "model" in modes:
                collection = product["collection"]
                for name, _ in MODEL_PROMPTS.get(collection, MODEL_PROMPTS["signature"])[:num_variants]:
                    print(f"    -> {sku}-{name}.webp")
        print(f"\n  Dry run complete. {total_images} images would be generated.")
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    client = get_client()

    all_results = {}
    for i, sku in enumerate(skus, 1):
        product = PRODUCTS[sku]
        print(f"\n[{i}/{len(skus)}] {sku} — {product['name']}")
        results = process_product(client, sku, product, modes, num_variants)
        all_results[sku] = results

    # Save results
    results_path = OUTPUT_DIR / "generation_results.json"
    with open(results_path, "w") as f:
        json.dump(all_results, f, indent=2)

    # Summary
    total_success = sum(
        1 for sku_results in all_results.values()
        for r in sku_results.values()
        if isinstance(r, dict) and r.get("status") == "success"
    )
    total_attempted = sum(len(r) for r in all_results.values())

    print("\n" + "=" * 70)
    print(f"  COMPLETE: {total_success}/{total_attempted} images generated")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"  Results: {results_path}")
    print("=" * 70)

    if total_success > 0:
        print(f"\n  View results:")
        print(f"    open {OUTPUT_DIR}")

    return 0 if total_success == total_attempted else 1


if __name__ == "__main__":
    exit(main())
