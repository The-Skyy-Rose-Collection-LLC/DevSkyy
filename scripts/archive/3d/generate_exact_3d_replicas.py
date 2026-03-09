#!/usr/bin/env python3
"""
Generate EXACT 3D replicas of SkyyRose products at maximum quality.

CRITICAL REQUIREMENTS:
- 100% identical to source images
- Maximum texture resolution (4096)
- PBR materials enabled
- 95%+ fidelity enforcement
- No creative alterations

Author: DevSkyy Platform Team
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_3d.generation_pipeline import (
    GenerationConfig,
    GenerationQuality,
    ModelFormat,
    ThreeDGenerationPipeline,
    ThreeDProvider,
)
from errors.production_errors import ModelFidelityError

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ProductToGenerate:
    """Product information for 3D generation."""

    collection: str  # signature, love-hurts, black-rose
    product_name: str
    image_path: Path
    output_name: str

    def __post_init__(self):
        """Validate product data."""
        if not self.image_path.exists():
            raise FileNotFoundError(f"Product image not found: {self.image_path}")


class ExactReplicaGenerator:
    """
    Generate EXACT 3D replicas of SkyyRose products.

    NO ALTERATIONS. NO CREATIVE INTERPRETATION.
    100% PHOTOREALISTIC FIDELITY REQUIRED.
    """

    def __init__(self, output_dir: str = "./generated_3d_replicas"):
        """Initialize generator with maximum quality settings."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # MAXIMUM QUALITY CONFIG - NO COMPROMISES
        self.config = GenerationConfig(
            provider=ThreeDProvider.AUTO,  # Auto-fallback for reliability
            quality=GenerationQuality.PRODUCTION,  # Highest quality
            minimum_fidelity=0.95,  # 95% minimum (ENFORCED)
            enforce_fidelity=True,  # CRITICAL: Reject low-fidelity models
            output_format=ModelFormat.GLB,  # For Threedium.io
            texture_resolution=4096,  # MAXIMUM resolution
            mesh_quality="high",
            generate_pbr=True,  # Physically-based rendering materials
            max_retries=5,  # Retry until perfect
            retry_delay_seconds=15,
        )

        self.pipeline = ThreeDGenerationPipeline()
        self.results: list[dict[str, Any]] = []

        # Validate API keys
        self._validate_environment()

    def _validate_environment(self) -> None:
        """Ensure required API keys are present."""
        tripo_key = os.getenv("TRIPO_API_KEY") or os.getenv("TRIPO3D_API_KEY")
        hf_key = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")

        if not tripo_key and not hf_key:
            raise ValueError(
                "TRIPO_API_KEY or HUGGINGFACE_API_KEY required. "
                "Get Tripo key from: https://www.tripo3d.ai/dashboard"
            )

        logger.info("✅ API keys validated")

    def discover_products(self, collection: str) -> list[ProductToGenerate]:
        """
        Discover all products in a collection.

        Args:
            collection: Collection name (signature, love-hurts, black-rose)

        Returns:
            List of products ready for generation
        """
        assets_dir = Path("assets/enhanced-images") / collection

        if not assets_dir.exists():
            logger.warning(f"Collection not found: {collection}")
            return []

        products: list[ProductToGenerate] = []

        # Find all product folders
        for product_dir in sorted(assets_dir.iterdir()):
            if not product_dir.is_dir():
                continue

            # Use transparent PNG (best for 3D) or retina JPG as fallback
            transparent_img = product_dir / f"{product_dir.name}_transparent.png"
            retina_img = product_dir / f"{product_dir.name}_retina.jpg"
            main_img = product_dir / f"{product_dir.name}_main.jpg"

            source_image = None
            if transparent_img.exists():
                source_image = transparent_img
            elif retina_img.exists():
                source_image = retina_img
            elif main_img.exists():
                source_image = main_img

            if source_image:
                products.append(
                    ProductToGenerate(
                        collection=collection,
                        product_name=product_dir.name,
                        image_path=source_image,
                        output_name=f"{collection}_{product_dir.name}",
                    )
                )
                logger.info(f"📸 Found: {product_dir.name} ({source_image.suffix})")

        return products

    async def generate_exact_replica(self, product: ProductToGenerate) -> dict[str, Any]:
        """
        Generate EXACT 3D replica of a product.

        Args:
            product: Product to generate

        Returns:
            Generation result with fidelity metrics
        """
        logger.info(f"\n{'=' * 70}")
        logger.info(f"🎯 Generating EXACT replica: {product.product_name}")
        logger.info(f"   Collection: {product.collection.upper()}")
        logger.info(f"   Source: {product.image_path.name}")
        logger.info(f"{'=' * 70}\n")

        start_time = datetime.now(UTC)

        try:
            # Generate with maximum quality settings
            result = await self.pipeline.generate_from_image(
                image_path=str(product.image_path),
                config=self.config,
            )

            end_time = datetime.now(UTC)
            duration = (end_time - start_time).total_seconds()

            # CRITICAL: Enforce 95% fidelity
            if not result.fidelity_passed:
                logger.error(
                    f"❌ REJECTED: {product.product_name} - "
                    f"Fidelity {result.fidelity_score:.1%} < 95% threshold"
                )
                raise ModelFidelityError(
                    f"Model fidelity {result.fidelity_score:.1%} below required 95%"
                )

            # Success - model is EXACT replica
            logger.info(f"✅ SUCCESS: {product.product_name}")
            logger.info(f"   Fidelity: {result.fidelity_score:.1%}")
            logger.info(
                f"   Provider: {result.provider_used.value if result.provider_used else 'unknown'}"
            )
            logger.info(f"   Time: {duration:.1f}s")
            logger.info(f"   Output: {result.model_path}\n")

            return {
                "success": True,
                "collection": product.collection,
                "product_name": product.product_name,
                "source_image": str(product.image_path),
                "model_path": result.model_path,
                "fidelity_score": result.fidelity_score,
                "provider": result.provider_used.value if result.provider_used else None,
                "generation_time_seconds": duration,
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except ModelFidelityError as e:
            logger.error(f"❌ Fidelity check failed: {e}")
            return {
                "success": False,
                "collection": product.collection,
                "product_name": product.product_name,
                "source_image": str(product.image_path),
                "error": str(e),
                "fidelity_score": result.fidelity_score if "result" in locals() else 0.0,
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            logger.exception(f"❌ Generation failed: {e}")
            return {
                "success": False,
                "collection": product.collection,
                "product_name": product.product_name,
                "source_image": str(product.image_path),
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
            }

    async def generate_collection(
        self,
        collection: str,
        max_concurrent: int = 3,
        products_limit: int | None = None,
    ) -> None:
        """
        Generate 3D replicas for entire collection.

        Args:
            collection: Collection name
            max_concurrent: Max concurrent generations (API rate limiting)
            products_limit: Optional limit on number of products (for testing)
        """
        logger.info(f"\n{'#' * 70}")
        logger.info(f"# EXACT REPLICA GENERATION: {collection.upper()} COLLECTION")
        logger.info(f"{'#' * 70}\n")

        products = self.discover_products(collection)

        if not products:
            logger.warning(f"No products found in {collection} collection")
            return

        if products_limit:
            products = products[:products_limit]
            logger.info(f"📦 Limiting to {products_limit} products for testing\n")

        logger.info(f"📦 Total products: {len(products)}\n")

        # Process with controlled concurrency (API rate limits)
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_with_semaphore(product: ProductToGenerate) -> dict[str, Any]:
            async with semaphore:
                return await self.generate_exact_replica(product)

        # Generate all products
        tasks = [generate_with_semaphore(p) for p in products]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        self.results.extend(results)

        # Summary
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful

        logger.info(f"\n{'=' * 70}")
        logger.info(f"COLLECTION SUMMARY: {collection.upper()}")
        logger.info(f"{'=' * 70}")
        logger.info(f"✅ Successful: {successful}/{len(results)}")
        logger.info(f"❌ Failed: {failed}/{len(results)}")

        if successful > 0:
            avg_fidelity = sum(r["fidelity_score"] for r in results if r["success"]) / successful
            logger.info(f"📊 Average Fidelity: {avg_fidelity:.1%}")

        logger.info(f"{'=' * 70}\n")

    def save_results(self, output_file: str = "3d_generation_results.json") -> None:
        """Save generation results to JSON file."""
        output_path = self.output_dir / output_file

        with open(output_path, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "config": {
                        "quality": self.config.quality.value,
                        "texture_resolution": self.config.texture_resolution,
                        "minimum_fidelity": self.config.minimum_fidelity,
                        "provider": self.config.provider.value,
                    },
                    "results": self.results,
                },
                f,
                indent=2,
            )

        logger.info(f"💾 Results saved to: {output_path}")


async def main():
    """Generate EXACT 3D replicas for all SkyyRose collections."""

    # Initialize generator
    generator = ExactReplicaGenerator(output_dir="./generated_3d_replicas")

    # PRIORITY: Start with Signature Collection (hero products)
    logger.info("\n" + "=" * 70)
    logger.info("🚀 SKYYROSE 3D GENERATION PIPELINE")
    logger.info("   Mode: EXACT REPLICAS - NO ALTERATIONS")
    logger.info("   Quality: MAXIMUM (4096 textures, PBR, 95% fidelity)")
    logger.info("=" * 70 + "\n")

    # Collections to process
    collections = [
        "signature",  # Priority: Hero products
        "love-hurts",  # 35 products
        "black-rose",  # 12 products
    ]

    # Process each collection
    for collection in collections:
        await generator.generate_collection(
            collection=collection,
            max_concurrent=2,  # Rate limit for API stability
            # products_limit=3,  # UNCOMMENT FOR TESTING (first 3 products only)
        )

    # Save final results
    generator.save_results()

    # Final summary
    total = len(generator.results)
    successful = sum(1 for r in generator.results if r["success"])

    logger.info("\n" + "#" * 70)
    logger.info("# FINAL SUMMARY - ALL COLLECTIONS")
    logger.info("#" * 70)
    logger.info(f"✅ Total Successful: {successful}/{total}")
    logger.info(f"❌ Total Failed: {total - successful}/{total}")

    if successful > 0:
        avg_fidelity = (
            sum(r["fidelity_score"] for r in generator.results if r["success"]) / successful
        )
        logger.info(f"📊 Overall Average Fidelity: {avg_fidelity:.1%}")

    logger.info("#" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
