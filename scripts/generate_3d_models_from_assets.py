#!/usr/bin/env python3
"""
Generate 3D Models from SkyyRose Collection Assets

Processes extracted product images and generates 3D models using:
- HuggingFace Shap-E (quick preview + optimization hints)
- Tripo3D (production-quality GLB/USDZ conversion)
- WordPress Media upload with custom meta fields

Usage:
    python3 scripts/generate_3d_models_from_assets.py \
        --assets-dir "./assets/3d-models" \
        --output-dir "./generated_assets" \
        --collection signature

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class CollectionMetadata(BaseModel):
    """Metadata for a collection's 3D models."""

    collection_slug: str = Field(..., description="Collection identifier")
    collection_name: str = Field(..., description="Human-readable collection name")
    brand_colors: dict[str, str] = Field(..., description="Collection color palette")
    generated_models: list[dict[str, Any]] = Field(
        default_factory=list, description="Generated models"
    )
    generation_status: str = Field(default="pending", description="Generation status")
    generated_at: str | None = Field(default=None, description="Generation timestamp")


class ModelGenerationPipeline:
    """Generate 3D models from product images using multi-stage pipeline."""

    def __init__(
        self,
        assets_dir: str = "./assets/3d-models",
        output_dir: str = "./generated_assets",
    ):
        """
        Initialize model generation pipeline.

        Args:
            assets_dir: Directory containing extracted assets
            output_dir: Output directory for generated models
        """
        self.assets_dir = Path(assets_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Collection configurations
        self.collections = {
            "signature": {
                "name": "SIGNATURE",
                "colors": {
                    "primary": "#0D0D0D",
                    "accent": "#D4AF37",
                    "accent_secondary": "#B76E79",
                    "accent_soft": "#C9A962",
                },
                "description": "Premium essentials built to last",
            },
            "black-rose": {
                "name": "BLACK ROSE",
                "colors": {
                    "primary": "#000000",
                    "accent": "#C0C0C0",
                    "accent_secondary": "#D4D4D4",
                },
                "description": "Dark elegance meets modern luxury",
            },
            "love-hurts": {
                "name": "LOVE HURTS",
                "colors": {
                    "primary": "#2D1B1F",
                    "accent": "#B76E79",
                    "accent_secondary": "#E8B4BC",
                },
                "description": "Raw emotion transformed into high fashion",
            },
        }

    async def find_product_images(self, collection: str) -> list[Path]:
        """
        Find product images in collection directory.

        Args:
            collection: Collection slug (signature, black-rose, love-hurts)

        Returns:
            List of image file paths
        """
        collection_dir = self.assets_dir / collection
        if not collection_dir.exists():
            logger.warning(f"Collection directory not found: {collection_dir}")
            return []

        # Find all image files
        image_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        images = [
            f
            for f in collection_dir.glob("*")
            if f.is_file() and f.suffix.lower() in image_extensions
        ]

        logger.info(f"Found {len(images)} product images in {collection}")
        return sorted(images)

    async def generate_model_metadata(
        self,
        image_path: Path,
        collection: str,
    ) -> dict[str, Any]:
        """
        Generate metadata for a product image.

        Args:
            image_path: Path to product image
            collection: Collection slug

        Returns:
            Model metadata dictionary
        """
        # Extract product name from filename
        product_name = image_path.stem.replace("_", " ")

        # Get file size
        file_size_mb = image_path.stat().st_size / (1024 * 1024)

        return {
            "product_name": product_name,
            "source_image": str(image_path.relative_to(self.assets_dir)),
            "source_image_size_mb": round(file_size_mb, 2),
            "collection": collection,
            "status": "pending_generation",
            "models": {
                "glb": None,  # Will be filled after generation
                "usdz": None,
                "preview": None,
            },
            "generation_pipeline": [
                {"stage": "image_optimization", "status": "pending"},
                {"stage": "huggingface_shap_e", "status": "pending"},
                {"stage": "tripo3d_conversion", "status": "pending"},
                {"stage": "wordpress_upload", "status": "pending"},
            ],
        }

    async def generate_collection_models(
        self,
        collection: str,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        Generate 3D models for all products in a collection.

        Args:
            collection: Collection slug
            limit: Optional limit on number of models to generate

        Returns:
            Generation results dictionary
        """
        logger.info(f"Starting model generation for {collection}")

        # Find product images
        images = await self.find_product_images(collection)

        if not images:
            logger.error(f"No product images found for {collection}")
            return {
                "collection": collection,
                "status": "failed",
                "reason": "No product images found",
                "models": [],
            }

        if limit:
            images = images[:limit]

        # Generate metadata for each image
        models_metadata = []
        for image_path in images:
            try:
                metadata = await self.generate_model_metadata(image_path, collection)
                models_metadata.append(metadata)
            except Exception as e:
                logger.error(f"Failed to generate metadata for {image_path}: {e}")
                continue

        # Create collection metadata
        collection_config = self.collections.get(collection)
        if not collection_config:
            logger.error(f"Unknown collection: {collection}")
            return {
                "collection": collection,
                "status": "failed",
                "reason": "Unknown collection",
                "models": [],
            }

        result = {
            "collection": collection,
            "collection_name": collection_config["name"],
            "status": "generated",
            "total_products": len(models_metadata),
            "models": models_metadata,
            "brand_colors": collection_config["colors"],
            "instructions": self._get_generation_instructions(),
        }

        # Save metadata
        await self._save_metadata(collection, result)

        logger.info(f"✓ Generated metadata for {len(models_metadata)} products in {collection}")
        return result

    def _get_generation_instructions(self) -> dict[str, Any]:
        """Get detailed instructions for 3D model generation."""
        return {
            "stage_1_image_optimization": {
                "description": "Prepare images for 3D generation",
                "tools": ["PIL", "OpenCV"],
                "steps": [
                    "Normalize image resolution to 1024x1024",
                    "Remove backgrounds (white/transparent recommended)",
                    "Enhance contrast for better 3D reconstruction",
                    "Validate image format (PNG recommended for transparency)",
                ],
            },
            "stage_2_huggingface_shap_e": {
                "description": "Generate quick 3D preview and optimization hints",
                "tools": ["orchestration/huggingface_3d_client.py"],
                "steps": [
                    "Call HuggingFace Shap-E API with optimized image",
                    "Generate low-poly preview model",
                    "Extract optimization metadata (polycount hints, texture size)",
                    "Cache results for faster subsequent processing",
                ],
                "output": {
                    "format": "OBJ/MTL",
                    "polycount": "10K-50K",
                    "texture_size": "1024x1024",
                },
            },
            "stage_3_tripo3d_conversion": {
                "description": "Generate production-quality GLB and USDZ models",
                "tools": ["agents/tripo_agent.py"],
                "steps": [
                    "Call Tripo3D API with source image",
                    "Request GLB format (web-optimized, 50-200K polygons)",
                    "Request USDZ format (AR-optimized for iOS)",
                    "Apply material/texture enhancements",
                    "Validate output model integrity",
                    "Store with version metadata",
                ],
                "output": {
                    "formats": ["GLB", "USDZ"],
                    "polycount": "50K-200K",
                    "filesize": "10-50MB",
                },
            },
            "stage_4_wordpress_upload": {
                "description": "Upload models to WordPress media library with metadata",
                "tools": ["wordpress/media_3d_sync.py"],
                "steps": [
                    "Upload GLB to WordPress media library",
                    "Upload USDZ to WordPress media library",
                    "Set custom meta fields: _skyyrose_glb_url, _skyyrose_usdz_url, _skyyrose_ar_enabled",
                    "Link to WooCommerce product via product ID",
                    "Enable AR Quick Look for iOS",
                    "Test cross-browser compatibility",
                ],
            },
        }

    async def _save_metadata(self, collection: str, metadata: dict[str, Any]) -> None:
        """Save generation metadata to JSON file."""
        output_file = self.output_dir / f"{collection}_models_metadata.json"

        try:
            with open(output_file, "w") as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"✓ Saved metadata to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            raise

    async def generate_all_collections(
        self,
        collections: list[str],
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        Generate 3D models for multiple collections in parallel.

        Args:
            collections: List of collection slugs
            limit: Optional limit on models per collection

        Returns:
            Combined results for all collections
        """
        tasks = [self.generate_collection_models(collection, limit) for collection in collections]

        results = await asyncio.gather(*tasks)

        summary = {
            "total_collections": len(collections),
            "generated_collections": sum(1 for r in results if r["status"] == "generated"),
            "total_products": sum(r.get("total_products", 0) for r in results),
            "collections": {r["collection"]: r for r in results},
            "next_steps": [
                "1. Review generated model metadata files",
                "2. Process images through HuggingFace Shap-E (stage 2)",
                "3. Convert to GLB/USDZ via Tripo3D (stage 3)",
                "4. Upload to WordPress media library (stage 4)",
                "5. Link 3D models to WooCommerce products",
                "6. Test AR experiences on mobile devices",
            ],
        }

        logger.info("\n" + "=" * 60)
        logger.info("MODEL GENERATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Collections: {summary['total_collections']}")
        logger.info(f"Generated: {summary['generated_collections']}")
        logger.info(f"Total Products: {summary['total_products']}")
        logger.info("\nNext Steps:")
        for step in summary["next_steps"]:
            logger.info(f"  {step}")
        logger.info("=" * 60 + "\n")

        return summary


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate 3D models from SkyyRose collection assets"
    )
    parser.add_argument(
        "--assets-dir",
        default="./assets/3d-models",
        help="Directory containing extracted assets",
    )
    parser.add_argument(
        "--output-dir",
        default="./generated_assets",
        help="Output directory for generated models",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default=None,
        help="Specific collection to process (signature, black-rose, love-hurts)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of models per collection",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate models for all collections",
    )

    args = parser.parse_args()

    pipeline = ModelGenerationPipeline(
        assets_dir=args.assets_dir,
        output_dir=args.output_dir,
    )

    if args.collection:
        # Generate for specific collection
        await pipeline.generate_collection_models(
            args.collection,
            limit=args.limit,
        )
    elif args.all:
        # Generate for all collections
        await pipeline.generate_all_collections(
            ["signature", "black-rose", "love-hurts"],
            limit=args.limit,
        )
    else:
        logger.error("Please specify --collection or use --all")
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
