#!/usr/bin/env python3
"""
Generate 3D Models for Premier SkyyRose Collection Items.

This script generates 3D models for 9 premier items across 3 collections:
- Signature Collection: Cotton Candy Tee, Hoodie, Signature Shorts
- Black Rose Collection: Best 3 items from available images
- Love Hurts Collection: Best 3 items from available images

Generation procedure:
1. Check API keys are available
2. Use fallback chain: TRELLIS (HuggingFace) -> Meshy -> Tripo3D
3. Wait 2 seconds between API calls (rate limiting)
4. Validate each model (file exists, size > 50KB)
5. Save to assets/3d-models-generated/{collection}/{sku}.glb
"""

from __future__ import annotations

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
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv  # noqa: E402

# Load environment variables from .env file
load_dotenv(project_root / ".env")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("premier_3d_generator")


@dataclass
class GenerationItem:
    """Item to generate 3D model for."""

    collection: str
    name: str
    image_path: Path
    output_path: Path
    sku: str = ""

    def __post_init__(self):
        if not self.sku:
            # Generate SKU from name
            safe_name = "".join(c if c.isalnum() else "_" for c in self.name)
            self.sku = f"{self.collection.upper()}_{safe_name}"[:50]


@dataclass
class GenerationResult:
    """Result of 3D model generation."""

    item: GenerationItem
    success: bool
    provider: str = ""
    model_path: str = ""
    file_size_kb: float = 0.0
    generation_time_seconds: float = 0.0
    error: str = ""


async def check_api_keys() -> dict[str, bool]:
    """Check which API keys are available."""
    keys = {
        "MESHY_API_KEY": bool(os.getenv("MESHY_API_KEY")),
        "TRIPO_API_KEY": bool(os.getenv("TRIPO_API_KEY") or os.getenv("TRIPO3D_API_KEY")),
        "HUGGINGFACE_TOKEN": bool(
            os.getenv("HUGGINGFACE_TOKEN")
            or os.getenv("HUGGINGFACE_API_TOKEN")
            or os.getenv("HF_TOKEN")
        ),
    }
    logger.info("API keys status:")
    for key, available in keys.items():
        logger.info(f"  {key}: {'AVAILABLE' if available else 'NOT SET'}")
    return keys


def discover_collection_images(base_dir: Path) -> dict[str, list[Path]]:
    """Discover all images in collection directories."""
    collections = {}

    # Signature Collection
    sig_dir = base_dir / "signature"
    if sig_dir.exists():
        images = []
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]:
            images.extend(sig_dir.glob(ext))
        collections["signature"] = sorted(images, key=lambda p: p.stat().st_size, reverse=True)

    # Black Rose Collection
    br_dir = base_dir / "black-rose"
    if br_dir.exists():
        images = []
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]:
            images.extend(br_dir.glob(ext))
        collections["black-rose"] = sorted(images, key=lambda p: p.stat().st_size, reverse=True)

    # Love Hurts Collection
    lh_dir = base_dir / "love-hurts"
    if lh_dir.exists():
        images = []
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]:
            images.extend(lh_dir.glob(ext))
        collections["love-hurts"] = sorted(images, key=lambda p: p.stat().st_size, reverse=True)

    return collections


def select_premier_items(
    collections: dict[str, list[Path]], output_base: Path
) -> list[GenerationItem]:
    """Select premier items for each collection."""
    items = []

    # Signature Collection - specific items
    if "signature" in collections:
        sig_items = {
            "_Signature Collection_ Cotton Candy Tee.jpg": "cotton_candy_tee",
            "_Signature Collection_ Hoodie.jpg": "signature_hoodie",
            "_Signature Collection_ Signature Shorts.jpg": "signature_shorts",
        }
        sig_dir = output_base.parent / "3d-models" / "signature"

        for filename, sku in sig_items.items():
            image_path = sig_dir / filename
            if image_path.exists():
                items.append(
                    GenerationItem(
                        collection="signature",
                        name=filename.replace("_Signature Collection_ ", "").replace(".jpg", ""),
                        image_path=image_path,
                        output_path=output_base / "signature" / f"{sku}.glb",
                        sku=sku,
                    )
                )
            else:
                logger.warning(f"Signature item not found: {image_path}")

    # Black Rose Collection - best 3 product images (clothing items)
    if "black-rose" in collections:
        br_dir = output_base.parent / "3d-models" / "black-rose"
        br_candidates = [
            ("BLACK Rose Sherpa.jpeg", "black_rose_sherpa"),
            ("Womens Black Rose Hooded Dress-1.jpeg", "black_rose_hooded_dress"),
            ("The BLACK Rose Sherpa.jpg", "black_rose_sherpa_alt"),
            ("PhotoRoom_010_20231221_160237-1.jpeg", "black_rose_item_1"),
            ("PhotoRoom_003_20230616_170635.jpeg", "black_rose_item_2"),
        ]

        count = 0
        for filename, sku in br_candidates:
            if count >= 3:
                break
            image_path = br_dir / filename
            if image_path.exists():
                items.append(
                    GenerationItem(
                        collection="black-rose",
                        name=filename.replace(".jpeg", "").replace(".jpg", ""),
                        image_path=image_path,
                        output_path=output_base / "black-rose" / f"{sku}.glb",
                        sku=sku,
                    )
                )
                count += 1

    # Love Hurts Collection - best 3 product images
    if "love-hurts" in collections:
        lh_dir = output_base.parent / "3d-models" / "love-hurts"
        lh_candidates = [
            (
                "_Love Hurts Collection_ Sincerely Hearted Joggers (Black).jpg",
                "love_hurts_joggers_black",
            ),
            (
                "_Love Hurts Collection_ Sincerely Hearted Joggers (White).jpg",
                "love_hurts_joggers_white",
            ),
            ("_Love Hurts Collection_ _Fannie_ Pack.jpg", "love_hurts_fannie_pack"),
            ("Men windbreaker jacket (1).png", "love_hurts_windbreaker"),
            ("mens Windbreaker shorts.png", "love_hurts_shorts"),
        ]

        count = 0
        for filename, sku in lh_candidates:
            if count >= 3:
                break
            image_path = lh_dir / filename
            if image_path.exists():
                items.append(
                    GenerationItem(
                        collection="love-hurts",
                        name=filename.replace(".jpg", "").replace(".png", ""),
                        image_path=image_path,
                        output_path=output_base / "love-hurts" / f"{sku}.glb",
                        sku=sku,
                    )
                )
                count += 1

    return items


