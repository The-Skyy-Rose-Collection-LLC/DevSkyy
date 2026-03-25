#!/usr/bin/env python3
"""
Iterative Scene Compositor — ALL products into ONE scene per collection.

Builds up each collection scene by compositing products one at a time:
  Scene → +product1 → +product2 → ... → final lookbook scene

3 output images total (one per collection), each with all products placed
naturally throughout the scene at different positions.

Pipeline per product: BiRefNet (bg removal) → Opus (prompt) → Kontext (ref-guided inpaint)
Each iteration uses the PREVIOUS composite as the base for the next product.

Usage:
    source .venv-imagery/bin/activate
    python scripts/run_compositor_pipeline.py
    python scripts/run_compositor_pipeline.py --collection black-rose
    python scripts/run_compositor_pipeline.py --dry-run
"""

import base64
import io
import json
import logging
import os
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Env loading — MUST happen before fal_client import
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
for env_file in [PROJECT_ROOT / ".env.hf", PROJECT_ROOT / ".env"]:
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.strip() and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

import fal_client
import httpx
from PIL import Image, ImageFilter

import anthropic

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("compositor")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
THEME_DIR = PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship"
PRODUCTS_DIR = THEME_DIR / "assets" / "images" / "products"
SCENES_DIR = THEME_DIR / "assets" / "scenes"
WORK_DIR = PROJECT_ROOT / "editorial-staging"

