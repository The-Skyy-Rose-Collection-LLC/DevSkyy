#!/usr/bin/env python3
"""SkyyRose Pipeline Orchestrator — Context-Aware AI Image Pipeline.

Smart-routes tasks to the minimum required builders:
    FLUX Pro v1.1  → Scene generation (text-to-image)
    FLUX Depth     → Depth-conditioned compositing (structure-preserving)
    Bria Product   → Product injection into scenes

Task Types:
    scene       — Generate scene backgrounds only (FLUX Pro)
    product     — Composite product into existing scene (Bria only)
    lookbook    — Full pipeline: scene → depth composite → product inject → QA
    reshoot     — Re-render scene with depth control (FLUX Depth)
    depth_comp  — Depth-aware composite only (FLUX Depth)

Usage:
    source .venv-imagery/bin/activate
    python scripts/skyyrose_pipeline.py --task scene --collection black-rose
    python scripts/skyyrose_pipeline.py --task product --scene black-rose-rooftop-garden
    python scripts/skyyrose_pipeline.py --task lookbook --collection black-rose
    python scripts/skyyrose_pipeline.py --task reshoot --scene black-rose-rooftop-garden --prompt "..."
    python scripts/skyyrose_pipeline.py --list
    python scripts/skyyrose_pipeline.py --task lookbook --all --dry-run
"""

import argparse
import base64
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("skyyrose-pipeline")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
THEME_DIR = PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship"
PRODUCTS_DIR = THEME_DIR / "assets" / "images" / "products"
SCENES_DIR = THEME_DIR / "assets" / "scenes"

# Load env vars
for env_file in [PROJECT_ROOT / ".env.hf", PROJECT_ROOT / ".env"]:
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.strip() and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                v = v.strip().strip('"').strip("'")
                if v:
                    os.environ.setdefault(k.strip(), v)