async def generate_with_meshy(image_path: Path, output_path: Path) -> tuple[bool, str]:
    """Generate 3D model using Meshy API."""
    try:
        from ai_3d.providers.meshy import MeshyArtStyle, MeshyClient

        output_path.parent.mkdir(parents=True, exist_ok=True)

        async with MeshyClient() as client:
            result = await client.generate_from_image(
                image_path=str(image_path),
                output_dir=str(output_path.parent),
                output_format="glb",
                art_style=MeshyArtStyle.REALISTIC,
                target_polycount=30000,
            )

            if result and Path(result).exists():
                # Rename to our output path
                if Path(result) != output_path:
                    import shutil

                    shutil.move(result, output_path)
                return True, ""
            return False, "No model generated"

    except Exception as e:
        return False, str(e)


async def generate_with_huggingface(image_path: Path, output_path: Path) -> tuple[bool, str]:
    """Generate 3D model using HuggingFace (TRELLIS/TripoSR)."""
    try:
        from ai_3d.providers.huggingface import HuggingFace3DClient

        output_path.parent.mkdir(parents=True, exist_ok=True)

        async with HuggingFace3DClient() as client:
            # Try TRELLIS first (default)
            result = await client.generate_from_image(
                image_path=str(image_path),
                output_dir=str(output_path.parent),
                output_format="glb",
                model="trellis",
            )

            if result and Path(result).exists():
                if Path(result) != output_path:
                    import shutil

                    shutil.move(result, output_path)
                return True, ""

            # Fallback to TripoSR
            result = await client.generate_from_image(
                image_path=str(image_path),
                output_dir=str(output_path.parent),
                output_format="glb",
                model="triposr",
            )

            if result and Path(result).exists():
                if Path(result) != output_path:
                    import shutil

                    shutil.move(result, output_path)
                return True, ""

            return False, "No model generated"

    except Exception as e:
        return False, str(e)


async def generate_with_tripo(image_path: Path, output_path: Path) -> tuple[bool, str]:
    """Generate 3D model using Tripo3D."""
    try:
        # Check for TRIPO_API_KEY or TRIPO3D_API_KEY
        api_key = os.getenv("TRIPO_API_KEY") or os.getenv("TRIPO3D_API_KEY")
        if not api_key:
            return False, "TRIPO_API_KEY not set"

        # Temporarily set TRIPO_API_KEY if TRIPO3D_API_KEY is used
        os.environ["TRIPO_API_KEY"] = api_key

        from ai_3d.providers.tripo import TripoClient

        output_path.parent.mkdir(parents=True, exist_ok=True)

        client = TripoClient()
        try:
            result = await client.generate_from_image(
                image_path=str(image_path),
                output_dir=str(output_path.parent),
                output_format="glb",
            )

            if result and Path(result).exists():
                if Path(result) != output_path:
                    import shutil

                    shutil.move(result, output_path)
                return True, ""
            return False, "No model generated"
        finally:
            await client.close()

    except Exception as e:
        return False, str(e)


