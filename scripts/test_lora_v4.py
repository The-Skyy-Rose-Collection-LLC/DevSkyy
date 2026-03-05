#!/usr/bin/env python3
"""
Test SkyyRose LoRA v4 — generate sample images for each product.

Generates one image per product using per-SKU trigger words,
saves results to datasets/skyyrose_lora_v4/test_outputs/

Usage:
    source .venv-lora/bin/activate
    python scripts/test_lora_v4.py

    # Test specific products only:
    python scripts/test_lora_v4.py --skus br-d02 br-d04 lh-002

    # Generate model shots (person wearing product):
    python scripts/test_lora_v4.py --mode model

    # Generate tech flat style (product only):
    python scripts/test_lora_v4.py --mode flat
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).parent.parent

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

# LoRA v4 model info
MODEL_VERSION = "devskyy/skyyrose-lora-v4:8bf4de484c4d21064ce79f43d0ffc7942f444c5b2e2e1c112aa1463743fb232a"
API_BASE = "https://api.replicate.com/v1"

# Test prompts per SKU — each uses the per-SKU trigger word
TEST_PROMPTS = {
    "br-001": {
        "trigger": "skyyrose_br001",
        "flat": "black crewneck sweatshirt with large white and gray rose graphic, matching jogger pants, product flat lay on white background",
        "model": "fashion model wearing black crewneck with gray rose graphic and matching joggers, full body, studio lighting, editorial photoshoot",
    },
    "br-003-giants": {
        "trigger": "skyyrose_br003_giants",
        "flat": "black baseball jersey with orange trim, BLACK IS BEAUTIFUL text in orange, button front, product flat lay",
        "model": "male model wearing black baseball jersey with orange trim, BLACK IS BEAUTIFUL text, urban streetwear photoshoot",
    },
    "br-d02": {
        "trigger": "skyyrose_brd02",
        "flat": "red football jersey number 80 with rose fill pattern in numbers, V-neck, striped sleeves, product flat lay",
        "model": "male model wearing red football jersey #80 with rose pattern numbers, casual streetwear, city background",
    },
    "br-d03": {
        "trigger": "skyyrose_brd03",
        "flat": "white football jersey number 32 with dark rose fill in numbers, black stripe sleeves, product flat lay",
        "model": "female model wearing white football jersey #32 with rose pattern, paired with black pants, studio shot",
    },
    "br-d04": {
        "trigger": "skyyrose_brd04",
        "flat": "white basketball jersey THE BAY in gold text, grayscale rose gradient bottom, sleeveless V-neck, product flat lay",
        "model": "male model wearing white basketball jersey with THE BAY in gold, rose gradient, outdoor Bay Area photoshoot",
    },
    "lh-002": {
        "trigger": "skyyrose_lh002",
        "flat": "white varsity jacket with black sleeves, Love Hurts red script, red heart roses on back, product flat lay",
        "model": "female model wearing white and black varsity jacket with Love Hurts script, red accents, editorial fashion shot",
    },
    "lh-003": {
        "trigger": "skyyrose_lh003",
        "flat": "black track pants with white side stripes, red rose embroidery on left thigh, zippered ankles, product flat lay",
        "model": "model wearing black track pants with white stripes and red rose embroidery, casual streetwear photoshoot",
    },
    "lh-004": {
        "trigger": "skyyrose_lh004",
        "flat": "white shorts with all-over red rose bouquet pattern, Love Hurts script, black mesh side panels, product flat lay",
        "model": "model wearing white shorts with red rose bouquet pattern, Love Hurts branding, summer streetwear look",
    },
    "sg-002": {
        "trigger": "skyyrose_sg002",
        "flat": "white tee with purple rose graphic and Golden Gate Bridge nighttime photo-print shorts in purple, product flat lay",
        "model": "female model wearing white tee with purple rose graphic and purple bridge shorts, San Francisco street style",
    },
    "sg-007": {
        "trigger": "skyyrose_sg007",
        "flat": "black ribbed knit beanie with rose logo patch on cuff, product photo on white background",
        "model": "model wearing black beanie with rose patch, casual layered outfit, autumn streetwear look",
    },
    "sg-d01": {
        "trigger": "skyyrose_sgd01",
        "flat": "pastel V-chevron windbreaker set, pink hood, white base with colorful panels, matching pants, product flat lay",
        "model": "female model wearing pastel colorblock windbreaker set with pink hood, outdoor photoshoot, vibrant streetwear",
    },
    "sg-d03": {
        "trigger": "skyyrose_sgd03",
        "flat": "mint green crewneck sweatshirt with purple pink rose graphic, matching mint jogger pants, product flat lay",
        "model": "model wearing mint green crewneck set with purple rose graphic, matching joggers, lifestyle photoshoot",
    },
    "sg-d04": {
        "trigger": "skyyrose_sgd04",
        "flat": "mint green hooded dress with purple rose graphic, purple drawstrings, knee-length, product flat lay",
        "model": "female model wearing mint green hooded dress with purple rose graphic, fashion editorial, clean background",
    },
}


def create_prediction(api_token: str, prompt: str) -> dict:
    """Submit a prediction to Replicate."""
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    response = httpx.post(
        f"{API_BASE}/predictions",
        headers=headers,
        json={
            "version": MODEL_VERSION.split(":")[1],
            "input": {
                "prompt": prompt,
                "num_outputs": 1,
                "guidance_scale": 3.5,
                "num_inference_steps": 28,
                "output_format": "webp",
                "output_quality": 90,
            },
        },
        timeout=60.0,
    )

    if response.status_code not in (200, 201):
        return {"error": f"HTTP {response.status_code}: {response.text[:200]}"}

    return response.json()


def poll_prediction(api_token: str, prediction_id: str) -> dict:
    """Poll until prediction completes."""
    headers = {"Authorization": f"Bearer {api_token}"}
    url = f"{API_BASE}/predictions/{prediction_id}"

    for _ in range(120):  # Max 4 minutes
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


def main():
    parser = argparse.ArgumentParser(description="Test SkyyRose LoRA v4 generation")
    parser.add_argument("--skus", nargs="+", help="Specific SKUs to test (default: all)")
    parser.add_argument("--mode", choices=["flat", "model", "both"], default="both",
                        help="Generation mode: flat (product only), model (on person), both")
    args = parser.parse_args()

    api_token = os.environ.get("REPLICATE_API_TOKEN")
    if not api_token:
        print("ERROR: REPLICATE_API_TOKEN not found")
        return 1

    # Output directory
    output_dir = PROJECT_ROOT / "datasets" / "skyyrose_lora_v4" / "test_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Filter SKUs
    skus = args.skus if args.skus else list(TEST_PROMPTS.keys())
    modes = ["flat", "model"] if args.mode == "both" else [args.mode]

    total_tests = len(skus) * len(modes)
    print("=" * 70)
    print("  SKYYROSE LORA V4 — TEST GENERATION")
    print(f"  Model: {MODEL_VERSION.split(':')[0]}")
    print(f"  Products: {len(skus)} | Modes: {', '.join(modes)} | Total: {total_tests} images")
    print("=" * 70)

    results = {}
    test_num = 0

    for sku in skus:
        if sku not in TEST_PROMPTS:
            print(f"\n  SKIP: {sku} not in test prompts")
            continue

        product = TEST_PROMPTS[sku]

        for mode in modes:
            test_num += 1
            prompt = f"{product['trigger']} {product[mode]}"

            print(f"\n[{test_num}/{total_tests}] {sku} ({mode})")
            print(f"  Prompt: {prompt[:80]}...")

            # Submit
            prediction = create_prediction(api_token, prompt)
            if prediction.get("error"):
                print(f"  ERROR: {prediction['error']}")
                results[f"{sku}-{mode}"] = {"error": prediction["error"]}
                continue

            pred_id = prediction.get("id", "")
            print(f"  Prediction: {pred_id}", end="", flush=True)

            # Poll
            result = poll_prediction(api_token, pred_id)
            status = result.get("status", "unknown")

            if status == "succeeded":
                output_urls = result.get("output", [])
                if output_urls:
                    url = output_urls[0] if isinstance(output_urls, list) else output_urls
                    img_path = output_dir / f"{sku}-{mode}-v4.webp"
                    if download_image(url, img_path):
                        size_kb = img_path.stat().st_size / 1024
                        print(f" → {status} ({size_kb:.0f} KB)")
                        results[f"{sku}-{mode}"] = {
                            "status": "success",
                            "file": str(img_path.name),
                            "size_kb": round(size_kb),
                            "url": url,
                        }
                    else:
                        print(f" → download failed")
                        results[f"{sku}-{mode}"] = {"error": "download failed", "url": url}
                else:
                    print(f" → no output")
                    results[f"{sku}-{mode}"] = {"error": "no output URLs"}
            else:
                error = result.get("error", "unknown")
                print(f" → {status}: {error}")
                results[f"{sku}-{mode}"] = {"status": status, "error": str(error)[:200]}

            # Rate limit between predictions
            time.sleep(1)

    # Save results
    results_path = output_dir / "test_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    # Summary
    successes = sum(1 for r in results.values() if r.get("status") == "success")
    failures = len(results) - successes

    print("\n" + "=" * 70)
    print(f"  TEST COMPLETE: {successes}/{len(results)} succeeded")
    print(f"  Output: {output_dir}")
    print(f"  Results: {results_path}")
    print("=" * 70)

    if successes > 0:
        print(f"\n  View results:")
        print(f"    open {output_dir}")

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    exit(main())
