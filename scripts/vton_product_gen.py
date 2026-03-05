#!/usr/bin/env python3
"""
SkyyRose VTON Pipeline — 100% Accurate Product Model Shots

Uses IDM-VTON (1.3M+ runs on Replicate) to place ACTUAL garment images
onto model photos. Unlike LoRA/Gemini which try to recreate products,
VTON warps the real garment pixels — so accuracy is guaranteed.

Pipeline:
  1. Take tech flat garment images (already cropped or auto-crop)
  2. Pair with stock model photos (neutral poses)
  3. Run IDM-VTON to composite garment onto model
  4. Output: photorealistic model shots with 100% accurate garments

Usage:
    source .venv-lora/bin/activate
    python scripts/vton_product_gen.py --dry-run
    python scripts/vton_product_gen.py --sku br-d02
    python scripts/vton_product_gen.py --all
    python scripts/vton_product_gen.py --sku lh-002 --category dresses

Model photos go in: datasets/vton_models/
Output goes to:     datasets/skyyrose_vton_output/
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import httpx

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

API_BASE = "https://api.replicate.com/v1"
VTON_MODEL = "cuuupid/idm-vton"
VTON_VERSION = "0513734a452173b8173e907e3a59d19a36266e55"

# Directories
TECHFLAT_DIR = PROJECT_ROOT / "datasets" / "skyyrose_lora_v4" / "images"
MODEL_PHOTOS_DIR = PROJECT_ROOT / "datasets" / "vton_models"
OUTPUT_DIR = PROJECT_ROOT / "datasets" / "skyyrose_vton_output"

# ── Product catalog ─────────────────────────────────────────────────────────
# Each product maps to its tech flat image and IDM-VTON category.
# For sets (top + bottom), we need separate garment images.
# category: upper_body, lower_body, dresses

PRODUCTS = {
    "br-001-top": {
        "name": "Black Rose Crewneck (Top)",
        "techflat": "br-001-techflat.jpg",
        "category": "upper_body",
        "garment_des": "Black crewneck sweatshirt with large white and gray rose graphic, white trim at neck hem and cuffs",
        "crop_region": "top",  # Auto-crop: take upper portion of set image
    },
    "br-003-giants": {
        "name": "Black Is Beautiful Baseball Jersey (Giants)",
        "techflat": "br-003-giants-techflat.jpg",
        "category": "upper_body",
        "garment_des": "Black short-sleeve baseball jersey with BLACK IS BEAUTIFUL orange text, orange trim, button front",
        "crop_region": "left",  # Front view is on left side
    },
    "br-d02": {
        "name": "Black Is Beautiful Football Jersey (Red #80)",
        "techflat": "br-d02-techflat.jpg",
        "category": "upper_body",
        "garment_des": "Red football jersey number 80 with rose fill pattern in numbers, V-neck, white striped sleeves",
        "crop_region": "left",
    },
    "br-d03": {
        "name": "Black Is Beautiful Football Jersey (White #32)",
        "techflat": "br-d03-techflat.jpg",
        "category": "upper_body",
        "garment_des": "White football jersey number 32 with dark rose fill in numbers, black V-neck, black striped sleeves",
        "crop_region": "left",
    },
    "br-d04": {
        "name": "The Bay Basketball Jersey",
        "techflat": "br-d04-techflat.jpg",
        "category": "upper_body",
        "garment_des": "White sleeveless basketball jersey with THE BAY gold text and grayscale rose gradient on bottom half",
        "crop_region": "left",
    },
    "lh-002": {
        "name": "Love Hurts Varsity Jacket",
        "techflat": "lh-002-techflat.jpg",
        "category": "upper_body",
        "garment_des": "White hooded varsity jacket with black sleeves, Love Hurts red script, snap buttons, red and black striped trim",
        "crop_region": "left",
    },
    "lh-003-black": {
        "name": "Love Hurts Track Pants (Black)",
        "techflat": "lh-003-techflat.jpg",
        "category": "lower_body",
        "garment_des": "Black track pants with white side stripe, red rose embroidery on thigh, tapered ankle cuffs",
        "crop_region": "right",  # Black version is on right side of tech flat
    },
    "lh-004": {
        "name": "Love Hurts Rose Shorts",
        "techflat": "lh-004-techflat.jpg",
        "category": "lower_body",
        "garment_des": "White athletic shorts with all-over red rose bouquet pattern, Love Hurts script, black mesh side panels",
        "crop_region": "full",
    },
    "sg-002-top": {
        "name": "Signature Purple Rose Tee",
        "techflat": "sg-002-techflat.jpg",
        "category": "upper_body",
        "garment_des": "White crewneck t-shirt with purple rose graphic on chest, roses growing from cloud base",
        "crop_region": "top-left",
    },
    "sg-d01-top": {
        "name": "Pastel V-Chevron Windbreaker (Jacket)",
        "techflat": "sg-d01-techflat.jpg",
        "category": "upper_body",
        "garment_des": "White zip-up hooded windbreaker with pastel pink green yellow purple V-chevron color blocks, pink hood",
        "crop_region": "top-left",
    },
    "sg-d03-top": {
        "name": "Mint Green Crewneck (Top)",
        "techflat": "sg-d03-techflat.jpg",
        "category": "upper_body",
        "garment_des": "Mint green crewneck sweatshirt with purple and pink rose graphic on chest",
        "crop_region": "top-left",
    },
    "sg-d04": {
        "name": "Mint Green Hooded Dress",
        "techflat": "sg-d04-techflat.jpg",
        "category": "dresses",
        "garment_des": "Mint green knee-length hooded sweatshirt dress with purple rose graphic and purple drawstrings",
        "crop_region": "full",
    },
}

# ── Stock model photos ──────────────────────────────────────────────────────
# These are neutral-pose model photos for VTON compositing.
# Users should add 3:4 ratio photos of models in simple clothing.
# The VTON will replace their clothing with the SkyyRose garment.

DEFAULT_MODEL_PHOTOS = {
    "upper_body": [
        "model-male-1.jpg",
        "model-female-1.jpg",
    ],
    "lower_body": [
        "model-male-1.jpg",
        "model-female-1.jpg",
    ],
    "dresses": [
        "model-female-1.jpg",
    ],
}


# ── Image processing ────────────────────────────────────────────────────────

def crop_garment(image_path: Path, crop_region: str) -> Path:
    """Crop a specific garment from a multi-view tech flat.

    Tech flats often show front+back side by side, or top+bottom stacked.
    This extracts the individual garment for VTON input.

    Returns path to cropped image (saved to temp location).
    """
    from PIL import Image

    img = Image.open(image_path).convert("RGB")
    w, h = img.size

    crops = {
        "full": (0, 0, w, h),
        "left": (0, 0, w // 2, h),           # Front view (left half)
        "right": (w // 2, 0, w, h),           # Back view or second colorway
        "top": (0, 0, w, h // 2),             # Top garment in a set
        "bottom": (0, h // 2, w, h),          # Bottom garment in a set
        "top-left": (0, 0, w // 2, h // 2),   # Top-left quadrant (front of top)
        "top-right": (w // 2, 0, w, h // 2),  # Top-right quadrant
    }

    if crop_region not in crops:
        crop_region = "full"

    box = crops[crop_region]
    cropped = img.crop(box)

    # Save cropped version
    crop_dir = OUTPUT_DIR / "_cropped_garments"
    crop_dir.mkdir(parents=True, exist_ok=True)
    crop_path = crop_dir / f"{image_path.stem}-{crop_region}.jpg"
    cropped.save(crop_path, "JPEG", quality=95)
    return crop_path


def upload_image_to_replicate(api_token: str, image_path: Path) -> str:
    """Upload an image to Replicate's file hosting and return the URL."""
    headers = {"Authorization": f"Bearer {api_token}"}

    # Create upload
    resp = httpx.post(
        f"{API_BASE}/files",
        headers={**headers, "Content-Type": "application/octet-stream"},
        content=image_path.read_bytes(),
        timeout=60.0,
    )

    if resp.status_code in (200, 201):
        data = resp.json()
        return data.get("urls", {}).get("get", "")

    # Fallback: use data URI for smaller images
    import base64
    b64 = base64.b64encode(image_path.read_bytes()).decode()
    ext = image_path.suffix.lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
    return f"data:{mime};base64,{b64}"


