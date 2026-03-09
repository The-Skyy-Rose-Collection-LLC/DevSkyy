#!/usr/bin/env python3
"""
SkyyRose Diverse Model Shot Generator

Generates men's and women's model shots for every product with diverse
ethnicities, backgrounds, and styling. Gender-neutral brand representation.

Output:
  {sku}-model-m.webp  — Men's model wearing the product
  {sku}-model-f.webp  — Women's model wearing the product

Usage:
    source .venv-imagery/bin/activate
    python scripts/generate-model-shots.py --dry-run
    python scripts/generate-model-shots.py --sku sg-d01
    python scripts/generate-model-shots.py --all
    python scripts/generate-model-shots.py --gender m   # men's only
    python scripts/generate-model-shots.py --gender f   # women's only
"""

import argparse
import io
import logging
import os
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("model-shots")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = (
    PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products"
)

MODEL_ID = "gemini-2.5-flash-image"
MIN_FILE_SIZE_KB = 30
MAX_RETRIES = 3
RETRY_DELAY_SEC = 8

# ── Diversity pools (cycled through the catalog) ────────────────────────────

MALE_MODELS = [
    "young Black man with a fresh fade, athletic build, confident expression",
    "East Asian man with stylish hair, lean build, cool relaxed pose",
    "Latino man with short curly hair, medium build, warm smile",
    "Middle Eastern man with trimmed beard, tall build, strong jawline",
    "mixed-race man with locs, athletic build, effortlessly cool stance",
    "South Asian man with clean-cut look, fit build, direct gaze",
    "Black man with braids, muscular build, powerful presence",
    "White man with textured hair, slim build, editorial pose",
]

FEMALE_MODELS = [
    "young Black woman with natural hair, confident stance, striking features",
    "East Asian woman with sleek bob, slim build, editorial expression",
    "Latina woman with long dark hair, curvy build, warm energy",
    "Middle Eastern woman with flowing hair, elegant posture, bold look",
    "mixed-race woman with curly afro, athletic build, radiant smile",
    "South Asian woman with long braided hair, graceful build, fierce gaze",
    "Black woman with short TWA, strong build, powerful presence",
    "White woman with wavy hair, lean build, relaxed cool vibe",
]

COLLECTION_BACKGROUNDS = {
    "black-rose": [
        "gothic cathedral interior with stained glass casting colored light on stone floors, moody and dark",
        "industrial Oakland warehouse with exposed brick, rusted beams, and dramatic single-source amber lighting",
        "concrete rooftop at twilight — city lights below, dark sky above, gritty urban texture",
        "dark contemporary art gallery with stark spotlights on raw concrete walls, shadows everywhere",
        "abandoned church with black roses growing through cracked stone walls, ethereal backlight",
        "rain-slicked downtown Oakland alley at night — warm amber streetlights reflecting off wet pavement, graffiti walls",
        "underground parking structure with cinematic neon strip-lighting cutting through darkness",
        "brutalist concrete overpass with ivy and roses breaking through, golden hour light from behind",
    ],
    "love-hurts": [
        "enchanted rose garden at golden hour with climbing red roses on iron trellises, soft romantic light",
        "vintage castle courtyard with weathered stone walls, wrought iron gates, and warm sunset pouring in",
        "romantic Parisian-style balcony overlooking a garden, wrought iron railing draped with red roses",
        "dimly lit vintage ballroom with crystal chandeliers, crimson velvet drapes, and candlelight",
        "secret garden pathway at dusk — rose-covered archway, soft fairy lights, dreamy atmosphere",
        "old-world wine cellar with warm candlelight, stone walls, and scattered red rose petals",
        "rooftop terrace at sunset with panoramic view, red roses in planters, warm amber and pink sky",
        "antique library with dark mahogany shelves, warm lamp light, and red leather chairs",
    ],
    "signature": [
        "Bay Area waterfront at golden hour — the Bay Bridge in soft-focus background, warm sunlight on the water",
        "modern Oakland downtown street with palm trees, clean sidewalks, and warm Californian sunlight",
        "sleek urban rooftop lounge with panoramic city skyline, string lights, and golden hour glow",
        "professional studio with rose-gold gradient backdrop and soft diffused lighting",
        "lush Oakland park with towering green trees, dappled sunlight filtering through leaves",
        "vintage Oakland storefront with character — exposed neon signage, warm golden afternoon light",
        "contemporary art-filled loft with floor-to-ceiling windows overlooking the city, natural light",
        "Bay Area hilltop viewpoint at sunset — rolling golden hills, distant San Francisco skyline",
    ],
}

