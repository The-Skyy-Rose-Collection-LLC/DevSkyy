#!/usr/bin/env python3
"""
Generate AI models wearing EXACT SkyyRose merchandise using IP-Adapter Plus.

CRITICAL: Models MUST wear the EXACT apparel from product photos.
Uses IP-Adapter Plus at scale 0.9 for maximum detail preservation.
"""

import sys
import time
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file
from dotenv import load_dotenv  # noqa: E402

load_dotenv(project_root / ".env")

print("=== SkyyRose AI Model Generator ===")
print("Generating models wearing EXACT merchandise\n")

try:
    import torch
    from diffusers import AutoPipelineForText2Image, DDIMScheduler
    from diffusers.utils import load_image
    from transformers import CLIPVisionModelWithProjection
except ImportError:
    print("Installing required packages...")
    import subprocess

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "diffusers[torch]",
            "transformers",
            "accelerate",
            "safetensors",
        ],
        check=True,
    )
    import torch
    from diffusers import AutoPipelineForText2Image, DDIMScheduler
    from diffusers.utils import load_image
    from transformers import CLIPVisionModelWithProjection


# Product photo directories
ENHANCED_DIR = project_root / "assets" / "enhanced_products" / "all"
OUTPUT_DIR = project_root / "assets" / "ai-models-with-products"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# SkyyRose brand DNA for prompts
BRAND_PROMPTS = {
    "SIGNATURE": "luxury streetwear fashion model wearing {product}, confident, sophisticated, premium, elegant, timeless, professional photoshoot, studio lighting, high fashion, 4k, ultra detailed",
    "BLACK_ROSE": "gothic luxury fashion model wearing {product}, mysterious, powerful, bold, dark elegance, rebellious sophistication, dramatic lighting, high fashion, 4k, ultra detailed",
    "LOVE_HURTS": "emotional streetwear fashion model wearing {product}, authentic, heartfelt, artistic passion, vulnerable strength, premium quality, professional photoshoot, 4k, ultra detailed",
}

NEGATIVE_PROMPT = "blurry, smooth, plastic, low quality, distorted, deformed, duplicate, watermark, text, wrong colors, mismatched clothing, cartoon, anime"


def detect_collection(filename: str) -> str:
    """Detect which collection a product belongs to from filename."""
    fname_lower = filename.lower()

    if "black" in fname_lower or "noir" in fname_lower or "gothic" in fname_lower:
        return "BLACK_ROSE"
    elif "love" in fname_lower or "hurts" in fname_lower or "heart" in fname_lower:
        return "LOVE_HURTS"
    else:
        return "SIGNATURE"


def extract_product_name(filename: str) -> str:
    """Extract clean product name from filename."""
    # Remove extension and enhanced suffix
    name = filename.replace("_enhanced.jpg", "").replace(".jpg", "")

    # Convert underscores to spaces and title case
    return name.replace("_", " ").title()


def setup_pipeline(device: str = "mps") -> tuple:
    """Setup SDXL pipeline with IP-Adapter Plus."""

    print("Loading CLIP Vision Model...")
    image_encoder = CLIPVisionModelWithProjection.from_pretrained(
        "h94/IP-Adapter", subfolder="models/image_encoder", torch_dtype=torch.float16
    )

    print("Loading SDXL Base Model (Juggernaut-XL-v9)...")
    pipeline = AutoPipelineForText2Image.from_pretrained(
        "RunDiffusion/Juggernaut-XL-v9",
        image_encoder=image_encoder,
        torch_dtype=torch.float16,
        variant="fp16",
    )

    # Use DDIM scheduler for better quality
    pipeline.scheduler = DDIMScheduler.from_config(pipeline.scheduler.config)

    # Load IP-Adapter Plus for exact clothing transfer
    print("Loading IP-Adapter Plus (exact clothing transfer)...")
    pipeline.load_ip_adapter(
        "h94/IP-Adapter",
        subfolder="sdxl_models",
        weight_name="ip-adapter-plus_sdxl_vit-h.safetensors",
    )

    # CRITICAL: High scale (0.9) for strong clothing preservation
    pipeline.set_ip_adapter_scale(0.9)

    # Enable memory optimizations BEFORE moving to device
    # These reduce memory usage from 44GB → 7GB for high-res images
    print("Enabling memory optimizations...")
    pipeline.enable_sequential_cpu_offload()  # Move inactive parts to CPU
    pipeline.vae.enable_slicing()  # Process images one at a time
    pipeline.vae.enable_tiling()  # Process in tiles (critical for memory)

    print(f"✅ Pipeline ready on {device}\n")

    return pipeline


