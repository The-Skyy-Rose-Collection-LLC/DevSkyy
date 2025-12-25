#!/usr/bin/env python3
"""
Generate 3D models from SkyyRose product images using Tripo3D API.

Usage:
    python scripts/generate_3d_models.py
"""

import asyncio
import os
import sys
from pathlib import Path

import aiohttp

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

TRIPO_API_KEY = os.getenv("TRIPO3D_API_KEY", "")
TRIPO_BASE_URL = "https://api.tripo3d.ai/v2/openapi"

# Best product images for 3D generation (clear, flat lay shots work best)
PRODUCTS_TO_GENERATE = [
    {
        "name": "Signature Hoodie",
        "image": "_Signature Collection_/_Signature Collection_ Hoodie.jpg",
        "collection": "SIGNATURE",
    },
    {
        "name": "Cotton Candy Tee",
        "image": "_Signature Collection_/_Signature Collection_ Cotton Candy Tee.jpg",
        "collection": "SIGNATURE",
    },
    {
        "name": "Crop Hoodie",
        "image": "_Signature Collection_/_Signature Collection_ Crop Hoodie front.jpg",
        "collection": "SIGNATURE",
    },
    {
        "name": "Sincerely Hearted Joggers",
        "image": "_Love Hurts Collection_/_Love Hurts Collection_ Sincerely Hearted Joggers (Black).jpg",
        "collection": "LOVE_HURTS",
    },
]

OUTPUT_DIR = Path(__file__).parent.parent / "generated_assets" / "3d"
IMAGE_DIR = Path(__file__).parent.parent / "generated_assets" / "product_images"


async def upload_image(session: aiohttp.ClientSession, image_path: Path) -> str:
    """Upload image to Tripo and get token."""
    print(f"  Uploading {image_path.name}...")

    with open(image_path, "rb") as f:
        image_data = f.read()

    # Get upload URL
    async with session.post(
        f"{TRIPO_BASE_URL}/upload",
        headers={"Authorization": f"Bearer {TRIPO_API_KEY}"},
        json={"type": "image"},
    ) as resp:
        if resp.status != 200:
            raise Exception(f"Failed to get upload URL: {await resp.text()}")
        data = await resp.json()
        upload_url = data["data"]["upload_url"]
        image_token = data["data"]["image_token"]

    # Upload to signed URL
    async with session.put(upload_url, data=image_data) as resp:
        if resp.status not in (200, 201):
            raise Exception(f"Failed to upload: {resp.status}")

    return image_token


async def create_3d_task(
    session: aiohttp.ClientSession, image_token: str, product_name: str
) -> str:
    """Create image-to-3D task."""
    print(f"  Creating 3D generation task for {product_name}...")

    async with session.post(
        f"{TRIPO_BASE_URL}/task",
        headers={"Authorization": f"Bearer {TRIPO_API_KEY}"},
        json={
            "type": "image_to_model",
            "file": {"type": "image", "token": image_token},
            "model_version": "v2.0-20240919",
        },
    ) as resp:
        if resp.status != 200:
            raise Exception(f"Failed to create task: {await resp.text()}")
        data = await resp.json()
        return data["data"]["task_id"]


async def wait_for_task(session: aiohttp.ClientSession, task_id: str, max_wait: int = 300) -> dict:
    """Poll task status until complete."""
    print(f"  Waiting for task {task_id}...")

    for i in range(max_wait // 5):
        async with session.get(
            f"{TRIPO_BASE_URL}/task/{task_id}",
            headers={"Authorization": f"Bearer {TRIPO_API_KEY}"},
        ) as resp:
            data = await resp.json()
            status = data["data"]["status"]
            progress = data["data"].get("progress", 0)

            print(f"    Status: {status} ({progress}%)")

            if status == "success":
                return data["data"]
            elif status == "failed":
                raise Exception(f"Task failed: {data['data'].get('error', 'Unknown error')}")

        await asyncio.sleep(5)

    raise Exception("Task timed out")


async def download_model(session: aiohttp.ClientSession, url: str, output_path: Path):
    """Download the GLB model."""
    print(f"  Downloading to {output_path.name}...")
    async with session.get(url) as resp:
        with open(output_path, "wb") as f:
            f.write(await resp.read())


async def generate_model(session: aiohttp.ClientSession, product: dict) -> Path | None:
    """Generate 3D model for a single product."""
    image_path = IMAGE_DIR / product["image"]

    if not image_path.exists():
        print(f"  ❌ Image not found: {image_path}")
        return None

    try:
        # Upload image
        image_token = await upload_image(session, image_path)

        # Create task
        task_id = await create_3d_task(session, image_token, product["name"])

        # Wait for completion
        result = await wait_for_task(session, task_id)

        # Download GLB
        glb_url = result["output"]["model"]
        output_path = OUTPUT_DIR / f"{product['name'].lower().replace(' ', '_')}.glb"
        await download_model(session, glb_url, output_path)

        print(f"  ✅ Generated: {output_path}")
        return output_path

    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return None


async def main():
    """Generate 3D models for all products."""
    if not TRIPO_API_KEY:
        print("❌ TRIPO3D_API_KEY not set!")
        print("Run: export TRIPO3D_API_KEY='your-key-here'")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("🚀 SkyyRose 3D Model Generator")
    print(f"   API: {TRIPO_BASE_URL}")
    print(f"   Output: {OUTPUT_DIR}")
    print()

    # SSL connector to handle certificate issues on macOS
    import ssl

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_context)

    async with aiohttp.ClientSession(connector=connector) as session:
        for i, product in enumerate(PRODUCTS_TO_GENERATE, 1):
            print(f"[{i}/{len(PRODUCTS_TO_GENERATE)}] {product['name']}")
            await generate_model(session, product)
            print()

    print("✅ Done! Check generated_assets/3d/ for your models.")


if __name__ == "__main__":
    asyncio.run(main())