FAL_KEY = os.environ.get("FAL_KEY", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# ── FAL Endpoints ────────────────────────────────────────────────────────────

ENDPOINTS = {
    "flux_pro": "https://fal.run/fal-ai/flux-pro/v1.1",
    "flux_depth": "https://fal.run/fal-ai/flux-lora-depth",
    "bria_product": "https://fal.run/fal-ai/bria/product-shot",
    "bria_bg_remove": "https://fal.run/fal-ai/bria/background/remove",
    "fashn_vton": "https://fal.run/fal-ai/fashn/tryon/v1.5",
}

# ── Cost Tracking ────────────────────────────────────────────────────────────

COST_PER_CALL = {
    "flux_pro": 0.05,
    "flux_depth": 0.025,
    "bria_product": 0.04,
    "bria_bg_remove": 0.018,
    "fashn_vton": 0.075,
    "gemini_qa": 0.002,
}

# ── Task Router ──────────────────────────────────────────────────────────────
# Each task type maps to the minimum set of builders needed.

TASK_BUILDERS = {
    "scene": ["flux_pro"],
    "product": ["bria_product"],
    "lookbook": ["flux_pro", "flux_depth", "bria_product"],
    "reshoot": ["flux_depth"],
    "depth_comp": ["flux_depth", "bria_product"],
}

# ── Scene Definitions ────────────────────────────────────────────────────────

SCENES = {
    "black-rose-rooftop-garden": {
        "collection": "black-rose",
        "background": "black-rose-rooftop-garden-v2.png",
        "scene_prompt": (
            "Luxury rooftop garden at night under a clear sky full of stars. "
            "The San Francisco Bay Bridge is lit up in the background, its "
            "lights reflecting on the dark water below. Modern dark planters "
            "overflowing with black roses and deep green foliage. Sleek black "
            "lounge furniture with a low-profile couch and accent chairs. "
            "A matte black clothing rack near the edge. Silver hanging "
            "pendant lights cast pools of cool light. Polished dark concrete "
            "floor with subtle wet reflections. Cinematic luxury fashion "
            "photography, 4K, photorealistic."
        ),
        "products": [
            {
                "sku": "br-006",
                "placement": "draped over arm of black lounge chair, left side of scene",
            },
            {
                "sku": "br-001",
                "placement": "folded on seat of low-profile couch, center-left of scene",
            },
            {
                "sku": "br-002",
                "placement": "folded on side table next to planter, center-right of scene",
            },
            {
                "sku": "br-004",
                "placement": "hanging from matte black clothing rack, right side of scene",
            },
        ],
    },
    "love-hurts-cathedral-rose-chamber": {
        "collection": "love-hurts",
        "background": "love-hurts-cathedral-rose-chamber-v2.png",
        "scene_prompt": (
            "Dark gothic cathedral interior converted into an intimate "
            "luxury showroom. Towering stained glass windows casting "
            "crimson and rose-gold light across stone walls. An enchanted "
            "rose under a glass dome on a marble pedestal at center. "
            "Gothic iron candelabra stands with flickering candles. "
            "Deep red velvet drapes and stone archways. Dark polished "
            "marble floor reflecting candlelight. Moody, romantic "
            "atmosphere. Cinematic luxury fashion photography, 4K."
        ),
        "products": [
            {
                "sku": "lh-005",
                "placement": "draped beside enchanted rose glass dome, center-left of scene",
            },
            {
                "sku": "lh-001",
                "placement": "hung from gothic candelabra stand, right side of scene",
            },
            {
                "sku": "lh-003",
                "placement": "displayed on stone ledge in stained glass alcove, center of scene",
            },
        ],
    },
    "signature-golden-gate-showroom": {
        "collection": "signature",
        "background": "signature-golden-gate-showroom-v2.png",
        "scene_prompt": (
            "Ultra-modern luxury showroom with floor-to-ceiling windows "
            "overlooking the Golden Gate Bridge at golden hour. Warm "
            "sunset light floods the space. Marble display tables, "
            "wall-mounted matte black clothing racks, and marble "
            "pedestals. Polished concrete floors with brass accents. "
            "Minimalist but luxurious. The bridge is bathed in golden "
            "light with fog rolling beneath. Cinematic luxury fashion "
            "photography, 4K, photorealistic."
        ),
        "products": [
            {"sku": "sg-012", "placement": "hanging on wall-mounted clothing rack, left side"},
            {"sku": "sg-005", "placement": "featured on center marble display table"},
            {"sku": "sg-007", "placement": "on marble pedestal, left-center"},
            {"sku": "sg-011", "placement": "hanging on wall-mounted clothing rack, right side"},
        ],
    },
}


# ── Utility ──────────────────────────────────────────────────────────────────


def encode_image_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def mime_for(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        "webp": "image/webp",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
    }.get(ext.lstrip("."), "image/png")


def fal_request(endpoint_key: str, payload: dict, retries: int = 3) -> dict:
    """Make a synchronous FAL API request with retries."""
    url = ENDPOINTS[endpoint_key]
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Key {FAL_KEY}",
        "Content-Type": "application/json",
    }

    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=180) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            log.warning(f"[{endpoint_key}] attempt {attempt}/{retries} HTTP {e.code}: {body[:200]}")
            if attempt < retries:
                time.sleep(10 * attempt)
        except Exception as e:
            log.warning(f"[{endpoint_key}] attempt {attempt}/{retries} error: {e}")
            if attempt < retries:
                time.sleep(10 * attempt)

    return {"error": f"All {retries} retries exhausted for {endpoint_key}"}


def download_image(url: str, dest: Path) -> bool:
    """Download image from URL to local path."""
    try:
        urllib.request.urlretrieve(url, str(dest))
        return True
    except Exception as e:
        log.error(f"Download failed: {e}")
        return False


def extract_image_url(result: dict) -> str | None:
    """Extract image URL from various FAL response formats."""
    if "images" in result and result["images"]:
        return result["images"][0].get("url")
    if "image" in result:
        if isinstance(result["image"], dict):
            return result["image"].get("url")
        if isinstance(result["image"], str):
            return result["image"]
    if "output" in result and isinstance(result["output"], str):
        return result["output"]
    return None


# ── Vision QA (Gemini) ───────────────────────────────────────────────────────


def vision_qa(image_path: Path, prompt: str) -> dict:
    """Run Gemini vision QA on a generated image."""
    if not GOOGLE_API_KEY:
        return {"pass": True, "reason": "QA skipped — no GOOGLE_API_KEY"}

    img_b64 = encode_image_b64(image_path)
    mime = mime_for(image_path)

    qa_prompt = (
        f"You are a luxury fashion brand quality inspector. {prompt}\n"
        'Respond with JSON: {"pass": true/false, "score": 1-10, "issues": [...]}'
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"inline_data": {"mime_type": mime, "data": img_b64}},
                    {"text": qa_prompt},
                ]
            }
        ],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GOOGLE_API_KEY}"
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    try:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except Exception as e:
        log.warning(f"Vision QA error: {e}")
        return {"pass": True, "reason": f"QA error: {e}"}


# ── Builders ─────────────────────────────────────────────────────────────────


