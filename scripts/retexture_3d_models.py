#!/usr/bin/env python3
"""
Retexture existing 3D GLB models using Meshy AI via fal.ai.

This takes your existing GLB models and applies high-quality PBR textures
using the original product images as style reference.

Cost: ~$0.30 per model
Quality: Production-ready PBR textures

Usage:
    export FAL_KEY="your_fal_api_key"
    python scripts/retexture_3d_models.py [--collection NAME] [--dry-run]

Get API key at: https://fal.ai/dashboard/keys
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path

try:
    import fal_client
except ImportError:
    print("Installing fal-client...")
    os.system("pip install fal-client")
    import fal_client


def find_matching_image(glb_path: Path, images_dir: Path) -> Path | None:
    """Find the original image that matches a GLB file."""
    stem = glb_path.stem.lower()

    # Look for exact or partial matches
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        # Try exact match first
        for img in images_dir.rglob(f"*{ext}"):
            if img.stem.lower() == stem:
                return img
        for img in images_dir.rglob(f"*{ext.upper()}"):
            if img.stem.lower() == stem:
                return img

    # Try partial match (GLB name contained in image name)
    for ext in [".jpg", ".jpeg", ".png", ".webp", ".JPG", ".JPEG", ".PNG"]:
        for img in images_dir.rglob(f"*{ext}"):
            # Clean up names for comparison
            glb_clean = stem.replace("_", " ").replace("-", " ").lower()
            img_clean = img.stem.replace("_", " ").replace("-", " ").lower()

            # Check if names are similar enough
            if glb_clean[:20] in img_clean or img_clean[:20] in glb_clean:
                return img

    return None


def upload_to_fal(file_path: Path) -> str:
    """Upload a file to fal.ai and return the URL."""
    url = fal_client.upload_file(str(file_path))
    return url


def retexture_model(
    glb_url: str,
    style_image_url: str | None = None,
    text_prompt: str | None = None,
    enable_pbr: bool = True,
) -> dict:
    """Retexture a 3D model using Meshy via fal.ai.

    Args:
        glb_url: URL of the GLB model to retexture
        style_image_url: URL of image to use as style reference
        text_prompt: Text description of desired texture
        enable_pbr: Whether to generate PBR maps

    Returns:
        dict with model URLs and textures
    """
    # Build request
    request = {
        "model_url": glb_url,
        "enable_pbr": enable_pbr,
        "enable_original_uv": True,
        "enable_safety_checker": True,
    }

    if style_image_url:
        request["image_style_url"] = style_image_url
    elif text_prompt:
        request["text_style_prompt"] = text_prompt
    else:
        # Default prompt for fashion items
        request[
            "text_style_prompt"
        ] = "High quality fabric texture, realistic clothing material, detailed stitching, professional fashion photography lighting"

    # Submit to fal.ai
    result = fal_client.subscribe("fal-ai/meshy/v5/retexture", arguments=request, with_logs=True)

    return result


def download_file(url: str, output_path: Path) -> bool:
    """Download a file from URL to local path."""
    import urllib.request

    try:
        urllib.request.urlretrieve(url, str(output_path))
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Retexture existing 3D models with Meshy AI")
    parser.add_argument("--collection", help="Specific collection to process")
    parser.add_argument("--dry-run", action="store_true", help="Preview without processing")
    parser.add_argument("--limit", type=int, default=0, help="Limit items to process")
    parser.add_argument(
        "--use-images",
        action="store_true",
        default=True,
        help="Use original images as style reference",
    )
    args = parser.parse_args()

    # Check API key
    if not os.environ.get("FAL_KEY"):
        print("ERROR: FAL_KEY environment variable not set")
        print("\nGet your API key at: https://fal.ai/dashboard/keys")
        print("Then run: export FAL_KEY='your_key_here'")
        return

    project_root = Path(__file__).parent.parent
    models_dir = project_root / "assets" / "3d-models-generated"
    assets_dir = project_root / "assets" / "3d-models"
    output_dir = project_root / "assets" / "3d-models-retextured"

    print("=" * 60)
    print("MESHY AI RETEXTURE - IMPROVE EXISTING 3D MODELS")
    print("=" * 60)
    print("\nThis will retexture your existing GLB models with:")
    print("  - High-quality PBR textures")
    print("  - Original images as style reference")
    print("  - Professional fabric/material rendering")
    print("\nCost: ~$0.30 per model")
    print()

    # Find collections with GLB files
    collections = {}
    if args.collection:
        coll_dir = models_dir / args.collection
        if coll_dir.exists():
            glbs = list(coll_dir.glob("*.glb"))
            # Filter out UUID-named files (from old generation)
            glbs = [g for g in glbs if not g.stem.endswith("_pbr")]
            if glbs:
                collections[args.collection] = glbs
    else:
        for coll_dir in models_dir.iterdir():
            if coll_dir.is_dir():
                glbs = list(coll_dir.glob("*.glb"))
                # Filter out UUID-named files
                glbs = [g for g in glbs if not g.stem.endswith("_pbr")]
                if glbs:
                    collections[coll_dir.name] = glbs

    if not collections:
        print("No GLB models found!")
        return

    total_models = sum(len(glbs) for glbs in collections.values())
    estimated_cost = total_models * 0.30

    print(f"Found {total_models} GLB models across {len(collections)} collections")
    print(f"Estimated cost: ${estimated_cost:.2f}\n")

    for name, glbs in collections.items():
        print(f"  {name}: {len(glbs)} models")
        for glb in glbs[:3]:
            print(f"    - {glb.name}")
        if len(glbs) > 3:
            print(f"    ... and {len(glbs) - 3} more")

    if args.dry_run:
        print("\n[DRY RUN] No models processed.")
        return

    # Confirm
    print(f"\nThis will cost approximately ${estimated_cost:.2f}")
    confirm = input("Continue? (y/n): ")
    if confirm.lower() != "y":
        print("Cancelled.")
        return

    print("\n" + "=" * 60)
    print("STARTING RETEXTURE")
    print("=" * 60)

    results = {}

    for coll_name, glbs in collections.items():
        print(f"\n[{coll_name.upper()}]\n")

        # Create output directory
        coll_output_dir = output_dir / coll_name
        coll_output_dir.mkdir(parents=True, exist_ok=True)

        # Find corresponding assets directory for style images
        coll_assets_dir = assets_dir / coll_name

        results[coll_name] = {"total": len(glbs), "successful": 0, "failed": 0, "results": []}

        glbs_to_process = glbs[: args.limit] if args.limit > 0 else glbs

        for i, glb_path in enumerate(glbs_to_process, 1):
            print(f"  [{i}/{len(glbs_to_process)}] {glb_path.name}")

            try:
                # Upload GLB to fal
                print("    Uploading model...", end=" ", flush=True)
                glb_url = upload_to_fal(glb_path)
                print("OK")

                # Find and upload matching style image
                style_url = None
                if args.use_images and coll_assets_dir.exists():
                    style_image = find_matching_image(glb_path, coll_assets_dir)
                    if style_image:
                        print(f"    Using style: {style_image.name}...", end=" ", flush=True)
                        style_url = upload_to_fal(style_image)
                        print("OK")
                    else:
                        print("    No matching image found, using text prompt")

                # Retexture
                print("    Retexturing with Meshy AI...", end=" ", flush=True)
                result = retexture_model(
                    glb_url=glb_url, style_image_url=style_url, enable_pbr=True
                )
                print("OK")

                # Download result
                if "model_glb" in result and result["model_glb"]:
                    output_path = coll_output_dir / f"{glb_path.stem}_hq.glb"
                    print("    Downloading...", end=" ", flush=True)
                    if download_file(result["model_glb"]["url"], output_path):
                        size_mb = output_path.stat().st_size / (1024 * 1024)
                        print(f"OK ({size_mb:.1f} MB)")
                        results[coll_name]["successful"] += 1
                        results[coll_name]["results"].append(
                            {
                                "status": "success",
                                "original": glb_path.name,
                                "retextured": str(output_path),
                                "size_mb": size_mb,
                            }
                        )
                    else:
                        raise Exception("Download failed")
                else:
                    raise Exception("No GLB in response")

            except Exception as e:
                print(f"FAILED: {e}")
                results[coll_name]["failed"] += 1
                results[coll_name]["results"].append(
                    {"status": "failed", "original": glb_path.name, "error": str(e)}
                )

            # Rate limit
            time.sleep(2)

    # Summary
    print("\n" + "=" * 60)
    print("RETEXTURE COMPLETE")
    print("=" * 60)

    total_success = sum(r["successful"] for r in results.values())
    total_failed = sum(r["failed"] for r in results.values())

    for name, data in results.items():
        print(f"  {name}: {data['successful']}/{data['total']} successful")

    print(f"\nTotal: {total_success}/{total_success + total_failed} successful")
    print(f"Actual cost: ~${total_success * 0.30:.2f}")

    # Save summary
    summary = {
        "retextured_at": datetime.now().isoformat(),
        "service": "Meshy AI via fal.ai",
        "cost_per_model": 0.30,
        "collections": results,
        "totals": {
            "successful": total_success,
            "failed": total_failed,
            "estimated_cost": total_success * 0.30,
        },
    }

    summary_path = output_dir / "RETEXTURE_SUMMARY.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nSummary saved: {summary_path}")
    print(f"Retextured models in: {output_dir}")


if __name__ == "__main__":
    main()
