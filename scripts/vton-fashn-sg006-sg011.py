#!/usr/bin/env python3
"""
VTON generation for sg-006 and sg-011 using FASHN VTON v1.5 on HuggingFace.
Falls back to IDM-VTON (yisol/IDM-VTON) if FASHN fails.
Outputs saved as WebP to existing product image paths.
"""
import sys
import os
import shutil
from pathlib import Path
from PIL import Image
from gradio_client import Client, handle_file

BASE = Path("/Users/theceo/DevSkyy/wordpress-theme/skyyrose-flagship")
AVATAR = BASE / "assets/images/avatar/skyyrose-model-front.png"
PRODUCTS = BASE / "assets/images/products"

JOBS = [
    {
        "sku": "sg-006",
        "garment": PRODUCTS / "sg-006-mint-lavender-hoodie.webp",
        "output": PRODUCTS / "sg-006-front-model.webp",
    },
    {
        "sku": "sg-011",
        "garment": PRODUCTS / "sg-011-label-tee-white.webp",
        "output": PRODUCTS / "sg-011-front-model.webp",
    },
]


def convert_to_webp(input_path, output_path, quality=85):
    img = Image.open(input_path)
    img.save(str(output_path), "WEBP", quality=quality)
    size_kb = output_path.stat().st_size / 1024
    print(f"  Saved: {output_path.name} ({size_kb:.1f} KB)")


def try_fashn(avatar_path, garment_path, sku):
    """Try FASHN VTON v1.5. Returns path to result image, 'QUOTA_ERROR', or None."""
    print(f"\n[{sku}] Connecting to fashn-ai/fashn-vton-1.5...")
    try:
        client = Client("fashn-ai/fashn-vton-1.5")
        print(f"  Connected. Viewing API...")
        client.view_api(print_info=True)

        # Try the standard predict call
        print(f"  Submitting VTON job...")
        result = client.predict(
            handle_file(str(avatar_path)),
            handle_file(str(garment_path)),
            api_name="/tryon",
        )
        print(f"  Raw result: {result}")

        if isinstance(result, (list, tuple)):
            for item in result:
                p = str(item) if not isinstance(item, dict) else item.get("path", item.get("url", ""))
                if p and os.path.exists(p):
                    print(f"  Found result file: {p}")
                    return p
            # Maybe it's a dict with value key
            if result and isinstance(result[0], dict) and "value" in result[0]:
                p = result[0]["value"]
                if os.path.exists(str(p)):
                    return str(p)
        elif isinstance(result, str) and os.path.exists(result):
            return result
        elif isinstance(result, dict):
            p = result.get("path", result.get("url", result.get("value", "")))
            if p and os.path.exists(str(p)):
                return str(p)

        print(f"  Could not extract output file from result")
        return None

    except Exception as e:
        msg = str(e).lower()
        if "quota" in msg or "gpu" in msg or "exceeded" in msg:
            print(f"  ZeroGPU quota error: {e}")
            return "QUOTA_ERROR"
        print(f"  FASHN error: {e}")
        return None


def try_idm_vton(avatar_path, garment_path, sku):
    """Try IDM-VTON. Returns path to result image, 'QUOTA_ERROR', or None."""
    print(f"\n[{sku}] Connecting to yisol/IDM-VTON...")
    try:
        client = Client("yisol/IDM-VTON")
        print(f"  Connected. Viewing API...")
        client.view_api(print_info=True)

        # IDM-VTON expects: model_image (dict with background/layers/composite), garment, description, booleans, steps, seed
        result = client.predict(
            dict(
                background=handle_file(str(avatar_path)),
                layers=[],
                composite=None,
            ),
            handle_file(str(garment_path)),
            "A fashion model wearing the garment",
            True,   # is_checked (auto-crop)
            True,   # is_checked_crop (auto-mask)
            30,     # denoise_steps
            42,     # seed
            api_name="/tryon",
        )
        print(f"  Raw result: {result}")

        if isinstance(result, (list, tuple)):
            for item in result:
                p = str(item) if not isinstance(item, dict) else item.get("path", item.get("url", ""))
                if p and os.path.exists(p):
                    return p
        elif isinstance(result, str) and os.path.exists(result):
            return result

        print(f"  Could not extract output file from result")
        return None

    except Exception as e:
        msg = str(e).lower()
        if "quota" in msg or "gpu" in msg or "exceeded" in msg:
            print(f"  ZeroGPU quota error: {e}")
            return "QUOTA_ERROR"
        print(f"  IDM-VTON error: {e}")
        return None


def main():
    results = {}
    quota_blocked = False

    for job in JOBS:
        sku = job["sku"]
        garment = job["garment"]
        output = job["output"]

        if not garment.exists():
            print(f"[{sku}] Garment not found: {garment}")
            results[sku] = "MISSING_GARMENT"
            continue

        print(f"\n{'='*60}")
        print(f"Processing {sku}: {garment.name}")
        print(f"{'='*60}")

        backup = output.with_suffix(".webp.bak")
        if output.exists():
            shutil.copy2(output, backup)
            print(f"  Backed up: {backup.name}")

        # Try FASHN first
        result_path = try_fashn(AVATAR, garment, sku)

        # If FASHN failed (not quota), try IDM-VTON
        if result_path is None:
            result_path = try_idm_vton(AVATAR, garment, sku)

        # Handle results
        if result_path == "QUOTA_ERROR":
            print(f"\n[{sku}] BLOCKED by ZeroGPU quota. Stopping.")
            results[sku] = "QUOTA_BLOCKED"
            quota_blocked = True
            if backup.exists():
                shutil.copy2(backup, output)
                backup.unlink()
            break
        elif result_path and os.path.exists(result_path):
            convert_to_webp(result_path, output, quality=85)
            results[sku] = "SUCCESS"
            if backup.exists():
                backup.unlink()
        else:
            print(f"\n[{sku}] All providers failed.")
            results[sku] = "FAILED"
            if backup.exists():
                shutil.copy2(backup, output)
                backup.unlink()

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for sku, status in results.items():
        print(f"  {sku}: {status}")

    if quota_blocked:
        print("\nZeroGPU daily quota reached. Try again later or run:")
        print("  huggingface-cli login")
        sys.exit(2)

    if all(s == "SUCCESS" for s in results.values()):
        print("\nAll VTON images generated successfully!")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
