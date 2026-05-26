#!/usr/bin/env python3
"""
Gemini Immersive Scene Generator — SkyyRose v1.

[DEPRECATED 2026-05-26] — Standalone path that bypasses the elite team.
Canonical entry point is now:

    python -m skyyrose.elite_studio home-spread --collection {br,sig,lh,all}

The elite-team path adds: PromptEnrichmentAgent canon enforcement, RunBudget
gates, Stage G visual QA, automatic retry-on-low-score, and SceneGeneratorAgent
that reads canonical scene.json configs from SCENES_DIR. This script remains
runnable for quick iteration but does NOT enforce any of those guardrails.

Migration map:
    python scripts/gemini_scene_gen.py --scene X
        → python -m skyyrose.elite_studio home-spread --scene X --collection Y

Generates immersive scene backgrounds where products are rendered INTO the
environment as a single unified cinematic image. Gemini 3 Pro Image
($0.08/image). Text-to-image generation (no reference images for scenes).

Usage:
    source .venv-imagery/bin/activate
    python scripts/gemini_scene_gen.py --list
    python scripts/gemini_scene_gen.py --scene black-rose-bay-bridge-sf-side-night
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
# Scene Definitions — 3 founder-directed canon-locked scenes (2026-05-26)
#
# Each scene anchors a SkyyRose DNA focal object — no catalog products in the
# Stage 1 generation. Real products composite via Stage 2 (composite_products.py
# or gemini_lookbook.py). Founder lock 2026-05-26:
#   BR  = Night from SF side of Bay Bridge facing Oakland
#   SIG = Daytime from Oakland to SF with Bay Bridge in back
#   LH  = Beauty & Beast, enchanted rose focal
# =============================================================================

SCENES = {
    # ── BLACK ROSE — Night, SF side of Bay Bridge looking toward Oakland ──
    "black-rose-bay-bridge-sf-side-night": {
        "collection": "black-rose",
        "filename": "black-rose-bay-bridge-sf-side-night-v2",
        "scene_description": (
            "Photorealistic cinematic night scene from the western (San "
            "Francisco) end of the San Francisco-Oakland Bay Bridge, looking "
            "eastward across the Bay toward Oakland. The Bay Bridge's iconic "
            "self-anchored suspension cables and steel girders extend into the "
            "foreground and middle distance, lit by amber sodium-vapor bridge "
            "lights along the deck. Bay water below shimmers with rippling "
            "reflections of bridge lights. Oakland skyline rises in the far "
            "distance — Port of Oakland's massive white container cranes "
            "silhouetted against the dark Oakland Hills, low-rise downtown "
            "Oakland buildings to the north, the warm lights of Jack London "
            "Square along the East Bay waterfront. A waxing moon casts cool "
            "silver light across the scene. Wet bridge deck and steel cables "
            "catch the moonlight. Atmospheric depth — distant Oakland softly "
            "fading into cool night haze. Single black rose with stem laid "
            "across the bridge railing at center-foreground, droplets of bay "
            "mist on its petals — armor and conviction made tangible. "
            "Photorealistic, FOG-cinematic restraint, no warm tones except "
            "distant city lights. Eye-level perspective from the bridge deck "
            "looking east with strong vanishing-point depth. No people, no "
            "traffic visible. Ultra-detailed: rivet patterns on steel, "
            "individual cable strands, water surface texture, distant "
            "container crane geometry. 3:4 portrait composition."
        ),
        "products_in_scene": [
            "Single deep black rose with stem and leaves resting across the "
            "bridge railing at center-foreground, single bead of bay mist on "
            "the topmost petal catching moonlight — the SkyyRose monogram "
            "object, no catalog product in this Stage-1 scene."
        ],
        "color_palette": "Deep black #0A0A0A base, silver #C0C0C0 moonlight on cables, amber sodium-vapor bridge deck lights, distant Oakland warm-amber city windows, Bay water dark navy with rippled silver reflections",
        "skyyrose_dna": "BR canon: armor not flower — a conviction. Concrete is the only soil that matters. Oakland Deep East. The Bay Bridge looked at from the SF side facing home. Beauty forces through cracks. Silver on near-black, no warm tones except the city you came from. FOG cinematic restraint.",
    },
    # ── SIGNATURE — Daytime, Oakland to SF, Bay Bridge in the back ────────
    "signature-oakland-waterfront-bay-bridge-day": {
        "collection": "signature",
        "filename": "signature-oakland-waterfront-bay-bridge-day-v2",
        "scene_description": (
            "Photorealistic cinematic daytime scene from the Oakland "
            "waterfront — Jack London Square / Embarcadero Cove area — "
            "looking southwest across the Bay toward San Francisco. The "
            "San Francisco-Oakland Bay Bridge spans the middle ground from "
            "left to right, its eastern span and self-anchored suspension "
            "section visible in full — the bridge is Oakland's, anchoring "
            "the East Bay to the western shore. San Francisco skyline rises "
            "in the far distance: Transamerica Pyramid, Salesforce Tower, "
            "Coit Tower, and the cluster of downtown SF financial district "
            "buildings as soft silhouettes. Golden hour late-morning light "
            "— warm amber on the water, soft blue-to-amber gradient sky "
            "overhead, light filtering through high cirrus clouds. Weathered "
            "wooden pier planks in the immediate foreground with brass "
            "mooring cleats, frayed weathered ropes, gentle Bay water lapping "
            "the pier pilings. Centered on the pier foreground: a small "
            "weathered wooden crate serving as an impromptu drafting "
            "surface, holding a partially-unfurled sheet of cream-colored "
            "drafting paper with the first SkyyRose rose script drawn in "
            "rich gold ink — edges curled, paper slightly weathered, a "
            "single fresh deep-red rose laid beside it. The 4 AM origin "
            "sketch brought into daylight. Photorealistic, Kith editorial "
            "restraint, magazine-grid framing. Slight low angle from the "
            "pier with strong depth toward the SF skyline. No people in "
            "frame. Ultra-detailed: wood grain on pier planks, ink texture "
            "on drafting paper, individual rose petals, water surface "
            "reflections, distant bridge cable detail, soft skyline "
            "atmospheric haze. 3:4 portrait composition."
        ),
        "products_in_scene": [
            "Cream-colored drafting paper at center-foreground on a weathered "
            "wooden crate, partially unfurled, showing the first SkyyRose "
            "rose script hand-drawn in gold ink — the origin sketch made "
            "permanent. Single fresh deep-red rose laid across the paper's "
            "edge. The SkyyRose monogram object, no catalog product in this "
            "Stage-1 scene."
        ],
        "color_palette": "Warm gold #D4AF37 morning light, cream drafting paper neutrals, weathered wood brown tones, Bay water blue-teal with gold reflections, soft amber-to-blue gradient sky, distant SF skyline grey-white silhouettes",
        "skyyrose_dna": "SIG canon: drew first rose at 4 AM, broke, a baby on the way. The Bay Bridge is Oakland's; the city on the other end is Frisco. The origin chapter. Foundation wardrobe, blueprints not basics. Kith editorial restraint. Gold accent on neutral palette. Gender-neutral by default.",
    },
    # ── LOVE HURTS — Beauty & Beast, enchanted rose focal ─────────────────
    "love-hurts-enchanted-rose-cathedral": {
        "collection": "love-hurts",
        "filename": "love-hurts-enchanted-rose-cathedral-v2",
        "scene_description": (
            "Photorealistic cinematic Beauty and the Beast inspired scene — "
            "Cocteau intensity, NOT Disney polish. Shadowed gothic cathedral "
            "interior at night, vast vaulted stone arches receding into "
            "darkness, ribbed stone columns disappearing into deep shadow on "
            "both sides. Center-foreground: ornate stone pedestal carved with "
            "intertwined thorns and roses, holding a tall hand-blown glass "
            "dome containing a single perfect deep-red enchanted rose — lit "
            "from within by an ethereal warm-amber glow, the rose is the only "
            "fully-lit object in the entire frame, the spotlight of the "
            "scene. Faint glow halo emanates from the dome into the "
            "surrounding shadow. A single shaft of deep crimson light pours "
            "through a high stained-glass rose window in the upper-right of "
            "the frame, dust motes drifting in the beam. Crimson velvet "
            "curtains line the stone columns, receding into deep shadow at "
            "the edges. Scattered deep-red rose petals on the polished dark "
            "stone floor around the pedestal base, some petals slightly "
            "wilted as if from the rose's slow magic. Wrought-iron candelabra "
            "in the mid-background hold lit candles casting small pools of "
            "amber warmth. The polished dark stone floor reflects the rose's "
            "ethereal glow as a soft crimson smear. Photorealistic, cinematic, "
            "fairy-tale gothic. Slight upward hero angle on the rose pedestal "
            "so the dome reads as monumental. Atmospheric: incense haze in "
            "the shafts of light. Ultra-detailed: glass refraction on dome, "
            "individual rose petals, thorn carving on pedestal, stone grain, "
            "stained glass color refraction, dust motes. 3:4 portrait "
            "composition. NO catalog products in this scene — products "
            "composite Stage 2."
        ),
        "products_in_scene": [
            "Single perfect deep-red enchanted rose under a tall hand-blown "
            "glass dome on ornate carved stone pedestal at center-foreground "
            "— the rose lit from within by ethereal warm-amber glow, the "
            "spotlight of the entire scene. The SkyyRose monogram object, "
            "no catalog product in this Stage-1 scene."
        ],
        "color_palette": "Deep crimson #DC143C accent on the rose and stained-glass shaft, burgundy curtains, near-black stone, ethereal warm-amber glow from inside the dome, candle-amber highlights in midground, dust-motes warm only in light beams",
        "skyyrose_dna": "LH canon: Hurts is the bloodline that raised me. Three generations of Hurts. The rose under glass — protected, fragile, kept. Beauty and the Beast cadence — Cocteau intensity, NOT Disney polish. The Beast didn't hide from ugliness, he hid because he loved something fragile.",
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
