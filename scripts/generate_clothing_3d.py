#!/usr/bin/env python3
"""
Generate 3D models for CLOTHING items only across all collections.

This script filters out non-clothing images (logos, artistic roses, etc.)
and only generates 3D models for actual garments.

Usage:
    export TRIPO3D_API_KEY="tsk_..."
    python3 scripts/generate_clothing_3d.py [--collection NAME] [--dry-run]

Examples:
    python3 scripts/generate_clothing_3d.py                    # All collections
    python3 scripts/generate_clothing_3d.py --collection black-rose
    python3 scripts/generate_clothing_3d.py --dry-run          # Preview only
"""

import argparse
import asyncio
import base64
import json
import os
import re
import ssl
import urllib.request
from datetime import datetime
from pathlib import Path

# ============================================================================
# CLOTHING DETECTION PATTERNS
# ============================================================================
# These patterns identify clothing items vs logos/artwork

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
    # Generic clothing terms
    "womens",
    "women's",
    "mens",
    "men's",
    "unisex",
]

# Patterns to EXCLUDE (not clothing)
EXCLUDE_PATTERNS = [
    r"logo",
    r"skyyrosedad_",  # AI-generated rose artwork
    r"hyper-realistic.*rose",
    r"close-up.*rose",
    r"wide-angle.*rose",
    r"bleeding.*rose",
    r"glowing.*rose",
    r"^IMG_\d+\.HEIC$",  # iPhone raw photos (often not product shots)
    r"^[A-F0-9]{8}-[A-F0-9]{4}",  # UUID filenames (unknown content)
]


def is_clothing_image(filename: str) -> tuple[bool, str]:
    """
    Determine if an image filename indicates clothing.

    Returns:
        (is_clothing, reason)
    """
    lower = filename.lower()

    # Check exclusions first
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, filename, re.IGNORECASE):
            return False, f"Excluded: matches '{pattern}'"

    # Check for clothing keywords
    for keyword in CLOTHING_KEYWORDS:
        if keyword in lower:
            return True, f"Clothing: contains '{keyword}'"

    # PhotoRoom files are usually product photos - include them
    if "photoroom" in lower:
        return True, "Likely product photo (PhotoRoom)"

    # Photo Dec files could be anything - check if descriptive
    if re.match(r"photo\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)", lower):
        return False, "Generic date-named photo (unknown content)"

    return False, "No clothing keywords found"


def get_clothing_images(base_dir: Path, collection: str | None = None) -> dict[str, list[Path]]:
    """
    Find all clothing images organized by collection.

    Args:
        base_dir: Base directory containing collection folders
        collection: Optional specific collection to filter

    Returns:
        Dict mapping collection name to list of clothing image paths
    """
    results = {}

    # Get collection directories
    if collection:
        collections = [base_dir / collection]
    else:
        collections = [d for d in base_dir.iterdir() if d.is_dir()]

    for coll_dir in collections:
        coll_name = coll_dir.name
        images = []
        seen = set()

        # Find all images
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]:
            for img in coll_dir.rglob(ext):
                # Skip duplicates
                if img.name in seen:
                    continue
                seen.add(img.name)

                # Check if clothing
                is_clothing, reason = is_clothing_image(img.name)
                if is_clothing:
                    images.append(img)

        if images:
            results[coll_name] = images

    return results


