#!/usr/bin/env python3
"""
Gemini single-shot lookbook generator.

Send scene background + all product techflats to Gemini in ONE call.
Gemini generates the complete lookbook scene with all products placed naturally.

Usage:
    source .venv-imagery/bin/activate
    python scripts/gemini_lookbook.py --collection love-hurts
    python scripts/gemini_lookbook.py --all
"""

import argparse
import io
import os
import sys
import time
from pathlib import Path

# Load env
PROJECT_ROOT = Path(__file__).resolve().parent.parent
for env_file in [PROJECT_ROOT / ".env.hf", PROJECT_ROOT / ".env"]:
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.strip() and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

from google import genai
from google.genai import types
from PIL import Image

THEME_DIR = PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship"
PRODUCTS_DIR = THEME_DIR / "assets" / "images" / "products"
SCENES_DIR = THEME_DIR / "assets" / "scenes"
OUTPUT_DIR = PROJECT_ROOT / "editorial-staging"

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# ---------------------------------------------------------------------------
# Collection definitions — techflats only, no model photos
# ---------------------------------------------------------------------------
COLLECTIONS = {
    "love-hurts": {
        "scene_file": "love-hurts/love-hurts-cathedral-rose-chamber-v2.png",
        "products": [
            {
                "sku": "lh-004",
                "ref": "lh-004-varsity-source.jpg",
                "desc": "White and black hooded varsity jacket with 'Love Hurts' script, rose-print hood lining",
                "placement": "displayed on carved wooden stand near stained glass window, left side",
            },
            {
                "sku": "lh-003",
                "ref": "lh-003-shorts-front-source.jpg",
                "desc": "White mesh shorts with red rose bouquet pattern, 'Love Hurts' script, black and red trim",
                "placement": "pinned flat on stone wall like art piece, right side of scene",
            },
            {
                "sku": "lh-001",
                "ref": "lh-001-fannie-pack-photo.jpg",
                "desc": "Black leather fanny pack with white 'FANNIE' text and small rose embroidery",
                "placement": "hanging prominently from ornate gothic candelabra arm near lit candles, strap draped over iron arm, clearly visible front-facing",
            },
            {
                "sku": "lh-002-white",
                "ref": "lh-002-joggers-variants.jpg",
                "desc": "WHITE joggers (the white pair on the right of the reference) with black side stripe. Must have the Love Hurts logo on the left thigh — the logo is a red heart wrapped in brown thorns with red roses blooming from the top and blood splatter (shown in the logo reference image)",
                "placement": "draped over gothic stone pew arm, right side near candles",
            },
            {
                "sku": "lh-002-black",
                "ref": "lh-002-joggers-variants.jpg",
                "desc": "BLACK joggers (the black pair on the left of the reference) with white side stripe. Must have the Love Hurts logo on the left thigh — the logo is a red heart wrapped in brown thorns with red roses blooming from the top and blood splatter (shown in the logo reference image)",
                "placement": "folded on stone bench, lower left near stained glass window",
            },
            {
                "sku": "lh-logo",
                "ref": "love-hurts-logo-reference.jpg",
                "desc": "THIS IS THE LOVE HURTS LOGO — red heart wrapped in brown thorns with red roses blooming from top, blood splatter on left side. This exact logo must appear on BOTH pairs of joggers on the left thigh area",
                "placement": "REFERENCE ONLY — do not place this as a separate item, use it as the logo on the joggers",
            },
        ],
    },
    "black-rose": {
        "scene_file": "black-rose/black-rose-rooftop-garden-v2.png",
        "products": [
            {
                "sku": "br-001",
                "ref": "br-001-techflat-v4.jpg",
                "desc": "Black crewneck with rose gold SkyyRose embroidery on chest",
                "placement": "folded on seat of black lounge chair, left side",
            },
            {
                "sku": "br-002",
                "ref": "br-002-joggers-source.jpg",
                "desc": "Black joggers with rose gold stripe and SkyyRose branding",
                "placement": "draped over arm of couch, center-left",
            },
            {
                "sku": "br-003",
                "ref": "br-003-jersey-front-techflat.jpg",
                "desc": "Black baseball jersey with 'Black Is Beautiful' text and alternating rose fill numbers",
                "placement": "displayed on iron railing, far right like a flag",
            },
            {
                "sku": "br-004",
                "ref": "br-004-hoodie-source.jpg",
                "desc": "Black hoodie with rose embroidery on sleeve",
                "placement": "hanging from matte black clothing rack, right side",
            },
            {
                "sku": "br-005",
                "ref": "br-005-hoodie-ltd-source.jpg",
                "desc": "Black hoodie and jogger matching set, limited edition",
                "placement": "folded and stacked on concrete bench near planter, far left",
            },
            {
                "sku": "br-007",
                "ref": "br-007-techflat.jpeg",
                "desc": "Black shorts with rose gold trim and SkyyRose logo",
                "placement": "laid flat on low coffee table, center of seating area",
            },
            {
                "sku": "br-008",
                "ref": "br-001-techflat-v4.jpg",
                "desc": "Black dress with rose gold accents",
                "placement": "hanging from display hook near pendant light, right-center",
            },
        ],
    },
    "signature": {
        "scene_file": "signature/signature-golden-gate-showroom-v2.png",
        "products": [
            {
                "sku": "sg-002",
                "ref": "sg-002-techflat-v4.jpg",
                "desc": "Mint green t-shirt with SkyyRose signature logo",
                "placement": "on acrylic mannequin bust near window, center",
            },
            {
                "sku": "sg-004",
                "ref": "sg-004-techflat.jpeg",
                "desc": "Mint hoodie with SkyyRose branding",
                "placement": "draped over marble display cube, center-right",
            },
            {
                "sku": "sg-005",
                "ref": "sg-005-techflat.jpeg",
                "desc": "Bay Rose matching set (hoodie + joggers) in mint and pink",
                "placement": "featured on center marble display table",
            },
            {
                "sku": "sg-006",
                "ref": "sg-006-techflat.jpeg",
                "desc": "Tie-dye crewneck sweatshirt with SkyyRose logo",
                "placement": "folded on marble shelf, right wall niche",
            },
            {
                "sku": "sg-007",
                "ref": "sg-007-techflat-v4.jpg",
                "desc": "Black beanie with SkyyRose embroidered rose logo",
                "placement": "on marble pedestal, left-center",
            },
            {
                "sku": "sg-009",
                "ref": "sg-009-sherpa.webp",
                "desc": "Sherpa jacket with SkyyRose branding",
                "placement": "draped over designer chair, far left",
            },
        ],
    },
}


