#!/usr/bin/env python3
"""
Generate SR Monogram + Black Rose art for SkyyRose branding.

Uses Gemini image generation with the flat SR monogram as reference
to create dramatic brand art pieces.

Usage:
    source .venv-imagery/bin/activate
    python scripts/gen-sr-monogram-art.py
"""

import logging
import os
import sys
import tempfile
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("sr-monogram-art")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRANDING_DIR = PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "branding"
MONOGRAM_REF = BRANDING_DIR / "sr-monogram-flat.jpg"

# Load env
for env_file in [PROJECT_ROOT / ".env", PROJECT_ROOT / ".env.hf"]:
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))

MODEL_ID = "gemini-2.5-flash-image"

PROMPTS = [
    # 1. PRIMARY — The flagship SkyyRose brand mark (NO TEXT — monogram only)
    {
        "name": "sr-primary-hero",
        "prompt": (
            "Create a stunning luxury fashion brand hero image. "
            "The EXACT SR monogram logo from the reference image "
            "(intertwined calligraphic S and R in rose gold with a rose growing from the R's tail) "
            "is rendered LARGE and centered as a polished rose gold (#B76E79) 3D metallic emblem. "
            "Background: deep black (#0A0A0A) with subtle concrete texture visible. "
            "A single spotlight from above casts dramatic volumetric light rays through haze. "
            "Microscopic gold (#D4AF37) dust particles floating in the light beam. "
            "ABSOLUTELY NO TEXT, NO WORDS, NO LETTERS besides the SR monogram itself. "
            "Ultra-premium, Gucci/Versace level brand identity. Square."
        ),
        "aspect": "1:1",
    },
    # 2. BLACK ROSE COLLECTION — Gothic, dark, powerful
    {
        "name": "sr-collection-black-rose",
        "prompt": (
            "Create dark gothic luxury brand artwork for the 'Black Rose' collection. "
            "A photorealistic black rose with velvety petals, slightly wet with dew, "
            "emerging from cracked concrete — growing through the cracks. "
            "The EXACT SR monogram from the reference image (intertwined S and R with rose stem) "
            "is embossed in dark gunmetal/black chrome on the concrete below the rose. "
            "Atmosphere: dark cathedral lighting, deep shadows, single shaft of moonlight. "
            "Color palette: black, charcoal, dark silver, with ONE subtle gold accent on a petal edge. "
            "Gothic luxury. Raw power meets elegance. The rose represents beauty surviving concrete. "
            "No additional text. Square composition."
        ),
        "aspect": "1:1",
    },
    # 3. LOVE HURTS COLLECTION — Passionate, red, emotional
    {
        "name": "sr-collection-love-hurts",
        "prompt": (
            "Create passionate luxury brand artwork for the 'Love Hurts' collection. "
            "A realistic cracked red heart wrapped in thorny rose vines, bleeding rose gold (#B76E79) "
            "liquid that pools and forms the EXACT SR monogram from the reference image "
            "(intertwined S and R with rose growing from the tail). "
            "Deep red roses with thorns surround the scene. "
            "Background: rich dark burgundy-to-black gradient, like velvet curtains. "
            "Color palette: deep crimson red, blood red, rose gold accents, black thorns. "
            "Dramatic Renaissance painting lighting — Caravaggio-style chiaroscuro. "
            "Emotional, passionate, pain-meets-beauty aesthetic. "
            "No additional text. Square composition."
        ),
        "aspect": "1:1",
    },
    # 4. SIGNATURE COLLECTION — Bay Area pride, clean, rose gold
    {
        "name": "sr-collection-signature",
        "prompt": (
            "Create clean luxury brand artwork for the 'Signature' collection. "
            "The EXACT SR monogram from the reference image (intertwined S and R with rose stem) "
            "rendered as a large brushed rose gold (#B76E79) metallic emblem, "
            "as if it were a luxury car badge — pristine, reflective, premium. "
            "Behind it: a stylized Bay Area cityscape silhouette (Golden Gate Bridge, Oakland skyline) "
            "in subtle dark gray outlines against a soft dawn sky gradient "
            "(charcoal at top fading to warm rose gold horizon at bottom). "
            "Scattered rose petals in pastel pink, lavender, and mint float gently. "
            "Clean, modern, aspirational. The freshest collection — streetwear meets luxury. "
            "No additional text. Square composition."
        ),
        "aspect": "1:1",
    },
]


def get_client():
    from google import genai

    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        log.error("No GOOGLE_API_KEY or GEMINI_API_KEY found")
        sys.exit(1)
    return genai.Client(api_key=key)


def load_reference():
    from google.genai import types

    if not MONOGRAM_REF.exists():
        log.error("Reference monogram not found: %s", MONOGRAM_REF)
        sys.exit(1)
    img_bytes = MONOGRAM_REF.read_bytes()
    return types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")


def generate(client, ref_img, prompt_cfg):
    from google.genai import types

    name = prompt_cfg["name"]
    prompt = prompt_cfg["prompt"]
    aspect = prompt_cfg["aspect"]

    log.info("Generating: %s (%s)", name, aspect)

    for attempt in range(1, 4):
        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=[
                    "REFERENCE: This is the exact SR monogram logo. Reproduce this EXACT design in the artwork:",
                    ref_img,
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(
                        aspect_ratio=aspect,
                    ),
                ),
            )
        except Exception as exc:
            log.error("  Attempt %d failed: %s", attempt, exc)
            time.sleep(5)
            continue

        if not response or not response.parts:
            log.warning("  Empty response (attempt %d)", attempt)
            time.sleep(3)
            continue

        for part in response.parts:
            if part.inline_data:
                with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as tmp:
                    tmp_path = tmp.name
                part.as_image().save(tmp_path)
                data = Path(tmp_path).read_bytes()
                Path(tmp_path).unlink(missing_ok=True)

                out_path = BRANDING_DIR / f"{name}.webp"
                out_path.write_bytes(data)
                log.info("  Saved: %s (%d KB)", out_path.name, len(data) // 1024)
                return True

        log.warning("  No image in response (attempt %d)", attempt)
        time.sleep(3)

    log.error("  FAILED after 3 attempts: %s", name)
    return False


def main():
    client = get_client()
    ref_img = load_reference()

    results = []
    for cfg in PROMPTS:
        ok = generate(client, ref_img, cfg)
        results.append((cfg["name"], ok))
        time.sleep(8)  # Rate limit

    log.info("=== Results ===")
    for name, ok in results:
        log.info("  %s: %s", name, "OK" if ok else "FAILED")


if __name__ == "__main__":
    main()
