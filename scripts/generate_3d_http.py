#!/usr/bin/env python3
"""
Direct Tripo3D HTTP API client - EXACT replicas.
Bypasses SDK completely, uses REST API directly.
"""

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
            # Remove Content-Type for multipart/form-data
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


def generate_3d_model(client: Tripo3DClient, image_path: str, product_name: str) -> dict:
    """Generate EXACT 3D replica."""

    print(f"\n{'=' * 70}")
    print(f"🎯 {product_name}")
    print(f"   Source: {Path(image_path).name}")
    print("   Quality: MAXIMUM (latest model)")
    print(f"{'=' * 70}\n")

    try:
        # Step 1: Upload image
        print("📤 Uploading image...")
        image_token = client.upload_image(image_path)
        print(f"✅ Uploaded: {image_token}\n")

        # Step 2: Create task
        print("🎨 Creating 3D generation task...")
        task_id = client.create_task(image_token)
        print(f"✅ Task ID: {task_id}\n")

        # Step 3: Poll until complete
        print("⏳ Generating (2-5 minutes)...")
        max_attempts = 60  # 5 minutes max

        for attempt in range(max_attempts):
            task_data = client.get_task_status(task_id)
            status = task_data["status"]

            if status == "success":
                print("✅ Generation complete!\n")

                # Download GLB
                output_dir = Path("generated_3d_models")
                output_dir.mkdir(parents=True, exist_ok=True)
                model_path = output_dir / f"{product_name}.glb"

                # Get model URL from result (nested structure)
                model_url = task_data["result"]["pbr_model"]["url"]
                rendered_url = task_data["result"]["rendered_image"]["url"]

                print("📥 Downloading GLB from Tripo...")
                client.download_model(model_url, str(model_path))

                file_size_mb = model_path.stat().st_size / (1024 * 1024)
                print(f"✅ Saved: {model_path} ({file_size_mb:.2f} MB)\n")

                return {
                    "success": True,
                    "product_name": product_name,
                    "source_image": image_path,
                    "model_path": str(model_path),
                    "file_size_mb": round(file_size_mb, 2),
                    "task_id": task_id,
                    "preview_url": rendered_url,
                    "timestamp": datetime.now(UTC).isoformat(),
                }

            elif status == "failed":
                error_msg = task_data.get("error", "Unknown error")
                print(f"❌ Generation failed: {error_msg}\n")
                return {
                    "success": False,
                    "product_name": product_name,
                    "error": error_msg,
                    "timestamp": datetime.now(UTC).isoformat(),
                }

            elif status in ["queued", "running"]:
                print(f"   [{attempt + 1}/{max_attempts}] Status: {status} (waiting 5s...)")
                time.sleep(5)

            else:
                print(f"❌ Unknown status: {status}\n")
                return {
                    "success": False,
                    "product_name": product_name,
                    "error": f"Unknown status: {status}",
                    "timestamp": datetime.now(UTC).isoformat(),
                }

        print(f"❌ Timeout after {max_attempts * 5}s\n")
        return {
            "success": False,
            "product_name": product_name,
            "error": "Timeout waiting for generation",
            "timestamp": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        print(f"❌ Exception: {e}\n")
        import traceback

        traceback.print_exc()
        return {
            "success": False,
            "product_name": product_name,
            "error": str(e),
            "timestamp": datetime.now(UTC).isoformat(),
        }


def main():
    """Generate 3D models using direct HTTP API."""

    print("\n" + "#" * 70)
    print("# SKYYROSE 3D GENERATION - TRIPO3D HTTP API")
    print("# Mode: EXACT REPLICAS - NO ALTERATIONS")
    print("# Quality: MAXIMUM")
    print("#" * 70 + "\n")

    # Get API key
    api_key = os.getenv("TRIPO3D_API_KEY") or os.getenv("TRIPO_API_KEY")
    if not api_key:
        print("❌ ERROR: TRIPO3D_API_KEY environment variable required")
        return

    client = Tripo3DClient(api_key)

    # Find products
    signature_dir = Path("assets/enhanced-images/signature")
    products = []

    for product_dir in sorted(signature_dir.iterdir())[:3]:  # TEST: 3 products
        if not product_dir.is_dir():
            continue

        # Prefer transparent PNG
        img_path = product_dir / f"{product_dir.name}_transparent.png"
        if not img_path.exists():
            img_path = product_dir / f"{product_dir.name}_retina.jpg"

        if img_path.exists():
            products.append(
                {
                    "image_path": str(img_path),
                    "product_name": product_dir.name,
                }
            )

    print(f"📦 Found {len(products)} products to generate\n")

    # Generate models
    results = []
    for i, product in enumerate(products, 1):
        print(f"[{i}/{len(products)}]")
        result = generate_3d_model(
            client=client,
            image_path=product["image_path"],
            product_name=product["product_name"],
        )
        results.append(result)

    # Summary
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful

    print("\n" + "=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)
    print(f"✅ Successful: {successful}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")
    print("=" * 70 + "\n")

    # Save results
    results_file = Path("generated_3d_models/generation_results.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)

    with open(results_file, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "api": "Tripo3D HTTP API",
                "model_version": "latest",
                "total": len(results),
                "successful": successful,
                "failed": failed,
                "results": results,
            },
            f,
            indent=2,
        )

    print(f"💾 Results: {results_file}")

    # Show successful models
    if successful > 0:
        print("\n✅ Generated Models:")
        for r in results:
            if r["success"]:
                print(f"   • {r['model_path']} ({r['file_size_mb']} MB)")

    print()


if __name__ == "__main__":
    main()