def create_vton_prediction(
    api_token: str,
    garment_url: str,
    model_url: str,
    garment_desc: str,
    category: str = "upper_body",
) -> dict:
    """Submit an IDM-VTON prediction to Replicate."""
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "version": VTON_VERSION,
        "input": {
            "garm_img": garment_url,
            "human_img": model_url,
            "garment_des": garment_desc,
            "category": category,
            "crop": True,  # Auto-crop if not 3:4
            "steps": 30,
            "seed": 42,
        },
    }

    # Use dresses version for dress category
    if category == "dresses":
        payload["input"]["force_dc"] = True

    response = httpx.post(
        f"{API_BASE}/predictions",
        headers=headers,
        json=payload,
        timeout=60.0,
    )

    if response.status_code not in (200, 201):
        return {"error": f"HTTP {response.status_code}: {response.text[:200]}"}

    return response.json()


def poll_prediction(api_token: str, prediction_id: str) -> dict:
    """Poll until prediction completes."""
    headers = {"Authorization": f"Bearer {api_token}"}
    url = f"{API_BASE}/predictions/{prediction_id}"

    for _ in range(120):
        resp = httpx.get(url, headers=headers, timeout=30.0)
        if resp.status_code != 200:
            time.sleep(2)
            continue

        data = resp.json()
        status = data.get("status", "unknown")

        if status == "succeeded":
            return data
        elif status in ("failed", "canceled"):
            return data

        time.sleep(2)

    return {"status": "timeout", "error": "Prediction timed out after 4 minutes"}