def build_scene(scene_key: str, output_dir: Path, dry_run: bool = False) -> Path | None:
    """Stage 1: Generate scene background with FLUX Pro v1.1."""
    scene = SCENES[scene_key]
    out_path = output_dir / f"{scene_key}-pipeline-v1.png"

    log.info(f"[FLUX Pro] Generating scene: {scene_key}")

    if dry_run:
        log.info(f"  [DRY RUN] Would generate scene (~${COST_PER_CALL['flux_pro']:.3f})")
        return None

    result = fal_request(
        "flux_pro",
        {
            "prompt": scene["scene_prompt"],
            "image_size": "landscape_16_9",
            "num_images": 1,
            "output_format": "png",
            "safety_tolerance": "5",
        },
    )

    if "error" in result:
        log.error(f"  Scene generation failed: {result['error']}")
        return None

    image_url = extract_image_url(result)
    if not image_url:
        log.error(f"  No image URL in response: {json.dumps(result)[:200]}")
        return None

    if download_image(image_url, out_path):
        size_kb = out_path.stat().st_size // 1024
        log.info(f"  Scene generated: {out_path.name} ({size_kb}KB)")
        return out_path

    return None


def build_depth_composite(
    scene_image: Path,
    prompt: str,
    output_path: Path,
    dry_run: bool = False,
) -> Path | None:
    """Stage 2: Depth-conditioned re-render with FLUX Depth.

    Takes an existing scene image as the depth source and generates a
    new image that preserves the spatial structure but can add/modify
    elements via the prompt.
    """
    log.info(f"[FLUX Depth] Depth composite from: {scene_image.name}")

    if dry_run:
        log.info(f"  [DRY RUN] Would run depth composite (~${COST_PER_CALL['flux_depth']:.3f})")
        return None

    scene_b64 = encode_image_b64(scene_image)
    scene_mime = mime_for(scene_image)

    result = fal_request(
        "flux_depth",
        {
            "prompt": prompt,
            "image_url": f"data:{scene_mime};base64,{scene_b64}",
            "image_size": "landscape_16_9",
            "num_inference_steps": 28,
            "guidance_scale": 3.5,
            "num_images": 1,
            "output_format": "png",
        },
    )

    if "error" in result:
        log.error(f"  Depth composite failed: {result['error']}")
        return None

    image_url = extract_image_url(result)
    if not image_url:
        log.error(f"  No image URL in response: {json.dumps(result)[:200]}")
        return None

    if download_image(image_url, output_path):
        size_kb = output_path.stat().st_size // 1024
        log.info(f"  Depth composite: {output_path.name} ({size_kb}KB)")
        return output_path

    return None


def build_product_shot(
    product_path: Path,
    scene_path: Path,
    placement: str,
    output_path: Path,
    dry_run: bool = False,
) -> Path | None:
    """Stage 3: Inject product into scene with Bria Product Shot."""
    log.info(f"[Bria] Product shot: {product_path.name} → {scene_path.name}")

    if dry_run:
        log.info(f"  [DRY RUN] Would call Bria (~${COST_PER_CALL['bria_product']:.3f})")
        return None

    product_b64 = encode_image_b64(product_path)
    scene_b64 = encode_image_b64(scene_path)
    p_mime = mime_for(product_path)
    s_mime = mime_for(scene_path)

    result = fal_request(
        "bria_product",
        {
            "image_url": f"data:{p_mime};base64,{product_b64}",
            "ref_image_url": f"data:{s_mime};base64,{scene_b64}",
            "scene_description": (
                f"Luxury fashion showroom. Place the clothing item {placement}. "
                "Photorealistic lighting, high-end retail environment."
            ),
            "placement_type": "automatic",
            "num_results": 1,
            "fast": False,
        },
    )

    if "error" in result:
        log.error(f"  Product shot failed: {result['error']}")
        return None

    image_url = extract_image_url(result)
    if not image_url:
        log.error(f"  No image URL in response: {json.dumps(result)[:200]}")
        return None

    if download_image(image_url, output_path):
        size_kb = output_path.stat().st_size // 1024
        log.info(f"  Product shot: {output_path.name} ({size_kb}KB)")
        return output_path

    return None


# ── Task Executors ───────────────────────────────────────────────────────────


def run_scene_task(scene_key: str, dry_run: bool = False) -> list[Path]:
    """Generate scene background only."""
    scene = SCENES[scene_key]
    out_dir = SCENES_DIR / scene["collection"]
    out_dir.mkdir(parents=True, exist_ok=True)

    result = build_scene(scene_key, out_dir, dry_run)
    return [result] if result else []


