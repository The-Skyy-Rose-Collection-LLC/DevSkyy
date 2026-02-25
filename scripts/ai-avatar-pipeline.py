#!/usr/bin/env python3
"""
SkyyRose AI Avatar & Virtual Try-On Pipeline

Step 3: Create brand avatar using InstantID
Step 4: Generate virtual try-on shots with IDM-VTON for all products

Usage:
    source .venv-imagery/bin/activate
    python scripts/ai-avatar-pipeline.py --step avatar
    python scripts/ai-avatar-pipeline.py --step vton
    python scripts/ai-avatar-pipeline.py --step all
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("skyyrose-ai-pipeline")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products"
MODELS_DIR = PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "models"
AVATAR_DIR = PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "avatar"
CANONICAL_MAP = PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "data" / "canonical-images.json"


def load_product_catalog():
    """Load product catalog from canonical-images.json."""
    with open(CANONICAL_MAP) as f:
        data = json.load(f)

    products = []
    for sku, info in data.get("products", {}).items():
        # Only process products that have real images (not placeholder-only)
        if info.get("status", "").startswith("webp_downloaded") or info.get("status") == "jpg_downloaded":
            # Find the best available image
            img_file = info.get("local_webp") or info.get("local_jpg")
            if img_file:
                img_path = PRODUCTS_DIR / img_file
                if img_path.exists():
                    products.append({
                        "sku": sku,
                        "name": info["name"],
                        "collection": info["collection"],
                        "image": str(img_path),
                    })
                else:
                    log.warning("Image not found for %s: %s", sku, img_path)
        else:
            log.info("Skipping %s (%s) — %s", sku, info["name"], info.get("status"))

    log.info("Loaded %d products with real images", len(products))
    return products


def step_avatar():
    """Step 3: Create brand avatar using InstantID."""
    from gradio_client import Client, handle_file

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)

    avatar_front = AVATAR_DIR / "skyyrose-model-front.png"
    avatar_back = AVATAR_DIR / "skyyrose-model-back.png"

    if avatar_front.exists() and avatar_back.exists():
        log.info("Avatar images already exist at %s", AVATAR_DIR)
        return str(avatar_front), str(avatar_back)

    log.info("=== Step 3A: Generating brand avatar with InstantID ===")

    # Check for reference face image
    ref_face = AVATAR_DIR / "reference-face.png"
    if not ref_face.exists():
        log.error(
            "Reference face image not found at %s. "
            "Please provide a reference face image (e.g., a stock model photo) "
            "and save it as %s before running this step.",
            ref_face, ref_face,
        )
        log.info(
            "TIP: Use a royalty-free stock photo of a fashion model. "
            "The image should be a clear face photo, at least 512x512px."
        )
        sys.exit(1)

    try:
        log.info("Connecting to InstantID Space...")
        client = Client("InstantX/InstantID")

        log.info("Generating front-facing avatar...")
        result = client.predict(
            face_image=handle_file(str(ref_face)),
            pose_image=handle_file(str(ref_face)),
            prompt=(
                "full body fashion model, front facing, standing confidently, "
                "studio lighting, white background, luxury streetwear editorial, "
                "4k, sharp focus, fashion photography"
            ),
            negative_prompt=(
                "deformed, ugly, blurry, low quality, text, watermark, "
                "cropped, out of frame, worst quality, low quality"
            ),
            style_name="(No style)",
            num_steps=30,
            identitynet_strength_ratio=0.8,
            adapter_strength_ratio=0.8,
            guidance_scale=5.0,
            seed=42,
            api_name="/generate_image",
        )

        if result and len(result) > 0:
            # result is typically a filepath to the generated image
            from shutil import copy2
            output_path = result[0] if isinstance(result, (list, tuple)) else result
            copy2(output_path, str(avatar_front))
            log.info("Avatar front saved: %s", avatar_front)
        else:
            log.error("InstantID returned no result")
            sys.exit(1)

    except Exception as exc:
        log.error("InstantID failed: %s", exc)
        log.info("Falling back to PuLID-FLUX...")

        try:
            client = Client("yanze/PuLID-FLUX")
            result = client.predict(
                id_image=handle_file(str(ref_face)),
                prompt=(
                    "full body fashion model, front facing, standing confidently, "
                    "studio lighting, white background, luxury streetwear editorial, 4k"
                ),
                negative_prompt="deformed, ugly, blurry, low quality",
                num_steps=20,
                guidance_scale=4.0,
                seed=42,
                api_name="/run",
            )
            if result:
                from shutil import copy2
                output_path = result[0] if isinstance(result, (list, tuple)) else result
                copy2(output_path, str(avatar_front))
                log.info("Avatar front (PuLID) saved: %s", avatar_front)
            else:
                log.error("PuLID-FLUX also returned no result")
                sys.exit(1)
        except Exception as exc2:
            log.error("PuLID-FLUX also failed: %s", exc2)
            sys.exit(1)

    # Generate back-facing pose using Leffa
    log.info("=== Step 3B: Generating back-facing pose with Leffa ===")
    time.sleep(5)  # Rate limit courtesy

    try:
        leffa = Client("franciszzj/Leffa")
        back_result = leffa.predict(
            src_image=handle_file(str(avatar_front)),
            ref_image=handle_file(str(avatar_front)),
            control_type="pose",
            step=30,
            scale=2.5,
            seed=42,
            api_name="/leffa_predict",
        )
        if back_result:
            from shutil import copy2
            output_path = back_result[0] if isinstance(back_result, (list, tuple)) else back_result
            copy2(output_path, str(avatar_back))
            log.info("Avatar back saved: %s", avatar_back)
        else:
            log.warning("Leffa returned no result — back pose not generated")
    except Exception as exc:
        log.warning("Leffa back-pose failed: %s — will use front only", exc)

    return str(avatar_front), str(avatar_back) if avatar_back.exists() else None


def step_vton(products):
    """Step 4: Virtual try-on for all products.

    Provider priority:
      1. WeShopAI (no GPU quota, swapped params: garment=main, person=background)
      2. IDM-VTON (best quality, requires HF auth for ZeroGPU quota)
    """
    from gradio_client import Client, handle_file
    from PIL import Image

    avatar_front = AVATAR_DIR / "skyyrose-model-front.png"
    if not avatar_front.exists():
        log.error("Avatar front image not found. Run --step avatar first.")
        sys.exit(1)

    log.info("=== Step 4: Virtual Try-On ===")
    log.info("Processing %d products...", len(products))

    results = {"success": [], "failed": [], "skipped": []}
    skip_skus = {"lh-001", "sg-007"}  # Accessories

    # Connect to WeShopAI (primary — no GPU quota issues)
    ws_client = None
    try:
        ws_client = Client("WeShopAI/WeShopAI-Virtual-Try-On")
        log.info("Connected to WeShopAI (primary)")
    except Exception as exc:
        log.warning("WeShopAI unavailable: %s", exc)

    # IDM-VTON fallback (lazy-connect)
    idm_client = None

    for i, product in enumerate(products):
        sku = product["sku"]
        name = product["name"]
        garment_path = product["image"]

        if sku in skip_skus:
            log.info("[%d/%d] %s — accessory, skipping", i + 1, len(products), sku)
            results["skipped"].append(sku)
            continue

        output_front = PRODUCTS_DIR / f"{sku}-front-model.webp"
        if output_front.exists():
            log.info("[%d/%d] %s — already generated, skipping", i + 1, len(products), sku)
            results["skipped"].append(sku)
            continue

        log.info("[%d/%d] Processing %s (%s)...", i + 1, len(products), sku, name)
        saved = False

        # Try WeShopAI (garment=main_image, person=background_image)
        if ws_client:
            try:
                result = ws_client.predict(
                    main_image=handle_file(garment_path),
                    background_image=handle_file(str(avatar_front)),
                    api_name="/generate_image",
                )
                if result:
                    src = result["path"] if isinstance(result, dict) else result
                    img = Image.open(src)
                    img.save(str(output_front), "WEBP", quality=90)
                    size_kb = output_front.stat().st_size / 1024
                    log.info("  SAVED (WeShopAI): %s (%.1f KB)", output_front.name, size_kb)
                    results["success"].append(sku)
                    saved = True
                else:
                    log.warning("  WeShopAI returned None for %s", sku)
            except Exception as exc:
                log.warning("  WeShopAI error for %s: %s", sku, exc)

        # Fallback to IDM-VTON
        if not saved:
            if idm_client is None:
                try:
                    idm_client = Client("yisol/IDM-VTON")
                    log.info("  Connected to IDM-VTON (fallback)")
                except Exception as exc:
                    log.warning("  IDM-VTON unavailable: %s", exc)

            if idm_client:
                try:
                    front_result = idm_client.predict(
                        dict(background=handle_file(str(avatar_front)), layers=[], composite=None),
                        handle_file(garment_path),
                        "Virtual try-on of luxury streetwear garment on fashion model",
                        True, True, 30, 42,
                        api_name="/tryon",
                    )
                    if front_result:
                        out = front_result[0] if isinstance(front_result, (list, tuple)) else front_result
                        img = Image.open(out)
                        img.save(str(output_front), "WEBP", quality=90)
                        size_kb = output_front.stat().st_size / 1024
                        log.info("  SAVED (IDM-VTON): %s (%.1f KB)", output_front.name, size_kb)
                        results["success"].append(sku)
                        saved = True
                except Exception as exc:
                    log.error("  IDM-VTON failed for %s: %s", sku, exc)

        if not saved:
            results["failed"].append(sku)

        time.sleep(5)

    log.info("=== VTON Results ===")
    log.info("Success: %d", len(results["success"]))
    log.info("Failed: %d", len(results["failed"]))
    log.info("Skipped: %d", len(results["skipped"]))
    if results["failed"]:
        log.warning("Failed: %s", ", ".join(results["failed"]))

    return results


def step_3d_avatar():
    """Step 3C: Generate 3D GLB avatar using Hunyuan3D-2.1."""
    from gradio_client import Client, handle_file

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    avatar_front = AVATAR_DIR / "skyyrose-model-front.png"
    glb_output = MODELS_DIR / "skyyrose-avatar.glb"

    if glb_output.exists():
        log.info("3D avatar already exists at %s", glb_output)
        return str(glb_output)

    if not avatar_front.exists():
        log.error("Avatar front image not found. Run --step avatar first.")
        sys.exit(1)

    log.info("=== Step 3C: Generating 3D avatar with Hunyuan3D-2.1 ===")

    try:
        client = Client("tencent/Hunyuan3D-2.1")
        result = client.predict(
            image=handle_file(str(avatar_front)),
            steps=30,
            guidance_scale=5.0,
            seed=42,
            octree_resolution=256,
            check_box_rembg=True,
            num_chunks=8000,
            randomize_seed=False,
            api_name="/generation_all",
        )

        if result:
            # generation_all returns (file1, file2, html, mesh_stats, seed)
            # file1 or file2 should be the GLB
            from shutil import copy2
            for item in (result if isinstance(result, (list, tuple)) else [result]):
                if isinstance(item, str) and item.endswith((".glb", ".obj", ".ply")):
                    copy2(item, str(glb_output))
                    log.info("3D avatar saved: %s (%.1f KB)", glb_output, glb_output.stat().st_size / 1024)
                    return str(glb_output)
            # If no GLB extension found, take the first file path
            output_path = result[0] if isinstance(result, (list, tuple)) else result
            if isinstance(output_path, str) and os.path.isfile(output_path):
                copy2(output_path, str(glb_output))
                log.info("3D avatar saved: %s (%.1f KB)", glb_output, glb_output.stat().st_size / 1024)
                return str(glb_output)
            log.error("Hunyuan3D returned unexpected result: %s", type(result))
        else:
            log.error("Hunyuan3D returned no result")
    except Exception as exc:
        log.error("Hunyuan3D failed: %s", exc)
        log.info("Trying TRELLIS.2 as backup...")
        try:
            client = Client("microsoft/TRELLIS.2")
            result = client.predict(
                image=handle_file(str(avatar_front)),
                api_name="/predict",
            )
            if result:
                from shutil import copy2
                output_path = result if isinstance(result, str) else result[0]
                if isinstance(output_path, str) and os.path.isfile(output_path):
                    copy2(output_path, str(glb_output))
                    log.info("3D avatar (TRELLIS) saved: %s", glb_output)
                    return str(glb_output)
        except Exception as exc2:
            log.error("TRELLIS.2 also failed: %s", exc2)

    return None


def main():
    parser = argparse.ArgumentParser(description="SkyyRose AI Avatar & VTON Pipeline")
    parser.add_argument(
        "--step",
        choices=["avatar", "vton", "3d", "all"],
        default="all",
        help="Which pipeline step to run",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List products that would be processed without calling APIs",
    )
    args = parser.parse_args()

    products = load_product_catalog()

    if args.dry_run:
        log.info("=== DRY RUN — Products to process ===")
        for p in products:
            existing_front = (PRODUCTS_DIR / f"{p['sku']}-front-model.webp").exists()
            status = "EXISTS" if existing_front else "PENDING"
            log.info("  %s: %s [%s] — %s", p["sku"], p["name"], p["collection"], status)
        return

    if args.step in ("avatar", "all"):
        step_avatar()

    if args.step in ("3d", "all"):
        step_3d_avatar()

    if args.step in ("vton", "all"):
        step_vton(products)

    log.info("=== Pipeline complete ===")


if __name__ == "__main__":
    main()