# ── Product catalog with descriptions for accurate prompting ────────────────

PRODUCT_CATALOG = {
    "br-001": {
        "name": "BLACK Rose Crewneck",
        "desc": "Black crewneck sweatshirt with large silver metallic rose graphic on the front. Premium heavyweight cotton.",
        "collection": "black-rose",
        "type": "top",
    },
    "br-002": {
        "name": "BLACK Rose Joggers",
        "desc": "Black joggers with silver rose embroidery on the thigh. Tapered fit, ribbed cuffs.",
        "collection": "black-rose",
        "type": "bottom",
    },
    "br-003": {
        "name": "BLACK is Beautiful Jersey",
        "desc": "Black sports jersey with silver/white 'BLACK is Beautiful' lettering. Athletic cut.",
        "collection": "black-rose",
        "type": "top",
    },
    "br-004": {
        "name": "BLACK Rose Hoodie",
        "desc": "Black premium hoodie with large silver rose graphic on the front. Heavyweight cotton, kangaroo pocket.",
        "collection": "black-rose",
        "type": "top",
    },
    "br-005": {
        "name": "BLACK Rose Hoodie — Signature Edition",
        "desc": "Black premium hoodie with silver and gold rose detailing. Limited edition, heavyweight cotton.",
        "collection": "black-rose",
        "type": "top",
    },
    "br-006": {
        "name": "BLACK Rose Sherpa Jacket",
        "desc": "Black sherpa-lined jacket with silver rose embroidery. Warm, luxurious texture.",
        "collection": "black-rose",
        "type": "outerwear",
    },
    "br-007": {
        "name": "BLACK Rose Basketball Shorts",
        "desc": "Black basketball shorts with silver rose logo. Mesh panels, athletic fit.",
        "collection": "black-rose",
        "type": "bottom",
    },
    "br-008": {
        "name": "Women's BLACK Rose Hooded Dress",
        "desc": "Black hooded dress with silver rose graphic. Fitted silhouette, premium cotton.",
        "collection": "black-rose",
        "type": "dress",
    },
    "br-d01": {
        "name": "BLACK is Beautiful Hockey Jersey (Teal)",
        "desc": "Teal hockey jersey with 'BLACK is Beautiful' branding, black rose logo, teal and black stripes.",
        "collection": "black-rose",
        "type": "top",
        "source_override": "br-design-hockey-jersey.jpg",
    },
    "br-d02": {
        "name": "BLACK is Beautiful Football Jersey (Red #80)",
        "desc": "Red football jersey #80 with 'BLACK is Beautiful' on back, rose-filled numbers, black and red design.",
        "collection": "black-rose",
        "type": "top",
        "source_override": "br-design-football-jersey-red.jpg",
    },
    "br-d03": {
        "name": "BLACK is Beautiful Football Jersey (White #32)",
        "desc": "White football jersey #32 with 'BLACK is Beautiful' on back, alternating rose-filled numbers, black and white design.",
        "collection": "black-rose",
        "type": "top",
        "source_override": "br-design-football-jersey-white.jpg",
    },
    "br-d04": {
        "name": "BLACK is Beautiful Basketball Jersey",
        "desc": "Black basketball jersey with rose-filled number, 'BLACK is Beautiful' branding, gold accents.",
        "collection": "black-rose",
        "type": "top",
        "source_override": "br-design-basketball-jersey.jpg",
    },
    "lh-001": {
        "name": "The Fannie Pack",
        "desc": "Red crossbody fanny pack with 'Love Hurts' branding and rose emblem. Adjustable strap.",
        "collection": "love-hurts",
        "type": "accessory",
    },
    "lh-002": {
        "name": "Love Hurts Joggers (Black)",
        "desc": "Black joggers with red 'Love Hurts' embroidery. Tapered fit, crimson accents.",
        "collection": "love-hurts",
        "type": "bottom",
    },
    "lh-003": {
        "name": "Love Hurts Basketball Shorts",
        "desc": "Black and red basketball shorts with 'Love Hurts' branding, rose embroidery, mesh panels.",
        "collection": "love-hurts",
        "type": "bottom",
    },
    "lh-004": {
        "name": "Love Hurts Varsity Jacket",
        "desc": "White satin varsity jacket with 'Love Hurts' in red script on chest. Black sleeves, red/white ribbing, orange floral hood lining.",
        "collection": "love-hurts",
        "type": "outerwear",
    },
    "lh-005": {
        "name": "Love Hurts Windbreaker",
        "desc": "Red and black windbreaker with 'Love Hurts' branding. Lightweight, hooded.",
        "collection": "love-hurts",
        "type": "outerwear",
    },
    "sg-001": {
        "name": "The Bay Set",
        "desc": "Matching hoodie and jogger set in rose gold and black. 'SkyyRose' branding, premium cotton.",
        "collection": "signature",
        "type": "set",
    },
    "sg-002": {
        "name": "Stay Golden Set",
        "desc": "Gold and black matching set — hoodie with 'Stay Golden' text, matching joggers. Premium cotton.",
        "collection": "signature",
        "type": "set",
    },
    "sg-003": {
        "name": "The Signature Tee (Orchid)",
        "desc": "Orchid purple tee with rose gold SkyyRose logo. Relaxed fit, premium cotton.",
        "collection": "signature",
        "type": "top",
    },
    "sg-004": {
        "name": "Signature Hoodie (White)",
        "desc": "White premium hoodie with rose gold SkyyRose branding. Heavyweight cotton, kangaroo pocket.",
        "collection": "signature",
        "type": "top",
    },
    "sg-005": {
        "name": "Stay Golden Tee",
        "desc": "Black tee with gold 'Stay Golden' text and rose emblem. Relaxed fit.",
        "collection": "signature",
        "type": "top",
    },
    "sg-006": {
        "name": "Mint & Lavender Hoodie",
        "desc": "Mint green and lavender split-color hoodie with SkyyRose branding. Pastel luxury.",
        "collection": "signature",
        "type": "top",
    },
    "sg-007": {
        "name": "The Signature Beanie (Black)",
        "desc": "Black knit beanie with silver rose patch. One size fits all.",
        "collection": "signature",
        "type": "accessory",
        "source_override": "sg-007-beanie-black.jpg",
    },
    "sg-008": {
        "name": "The Signature Beanie (Forest Green)",
        "desc": "Forest green knit beanie with teal rose patch. One size fits all.",
        "collection": "signature",
        "type": "accessory",
        "source_override": "sg-008-beanie-green.jpg",
    },
    "sg-009": {
        "name": "The Sherpa Jacket",
        "desc": "Cream sherpa jacket with rose gold SkyyRose embroidery. Warm, luxurious texture.",
        "collection": "signature",
        "type": "outerwear",
    },
    "sg-010": {
        "name": "The Bridge Series Shorts",
        "desc": "Rose gold and black athletic shorts with Bay Bridge graphic. Mesh panels.",
        "collection": "signature",
        "type": "bottom",
    },
    "sg-011": {
        "name": "Original Label Tee (White)",
        "desc": "White tee with vintage-style SkyyRose label graphic. Classic fit.",
        "collection": "signature",
        "type": "top",
    },
    "sg-012": {
        "name": "Original Label Tee (Orchid)",
        "desc": "Orchid purple tee with vintage-style SkyyRose label graphic. Classic fit.",
        "collection": "signature",
        "type": "top",
    },
    "sg-d01": {
        "name": "Multi-Colored Windbreaker Set",
        "desc": "White windbreaker jacket and matching joggers with pastel V-chevron (pink, yellow, lavender, green). Pink hood, rose emblem, rainbow ribbed cuffs.",
        "collection": "signature",
        "type": "set",
    },
    "sg-d02": {
        "name": "The SkyyRose Collection Shorts",
        "desc": "Black athletic shorts with 'The Skyy Rose Collection' in gold script, gold mesh side panels with embroidered pink roses.",
        "collection": "signature",
        "type": "bottom",
        "source_override": "sg-d02-skyyrose-shorts-2.jpg",
    },
    "sg-d03": {
        "name": "Mint Rose Crewneck + Jogger Set",
        "desc": "Mint green crewneck sweatshirt and matching joggers with purple rose-growing-from-concrete graphic. Large rose on crewneck front, smaller emblem on jogger thigh. Ribbed cuffs, tapered joggers.",
        "collection": "signature",
        "type": "set",
        "source_override": "sg-d03-mint-crewneck-set.jpg",
    },
    "sg-d04": {
        "name": "Mint Rose Hooded Dress",
        "desc": "Mint green hooded dress with large purple rose-growing-from-concrete graphic on front. Kangaroo pocket, purple drawstrings, relaxed fit.",
        "collection": "signature",
        "type": "dress",
        "source_override": "sg-d04-mint-hooded-dress.jpg",
    },
}