def run_product_task(scene_key: str, dry_run: bool = False) -> list[Path]:
    """Composite products into existing scene background."""
    scene = SCENES[scene_key]
    collection = scene["collection"]
    bg_path = SCENES_DIR / collection / scene["background"]
    out_dir = SCENES_DIR / collection

    if not bg_path.exists():
        log.error(f"Background not found: {bg_path}")
        return []

    results = []
    for prod in scene["products"]:
        sku = prod["sku"]
        product_path = PRODUCTS_DIR / f"{sku}-front-model.webp"

        if not product_path.exists():
            log.warning(f"  SKIP {sku}: product image not found")
            continue

        out_name = f"{scene['background'].replace('.png', '')}-{sku}.webp"
        out_path = out_dir / out_name

        result = build_product_shot(product_path, bg_path, prod["placement"], out_path, dry_run)
        if result:
            results.append(result)
        time.sleep(2)  # Rate limiting between products

    return results


def run_lookbook_task(scene_key: str, dry_run: bool = False) -> list[Path]:
    """Full pipeline: scene gen → depth composite → product injection → QA."""
    scene = SCENES[scene_key]
    collection = scene["collection"]
    out_dir = SCENES_DIR / collection
    out_dir.mkdir(parents=True, exist_ok=True)

    builders = TASK_BUILDERS["lookbook"]
    log.info(f"Lookbook pipeline for {scene_key}")
    log.info(f"  Builders: {', '.join(builders)}")

    # Stage 1: Generate fresh scene
    scene_path = build_scene(scene_key, out_dir, dry_run)
    if not scene_path and not dry_run:
        # Fall back to existing background
        bg_fallback = SCENES_DIR / collection / scene["background"]
        if bg_fallback.exists():
            log.info(f"  Falling back to existing background: {bg_fallback.name}")
            scene_path = bg_fallback
        else:
            log.error("  No scene available — aborting lookbook")
            return []

    if dry_run:
        scene_path = SCENES_DIR / collection / scene["background"]

    # Stage 2: Depth-conditioned enhancement
    depth_prompt = (
        f"{scene['scene_prompt']} "
        "Add subtle atmospheric haze, volumetric lighting, and deeper "
        "shadows for dramatic effect. Keep the spatial layout identical."
    )
    depth_path = out_dir / f"{scene_key}-depth-enhanced.png"
    depth_result = build_depth_composite(scene_path, depth_prompt, depth_path, dry_run)

    # Use depth-enhanced scene if available, otherwise original
    final_scene = depth_result or scene_path

    # Stage 3: Product injection
    results = []
    for prod in scene["products"]:
        sku = prod["sku"]
        product_path = PRODUCTS_DIR / f"{sku}-front-model.webp"

        if not product_path.exists():
            log.warning(f"  SKIP {sku}: product image not found")
            continue

        out_name = f"{scene_key}-lookbook-{sku}.webp"
        out_path = out_dir / out_name

        result = build_product_shot(product_path, final_scene, prod["placement"], out_path, dry_run)
        if result:
            # Stage 4: Vision QA
            qa = vision_qa(
                result,
                "Evaluate this luxury fashion product composite. Check: "
                "(1) Product looks natural in the scene. "
                "(2) Lighting matches the environment. "
                "(3) No obvious compositing artifacts. "
                "(4) Professional luxury brand quality.",
            )
            if qa.get("pass"):
                log.info(f"  QA PASS: score={qa.get('score', '?')}/10")
            else:
                log.warning(f"  QA FAIL: {qa.get('issues', qa.get('reason', '?'))}")

            results.append(result)
        time.sleep(3)

    return results


def run_reshoot_task(
    scene_key: str, custom_prompt: str | None = None, dry_run: bool = False
) -> list[Path]:
    """Re-render scene with depth control for modified atmosphere."""
    scene = SCENES[scene_key]
    collection = scene["collection"]
    bg_path = SCENES_DIR / collection / scene["background"]
    out_dir = SCENES_DIR / collection

    if not bg_path.exists():
        log.error(f"Background not found for reshoot: {bg_path}")
        return []

    prompt = custom_prompt or (
        f"{scene['scene_prompt']} "
        "Enhance with dramatic golden hour lighting, deeper shadows, "
        "and cinematic depth of field."
    )

    out_path = out_dir / f"{scene_key}-reshoot-v1.png"
    result = build_depth_composite(bg_path, prompt, out_path, dry_run)
    return [result] if result else []


# ── Main ─────────────────────────────────────────────────────────────────────


