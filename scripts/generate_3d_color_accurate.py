#!/usr/bin/env python3
"""
Generate EXACT 3D replicas with ACCURATE COLORS.
Uses color-enhanced images for perfect color fidelity.

Usage:
    # Test batch (3 products)
    python3 scripts/generate_3d_color_accurate.py --test

    # Full catalog (80 products)
    python3 scripts/generate_3d_color_accurate.py --full
"""

import argparse
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path

import requests


class Tripo3DClient:
    """Direct HTTP client for Tripo3D API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.tripo3d.ai/v2/openapi"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def upload_image(self, image_path: str) -> str:
        """Upload image and return image_token."""
        url = f"{self.base_url}/upload"

        with open(image_path, "rb") as f:
            files = {"file": f}
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.post(url, headers=headers, files=files)

        response.raise_for_status()
        data = response.json()
        return data["data"]["image_token"]

    def create_task(self, image_token: str) -> str:
        """Create 3D generation task, return task_id."""
        url = f"{self.base_url}/task"

        payload = {
            "type": "image_to_model",
            "file": {"type": "png", "file_token": image_token},
        }

        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["data"]["task_id"]

    def get_task_status(self, task_id: str) -> dict:
        """Get task status and result."""
        url = f"{self.base_url}/task/{task_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()["data"]

    def download_model(self, model_url: str, output_path: str):
        """Download GLB model from URL."""
        response = requests.get(model_url)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)


def generate_3d_model(
    client: Tripo3DClient, image_path: str, product_name: str, collection: str
) -> dict:
    """Generate EXACT 3D replica with accurate colors."""

    print(f"\n{'=' * 70}")
    print(f"🎯 {product_name}")
    print(f"   Collection: {collection.upper()}")
    print(f"   Source: {Path(image_path).name} (COLOR ENHANCED)")
    print(f"{'=' * 70}\n")

    try:
        # Step 1: Upload image
        print("📤 Uploading color-enhanced image...")
        image_token = client.upload_image(image_path)
        print("✅ Uploaded\n")

        # Step 2: Create task
        print("🎨 Generating 3D with EXACT colors...")
        task_id = client.create_task(image_token)

        # Step 3: Poll until complete
        max_attempts = 60  # 5 minutes max
        for attempt in range(max_attempts):
            task_data = client.get_task_status(task_id)
            status = task_data["status"]
            progress = task_data.get("progress", 0)

            if status == "success":
                print(f"✅ Complete! ({progress}%)\n")

                # Download GLB
                output_dir = Path("generated_3d_models_color_accurate") / collection
                output_dir.mkdir(parents=True, exist_ok=True)
                model_path = output_dir / f"{product_name}.glb"

                model_url = task_data["result"]["pbr_model"]["url"]
                rendered_url = task_data["result"]["rendered_image"]["url"]

                print("📥 Downloading...")
                client.download_model(model_url, str(model_path))

                file_size_mb = model_path.stat().st_size / (1024 * 1024)
                print(f"✅ Saved: {file_size_mb:.2f} MB\n")

                return {
                    "success": True,
                    "product_name": product_name,
                    "collection": collection,
                    "source_image": image_path,
                    "model_path": str(model_path),
                    "file_size_mb": round(file_size_mb, 2),
                    "task_id": task_id,
                    "preview_url": rendered_url,
                    "timestamp": datetime.now(UTC).isoformat(),
                }

            elif status == "failed":
                error_msg = task_data.get("error", "Unknown error")
                print(f"❌ Failed: {error_msg}\n")
                return {
                    "success": False,
                    "product_name": product_name,
                    "collection": collection,
                    "error": error_msg,
                    "timestamp": datetime.now(UTC).isoformat(),
                }

            elif status in ["queued", "running"]:
                if attempt % 5 == 0:  # Print every 25 seconds
                    print(f"   [{progress}%] Generating... ({attempt * 5}s)")
                time.sleep(5)

        print("❌ Timeout\n")
        return {
            "success": False,
            "product_name": product_name,
            "collection": collection,
            "error": "Timeout",
            "timestamp": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        print(f"❌ Exception: {e}\n")
        return {
            "success": False,
            "product_name": product_name,
            "collection": collection,
            "error": str(e),
            "timestamp": datetime.now(UTC).isoformat(),
        }


def discover_products(collection: str, test_mode: bool = False) -> list[dict]:
    """Discover color-enhanced products."""
    enhanced_dir = Path(f"assets/3d-ready-images/{collection}")

    if not enhanced_dir.exists():
        print(f"❌ Enhanced images not found: {enhanced_dir}")
        print("   Run: python3 scripts/enhance_colors_for_3d.py first")
        return []

    products = []

    for img_path in sorted(enhanced_dir.glob("*_3d_ready.png")):
        product_name = img_path.stem.replace("_3d_ready", "")
        products.append(
            {
                "image_path": str(img_path),
                "product_name": product_name,
                "collection": collection,
            }
        )

    if test_mode:
        products = products[:3]  # Test with first 3

    return products


def main():
    """Generate 3D models with accurate colors."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Test mode (3 products)")
    parser.add_argument("--full", action="store_true", help="Full catalog (80 products)")
    parser.add_argument("--yes", "-y", action="store_true", help="Auto-confirm (skip prompt)")
    args = parser.parse_args()

    test_mode = args.test or not args.full

    print("\n" + "#" * 70)
    print("# SKYYROSE COLOR-ACCURATE 3D GENERATION")
    print("# Mode: EXACT REPLICAS - ACCURATE COLORS")
    print("# Source: Color-Enhanced Images (1.8x saturation, 1.3x contrast)")
    print("#" * 70 + "\n")

    # Get API key
    api_key = os.getenv("TRIPO3D_API_KEY") or os.getenv("TRIPO_API_KEY")
    if not api_key:
        print("❌ ERROR: TRIPO3D_API_KEY environment variable required")
        return

    client = Tripo3DClient(api_key)

    # Discover all products
    collections = ["signature", "love-hurts", "black-rose"]
    all_products = []

    for collection in collections:
        products = discover_products(collection, test_mode=test_mode)
        all_products.extend(products)
        if products:
            print(f"📦 {collection.upper()}: {len(products)} products")

    if not all_products:
        print("❌ No enhanced images found!")
        print("   Run: python3 scripts/enhance_colors_for_3d.py")
        return

    mode_str = "TEST (3 products)" if test_mode else f"FULL ({len(all_products)} products)"
    print(f"\n📊 Mode: {mode_str}")
    print(f"⏱️  Estimated: {len(all_products) * 1.5:.0f}-{len(all_products) * 2:.0f} minutes\n")

    # Confirm (unless --yes flag)
    if not args.yes:
        print("Press ENTER to start generation (or Ctrl+C to cancel)...")
        input()
    else:
        print("🚀 Auto-starting generation (--yes flag)\n")

    # Generate all models
    results = []
    start_time = time.time()

    for i, product in enumerate(all_products, 1):
        print(f"\n{'=' * 70}")
        print(f"[{i}/{len(all_products)}] {product['product_name']}")
        print(f"{'=' * 70}")

        result = generate_3d_model(
            client=client,
            image_path=product["image_path"],
            product_name=product["product_name"],
            collection=product["collection"],
        )
        results.append(result)

    # Summary
    elapsed = time.time() - start_time
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful

    print("\n" + "=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)
    print(f"✅ Successful: {successful}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")
    print(f"⏱️  Time: {elapsed / 60:.1f} minutes")
    print("=" * 70 + "\n")

    # Save results
    mode_suffix = "test" if test_mode else "full"
    results_file = Path(f"generated_3d_models_color_accurate/results_{mode_suffix}.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)

    with open(results_file, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "mode": mode_str,
                "color_enhancement": "1.8x saturation, 1.3x contrast, 1.1x brightness",
                "total": len(results),
                "successful": successful,
                "failed": failed,
                "elapsed_minutes": round(elapsed / 60, 1),
                "results": results,
            },
            f,
            indent=2,
        )

    print(f"💾 Results: {results_file}\n")


if __name__ == "__main__":
    main()
