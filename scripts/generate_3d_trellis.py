#!/usr/bin/env python3
"""
High-Quality 3D Model Generator using Microsoft TRELLIS.

TRELLIS (CVPR'25 Spotlight) produces superior 3D models with:
- High-fidelity geometry and textures
- PBR-quality outputs
- 1024px texture resolution
- FREE via HuggingFace Gradio API

Usage:
    python scripts/generate_3d_trellis.py [--collection NAME] [--dry-run]
"""

import argparse
import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path

# Install if needed: pip install gradio_client
try:
    from gradio_client import Client, handle_file
except ImportError:
    print("Installing gradio_client...")
    os.system("pip install gradio_client")
    from gradio_client import Client, handle_file


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


def find_clothing_images(collection_path: Path) -> list:
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


def generate_3d_trellis(
    image_path: Path,
    output_dir: Path,
    client: Client,
    texture_size: int = 1024,
    mesh_simplify: float = 0.95,
    seed: int = 42,
) -> dict:
    """Generate 3D model using TRELLIS API.

    Args:
        image_path: Path to input image
        output_dir: Directory to save GLB
        client: Gradio client instance
        texture_size: Texture resolution (512, 1024, 2048)
        mesh_simplify: Mesh simplification ratio (0.0-1.0)
        seed: Random seed for reproducibility

    Returns:
        dict with status, model path, or error
    """
    output_name = image_path.stem + ".glb"
    output_path = output_dir / output_name

    try:
        # Call TRELLIS API
        result = client.predict(
            image=handle_file(str(image_path)),
            multiimages=[],
            seed=seed,
            ss_guidance_strength=7.5,  # Structure guidance
            ss_sampling_steps=12,
            slat_guidance_strength=3,  # Latent guidance
            slat_sampling_steps=12,
            multiimage_algo="stochastic",
            mesh_simplify=mesh_simplify,
            texture_size=texture_size,
            api_name="/generate_and_extract_glb",
        )

        # result is tuple: (video_dict, glb_path, download_path)
        video_info, glb_path, download_path = result

        # Copy GLB to output directory
        if glb_path and os.path.exists(glb_path):
            shutil.copy2(glb_path, output_path)
            size_mb = output_path.stat().st_size / (1024 * 1024)
            return {
                "status": "success",
                "image": image_path.name,
                "model": str(output_path),
                "size_mb": size_mb,
            }
        else:
            return {"status": "failed", "image": image_path.name, "error": "No GLB file returned"}

    except Exception as e:
        return {"status": "failed", "image": image_path.name, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Generate 3D models with TRELLIS")
    parser.add_argument("--collection", help="Specific collection to process")
    parser.add_argument("--dry-run", action="store_true", help="Preview without generating")
    parser.add_argument(
        "--texture-size",
        type=int,
        default=1024,
        choices=[512, 1024, 2048],
        help="Texture resolution",
    )
    parser.add_argument("--limit", type=int, default=0, help="Limit items to process")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    assets_dir = project_root / "assets" / "3d-models"
    output_dir = project_root / "assets" / "3d-models-generated"

    print("=" * 60)
    print("TRELLIS HIGH-QUALITY 3D MODEL GENERATOR")
    print("=" * 60)
    print("\nTRELLIS (Microsoft CVPR'25) produces superior quality:")
    print("  - High-fidelity geometry matching input images")
    print("  - PBR-quality textures up to 2048px")
    print("  - FREE via HuggingFace Gradio API")
    print()

    # Find collections
    collections = {}
    if args.collection:
        coll_path = assets_dir / args.collection
        if coll_path.exists():
            items = find_clothing_images(coll_path)
            if items:
                collections[args.collection] = items
    else:
        for coll_dir in assets_dir.iterdir():
            if coll_dir.is_dir() and not coll_dir.name.startswith("."):
                items = find_clothing_images(coll_dir)
                if items:
                    collections[coll_dir.name] = items

    if not collections:
        print("No clothing items found!")
        return

    total_items = sum(len(items) for items in collections.values())
    print(f"Found {total_items} clothing items across {len(collections)} collections:\n")

    for name, items in collections.items():
        print(f"  {name}: {len(items)} items")
        for item in items[:5]:
            print(f"    - {item.name}")
        if len(items) > 5:
            print(f"    ... and {len(items) - 5} more")

    if args.dry_run:
        print("\n[DRY RUN] No models generated.")
        return

    # Initialize TRELLIS client
    print("\nConnecting to TRELLIS API...")
    try:
        client = Client("trellis-community/TRELLIS")
        print("Connected!")
    except Exception as e:
        print(f"Failed to connect: {e}")
        print("\nTry again later or check: https://huggingface.co/spaces/trellis-community/TRELLIS")
        return

    print("\n" + "=" * 60)
    print("STARTING GENERATION")
    print("=" * 60)

    results = {}

    for coll_name, items in collections.items():
        print(f"\n[{coll_name.upper()}]\n")

        coll_output_dir = output_dir / coll_name
        coll_output_dir.mkdir(parents=True, exist_ok=True)

        results[coll_name] = {"total": len(items), "successful": 0, "failed": 0, "results": []}

        items_to_process = items[: args.limit] if args.limit > 0 else items

        for i, img_path in enumerate(items_to_process, 1):
            print(f"  [{i}/{len(items_to_process)}] {img_path.name}")
            print("    Generating 3D model...", end=" ", flush=True)

            result = generate_3d_trellis(
                image_path=img_path,
                output_dir=coll_output_dir,
                client=client,
                texture_size=args.texture_size,
            )

            if result["status"] == "success":
                print(f"OK ({result['size_mb']:.1f} MB)")
                results[coll_name]["successful"] += 1
            else:
                print(f"FAILED: {result.get('error', 'Unknown error')}")
                results[coll_name]["failed"] += 1

            results[coll_name]["results"].append(result)

            # Small delay to be nice to the API
            time.sleep(2)

    # Summary
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)

    total_success = 0
    total_failed = 0

    for name, data in results.items():
        print(f"  {name}: {data['successful']}/{data['total']} successful")
        total_success += data["successful"]
        total_failed += data["failed"]

    print(f"\nTotal: {total_success}/{total_success + total_failed} successful")

    # Save summary
    summary = {
        "generated_at": datetime.now().isoformat(),
        "generator": "TRELLIS (Microsoft CVPR'25)",
        "texture_size": args.texture_size,
        "collections": results,
        "totals": {"successful": total_success, "failed": total_failed},
    }

    summary_path = output_dir / "TRELLIS_GENERATION_SUMMARY.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nSummary saved: {summary_path}")


if __name__ == "__main__":
    main()
