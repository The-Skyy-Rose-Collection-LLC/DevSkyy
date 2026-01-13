#!/usr/bin/env python3
"""
Generate HIGH-QUALITY 3D models for CLOTHING items using HuggingFace pipeline.

Pipeline:
1. Filter for clothing-only images (no logos, roses, random images)
2. Enhance images with HuggingFace (upscale, background removal, quality boost)
3. Generate 3D models from enhanced images using HuggingFace models

Usage:
    export HF_TOKEN="hf_..."
    python3 scripts/generate_clothing_3d_huggingface.py [--collection NAME] [--dry-run]

Examples:
    python3 scripts/generate_clothing_3d_huggingface.py                    # All collections
    python3 scripts/generate_clothing_3d_huggingface.py --collection love-hurts
    python3 scripts/generate_clothing_3d_huggingface.py --dry-run          # Preview only
"""

import argparse
import asyncio
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# CLOTHING DETECTION PATTERNS
# ============================================================================

CLOTHING_KEYWORDS = [
    # Tops
    "shirt",
    "tee",
    "t-shirt",
    "tshirt",
    "top",
    "blouse",
    "tank",
    "hoodie",
    "hooded",
    "sweatshirt",
    "sweater",
    "pullover",
    "crewneck",
    "jacket",
    "coat",
    "blazer",
    "cardigan",
    "vest",
    "crop",
    # Bottoms
    "pants",
    "jeans",
    "shorts",
    "skirt",
    "leggings",
    "joggers",
    "trousers",
    # Dresses
    "dress",
    "gown",
    "romper",
    "jumpsuit",
    # Outerwear
    "sherpa",
    "fleece",
    "parka",
    "windbreaker",
    # Accessories (wearable)
    "beanie",
    "hat",
    "cap",
    "scarf",
    "gloves",
    "pack",
    "fannie",
    "fanny",
    # Generic clothing terms
    "womens",
    "women's",
    "mens",
    "men's",
    "unisex",
    # SkyyRose specific
    "cotton candy",
    "lavender rose",
    "signature",
    "label",
    "golden",
    "smoke",
    "hearted",
]

# Patterns to EXCLUDE (not clothing)
EXCLUDE_PATTERNS = [
    r"logo",  # Any logo file
    r"skyyrosedad_",  # AI-generated rose artwork
    r"hyper-realistic.*rose",
    r"close-up.*rose",
    r"wide-angle.*rose",
    r"bleeding.*rose",
    r"glowing.*rose",
    r"^IMG_\d+\.HEIC$",  # iPhone raw photos
    r"^[A-F0-9]{8}-[A-F0-9]{4}",  # UUID filenames
    r"\.html$",
    r"\.zip$",
    r"\.mov$",
    r"\.mp4$",
]

# Collections config
COLLECTIONS = {
    "signature": {
        "source_dir": "assets/3d-models/signature",
        "output_dir": "assets/3d-models-generated/signature",
        "subdirs": ["_Signature Collection_"],
    },
    "black-rose": {
        "source_dir": "assets/3d-models/black-rose",
        "output_dir": "assets/3d-models-generated/black-rose",
        "subdirs": ["_BLACK Rose Collection_"],
    },
    "love-hurts": {
        "source_dir": "assets/3d-models/love-hurts",
        "output_dir": "assets/3d-models-generated/love-hurts",
        "subdirs": ["_Love Hurts Collection_"],
    },
}


def is_clothing_image(filename: str) -> tuple[bool, str]:
    """Check if a file is a clothing product image."""
    filename_lower = filename.lower()

    # Check exclusions first
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, filename_lower):
            return False, f"excluded by pattern: {pattern}"

    # Must be an image file
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    ext = Path(filename).suffix.lower()
    if ext not in valid_extensions:
        return False, f"not an image file: {ext}"

    # Check for clothing keywords
    for keyword in CLOTHING_KEYWORDS:
        if keyword.lower() in filename_lower:
            return True, f"matched keyword: {keyword}"

    return False, "no clothing keyword found"


def find_clothing_images(collection_name: str) -> list[dict]:
    """Find all clothing images in a collection (deduplicated by filename)."""
    config = COLLECTIONS.get(collection_name)
    if not config:
        print(f"Unknown collection: {collection_name}")
        return []

    project_root = Path(__file__).parent.parent
    source_base = project_root / config["source_dir"]

    # Use dict to deduplicate by stem (filename without extension)
    clothing_images_map = {}

    # Search subdirs FIRST (prefer these), then main dir as fallback
    search_dirs = []
    for subdir in config.get("subdirs", []):
        search_dirs.append(source_base / subdir)
    search_dirs.append(source_base)  # Main dir last

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        for file_path in search_dir.iterdir():
            if not file_path.is_file():
                continue

            is_clothing, reason = is_clothing_image(file_path.name)
            if is_clothing:
                # Deduplicate by stem - prefer first found (subdir)
                stem = file_path.stem
                if stem not in clothing_images_map:
                    clothing_images_map[stem] = {
                        "path": str(file_path),
                        "name": stem,
                        "collection": collection_name,
                        "reason": reason,
                    }

    return list(clothing_images_map.values())