def download_image(url: str, output_path: Path) -> bool:
    """Download generated image."""
    try:
        resp = httpx.get(url, timeout=60.0, follow_redirects=True)
        if resp.status_code == 200:
            output_path.write_bytes(resp.content)
            return True
    except Exception as e:
        print(f"    Download error: {e}")
    return False


# ── Main pipeline ───────────────────────────────────────────────────────────

def setup_model_photos():
    """Check for model photos and provide download guidance."""
    MODEL_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

    existing = list(MODEL_PHOTOS_DIR.glob("*.jpg")) + list(MODEL_PHOTOS_DIR.glob("*.png"))
    if existing:
        print(f"  Found {len(existing)} model photos in {MODEL_PHOTOS_DIR}")
        return True

    print(f"""
  NO MODEL PHOTOS FOUND

  VTON needs photos of people to dress. Add 3:4 ratio photos to:
    {MODEL_PHOTOS_DIR}/

  Requirements:
    - Full body shot, front-facing
    - Simple/neutral clothing (will be replaced)
    - Good lighting, clean background preferred
    - 3:4 aspect ratio (or VTON will auto-crop)

  File naming:
    model-male-1.jpg
    model-female-1.jpg
    model-male-2.jpg
    etc.

  You can use:
    - Your own photos
    - Stock photos from Unsplash/Pexels
    - AI-generated model photos (Gemini/Midjourney)
    """)
    return False


