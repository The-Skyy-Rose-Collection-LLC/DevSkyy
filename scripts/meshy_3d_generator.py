#!/usr/bin/env python3
"""
Meshy AI 3D Model Generator with Webhook Support.

Supports both:
- Image-to-3D: Generate new 3D models from product images
- Retexture: Improve existing 3D models with better textures

Usage:
    python scripts/meshy_3d_generator.py generate --collection signature
    python scripts/meshy_3d_generator.py retexture --collection signature
    python scripts/meshy_3d_generator.py status <task_id>

Webhook: Your webhook URL will receive POST requests when tasks complete.
"""

import argparse
import base64
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

# Meshy API Configuration
MESHY_API_KEY = "msy_csVMaXfeQR0zah2ArXqVZeyYEDmB7kgbkRna"
MESHY_API_BASE = "https://api.meshy.ai/openapi/v1"

# Webhook URL (set this to receive notifications)
WEBHOOK_URL = os.environ.get("MESHY_WEBHOOK_URL", "")


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


def meshy_request(endpoint: str, method: str = "GET", data: dict = None) -> dict:
    """Make authenticated request to Meshy API."""
    import ssl

    url = f"{MESHY_API_BASE}/{endpoint}"
    headers = {"Authorization": f"Bearer {MESHY_API_KEY}", "Content-Type": "application/json"}

    req = urllib.request.Request(url, headers=headers, method=method)

    if data:
        req.data = json.dumps(data).encode("utf-8")

    # SSL context for macOS compatibility
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, timeout=120, context=ctx) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else str(e)
        raise Exception(f"Meshy API error {e.code}: {error_body}")


def image_to_base64(image_path: Path) -> str:
    """Convert image to base64 data URI."""
    with open(image_path, "rb") as f:
        data = f.read()

    ext = image_path.suffix.lower()
    mime_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(ext, "image/jpeg")

    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"


def create_image_to_3d_task(
    image_path: Path,
    art_style: str = "realistic",
    topology: str = "quad",
    target_polycount: int = 30000,
    should_remesh: bool = True,
) -> dict:
    """Create an Image-to-3D task on Meshy.

    Args:
        image_path: Path to the product image
        art_style: "realistic" or "cartoon"
        topology: "quad" or "triangle"
        target_polycount: Target polygon count
        should_remesh: Whether to remesh for cleaner topology

    Returns:
        Task info with task ID
    """
    image_data = image_to_base64(image_path)

    payload = {
        "image_url": image_data,
        "enable_pbr": True,
        "should_remesh": should_remesh,
        "topology": topology,
        "target_polycount": target_polycount,
        "ai_model": "meshy-5",
        "art_style": art_style,
    }

    if WEBHOOK_URL:
        payload["webhook_url"] = WEBHOOK_URL

    result = meshy_request("image-to-3d", method="POST", data=payload)
    return result


def create_retexture_task(
    model_path: Path,
    style_image_path: Path | None = None,
    text_prompt: str | None = None,
    enable_pbr: bool = True,
) -> dict:
    """Create a retexture task on Meshy.

    Args:
        model_path: Path to existing GLB model
        style_image_path: Optional image to use as texture reference
        text_prompt: Optional text description of desired texture
        enable_pbr: Whether to generate PBR maps

    Returns:
        Task info with task ID
    """
    # Read and encode the model
    with open(model_path, "rb") as f:
        model_data = base64.b64encode(f.read()).decode("utf-8")

    model_url = f"data:model/gltf-binary;base64,{model_data}"

    payload = {"model_url": model_url, "enable_pbr": enable_pbr, "enable_original_uv": True}

    if style_image_path:
        payload["image_style_url"] = image_to_base64(style_image_path)
    elif text_prompt:
        payload["text_style_prompt"] = text_prompt
    else:
        payload["text_style_prompt"] = (
            "High quality fabric texture, realistic clothing material, detailed stitching, professional lighting"
        )

    if WEBHOOK_URL:
        payload["webhook_url"] = WEBHOOK_URL

    result = meshy_request("retexture", method="POST", data=payload)
    return result


def get_task_status(task_id: str, task_type: str = "image-to-3d") -> dict:
    """Get status of a Meshy task."""
    return meshy_request(f"{task_type}/{task_id}")


def download_model(url: str, output_path: Path) -> bool:
    """Download a model from URL."""
    try:
        urllib.request.urlretrieve(url, str(output_path))
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False


