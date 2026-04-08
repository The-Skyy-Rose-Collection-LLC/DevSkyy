#!/usr/bin/env python3
"""
Image Generation Demo - Replicate & Stability AI
=================================================

Demonstrates capabilities for SkyyRose product generation.

Usage:
    python scripts/demo_image_generation.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm.providers.replicate import ReplicateClient
from llm.providers.stability import StabilityClient


async def demo_replicate():
    """Demonstrate Replicate capabilities for fashion/products."""
    print("\n" + "=" * 60)
    print("🔮 REPLICATE CAPABILITIES FOR SKYYROSE")
    print("=" * 60)

    client = ReplicateClient()

    if not client.api_token:
        print("⚠️  REPLICATE_API_TOKEN not set - showing capabilities only")
        print("\nCapabilities available:")
        print("""
    1. IMAGE GENERATION (SDXL, Flux)
       ─────────────────────────────
       • Generate product renders from text descriptions
       • Style: photorealistic, studio lighting, white background
       • Resolution: 1024x1024 (SDXL optimal)

       Example prompt:
       "skyyrose signature collection lavender beanie, luxury fashion,
        professional product photography, studio lighting, white background,
        high detail, 8k quality"

    2. IMAGE UPSCALING (Real-ESRGAN)
       ─────────────────────────────
       • 4x upscale for print-ready images
       • Face enhancement for model shots
       • Preserve fine details in fabric textures

    3. BACKGROUND REMOVAL (rembg)
       ─────────────────────────────
       • Clean product cutouts for catalogs
       • Transparent PNG output
       • Perfect for WooCommerce products

    4. CONTROLNET (Pose/Canny)
       ─────────────────────────────
       • Generate products in specific poses
       • Use edge maps for consistent silhouettes
       • Create matching product line images

       Use case: Generate hoodie on model in same pose as reference

    5. IMAGE CAPTIONING (BLIP-2)
       ─────────────────────────────
       • Auto-generate captions for training data
       • Create SEO descriptions for products
       • Build training datasets automatically

    6. CUSTOM LORA INFERENCE
       ─────────────────────────────
       • Run YOUR trained SkyyRose LoRA model
       • Generate exact product replicas
       • Maintain brand consistency

       Example:
       await client.run_lora(
           "damBruh/skyyrose-lora:latest",
           prompt="skyyrose signature collection, lavender rose beanie"
       )

    7. VIDEO GENERATION (Stable Video Diffusion)
       ─────────────────────────────
       • Create rotating product videos
       • Marketing content from static images
       • Social media ready output
""")
        return

    print("\n✅ API Key configured - ready to generate!")
    print("\nTo generate images, use:")
    print("""
    from llm.providers.replicate import ReplicateClient

    client = ReplicateClient()

    # Generate product image
    urls = await client.generate_image(
        "skyyrose signature collection hoodie, lavender rose embroidery, "
        "luxury fashion, studio lighting, white background",
        model="sdxl",
        num_outputs=4
    )

    # Upscale for print
    url = await client.upscale_image("product.jpg", scale=4)

    # Remove background
    url = await client.remove_background("product.jpg")

    # Generate from pose reference
    urls = await client.run_controlnet(
        "skyyrose hoodie, professional model, studio",
        control_image="pose_reference.jpg",
        control_type="pose"
    )
    """)


async def demo_stability():
    """Demonstrate Stability AI capabilities for fashion/products."""
    print("\n" + "=" * 60)
    print("🎨 STABILITY AI CAPABILITIES FOR SKYYROSE")
    print("=" * 60)

    client = StabilityClient()

    if not client.api_key:
        print("⚠️  STABILITY_API_KEY not set - showing capabilities only")
        print("\nCapabilities available:")
        print("""
    1. TEXT-TO-IMAGE (SDXL, SD3, Core, Ultra)
       ──────────────────────────────────────
       • Highest quality product renders
       • Multiple style presets optimized for products
       • Style presets: photographic, cinematic, digital-art

       Example:
       images = await client.generate(
           "skyyrose black rose collection sherpa jacket, luxury urban fashion, "
           "professional product photo, studio lighting",
           style_preset="photographic"
       )

    2. IMAGE-TO-IMAGE TRANSFORMATION
       ──────────────────────────────────────
       • Create color variations of existing products
       • Apply style transfers while preserving structure
       • Generate seasonal variations

       Use case: Turn black hoodie into rose gold version

       images = await client.image_to_image(
           "hoodie_black.jpg",
           prompt="same hoodie in rose gold metallic fabric",
           strength=0.6
       )

    3. INPAINTING (Background Replacement)
       ──────────────────────────────────────
       • Replace backgrounds professionally
       • Add lifestyle context to product shots
       • Create consistent catalog backgrounds

       Example:
       images = await client.inpaint(
           "product_messy_bg.jpg",
           "background_mask.png",
           prompt="clean white studio background, soft shadow"
       )

    4. OUTPAINTING (Image Extension)
       ──────────────────────────────────────
       • Extend cropped product images
       • Show full outfit from crop
       • Create banner/hero images

       extended = await client.outpaint(
           "hoodie_crop.jpg",
           prompt="full body shot, model wearing hoodie, studio",
           down=512  # Extend downward
       )

    5. CREATIVE UPSCALING
       ──────────────────────────────────────
       • 4x upscale with AI enhancement
       • Add realistic details to textures
       • Print-ready resolution

       upscaled = await client.upscale(
           "product_small.jpg",
           prompt="luxury fabric texture, fine stitching details"
       )

    6. BACKGROUND REMOVAL
       ──────────────────────────────────────
       • Clean product cutouts
       • Transparent PNG output
       • Edge-aware masking

    7. SEARCH & REPLACE
       ──────────────────────────────────────
       • Find and replace objects in images
       • Change colors, patterns, or elements
       • Create product variations

       modified = await client.search_and_replace(
           "hoodie_black.jpg",
           search_prompt="black hoodie",
           prompt="lavender purple hoodie with rose embroidery"
       )
