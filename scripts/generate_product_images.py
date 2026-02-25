"""SkyyRose Product Image Generator — Standalone Runner.

Generates branded AI model product images for all WooCommerce products
using Google Gemini's image generation API, then uploads to WordPress
and sets as featured images.

Usage:
    python3 scripts/generate_product_images.py
    python3 scripts/generate_product_images.py --dry-run  # Preview prompts only
    python3 scripts/generate_product_images.py --product BR-001  # Single product

Author: DevSkyy Platform Team
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx
from dotenv import load_dotenv

# =============================================================================
# Setup
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("skyyrose-imagery")

# Load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Output directory for generated images
OUTPUT_DIR = PROJECT_ROOT / "generated_images"
OUTPUT_DIR.mkdir(exist_ok=True)

# WordPress SSH config
WP_SSH_USER = "skyyrose.wordpress.com"
WP_SSH_HOST = "sftp.wp.com"
WP_SSH_PASS = os.getenv("SFTP_PASSWORD", "")
WP_UPLOAD_PATH = "/srv/htdocs/wp-content/uploads/skyyrose-products"

# Gemini config
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_API_KEY", "")
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_MODEL = "gemini-2.0-flash-exp-image-generation"  # Gemini 2.0 Flash Image Gen
GEMINI_MODEL_FALLBACK = "gemini-2.5-flash-image"  # Fallback

# Rate limiting
REQUESTS_PER_MINUTE = int(os.getenv("GEMINI_MAX_REQUESTS_PER_MINUTE", "8"))
DELAY_BETWEEN_REQUESTS = 60.0 / REQUESTS_PER_MINUTE


# =============================================================================
# Product Catalog — 100% accurate to WooCommerce
# =============================================================================


@dataclass
class Product:
    """WooCommerce product with imagery metadata."""

    sku: str
    name: str
    wp_id: int
    collection: str
    category_id: int
    price: str
    product_type: str  # e.g. "crewneck", "jersey", "hoodie"
    color: str = ""
    is_preorder: bool = False
    description: str = ""


# Every product exactly matching what's in WooCommerce
PRODUCTS: list[Product] = [
    # ── Black Rose Collection (cat 20) ──
    Product(
        sku="BR-001",
        name="BLACK Rose Crewneck",
        wp_id=9676,
        collection="black_rose",
        category_id=20,
        price="89.99",
        product_type="crewneck sweatshirt",
        color="black with silver rose embroidery",
        description="Luxury crewneck from the Black Rose Collection with gothic rose detailing.",
    ),
    Product(
        sku="BR-002",
        name="Last Oakland Jersey",
        wp_id=9677,
        collection="black_rose",
        category_id=20,
        price="149.99",
        product_type="athletic jersey",
        color="black and silver with Oakland-inspired lettering",
        is_preorder=True,
        description="Limited edition Last Oakland Jersey. Streetwear meets luxury.",
    ),
    Product(
        sku="BR-003",
        name="Black Rose Short Set - Onyx",
        wp_id=9678,
        collection="black_rose",
        category_id=20,
        price="119.99",
        product_type="matching short set (shorts + top)",
        color="solid onyx black with subtle rose pattern",
        is_preorder=True,
        description="Premium short set in Onyx colorway from the Black Rose Collection.",
    ),
    Product(
        sku="BR-004",
        name="Black Rose Short Set - Midnight",
        wp_id=9679,
        collection="black_rose",
        category_id=20,
        price="119.99",
        product_type="matching short set (shorts + top)",
        color="midnight blue-black with silver accents",
        is_preorder=True,
        description="Premium short set in Midnight colorway from the Black Rose Collection.",
    ),
    Product(
        sku="BR-005",
        name="Black Rose Sherpa Bomber",
        wp_id=9680,
        collection="black_rose",
        category_id=20,
        price="199.99",
        product_type="sherpa-lined bomber jacket",
        color="black sherpa exterior with satin rose-embroidered interior",
        is_preorder=True,
        description="Luxury Sherpa Bomber jacket with signature rose detailing.",
    ),
    # ── Love Hurts Collection (cat 18) ──
    Product(
        sku="LH-001",
        name="Crimson Heart Hoodie",
        wp_id=9681,
        collection="love_hurts",
        category_id=18,
        price="129.99",
        product_type="pullover hoodie",
        color="deep crimson red with rose gold heart graphics",
        description="Crimson Heart Hoodie with bold rose-crimson tones.",
    ),
    Product(
        sku="LH-002",
        name="Bleeding Rose Tee",
        wp_id=9682,
        collection="love_hurts",
        category_id=18,
        price="59.99",
        product_type="graphic t-shirt",
        color="black with crimson bleeding rose print",
        description="Signature Bleeding Rose graphic tee from the Love Hurts Collection.",
    ),
    Product(
        sku="LH-003",
        name="Thorned Embrace Joggers",
        wp_id=9683,
        collection="love_hurts",
        category_id=18,
        price="99.99",
        product_type="jogger pants",
        color="charcoal grey with rose gold thorn embroidery down the leg",
        description="Thorned Embrace Joggers. Comfort meets streetwear.",
    ),
    # ── Signature Collection (cat 19) ──
    Product(
        sku="SG-001",
        name="Rose Gold Varsity Jacket",
        wp_id=9684,
        collection="signature",
        category_id=19,
        price="249.99",
        product_type="varsity jacket",
        color="black wool body with rose gold leather sleeves and SR monogram",
        description="The signature Rose Gold Varsity Jacket. Premium leather and wool.",
    ),
    Product(
        sku="SG-002",
        name="Signature Logo Crewneck",
        wp_id=9685,
        collection="signature",
        category_id=19,
        price="89.99",
        product_type="crewneck sweatshirt",
        color="cream with rose gold embroidered SR monogram on chest",
        description="Classic Signature Logo Crewneck with embroidered SR monogram.",
    ),
    Product(
        sku="SG-003",
        name="Signature Track Pants",
        wp_id=9686,
        collection="signature",
        category_id=19,
        price="109.99",
        product_type="track pants",
        color="black with rose gold stripe and SR logo on thigh",
        description="Signature Collection Track Pants with rose gold accents.",
    ),
    # ── Kids Capsule Collection (cat 109) ──
    Product(
        sku="KC-001",
        name="Mini Rose Hoodie",
        wp_id=9687,
        collection="kids_capsule",
        category_id=109,
        price="69.99",
        product_type="kids pullover hoodie",
        color="soft pink with mini rose gold logo",
        description="Kids Mini Rose Hoodie. Same luxury quality, sized for young royalty.",
    ),
    Product(
        sku="KC-002",
        name="Little Legend Tee",
        wp_id=9688,
        collection="kids_capsule",
        category_id=109,
        price="39.99",
        product_type="kids graphic t-shirt",
        color="white with rose gold 'Little Legend' script",
        description="Kids Little Legend graphic tee from the Kids Capsule Collection.",
    ),
    # ── Pre-Order (existing) ──
    Product(
        sku="FP-001",
        name='The "Fannie" Pack',
        wp_id=9033,
        collection="signature",
        category_id=19,
        price="79.99",
        product_type="belt bag / fanny pack",
        color="rose gold hardware with black leather body and SR embossing",
        is_preorder=True,
        description="The Fannie Pack. Rose gold hardware, premium leather.",
    ),
]


# =============================================================================
# Collection Visual DNA
# =============================================================================

COLLECTION_STYLES: dict[str, dict[str, str]] = {
    "black_rose": {
        "setting": "dramatic midnight garden with wrought-iron gates, dark roses, silver moonlight filtering through gothic archways",
        "palette": "black, sterling silver, deep violet, midnight blue",
        "mood": "mysterious gothic elegance, shadows and silver light, powerful and dark",
        "lighting": "high-contrast silver moonlight with dramatic shadows, film noir aesthetic",
    },
    "love_hurts": {
        "setting": "candlelit baroque ballroom with rose petals scattered on marble floor, crimson velvet drapes",
        "palette": "crimson red, rose gold, blush pink, deep burgundy, soft white",
        "mood": "passionate vulnerability, romantic tension, bittersweet beauty",
        "lighting": "warm candlelight glow with golden hour softness, romantic haze",
    },
    "signature": {
        "setting": "luxurious gold-lit studio with marble pedestals, champagne-toned surfaces, subtle art deco details",
        "palette": "rose gold, cream, champagne, warm black, gold accents",
        "mood": "regal confidence, timeless sophistication, commanding presence",
        "lighting": "warm golden studio lighting, soft editorial fill, subtle rim light",
    },
    "kids_capsule": {
        "setting": "bright, playful luxury studio with soft pastel backdrop, rose gold confetti details, fun but elegant",
        "palette": "soft pink, rose gold, cream white, gentle lavender",
        "mood": "joyful elegance, playful luxury, young royalty energy",
        "lighting": "bright and airy, soft even lighting, no harsh shadows",
    },
}


# =============================================================================
# Prompt Builder
# =============================================================================


def build_product_prompt(product: Product) -> str:
    """Build a precise, product-specific prompt for Gemini image generation.

    Args:
        product: Product with all metadata

    Returns:
        Detailed prompt string for Gemini
    """
    style = COLLECTION_STYLES.get(product.collection, COLLECTION_STYLES["signature"])
    collection_display = product.collection.replace("_", " ").title()

    prompt = f"""Professional fashion photography for SkyyRose luxury streetwear brand.

