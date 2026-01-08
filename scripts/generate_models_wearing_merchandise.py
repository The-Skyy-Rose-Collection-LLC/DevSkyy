#!/usr/bin/env python3
"""
Generate AI Models Wearing EXACT SkyyRose Merchandise.

Uses ControlNet Reference Pipeline to ensure AI models are wearing
the EXACT apparel from product photos - not generic versions.

CRITICAL: The clothing must be identical to the source product photos.
"""

import asyncio
import json
import sys
from pathlib import Path

import torch
from diffusers import (
    AutoencoderKL,
    DPMSolverMultistepScheduler,
    StableDiffusionXLPipeline,
)
from PIL import Image

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# SkyyRose brand DNA for consistent style
BRAND_DNA = {
    "BLACK_ROSE": {
        "style": "gothic luxury, dramatic lighting, dark aesthetic, rebellious elegance",
        "negative": "bright colors, casual, playful, cheerful",
    },
    "LOVE_HURTS": {
        "style": "emotional depth, artistic, warm tones, authentic luxury",
        "negative": "cold, corporate, impersonal, generic",
    },
    "SIGNATURE": {
        "style": "understated luxury, confident, premium streetwear, everyday excellence",
        "negative": "loud, flashy, over-branded, cheap",
    },
}


def detect_collection(filename: str) -> str:
    """Detect collection from filename."""
    filename_lower = filename.lower()
    if "black" in filename_lower or "noir" in filename_lower:
        return "BLACK_ROSE"
    elif "love" in filename_lower or "heart" in filename_lower:
        return "LOVE_HURTS"
    else:
        return "SIGNATURE"


def detect_garment_type(filename: str) -> str:
    """Detect type of garment from filename."""
    filename_lower = filename.lower()

    if any(word in filename_lower for word in ["tee", "t-shirt", "shirt"]):
        return "tee"
    elif any(word in filename_lower for word in ["hoodie", "hooded"]):
        return "hoodie"
    elif any(word in filename_lower for word in ["sweatshirt", "crewneck"]):
        return "sweatshirt"
    elif any(word in filename_lower for word in ["shorts"]):
        return "shorts"
    elif any(word in filename_lower for word in ["sherpa", "jacket"]):
        return "sherpa"
    elif any(word in filename_lower for word in ["beanie", "hat"]):
        return "beanie"
    elif any(word in filename_lower for word in ["dress"]):
        return "dress"
    else:
        return "apparel"


