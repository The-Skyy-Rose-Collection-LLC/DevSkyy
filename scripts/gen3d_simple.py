#!/usr/bin/env python3
"""
Simple direct Tripo3D API generation - EXACT replicas.
Uses official Tripo SDK directly without agent wrapper.
"""

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path

# Tripo3D official SDK
from tripo3d import TaskStatus, TripoClient


def generate_3d_model(image_path: str, product_name: str) -> dict:
    """Generate 3D model using Tripo3D API directly."""

    api_key = os.getenv("TRIPO3D_API_KEY") or os.getenv("TRIPO_API_KEY")
    if not api_key:
        raise ValueError("TRIPO3D_API_KEY environment variable required")

    client = TripoClient(api_key=api_key)

    print(f"\n{'=' * 70}")
    print(f"🎯 {product_name}")
    print(f"   Source: {Path(image_path).name}")
    print("   Quality: MAXIMUM")
    print(f"{'=' * 70}\n")

    try:
        # Step 1: Upload image
        print("📤 Uploading image...")
        upload_result = client.upload_file(image_path)
        image_token = upload_result["image_token"]
        print(f"✅ Uploaded: {image_token}\n")

        # Step 2: Submit generation task
        print("🎨 Submitting 3D generation task...")
        task = client.create_task_from_image(
            image_token=image_token,
            model_version="v2.0-20250104",  # Latest model
            texture_seed=0,
        )
        task_id = task["task_id"]
        print(f"✅ Task created: {task_id}\n")

        # Step 3: Wait for completion
        print("⏳ Generating 3D model (2-5 minutes)...")
        max_attempts = 60  # 5 minutes max
        for attempt in range(max_attempts):
            task_status = client.get_task(task_id)
            status = task_status["data"]["status"]

            if status == TaskStatus.SUCCESS.value:
                print("✅ Generation complete!\n")

                # Download GLB model
                output_dir = Path("./generated_3d_models")
                output_dir.mkdir(parents=True, exist_ok=True)

                model_path = output_dir / f"{product_name}.glb"

                result = task_status["data"]["result"]
                rendered_image_url = result.get("rendered_image", {}).get("url")
                pbr_model_url = result.get("pbr_model", {}).get("url")

                if pbr_model_url:
                    print("📥 Downloading GLB...")
                    import requests

                    response = requests.get(pbr_model_url)
                    with open(model_path, "wb") as f:
                        f.write(response.content)

                    print(f"✅ Saved: {model_path}\n")

                    return {
                        "success": True,
                        "product_name": product_name,
                        "source_image": image_path,
                        "model_path": str(model_path),
                        "rendered_preview": rendered_image_url,
                        "task_id": task_id,
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                else:
                    print("❌ No model URL in result\n")
                    return {
                        "success": False,
                        "product_name": product_name,
                        "error": "No model URL",
                        "timestamp": datetime.now(UTC).isoformat(),
                    }

            elif status == TaskStatus.FAILED.value:
                print("❌ Generation failed\n")
                return {
                    "success": False,
                    "product_name": product_name,
                    "error": "Task failed",
                    "timestamp": datetime.now(UTC).isoformat(),
                }

            elif status == TaskStatus.RUNNING.value or status == TaskStatus.QUEUED.value:
                print(f"   Progress: {attempt + 1}/{max_attempts} (waiting 5s...)")
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
            "error": "Timeout",
            "timestamp": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        print(f"❌ Exception: {e}\n")
        return {
            "success": False,
            "product_name": product_name,
            "error": str(e),
            "timestamp": datetime.now(UTC).isoformat(),
        }


def main():
    """Generate 3D models for Signature collection."""

    print("\n" + "#" * 70)
    print("# SKYYROSE 3D GENERATION - TRIPO3D SDK")
    print("# Mode: EXACT REPLICAS - NO ALTERATIONS")
    print("# Quality: MAXIMUM")
    print("#" * 70 + "\n")

    # Find products
    signature_dir = Path("assets/enhanced-images/signature")
    products = []

    for product_dir in sorted(signature_dir.iterdir())[:3]:  # TEST: 3 products
        if not product_dir.is_dir():
            continue

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

    print(f"📦 Found {len(products)} products\n")

    # Generate models
    results = []
    for product in products:
        result = generate_3d_model(
            image_path=product["image_path"],
            product_name=product["product_name"],
        )
        results.append(result)

    # Summary
    successful = sum(1 for r in results if r["success"])

    print("\n" + "=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)
    print(f"✅ Successful: {successful}/{len(results)}")
    print(f"❌ Failed: {len(results) - successful}/{len(results)}")
    print("=" * 70 + "\n")

    # Save results
    results_file = Path("generated_3d_models/results.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)

    with open(results_file, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "total": len(results),
                "successful": successful,
                "results": results,
            },
            f,
            indent=2,
        )

    print(f"💾 Results: {results_file}\n")


if __name__ == "__main__":
    main()