def main():
    parser = argparse.ArgumentParser(description="SkyyRose VTON Pipeline — 100% accurate model shots")
    parser.add_argument("--sku", help="Specific product SKU to process")
    parser.add_argument("--all", action="store_true", help="Process all products")
    parser.add_argument("--category", choices=["upper_body", "lower_body", "dresses"],
                        help="Override garment category")
    parser.add_argument("--model-photo", help="Specific model photo to use (filename in vton_models/)")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without calling API")
    parser.add_argument("--generate-models", action="store_true",
                        help="Use Gemini to generate stock model photos first")
    args = parser.parse_args()

    api_token = os.environ.get("REPLICATE_API_TOKEN")
    if not api_token and not args.dry_run:
        print("ERROR: REPLICATE_API_TOKEN not found")
        return 1

    # Select products
    if args.sku:
        if args.sku not in PRODUCTS:
            print(f"Unknown SKU: {args.sku}")
            print(f"Available: {', '.join(sorted(PRODUCTS))}")
            return 1
        skus = [args.sku]
    elif args.all:
        skus = sorted(PRODUCTS.keys())
    else:
        print("Specify --sku <name> or --all")
        print(f"Available SKUs: {', '.join(sorted(PRODUCTS))}")
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Check model photos
    if args.generate_models:
        print("\n  Generating model photos with Gemini...")
        generate_model_photos()
    elif not args.dry_run:
        if not setup_model_photos():
            print("\n  Add model photos first, or use --generate-models to create them with Gemini.")
            return 1

    print("=" * 70)
    print("  SKYYROSE VTON PIPELINE")
    print(f"  Engine: IDM-VTON ({VTON_MODEL})")
    print(f"  Products: {len(skus)}")
    print("=" * 70)

    if args.dry_run:
        for sku in skus:
            p = PRODUCTS[sku]
            techflat = TECHFLAT_DIR / p["techflat"]
            exists = "OK" if techflat.exists() else "MISSING"
            print(f"\n  {sku}: {p['name']}")
            print(f"    Tech flat: {p['techflat']} [{exists}]")
            print(f"    Category: {p['category']}")
            print(f"    Crop: {p['crop_region']}")
            print(f"    Description: {p['garment_des'][:80]}...")
            # Show what model photos would be used
            category = args.category or p["category"]
            model_files = DEFAULT_MODEL_PHOTOS.get(category, [])
            if args.model_photo:
                model_files = [args.model_photo]
            for mf in model_files:
                mp = MODEL_PHOTOS_DIR / mf
                m_exists = "OK" if mp.exists() else "NEEDED"
                print(f"    -> {sku}-{Path(mf).stem}-vton.webp  (model: {mf} [{m_exists}])")
        print(f"\n  Dry run complete.")
        return 0

    # Get available model photos
    model_photos = list(MODEL_PHOTOS_DIR.glob("*.jpg")) + list(MODEL_PHOTOS_DIR.glob("*.png"))
    if args.model_photo:
        mp = MODEL_PHOTOS_DIR / args.model_photo
        if not mp.exists():
            print(f"Model photo not found: {mp}")
            return 1
        model_photos = [mp]

    results = {}
    total = len(skus) * len(model_photos)
    count = 0

    for sku in skus:
        product = PRODUCTS[sku]
        techflat_path = TECHFLAT_DIR / product["techflat"]

        if not techflat_path.exists():
            print(f"\n  SKIP {sku}: tech flat not found")
            continue

        # Crop garment from tech flat
        print(f"\n[{sku}] {product['name']}")
        garment_path = crop_garment(techflat_path, product["crop_region"])
        print(f"  Cropped: {garment_path.name}")

        # Upload garment image
        garment_url = upload_image_to_replicate(api_token, garment_path)
        if not garment_url:
            print(f"  ERROR: Failed to upload garment image")
            continue

        category = args.category or product["category"]

        for model_photo in model_photos:
            count += 1
            model_name = model_photo.stem
            print(f"  [{count}/{total}] + {model_name}...", end="", flush=True)

            # Upload model photo
            model_url = upload_image_to_replicate(api_token, model_photo)
            if not model_url:
                print(" ERROR: upload failed")
                continue

            # Submit VTON
            prediction = create_vton_prediction(
                api_token,
                garment_url,
                model_url,
                product["garment_des"],
                category,
            )

            if prediction.get("error"):
                print(f" ERROR: {prediction['error'][:80]}")
                results[f"{sku}-{model_name}"] = {"error": prediction["error"]}
                continue

            pred_id = prediction.get("id", "")

            # Poll
            result = poll_prediction(api_token, pred_id)
            status = result.get("status", "unknown")

            if status == "succeeded":
                output = result.get("output", "")
                if output:
                    out_path = OUTPUT_DIR / f"{sku}-{model_name}-vton.webp"
                    if download_image(output, out_path):
                        size_kb = out_path.stat().st_size / 1024
                        print(f" OK ({size_kb:.0f} KB)")
                        results[f"{sku}-{model_name}"] = {
                            "status": "success",
                            "file": out_path.name,
                            "size_kb": round(size_kb),
                        }
                    else:
                        print(" download failed")
                        results[f"{sku}-{model_name}"] = {"error": "download failed"}
                else:
                    print(" no output")
                    results[f"{sku}-{model_name}"] = {"error": "no output"}
            else:
                error = result.get("error", "unknown")
                print(f" {status}: {str(error)[:80]}")
                results[f"{sku}-{model_name}"] = {"status": status, "error": str(error)[:200]}

            time.sleep(1)

    # Save results
    results_path = OUTPUT_DIR / "vton_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    successes = sum(1 for r in results.values() if r.get("status") == "success")
    print("\n" + "=" * 70)
    print(f"  COMPLETE: {successes}/{len(results)} model shots generated")
    print(f"  Output: {OUTPUT_DIR}")
    print("=" * 70)

    return 0 if successes == len(results) else 1