def find_source_image(sku):
    """Find the best source image for a product."""
    info = PRODUCT_CATALOG.get(sku, {})
    if "source_override" in info:
        p = PRODUCTS_DIR / info["source_override"]
        if p.exists():
            return p

    candidates = list(PRODUCTS_DIR.glob(f"{sku}*.webp")) + list(PRODUCTS_DIR.glob(f"{sku}*.jpg"))
    real = [
        p
        for p in candidates
        if not any(
            x in p.stem
            for x in ["-render", "-front-model", "-back-model", "-branding", "-model-m", "-model-f"]
        )
    ]
    if not real:
        return None
    real.sort(key=lambda p: (p.suffix != ".webp", len(p.name)))
    return real[0]


def build_prompt(sku, gender, model_idx, bg_idx):
    """Build a model shot prompt with diversity."""
    info = PRODUCT_CATALOG[sku]
    product_desc = info["desc"]
    product_name = info["name"]
    product_type = info["type"]

    models = MALE_MODELS if gender == "m" else FEMALE_MODELS
    model_desc = models[model_idx % len(models)]
    collection = info.get("collection", "signature")
    backgrounds = COLLECTION_BACKGROUNDS.get(collection, COLLECTION_BACKGROUNDS["signature"])
    background = backgrounds[bg_idx % len(backgrounds)]

    gender_word = "man" if gender == "m" else "woman"

    # Accessories get styled differently
    if product_type == "accessory":
        if "beanie" in product_name.lower():
            wear_desc = "wearing this EXACT beanie on their head, styled casually"
        elif "fannie" in product_name.lower() or "fanny" in product_name.lower():
            wear_desc = "wearing this EXACT crossbody bag across their chest, styled with a plain black tee and jeans"
        else:
            wear_desc = "holding/wearing this EXACT accessory, styled casually"
    elif product_type == "bottom":
        wear_desc = f"wearing these EXACT {product_name}, paired with a plain black tee on top"
    elif product_type == "set":
        wear_desc = "wearing this EXACT matching set (top and bottom together)"
    elif product_type == "dress":
        wear_desc = "wearing this EXACT dress"
    elif product_type == "outerwear":
        wear_desc = "wearing this EXACT jacket/outerwear piece over a plain black tee"
    else:
        wear_desc = "wearing this EXACT top"

    prompt = (
        f"Full-body fashion editorial photograph of a {model_desc}, "
        f"{wear_desc}. "
        f"Product: {product_desc}. "
        f"The garment/product must be 100% identical to the reference image — same colors, same design, same details. "
        f"Background: {background}. "
        f"Style: high-end streetwear editorial photography, natural confident pose, "
        f"shot on medium format, shallow depth of field, warm cinematic lighting. "
        f"Full body visible from head to toe. No text overlays or watermarks."
    )
    return prompt