BRAND: SkyyRose — "Where Love Meets Luxury" — Oakland-inspired luxury fashion.
COLLECTION: {collection_display}

PRODUCT: {product.name}
TYPE: {product.product_type}
COLOR/DETAILS: {product.color}
PRICE POINT: ${product.price} (premium luxury streetwear)

SCENE:
Setting: {style['setting']}
Color Palette: {style['palette']}
Mood: {style['mood']}
Lighting: {style['lighting']}

MODEL DIRECTION:
- Beautiful, confident AI model wearing the {product.name}
- The {product.product_type} is the hero of the shot — it must be clearly visible and accurate
- Model styled head-to-toe in {collection_display} collection aesthetic
- Pose: editorial confidence, fashion-forward, streetwear-meets-high-fashion energy
- Model should look like they belong on skyyrose.co — aspirational, Oakland luxury

PRODUCT ACCURACY (CRITICAL):
- The garment is a {product.product_type}
- Color: {product.color}
- Must show the complete garment clearly, not cropped or obscured
- Brand identity: SR monogram or rose motif where appropriate
- No text, no watermarks, no logos that aren't part of the design

COMPOSITION:
- Three-quarter body shot, slightly off-center
- Leave breathing room for potential text overlay on one side
- Clean background that matches the {collection_display} collection setting
- High-end fashion editorial quality — this goes on a luxury e-commerce site
- Aspect ratio: 3:4 (portrait, product-focused)

