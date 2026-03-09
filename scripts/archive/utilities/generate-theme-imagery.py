#!/usr/bin/env python3
"""
SkyyRose Theme Imagery Generator

Generates all missing theme assets using Gemini image generation:
  - About page story images (3)
  - Founder portrait (1)
  - Instagram feed lifestyle shots (6)
  - Mascot variants (7: reference + 6 context-specific)

Usage:
    source .venv-imagery/bin/activate
    python scripts/generate-theme-imagery.py --dry-run
    python scripts/generate-theme-imagery.py --category about
    python scripts/generate-theme-imagery.py --category instagram
    python scripts/generate-theme-imagery.py --category mascot
    python scripts/generate-theme-imagery.py --all
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
log = logging.getLogger("theme-imagery")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
THEME_DIR = PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship"
IMAGES_DIR = THEME_DIR / "assets" / "images"
MASCOT_DIR = IMAGES_DIR / "mascot"
INSTAGRAM_DIR = IMAGES_DIR / "instagram"

MODEL_ID = "gemini-2.5-flash-image"
MIN_FILE_SIZE_KB = 20
MAX_RETRIES = 3
RETRY_DELAY_SEC = 8

# ── Brand constants ─────────────────────────────────────────────────────────

BRAND_STYLE = (
    "SkyyRose luxury streetwear brand. Colors: rose gold (#B76E79), black (#0a0a0a), "
    "gold (#d4af37). Based in Oakland, California. Tagline: 'Luxury Grows from Concrete.' "
    "Aesthetic: luxury streetwear, urban elegance, editorial fashion photography. "
    "The brand blends authentic street culture with high-end craftsmanship."
)

# ── About Page Images ───────────────────────────────────────────────────────

ABOUT_IMAGES = [
    {
        "filename": "about-story-0.jpg",
        "output_dir": IMAGES_DIR,
        "prompt": (
            "Editorial lifestyle photograph for a luxury streetwear brand's 'About' page. "
            "Scene: A young Black creative entrepreneur sketching fashion designs late at night "
            "in a small Oakland apartment. Warm lamplight illuminates design sketches spread "
            "across a table. Mood: intimate, aspirational, the birth of a dream. "
            "Style: cinematic documentary photography, shallow depth of field, warm golden "
            "tones mixed with deep shadows. Shot on medium format. No text or logos."
        ),
        "aspect_ratio": "4:3",
    },
    {
        "filename": "about-story-1.jpg",
        "output_dir": IMAGES_DIR,
        "prompt": (
            "Editorial lifestyle photograph for a luxury streetwear brand. "
            "Scene: A single rose growing through a crack in concrete, with the Oakland "
            "skyline visible in the soft-focus background during golden hour. The rose has "
            "warm rose-gold tones. Concept: 'where the sky meets the rose' — reaching high "
            "while staying grounded. "
            "Style: fine art photography, dreamy bokeh, warm golden-hour light, "
            "slightly desaturated except for the rose. Cinematic composition. No text or logos."
        ),
        "aspect_ratio": "4:3",
    },
    {
        "filename": "about-story-2.jpg",
        "output_dir": IMAGES_DIR,
        "prompt": (
            "Editorial close-up photograph for a luxury streetwear brand's craftsmanship section. "
            "Scene: Hands carefully examining premium fabric and embroidered details on a "
            "dark garment. Rose gold thread visible in the stitching. A workbench with fabric "
            "swatches, thread spools, and quality tools visible in the background. "
            "Mood: meticulous care, artisan craftsmanship, luxury materials. "
            "Style: product/editorial photography, macro lens, shallow depth of field, "
            "dramatic side lighting on dark background. No text or logos."
        ),
        "aspect_ratio": "4:3",
    },
    {
        "filename": "founder-portrait.jpg",
        "output_dir": IMAGES_DIR,
        "prompt": (
            "Professional editorial portrait of a young Black male fashion entrepreneur "
            "and streetwear brand founder, late 20s. He's wearing a premium black hoodie "
            "with subtle rose-gold accents. Standing confidently with arms crossed, "
            "looking directly at camera with a warm but determined expression. "
            "Background: blurred urban Oakland environment, golden hour light. "
            "Style: GQ/Vogue editorial portrait, medium format look, shallow depth of field, "
            "warm skin tones, professional studio-quality lighting with natural feel. "
            "Composition: 4:5 portrait crop, subject fills frame from waist up. No text or logos."
        ),
        "aspect_ratio": "3:4",
    },
]

# ── Instagram Feed Images ───────────────────────────────────────────────────

INSTAGRAM_IMAGES = [
    {
        "filename": "insta-1-black-rose-shoot.jpg",
        "output_dir": INSTAGRAM_DIR,
        "prompt": (
            "Instagram-style fashion editorial photo. A Black male model wearing a premium "
            "black crewneck with silver metallic rose embroidery, posing against a dark "
            "industrial backdrop with dramatic rim lighting. Gothic luxury streetwear aesthetic. "
            "The mood is powerful and elegant. Square crop, high contrast, "
            "editorial fashion photography. Black Rose collection vibes — silver on black. "
            "No text or watermarks."
        ),
        "aspect_ratio": "1:1",
    },
    {
        "filename": "insta-2-love-hurts-detail.jpg",
        "output_dir": INSTAGRAM_DIR,
        "prompt": (
            "Instagram-style close-up product detail shot. A crimson red varsity jacket "
            "sleeve with 'Love Hurts' embroidered in elegant script, with rose embellishments. "
            "The jacket is draped over a velvet surface. Warm, moody lighting with red "
            "and rose-gold tones. Luxury texture photography, shallow depth of field. "
            "Square crop, editorial product photography. No text overlay."
        ),
        "aspect_ratio": "1:1",
    },
    {
        "filename": "insta-3-oakland-skyline.jpg",
        "output_dir": INSTAGRAM_DIR,
        "prompt": (
            "Instagram-style lifestyle photo. A figure wearing premium streetwear "
            "standing on a rooftop overlooking the Oakland, California skyline at dusk. "
            "City lights beginning to glow, warm rose-gold sunset sky. The person is "
            "silhouetted against the sky, wearing a dark hoodie. Urban luxury vibes, "
            "aspirational, the city as a backdrop to ambition. "
            "Square crop, cinematic photography, warm color grading. No text."
        ),
        "aspect_ratio": "1:1",
    },
    {
        "filename": "insta-4-signature-bts.jpg",
        "output_dir": INSTAGRAM_DIR,
        "prompt": (
            "Instagram-style behind-the-scenes photo from a fashion photoshoot. "
            "A clothing rack with premium streetwear pieces in rose-gold, gold, and black. "
            "A photographer and stylist visible in the background, blurred. Studio lights "
            "and reflectors visible. The aesthetic is professional but candid — showing "
            "the real work behind a luxury streetwear collection. Warm, golden tones. "
            "Square crop, documentary-style photography. No text."
        ),
        "aspect_ratio": "1:1",
    },
    {
        "filename": "insta-5-customer-lifestyle.jpg",
        "output_dir": INSTAGRAM_DIR,
        "prompt": (
            "Instagram-style street photography. A confident Black woman walking through "
            "an urban neighborhood wearing a premium black hoodie with rose gold accents. "
            "She's carrying a coffee cup, natural stride, candid feel. Warm afternoon light, "
            "urban environment with graffiti walls in soft focus behind her. "
            "Street style photography, authentic and aspirational. "
            "Square crop, warm color grading. No text or watermarks."
        ),
        "aspect_ratio": "1:1",
    },
    {
        "filename": "insta-6-popup-event.jpg",
        "output_dir": INSTAGRAM_DIR,
        "prompt": (
            "Instagram-style event photography. A vibrant pop-up shop event scene — "
            "a stylish retail space with rose-gold accents, neon 'SKYYROSE' sign glowing "
            "on the wall, clothing racks with premium streetwear, and a diverse crowd of "
            "fashionable young people socializing and browsing. DJ booth in corner. "
            "Energy: exclusive, exciting, community-driven. Warm ambient lighting with "
            "pink/rose-gold accent lights. Square crop, event photography. No text overlay."
        ),
        "aspect_ratio": "1:1",
    },
]

# ── Mascot Images ───────────────────────────────────────────────────────────

MASCOT_BASE_PROMPT = (
    "A cute, stylized mascot character for a luxury streetwear brand called SkyyRose. "
    "The mascot is a small anthropomorphic rose character with rose-gold petals, "
    "wearing tiny premium streetwear. It has expressive eyes, a friendly personality, "
    "and a cool urban attitude. The character stands on two small legs and has "
    "leaf-like arms. Style: clean vector illustration on transparent background, "
    "soft shading, kawaii meets streetwear aesthetic. PNG with alpha transparency."
)

MASCOT_IMAGES = [
    {
        "filename": "skyyrose-mascot-reference.png",
        "output_dir": MASCOT_DIR,
        "prompt": (
            f"{MASCOT_BASE_PROMPT} "
            "The mascot is in a neutral standing pose, waving with one leaf-arm. "
            "Wearing a tiny black hoodie with a rose-gold rose emblem. "
            "This is the reference/default pose used across the site. "
            "Full body, centered, white background."
        ),
    },
    {
        "filename": "skyyrose-mascot-404.png",
        "output_dir": MASCOT_DIR,
        "prompt": (
            f"{MASCOT_BASE_PROMPT} "
            "The mascot looks confused and lost, holding a torn map, with a question mark "
            "floating above its head. One petal is slightly drooping. "
            "Wearing a tiny black hoodie. Expression: adorably bewildered. "
            "Concept: 'page not found' error page mascot. White background."
        ),
    },
    {
        "filename": "skyyrose-mascot-homepage.png",
        "output_dir": MASCOT_DIR,
        "prompt": (
            f"{MASCOT_BASE_PROMPT} "
            "The mascot is in a welcoming, arms-wide-open pose, with sparkles around it. "
            "Wearing a premium-looking tiny black and rose-gold outfit. "
            "Expression: warm, inviting, confident smile. "
            "Concept: welcoming visitors to the homepage. White background."
        ),
    },
    {
        "filename": "skyyrose-mascot-black-rose.png",
        "output_dir": MASCOT_DIR,
        "prompt": (
            f"{MASCOT_BASE_PROMPT} "
            "The mascot has dark, gothic-elegant styling — petals are deep midnight black "
            "with silver metallic edges. Wearing a tiny silver-accented black crewneck. "
            "Expression: cool, mysterious, powerful. Standing with arms crossed. "
            "Concept: Black Rose collection — elegance in darkness. White background."
        ),
    },
    {
        "filename": "skyyrose-mascot-love-hurts.png",
        "output_dir": MASCOT_DIR,
        "prompt": (
            f"{MASCOT_BASE_PROMPT} "
            "The mascot's petals are deep crimson red. Wearing a tiny red varsity jacket "
            "with a heart patch. One leaf-arm is placed over its heart, the other holds "
            "a small rose. Expression: passionate, emotional, bold. "
            "Small floating hearts around it. "
            "Concept: Love Hurts collection — wear your heart outside. White background."
        ),
    },
    {
        "filename": "skyyrose-mascot-signature.png",
        "output_dir": MASCOT_DIR,
        "prompt": (
            f"{MASCOT_BASE_PROMPT} "
            "The mascot has luxurious rose-gold and gold coloring. Wearing a tiny "
            "gold-accented jacket and a miniature crown. Expression: regal, confident, "
            "like royalty. Standing tall with one arm on hip. Small gold sparkles. "
            "Concept: Signature collection — the crown jewel. White background."
        ),
    },
    {
        "filename": "skyyrose-mascot-preorder.png",
        "output_dir": MASCOT_DIR,
        "prompt": (
            f"{MASCOT_BASE_PROMPT} "
            "The mascot is excitedly holding up a tiny shopping bag with a rose-gold bow "
            "on it, eyes wide with anticipation. One leg is lifted in excitement. "
            "A small clock or countdown timer icon floats nearby. "
            "Expression: excited, eager, can't-wait energy. "
            "Concept: pre-order page — exciting upcoming drops. White background."
        ),
    },
]


# ── Generation Engine ───────────────────────────────────────────────────────


def init_client():
    """Initialize Google GenAI client."""
    try:
        from google import genai
        from google.genai.types import GenerateContentConfig, ImageConfig
    except ImportError:
        log.error("google-genai not installed. Run: pip install google-genai")
        sys.exit(1)

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        # Try loading from .env.hf
        env_file = PROJECT_ROOT / ".env.hf"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("GOOGLE_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break

    if not api_key:
        log.error("GOOGLE_API_KEY not found. Set it in environment or .env.hf")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    return client, GenerateContentConfig, ImageConfig


def generate_image(
    client,
    GenerateContentConfig,
    ImageConfig,
    prompt,
    output_path,
    aspect_ratio="1:1",
    reference_image=None,
):
    """Generate a single image with retry logic."""
    from PIL import Image

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log.info("  Attempt %d/%d for %s", attempt, MAX_RETRIES, output_path.name)

            contents = []
            if reference_image:
                ref_img = Image.open(reference_image)
                contents.append("Use this image as style reference:")
                contents.append(ref_img)
            contents.append(prompt)

            config = GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=ImageConfig(
                    aspect_ratio=aspect_ratio,
                ),
            )

            response = client.models.generate_content(
                model=MODEL_ID,
                contents=contents,
                config=config,
            )

            # Extract image from response
            if not response.candidates:
                log.warning("  No candidates in response")
                time.sleep(RETRY_DELAY_SEC)
                continue

            image_part = None
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    image_part = part
                    break

            if not image_part:
                log.warning("  No image in response parts")
                time.sleep(RETRY_DELAY_SEC)
                continue

            img_data = image_part.inline_data.data
            img = Image.open(io.BytesIO(img_data))

            # Save as appropriate format
            if output_path.suffix == ".png":
                img.save(output_path, "PNG", optimize=True)
            elif output_path.suffix == ".webp":
                img.save(output_path, "WEBP", quality=90)
            else:
                img.convert("RGB").save(output_path, "JPEG", quality=92)

            file_size_kb = output_path.stat().st_size / 1024
            if file_size_kb < MIN_FILE_SIZE_KB:
                log.warning("  File too small (%.1f KB), retrying...", file_size_kb)
                output_path.unlink()
                time.sleep(RETRY_DELAY_SEC)
                continue

            log.info(
                "  SUCCESS: %s (%.1f KB, %dx%d)",
                output_path.name,
                file_size_kb,
                img.width,
                img.height,
            )
            return True

        except Exception as e:
            log.error("  Error: %s", e)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SEC * attempt)

    log.error("  FAILED after %d attempts: %s", MAX_RETRIES, output_path.name)
    return False


def run_category(client, GenerateContentConfig, ImageConfig, images, category_name, dry_run=False):
    """Generate all images in a category."""
    log.info("=" * 60)
    log.info("CATEGORY: %s (%d images)", category_name, len(images))
    log.info("=" * 60)

    results = {"success": 0, "failed": 0, "skipped": 0}

    for i, img_def in enumerate(images, 1):
        output_path = img_def["output_dir"] / img_def["filename"]
        aspect = img_def.get("aspect_ratio", "1:1")

        log.info("[%d/%d] %s (aspect: %s)", i, len(images), img_def["filename"], aspect)

        if output_path.exists():
            file_size_kb = output_path.stat().st_size / 1024
            if file_size_kb >= MIN_FILE_SIZE_KB:
                log.info("  SKIP: already exists (%.1f KB)", file_size_kb)
                results["skipped"] += 1
                continue

        if dry_run:
            log.info("  DRY RUN: would generate %s", output_path)
            results["skipped"] += 1
            continue

        ref_image = img_def.get("reference_image")
        success = generate_image(
            client,
            GenerateContentConfig,
            ImageConfig,
            img_def["prompt"],
            output_path,
            aspect,
            ref_image,
        )

        if success:
            results["success"] += 1
        else:
            results["failed"] += 1

        # Rate limit: wait between API calls
        if i < len(images):
            delay = 6
            log.info("  Waiting %ds for rate limit...", delay)
            time.sleep(delay)

    log.info("-" * 40)
    log.info(
        "RESULTS: %d success, %d failed, %d skipped",
        results["success"],
        results["failed"],
        results["skipped"],
    )
    return results


def main():
    parser = argparse.ArgumentParser(description="Generate SkyyRose theme imagery")
    parser.add_argument(
        "--category", choices=["about", "instagram", "mascot"], help="Generate specific category"
    )
    parser.add_argument("--all", action="store_true", help="Generate all categories")
    parser.add_argument("--dry-run", action="store_true", help="List what would be generated")
    args = parser.parse_args()

    if not args.category and not args.all and not args.dry_run:
        parser.print_help()
        sys.exit(1)

    client, GenerateContentConfig, ImageConfig = init_client()

    total = {"success": 0, "failed": 0, "skipped": 0}

    categories = {
        "about": (ABOUT_IMAGES, "About Page (4 images)"),
        "instagram": (INSTAGRAM_IMAGES, "Instagram Feed (6 images)"),
        "mascot": (MASCOT_IMAGES, "Mascot Variants (7 images)"),
    }

    if args.all or args.dry_run:
        run_list = ["about", "instagram", "mascot"]
    else:
        run_list = [args.category]

    for cat in run_list:
        images, label = categories[cat]
        results = run_category(
            client, GenerateContentConfig, ImageConfig, images, label, dry_run=args.dry_run
        )
        for k in total:
            total[k] += results[k]

    log.info("=" * 60)
    log.info(
        "TOTAL: %d success, %d failed, %d skipped (of %d)",
        total["success"],
        total["failed"],
        total["skipped"],
        total["success"] + total["failed"] + total["skipped"],
    )
    log.info("=" * 60)


if __name__ == "__main__":
    main()
