#!/usr/bin/env python3
"""
Upload generated 3D models to Threedium.io platform.
Generates iOS USDZ and Android GLTF for AR viewers.

API Docs: https://docs.threedium.io/
"""

import json
import os
from pathlib import Path

import requests


class ThreediumClient:
    """Threedium.io API client."""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.base_url = "https://api.threedium.io/v1"
        self.headers = {
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json",
        }

    def upload_model(
        self,
        model_path: str,
        product_name: str,
        collection: str,
        generate_ar: bool = True,
        optimize: bool = True,
    ) -> dict:
        """Upload GLB model to Threedium."""

        print(f"\n{'=' * 70}")
        print(f"📤 Uploading: {product_name}")
        print(f"   Collection: {collection.upper()}")
        print(f"   File: {Path(model_path).name}")
        print(f"   Size: {Path(model_path).stat().st_size / (1024 * 1024):.2f} MB")
        print(f"{'=' * 70}\n")

        url = f"{self.base_url}/models/upload"

        try:
            with open(model_path, "rb") as model_file:
                files = {"model": (Path(model_path).name, model_file, "model/gltf-binary")}

                data = {
                    "name": product_name,
                    "collection": collection,
                    "format": "glb",
                    "optimize": str(optimize).lower(),
                    "generateAR": str(generate_ar).lower(),
                }

                # Use multipart/form-data (remove Content-Type header)
                headers = {"Authorization": f"Bearer {self.secret_key}"}

                response = requests.post(
                    url,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=300,  # 5 minutes for large files
                )

                response.raise_for_status()
                result = response.json()

                print("✅ Upload successful!")
                print(f"   Model ID: {result.get('id', 'N/A')}")

                if generate_ar:
                    print(f"   iOS USDZ: {result.get('ar_ios_url', 'Generating...')}")
                    print(f"   Android GLTF: {result.get('ar_android_url', 'Generating...')}")

                print()

                return {
                    "success": True,
                    "product_name": product_name,
                    "collection": collection,
                    "model_id": result.get("id"),
                    "viewer_url": result.get("viewer_url"),
                    "ar_ios_url": result.get("ar_ios_url"),
                    "ar_android_url": result.get("ar_android_url"),
                }

        except requests.exceptions.HTTPError as e:
            error_msg = e.response.text if hasattr(e, "response") else str(e)
            print(f"❌ Upload failed: {error_msg}\n")
            return {
                "success": False,
                "product_name": product_name,
                "collection": collection,
                "error": error_msg,
            }

        except Exception as e:
            print(f"❌ Exception: {e}\n")
            return {
                "success": False,
                "product_name": product_name,
                "collection": collection,
                "error": str(e),
            }


def load_generated_models() -> list[dict]:
    """Load successfully generated models from results file."""

    results_file = Path("generated_3d_models/generation_results.json")
    if not results_file.exists():
        # Try full catalog results
        results_file = Path("generated_3d_models/full_catalog_results.json")

    if not results_file.exists():
        print("❌ No generation results found. Run generate_3d_http.py first.")
        return []

    with open(results_file) as f:
        data = json.load(f)

    # Extract successful models
    models = []
    for result in data.get("results", []):
        if result.get("success") and Path(result["model_path"]).exists():
            models.append(
                {
                    "model_path": result["model_path"],
                    "product_name": result["product_name"],
                    "collection": result.get("collection", "signature"),
                }
            )

    return models


def main():
    """Upload all generated models to Threedium."""

    print("\n" + "#" * 70)
    print("# THREEDIUM.IO UPLOAD")
    print("# Upload 3D models with AR generation")
    print("#" * 70 + "\n")

    # Get API key
    secret_key = os.getenv("THREEDIUM_SECRET_KEY")
    if not secret_key:
        print("❌ ERROR: THREEDIUM_SECRET_KEY environment variable required")
        print(
            "   Set with: export THREEDIUM_SECRET_KEY='sk_j9M44LYAQ...'"  # pragma: allowlist secret
        )
        return

    client = ThreediumClient(secret_key)

    # Load generated models
    models = load_generated_models()
    if not models:
        print("❌ No models to upload")
        return

    print(f"📦 Found {len(models)} models to upload\n")

    # Confirm
    print("This will upload models and generate AR assets.")
    print("Press ENTER to continue (or Ctrl+C to cancel)...")
    input()

    # Upload all models
    results = []
    for i, model in enumerate(models, 1):
        print(f"\n[{i}/{len(models)}]")

        result = client.upload_model(
            model_path=model["model_path"],
            product_name=model["product_name"],
            collection=model["collection"],
            generate_ar=True,
            optimize=True,
        )
        results.append(result)

    # Summary
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful

    print("\n" + "=" * 70)
    print("UPLOAD COMPLETE")
    print("=" * 70)
    print(f"✅ Successful: {successful}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")
    print("=" * 70 + "\n")

    # Save results
    results_file = Path("generated_3d_models/threedium_upload_results.json")
    with open(results_file, "w") as f:
        json.dump(
            {
                "total": len(results),
                "successful": successful,
                "failed": failed,
                "results": results,
            },
            f,
            indent=2,
        )

    print(f"💾 Results: {results_file}")

    # Show viewer URLs
    if successful > 0:
        print("\n🌐 Threedium Viewer URLs:")
        for r in results:
            if r["success"] and r.get("viewer_url"):
                print(f"   • {r['product_name']}: {r['viewer_url']}")

    print()


if __name__ == "__main__":
    main()