FAL_KEY = os.environ.get("FAL_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# ---------------------------------------------------------------------------
# Retry
# ---------------------------------------------------------------------------
MAX_RETRIES = 3
RETRY_DELAY = 5
STAGE_DELAY = 2


def retry_call(fn, label="", retries=MAX_RETRIES):
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                log.warning("%s attempt %d/%d: %s — retrying", label, attempt, retries, exc)
                time.sleep(RETRY_DELAY * attempt)
            else:
                log.error("%s failed after %d attempts: %s", label, retries, exc)
    raise last_exc


# ---------------------------------------------------------------------------
# Collection Scenes — ALL products per scene, with positions
# ---------------------------------------------------------------------------
COLLECTIONS = {
    "black-rose": {
        "scene_file": "black-rose-rooftop-garden-v2.png",
        "output_file": "black-rose-rooftop-garden-lookbook.webp",
        "products": [
            {
                "sku": "br-001",
                "x_pct": 0.10,
                "y_pct": 0.15,
                "scale": 0.22,
                "placement": "draped over arm of black lounge chair, left side of rooftop",
            },
            {
                "sku": "br-002",
                "x_pct": 0.32,
                "y_pct": 0.20,
                "scale": 0.20,
                "placement": "folded on seat of low-profile couch, center-left",
            },
            {
                "sku": "br-003",
                "x_pct": 0.75,
                "y_pct": 0.10,
                "scale": 0.22,
                "placement": "displayed on iron display ledge near railing, far right",
            },
            {
                "sku": "br-004",
                "x_pct": 0.58,
                "y_pct": 0.05,
                "scale": 0.25,
                "placement": "hanging from matte black clothing rack, right side",
            },
            {
                "sku": "br-005",
                "x_pct": 0.02,
                "y_pct": 0.35,
                "scale": 0.20,
                "placement": "folded and stacked on concrete bench near rose planter, far left",
            },
            {
                "sku": "br-006",
                "x_pct": 0.18,
                "y_pct": 0.05,
                "scale": 0.23,
                "placement": "draped over arm of black lounge chair, left-center",
            },
            {
                "sku": "br-007",
                "x_pct": 0.42,
                "y_pct": 0.40,
                "scale": 0.18,
                "placement": "laid flat on low coffee table between seating, center",
            },
            {
                "sku": "br-008",
                "x_pct": 0.65,
                "y_pct": 0.25,
                "scale": 0.22,
                "placement": "hanging from iron display hook near pendant light, right-center",
            },
        ],
    },
    "love-hurts": {
        "scene_file": "love-hurts-cathedral-rose-chamber-v2.png",
        "output_file": "love-hurts-cathedral-rose-chamber-lookbook.webp",
        "products": [
            {
                "sku": "lh-003",
                "ref_image": "lh-003-shorts-front-source.jpg",
                "x_pct": 0.70,
                "y_pct": 0.08,
                "scale": 0.22,
                "placement": "Love Hurts mesh shorts pinned flat on gothic stone wall, right side, displayed like art piece showing rose pattern and branding",
            },
            {
                "sku": "lh-001",
                "ref_image": "lh-001-fannie-pack-photo.jpg",
                "x_pct": 0.12,
                "y_pct": 0.15,
                "scale": 0.18,
                "placement": "black Fannie pack with white FANNIE text hanging from ornate gothic candelabra lamp near candles, left side, strap draped over iron arm",
            },
            {
                "sku": "lh-002",
                "ref_image": "lh-002-techflat.jpeg",
                "x_pct": 0.55,
                "y_pct": 0.35,
                "scale": 0.22,
                "placement": "black joggers with white stripe draped over gothic stone pew arm, right-center near candles, folded casually",
            },
            {
                "sku": "lh-004",
                "ref_image": "lh-004-techflat.jpeg",
                "x_pct": 0.02,
                "y_pct": 0.05,
                "scale": 0.26,
                "placement": "Love Hurts varsity jacket displayed open on carved wooden stand near stained glass window, far left, front facing showing letterman styling",
            },
        ],
    },
    "signature": {
        "scene_file": "signature-golden-gate-showroom-v2.png",
        "output_file": "signature-golden-gate-showroom-lookbook.webp",
        "products": [
            {
                "sku": "sg-002",
                "x_pct": 0.38,
                "y_pct": 0.10,
                "scale": 0.18,
                "placement": "displayed on acrylic mannequin bust near window, center",
            },
            {
                "sku": "sg-003",
                "x_pct": 0.08,
                "y_pct": 0.08,
                "scale": 0.20,
                "placement": "hanging from gold clothing rail, left alcove",
            },
            {
                "sku": "sg-004",
                "x_pct": 0.55,
                "y_pct": 0.25,
                "scale": 0.18,
                "placement": "draped over marble display cube, center-right",
            },
            {
                "sku": "sg-005",
                "x_pct": 0.30,
                "y_pct": 0.30,
                "scale": 0.20,
                "placement": "featured on center marble display table",
            },
            {
                "sku": "sg-006",
                "x_pct": 0.72,
                "y_pct": 0.15,
                "scale": 0.18,
                "placement": "folded on marble shelf display, right wall niche",
            },
            {
                "sku": "sg-007",
                "x_pct": 0.15,
                "y_pct": 0.30,
                "scale": 0.14,
                "placement": "on marble pedestal, left-center",
            },
            {
                "sku": "sg-008",
                "x_pct": 0.62,
                "y_pct": 0.35,
                "scale": 0.14,
                "placement": "on marble pedestal display, right-center near window",
            },
            {
                "sku": "sg-009",
                "x_pct": 0.02,
                "y_pct": 0.20,
                "scale": 0.22,
                "placement": "draped over designer chair, far left of showroom",
            },
            {
                "sku": "sg-010",
                "x_pct": 0.82,
                "y_pct": 0.30,
                "scale": 0.18,
                "placement": "laid flat on marble counter display, far right",
            },
            {
                "sku": "sg-011",
                "x_pct": 0.72,
                "y_pct": 0.05,
                "scale": 0.20,
                "placement": "hanging on wall-mounted clothing rack, right side",
            },
            {
                "sku": "sg-012",
                "x_pct": 0.08,
                "y_pct": 0.05,
                "scale": 0.20,
                "placement": "hanging on wall-mounted clothing rack, left side",
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def img_to_b64(path: Path, max_bytes: int = 4_500_000) -> tuple[str, str]:
    """Convert image to base64 JPEG for Anthropic API."""
    img = Image.open(path)
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (0, 0, 0))
        bg.paste(img, mask=img.split()[-1])
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")

    quality = 90
    while quality >= 40:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        data = buf.getvalue()
        if len(data) <= max_bytes:
            return base64.b64encode(data).decode("utf-8"), "image/jpeg"
        quality -= 10
        if quality < 70:
            img = img.resize((img.width * 3 // 4, img.height * 3 // 4), Image.Resampling.LANCZOS)
    return base64.b64encode(data).decode("utf-8"), "image/jpeg"


def upload_to_fal(data: bytes, name: str) -> str:
    """Upload image bytes to fal CDN."""
    for attempt in range(3):
        try:
            return fal_client.upload(data, content_type="image/png")
        except Exception as exc:
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
            else:
                raise


# ---------------------------------------------------------------------------
# Step 1: Background Removal (BiRefNet)
# ---------------------------------------------------------------------------
def remove_background(subject_path: Path, work: Path, sku: str) -> Path:
    """Remove background using BiRefNet via fal."""
    cached = work / f"{sku}-alpha.png"
    if cached.exists() and cached.stat().st_size > 10_000:
        log.info("  [bg-remove] cached: %s", cached.name)
        return cached

    log.info("  [bg-remove] BiRefNet for %s...", sku)

    def _call():
        url = upload_to_fal(subject_path.read_bytes(), f"{sku}-subject")
        result = fal_client.run("fal-ai/birefnet", arguments={"image_url": url})
        if not result or "image" not in result:
            raise RuntimeError(f"BiRefNet failed: {json.dumps(result)[:200]}")
        resp = httpx.get(result["image"]["url"], timeout=60)
        resp.raise_for_status()
        if len(resp.content) < 1000:
            raise RuntimeError("Alpha too small")
        cached.write_bytes(resp.content)
        return cached

    return retry_call(_call, label=f"BiRefNet-{sku}")


# ---------------------------------------------------------------------------
# Step 2: Opus Prompt for single product placement
# ---------------------------------------------------------------------------
def opus_prompt_for_product(
    current_scene_path: Path,
    alpha_path: Path,
    collection: str,
    placement: str,
    sku: str,
    work: Path,
) -> str:
    """Claude Opus engineers a FLUX prompt for placing ONE product into the scene."""
    cache = work / f"{sku}-prompt.txt"
    if cache.exists() and cache.stat().st_size > 50:
        prompt = cache.read_text().strip()
        log.info("  [opus] cached prompt: %d chars", len(prompt))
        return prompt

    log.info("  [opus] engineering prompt for %s...", sku)
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY, timeout=90.0)
    scene_b64, scene_mime = img_to_b64(current_scene_path)
    alpha_b64, alpha_mime = img_to_b64(alpha_path)

    def _call():
        resp = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": scene_mime,
                                "data": scene_b64,
                            },
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": alpha_mime,
                                "data": alpha_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                f"You are a scene compositor for luxury fashion brand SkyyRose.\n\n"
                                f"Image 1 is the CURRENT SCENE (may already have other products placed).\n"
                                f"Image 2 is the PRODUCT to add (background removed).\n"
                                f"PLACEMENT: {placement}\n"
                                f"COLLECTION: {collection}\n\n"
                                f"Write a FLUX inpainting prompt to render this garment naturally into the scene.\n"
                                f"The reference is a TECHFLAT (flat product photo, no model).\n"
                                f"PLACEMENT: {placement}\n\n"
                                f"CRITICAL RULES:\n"
                                f"1. GARMENT ONLY — absolutely NO people, NO mannequins, NO human figures\n"
                                f"2. Render the clothing item as an OBJECT: hung on wall, draped on furniture, pinned for display\n"
                                f"3. Preserve ALL garment details, colors, logos, patterns, and branding EXACTLY\n"
                                f"4. Match scene lighting, cast realistic shadows, correct perspective\n"
                                f"5. Natural fabric behavior: gravity, folds, draping appropriate to placement\n\n"
                                f"Return ONLY the prompt text, no explanation."
                            ),
                        },
                    ],
                }
            ],
        )
        return resp.content[0].text.strip()

    prompt = retry_call(_call, label=f"Opus-{sku}")
    cache.write_text(prompt)
    log.info("  [opus] prompt: %d chars", len(prompt))
    return prompt