def generate_model_photos():
    """Generate neutral model photos using Gemini for VTON input."""
    from google import genai
    from google.genai import types

    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        print("  ERROR: GOOGLE_API_KEY not found")
        return

    client = genai.Client(api_key=key)
    MODEL_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

    prompts = [
        ("model-male-1.jpg", (
            "Full body photograph of a young Black male fashion model, "
            "front-facing, standing straight with relaxed confident pose. "
            "Wearing plain white t-shirt and dark jeans. Clean white studio background. "
            "Professional fashion photography lighting. 3:4 aspect ratio. "
            "The model has a neutral expression, looking at camera."
        )),
        ("model-female-1.jpg", (
            "Full body photograph of a young Black female fashion model, "
            "front-facing, standing straight with relaxed confident pose. "
            "Wearing plain white t-shirt and dark jeans. Clean white studio background. "
            "Professional fashion photography lighting. 3:4 aspect ratio. "
            "The model has a neutral expression, looking at camera."
        )),
        ("model-male-2.jpg", (
            "Full body photograph of a young Latino male fashion model, "
            "front-facing, standing with hands at sides, relaxed pose. "
            "Wearing plain gray t-shirt and black pants. Clean white studio background. "
            "Professional fashion photography lighting. 3:4 aspect ratio."
        )),
        ("model-female-2.jpg", (
            "Full body photograph of a young mixed-race female fashion model, "
            "front-facing, standing with confident relaxed pose. "
            "Wearing plain black tank top and light jeans. Clean white studio background. "
            "Professional fashion photography lighting. 3:4 aspect ratio."
        )),
    ]

    for filename, prompt in prompts:
        out_path = MODEL_PHOTOS_DIR / filename
        if out_path.exists():
            print(f"  EXISTS: {filename}")
            continue

        print(f"  Generating {filename}...", end="", flush=True)
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio="3:4"),
                ),
            )
            if response and response.parts:
                for part in response.parts:
                    if part.inline_data:
                        import tempfile
                        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                            tmp_path = tmp.name
                        part.as_image().save(tmp_path)
                        data = Path(tmp_path).read_bytes()
                        Path(tmp_path).unlink(missing_ok=True)
                        out_path.write_bytes(data)
                        print(f" OK ({len(data) / 1024:.0f} KB)")
                        break
                else:
                    print(" no image in response")
            else:
                print(" empty response")
        except Exception as e:
            print(f" ERROR: {e}")

        time.sleep(3)


if __name__ == "__main__":
    exit(main())