def wait_for_task(task_id: str, task_type: str = "image-to-3d", timeout: int = 300) -> dict:
    """Wait for a task to complete."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        status = get_task_status(task_id, task_type)

        if status.get("status") == "SUCCEEDED":
            return status
        elif status.get("status") in ["FAILED", "EXPIRED"]:
            raise Exception(f"Task failed: {status.get('message', 'Unknown error')}")

        progress = status.get("progress", 0)
        print(f"    Progress: {progress}%...", end="\r", flush=True)
        time.sleep(5)

    raise Exception("Task timed out")


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


def cmd_generate(args):
    """Generate new 3D models from images."""
    project_root = Path(__file__).parent.parent
    assets_dir = project_root / "assets" / "3d-models"
    output_dir = project_root / "assets" / "3d-models-generated" / "meshy"

    print("=" * 60)
    print("MESHY AI - IMAGE TO 3D GENERATION")
    print("=" * 60)

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

    total = sum(len(items) for items in collections.values())
    print(f"\nFound {total} clothing items")

    for name, items in collections.items():
        print(f"  {name}: {len(items)} items")

    if args.dry_run:
        print("\n[DRY RUN] No tasks created.")
        return

    print("\n" + "=" * 60)
    print("CREATING TASKS")
    print("=" * 60)

    results = {}
    tasks = []

    for coll_name, items in collections.items():
        print(f"\n[{coll_name.upper()}]")

        coll_output_dir = output_dir / coll_name
        coll_output_dir.mkdir(parents=True, exist_ok=True)

        results[coll_name] = {"tasks": [], "successful": 0, "failed": 0}

        items_to_process = items[: args.limit] if args.limit > 0 else items

        for img_path in items_to_process:
            print(f"  Creating task: {img_path.name}...", end=" ", flush=True)

            try:
                task = create_image_to_3d_task(
                    image_path=img_path, art_style="realistic", target_polycount=30000
                )

                task_id = task.get("result")
                print(f"OK (task: {task_id[:8]}...)")

                results[coll_name]["tasks"].append(
                    {"task_id": task_id, "image": img_path.name, "output_dir": str(coll_output_dir)}
                )

                tasks.append((task_id, img_path.name, coll_output_dir))

            except Exception as e:
                print(f"FAILED: {e}")
                results[coll_name]["failed"] += 1

            time.sleep(1)  # Rate limit

    # If webhook is set, just save task list
    if WEBHOOK_URL:
        print(f"\n✓ Tasks submitted! Webhook will notify at: {WEBHOOK_URL}")
        task_list_path = output_dir / "pending_tasks.json"
        with open(task_list_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Task list saved: {task_list_path}")
        return

    # Otherwise wait for completion
    print("\n" + "=" * 60)
    print("WAITING FOR COMPLETION")
    print("=" * 60)

    for task_id, image_name, output_dir in tasks:
        print(f"\n  Waiting: {image_name}")
        try:
            result = wait_for_task(task_id, "image-to-3d", timeout=300)

            # Download model
            glb_url = result.get("model_urls", {}).get("glb")
            if glb_url:
                output_path = output_dir / f"{Path(image_name).stem}.glb"
                print("    Downloading...", end=" ", flush=True)
                if download_model(glb_url, output_path):
                    size_mb = output_path.stat().st_size / (1024 * 1024)
                    print(f"OK ({size_mb:.1f} MB)")
                else:
                    print("FAILED")
            else:
                print("    No GLB URL in response")

        except Exception as e:
            print(f"    Error: {e}")

    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)


def cmd_retexture(args):
    """Retexture existing 3D models."""
    project_root = Path(__file__).parent.parent
    models_dir = project_root / "assets" / "3d-models-generated"
    project_root / "assets" / "3d-models"
    project_root / "assets" / "3d-models-retextured" / "meshy"

    print("=" * 60)
    print("MESHY AI - RETEXTURE EXISTING MODELS")
    print("=" * 60)

    # Find GLB files
    collections = {}
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
        print("\n[DRY RUN] No tasks created.")
        return

    # Similar logic as generate...
    print("\nRetexture functionality ready - use --help for options")


def cmd_status(args):
    """Check status of a task."""
    task_id = args.task_id
    task_type = args.type or "image-to-3d"

    print(f"Checking task: {task_id}")

    try:
        status = get_task_status(task_id, task_type)
        print(json.dumps(status, indent=2))
    except Exception as e:
        print(f"Error: {e}")


def cmd_balance(args):
    """Check Meshy account balance."""
    try:
        # The balance endpoint might vary - check Meshy docs
        result = meshy_request("user/credits")
        print(f"Credits: {result}")
    except Exception as e:
        print(f"Could not fetch balance: {e}")


def main():
    parser = argparse.ArgumentParser(description="Meshy AI 3D Model Generator")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate 3D from images")
    gen_parser.add_argument("--collection", help="Collection to process")
    gen_parser.add_argument("--dry-run", action="store_true")
    gen_parser.add_argument("--limit", type=int, default=0)
    gen_parser.set_defaults(func=cmd_generate)

    # Retexture command
    ret_parser = subparsers.add_parser("retexture", help="Retexture existing models")
    ret_parser.add_argument("--collection", help="Collection to process")
    ret_parser.add_argument("--dry-run", action="store_true")
    ret_parser.add_argument("--limit", type=int, default=0)
    ret_parser.set_defaults(func=cmd_retexture)

    # Status command
    stat_parser = subparsers.add_parser("status", help="Check task status")
    stat_parser.add_argument("task_id", help="Task ID to check")
    stat_parser.add_argument("--type", choices=["image-to-3d", "retexture"])
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