def init_client():
    """Initialize Google GenAI client."""
    from google import genai
    from google.genai.types import GenerateContentConfig, ImageConfig

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        env_file = PROJECT_ROOT / ".env.hf"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("GOOGLE_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break

    if not api_key:
        log.error("GOOGLE_API_KEY not found")
        sys.exit(1)

    return genai.Client(api_key=api_key), GenerateContentConfig, ImageConfig


def generate_model_shot(
    client, GenConfig, ImgConfig, sku, gender, model_idx, bg_idx, dry_run=False
):
    """Generate a single model shot."""
    from PIL import Image

    suffix = "m" if gender == "m" else "f"
    output_path = PRODUCTS_DIR / f"{sku}-model-{suffix}.webp"

    if output_path.exists() and output_path.stat().st_size / 1024 >= MIN_FILE_SIZE_KB:
        log.info(
            "  SKIP: %s already exists (%.1f KB)",
            output_path.name,
            output_path.stat().st_size / 1024,
        )
        return "skipped"

    prompt = build_prompt(sku, gender, model_idx, bg_idx)

    if dry_run:
        log.info("  DRY RUN: %s", output_path.name)
        return "skipped"

    source = find_source_image(sku)
    if not source:
        log.warning("  NO SOURCE IMAGE for %s — skipping", sku)
        return "failed"

    src_img = Image.open(source)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log.info("  Attempt %d/%d for %s", attempt, MAX_RETRIES, output_path.name)

            response = client.models.generate_content(
                model=MODEL_ID,
                contents=[
                    "REFERENCE PHOTO — the model must wear this EXACT product:",
                    src_img,
                    prompt,
                ],
                config=GenConfig(
                    response_modalities=["IMAGE"],
                    image_config=ImgConfig(aspect_ratio="3:4"),
                ),
            )

            if not response.candidates:
                log.warning("  No candidates")
                time.sleep(RETRY_DELAY_SEC)
                continue

            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    img = Image.open(io.BytesIO(part.inline_data.data))
                    img.save(output_path, "WEBP", quality=90)
                    kb = output_path.stat().st_size / 1024
                    if kb < MIN_FILE_SIZE_KB:
                        log.warning("  Too small (%.1f KB), retrying", kb)
                        output_path.unlink()
                        time.sleep(RETRY_DELAY_SEC)
                        break
                    log.info(
                        "  SUCCESS: %s (%.1f KB, %dx%d)",
                        output_path.name,
                        kb,
                        img.width,
                        img.height,
                    )
                    return "success"

        except Exception as e:
            log.error("  Error: %s", e)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SEC * attempt)

    log.error("  FAILED: %s", output_path.name)
    return "failed"


