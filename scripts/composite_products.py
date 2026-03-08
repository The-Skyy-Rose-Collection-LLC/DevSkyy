#!/usr/bin/env python3
"""
Composite product photos INTO immersive scene backgrounds using FAL AI Bria Product Shot.

Usage:
    source .venv-imagery/bin/activate
    python scripts/composite_products.py --scene black-rose-rooftop-garden
    python scripts/composite_products.py --all
    python scripts/composite_products.py --list
    python scripts/composite_products.py --all --dry-run
"""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

# Load env vars from .env.hf
PROJECT_ROOT = Path(__file__).resolve().parent.parent
for env_file in [PROJECT_ROOT / ".env.hf", PROJECT_ROOT / ".env"]:
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.strip() and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

THEME_DIR = PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship"
PRODUCTS_DIR = THEME_DIR / "assets" / "images" / "products"
SCENES_DIR = THEME_DIR / "assets" / "scenes"

FAL_KEY = os.environ.get("FAL_KEY", "")
FAL_ENDPOINT = "https://fal.run/fal-ai/bria/product-shot"

# --- Scene definitions ---
SCENES = {
    "black-rose-rooftop-garden": {
        "collection": "black-rose",
        "background": "black-rose-rooftop-garden-v2.png",
        "products": [
            {
                "sku": "br-006",
                "placement": "draped over arm of black lounge chair, left side of scene",
            },
            {
                "sku": "br-001",
                "placement": "folded on seat of low-profile couch, center-left of scene",
            },
            {
                "sku": "br-002",
                "placement": "folded on side table next to planter, center-right of scene",
            },
            {
                "sku": "br-004",
                "placement": "hanging from matte black clothing rack, right side of scene",
            },
        ],
    },
    "love-hurts-cathedral-rose-chamber": {
        "collection": "love-hurts",
        "background": "love-hurts-cathedral-rose-chamber-v2.png",
        "products": [
            {
                "sku": "lh-005",
                "placement": "draped beside enchanted rose glass dome, center-left of scene",
            },
            {
                "sku": "lh-001",
                "placement": "hung from gothic candelabra stand, right side of scene",
            },
            {
                "sku": "lh-003",
                "placement": "displayed on stone ledge in stained glass alcove, center of scene",
            },
        ],
    },
    "signature-golden-gate-showroom": {
        "collection": "signature",
        "background": "signature-golden-gate-showroom-v2.png",
        "products": [
            {"sku": "sg-012", "placement": "hanging on wall-mounted clothing rack, left side"},
            {"sku": "sg-005", "placement": "featured on center marble display table"},
            {"sku": "sg-007", "placement": "on marble pedestal, left-center"},
            {"sku": "sg-011", "placement": "hanging on wall-mounted clothing rack, right side"},
        ],
    },
}

COST_PER_IMAGE = 0.04


def encode_image_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def call_fal_product_shot(
    product_path: Path, scene_path: Path, placement: str, retries: int = 3
) -> dict:
    """Call FAL AI Bria Product Shot API."""
    import urllib.error
    import urllib.request

    product_b64 = encode_image_base64(product_path)
    scene_b64 = encode_image_base64(scene_path)

    # Determine mime types
    p_ext = product_path.suffix.lower()
    s_ext = scene_path.suffix.lower()
    p_mime = "image/webp" if p_ext == ".webp" else "image/png"
    s_mime = "image/webp" if s_ext == ".webp" else "image/png"

    payload = json.dumps(
        {
            "image_url": f"data:{p_mime};base64,{product_b64}",
            "ref_image_url": f"data:{s_mime};base64,{scene_b64}",
            "scene_description": f"Luxury fashion showroom. Place the clothing item {placement}. Photorealistic lighting, high-end retail environment.",
            "placement_type": "automatic",
            "num_results": 1,
            "fast": False,
        }
    ).encode("utf-8")

    headers = {
        "Authorization": f"Key {FAL_KEY}",
        "Content-Type": "application/json",
    }

    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(FAL_ENDPOINT, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            # Synchronous endpoint returns result directly
            return result

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"  [attempt {attempt}/{retries}] HTTP {e.code}: {body[:200]}")
            if attempt < retries:
                time.sleep(8 * attempt)
        except Exception as e:
            print(f"  [attempt {attempt}/{retries}] Error: {e}")
            if attempt < retries:
                time.sleep(8 * attempt)

    return {"error": "All retries exhausted"}


