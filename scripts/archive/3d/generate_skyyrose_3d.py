#!/usr/bin/env python3
"""
Generate EXACT 3D replicas of SkyyRose products at MAXIMUM quality.

CRITICAL: 100% identical to source images - NO alterations.

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

from agents.tripo_agent import TripoAssetAgent, TripoConfig
from core.runtime.tool_registry import ToolCallContext

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def generate_product_3d(
    agent: TripoAssetAgent,
    image_path: Path,
    product_name: str,
    collection: str,
) -> dict:
    """Generate EXACT 3D replica."""

    logger.info(f"\n{'=' * 70}")
    logger.info(f"🎯 {product_name}")
    logger.info(f"   Collection: {collection.upper()}")
    logger.info(f"   Source: {image_path.name}")
    logger.info(f"{'=' * 70}\n")

    try:
        # Execute via agent.run() with correct action dict
        result = await agent.run(
            request={
                "action": "generate_from_image",
                "image_path": str(image_path),
                "product_name": product_name,
                "collection": collection,
                "quality": "high",  # Maximum quality
            },
            context=ToolCallContext(
                request_id=f"3d-gen-{product_name}",
                permissions={"media", "ai"},
            ),
        )

        if result.success:
            model_path = result.outputs.get("model_path")
            logger.info("✅ SUCCESS")
            logger.info(f"   Output: {model_path}")
            logger.info("   Format: GLB\n")

            return {
                "success": True,
                "product_name": product_name,
                "collection": collection,
                "source_image": str(image_path),
                "model_path": model_path,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        else:
            logger.error("❌ FAILED")
            logger.error(f"   Errors: {result.errors}\n")

            return {
                "success": False,
                "product_name": product_name,
                "collection": collection,
                "source_image": str(image_path),
                "errors": result.errors,
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
    """Generate 3D models for SkyyRose products."""

    logger.info("\n" + "#" * 70)
    logger.info("# SKYYROSE 3D GENERATION")
    logger.info("# Mode: EXACT REPLICAS - NO ALTERATIONS")
    logger.info("# Quality: MAXIMUM (4096 textures, PBR materials)")
    logger.info("#" * 70 + "\n")

    # Configure for maximum quality
    config = TripoConfig(
        texture_resolution=4096,  # MAXIMUM
        texture_quality="high",
        pbr_enabled=True,
        output_dir="./generated_3d_models",
    )

    # Initialize agent
    agent = TripoAssetAgent(config=config)

    # Find Signature collection products
    signature_dir = Path("assets/enhanced-images/signature")

    products = []
    for product_dir in sorted(signature_dir.iterdir())[:3]:  # TEST: 3 products
        if not product_dir.is_dir():
            continue

        # Use transparent PNG (best for 3D)
        img_path = product_dir / f"{product_dir.name}_transparent.png"
        if not img_path.exists():
            img_path = product_dir / f"{product_dir.name}_retina.jpg"

        if img_path.exists():
            products.append(
                {
                    "image_path": img_path,
                    "product_name": product_dir.name,
                    "collection": "signature",
                }
            )

    logger.info(f"📦 Found {len(products)} products\n")

    # Generate models
    results = []
    for product in products:
        result = await generate_product_3d(
            agent=agent,
            image_path=product["image_path"],
            product_name=product["product_name"],
            collection=product["collection"],
        )
        results.append(result)

        # Rate limiting
        await asyncio.sleep(3)

    # Summary
    successful = sum(1 for r in results if r["success"])

    logger.info("\n" + "=" * 70)
    logger.info("GENERATION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"✅ Successful: {successful}/{len(results)}")
    logger.info(f"❌ Failed: {len(results) - successful}/{len(results)}")
    logger.info("=" * 70 + "\n")

    # Save results
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results_file = output_dir / "generation_results.json"

    with open(results_file, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "total": len(results),
                "successful": successful,
                "results": results,
            },
            f,
            indent=2,
        )

    logger.info(f"💾 Results: {results_file}\n")


if __name__ == "__main__":
    asyncio.run(main())
