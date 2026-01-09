#!/usr/bin/env python3
"""
SkyyRose 3D Model Generation using Official Tripo3D SDK

This script uses the official Tripo3D Python SDK for reliable 3D model generation
from product images. The SDK handles all API communication, retry logic, and
polling - avoiding the complexity of manual HTTP requests.

Installation:
    pip install tripo3d

Usage:
    python3 scripts/generate_3d_models_official_sdk.py

Environment Variables:
    TRIPO_API_KEY - Your Tripo3D API key (required)
"""

import asyncio
import json
import logging
import ssl
from datetime import datetime
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Try to import official SDK
try:
    from tripo3d import TaskStatus, TripoClient

    TRIPO_SDK_AVAILABLE = True
except ImportError:
    TRIPO_SDK_AVAILABLE = False
    logger.error("Tripo3D SDK not installed! Install with: pip install tripo3d")


def get_image_files(base_path: Path) -> dict[str, list[Path]]:
    """
    Discover product images organized by collection.

    Expected structure:
        assets/
        ├── BLACK_ROSE/
        │   ├── image1.jpg
        │   └── image2.png
        ├── LOVE_HURTS/
        └── SIGNATURE/
    """
    images_by_collection = {}

    if not base_path.exists():
        logger.warning(f"Assets path not found: {base_path}")
        return {}

    for collection_dir in base_path.iterdir():
        if not collection_dir.is_dir():
            continue

        collection_name = collection_dir.name.upper()
        image_files = list(collection_dir.glob("*.jpg")) + list(collection_dir.glob("*.png"))

        if image_files:
            images_by_collection[collection_name] = sorted(image_files)
            logger.info(f"Found {len(image_files)} images in {collection_name}")

    return images_by_collection


async def generate_3d_model(
    client: TripoClient,
    image_path: Path,
    output_dir: Path,
    collection: str,
    max_retries: int = 3,
) -> dict[str, Any]:
    """
    Generate a 3D model from an image using the official SDK.

    Returns:
        Dict with keys: task_id, status, model_path, error (if failed)
    """
    result = {
        "image_path": str(image_path),
        "collection": collection,
        "task_id": None,
        "status": "pending",
        "model_path": None,
        "error": None,
    }

    try:
        # Generate 3D model from image
        logger.info(f"Generating 3D model from: {image_path.name}")
        task_id = await client.image_to_model(image=str(image_path))
        result["task_id"] = task_id
        logger.info(f"Created task: {task_id}")

        # Wait for task completion with verbose logging
        task = await client.wait_for_task(task_id, verbose=True)

        if task.status == TaskStatus.SUCCESS:
            logger.info(f"Task {task_id} completed successfully!")

            # Download model files
            try:
                downloaded_files = await client.download_task_models(task, str(output_dir))

                # Find the GLB file (primary output)
                # The official SDK returns "pbr_model" key for PBR-textured GLB files
                if downloaded_files and "pbr_model" in downloaded_files:
                    model_path = downloaded_files["pbr_model"]
                    result["model_path"] = str(model_path)
                    result["status"] = "success"

                    # Log what was downloaded
                    for model_type, file_path in downloaded_files.items():
                        if file_path:
                            logger.info(f"  Downloaded {model_type}: {file_path}")
                else:
                    result["error"] = "No model file found in download results"
                    result["status"] = "failed"
                    logger.error(f"Failed to find model in downloads: {downloaded_files}")

            except Exception as e:
                result["error"] = f"Download failed: {str(e)}"
                result["status"] = "failed"
                logger.error(f"Failed to download model files: {e}")
        else:
            result["error"] = f"Task failed with status: {task.status}"
            result["status"] = "failed"
            logger.error(f"Task {task_id} failed: {task.status}")

    except Exception as e:
        result["error"] = str(e)
        result["status"] = "failed"
        logger.error(f"Generation failed for {image_path.name}: {e}")

    return result


