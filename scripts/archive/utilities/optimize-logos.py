"""
SkyyRose Logo Enhancement Pipeline
===================================
1. AI background removal (BRIA-RMBG-2.0)
2. AI-guided upscale + enhance (finegrain-image-enhancer)
3. High-quality transparent WebP output

Uses HF token for authenticated GPU quota.
"""

import os
import shutil
import sys
from pathlib import Path

VENV = Path("/Users/theceo/DevSkyy/.venv-imagery")
sys.path.insert(0, str(VENV / "lib/python3.13/site-packages"))

os.environ.setdefault("HF_TOKEN", os.getenv("HF_TOKEN", ""))

from gradio_client import Client, handle_file
from PIL import Image, ImageEnhance, ImageFilter

OUT_DIR = Path("/Users/theceo/DevSkyy/wordpress-theme/skyyrose-flagship/assets/branding")
WORK_DIR = Path("/tmp/skyyrose-logo-pipeline")
WORK_DIR.mkdir(exist_ok=True)

HF_TOKEN = os.getenv("HF_TOKEN", "")

LOGOS = [
    {
        "src": "/Users/theceo/Pictures/Photos Library.photoslibrary/resources/derivatives/B/BE33A5B9-BE47-48AA-9F81-229AE8328539_1_102_o.jpeg",
        "name": "skyyrose-monogram",
        "prompt": "luxury fashion brand monogram, metallic rose gold lettering, sharp crisp edges, premium quality",
    },
    {
        "src": "/Users/theceo/Pictures/Photos Library.photoslibrary/resources/derivatives/E/ECCA0481-ECD7-4171-9979-3EDEC19A333C_1_102_o.jpeg",
        "name": "skyyrose-rose-icon",
        "prompt": "luxury metallic rose gold flower icon, sharp metallic petals, premium brand emblem, crisp detail",
    },
    {
        "src": "/Users/theceo/Pictures/Photos Library.photoslibrary/resources/derivatives/masters/6/60568819-6A5F-4915-867C-7ABE906DAFC4_4_5005_c.jpeg",
        "name": "love-hurts-logo",
        "prompt": "enamel pin logo, red heart with thorns, love hurts script lettering, sharp detail, premium quality",
    },
    {
        "src": "/Users/theceo/Pictures/Photos Library.photoslibrary/resources/derivatives/2/2C70F0F2-3ED0-4E2E-B579-93EF9496C94C_1_102_o.jpeg",
        "name": "black-rose-logo",
        "prompt": "crystal glass star trophy with black rose inside, luxury award, sharp detail, premium quality",
    },
    {
        "src": "/Users/theceo/Pictures/Photos Library.photoslibrary/resources/derivatives/C/C3884F19-81F6-417A-A021-B0D0DDBB89AB_1_105_c.jpeg",
        "name": "black-rose-collection-text",
        "prompt": "luxury fashion brand text logo, The Black Rose Collection, 3D glossy black lettering, sharp crisp edges",
    },
]


def step_remove_bg(src_path: str, out_path: str) -> str:
    """AI background removal using BRIA-RMBG-2.0."""
    # Check if we already have the bg-removed version from a previous run
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        print("        (cached from previous run)")
        return out_path
    client = Client("briaai/BRIA-RMBG-2.0")
    result = client.predict(handle_file(src_path), api_name="/image")
    shutil.copy(result[1], out_path)
    return out_path


def step_enhance(src_path: str, out_path: str, prompt: str) -> str:
    """AI-guided enhance + upscale using finegrain image enhancer."""
    client = Client("finegrain/finegrain-image-enhancer")
    result = client.predict(
        input_image=handle_file(src_path),
        prompt=prompt,
        negative_prompt="blurry, low quality, pixelated, artifacts, noise, jpeg artifacts, washed out",
        seed=42,
        upscale_factor=4,  # 4x upscale for max resolution
        controlnet_scale=0.6,
        controlnet_decay=1.0,
        condition_scale=6,
        tile_width=112,
        tile_height=144,
        denoise_strength=0.30,  # slightly lower to preserve original detail
        num_inference_steps=20,  # more steps for better quality
        solver="DDIM",
        api_name="/process",
    )
    # result is a list of [before_path, after_path]
    enhanced_path = result[1] if isinstance(result, list) else result[1]["path"]
    shutil.copy(enhanced_path, out_path)
    return out_path


def step_finalize(src_path: str, out_path: str) -> str:
    """Sharpen + convert to high-quality transparent WebP."""
    img = Image.open(src_path).convert("RGBA")

    # Light sharpening for crisp edges
    img = img.filter(ImageFilter.SHARPEN)

    # Boost contrast slightly for luxury feel
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.05)

    img.save(
        out_path,
        format="WEBP",
        quality=95,
        method=6,
        lossless=False,
        exact=True,
    )
    return out_path


def process_logo(logo: dict):
    name = logo["name"]
    src = logo["src"]

    src_size = os.path.getsize(src)
    img = Image.open(src)
    print(f"\n{'=' * 55}")
    print(f"  {name}")
    print(f"  Source: {img.size[0]}x{img.size[1]}, {src_size / 1024:.1f}KB")
    print(f"{'=' * 55}")

    # Step 1: Remove background
    print("  [1/3] AI background removal (BRIA-RMBG-2.0)...")
    nobg_path = str(WORK_DIR / f"{name}-nobg.png")
    step_remove_bg(src, nobg_path)
    nobg_img = Image.open(nobg_path)
    print(
        f"        → {nobg_img.size[0]}x{nobg_img.size[1]}, {os.path.getsize(nobg_path) / 1024:.1f}KB"
    )

    # Step 2: AI enhance + 4x upscale
    print("  [2/3] AI enhance + 4x upscale (finegrain)...")
    enhanced_path = str(WORK_DIR / f"{name}-enhanced.png")
    step_enhance(nobg_path, enhanced_path, logo["prompt"])
    enh_img = Image.open(enhanced_path)
    print(
        f"        → {enh_img.size[0]}x{enh_img.size[1]}, {os.path.getsize(enhanced_path) / 1024:.1f}KB"
    )

    # Step 3: Sharpen + WebP
    print("  [3/3] Sharpen + high-quality transparent WebP...")
    webp_path = str(OUT_DIR / f"{name}.webp")
    step_finalize(enhanced_path, webp_path)
    final_img = Image.open(webp_path)
    final_size = os.path.getsize(webp_path)
    print(f"        → {final_img.size[0]}x{final_img.size[1]}, {final_size / 1024:.1f}KB")
    print(f"  ✓ {name}.webp")


def main():
    print("\n" + "=" * 55)
    print("  SKYYROSE LOGO ENHANCEMENT PIPELINE")
    print("  BG Removal → AI 4x Enhance → Sharpen → WebP")
    print("=" * 55)

    for logo in LOGOS:
        try:
            process_logo(logo)
        except Exception as e:
            print(f"\n  ✗ FAILED {logo['name']}: {e}")
            continue

    print("\n" + "=" * 55)
    print("  PIPELINE COMPLETE")
    print(f"  Output: {OUT_DIR}")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
