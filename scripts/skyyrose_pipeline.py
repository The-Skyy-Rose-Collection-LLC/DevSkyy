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
    "editorial": ["bria_bg_remove", "fashn_vton", "flux_pro", "flux_depth", "bria_product"],
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
            "crimson and rose-gold light across stone walls. A glowing enchanted "
            "rose floating under a glass dome (Beauty and the Beast style) on "
            "a marble pedestal at center. Rose petals scattered on the floor. "
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


# ── Editorial Scene Definitions ──────────────────────────────────────────────
# Each scene has AI models wearing exact product replicas via virtual try-on.
# Techflat source images from PRODUCTS_DIR are used as garment input.

GARMENT_SOURCES = {
    "br-001": "br-001-techflat-v4.jpg",
    "br-002": "br-002-joggers-source.jpg",
    "br-003": "br-003-jersey-front-techflat.jpg",
    "br-004": "br-004-hoodie-product.jpg",
    "br-005": "br-005-hoodie-ltd-source.jpg",
    "br-006": "br-006-sherpa-product.jpg",
    "br-007": "br-007-shorts-front-source.jpg",
    "br-008": "br-008-hooded-dress.webp",
    "lh-001": "lh-001-fannie-pack-photo.jpg",
    "lh-002": "lh-002-joggers-variants.jpg",
    "lh-003": "lh-003-shorts-front-closeup.jpg",
    "lh-004": "lh-004-varsity-source.jpg",
    "lh-005": "lh-005-bomber.webp",
    "sg-001": "sg-001-bay-set.webp",
    "sg-004": "sg-004-signature-hoodie.webp",
    "sg-005": "sg-005-stay-golden-tee.webp",
    "sg-008": "sg-008-crop-hoodie.webp",
    "sg-009": "sg-009-sherpa-jacket.webp",
    "sg-010": "sg-010-bridge-shorts-variants.jpg",
}

MODEL_PROMPTS = {
    "black-rose": (
        "Full-body fashion model, dark moody studio, dramatic lighting, "
        "gothic luxury streetwear aesthetic, confident pose, standing, "
        "dark background, 4K fashion photography, sharp focus"
    ),
    "love-hurts": (
        "Full-body fashion model, romantic dramatic studio, warm red and "
        "rose-gold lighting, passionate luxury streetwear aesthetic, "
        "confident pose, standing, 4K fashion photography, sharp focus"
    ),
    "signature": (
        "Full-body fashion model, golden hour studio, warm natural lighting, "
        "premium Bay Area streetwear aesthetic, confident urban pose, standing, "
        "clean background, 4K fashion photography, sharp focus"
    ),
}