def generate_model_with_product(
    pipeline,
    product_image_path: Path,
    output_path: Path,
    collection: str,
    product_name: str,
    seed: int = 42,
) -> bool:
    """Generate AI model wearing exact product using IP-Adapter Plus."""

    try:
        # Load product image
        product_image = load_image(str(product_image_path))

        # Generate prompt for collection
        prompt_template = BRAND_PROMPTS[collection]
        prompt = prompt_template.format(product=product_name)

        print(f"  Prompt: {prompt[:80]}...")
        print("  IP-Adapter Scale: 0.9 (strong clothing preservation)")

        # Generate with IP-Adapter (use CPU generator for MPS compatibility)
        generator = torch.Generator(device="cpu").manual_seed(seed)

        result = pipeline(
            prompt=prompt,
            negative_prompt=NEGATIVE_PROMPT,
            ip_adapter_image=product_image,  # Reference for exact clothing
            num_inference_steps=30,
            guidance_scale=7.5,
            generator=generator,
            height=768,  # Reduced from 1024 for memory optimization
            width=768,  # Reduced from 1024 for memory optimization
        ).images[0]

        # Save result
        result.save(output_path)
        print(f"  ✅ Saved: {output_path.name}")

        return True

    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


def main():
    """Generate AI models for all enhanced products."""

    # Check if enhanced products exist
    if not ENHANCED_DIR.exists():
        print(f"❌ Enhanced products directory not found: {ENHANCED_DIR}")
        return 1

    # Get all enhanced product images
    product_images = list(ENHANCED_DIR.glob("*.jpg"))

    if not product_images:
        print(f"❌ No product images found in: {ENHANCED_DIR}")
        return 1

    print(f"Found {len(product_images)} product images\n")

    # Setup pipeline - prefer MPS (Mac GPU) over CPU
    if torch.cuda.is_available():
        device = "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"
        print("✅ Using Metal Performance Shaders (Mac GPU acceleration)\n")
    else:
        device = "cpu"
        print("⚠️  No GPU available. Using CPU (will be very slow)\n")

    pipeline = setup_pipeline(device)

    # Generate AI models for each product
    success_count = 0

    for idx, product_path in enumerate(product_images, 1):
        print(f"\n[{idx}/{len(product_images)}] Processing: {product_path.name}")

        # Detect collection and extract product name
        collection = detect_collection(product_path.name)
        product_name = extract_product_name(product_path.name)

        print(f"  Collection: {collection}")
        print(f"  Product: {product_name}")

        # Output filename
        output_filename = f"model_{product_path.stem}.jpg"
        output_path = OUTPUT_DIR / output_filename

        # Skip if already generated
        if output_path.exists():
            print("  ⏭️  Already exists, skipping")
            success_count += 1
            continue

        # Generate with retry (ralph-loop)
        max_retries = 2
        for attempt in range(max_retries):
            if generate_model_with_product(
                pipeline, product_path, output_path, collection, product_name, seed=42 + idx
            ):
                success_count += 1
                break
            elif attempt < max_retries - 1:
                wait_time = 2**attempt
                print(f"  ⚠️  Retry in {wait_time}s...")
                time.sleep(wait_time)

        # Small delay between generations
        if idx < len(product_images):
            time.sleep(1)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"✅ Generated {success_count}/{len(product_images)} AI models")
    print(f"{'=' * 60}")
    print(f"\nOutput directory: {OUTPUT_DIR}")

    if success_count == len(product_images):
        print("\n📋 Next Steps:")
        print("  1. Review AI models to verify EXACT apparel match")
        print("  2. Upload to WordPress media library")
        print("  3. Use in product marketing and ads")
        return 0
    else:
        print(f"\n⚠️  {len(product_images) - success_count} generations failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