def load_image_bytes(path: Path) -> bytes:
    """Load and optionally resize image to keep under Gemini limits."""
    img = Image.open(path)
    # Resize if too large (Gemini has input limits)
    max_dim = 1536
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    fmt = "JPEG"
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")
    img.save(buf, format=fmt, quality=90)
    return buf.getvalue()


def generate_lookbook(collection_name: str, config: dict) -> Path | None:
    """Generate a single lookbook scene using Gemini."""
    scene_path = SCENES_DIR / config["scene_file"]
    if not scene_path.exists():
        print(f"ERROR: Scene not found: {scene_path}")
        return None

    products = config["products"]
    # Filter to products with existing ref images
    available = []
    for p in products:
        ref_path = PRODUCTS_DIR / p["ref"]
        if ref_path.exists():
            available.append(p)
        else:
            print(f"  SKIP {p['sku']}: {p['ref']} not found")

    print(f"\n{'=' * 60}")
    print(f"COLLECTION: {collection_name.upper()} — {len(available)} products")
    print(f"Scene: {scene_path.name}")
    print(f"{'=' * 60}")

    # Build the prompt
    product_list = ""
    for i, p in enumerate(available, 1):
        product_list += f"\n{i}. {p['sku'].upper()}: {p['desc']}\n   PLACEMENT: {p['placement']}\n"

    prompt = f"""You are creating a luxury fashion lookbook scene for SkyyRose brand.

SCENE: The first image is the background scene — a beautifully lit editorial environment.

PRODUCTS: The following images (2 through {len(available) + 1}) are individual product photos (techflat/flat-lay style) of clothing items and accessories.

YOUR TASK: Generate a single photorealistic editorial image that places ALL of these products naturally throughout the scene.

CRITICAL RULES:
- ABSOLUTELY NO PEOPLE. No mannequins. No human figures. No body parts. Just the garments as objects.
- Each product should be DISPLAYED as an object: hung on walls, draped over furniture, folded on surfaces, hanging from fixtures.
- Products must look PHYSICALLY PRESENT in the scene with correct lighting, shadows, and perspective.
- Preserve EVERY detail of each garment: colors, logos, text, patterns, branding — exactly as shown in the reference photos.
- The scene should feel like a curated luxury showroom or editorial styling setup.

PRODUCT PLACEMENTS:
{product_list}

Make it look like a high-end fashion editorial spread — the kind you'd see in Vogue or GQ. Rich lighting, natural shadows, luxury atmosphere. The clothing is the star — displayed beautifully throughout the space."""

    # Build content parts: scene image first, then all product images
    client = genai.Client(api_key=GOOGLE_API_KEY)

    parts = []

    # Scene background
    print(f"  Loading scene: {scene_path.name}")
    scene_bytes = load_image_bytes(scene_path)
    parts.append(types.Part.from_bytes(data=scene_bytes, mime_type="image/jpeg"))

    # Product techflats
    for p in available:
        ref_path = PRODUCTS_DIR / p["ref"]
        print(f"  Loading {p['sku']}: {ref_path.name}")
        ref_bytes = load_image_bytes(ref_path)
        parts.append(types.Part.from_bytes(data=ref_bytes, mime_type="image/jpeg"))

    # Text prompt last
    parts.append(types.Part.from_text(text=prompt))

    print(f"\n  Sending to Gemini ({len(available)} products + scene)...")
    print("  This may take 30-60 seconds...")

    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=types.Content(parts=parts, role="user"),
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
            temperature=0.8,
        ),
    )

    # Extract generated image
    out_dir = OUTPUT_DIR / collection_name
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"{collection_name}-gemini-lookbook.webp"

    image_found = False
    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            img = Image.open(io.BytesIO(part.inline_data.data))
            img.save(output_path, format="WEBP", quality=95, method=6)
            size_kb = output_path.stat().st_size // 1024
            print(f"\n  SUCCESS: {output_path.name} ({img.width}x{img.height}, {size_kb}KB)")
            image_found = True
            break
        elif part.text:
            print(f"  Gemini text: {part.text[:200]}")

    if not image_found:
        print("\n  FAILED: No image in Gemini response")
        # Try with gemini-2.5-flash as fallback
        print("  Trying gemini-3-flash-preview...")
        response2 = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=types.Content(parts=parts, role="user"),
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
                temperature=0.8,
            ),
        )
        for part in response2.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                img = Image.open(io.BytesIO(part.inline_data.data))
                img.save(output_path, format="WEBP", quality=95, method=6)
                size_kb = output_path.stat().st_size // 1024
                print(
                    f"\n  SUCCESS (flash): {output_path.name} ({img.width}x{img.height}, {size_kb}KB)"
                )
                image_found = True
                break

    if not image_found:
        return None

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Gemini single-shot lookbook generator")
    parser.add_argument("--collection", type=str, help="Collection to generate")
    parser.add_argument("--all", action="store_true", help="Generate all collections")
    args = parser.parse_args()

    if not GOOGLE_API_KEY:
        print("ERROR: GOOGLE_API_KEY not set")
        sys.exit(1)

    if not args.collection and not args.all:
        parser.print_help()
        return

    collections = COLLECTIONS
    if args.collection:
        if args.collection not in COLLECTIONS:
            print(f"Unknown: {args.collection} (available: {', '.join(COLLECTIONS)})")
            sys.exit(1)
        collections = {args.collection: COLLECTIONS[args.collection]}

    results = []
    for name, config in collections.items():
        result = generate_lookbook(name, config)
        results.append((name, result))
        if result:
            # Small delay between collections
            time.sleep(3)

    print(f"\n{'=' * 60}")
    for name, path in results:
        status = f"→ {path}" if path else "→ FAILED"
        print(f"  {name}: {status}")


if __name__ == "__main__":
    main()
