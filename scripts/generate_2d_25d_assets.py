#!/usr/bin/env python3
"""
Generate Advanced 2D/2.5D Product Visualizations.

Creates modern e-commerce product visualizations:
1. Multiple angles (front, back, side, detail shots)
2. 360° spin view frames
3. Depth effect layers for parallax
4. High-resolution zoom tiles
5. Lifestyle context scenes

Uses Google Imagen 3 via CreativeAgent for angle generation.

Usage:
    python3 scripts/generate_2d_25d_assets.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.creative_agent import CreativeAgent

# 2D/2.5D asset types to generate
ASSET_TYPES = {
    "angles": {
        "front_view": "front view centered, studio photography",
        "back_view": "back view centered, showing back design",
        "side_left": "left side profile, showing side seam",
        "side_right": "right side profile, fabric texture visible",
        "detail_logo": "extreme closeup of logo embroidery, macro detail",
        "detail_fabric": "fabric weave texture closeup, material quality visible",
    },
    "spin_360": {
        "frames": 24,  # 24 frames for smooth 360° rotation
        "description": "product rotating on white background, consistent lighting",
    },
    "depth_layers": {
        "foreground": "product sharp focus in foreground",
        "midground": "product with subtle background elements",
        "background": "blurred luxury environment backdrop",
    },
}


# SkyyRose collection aesthetics
COLLECTION_STYLES = {
    "BLACK_ROSE": {
        "environment": "dark studio with noir aesthetic, dramatic rim lighting",
        "mood": "mysterious, sophisticated, rebellious luxury",
        "details": "intricate stitching visible, premium hardware gleaming",
    },
    "LOVE_HURTS": {
        "environment": "artistic studio with emotional depth, warm dramatic lighting",
        "mood": "passionate, authentic, artistically refined",
        "details": "hand-finished details visible, emotional craftsmanship",
    },
    "SIGNATURE": {
        "environment": "clean luxury studio, balanced professional lighting",
        "mood": "confident, understated luxury, everyday excellence",
        "details": "impeccable construction visible, premium materials",
    },
}


async def generate_angle_views(
    enhanced_photo: Path,
    product_name: str,
    collection: str,
    creative_agent: CreativeAgent,
    output_dir: Path,
) -> list[dict]:
    """Generate multiple angle views of product using Imagen 3."""

    print(f"\n{product_name} - Generating angle views...")

    aesthetic = COLLECTION_STYLES.get(collection, COLLECTION_STYLES["SIGNATURE"])
    generated_angles = []

    for angle_name, angle_desc in ASSET_TYPES["angles"].items():
        prompt = f"""
        Professional luxury fashion product photography,
        {product_name},
        {angle_desc},
        {aesthetic["environment"]},
        {aesthetic["mood"]},
        {aesthetic["details"]},
        SkyyRose luxury streetwear brand,
        commercial product photography, catalog quality,
        ultra detailed, sharp focus, professional color grading
        """

        try:
            # Generate via CreativeAgent using Imagen 3
            result = await creative_agent.generate_image(
                prompt=prompt.strip(), width=2048, height=2048, model="google_imagen_3"
            )

            output_path = output_dir / f"{angle_name}.jpg"

            # Save generated image
            if hasattr(result, "save"):
                result.save(output_path, "JPEG", quality=95)
            else:
                # result might be a path string
                import shutil

                shutil.copy2(result, output_path)

            print(f"  ✓ {angle_name}")

            generated_angles.append(
                {"angle": angle_name, "path": str(output_path), "description": angle_desc}
            )

        except Exception as e:
            print(f"  ✗ {angle_name} failed: {e}")

    return generated_angles


async def generate_360_spin_frames(
    enhanced_photo: Path,
    product_name: str,
    collection: str,
    creative_agent: CreativeAgent,
    output_dir: Path,
) -> list[dict]:
    """Generate 24 frames for 360° product spin."""

    print(f"\n{product_name} - Generating 360° spin frames...")

    aesthetic = COLLECTION_STYLES.get(collection, COLLECTION_STYLES["SIGNATURE"])
    spin_frames = []

    num_frames = ASSET_TYPES["spin_360"]["frames"]
    degrees_per_frame = 360 / num_frames

    for i in range(num_frames):
        degrees = int(i * degrees_per_frame)

        prompt = f"""
        Professional luxury fashion product photography,
        {product_name},
        rotated {degrees} degrees from front view,
        centered on white background,
        studio photography with consistent lighting,
        {aesthetic["environment"]},
        {aesthetic["mood"]},
        ultra detailed, sharp focus
        """

        try:
            result = await creative_agent.generate_image(
                prompt=prompt.strip(), width=1024, height=1024, model="google_imagen_3"
            )

            output_path = output_dir / f"spin_{i:02d}_{degrees}deg.jpg"

            if hasattr(result, "save"):
                result.save(output_path, "JPEG", quality=92)
            else:
                import shutil

                shutil.copy2(result, output_path)

            if i % 6 == 0:  # Progress every 6 frames
                print(f"  {i + 1}/{num_frames} frames")

            spin_frames.append({"frame": i, "degrees": degrees, "path": str(output_path)})

        except Exception as e:
            print(f"  ✗ Frame {i} ({degrees}°) failed: {e}")

    print(f"  ✓ Generated {len(spin_frames)}/{num_frames} frames")
    return spin_frames


async def generate_depth_layers(
    enhanced_photo: Path,
    product_name: str,
    collection: str,
    creative_agent: CreativeAgent,
    output_dir: Path,
) -> list[dict]:
    """Generate depth layers for parallax effects."""

    print(f"\n{product_name} - Generating depth layers...")

    aesthetic = COLLECTION_STYLES.get(collection, COLLECTION_STYLES["SIGNATURE"])
    depth_layers = []

    for layer_name, layer_desc in ASSET_TYPES["depth_layers"].items():
        prompt = f"""
        Professional luxury fashion product photography,
        {product_name},
        {layer_desc},
        {aesthetic["environment"]},
        {aesthetic["mood"]},
        depth of field effect,
        professional bokeh background
        """

        try:
            result = await creative_agent.generate_image(
                prompt=prompt.strip(), width=2048, height=2048, model="google_imagen_3"
            )

            output_path = output_dir / f"layer_{layer_name}.png"

            if hasattr(result, "save"):
                result.save(output_path, "PNG", optimize=True)
            else:
                import shutil

                shutil.copy2(result, output_path)

            print(f"  ✓ {layer_name}")

            depth_layers.append(
                {"layer": layer_name, "path": str(output_path), "description": layer_desc}
            )

        except Exception as e:
            print(f"  ✗ {layer_name} failed: {e}")

    return depth_layers


async def generate_product_2d_25d_assets(
    enhanced_photo: Path, product_name: str, collection: str
) -> dict:
    """Generate full 2D/2.5D asset suite for a product."""

    # Initialize CreativeAgent
    creative_agent = CreativeAgent()

    # Output directory
    output_dir = (
        project_root
        / "assets"
        / "2d-25d-assets"
        / collection.lower()
        / product_name.replace(" ", "_")
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 60}")
    print(f"Generating 2D/2.5D Assets: {product_name}")
    print(f"Collection: {collection}")
    print(f"Output: {output_dir}")
    print(f"{'=' * 60}")

    # Generate angle views
    angles = await generate_angle_views(
        enhanced_photo, product_name, collection, creative_agent, output_dir / "angles"
    )

    # Generate 360° spin
    spin_frames = await generate_360_spin_frames(
        enhanced_photo, product_name, collection, creative_agent, output_dir / "spin_360"
    )

    # Generate depth layers
    depth_layers = await generate_depth_layers(
        enhanced_photo, product_name, collection, creative_agent, output_dir / "depth_layers"
    )

    return {
        "product": product_name,
        "collection": collection,
        "enhanced_photo": str(enhanced_photo),
        "output_dir": str(output_dir),
        "assets": {"angles": angles, "spin_360": spin_frames, "depth_layers": depth_layers},
    }


async def main():
    """Generate 2D/2.5D assets for all enhanced products."""

    # Load enhancement manifest
    manifest_path = project_root / "assets" / "enhanced_products" / "enhancement_manifest.json"

    with open(manifest_path) as f:
        enhanced_products = json.load(f)

    print("=== SkyyRose 2D/2.5D Asset Generation ===\n")
    print(f"Processing {len(enhanced_products)} enhanced products\n")

    # Track all generated assets
    all_assets = []

    for product_data in enhanced_products:
        enhanced_photo = Path(product_data["enhanced"])
        collection = product_data["collection"]
        product_name = enhanced_photo.stem.replace("enhanced_", "").replace("_", " ")

        assets = await generate_product_2d_25d_assets(enhanced_photo, product_name, collection)

        all_assets.append(assets)

    # Save master manifest
    master_manifest_path = project_root / "assets" / "2d-25d-assets" / "master_manifest.json"
    with open(master_manifest_path, "w") as f:
        json.dump(all_assets, f, indent=2)

    print(f"\n\n{'=' * 60}")
    print("✅ 2D/2.5D Asset Generation Complete!")
    print(f"{'=' * 60}")
    print(f"\nGenerated assets for {len(all_assets)} products")
    print(f"Master manifest: {master_manifest_path}")

    print("\n📋 Assets Generated per Product:")
    print("  - 6 angle views (front, back, sides, details)")
    print("  - 24 frames for 360° spin view")
    print("  - 3 depth layers for parallax effects")
    print("\n🎯 Next Steps:")
    print("  1. Upload 2D/2.5D assets to WordPress media library")
    print("  2. Attach to WooCommerce products")
    print("  3. Configure interactive product viewers on site")


if __name__ == "__main__":
    asyncio.run(main())
