#!/usr/bin/env python3
"""
Meshy AI 3D Model Generator with Async Support.

Production-ready 3D generation script with:
- Proper async/await patterns (no deadlocks)
- Rate limiting: asyncio.Semaphore(5), 2s delay between calls
- Exponential backoff on 429 errors
- Robust response parsing

Supports both:
- Image-to-3D: Generate new 3D models from product images
- Retexture: Improve existing 3D models with better textures

Usage:
    python scripts/meshy_3d_generator.py generate --collection signature
    python scripts/meshy_3d_generator.py generate --collection signature --limit 5
    python scripts/meshy_3d_generator.py retexture --collection signature
    python scripts/meshy_3d_generator.py status <task_id>
    python scripts/meshy_3d_generator.py balance
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


CLOTHING_KEYWORDS = [
    "hoodie",
    "jacket",
    "shorts",
    "jogger",
    "tee",
    "shirt",
    "sweater",
    "pants",
    "dress",
    "beanie",
    "crewneck",
    "sherpa",
    "windbreaker",
    "crop",
    "collection",
    "lavender",
    "mint",
    "golden",
    "smoke",
    "photoroom",
]


def is_clothing_item(filename: str) -> bool:
    """Check if filename represents a clothing item."""
    name_lower = filename.lower()
    return any(keyword in name_lower for keyword in CLOTHING_KEYWORDS)


def find_clothing_images(collection_path: Path) -> list[Path]:
    """Find all clothing images in a collection directory."""
    extensions = [".jpg", ".jpeg", ".png", ".webp"]
    clothing_items = []

    for ext in extensions:
        for img_path in collection_path.glob(f"*{ext}"):
            if is_clothing_item(img_path.name):
                clothing_items.append(img_path)
        for img_path in collection_path.glob(f"*{ext.upper()}"):
            if is_clothing_item(img_path.name):
                clothing_items.append(img_path)

    return sorted(set(clothing_items), key=lambda x: x.name)


async def generate_models(args: argparse.Namespace) -> None:
    """Generate 3D models from images using async Meshy client."""
    from ai_3d.providers.meshy import MeshyArtStyle, MeshyClient

    assets_dir = project_root / "assets" / "3d-models"
    output_dir = project_root / "assets" / "3d-models-generated" / "meshy"

    print("=" * 60)
    print("MESHY AI - IMAGE TO 3D GENERATION (ASYNC)")
    print("=" * 60)

    # Find collections
    collections: dict[str, list[Path]] = {}
    if args.collection:
        coll_path = assets_dir / args.collection
        if coll_path.exists():
            items = find_clothing_images(coll_path)
            if items:
                collections[args.collection] = items
        else:
            print(f"Collection not found: {coll_path}")
            return
    else:
        for coll_dir in assets_dir.iterdir():
            if coll_dir.is_dir() and not coll_dir.name.startswith("."):
                items = find_clothing_images(coll_dir)
                if items:
                    collections[coll_dir.name] = items

    if not collections:
        print("No clothing items found!")
        return

    total = sum(len(items) for items in collections.values())
    print(f"\nFound {total} clothing items")

    for name, items in collections.items():
        print(f"  {name}: {len(items)} items")

    if args.dry_run:
        print("\n[DRY RUN] No tasks will be created.")
        return

    # Initialize Meshy client
    try:
        client = MeshyClient()
    except Exception as e:
        print(f"Failed to initialize Meshy client: {e}")
        print("Make sure MESHY_API_KEY is set in your environment.")
        return

    print("\n" + "=" * 60)
    print("GENERATING 3D MODELS")
    print("=" * 60)

    results: dict[str, dict] = {}

    async with client:
        for coll_name, items in collections.items():
            print(f"\n[{coll_name.upper()}]")

            coll_output_dir = output_dir / coll_name
            coll_output_dir.mkdir(parents=True, exist_ok=True)

            results[coll_name] = {"successful": 0, "failed": 0, "models": []}

            items_to_process = items[: args.limit] if args.limit > 0 else items

            for img_path in items_to_process:
                print(f"  Processing: {img_path.name}...", end=" ", flush=True)

                try:
                    model_path = await client.generate_from_image(
                        image_path=str(img_path),
                        output_dir=str(coll_output_dir),
                        output_format="glb",
                        art_style=MeshyArtStyle.REALISTIC,
                        target_polycount=30000,
                    )

                    if model_path and Path(model_path).exists():
                        size_mb = Path(model_path).stat().st_size / (1024 * 1024)
                        print(f"OK ({size_mb:.1f} MB)")
                        results[coll_name]["successful"] += 1
                        results[coll_name]["models"].append(model_path)
                    else:
                        print("FAILED (no output)")
                        results[coll_name]["failed"] += 1

                except Exception as e:
                    print(f"FAILED: {e}")
                    results[coll_name]["failed"] += 1
                    logger.exception(f"Error processing {img_path.name}")

    # Print summary
    print("\n" + "=" * 60)
    print("GENERATION SUMMARY")
    print("=" * 60)

    total_success = sum(r["successful"] for r in results.values())
    total_failed = sum(r["failed"] for r in results.values())

    for coll_name, stats in results.items():
        print(f"  {coll_name}: {stats['successful']} succeeded, {stats['failed']} failed")

    print(f"\nTotal: {total_success} succeeded, {total_failed} failed")

    # Save results
    results_path = output_dir / "generation_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved: {results_path}")


async def retexture_models(args: argparse.Namespace) -> None:
    """Retexture existing 3D models using async Meshy client."""
    from ai_3d.providers.meshy import MeshyClient

    models_dir = project_root / "assets" / "3d-models-generated"
    output_dir = project_root / "assets" / "3d-models-retextured" / "meshy"

    print("=" * 60)
    print("MESHY AI - RETEXTURE MODELS (ASYNC)")
    print("=" * 60)

    # Find GLB files
    collections: dict[str, list[Path]] = {}
    if args.collection:
        coll_dir = models_dir / args.collection
        if coll_dir.exists():
            glbs = [g for g in coll_dir.glob("*.glb") if not g.stem.endswith("_pbr")]
            if glbs:
                collections[args.collection] = glbs
    else:
        for coll_dir in models_dir.iterdir():
            if coll_dir.is_dir():
                glbs = [g for g in coll_dir.glob("*.glb") if not g.stem.endswith("_pbr")]
                if glbs:
                    collections[coll_dir.name] = glbs

    if not collections:
        print("No GLB models found!")
        return

    total = sum(len(glbs) for glbs in collections.values())
    print(f"\nFound {total} GLB models to retexture")

    if args.dry_run:
        print("\n[DRY RUN] No tasks will be created.")
        return

    try:
        client = MeshyClient()
    except Exception as e:
        print(f"Failed to initialize Meshy client: {e}")
        return

    print("\n" + "=" * 60)
    print("RETEXTURING MODELS")
    print("=" * 60)

    async with client:
        for coll_name, glbs in collections.items():
            print(f"\n[{coll_name.upper()}]")

            coll_output_dir = output_dir / coll_name
            coll_output_dir.mkdir(parents=True, exist_ok=True)

            glbs_to_process = glbs[: args.limit] if args.limit > 0 else glbs

            for glb_path in glbs_to_process:
                print(f"  Retexturing: {glb_path.name}...", end=" ", flush=True)

                try:
                    result_path = await client.retexture_model(
                        model_path=str(glb_path),
                        output_dir=str(coll_output_dir),
                        enable_pbr=True,
                    )

                    if result_path and Path(result_path).exists():
                        size_mb = Path(result_path).stat().st_size / (1024 * 1024)
                        print(f"OK ({size_mb:.1f} MB)")
                    else:
                        print("FAILED")

                except Exception as e:
                    print(f"FAILED: {e}")

    print("\n" + "=" * 60)
    print("RETEXTURE COMPLETE")
    print("=" * 60)


async def check_status(args: argparse.Namespace) -> None:
    """Check status of a Meshy task."""
    from ai_3d.providers.meshy import MeshyClient

    task_id = args.task_id
    task_type = args.type or "image-to-3d"

    print(f"Checking task: {task_id}")

    try:
        client = MeshyClient()
        async with client:
            task = await client.get_task_status(task_id, task_type)
            if task:
                print(f"Status: {task.status.value}")
                print(f"Progress: {task.progress}%")
                if task.model_urls:
                    print(f"Model URLs: {json.dumps(task.model_urls, indent=2)}")
                if task.error_message:
                    print(f"Error: {task.error_message}")
            else:
                print("Failed to get task status")
    except Exception as e:
        print(f"Error: {e}")


async def check_balance(args: argparse.Namespace) -> None:
    """Check Meshy account balance."""
    from ai_3d.providers.meshy import MeshyClient

    try:
        client = MeshyClient()
        async with client:
            balance = await client.get_balance()
            print(f"Credits: {json.dumps(balance, indent=2)}")
    except Exception as e:
        print(f"Could not fetch balance: {e}")


def cmd_generate(args: argparse.Namespace) -> None:
    """Wrapper to run async generate."""
    asyncio.run(generate_models(args))


def cmd_retexture(args: argparse.Namespace) -> None:
    """Wrapper to run async retexture."""
    asyncio.run(retexture_models(args))


def cmd_status(args: argparse.Namespace) -> None:
    """Wrapper to run async status check."""
    asyncio.run(check_status(args))


def cmd_balance(args: argparse.Namespace) -> None:
    """Wrapper to run async balance check."""
    asyncio.run(check_balance(args))


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Meshy AI 3D Model Generator (Async)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/meshy_3d_generator.py generate --collection signature --limit 5
  python scripts/meshy_3d_generator.py retexture --collection signature
  python scripts/meshy_3d_generator.py status abc123
  python scripts/meshy_3d_generator.py balance
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate 3D from images")
    gen_parser.add_argument("--collection", help="Collection to process")
    gen_parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    gen_parser.add_argument("--limit", type=int, default=0, help="Limit items to process")
    gen_parser.set_defaults(func=cmd_generate)

    # Retexture command
    ret_parser = subparsers.add_parser("retexture", help="Retexture existing models")
    ret_parser.add_argument("--collection", help="Collection to process")
    ret_parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    ret_parser.add_argument("--limit", type=int, default=0, help="Limit items to process")
    ret_parser.set_defaults(func=cmd_retexture)

    # Status command
    stat_parser = subparsers.add_parser("status", help="Check task status")
    stat_parser.add_argument("task_id", help="Task ID to check")
    stat_parser.add_argument("--type", choices=["image-to-3d", "retexture", "text-to-3d"])
    stat_parser.set_defaults(func=cmd_status)

    # Balance command
    bal_parser = subparsers.add_parser("balance", help="Check account balance")
    bal_parser.set_defaults(func=cmd_balance)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