async def generate_3d_model(image_path: Path, api_key: str, output_dir: Path) -> dict:
    """Generate 3D model from image using Tripo3D API."""
    print(f"\n  Processing: {image_path.name}")

    # Read and encode image
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    # Determine mime type
    ext = image_path.suffix.lower()
    mime_types = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png"}
    file_type = mime_types.get(ext, "jpeg")

    # SSL context
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # Step 1: Create task
    print("    Creating task...", end=" ", flush=True)
    create_payload = json.dumps(
        {
            "type": "image_to_model",
            "file": {"type": "base64", "data": image_data, "file_type": file_type},
        }
    ).encode()

    req = urllib.request.Request(
        "https://api.tripo3d.ai/v2/openapi/task",
        data=create_payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            result = json.loads(resp.read())
            if result.get("code") != 0:
                print(f"FAILED: {result.get('message')}")
                return {
                    "status": "failed",
                    "error": result.get("message"),
                    "image": image_path.name,
                }
            task_id = result["data"]["task_id"]
            print(f"OK (task: {task_id[:8]}...)")
    except Exception as e:
        print(f"FAILED: {e}")
        return {"status": "failed", "error": str(e), "image": image_path.name}

    # Step 2: Poll for completion
    print("    Generating 3D model", end="", flush=True)
    max_polls = 60
    model_url = None

    for _i in range(max_polls):
        await asyncio.sleep(5)
        print(".", end="", flush=True)

        poll_req = urllib.request.Request(
            f"https://api.tripo3d.ai/v2/openapi/task/{task_id}",
            headers={"Authorization": f"Bearer {api_key}"},
        )

        try:
            with urllib.request.urlopen(poll_req, context=ctx, timeout=30) as resp:
                status_result = json.loads(resp.read())
                status = status_result.get("data", {}).get("status", "unknown")

                if status == "success":
                    # API returns pbr_model, not model
                    model_url = status_result["data"]["output"].get("pbr_model") or status_result[
                        "data"
                    ]["output"].get("model")
                    print(" DONE!")
                    break
                elif status in ["failed", "cancelled"]:
                    print(f" FAILED ({status})")
                    return {"status": "failed", "error": f"Task {status}", "image": image_path.name}
        except Exception:
            continue
    else:
        print(" TIMEOUT")
        return {"status": "failed", "error": "Timeout after 5 minutes", "image": image_path.name}

    # Step 3: Download model
    print("    Downloading...", end=" ", flush=True)
    output_path = output_dir / f"{image_path.stem}.glb"

    try:
        download_req = urllib.request.Request(model_url)
        with urllib.request.urlopen(download_req, context=ctx, timeout=120) as resp:  # noqa: SIM117
            with open(output_path, "wb") as f:
                f.write(resp.read())
        size_mb = output_path.stat().st_size / 1024 / 1024
        print(f"OK ({size_mb:.1f} MB)")
        return {
            "status": "success",
            "image": image_path.name,
            "model": str(output_path),
            "size_mb": size_mb,
        }
    except Exception as e:
        print(f"FAILED: {e}")
        return {"status": "failed", "error": f"Download failed: {e}", "image": image_path.name}


async def main():
    parser = argparse.ArgumentParser(description="Generate 3D models for clothing items")
    parser.add_argument("--collection", help="Specific collection to process")
    parser.add_argument("--dry-run", action="store_true", help="Preview without generating")
    args = parser.parse_args()

    api_key = os.environ.get("TRIPO3D_API_KEY")
    if not api_key and not args.dry_run:
        print("ERROR: TRIPO3D_API_KEY not set")
        print("Run: export TRIPO3D_API_KEY='tsk_...'")
        return

    project_root = Path(__file__).parent.parent
    source_dir = project_root / "assets" / "3d-models"
    output_base = project_root / "assets" / "3d-models-generated"

    # Find clothing images
    print("=" * 60)
    print("CLOTHING-ONLY 3D MODEL GENERATOR")
    print("=" * 60)

    clothing_by_collection = get_clothing_images(source_dir, args.collection)

    total_items = sum(len(imgs) for imgs in clothing_by_collection.values())
    print(
        f"\nFound {total_items} clothing items across {len(clothing_by_collection)} collections:\n"
    )

    for coll_name, images in clothing_by_collection.items():
        print(f"  {coll_name}: {len(images)} items")
        for img in images:
            print(f"    - {img.name}")

    if args.dry_run:
        print("\n[DRY RUN] No models generated.")
        return

    if total_items == 0:
        print("\nNo clothing items to process.")
        return

    # Check balance
    print("\nChecking Tripo3D balance...")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    bal_req = urllib.request.Request(
        "https://api.tripo3d.ai/v2/openapi/user/balance",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(bal_req, context=ctx, timeout=10) as resp:
            bal_data = json.loads(resp.read())
            balance = bal_data.get("data", {}).get("balance", 0)
            print(f"Balance: {balance} credits")
            estimated_cost = total_items * 30  # ~30 credits per model
            print(f"Estimated cost: ~{estimated_cost} credits")
            if balance < estimated_cost:
                print("WARNING: May not have enough credits!")
    except Exception as e:
        print(f"Could not check balance: {e}")

    # Generate models
    print("\n" + "=" * 60)
    print("STARTING GENERATION")
    print("=" * 60)

    all_results = {}

    for coll_name, images in clothing_by_collection.items():
        print(f"\n[{coll_name.upper()}]")
        output_dir = output_base / coll_name
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        for img in images:
            result = await generate_3d_model(img, api_key, output_dir)
            results.append(result)
            await asyncio.sleep(2)  # Rate limiting

        all_results[coll_name] = results

    # Summary
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)

    total_success = 0
    total_failed = 0

    for coll_name, results in all_results.items():
        success = len([r for r in results if r["status"] == "success"])
        failed = len([r for r in results if r["status"] == "failed"])
        total_success += success
        total_failed += failed
        print(f"  {coll_name}: {success}/{len(results)} successful")

    print(f"\nTotal: {total_success}/{total_success + total_failed} successful")

    # Save summary
    summary = {
        "generated_at": datetime.now().isoformat(),
        "filter": "clothing_only",
        "collections": {
            name: {
                "total": len(results),
                "successful": len([r for r in results if r["status"] == "success"]),
                "failed": len([r for r in results if r["status"] == "failed"]),
                "results": results,
            }
            for name, results in all_results.items()
        },
        "totals": {"successful": total_success, "failed": total_failed},
    }

    summary_path = output_base / "CLOTHING_GENERATION_SUMMARY.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary saved: {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