""")
        return

    # Check balance if API key is set
    try:
        balance = await client.get_balance()
        print(f"\n✅ API Key configured - Balance: {balance} credits")
    except Exception as e:
        print(f"\n✅ API Key configured (balance check failed: {e})")

    print("\nTo generate images, use:")
    print("""
    from llm.providers.stability import StabilityClient

    client = StabilityClient()

    # Generate with style preset
    images = await client.generate(
        "skyyrose love hurts collection windbreaker, urban luxury fashion, "
        "model wearing jacket, studio lighting, professional photo",
        style_preset="photographic"
    )

    # Save output
    for i, img_bytes in enumerate(images):
        with open(f"output_{i}.png", "wb") as f:
            f.write(img_bytes)
    """)


async def compare_providers():
    """Compare Replicate vs Stability AI for different use cases."""
    print("\n" + "=" * 60)
    print("📊 PROVIDER COMPARISON FOR SKYYROSE USE CASES")
    print("=" * 60)
    print("""
    ┌─────────────────────────┬──────────────────┬──────────────────┐
    │ USE CASE                │ REPLICATE        │ STABILITY AI     │
    ├─────────────────────────┼──────────────────┼──────────────────┤
    │ Product Generation      │ ✅ SDXL, Flux    │ ✅ SDXL, SD3     │
    │ Custom LoRA Inference   │ ✅ BEST          │ ❌ No support    │
    │ Background Removal      │ ✅ rembg         │ ✅ Native        │
    │ Upscaling              │ ✅ Real-ESRGAN   │ ✅ Creative      │
    │ Pose-Guided Generation │ ✅ ControlNet    │ ❌ Limited       │
    │ Inpainting             │ ⚠️ Basic         │ ✅ BEST          │
    │ Outpainting            │ ❌ No            │ ✅ BEST          │
    │ Color Variations       │ ⚠️ img2img       │ ✅ Search/Replace│
    │ Image Captioning       │ ✅ BLIP-2        │ ❌ No            │
    │ Video Generation       │ ✅ SVD           │ ❌ No            │
    │ API Simplicity         │ ✅ Simple        │ ✅ Simple        │
    │ Pricing                │ Pay per run      │ Credit based     │
    └─────────────────────────┴──────────────────┴──────────────────┘

    RECOMMENDATIONS FOR SKYYROSE:

    🔮 USE REPLICATE FOR:
       • Running your trained LoRA models (damBruh/skyyrose-lora)
       • Pose-guided product shots (ControlNet)
       • Auto-captioning training images (BLIP-2)
       • Creating product videos (SVD)
       • Fast background removal (rembg)

    🎨 USE STABILITY AI FOR:
       • Highest quality base generation (SD3 Ultra)
       • Creating color/style variations (Search & Replace)
       • Professional background replacement (Inpainting)
       • Extending cropped images (Outpainting)
       • Print-ready upscaling

    💡 COMBINED WORKFLOW:
       1. Generate base with Stability (highest quality)
       2. Create variations with Stability Search/Replace
       3. Run through YOUR LoRA on Replicate for brand consistency
       4. Upscale final with Stability Creative Upscaler
       5. Generate product video with Replicate SVD
""")


async def main():
    """Run all demos."""
    print("\n" + "🌹" * 30)
    print("  SKYYROSE IMAGE GENERATION CAPABILITIES DEMO")
    print("🌹" * 30)

    await demo_replicate()
    await demo_stability()
    await compare_providers()

    print("\n" + "=" * 60)
    print("🚀 QUICK START")
    print("=" * 60)
    print("""
    # Set your API keys in .env.hf:
    REPLICATE_API_TOKEN=r8_xxxxx
    STABILITY_API_KEY=sk-xxxxx

    # Generate a product image:
    python -c "
    import asyncio
    from llm.providers.replicate import ReplicateClient

    async def gen():
        client = ReplicateClient()
        urls = await client.generate_image(
            'skyyrose signature collection hoodie, lavender rose, luxury fashion',
            model='sdxl'
        )
        print('Generated:', urls)

    asyncio.run(gen())
    "
    """)


if __name__ == "__main__":
    asyncio.run(main())