async def generate_single_model(item: GenerationItem, delay: float = 2.0) -> GenerationResult:
    """Generate a single 3D model with fallback chain."""
    logger.info(f"Generating: {item.name} ({item.collection})")
    start_time = datetime.now(UTC)

    result = GenerationResult(
        item=item,
        success=False,
    )

    # Fallback chain: HuggingFace (TRELLIS) -> Meshy -> Tripo
    providers = [
        ("HuggingFace/TRELLIS", generate_with_huggingface),
        ("Meshy", generate_with_meshy),
        ("Tripo3D", generate_with_tripo),
    ]

    for provider_name, generator in providers:
        logger.info(f"  Trying {provider_name}...")
        try:
            success, error = await generator(item.image_path, item.output_path)

            if success and item.output_path.exists():
                file_size = item.output_path.stat().st_size / 1024  # KB

                if file_size >= 50:  # Validate: > 50KB
                    result.success = True
                    result.provider = provider_name
                    result.model_path = str(item.output_path)
                    result.file_size_kb = file_size
                    end_time = datetime.now(UTC)
                    result.generation_time_seconds = (end_time - start_time).total_seconds()
                    logger.info(
                        f"  SUCCESS with {provider_name}: {file_size:.1f}KB in {result.generation_time_seconds:.1f}s"
                    )
                    break
                else:
                    logger.warning(f"  {provider_name} generated file too small: {file_size:.1f}KB")
                    item.output_path.unlink(missing_ok=True)
            else:
                logger.warning(f"  {provider_name} failed: {error}")

        except Exception as e:
            logger.error(f"  {provider_name} error: {e}")
            result.error = str(e)

        # Rate limiting delay between providers
        await asyncio.sleep(delay)

    if not result.success:
        result.error = "All providers failed"
        logger.error(f"  FAILED: {item.name} - {result.error}")

    return result


async def generate_all_models(items: list[GenerationItem]) -> list[GenerationResult]:
    """Generate all models sequentially with rate limiting."""
    results = []

    for i, item in enumerate(items):
        logger.info(f"\n[{i + 1}/{len(items)}] Processing {item.name}")
        result = await generate_single_model(item, delay=2.0)
        results.append(result)

        # Additional delay between items
        if i < len(items) - 1:
            logger.info("  Waiting 2s before next item...")
            await asyncio.sleep(2.0)

    return results


def generate_report(results: list[GenerationResult], output_path: Path) -> dict[str, Any]:
    """Generate a summary report of the generation."""
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "total_items": len(results),
        "successful": sum(1 for r in results if r.success),
        "failed": sum(1 for r in results if not r.success),
        "by_collection": {},
        "by_provider": {},
        "items": [],
    }

    for r in results:
        # By collection
        if r.item.collection not in report["by_collection"]:
            report["by_collection"][r.item.collection] = {"success": 0, "failed": 0}
        if r.success:
            report["by_collection"][r.item.collection]["success"] += 1
        else:
            report["by_collection"][r.item.collection]["failed"] += 1

        # By provider
        if r.success and r.provider:
            report["by_provider"][r.provider] = report["by_provider"].get(r.provider, 0) + 1

        # Item details
        report["items"].append(
            {
                "name": r.item.name,
                "collection": r.item.collection,
                "sku": r.item.sku,
                "success": r.success,
                "provider": r.provider,
                "model_path": r.model_path,
                "file_size_kb": round(r.file_size_kb, 2),
                "generation_time_seconds": round(r.generation_time_seconds, 2),
                "error": r.error,
            }
        )

    # Save report
    report_path = output_path / "GENERATION_REPORT.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"\nReport saved to: {report_path}")
    return report


async def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("Premier 3D Model Generation")
    logger.info("=" * 60)

    # Check API keys
    keys = await check_api_keys()
    if not any(keys.values()):
        logger.error("No API keys available! Set at least one of:")
        logger.error("  MESHY_API_KEY, TRIPO_API_KEY, or HUGGINGFACE_TOKEN")
        return 1

    # Set up paths
    project_root = Path(__file__).parent.parent
    assets_dir = project_root / "assets" / "3d-models"
    output_dir = project_root / "assets" / "3d-models-generated"

    # Create output directories
    for collection in ["signature", "black-rose", "love-hurts"]:
        (output_dir / collection).mkdir(parents=True, exist_ok=True)

    # Discover images
    logger.info("\nDiscovering collection images...")
    collections = discover_collection_images(assets_dir)
    for name, images in collections.items():
        logger.info(f"  {name}: {len(images)} images")

    # Select premier items
    logger.info("\nSelecting premier items...")
    items = select_premier_items(collections, output_dir)
    logger.info(f"Selected {len(items)} items for generation:")
    for item in items:
        logger.info(f"  - [{item.collection}] {item.name}")

    if not items:
        logger.error("No items found for generation!")
        return 1

    # Generate models
    logger.info("\nStarting 3D model generation...")
    results = await generate_all_models(items)

    # Generate report
    report = generate_report(results, output_dir)

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("GENERATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total: {report['total_items']}")
    logger.info(f"Successful: {report['successful']}")
    logger.info(f"Failed: {report['failed']}")
    logger.info("\nBy Collection:")
    for collection, stats in report["by_collection"].items():
        logger.info(f"  {collection}: {stats['success']} success, {stats['failed']} failed")
    logger.info("\nBy Provider:")
    for provider, count in report["by_provider"].items():
        logger.info(f"  {provider}: {count} models")

    # List generated models
    logger.info("\nGenerated Models:")
    for item in report["items"]:
        status = "OK" if item["success"] else "FAILED"
        if item["success"]:
            logger.info(
                f"  [{status}] {item['name']}: {item['file_size_kb']}KB via {item['provider']}"
            )
        else:
            logger.info(f"  [{status}] {item['name']}: {item['error']}")

    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