async def enhance_and_generate_3d(
    image_info: dict,
    output_dir: Path,
    dry_run: bool = False,
) -> dict:
    """Enhance image and generate 3D model."""
    from orchestration.huggingface_asset_enhancer import (
        EnhancerConfig,
        HF3DQuality,
        HuggingFaceAssetEnhancerWithTextures,
        PreprocessingMode,
    )

    image_path = image_info["path"]
    product_name = image_info["name"].replace("_", " ").strip()
    collection = image_info["collection"].upper().replace("-", "_")

    print(f"\n{'=' * 60}")
    print(f"Processing: {product_name}")
    print(f"Collection: {collection}")
    print(f"Source: {image_path}")
    print(f"{'=' * 60}")

    if dry_run:
        print("[DRY RUN] Would enhance and generate 3D model")
        return {
            "status": "dry_run",
            "product_name": product_name,
            "image_path": image_path,
        }

    # Configure enhancer for high quality
    config = EnhancerConfig(
        hf_api_token=os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN"),
        quality=HF3DQuality.PRODUCTION,
        preprocessing_mode=PreprocessingMode.ADVANCED,
        remove_background=True,
        target_resolution=1024,
        output_dir=str(output_dir),
        generate_usdz=True,
        generate_thumbnails=True,
        batch_concurrency=1,  # One at a time for stability
        timeout_seconds=300,
    )

    enhancer = HuggingFaceAssetEnhancerWithTextures(config)

    try:
        # Step 1: Enhance image first, then generate 3D
        print("Step 1: Enhancing source image with HuggingFace...")
        result = await enhancer.enhance_asset_with_textures(
            image_path=image_path,
            product_name=product_name,
            collection=collection,
            enhance_source_texture=True,  # KEY: Enhance image FIRST
        )

        if result.status == "completed" and result.glb_path:
            print(f"SUCCESS: {result.glb_path}")
            print(
                f"  Quality Score: {result.best_model.quality_score if result.best_model else 'N/A'}"
            )
            print(f"  Brand Score: {result.brand_score}")
            print(f"  Duration: {result.duration_seconds:.1f}s")

            return {
                "status": "success",
                "product_name": product_name,
                "glb_path": result.glb_path,
                "usdz_path": result.usdz_path,
                "quality_score": result.best_model.quality_score if result.best_model else None,
                "brand_score": result.brand_score,
                "duration": result.duration_seconds,
            }
        else:
            print(f"FAILED: {result.errors}")
            return {
                "status": "failed",
                "product_name": product_name,
                "errors": result.errors,
            }

    except Exception as e:
        print(f"ERROR: {e}")
        return {
            "status": "error",
            "product_name": product_name,
            "error": str(e),
        }

    finally:
        await enhancer.close()


async def process_collection(collection_name: str, dry_run: bool = False) -> dict:
    """Process all clothing items in a collection."""
    print(f"\n{'#' * 60}")
    print(f"# Processing Collection: {collection_name.upper()}")
    print(f"{'#' * 60}")

    # Find clothing images
    clothing_images = find_clothing_images(collection_name)
    print(f"\nFound {len(clothing_images)} clothing images")

    if not clothing_images:
        return {"collection": collection_name, "processed": 0, "results": []}

    # Show what we found
    print("\nClothing items to process:")
    for i, img in enumerate(clothing_images, 1):
        print(f"  {i}. {img['name']} ({img['reason']})")

    # Setup output directory
    project_root = Path(__file__).parent.parent
    config = COLLECTIONS[collection_name]
    output_dir = project_root / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process each image
    results = []
    for img in clothing_images:
        result = await enhance_and_generate_3d(img, output_dir, dry_run)
        results.append(result)

        # Small delay between items
        if not dry_run:
            await asyncio.sleep(2)

    # Summary
    successful = sum(1 for r in results if r.get("status") == "success")
    failed = sum(1 for r in results if r.get("status") in ("failed", "error"))

    print(f"\n{'=' * 60}")
    print(f"Collection {collection_name.upper()} Summary:")
    print(f"  Total: {len(results)}")
    print(f"  Success: {successful}")
    print(f"  Failed: {failed}")
    print(f"{'=' * 60}")

    return {
        "collection": collection_name,
        "processed": len(results),
        "successful": successful,
        "failed": failed,
        "results": results,
    }


async def main():
    parser = argparse.ArgumentParser(
        description="Generate 3D models for clothing using HuggingFace pipeline"
    )
    parser.add_argument(
        "--collection",
        choices=list(COLLECTIONS.keys()),
        help="Specific collection to process (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be processed without generating",
    )

    args = parser.parse_args()

    # Check for API token
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN")
    if not token:
        print("ERROR: HF_TOKEN or HUGGINGFACE_API_TOKEN not set")
        print("Run: export HF_TOKEN='hf_...'")
        sys.exit(1)

    print(f"HuggingFace Token: {'*' * 20}{token[-4:]}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'GENERATE'}")
    print(f"Timestamp: {datetime.now().isoformat()}")

    # Determine collections to process
    collections = [args.collection] if args.collection else list(COLLECTIONS)

    # Process each collection
    all_results = []
    for collection in collections:
        result = await process_collection(collection, args.dry_run)
        all_results.append(result)

    # Final summary
    print(f"\n{'#' * 60}")
    print("# FINAL SUMMARY")
    print(f"{'#' * 60}")

    total_processed = sum(r["processed"] for r in all_results)
    total_successful = sum(r.get("successful", 0) for r in all_results)
    total_failed = sum(r.get("failed", 0) for r in all_results)

    print(f"Total Processed: {total_processed}")
    print(f"Total Successful: {total_successful}")
    print(f"Total Failed: {total_failed}")

    # Save results
    if not args.dry_run:
        results_path = (
            Path(__file__).parent.parent / "generated_assets" / "huggingface_3d_results.json"
        )
        results_path.parent.mkdir(exist_ok=True)

        import json

        with open(results_path, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "collections": all_results,
                    "summary": {
                        "total_processed": total_processed,
                        "total_successful": total_successful,
                        "total_failed": total_failed,
                    },
                },
                f,
                indent=2,
                default=str,
            )

        print(f"\nResults saved to: {results_path}")


if __name__ == "__main__":
    asyncio.run(main())
