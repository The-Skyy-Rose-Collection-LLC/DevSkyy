#!/usr/bin/env python3
"""
Direct 3D generation using Tripo3D API.

EXACT REPLICAS ONLY - No alterations.
Maximum quality: 4096 textures, PBR materials.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

import asyncio
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.tripo_agent import ModelFormat, TripoAssetAgent, TripoConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def generate_exact_replica(
    image_path: Path,
    product_name: str,
    collection: str,
    output_dir: Path,
) -> dict:
    """Generate EXACT 3D replica from product image."""

    logger.info(f"\n{'=' * 70}")
    logger.info(f"🎯 Generating: {product_name}")
    logger.info(f"   Collection: {collection.upper()}")
    logger.info(f"   Source: {image_path.name}")
    logger.info(f"{'=' * 70}\n")

    # Maximum quality configuration
    config = TripoConfig(
        texture_resolution=4096,  # MAXIMUM
        texture_quality="high",
        pbr_enabled=True,
        output_dir=str(output_dir),
    )

    # Initialize Tripo agent
    agent = TripoAssetAgent(config=config)

    try:
        # Generate with product-specific prompt
        prompt = f"""
SkyyRose {collection.replace("-", " ").title()} Collection product.
Luxury streetwear clothing item.
EXACT replica of the provided image.
High-quality materials and construction.
Preserve all design details, colors, and proportions exactly.
"""

        # Execute generation
        result = await agent.generate_3d_from_image(
            image_path=str(image_path),
            prompt=prompt.strip(),
            model_format=ModelFormat.GLB,  # For Threedium.io
        )

        if result.success and result.model_path:
            logger.info(f"✅ SUCCESS: {product_name}")
            logger.info(f"   Output: {result.model_path}")
            logger.info("   Format: GLB")
            logger.info("   Ready for Threedium.io\n")

            return {
                "success": True,
                "product_name": product_name,
                "collection": collection,
                "source_image": str(image_path),
                "model_path": result.model_path,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        else:
            errors = result.errors if hasattr(result, "errors") else ["Unknown error"]
            logger.error(f"❌ FAILED: {product_name}")
            logger.error(f"   Errors: {', '.join(errors)}\n")

            return {
                "success": False,
                "product_name": product_name,
                "collection": collection,
                "source_image": str(image_path),
                "errors": errors,
                "timestamp": datetime.now(UTC).isoformat(),
            }

    except Exception as e:
        logger.exception(f"❌ Exception: {e}")
        return {
            "success": False,
            "product_name": product_name,
            "collection": collection,
            "source_image": str(image_path),
            "errors": [str(e)],
            "timestamp": datetime.now(UTC).isoformat(),
        }


async def main():
    """Generate 3D models for Signature collection (test with 3 products)."""

    logger.info("\n" + "#" * 70)
    logger.info("# SKYYROSE 3D GENERATION - DIRECT TRIPO3D")
    logger.info("# Quality: MAXIMUM (4096 textures, PBR materials)")
    logger.info("# Mode: EXACT REPLICAS - NO ALTERATIONS")
    logger.info("#" * 70 + "\n")

    # Output directory
    output_dir = Path("./generated_3d_models")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Discover Signature collection products
    signature_dir = Path("assets/enhanced-images/signature")

    products_to_generate = []
    for product_dir in sorted(signature_dir.iterdir())[:3]:  # TEST: First 3
        if not product_dir.is_dir():
            continue

        # Use transparent PNG (best for 3D)
        transparent_img = product_dir / f"{product_dir.name}_transparent.png"
        retina_img = product_dir / f"{product_dir.name}_retina.jpg"

        source_image = transparent_img if transparent_img.exists() else retina_img

        if source_image and source_image.exists():
            products_to_generate.append(
                {
                    "image_path": source_image,
                    "product_name": product_dir.name,
                    "collection": "signature",
                }
            )

    logger.info(f"📦 Found {len(products_to_generate)} products\n")

    # Generate models
    results = []
    for product in products_to_generate:
        result = await generate_exact_replica(
            image_path=product["image_path"],
            product_name=product["product_name"],
            collection=product["collection"],
            output_dir=output_dir,
        )
        results.append(result)

        # Rate limiting (Tripo API limits)
        await asyncio.sleep(2)

    # Summary
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful

    logger.info("\n" + "=" * 70)
    logger.info("GENERATION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"✅ Successful: {successful}/{len(results)}")
    logger.info(f"❌ Failed: {failed}/{len(results)}")
    logger.info("=" * 70 + "\n")

    # Save results
    results_file = output_dir / "generation_results.json"
    with open(results_file, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "total": len(results),
                "successful": successful,
                "failed": failed,
                "results": results,
            },
            f,
            indent=2,
        )

    logger.info(f"💾 Results saved to: {results_file}\n")


if __name__ == "__main__":
    asyncio.run(main())
