#!/usr/bin/env python3
"""
Asset Pipeline CLI Runner
=========================

Command-line interface for running the product asset generation pipeline.

Usage:
    python scripts/run_asset_pipeline.py \
        --product-id "12345" \
        --title "SkyyRose Signature Hoodie" \
        --category "apparel" \
        --collection "SIGNATURE" \
        --garment-type "hoodie"

Author: DevSkyy Platform Team
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.asset_pipeline import ProductAssetPipeline


async def run_pipeline(
    product_id: str,
    title: str,
    description: str,
    category: str,
    collection: str,
    garment_type: str,
    images: list[str] | None = None,
    wp_product_id: int | None = None,
) -> dict:
    """Run the asset generation pipeline."""
    pipeline = ProductAssetPipeline()

    try:
        result = await pipeline.process_product(
            product_id=product_id,
            title=title,
            description=description,
            images=images or [],
            category=category,
            collection=collection,
            garment_type=garment_type,
            wp_product_id=wp_product_id,
        )
        return result.model_dump()
    finally:
        await pipeline.close()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run the DevSkyy asset generation pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--product-id",
        required=True,
        help="Unique product identifier",
    )
    parser.add_argument(
        "--title",
        required=True,
        help="Product title",
    )
    parser.add_argument(
        "--description",
        default="",
        help="Product description",
    )
    parser.add_argument(
        "--category",
        choices=["apparel", "accessory", "footwear"],
        default="apparel",
        help="Product category",
    )
    parser.add_argument(
        "--collection",
        choices=["BLACK_ROSE", "LOVE_HURTS", "SIGNATURE"],
        default="SIGNATURE",
        help="SkyyRose collection",
    )
    parser.add_argument(
        "--garment-type",
        choices=["hoodie", "tee", "shirt", "jacket", "pants", "dress"],
        default="tee",
        help="Garment type (for apparel)",
    )
    parser.add_argument(
        "--images",
        nargs="*",
        default=[],
        help="Product image paths",
    )
    parser.add_argument(
        "--wp-product-id",
        type=int,
        default=None,
        help="WordPress/WooCommerce product ID",
    )
    parser.add_argument(
        "--output",
        choices=["json", "summary"],
        default="json",
        help="Output format",
    )

    args = parser.parse_args()

    print(f"Starting asset pipeline for: {args.title} ({args.product_id})")
    print(f"Category: {args.category}, Collection: {args.collection}")

    try:
        result = asyncio.run(
            run_pipeline(
                product_id=args.product_id,
                title=args.title,
                description=args.description,
                category=args.category,
                collection=args.collection,
                garment_type=args.garment_type,
                images=args.images,
                wp_product_id=args.wp_product_id,
            )
        )

        if args.output == "json":
            print(json.dumps(result, indent=2))
        else:
            print(f"\n{'='*50}")
            print(f"Pipeline Result: {result['status'].upper()}")
            print(f"Duration: {result['duration_seconds']:.2f}s")
            print(f"3D Assets: {len(result['assets_3d'])}")
            print(f"Try-On Assets: {len(result['assets_tryon'])}")
            print(f"WordPress Uploads: {len(result['assets_wordpress'])}")
            if result['errors']:
                print(f"Errors: {len(result['errors'])}")
                for err in result['errors']:
                    print(f"  - {err['stage']}: {err['error']}")
            print(f"{'='*50}")

        return 0 if result['status'] == 'success' else 1

    except Exception as e:
        print(f"Pipeline failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