def main():
    parser = argparse.ArgumentParser(description="Generate diverse model shots")
    parser.add_argument("--sku", help="Generate for specific SKU only")
    parser.add_argument(
        "--gender", choices=["m", "f"], help="Generate only men's (m) or women's (f)"
    )
    parser.add_argument("--all", action="store_true", help="Generate all")
    parser.add_argument("--dry-run", action="store_true", help="List what would be generated")
    parser.add_argument(
        "--skip-existing", action="store_true", default=True, help="Skip existing files (default)"
    )
    args = parser.parse_args()

    if not args.sku and not args.all and not args.dry_run:
        parser.print_help()
        sys.exit(1)

    client, GenConfig, ImgConfig = init_client()

    skus = [args.sku] if args.sku else sorted(PRODUCT_CATALOG.keys())
    genders = [args.gender] if args.gender else ["m", "f"]

    total = {"success": 0, "failed": 0, "skipped": 0}
    job_count = 0

    log.info("=" * 60)
    log.info("DIVERSE MODEL SHOT GENERATOR")
    log.info(
        "Products: %d | Genders: %s | Total: ~%d shots",
        len(skus),
        genders,
        len(skus) * len(genders),
    )
    log.info("=" * 60)

    for i, sku in enumerate(skus):
        if sku not in PRODUCT_CATALOG:
            log.error("Unknown SKU: %s", sku)
            continue

        info = PRODUCT_CATALOG[sku]
        log.info("\n[%d/%d] %s — %s", i + 1, len(skus), sku, info["name"])

        for gender in genders:
            gender_label = "Men's" if gender == "m" else "Women's"
            log.info("  %s model shot:", gender_label)

            # Cycle through diverse models and backgrounds
            model_idx = i * 2 + (0 if gender == "m" else 1)
            bg_idx = i

            result = generate_model_shot(
                client,
                GenConfig,
                ImgConfig,
                sku,
                gender,
                model_idx,
                bg_idx,
                dry_run=args.dry_run,
            )
            total[result] += 1
            job_count += 1

            # Rate limit
            if result == "success" and job_count < len(skus) * len(genders):
                delay = 6
                log.info("  Rate limit pause (%ds)...", delay)
                time.sleep(delay)

    log.info("\n" + "=" * 60)
    log.info(
        "FINAL: %d success, %d failed, %d skipped (of %d)",
        total["success"],
        total["failed"],
        total["skipped"],
        job_count,
    )
    log.info("=" * 60)


if __name__ == "__main__":
    main()