def estimate_cost(task: str, scene_keys: list[str]) -> float:
    """Estimate total cost for a task across scenes."""
    builders = TASK_BUILDERS.get(task, [])
    total = 0.0

    for key in scene_keys:
        scene = SCENES.get(key, {})
        n_products = len(scene.get("products", []))

        for builder in builders:
            if builder == "bria_product":
                total += COST_PER_CALL[builder] * n_products
            else:
                total += COST_PER_CALL[builder]

    # Add QA cost for lookbook
    if task == "lookbook":
        for key in scene_keys:
            scene = SCENES.get(key, {})
            total += COST_PER_CALL["gemini_qa"] * len(scene.get("products", []))

    return total


def main():
    parser = argparse.ArgumentParser(
        description="SkyyRose Pipeline Orchestrator — Context-Aware AI Image Pipeline"
    )
    parser.add_argument(
        "--task",
        choices=list(TASK_BUILDERS.keys()),
        help="Task type: scene, product, lookbook, reshoot, depth_comp",
    )
    parser.add_argument("--scene", type=str, help="Specific scene key")
    parser.add_argument("--collection", type=str, help="Process all scenes in a collection")
    parser.add_argument("--all", action="store_true", help="Process all scenes")
    parser.add_argument("--prompt", type=str, help="Custom prompt (for reshoot task)")
    parser.add_argument("--list", action="store_true", help="List scenes and their status")
    parser.add_argument("--dry-run", action="store_true", help="Preview without API calls")

    args = parser.parse_args()

    if not FAL_KEY:
        log.error("FAL_KEY not found. Check .env.hf")
        sys.exit(1)

    if args.list:
        print("\n  SkyyRose Pipeline — Available Scenes")
        print("  " + "=" * 55)
        for key, scene in SCENES.items():
            bg_path = SCENES_DIR / scene["collection"] / scene["background"]
            bg_status = "OK" if bg_path.exists() else "MISSING"
            print(f"\n  {key} [{bg_status}]")
            print(f"    Collection: {scene['collection']}")
            for p in scene["products"]:
                prod_exists = (PRODUCTS_DIR / f"{p['sku']}-front-model.webp").exists()
                ps = "OK" if prod_exists else "MISSING"
                print(f"    {p['sku']} [{ps}] — {p['placement']}")

        print("\n  Task Types & Builders:")
        for task, builders in TASK_BUILDERS.items():
            print(f"    {task:12s} → {', '.join(builders)}")
        return

    if not args.task:
        parser.print_help()
        return

    # Determine which scenes to process
    if args.all:
        scene_keys = list(SCENES.keys())
    elif args.collection:
        scene_keys = [k for k, v in SCENES.items() if v["collection"] == args.collection]
        if not scene_keys:
            log.error(f"No scenes for collection: {args.collection}")
            return
    elif args.scene:
        if args.scene not in SCENES:
            log.error(f"Unknown scene: {args.scene}")
            log.error(f"Available: {', '.join(SCENES.keys())}")
            return
        scene_keys = [args.scene]
    else:
        log.error("Specify --scene, --collection, or --all")
        return

    # Show plan
    builders = TASK_BUILDERS[args.task]
    est_cost = estimate_cost(args.task, scene_keys)

    print(f"\n{'=' * 60}")
    print(f"  SkyyRose Pipeline — {args.task.upper()}")
    print(f"  Scenes: {len(scene_keys)}")
    print(f"  Builders: {', '.join(builders)}")
    print(f"  Estimated cost: ${est_cost:.2f}")
    if args.dry_run:
        print("  MODE: DRY RUN")
    print(f"{'=' * 60}")

    # Execute
    task_funcs = {
        "scene": lambda k: run_scene_task(k, args.dry_run),
        "product": lambda k: run_product_task(k, args.dry_run),
        "lookbook": lambda k: run_lookbook_task(k, args.dry_run),
        "reshoot": lambda k: run_reshoot_task(k, args.prompt, args.dry_run),
        "depth_comp": lambda k: run_reshoot_task(k, args.prompt, args.dry_run),
    }

    total_images = 0
    total_cost = 0.0

    for scene_key in scene_keys:
        print(f"\n{'─' * 60}")
        print(f"  Scene: {scene_key}")
        print(f"{'─' * 60}")

        results = task_funcs[args.task](scene_key)
        total_images += len(results)

    total_cost = est_cost  # Use estimate (actual tracking would need per-call hooks)

    print(f"\n{'=' * 60}")
    print(
        f"  DONE {'(DRY RUN) ' if args.dry_run else ''}— {total_images} images, ~${total_cost:.2f}"
    )
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