# ---------------------------------------------------------------------------
# Step 3: Composite one product into the scene via Kontext
# ---------------------------------------------------------------------------
def composite_product_into_scene(
    current_scene: Image.Image,
    alpha_path: Path,
    product: dict,
    prompt: str,
    work: Path,
    sku: str,
) -> Image.Image:
    """Paste product at position, then use Kontext to harmonize it into the scene."""
    log.info("  [composite] placing %s...", sku)

    # Load alpha-matted product
    alpha_img = Image.open(alpha_path).convert("RGBA")

    # Scale and position based on product config
    target_w = int(current_scene.width * product["scale"])
    aspect = alpha_img.height / alpha_img.width
    target_h = int(target_w * aspect)
    subject_resized = alpha_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

    x = int(current_scene.width * product["x_pct"])
    y = int(current_scene.height * product["y_pct"])

    # Clamp to scene bounds
    x = min(x, current_scene.width - target_w)
    y = min(y, current_scene.height - target_h)
    x = max(0, x)
    y = max(0, y)

    # Create rough composite (paste product on scene)
    comp = current_scene.copy()
    comp.paste(subject_resized, (x, y), mask=subject_resized.split()[-1])

    # Create mask for the product region (padded for natural blending)
    mask = Image.new("L", current_scene.size, 0)
    mask.paste(subject_resized.split()[-1], (x, y))
    mask = mask.filter(ImageFilter.MaxFilter(size=21))
    mask = mask.filter(ImageFilter.GaussianBlur(radius=8))

    # Save intermediates
    comp_path = work / f"{sku}-comp-iter.png"
    mask_path = work / f"{sku}-mask-iter.png"
    comp.save(comp_path, format="PNG")
    mask.save(mask_path, format="PNG")

    # Use Kontext to harmonize (reference-guided, low strength)
    def _kontext():
        comp_url = upload_to_fal(comp_path.read_bytes(), f"{sku}-comp")
        mask_url = upload_to_fal(mask_path.read_bytes(), f"{sku}-mask")
        alpha_url = upload_to_fal(alpha_path.read_bytes(), f"{sku}-ref")

        result = fal_client.run(
            "fal-ai/flux-kontext-lora/inpaint",
            arguments={
                "image_url": comp_url,
                "mask_url": mask_url,
                "reference_image_url": alpha_url,
                "prompt": prompt,
                "num_inference_steps": 40,
                "guidance_scale": 3.5,
                "strength": 0.55,
                "output_format": "png",
                "num_images": 1,
            },
        )
        if result and "images" in result and result["images"]:
            resp = httpx.get(result["images"][0]["url"], timeout=60)
            resp.raise_for_status()
            return resp.content
        raise RuntimeError("Kontext returned no images")

    def _fal_fill_fallback():
        comp_url = upload_to_fal(comp_path.read_bytes(), f"{sku}-comp")
        mask_url = upload_to_fal(mask_path.read_bytes(), f"{sku}-mask")
        result = fal_client.run(
            "fal-ai/flux-pro/v1/fill",
            arguments={
                "image_url": comp_url,
                "mask_url": mask_url,
                "prompt": prompt,
                "output_format": "png",
                "num_images": 1,
            },
        )
        if result and "images" in result and result["images"]:
            resp = httpx.get(result["images"][0]["url"], timeout=60)
            resp.raise_for_status()
            return resp.content
        raise RuntimeError("FLUX Fill returned no images")

    # Try Kontext first, then FLUX Fill fallback
    result_bytes = None
    try:
        result_bytes = retry_call(_kontext, label=f"Kontext-{sku}")
        log.info("  [composite] %s harmonized via Kontext (%dKB)", sku, len(result_bytes) // 1024)
    except Exception as exc:
        log.warning("  [composite] Kontext failed for %s: %s — trying FLUX Fill", sku, exc)
        try:
            result_bytes = retry_call(_fal_fill_fallback, label=f"FillFallback-{sku}")
            log.info(
                "  [composite] %s via FLUX Fill fallback (%dKB)", sku, len(result_bytes) // 1024
            )
        except Exception as exc2:
            log.error("  [composite] All providers failed for %s: %s", sku, exc2)
            # Return the rough composite as last resort
            log.warning("  [composite] Using rough paste for %s (no harmonization)", sku)
            return comp

    # Load the harmonized result
    result_img = Image.open(io.BytesIO(result_bytes)).convert("RGB")

    # Save iteration checkpoint
    iter_path = work / f"{sku}-result.png"
    result_img.save(iter_path, format="PNG")

    return result_img


# ---------------------------------------------------------------------------
# Process one collection
# ---------------------------------------------------------------------------
def process_collection(name: str, config: dict, dry_run: bool = False) -> Path | None:
    collection_dir = SCENES_DIR / name
    scene_path = collection_dir / config["scene_file"]
    output_path = collection_dir / config["output_file"]

    if not scene_path.exists():
        log.error("Scene not found: %s", scene_path)
        return None

    products = config["products"]
    # Filter to products that actually exist
    available = []
    for p in products:
        subject = PRODUCTS_DIR / f"{p['sku']}-front-model.webp"
        if subject.exists():
            available.append(p)
        else:
            log.warning("SKIP %s: %s not found", p["sku"], subject.name)

    log.info("=" * 60)
    log.info("COLLECTION: %s — %d products into 1 scene", name.upper(), len(available))
    log.info("Scene: %s", scene_path.name)
    log.info("Output: %s", output_path.name)
    log.info("=" * 60)

    if dry_run:
        for p in available:
            log.info(
                "  [DRY RUN] Would composite %s at (%.0f%%, %.0f%%) scale=%.0f%%",
                p["sku"],
                p["x_pct"] * 100,
                p["y_pct"] * 100,
                p["scale"] * 100,
            )
        return None

    work = WORK_DIR / name
    work.mkdir(parents=True, exist_ok=True)

    # Start with the original scene
    current_scene = Image.open(scene_path).convert("RGB")
    log.info("Scene loaded: %dx%d", current_scene.width, current_scene.height)

    for i, product in enumerate(available, 1):
        sku = product["sku"]
        log.info("")
        log.info("── Product %d/%d: %s ──", i, len(available), sku.upper())

        # Use custom ref_image if specified, else default to front-model
        ref_name = product.get("ref_image", f"{sku}-front-model.webp")
        subject_path = PRODUCTS_DIR / ref_name
        if not subject_path.exists():
            subject_path = PRODUCTS_DIR / f"{sku}-front-model.webp"

        # Step 1: Remove background
        alpha = remove_background(subject_path, work, sku)
        time.sleep(STAGE_DELAY)

        # Step 2: Opus prompt (sees current scene state)
        # Save current scene for Opus to analyze
        current_scene_path = work / f"scene-after-{i - 1}.png"
        if not current_scene_path.exists():
            current_scene.save(current_scene_path, format="PNG")

        prompt = opus_prompt_for_product(
            current_scene_path,
            alpha,
            name,
            product["placement"],
            sku,
            work,
        )
        time.sleep(STAGE_DELAY)

        # Step 3: Composite product into scene (Kontext harmonized)
        current_scene = composite_product_into_scene(
            current_scene,
            alpha,
            product,
            prompt,
            work,
            sku,
        )

        # Save checkpoint after each product
        checkpoint = work / f"scene-after-{i}.png"
        current_scene.save(checkpoint, format="PNG")
        log.info(
            "  Checkpoint: %s (%dx%d)", checkpoint.name, current_scene.width, current_scene.height
        )
        time.sleep(STAGE_DELAY)

    # Save final lookbook
    output_path.parent.mkdir(parents=True, exist_ok=True)
    current_scene.save(output_path, format="WEBP", quality=95, method=6)
    size_kb = output_path.stat().st_size // 1024
    log.info("")
    log.info("DONE: %s — %s (%dKB)", name.upper(), output_path.name, size_kb)
    return output_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Iterative scene compositor")
    parser.add_argument("--collection", type=str, help="Single collection to process")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not FAL_KEY:
        log.error("FAL_KEY not set — check .env.hf")
        sys.exit(1)
    if not ANTHROPIC_KEY:
        log.error("ANTHROPIC_API_KEY not set — check .env.hf")
        sys.exit(1)

    collections = COLLECTIONS
    if args.collection:
        if args.collection not in COLLECTIONS:
            log.error(
                "Unknown collection: %s (available: %s)", args.collection, ", ".join(COLLECTIONS)
            )
            sys.exit(1)
        collections = {args.collection: COLLECTIONS[args.collection]}

    log.info("Iterative Scene Compositor — %d collections", len(collections))
    log.info("Pipeline: BiRefNet → Opus → Kontext (ref-guided) → iterate")
    log.info("=" * 60)

    results = []
    for name, config in collections.items():
        result = process_collection(name, config, dry_run=args.dry_run)
        results.append((name, result))

    log.info("")
    log.info("=" * 60)
    success = sum(1 for _, r in results if r)
    log.info("COMPLETE: %d/%d collections", success, len(results))
    for name, path in results:
        if path:
            log.info("  %s → %s", name, path)
        else:
            log.info("  %s → FAILED", name)


if __name__ == "__main__":
    main()
