#!/usr/bin/env python3
"""
Gemini Immersive Scene Generator — SkyyRose v1

Generates drakerelated.com-style immersive scene backgrounds where products
are rendered INTO the environment as a single unified cinematic image.

Uses Gemini 3 Pro Image for 4K cinematic quality ($0.08/image).
Text-to-image generation (no reference images needed for scenes).

Usage:
    source .venv-imagery/bin/activate
    python scripts/gemini_scene_gen.py --list
    python scripts/gemini_scene_gen.py --scene black-rose-moonlit-courtyard
    python scripts/gemini_scene_gen.py --collection black-rose
    python scripts/gemini_scene_gen.py --all
    python scripts/gemini_scene_gen.py --all --variants 3
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("gemini-scene-gen")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
THEME_ROOT = PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship"
SCENES_DIR = THEME_ROOT / "assets" / "scenes"

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

MODEL_ID = "gemini-3-pro-image-preview"
MAX_RETRIES = 3
RETRY_DELAY_SEC = 8
MIN_FILE_SIZE_KB = 100  # Scenes should be larger than product shots

# =============================================================================
# Scene Definitions — 6 rooms across 3 collections
# =============================================================================

SCENES = {
    # ── BLACK ROSE: "The Garden" ──────────────────────────────────────────
    "black-rose-rooftop-garden": {
        "collection": "black-rose",
        "filename": "black-rose-rooftop-garden-v2",
        "scene_description": (
            "Luxury rooftop garden at night under a clear sky full of stars. "
            "The San Francisco Bay Bridge is lit up in the background, its "
            "lights reflecting on the dark water below. The rooftop has modern "
            "dark planters overflowing with black roses and deep green foliage. "
            "Sleek black lounge furniture — a low-profile couch and accent "
            "chairs. A matte black clothing rack stands near the edge. Silver "
            "hanging pendant lights cast pools of cool light. Polished dark "
            "concrete floor with subtle wet reflections."
        ),
        "products_in_scene": [
            "A BLACK sherpa jacket (black satin with sherpa lining, embroidered "
            "rose on chest) draped over the arm of a sleek black lounge chair "
            "on the left side",
            "A premium BLACK hoodie with rose embroidery folded neatly on the "
            "seat of the low-profile couch at center-left, rose detail visible",
            "BLACK joggers with small embroidered roses folded on a side table "
            "next to a planter of black roses at center-right",
            "Another BLACK hoodie with rose embroidery hanging from the matte "
            "black clothing rack on the right side, Bay Bridge visible behind it",
        ],
        "color_palette": "Clear night sky, Bay Bridge blue-white lights, silver (#C0C0C0) pendant lights, near-black (#0A0A0A) furniture, dark green foliage",
    },
    "black-rose-rooftop-lounge": {
        "collection": "black-rose",
        "filename": "black-rose-rooftop-lounge-v2",
        "scene_description": (
            "Different angle of the same luxury rooftop — closer, more intimate. "
            "A dark marble bar counter with silver stools in the foreground. "
            "Black rose arrangements in silver vases line the bar top. The Bay "
            "Bridge glows in the distance through a clear night sky. Modern "
            "black display pedestals with silver bases are arranged near the "
            "rooftop edge. String lights overhead create a warm canopy effect "
            "against the night sky."
        ),
        "products_in_scene": [
            "A BLACK hoodie with rose embroidery displayed on a dark mannequin "
            "bust on the center display pedestal",
            "A BLACK crewneck with rose embroidery laid flat on the dark marble "
            "bar counter at right-center, next to a silver vase of black roses",
            "A gothic BLACK hooded dress with rose embroidery draped elegantly "
            "over a silver bar stool on the right",
            "A BLACK luxury athletic jersey hanging from a minimal wall hook "
            "on a dark partition at center-left",
        ],
        "color_palette": "Bay Bridge blue-white glow, warm string lights, silver (#C0C0C0) accents, near-black (#0A0A0A) marble, clear starry sky",
    },
    # ── LOVE HURTS: "The Ballroom" ────────────────────────────────────────
    "love-hurts-cathedral-rose-chamber": {
        "collection": "love-hurts",
        "filename": "love-hurts-cathedral-rose-chamber-v2",
        "scene_description": (
            "Gothic cathedral interior with vaulted ceilings. A glowing "
            "enchanted rose floats under a glass dome at center (Beauty and "
            "the Beast style). Stained glass windows cast red and pink light. "
            "Ornate candelabras with lit candles. Crimson rose petals scattered "
            "on the stone floor. Purple and crimson fabric draped from arches."
        ),
        "products_in_scene": [
            "A BLACK satin varsity jacket with fire-red script lettering and "
            "rose garden embroidery draped beside the enchanted rose glass "
            "dome at center-left",
            "A luxury BLACK fanny pack with rose detail hung from a gothic "
            "candelabra stand on the right",
            "BLACK mesh basketball shorts with rose design displayed on a "
            "stone ledge in a stained glass alcove at center",
        ],
        "color_palette": "Crimson (#DC143C), pink rose petals, purple fabrics, warm candlelight",
    },
    "love-hurts-gothic-ballroom": {
        "collection": "love-hurts",
        "filename": "love-hurts-gothic-ballroom-v2",
        "scene_description": (
            "Vast gothic ballroom with soaring arched ceiling. Purple velvet "
            "drapes frame tall windows. A glowing enchanted rose under glass "
            "dome sits on a marble pedestal. Pink rose petals cover the stone "
            "floor. Candlelit crystal chandeliers cast warm flickering light. "
            "Dark romantic atmosphere with deep shadows."
        ),
        "products_in_scene": [
            "BLACK joggers with embroidered rose detail folded neatly on a "
            "purple velvet chair at center-left",
            "A blush PINK windbreaker with rose detailing displayed beside "
            "the glass dome on a marble stand on the right",
        ],
        "color_palette": "Purple velvet, crimson (#DC143C), pink petals, warm candlelight amber",
    },
    # ── SIGNATURE: "The Runway" ───────────────────────────────────────────
    "signature-waterfront-runway": {
        "collection": "signature",
        "filename": "signature-waterfront-runway-v2",
        "scene_description": (
            "San Francisco Bay Bridge at night in the background. A floating "
            "black marble platform extends over dark water. Gold LED trim "
            "lighting edges the platform. Glass orb display case on the left. "
            "Three gold-lit LED display frames at center. Stepped marble "
            "pedestals on the right. Reflective black marble floor mirrors "
            "the city lights. Gold accent lighting throughout."
        ),
        "products_in_scene": [
            "A luxury BLACK duffle bag displayed inside a glass orb case on the far left",
            "A gold-colorway streetwear set hanging in a gold-lit LED display frame at center-left",
            "Bay Area inspired athletic shorts hanging in a gold-lit LED display frame at center",
            "A pastel mint-and-lavender colorblock hoodie hanging in a "
            "gold-lit LED display frame at center-right",
            "A blue-rose Bay Area streetwear ensemble featured on the top "
            "stepped marble pedestal on the right",
            "A forest green beanie on the lower marble pedestal step at far right",
        ],
        "color_palette": "Gold (#D4AF37) accents, warm amber LEDs, near-black marble, Bay Bridge blue lights",
    },
    "signature-golden-gate-showroom": {
        "collection": "signature",
        "filename": "signature-golden-gate-showroom-v2",
        "scene_description": (
            "Luxury showroom interior with floor-to-ceiling panoramic windows "
            "showing the Golden Gate Bridge at sunset. Black marble floor and "
            "walls. Gold LED strip lighting runs along ceiling edges and "
            "display areas. Minimalist clothing racks on left and right walls. "
            "A marble display table at center. Marble pedestals flanking the "
            "table. Reflective black marble floor captures the sunset glow."
        ),
        "products_in_scene": [
            "An orchid-purple colorway tee hanging on a wall-mounted clothing rack on the left",
            "A gold colorway tee featured on the center marble display table",
            "A black beanie on a marble pedestal at left-center",
            "A white tee hanging on a wall-mounted clothing rack on the right",
        ],
        "color_palette": "Gold (#D4AF37) sunset light, warm amber, black marble, San Francisco sky",
    },
}


# =============================================================================
# Prompt Builder
# =============================================================================

STYLE_SUFFIX = (
    "3D rendered environment with strong volumetric lighting, atmospheric fog, "
    "and parallax depth — foreground objects slightly blurred, midground sharp, "
    "background softly fading. Hyper-realistic materials: visible marble grain, "
    "fabric texture on clothing, reflective surfaces catching light sources. "
    "Dramatic rim lighting separates layers and creates a sense of walkable space. "
    "Dark luxury aesthetic, ultra-wide 16:9 cinematic composition, 4K resolution. "
    "The clothing items must look PHYSICALLY PRESENT in the scene — proper "
    "lighting, cast shadows, ambient occlusion, and color grading matching "
    "the environment. NOT flat, NOT photoshopped overlays. The viewer should "
    "feel like they could step INTO this room."
)


def build_prompt(scene: dict, variant: int = 0) -> str:
    """Build the full generation prompt for a scene."""
    products_text = "\n".join(f"- {p}" for p in scene["products_in_scene"])

    base = (
        f"Generate a single photorealistic cinematic scene:\n\n"
        f"ENVIRONMENT: {scene['scene_description']}\n\n"
        f"COLOR PALETTE: {scene['color_palette']}\n\n"
        f"CLOTHING ITEMS physically placed IN the scene:\n{products_text}\n\n"
        f"{STYLE_SUFFIX}"
    )

    if variant == 1:
        base += (
            "\n\nSHOT VARIATION: Slightly different camera angle — lower perspective, "
            "more dramatic foreground, enhanced atmospheric haze."
        )
    elif variant == 2:
        base += (
            "\n\nSHOT VARIATION: Warmer color grade, slightly more saturated, "
            "stronger rim lighting on clothing items to make them pop."
        )

    return base


# =============================================================================
# Image Generation
# =============================================================================


def get_client():
    """Initialize Gemini client."""
    from google import genai

    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        log.error("No GOOGLE_API_KEY found. Set in .env or .env.hf")
        sys.exit(1)
    return genai.Client(api_key=key)


def generate_scene(client, prompt: str, attempt: int = 1) -> bytes | None:
    """Generate a single scene image using Gemini text-to-image."""
    from google.genai import types

    suffix = ""
    if attempt > 1:
        suffix = (
            " CRITICAL: Generate a COMPLETE scene with ALL clothing items "
            "physically present. Each item must be clearly visible and "
            "naturally integrated into the environment with proper lighting."
        )

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[prompt + suffix],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="16:9",
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

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name
            part.as_image().save(tmp_path)
            data = Path(tmp_path).read_bytes()
            Path(tmp_path).unlink(missing_ok=True)
            return data

    log.warning("No image in response (attempt %d)", attempt)
    return None


def convert_to_webp(png_path: Path, webp_path: Path, quality: int = 85) -> bool:
    """Convert PNG to WebP using cwebp or Pillow fallback."""
    try:
        result = subprocess.run(
            ["cwebp", "-q", str(quality), str(png_path), "-o", str(webp_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Pillow fallback
    try:
        from PIL import Image

        img = Image.open(png_path)
        img.save(webp_path, "WEBP", quality=quality)
        return True
    except Exception as exc:
        log.error("WebP conversion failed: %s", exc)
        return False


def process_scene(client, scene_key: str, scene: dict, num_variants: int):
    """Generate all variants for a single scene."""
    collection_dir = SCENES_DIR / scene["collection"]
    collection_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    for variant in range(num_variants):
        variant_suffix = "" if variant == 0 else f"-alt{variant}"
        base_name = f"{scene['filename']}{variant_suffix}"
        png_path = collection_dir / f"{base_name}.png"
        webp_path = collection_dir / f"{base_name}.webp"

        prompt = build_prompt(scene, variant)
        label = f"{scene_key}{variant_suffix}"
        log.info("  [SCENE] %s ...", label)

        for attempt in range(1, MAX_RETRIES + 1):
            img_bytes = generate_scene(client, prompt, attempt)
            if img_bytes and len(img_bytes) / 1024 >= MIN_FILE_SIZE_KB:
                png_path.write_bytes(img_bytes)
                size_kb = len(img_bytes) / 1024
                log.info("  SAVED %s (%.0f KB)", png_path.name, size_kb)

                # Convert to WebP
                if convert_to_webp(png_path, webp_path):
                    webp_kb = webp_path.stat().st_size / 1024
                    log.info("  WEBP  %s (%.0f KB)", webp_path.name, webp_kb)

                results[label] = {
                    "status": "success",
                    "png_kb": round(size_kb),
                    "webp_kb": round(webp_kb) if webp_path.exists() else None,
                }
                break

            if attempt < MAX_RETRIES:
                log.info("  Retry %d/%d ...", attempt + 1, MAX_RETRIES)
                time.sleep(RETRY_DELAY_SEC)
        else:
            results[label] = {"status": "failed"}
            log.warning("  FAILED %s after %d attempts", label, MAX_RETRIES)

        time.sleep(3)  # Rate limit between variants

    return results


# =============================================================================
# CLI
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Generate immersive scene backgrounds for SkyyRose experience pages"
    )
    parser.add_argument("--scene", help="Specific scene key to generate")
    parser.add_argument(
        "--collection",
        choices=["black-rose", "love-hurts", "signature"],
        help="Generate all scenes for a collection",
    )
    parser.add_argument("--all", action="store_true", help="Generate all 6 scenes")
    parser.add_argument("--list", action="store_true", help="List available scenes")
    parser.add_argument(
        "--variants",
        type=int,
        default=1,
        help="Number of variants per scene (1-3, default: 1)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show prompts without calling API",
    )
    args = parser.parse_args()

    if args.list:
        print("\nAvailable scenes:")
        for key, scene in SCENES.items():
            output = SCENES_DIR / scene["collection"] / f"{scene['filename']}.webp"
            exists = "EXISTS" if output.exists() else "MISSING"
            n_products = len(scene["products_in_scene"])
            print(f"  {key}")
            print(f"    Collection: {scene['collection']} | Products: {n_products} | [{exists}]")
            print(f"    Output: {output.relative_to(PROJECT_ROOT)}")
        return 0

    # Determine which scenes to generate
    if args.scene:
        if args.scene not in SCENES:
            log.error("Unknown scene: %s", args.scene)
            log.error("Available: %s", ", ".join(sorted(SCENES)))
            return 1
        scene_keys = [args.scene]
    elif args.collection:
        scene_keys = [k for k, s in SCENES.items() if s["collection"] == args.collection]
    elif args.all:
        scene_keys = list(SCENES.keys())
    else:
        parser.print_help()
        return 0

    num_variants = min(max(args.variants, 1), 3)
    total_images = len(scene_keys) * num_variants

    print("=" * 70)
    print("  SKYYROSE IMMERSIVE SCENE GENERATOR")
    print(f"  Model: {MODEL_ID}")
    print(f"  Scenes: {len(scene_keys)} | Variants: {num_variants} | Total: ~{total_images} images")
    print(f"  Est. cost: ~${total_images * 0.08:.2f}")
    print(f"  Output: {SCENES_DIR.relative_to(PROJECT_ROOT)}")
    print("=" * 70)

    if args.dry_run:
        for key in scene_keys:
            scene = SCENES[key]
            print(f"\n--- {key} ---")
            print(f"File: {scene['filename']}.webp")
            prompt = build_prompt(scene)
            print(f"Prompt ({len(prompt)} chars):\n{prompt}\n")
        print(f"\nDry run complete. {total_images} images would be generated.")
        return 0

    client = get_client()
    all_results = {}

    for i, key in enumerate(scene_keys, 1):
        scene = SCENES[key]
        print(f"\n[{i}/{len(scene_keys)}] {key} — {scene['collection']}")
        results = process_scene(client, key, scene, num_variants)
        all_results[key] = results

    # Save results
    results_path = SCENES_DIR / "scene_generation_results.json"
    with open(results_path, "w") as f:
        json.dump(all_results, f, indent=2)

    # Summary
    total_success = sum(
        1
        for scene_results in all_results.values()
        for r in scene_results.values()
        if isinstance(r, dict) and r.get("status") == "success"
    )
    total_attempted = sum(len(r) for r in all_results.values())

    print("\n" + "=" * 70)
    print(f"  COMPLETE: {total_success}/{total_attempted} scenes generated")
    print(f"  Output: {SCENES_DIR}")
    print(f"  Results: {results_path}")
    print("=" * 70)

    if total_success > 0:
        print("\n  Next steps:")
        print("  1. Review generated images in assets/scenes/")
        print("  2. Verify hotspot positions in template-immersive-*.php")
        print("  3. Test in browser at multiple viewport sizes")
        print(f"\n  open {SCENES_DIR}")

    return 0 if total_success == total_attempted else 1


if __name__ == "__main__":
    sys.exit(main())