def poll_fal_result(request_id: str, retries: int = 30) -> dict:
    """Poll FAL queue for result."""
    import urllib.request

    status_url = f"https://queue.fal.run/fal-ai/bria/product-shot/requests/{request_id}/status"
    result_url = f"https://queue.fal.run/fal-ai/bria/product-shot/requests/{request_id}"
    headers = {"Authorization": f"Key {FAL_KEY}"}

    for i in range(retries):
        try:
            req = urllib.request.Request(status_url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                status = json.loads(resp.read().decode("utf-8"))

            if status.get("status") == "COMPLETED":
                req2 = urllib.request.Request(result_url, headers=headers)
                with urllib.request.urlopen(req2, timeout=30) as resp2:
                    return json.loads(resp2.read().decode("utf-8"))
            elif status.get("status") in ("FAILED", "CANCELLED"):
                return {"error": f"Job {status.get('status')}: {status}"}

            time.sleep(3)
        except Exception as e:
            print(f"  Poll error: {e}")
            time.sleep(5)

    return {"error": "Polling timeout"}


def download_image(url: str, dest: Path):
    """Download image from URL to local path."""
    import urllib.request

    urllib.request.urlretrieve(url, str(dest))


def process_scene(scene_key: str, dry_run: bool = False):
    """Process all products for a single scene."""
    scene = SCENES[scene_key]
    collection = scene["collection"]
    bg_path = SCENES_DIR / collection / scene["background"]
    out_dir = SCENES_DIR / collection

    if not bg_path.exists():
        print(f"ERROR: Background not found: {bg_path}")
        return

    print(f"\n{'=' * 60}")
    print(f"Scene: {scene_key}")
    print(f"Background: {bg_path.name}")
    print(f"Products: {len(scene['products'])}")
    print(f"{'=' * 60}")

    total_cost = 0.0
    composited_files = []

    for prod in scene["products"]:
        sku = prod["sku"]
        product_path = PRODUCTS_DIR / f"{sku}-front-model.webp"

        if not product_path.exists():
            print(f"\n  SKIP {sku}: {product_path.name} not found")
            continue

        out_name = f"{scene['background'].replace('.png', '')}-{sku}.webp"
        out_path = out_dir / out_name

        print(f"\n  Processing {sku}...")
        print(f"    Product: {product_path.name} ({product_path.stat().st_size // 1024}KB)")
        print(f"    Placement: {prod['placement']}")
        print(f"    Output: {out_name}")

        if dry_run:
            print(f"    [DRY RUN] Would call FAL API (~${COST_PER_IMAGE:.2f})")
            total_cost += COST_PER_IMAGE
            continue

        result = call_fal_product_shot(product_path, bg_path, prod["placement"])

        if "error" in result:
            print(f"    FAILED: {result['error']}")
            continue

        # Extract image URL from result
        image_url = None
        if "image" in result and "url" in result["image"]:
            image_url = result["image"]["url"]
        elif "images" in result and len(result["images"]) > 0:
            image_url = result["images"][0].get("url")
        elif "output" in result:
            image_url = result["output"] if isinstance(result["output"], str) else None

        if not image_url:
            print(f"    FAILED: No image URL in response: {json.dumps(result)[:200]}")
            continue

        download_image(image_url, out_path)
        size_kb = out_path.stat().st_size // 1024
        print(f"    SUCCESS: {out_name} ({size_kb}KB) — ${COST_PER_IMAGE:.2f}")
        total_cost += COST_PER_IMAGE
        composited_files.append(out_path)

    print(f"\n  Scene total: {len(composited_files)} images, ${total_cost:.2f}")
    return composited_files


def main():
    parser = argparse.ArgumentParser(
        description="Composite products into scene backgrounds using FAL AI"
    )
    parser.add_argument("--scene", type=str, help="Scene key to process")
    parser.add_argument("--all", action="store_true", help="Process all scenes")
    parser.add_argument("--list", action="store_true", help="List available scenes")
    parser.add_argument("--dry-run", action="store_true", help="Preview without API calls")
    args = parser.parse_args()

    if not FAL_KEY:
        print("ERROR: FAL_KEY not found. Check .env.hf")
        sys.exit(1)

    if args.list:
        print("\nAvailable scenes:")
        for key, scene in SCENES.items():
            print(f"  {key}")
            for p in scene["products"]:
                exists = (PRODUCTS_DIR / f"{p['sku']}-front-model.webp").exists()
                status = "OK" if exists else "MISSING"
                print(f"    {p['sku']} [{status}] — {p['placement']}")
        return

    if not args.scene and not args.all:
        parser.print_help()
        return

    scenes_to_process = list(SCENES.keys()) if args.all else [args.scene]
    grand_total = 0.0

    for scene_key in scenes_to_process:
        if scene_key not in SCENES:
            print(f"Unknown scene: {scene_key}")
            print(f"Available: {', '.join(SCENES.keys())}")
            continue
        process_scene(scene_key, dry_run=args.dry_run)

    print(f"\n{'=' * 60}")
    print(f"DONE. {'(DRY RUN)' if args.dry_run else ''}")


if __name__ == "__main__":
    main()