EDITORIAL_SCENES = {
    "black-rose-rooftop-garden": {
        "models": [
            {
                "id": "br-m1",
                "gender": "male",
                "pose": "standing confidently near lounge chair, left side",
                "position": "full-body model standing left side of scene near furniture",
                "outfit": [
                    {"sku": "br-001", "category": "tops"},
                    {"sku": "br-002", "category": "bottoms"},
                ],
            },
            {
                "id": "br-m2",
                "gender": "female",
                "pose": "walking forward with attitude, center-left",
                "position": "full-body model walking center-left of scene",
                "outfit": [
                    {"sku": "br-004", "category": "tops"},
                    {"sku": "br-007", "category": "bottoms"},
                ],
            },
            {
                "id": "br-m3",
                "gender": "male",
                "pose": "leaning against railing, center-right",
                "position": "full-body model leaning center-right of scene",
                "outfit": [{"sku": "br-006", "category": "tops"}],
            },
            {
                "id": "br-m4",
                "gender": "female",
                "pose": "standing with hand on hip, right side",
                "position": "full-body model standing right side of scene",
                "outfit": [{"sku": "br-008", "category": "one-pieces"}],
            },
        ],
    },
    "love-hurts-cathedral-rose-chamber": {
        "models": [
            {
                "id": "lh-m1",
                "gender": "male",
                "pose": "standing beside enchanted rose dome, center-left",
                "position": "full-body model standing center-left near glass dome",
                "outfit": [
                    {"sku": "lh-004", "category": "tops"},
                    {"sku": "lh-003", "category": "bottoms"},
                ],
            },
            {
                "id": "lh-m2",
                "gender": "female",
                "pose": "leaning against stone archway, right side",
                "position": "full-body model leaning against archway right side",
                "outfit": [
                    {"sku": "lh-005", "category": "tops"},
                    {"sku": "lh-002", "category": "bottoms"},
                ],
            },
            {
                "id": "lh-m3",
                "gender": "female",
                "pose": "walking through cathedral, center",
                "position": "full-body model walking center of scene",
                "outfit": [{"sku": "lh-001", "category": "auto"}],
            },
        ],
    },
    "signature-golden-gate-showroom": {
        "models": [
            {
                "id": "sg-m1",
                "gender": "male",
                "pose": "standing near window with bridge view, left side",
                "position": "full-body model standing left side near windows",
                "outfit": [
                    {"sku": "sg-004", "category": "tops"},
                    {"sku": "sg-010", "category": "bottoms"},
                ],
            },
            {
                "id": "sg-m2",
                "gender": "female",
                "pose": "seated on marble display, center-left",
                "position": "full-body model seated center-left of scene",
                "outfit": [
                    {"sku": "sg-008", "category": "tops"},
                    {"sku": "sg-005", "category": "tops"},
                ],
            },
            {
                "id": "sg-m3",
                "gender": "male",
                "pose": "walking through showroom, center-right",
                "position": "full-body model walking center-right of scene",
                "outfit": [{"sku": "sg-009", "category": "tops"}],
            },
            {
                "id": "sg-m4",
                "gender": "female",
                "pose": "standing by marble pedestal, right side",
                "position": "full-body model standing right side of scene",
                "outfit": [{"sku": "sg-001", "category": "one-pieces"}],
            },
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


# ── Editorial Builders ───────────────────────────────────────────────────────


def remove_background(image_path: Path, output_path: Path, dry_run: bool = False) -> Path | None:
    """Remove background from product techflat using Bria RMBG 2.0."""
    log.info(f"[Bria BG] Removing background: {image_path.name}")

    if dry_run:
        log.info(f"  [DRY RUN] Would remove bg (~${COST_PER_CALL['bria_bg_remove']:.3f})")
        return None

    img_b64 = encode_image_b64(image_path)
    mime = mime_for(image_path)

    result = fal_request(
        "bria_bg_remove",
        {"image_url": f"data:{mime};base64,{img_b64}"},
    )

    if "error" in result:
        log.error(f"  BG removal failed: {result['error']}")
        return None

    image_url = extract_image_url(result)
    if not image_url:
        log.error("  No image URL in BG removal response")
        return None

    if download_image(image_url, output_path):
        size_kb = output_path.stat().st_size // 1024
        log.info(f"  BG removed: {output_path.name} ({size_kb}KB)")
        return output_path

    return None


def generate_model_image(
    gender: str, pose: str, collection: str, output_path: Path, dry_run: bool = False
) -> Path | None:
    """Generate a full-body AI model with FLUX Pro v1.1."""
    log.info(f"[FLUX Pro] Generating {gender} model for {collection}")

    if dry_run:
        log.info(f"  [DRY RUN] Would generate model (~${COST_PER_CALL['flux_pro']:.3f})")
        return None

    base_prompt = MODEL_PROMPTS.get(collection, MODEL_PROMPTS["signature"])
    prompt = (
        f"{base_prompt}, {gender} model, {pose}, "
        "full body visible head to toe, plain neutral background for easy compositing, "
        "no text, no logos, professional editorial fashion photography"
    )

    result = fal_request(
        "flux_pro",
        {
            "prompt": prompt,
            "image_size": "portrait_4_3",
            "num_images": 1,
            "output_format": "png",
            "safety_tolerance": "5",
        },
    )

    if "error" in result:
        log.error(f"  Model generation failed: {result['error']}")
        return None

    image_url = extract_image_url(result)
    if not image_url:
        log.error("  No image URL in model response")
        return None

    if download_image(image_url, output_path):
        size_kb = output_path.stat().st_size // 1024
        log.info(f"  Model generated: {output_path.name} ({size_kb}KB)")
        return output_path

    return None


def virtual_tryon(
    model_path: Path, garment_path: Path, category: str, output_path: Path, dry_run: bool = False
) -> Path | None:
    """Dress AI model in garment using FASHN Virtual Try-On v1.5."""
    log.info(f"[FASHN] Try-on: {garment_path.name} → {model_path.name} ({category})")

    if dry_run:
        log.info(f"  [DRY RUN] Would run VTON (~${COST_PER_CALL['fashn_vton']:.3f})")
        return None

    model_b64 = encode_image_b64(model_path)
    garment_b64 = encode_image_b64(garment_path)
    m_mime = mime_for(model_path)
    g_mime = mime_for(garment_path)

    result = fal_request(
        "fashn_vton",
        {
            "model_image": f"data:{m_mime};base64,{model_b64}",
            "garment_image": f"data:{g_mime};base64,{garment_b64}",
            "category": category,
            "mode": "quality",
            "garment_photo_type": "flat-lay",
            "num_samples": 1,
            "output_format": "png",
        },
    )

    if "error" in result:
        log.error(f"  VTON failed: {result['error']}")
        return None

    image_url = extract_image_url(result)
    if not image_url:
        log.error("  No image URL in VTON response")
        return None

    if download_image(image_url, output_path):
        size_kb = output_path.stat().st_size // 1024
        log.info(f"  Try-on complete: {output_path.name} ({size_kb}KB)")
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


def run_editorial_task(scene_key: str, dry_run: bool = False) -> list[Path]:
    """Multi-model editorial: bg remove → model gen → VTON → scene compose → QA."""
    import shutil

    scene = SCENES[scene_key]
    editorial = EDITORIAL_SCENES.get(scene_key)
    if not editorial:
        log.error(f"No editorial definition for {scene_key}")
        return []

    collection = scene["collection"]
    out_dir = SCENES_DIR / collection
    staging_dir = out_dir / "editorial-staging"
    staging_dir.mkdir(parents=True, exist_ok=True)

    models_def = editorial["models"]
    log.info(f"Editorial pipeline for {scene_key}")
    log.info(f"  Models: {len(models_def)}, Collection: {collection}")

    # Stage 0: Background removal on all garment techflats
    log.info("── Stage 0: Background Removal ──")
    cleaned_garments: dict[str, Path] = {}
    for model_def in models_def:
        for item in model_def["outfit"]:
            sku = item["sku"]
            if sku in cleaned_garments:
                continue
            src_file = GARMENT_SOURCES.get(sku)
            if not src_file:
                log.warning(f"  No garment source for {sku}")
                continue
            src_path = PRODUCTS_DIR / src_file
            if not src_path.exists():
                log.warning(f"  SKIP {sku}: {src_file} not found")
                continue
            clean_path = staging_dir / f"{sku}-clean.png"
            result = remove_background(src_path, clean_path, dry_run)
            if result:
                cleaned_garments[sku] = result
            elif dry_run:
                cleaned_garments[sku] = src_path
            time.sleep(1)

    # Stage 1: Generate scene background
    log.info("── Stage 1: Scene Generation ──")
    scene_path = build_scene(scene_key, out_dir, dry_run)
    if not scene_path and not dry_run:
        bg_fallback = SCENES_DIR / collection / scene["background"]
        if bg_fallback.exists():
            log.info(f"  Falling back to existing background: {bg_fallback.name}")
            scene_path = bg_fallback
        else:
            log.error("  No scene available — aborting editorial")
            return []
    if dry_run:
        scene_path = SCENES_DIR / collection / scene["background"]

    # Stage 2: Depth enhancement
    log.info("── Stage 2: Scene Enhancement ──")
    depth_prompt = (
        f"{scene['scene_prompt']} "
        "Add subtle atmospheric haze, volumetric lighting, and deeper "
        "shadows for dramatic effect. Keep the spatial layout identical."
    )
    depth_path = out_dir / f"{scene_key}-editorial-enhanced.png"
    depth_result = build_depth_composite(scene_path, depth_prompt, depth_path, dry_run)
    final_scene = depth_result or scene_path

    # Stage 3-4: Generate models and dress them
    log.info("── Stage 3-4: Model Generation + Virtual Try-On ──")
    dressed_models: list[dict] = []
    for model_def in models_def:
        mid = model_def["id"]

        # Stage 3: Generate base model
        model_path = staging_dir / f"{mid}-base.png"
        model_result = generate_model_image(
            model_def["gender"], model_def["pose"], collection, model_path, dry_run
        )
        if not model_result and not dry_run:
            log.warning(f"  SKIP {mid}: model generation failed")
            continue
        current_model = model_result or model_path
        time.sleep(2)

        # Stage 4: Virtual try-on for each garment piece
        for item in model_def["outfit"]:
            sku = item["sku"]
            garment = cleaned_garments.get(sku)
            if not garment:
                log.warning(f"  SKIP VTON {sku}: no cleaned garment")
                continue
            if dry_run:
                continue

            vton_path = staging_dir / f"{mid}-vton-{sku}.png"
            vton_result = virtual_tryon(
                current_model, garment, item["category"], vton_path, dry_run
            )
            if vton_result:
                current_model = vton_result
            time.sleep(2)

        dressed_models.append({"id": mid, "path": current_model, "def": model_def})
        log.info(f"  Dressed model {mid}: {len(model_def['outfit'])} garments applied")

    # Stage 5: Compose dressed models into scene
    log.info("── Stage 5: Scene Composition ──")
    results: list[Path] = []
    current_scene = final_scene
    for i, dm in enumerate(dressed_models):
        mid = dm["id"]
        position = dm["def"]["position"]
        out_name = f"{scene_key}-editorial-{mid}.webp"
        out_path = out_dir / out_name

        result = build_product_shot(dm["path"], current_scene, position, out_path, dry_run)
        if result:
            current_scene = result  # Accumulate: next model placed on updated scene
            results.append(result)

            # Stage 6: QA on final composite (last model placed)
            if i == len(dressed_models) - 1:
                log.info("── Stage 6: Quality Assessment ──")
                qa = vision_qa(
                    result,
                    "Evaluate this luxury fashion editorial scene with multiple models. "
                    "Check: (1) Models look natural in the scene. "
                    "(2) Clothing matches the brand aesthetic. "
                    "(3) No compositing artifacts. "
                    "(4) Professional editorial quality. "
                    "(5) Models are full-bodied and properly positioned.",
                )
                if qa.get("pass"):
                    log.info(f"  QA PASS: score={qa.get('score', '?')}/10")
                else:
                    log.warning(f"  QA FAIL: {qa.get('issues', qa.get('reason', '?'))}")
        time.sleep(3)

    # Save final composite with clear name
    if results and current_scene != final_scene and current_scene.exists():
        final_name = f"{scene_key}-editorial-final.webp"
        final_path = out_dir / final_name
        shutil.copy2(current_scene, final_path)
        log.info(f"  Final editorial: {final_name}")
        results.append(final_path)

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

    # Editorial: per-model and per-garment costs
    if task == "editorial":
        total = 0.0
        for key in scene_keys:
            editorial = EDITORIAL_SCENES.get(key, {})
            models = editorial.get("models", [])
            n_models = len(models)
            n_garments = sum(len(m.get("outfit", [])) for m in models)
            # Unique garments for BG removal
            unique_skus = {item["sku"] for m in models for item in m.get("outfit", [])}
            total += COST_PER_CALL["bria_bg_remove"] * len(unique_skus)
            total += COST_PER_CALL["flux_pro"]  # scene gen
            total += COST_PER_CALL["flux_depth"]  # depth enhance
            total += COST_PER_CALL["flux_pro"] * n_models  # model gen
            total += COST_PER_CALL["fashn_vton"] * n_garments  # VTON
            total += COST_PER_CALL["bria_product"] * n_models  # scene compose
            total += COST_PER_CALL["gemini_qa"]  # QA on final

    return total


def main():
    parser = argparse.ArgumentParser(
        description="SkyyRose Pipeline Orchestrator — Context-Aware AI Image Pipeline"
    )
    parser.add_argument(
        "--task",
        choices=list(TASK_BUILDERS.keys()),
        help="Task type: scene, product, lookbook, editorial, reshoot, depth_comp",
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
        "editorial": lambda k: run_editorial_task(k, args.dry_run),
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