STYLE: Cinematic luxury fashion photography, shot on medium format camera, shallow depth of field, rich color grading matching the {style['palette']} palette. This is NOT stock photography — it should feel like a Drake/OVO-level fashion editorial."""

    return prompt


# =============================================================================
# Gemini API Client (Standalone)
# =============================================================================


async def generate_image_gemini(
    prompt: str,
    *,
    api_key: str,
    aspect_ratio: str = "3:4",
    model: str = GEMINI_MODEL,
    timeout: float = 120.0,
) -> bytes | None:
    """Generate image via Gemini API and return raw PNG bytes.

    Args:
        prompt: Image generation prompt
        api_key: Gemini API key
        aspect_ratio: Output aspect ratio
        model: Gemini model ID
        timeout: Request timeout

    Returns:
        PNG image bytes or None if generation failed
    """
    url = f"{GEMINI_API_BASE}/models/{model}:generateContent?key={api_key}"

    generation_config: dict = {
        "responseModalities": ["TEXT", "IMAGE"],
    }

    # Only add imageConfig if model supports it
    if "2.5" in model or "3" in model or "nano" in model:
        generation_config["imageConfig"] = {"aspectRatio": aspect_ratio}

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": generation_config,
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(3):
            try:
                response = await client.post(url, json=payload)

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "60"))
                    logger.warning(f"Rate limited. Waiting {retry_after}s...")
                    await asyncio.sleep(retry_after)
                    continue

                if response.status_code == 400:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "")
                    logger.error(f"Bad request: {error_msg}")
                    return None

                if response.status_code != 200:
                    logger.error(f"API error {response.status_code}: {response.text[:200]}")
                    if response.status_code >= 500:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    return None

                data = response.json()

                # Extract image from response
                candidates = data.get("candidates", [])
                for candidate in candidates:
                    parts = candidate.get("content", {}).get("parts", [])
                    for part in parts:
                        if "inlineData" in part:
                            inline = part["inlineData"]
                            return base64.b64decode(inline["data"])

                logger.warning("No image in response")
                return None

            except httpx.TimeoutException:
                logger.warning(f"Timeout on attempt {attempt + 1}/3")
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Request failed: {e}")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)

    return None


# =============================================================================
# WordPress Upload
# =============================================================================


def ssh_cmd(command: str) -> str:
    """Run command on WordPress.com via SSH."""
    ssh = (
        f"sshpass -p '{WP_SSH_PASS}' ssh -o StrictHostKeyChecking=no "
        f"{WP_SSH_USER}@{WP_SSH_HOST} \"{command}\""
    )
    result = subprocess.run(ssh, shell=True, capture_output=True, text=True, timeout=30)
    return result.stdout.strip()


def scp_upload(local_path: str, remote_path: str) -> bool:
    """Upload file to WordPress.com via SCP."""
    scp = (
        f"sshpass -p '{WP_SSH_PASS}' scp -o StrictHostKeyChecking=no "
        f"{local_path} {WP_SSH_USER}@{WP_SSH_HOST}:{remote_path}"
    )
    result = subprocess.run(scp, shell=True, capture_output=True, text=True, timeout=60)
    return result.returncode == 0


def upload_and_attach(product: Product, image_path: Path) -> int | None:
    """Upload image to WordPress media library and set as product featured image.

    Args:
        product: Product to attach image to
        image_path: Local path to generated image

    Returns:
        WordPress media attachment ID or None
    """
    filename = image_path.name
    collection_display = product.collection.replace("_", " ").title()

    # Ensure upload directory exists
    ssh_cmd(f"mkdir -p {WP_UPLOAD_PATH}")

    # Upload file
    remote_path = f"{WP_UPLOAD_PATH}/{filename}"
    if not scp_upload(str(image_path), remote_path):
        logger.error(f"SCP upload failed for {filename}")
        return None

    # Import into WordPress media library
    title = f"SkyyRose {product.name} — {collection_display}"
    alt_text = f"{product.name} from SkyyRose {collection_display} Collection — luxury fashion product photography"

    import_cmd = (
        f"wp media import {remote_path} "
        f"--title='{title}' "
        f"--alt='{alt_text}' "
        f"--porcelain"
    )
    media_id_str = ssh_cmd(import_cmd)

    if not media_id_str or not media_id_str.strip().isdigit():
        logger.error(f"Media import failed for {filename}: {media_id_str}")
        return None

    media_id = int(media_id_str.strip())

    # Set as product featured image (thumbnail)
    ssh_cmd(f"wp post meta update {product.wp_id} _thumbnail_id {media_id}")
    logger.info(f"Set media {media_id} as featured image for {product.name} (ID {product.wp_id})")

    return media_id


# =============================================================================
# Main Runner
# =============================================================================


async def generate_for_product(
    product: Product,
    *,
    api_key: str,
    dry_run: bool = False,
    skip_upload: bool = False,
) -> dict:
    """Generate image for a single product.

    Args:
        product: Product to generate for
        api_key: Gemini API key
        dry_run: If True, only print prompts
        skip_upload: If True, generate but don't upload

    Returns:
        Result dict with status and paths
    """
    prompt = build_product_prompt(product)
    image_filename = f"skyyrose-{product.sku.lower()}-{product.collection}.png"
    image_path = OUTPUT_DIR / image_filename

    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Processing {product.sku}: {product.name}")

    if dry_run:
        print(f"\n{'='*60}")
        print(f"SKU: {product.sku} | {product.name}")
        print(f"Collection: {product.collection} | WP ID: {product.wp_id}")
        print(f"{'='*60}")
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        return {"sku": product.sku, "status": "dry_run", "prompt_length": len(prompt)}

    # Check if already generated
    if image_path.exists() and image_path.stat().st_size > 10000:
        logger.info(f"Image already exists: {image_path.name} ({image_path.stat().st_size:,} bytes)")
        if not skip_upload:
            media_id = upload_and_attach(product, image_path)
            return {"sku": product.sku, "status": "cached_upload", "media_id": media_id}
        return {"sku": product.sku, "status": "cached", "path": str(image_path)}

    # Generate via Gemini
    logger.info(f"Generating image for {product.sku}...")
    image_bytes = await generate_image_gemini(prompt, api_key=api_key)

    if not image_bytes:
        logger.error(f"FAILED to generate image for {product.sku}")
        return {"sku": product.sku, "status": "failed"}

    # Save locally
    image_path.write_bytes(image_bytes)
    logger.info(f"Saved: {image_path.name} ({len(image_bytes):,} bytes)")

    # Upload to WordPress
    media_id = None
    if not skip_upload:
        media_id = upload_and_attach(product, image_path)

    return {
        "sku": product.sku,
        "status": "success",
        "path": str(image_path),
        "size_bytes": len(image_bytes),
        "media_id": media_id,
    }


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate SkyyRose product images")
    parser.add_argument("--dry-run", action="store_true", help="Preview prompts only")
    parser.add_argument("--skip-upload", action="store_true", help="Generate but don't upload")
    parser.add_argument("--product", type=str, help="Generate for single SKU (e.g. BR-001)")
    parser.add_argument("--collection", type=str, help="Filter by collection (e.g. black_rose)")
    args = parser.parse_args()

    # Validate API key
    if not GEMINI_API_KEY and not args.dry_run:
        logger.error("GEMINI_API_KEY or GOOGLE_AI_API_KEY not set in .env")
        sys.exit(1)

    # Validate SSH password for uploads
    if not WP_SSH_PASS and not args.dry_run and not args.skip_upload:
        logger.error("SFTP_PASSWORD not set in .env")
        sys.exit(1)

    # Filter products
    products = PRODUCTS
    if args.product:
        products = [p for p in products if p.sku == args.product.upper()]
        if not products:
            logger.error(f"Product {args.product} not found")
            sys.exit(1)
    if args.collection:
        products = [p for p in products if p.collection == args.collection]
        if not products:
            logger.error(f"Collection {args.collection} not found")
            sys.exit(1)

    logger.info(f"SkyyRose Imagery Generator — {len(products)} products")
    logger.info(f"Output: {OUTPUT_DIR}")
    if args.dry_run:
        logger.info("DRY RUN MODE — prompts only, no API calls")

    results = []
    for i, product in enumerate(products):
        result = await generate_for_product(
            product,
            api_key=GEMINI_API_KEY,
            dry_run=args.dry_run,
            skip_upload=args.skip_upload,
        )
        results.append(result)

        # Rate limiting between API calls
        if not args.dry_run and i < len(products) - 1:
            logger.info(f"Rate limit delay: {DELAY_BETWEEN_REQUESTS:.1f}s...")
            await asyncio.sleep(DELAY_BETWEEN_REQUESTS)

    # Summary
    print(f"\n{'='*60}")
    print("GENERATION SUMMARY")
    print(f"{'='*60}")

    success = sum(1 for r in results if r["status"] in ("success", "cached_upload", "cached"))
    failed = sum(1 for r in results if r["status"] == "failed")

    for r in results:
        status_icon = {
            "success": "OK",
            "cached": "CACHED",
            "cached_upload": "CACHED+UPLOADED",
            "failed": "FAIL",
            "dry_run": "DRY",
        }.get(r["status"], "?")
        media_info = f" (media #{r['media_id']})" if r.get("media_id") else ""
        print(f"  [{status_icon}] {r['sku']}{media_info}")

    print(f"\nTotal: {len(results)} | Success: {success} | Failed: {failed}")

    # Save results manifest
    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(results, indent=2))
    logger.info(f"Manifest saved: {manifest_path}")


if __name__ == "__main__":
    asyncio.run(main())