async def batch_generate_models(
    client: TripoClient,
    images_by_collection: dict[str, list[Path]],
    output_dir: Path,
    batch_size: int = 3,
    delay_between_batches: float = 1.0,
) -> dict[str, Any]:
    """
    Generate 3D models in batches to avoid rate limiting.

    Args:
        client: TripoClient instance
        images_by_collection: Dict mapping collection names to image paths
        output_dir: Base output directory
        batch_size: Number of concurrent generations per batch
        delay_between_batches: Delay between batches in seconds

    Returns:
        Summary with success/failure counts
    """
    summary = {
        "total_images": 0,
        "successful": 0,
        "failed": 0,
        "collections": {},
        "start_time": datetime.now().isoformat(),
        "results": [],
    }

    for collection, image_paths in images_by_collection.items():
        logger.info(f"\n{'=' * 70}")
        logger.info(f"Processing {collection} collection ({len(image_paths)} images)")
        logger.info(f"{'=' * 70}")

        collection_output_dir = output_dir / collection.lower()
        collection_output_dir.mkdir(parents=True, exist_ok=True)

        collection_stats = {
            "collection": collection,
            "total": len(image_paths),
            "successful": 0,
            "failed": 0,
            "results": [],
        }

        # Process in batches
        for batch_idx in range(0, len(image_paths), batch_size):
            batch = image_paths[batch_idx : batch_idx + batch_size]
            logger.info(f"\nBatch {batch_idx // batch_size + 1}: Processing {len(batch)} images")

            # Generate models concurrently within batch
            tasks = [
                generate_3d_model(
                    client=client,
                    image_path=image_path,
                    output_dir=collection_output_dir,
                    collection=collection,
                )
                for image_path in batch
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch task exception: {result}")
                    summary["failed"] += 1
                    collection_stats["failed"] += 1
                else:
                    summary["results"].append(result)
                    collection_stats["results"].append(result)

                    if result["status"] == "success":
                        summary["successful"] += 1
                        collection_stats["successful"] += 1
                        logger.info(f"✓ {result['image_path']}")
                    else:
                        summary["failed"] += 1
                        collection_stats["failed"] += 1
                        logger.error(f"✗ {result['image_path']}: {result['error']}")

            summary["total_images"] += len(batch)

            # Wait between batches to avoid rate limiting
            if batch_idx + batch_size < len(image_paths):
                logger.info(f"Waiting {delay_between_batches}s before next batch...")
                await asyncio.sleep(delay_between_batches)

        summary["collections"][collection] = collection_stats

    summary["end_time"] = datetime.now().isoformat()

    return summary


async def main() -> None:
    """Main entry point."""
    import os

    # Check SDK availability
    if not TRIPO_SDK_AVAILABLE:
        logger.error("Cannot proceed without Tripo3D SDK")
        return

    # Check API key
    api_key = os.getenv("TRIPO_API_KEY")
    if not api_key:
        logger.error("TRIPO_API_KEY environment variable is not set!")
        logger.error("Please set it with: export TRIPO_API_KEY='tsk_your_sdk_key'")
        logger.error("Get your SDK API key from: https://www.tripo3d.ai/dashboard")
        return

    if not api_key.startswith("tsk_"):
        logger.error(f"Invalid API key format: {api_key[:10]}...")
        logger.error("SDK API keys must start with 'tsk_' (not 'tcli_')")
        logger.error("Get your SDK API key from: https://www.tripo3d.ai/dashboard")
        return

    # Setup paths
    project_root = Path.cwd()
    assets_dir = project_root / "assets" / "3d-models"
    output_base_dir = project_root / "assets" / "3d-models-generated"
    output_base_dir.mkdir(parents=True, exist_ok=True)

    # Discover images
    logger.info(f"Searching for images in: {assets_dir}")
    images_by_collection = get_image_files(assets_dir)

    if not images_by_collection:
        logger.warning(f"No images found in {assets_dir}")
        logger.info("Please ensure images are in assets/3d-models/{COLLECTION}/")
        return

    total_images = sum(len(paths) for paths in images_by_collection.values())
    logger.info(f"Found {total_images} images across {len(images_by_collection)} collections")

    # Initialize Tripo client
    try:
        logger.info("Initializing Tripo3D client...")
        # Create SSL context with verification disabled for development environments
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        async with TripoClient(api_key=api_key) as client:
            # Check balance
            balance = await client.get_balance()
            logger.info(f"Account balance: {balance.balance} (frozen: {balance.frozen})")

            # Generate models
            logger.info("\nStarting batch generation...")
            summary = await batch_generate_models(
                client=client,
                images_by_collection=images_by_collection,
                output_dir=output_base_dir,
                batch_size=3,
                delay_between_batches=1.0,
            )

            # Calculate statistics
            success_rate = (
                (summary["successful"] / summary["total_images"] * 100)
                if summary["total_images"] > 0
                else 0
            )

            # Log final summary
            logger.info(f"\n{'=' * 70}")
            logger.info("GENERATION SUMMARY")
            logger.info(f"{'=' * 70}")
            logger.info(f"Total images: {summary['total_images']}")
            logger.info(f"Successful: {summary['successful']}")
            logger.info(f"Failed: {summary['failed']}")
            logger.info(f"Success rate: {success_rate:.1f}%")

            # Save summary to JSON
            summary_path = output_base_dir / "GENERATION_SUMMARY.json"
            with open(summary_path, "w") as f:
                json.dump(summary, f, indent=2)
            logger.info(f"\nSummary saved to: {summary_path}")

            # Log per-collection stats
            logger.info("\nPer-Collection Statistics:")
            for collection_name, stats in summary["collections"].items():
                logger.info(
                    f"  {collection_name}: {stats['successful']}/{stats['total']} successful"
                )

    except Exception as e:
        logger.error(f"Failed to initialize Tripo client: {e}")
        logger.error("Make sure TRIPO_API_KEY environment variable is set")
        return


if __name__ == "__main__":
    asyncio.run(main())
