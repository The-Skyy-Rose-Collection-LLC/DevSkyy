"""Generate immersive scene background images for SkyyRose.

Creates the fullscreen atmospheric scene images that serve as backgrounds
for the drakerelated.com-style immersive experience pages.

Usage:
    python3 scripts/generate_scene_images.py
    python3 scripts/generate_scene_images.py --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import logging
import os
import subprocess
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("skyyrose-scenes")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_API_KEY", "")
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_MODEL = "gemini-2.0-flash-exp-image-generation"

WP_SSH_PASS = os.getenv("SFTP_PASSWORD", "")
WP_SSH_USER = "skyyrose.wordpress.com"
WP_SSH_HOST = "sftp.wp.com"

OUTPUT_DIR = PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "scenes"


# =============================================================================
# Scene Definitions
# =============================================================================

SCENES = [
    # ── Black Rose: The Garden ──
    {
        "filename": "black-rose-garden.jpg",
        "prompt": (
            "Ultra-wide cinematic photograph of a gothic midnight garden scene. "
            "Wrought-iron gates and archways draped in black roses. Sterling silver moonlight "
            "filters through misty cathedral spires in the background. Dark marble pathways "
            "with scattered black rose petals. Deep violet and midnight blue atmospheric haze. "
            "Dramatic shadows and pools of silver light. No people. "
            "Luxury fashion editorial set design. Aspect ratio 16:9 ultra-wide. "
            "Cinematic lighting, film-grade color grading, 8K quality. "
            "This is a background scene for a drakerelated.com-style immersive shopping experience."
        ),
    },
    # ── Love Hurts: The Ballroom ──
    {
        "filename": "love-hurts-ballroom.jpg",
        "prompt": (
            "Ultra-wide cinematic photograph of a baroque ballroom interior. "
            "Crystal chandeliers casting warm golden candlelight across the room. "
            "Crimson velvet drapery frames tall arched windows. Rose petals scattered "
            "across polished marble floor. Blush pink fog drifts through the space. "
            "Ornate gold moldings and mirrors reflect flickering candlelight. "
            "Deep burgundy and rose gold color palette. Romantic, passionate atmosphere. "
            "No people. Luxury fashion editorial set design. Aspect ratio 16:9. "
            "Cinematic photography, warm golden hour lighting, 8K quality. "
            "Background for an immersive fashion shopping experience."
        ),
    },
    # ── Love Hurts: The Manor ──
    {
        "filename": "love-hurts-manor.jpg",
        "prompt": (
            "Ultra-wide cinematic photograph of a candlelit gothic manor interior. "
            "Deep crimson velvet armchairs and golden pedestals displaying candelabras. "
            "Flickering candlelight creates dancing shadows on dark wood paneling. "
            "A grand fireplace with carved roses glows warmly. Rose gold accents "
            "throughout. Heavy crimson curtains, dark wood floors with a plush rug. "
            "Intimate, romantic, bittersweet beauty. No people. "
            "Luxury fashion editorial set. Aspect ratio 16:9. "
            "Cinematic photography, warm candlelight, 8K quality."
        ),
    },
    # ── Signature: The Runway ──
    {
        "filename": "signature-runway.jpg",
        "prompt": (
            "Ultra-wide cinematic photograph of a luxury fashion runway set. "
            "Long elevated catwalk with rose gold trim and warm golden spotlights. "
            "Champagne-toned marble floor reflects the lights. Art deco geometric "
            "patterns on the walls in gold and cream. Subtle fog machine haze "
            "catches the warm amber lighting. Empty front-row seats in black velvet. "
            "Regal, commanding, sophisticated atmosphere. No people. "
            "High-end fashion show production design. Aspect ratio 16:9. "
            "Cinematic photography, dramatic stage lighting, 8K quality."
        ),
    },
    # ── Signature: The Showroom ──
    {
        "filename": "signature-showroom.jpg",
        "prompt": (
            "Ultra-wide cinematic photograph of an exclusive luxury showroom. "
            "Marble pedestals and glass display cases with warm golden uplighting. "
            "Rose gold clothing racks with premium garments. Champagne-colored walls "
            "with subtle art deco detailing. Soft amber spotlights create pools of "
            "warm light. A large mirror with gold frame reflects the space. "
            "Elegant, timeless, sophisticated. No people. "
            "Luxury fashion retail interior design. Aspect ratio 16:9. "
            "Cinematic photography, warm studio lighting, 8K quality."
        ),
    },
    # ── Signature: The Fitting Room ──
    {
        "filename": "signature-fitting-room.jpg",
        "prompt": (
            "Ultra-wide cinematic photograph of a VIP luxury fitting room. "
            "Plush cream velvet seating and a three-panel mirror with gold frames. "
            "Rose gold hangers on a minimal rack. Warm soft lighting from art deco "
            "sconces. Champagne carpet, cream walls with subtle gold trim. "
            "A small marble table with fresh roses in a gold vase. "
            "Intimate, exclusive, personal luxury. No people. "
            "High-end retail fitting room design. Aspect ratio 16:9. "
            "Cinematic photography, soft warm lighting, 8K quality."
        ),
    },
    # ── Product Hotspot Thumbnails: Black Rose ──
    {
        "filename": "black-rose-product-1.jpg",
        "prompt": "Product photograph of a luxury sterling silver and black necklace with thorned rose pendant on dark velvet. Dramatic moonlit lighting, gothic jewelry editorial. Square crop.",
    },
    {
        "filename": "black-rose-product-2.jpg",
        "prompt": "Product photograph of a luxury sterling silver ring with gothic cathedral design on dark marble. Dramatic silver moonlight, editorial jewelry photography. Square crop.",
    },
    {
        "filename": "black-rose-product-3.jpg",
        "prompt": "Product photograph of a luxury black leather and silver chain bracelet with rose clasp on dark velvet. Gothic elegance, editorial jewelry photography. Square crop.",
    },
    {
        "filename": "black-rose-product-4.jpg",
        "prompt": "Product photograph of luxury sterling silver drop earrings with black rose design on dark fabric. Dramatic lighting, gothic jewelry editorial. Square crop.",
    },
    {
        "filename": "black-rose-product-5.jpg",
        "prompt": "Product photograph of a luxury sterling silver pendant necklace with vine design on dark marble. Silver moonlight, gothic jewelry editorial. Square crop.",
    },
    # ── Product Hotspot Thumbnails: Love Hurts ──
    {
        "filename": "love-hurts-product-1.jpg",
        "prompt": "Product photograph of a luxury rose gold necklace with crimson heart pendant on blush velvet. Warm candlelight glow, romantic jewelry editorial. Square crop.",
    },
    {
        "filename": "love-hurts-product-2.jpg",
        "prompt": "Product photograph of a luxury rose gold ring with bleeding rose design on pink marble. Warm romantic lighting, editorial jewelry photography. Square crop.",
    },
    {
        "filename": "love-hurts-product-3.jpg",
        "prompt": "Product photograph of a luxury rose gold bracelet with thorned vine design on crimson velvet. Candlelit romantic atmosphere, jewelry editorial. Square crop.",
    },
    {
        "filename": "love-hurts-product-4.jpg",
        "prompt": "Product photograph of luxury rose gold drop earrings with passion flower design on blush fabric. Warm golden light, romantic jewelry editorial. Square crop.",
    },
    {
        "filename": "love-hurts-product-5.jpg",
        "prompt": "Product photograph of a luxury rose gold pendant with flame design on crimson velvet. Warm candlelight, romantic jewelry editorial. Square crop.",
    },
    # ── Product Hotspot Thumbnails: Signature ──
    {
        "filename": "signature-product-1.jpg",
        "prompt": "Product photograph of a luxury gold and rose gold varsity jacket on marble pedestal. Warm golden studio lighting, premium fashion editorial. Square crop.",
    },
    {
        "filename": "signature-product-2.jpg",
        "prompt": "Product photograph of a luxury cream crewneck sweatshirt with rose gold SR monogram on champagne fabric. Warm studio lighting, fashion editorial. Square crop.",
    },
    {
        "filename": "signature-product-3.jpg",
        "prompt": "Product photograph of luxury black track pants with rose gold stripe on marble surface. Warm golden lighting, premium fashion editorial. Square crop.",
    },
    {
        "filename": "signature-product-4.jpg",
        "prompt": "Product photograph of a luxury rose gold belt bag with SR embossing on cream marble. Warm studio lighting, accessory editorial. Square crop.",
    },
    {
        "filename": "signature-product-5.jpg",
        "prompt": "Product photograph of luxury rose gold jewelry set on champagne velvet. Warm golden lighting, premium accessory editorial. Square crop.",
    },
    {
        "filename": "signature-product-6.jpg",
        "prompt": "Product photograph of a luxury cream hoodie with rose gold details on marble pedestal. Warm golden studio lighting, fashion editorial. Square crop.",
    },
    {
        "filename": "signature-product-7.jpg",
        "prompt": "Product photograph of luxury black joggers with rose gold accents on champagne fabric. Warm studio lighting, fashion editorial. Square crop.",
    },
    {
        "filename": "signature-product-8.jpg",
        "prompt": "Product photograph of a luxury rose gold watch on cream marble with gold accents. Warm studio lighting, accessory editorial. Square crop.",
    },
    {
        "filename": "signature-product-9.jpg",
        "prompt": "Product photograph of luxury rose gold chain necklace on champagne velvet. Warm golden lighting, jewelry editorial. Square crop.",
    },
    {
        "filename": "signature-product-10.jpg",
        "prompt": "Product photograph of luxury cream silk scarf with rose gold SR pattern on marble. Warm studio lighting, accessory editorial. Square crop.",
    },
    # ── Signature Beanies ──
    {
        "filename": "signature-beanie-1.jpg",
        "prompt": "Product photograph of a luxury black beanie with rose gold SR embroidered logo on cream marble. Warm golden studio lighting, fashion editorial. Square crop.",
    },
    {
        "filename": "signature-beanie-2.jpg",
        "prompt": "Product photograph of a luxury cream beanie with rose gold SR embroidered logo on dark marble. Warm golden studio lighting, fashion editorial. Square crop.",
    },
    {
        "filename": "signature-beanie-3.jpg",
        "prompt": "Product photograph of a luxury rose gold beanie with SR embroidered logo on champagne velvet. Warm golden studio lighting, fashion editorial. Square crop.",
    },
    {
        "filename": "signature-beanie-4.jpg",
        "prompt": "Product photograph of a luxury grey beanie with rose gold SR embroidered logo on marble. Warm golden studio lighting, fashion editorial. Square crop.",
    },
    # ── Placeholder ──
    {
        "filename": "placeholder.jpg",
        "prompt": "Minimalist luxury placeholder image. Soft cream background with subtle rose gold SR monogram watermark in center. Clean, elegant, professional. Square crop.",
    },
]


async def generate_image(prompt: str, api_key: str, timeout: float = 120.0) -> bytes | None:
    """Generate image via Gemini API."""
    url = f"{GEMINI_API_BASE}/models/{GEMINI_MODEL}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(3):
            try:
                resp = await client.post(url, json=payload)
                if resp.status_code == 429:
                    wait = int(resp.headers.get("Retry-After", "60"))
                    logger.warning(f"Rate limited, waiting {wait}s")
                    await asyncio.sleep(wait)
                    continue
                if resp.status_code != 200:
                    logger.error(f"API {resp.status_code}: {resp.text[:200]}")
                    if resp.status_code >= 500:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    return None

                data = resp.json()
                for cand in data.get("candidates", []):
                    for part in cand.get("content", {}).get("parts", []):
                        if "inlineData" in part:
                            return base64.b64decode(part["inlineData"]["data"])
                return None
            except httpx.TimeoutException:
                logger.warning(f"Timeout attempt {attempt + 1}/3")
                await asyncio.sleep(2 ** attempt)
    return None


def ssh_cmd(command: str) -> str:
    """Run command on WordPress.com via SSH."""
    cmd = f"sshpass -p '{WP_SSH_PASS}' ssh -o StrictHostKeyChecking=no {WP_SSH_USER}@{WP_SSH_HOST} \"{command}\""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return result.stdout.strip()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SkyyRose scene images")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--scenes-only", action="store_true", help="Only generate the 6 scene backgrounds")
    args = parser.parse_args()

    if not GEMINI_API_KEY and not args.dry_run:
        logger.error("GEMINI_API_KEY not set")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    scenes = SCENES
    if args.scenes_only:
        scenes = [s for s in SCENES if not s["filename"].startswith(("black-rose-product", "love-hurts-product", "signature-product", "signature-beanie", "placeholder"))]

    logger.info(f"Generating {len(scenes)} scene images")

    success = 0
    failed = 0

    for i, scene in enumerate(scenes):
        filename = scene["filename"]
        filepath = OUTPUT_DIR / filename

        if args.dry_run:
            logger.info(f"[DRY] {filename}: {scene['prompt'][:80]}...")
            continue

        if filepath.exists() and filepath.stat().st_size > 5000:
            logger.info(f"CACHED: {filename} ({filepath.stat().st_size:,} bytes)")
            success += 1
            continue

        logger.info(f"Generating {filename} ({i+1}/{len(scenes)})...")
        image_bytes = await generate_image(scene["prompt"], GEMINI_API_KEY)

        if image_bytes:
            # Gemini returns PNG, convert filename expectation
            filepath.write_bytes(image_bytes)
            logger.info(f"OK: {filename} ({len(image_bytes):,} bytes)")
            success += 1
        else:
            logger.error(f"FAIL: {filename}")
            failed += 1

        # Rate limit
        if i < len(scenes) - 1:
            await asyncio.sleep(1.5)

    if not args.dry_run:
        logger.info(f"\nDone: {success} success, {failed} failed")
        logger.info(f"Files at: {OUTPUT_DIR}")

        # Upload to server
        if WP_SSH_PASS:
            logger.info("Uploading scenes to WordPress...")
            remote_dir = "/srv/htdocs/wp-content/themes/skyyrose-flagship/assets/images/scenes"
            ssh_cmd(f"mkdir -p {remote_dir}")

            for scene in scenes:
                local = OUTPUT_DIR / scene["filename"]
                if local.exists():
                    scp = (
                        f"sshpass -p '{WP_SSH_PASS}' scp -o StrictHostKeyChecking=no "
                        f"{local} {WP_SSH_USER}@{WP_SSH_HOST}:{remote_dir}/{scene['filename']}"
                    )
                    result = subprocess.run(scp, shell=True, capture_output=True, timeout=60)
                    if result.returncode == 0:
                        logger.info(f"Uploaded: {scene['filename']}")
                    else:
                        logger.error(f"Upload failed: {scene['filename']}")

            logger.info("Upload complete")


if __name__ == "__main__":
    asyncio.run(main())