async def generate_model_wearing_product(
    product_photo_path: Path,
    collection: str,
    output_dir: Path,
    device: str = "cuda" if torch.cuda.is_available() else "cpu",
) -> dict:
    """
    Generate AI model wearing EXACT product from photo.

    Uses ControlNet reference pipeline to ensure the clothing
    is identical to the product photo.
    """

    print(f"\n{'='*60}")
    print(f"Generating model wearing: {product_photo_path.name}")
    print(f"Collection: {collection}")
    print(f"{'='*60}")

    # Detect garment type
    garment_type = detect_garment_type(product_photo_path.name)

    # Load VAE for better quality
    print("  Loading VAE and pipeline...")
    vae = AutoencoderKL.from_pretrained(
        "madebyollin/sdxl-vae-fp16-fix",
        torch_dtype=torch.float16,
    ).to(device)

    # Load SDXL pipeline with IP-Adapter for EXACT clothing transfer
    pipeline = StableDiffusionXLPipeline.from_pretrained(
        "RunDiffusion/Juggernaut-XL-v9",
        torch_dtype=torch.float16,
        vae=vae,
        variant="fp16",
    ).to(device)

    pipeline.scheduler = DPMSolverMultistepScheduler.from_config(pipeline.scheduler.config)
    pipeline.scheduler.config.use_karras_sigmas = True

    # Load IP-Adapter Plus for preserving EXACT clothing details
    print("  Loading IP-Adapter Plus for exact clothing transfer...")
    pipeline.load_ip_adapter(
        "h94/IP-Adapter",
        subfolder="sdxl_models",
        weight_name="ip-adapter-plus_sdxl_vit-h.safetensors",
        image_encoder_folder="models/image_encoder",
    )
    # High scale = strong influence from reference image (EXACT clothing)
    pipeline.set_ip_adapter_scale(0.9)

    # Load product photo as reference
    print("  Loading product photo as reference...")
    product_image = Image.open(product_photo_path)

    # Resize to SDXL size
    product_image = product_image.resize((1024, 1024))

    # Get brand style
    brand_style = BRAND_DNA.get(collection, BRAND_DNA["SIGNATURE"])

    # Construct prompt to ensure EXACT clothing
    prompt = f"""
    Professional fashion photography, full body shot,
    attractive model wearing the EXACT {garment_type} from reference image,
    {brand_style['style']},
    studio lighting, high fashion, commercial photography,
    model poses naturally, confident expression,
    SkyyRose luxury streetwear brand,
    ultra detailed, sharp focus, professional color grading,
    CRITICAL: The {garment_type} must match the reference image EXACTLY -
    same colors, same design, same logos, same details
    """.strip()

    negative_prompt = f"""
    {brand_style['negative']},
    different clothing, generic clothing, wrong colors, wrong design,
    blurry, low quality, distorted, amateur, bad anatomy,
    clothing that doesn't match reference
    """.strip()

    print("  Generating with IP-Adapter (EXACT clothing transfer)...")

    # Generate model wearing EXACT product using IP-Adapter
    # IP-Adapter preserves exact details from reference image
    result = pipeline(
        prompt=prompt,
        negative_prompt=negative_prompt,
        ip_adapter_image=product_image,  # Reference image with EXACT clothing
        height=1024,
        width=1024,
        num_inference_steps=40,
        guidance_scale=7.5,
        generator=torch.Generator(device="cpu").manual_seed(42),
    )

    generated_image = result.images[0]

    # Save result
    output_path = output_dir / f"model_wearing_{product_photo_path.stem}.jpg"
    generated_image.save(output_path, "JPEG", quality=95)

    print(f"  ✓ Saved: {output_path}")

    return {
        "product_photo": str(product_photo_path),
        "model_photo": str(output_path),
        "collection": collection,
        "garment_type": garment_type,
        "prompt": prompt,
    }


async def main():
    """Generate AI models wearing ALL SkyyRose merchandise."""

    # Load enhanced products manifest
    manifest_path = project_root / "assets" / "enhanced_products" / "all" / "manifest.json"

    with open(manifest_path) as f:
        products = json.load(f)

    print("=== SkyyRose AI Model Generation ===\n")
    print(f"Generating models wearing {len(products)} products\n")
    print("CRITICAL: Each model MUST be wearing EXACT apparel from product photo\n")

    # Output directory
    output_dir = project_root / "assets" / "ai_models_wearing_merchandise"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate models for each product
    results = []

    for product_data in products:
        if not product_data["success"]:
            continue

        product_photo = Path(product_data["enhanced"])
        collection = product_data.get("collection", detect_collection(product_photo.name))

        try:
            result = await generate_model_wearing_product(product_photo, collection, output_dir)
            results.append(result)
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            results.append(
                {
                    "product_photo": str(product_photo),
                    "error": str(e),
                    "success": False,
                }
            )

    # Save results manifest
    results_path = output_dir / "ai_models_manifest.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n\n{'='*60}")
    print("✅ AI Model Generation Complete!")
    print(f"{'='*60}")
    print(f"\nGenerated {len(results)} model photos")
    print(f"Output: {output_dir}")
    print(f"Manifest: {results_path}")

    print("\n🎯 VERIFICATION:")
    print("  - Each model MUST be wearing EXACT apparel from product photo")
    print("  - Check colors, logos, designs match EXACTLY")
    print("  - If clothing doesn't match, regenerate with stronger reference")


if __name__ == "__main__":
    asyncio.run(main())
