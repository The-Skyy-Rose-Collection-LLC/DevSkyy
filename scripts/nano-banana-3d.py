#!/usr/bin/env python3
"""
Nano Banana 3D — SkyyRose 3D Asset Generator

Converts product source images into production-ready GLB 3D models
for web 3D viewers (model-viewer / three.js).

Providers:
  - fal.ai Trellis-2 (primary — best quality, $0.02/gen, 4B params)
  - Replicate Trellis (fallback — direct HTTP API)

Pipeline:
  Source Image → Preprocess → 3D Generation → GLB Export → QA

Outputs:
  assets/3d/{sku}.glb   — Production 3D model
  assets/3d/{sku}-preview.webp — Turntable preview render

Usage:
    source .venv-imagery/bin/activate
    python scripts/nano-banana-3d.py --dry-run
    python scripts/nano-banana-3d.py --sku br-001
    python scripts/nano-banana-3d.py --all
    python scripts/nano-banana-3d.py --provider replicate
    python scripts/nano-banana-3d.py --all --qa
"""

import argparse
import base64
import io
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
log = logging.getLogger("nano-banana-3d")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = (
    PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products"
)
OUTPUT_DIR = PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "3d"

# -- API config ---------------------------------------------------------------

FAL_TRELLIS_MODEL = "fal-ai/trellis-2"
REPLICATE_TRELLIS_MODEL = "firtoz/trellis"
REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"
MESHY_API_URL = "https://api.meshy.ai/openapi/v1/image-to-3d"

MIN_GLB_SIZE_KB = 100  # Reject GLBs smaller than this (likely failed)
MAX_RETRIES = 2
POLL_INTERVAL_SEC = 5
POLL_TIMEOUT_SEC = 300  # 5 min max per generation


# -- Product catalog (shared with nano-banana-vton.py) -----------------------
# Source of truth: products.csv → PRODUCT_CATALOG in nano-banana-vton.py
# This is a lightweight mirror — SKU → source_override only.

PRODUCT_CATALOG = {
    # Black Rose Collection
    "br-001": {
        "name": "BLACK Rose Crewneck",
        "collection": "black-rose",
        "source_override": "br-001-techflat-v4.jpg",
    },
    "br-002": {
        "name": "BLACK Rose Joggers",
        "collection": "black-rose",
        "source_override": "br-002-joggers-source.jpg",
    },
    "br-003": {
        "name": "BLACK is Beautiful Jersey",
        "collection": "black-rose",
        "source_override": "br-003-jersey-front-techflat.jpg",
    },
    "br-004": {
        "name": "BLACK Rose Hoodie",
        "collection": "black-rose",
        "source_override": "br-004-hoodie-product.jpg",
    },
    "br-005": {
        "name": "BLACK Rose Hoodie — Signature Edition",
        "collection": "black-rose",
        "source_override": "br-005-hoodie-ltd-source.jpg",
    },
    "br-006": {
        "name": "BLACK Rose Sherpa Jacket",
        "collection": "black-rose",
        "source_override": "br-006-sherpa-product.jpg",
    },
    "br-007": {
        "name": "BLACK Rose × Love Hurts Basketball Shorts",
        "collection": "black-rose",
        "source_override": "br-007-shorts-front-source.jpg",
    },
    "br-008": {
        "name": "Women's BLACK Rose Hooded Dress",
        "collection": "black-rose",
        "source_override": "br-008-hooded-dress.webp",
    },
    # Love Hurts Collection
    "lh-001": {
        "name": "The Fannie",
        "collection": "love-hurts",
        "source_override": "lh-001-fannie-pack-photo.jpg",
    },
    "lh-002": {
        "name": "Love Hurts Joggers",
        "collection": "love-hurts",
        "source_override": "lh-002-joggers-variants.jpg",
    },
    "lh-003": {
        "name": "Love Hurts Basketball Shorts",
        "collection": "love-hurts",
        "source_override": "lh-003-shorts-front-closeup.jpg",
    },
    "lh-004": {
        "name": "Love Hurts Varsity Jacket",
        "collection": "love-hurts",
        "source_override": "lh-004-varsity-source.jpg",
    },
    "lh-005": {
        "name": "Love Hurts Windbreaker",
        "collection": "love-hurts",
        "source_override": "lh-005-bomber.webp",
    },
    # Signature Collection
    "sg-001": {
        "name": "The Bay Set",
        "collection": "signature",
        "source_override": "sg-001-bay-set.webp",
    },
    "sg-002": {
        "name": "Stay Golden Set",
        "collection": "signature",
        "source_override": "sg-002-techflat-v4.jpg",
    },
    "sg-003": {
        "name": "The Signature Tee",
        "collection": "signature",
        "source_override": "sg-003.webp",
    },
    "sg-004": {
        "name": "The Signature Hoodie",
        "collection": "signature",
        "source_override": "sg-004-signature-hoodie.webp",
    },
    "sg-005": {
        "name": "Stay Golden Tee",
        "collection": "signature",
        "source_override": "sg-005-stay-golden-tee.webp",
    },
    "sg-006": {
        "name": "Mint & Lavender Hoodie",
        "collection": "signature",
        "source_override": "sg-006-hoodie-source.jpg",
    },
    "sg-007": {
        "name": "The Signature Beanie",
        "collection": "signature",
        "source_override": "sg-007-beanie-source.jpg",
    },
    "sg-008": {
        "name": "Signature Crop Hoodie",
        "collection": "signature",
        "source_override": "sg-008-crop-hoodie.webp",
    },
    "sg-009": {
        "name": "The Sherpa Jacket",
        "collection": "signature",
        "source_override": "sg-009-sherpa-jacket.webp",
    },
    "sg-010": {
        "name": "The Bridge Series Shorts",
        "collection": "signature",
        "source_override": "sg-010-bridge-shorts-variants.jpg",
    },
    "sg-011": {
        "name": "Original Label Tee (White)",
        "collection": "signature",
        "source_override": "sg-011-label-tee-white.webp",
    },
    "sg-012": {
        "name": "Original Label Tee (Orchid)",
        "collection": "signature",
        "source_override": "sg-012-label-tee-orchid.webp",
    },
    # Pre-Order Products
    "po-001": {
        "name": "Red #80 Football Jersey",
        "collection": "black-rose",
        "source_override": "br-design-football-jersey-red.jpg",
    },
    "po-002": {
        "name": '"THE BAY" Basketball Tank',
        "collection": "black-rose",
        "source_override": "br-design-basketball-jersey.jpg",
    },
    "po-003": {
        "name": "White #32 Football Jersey",
        "collection": "black-rose",
        "source_override": "br-design-football-jersey-white.jpg",
    },
    "po-004": {
        "name": "Black & Teal Hockey Jersey",
        "collection": "black-rose",
        "source_override": "br-design-hockey-jersey.jpg",
    },
    "po-005": {
        "name": "Purple GG Bridge Mesh Shorts",
        "collection": "signature",
        "source_override": "po-005-bridge-shorts-source.jpg",
    },
    "po-006": {
        "name": "Black Rose Crewneck & Joggers",
        "collection": "black-rose",
        "source_override": "po-006-techflat.jpg",
    },
    "po-007": {
        "name": "Black Rose Beanie",
        "collection": "black-rose",
        "source_override": "po-007-beanie-source.jpg",
    },
    "po-009": {
        "name": "SR Monogram Slides",
        "collection": "black-rose",
        "source_override": "po-009-slides-source.jpg",
    },
    "po-010": {
        "name": "Love Hurts Slides",
        "collection": "love-hurts",
        "source_override": "po-010-slides-source.jpg",
    },
    "po-011": {
        "name": "Black Rose Slides",
        "collection": "black-rose",
        "source_override": "po-011-slides-source.jpg",
    },
}


# -- API key loading ----------------------------------------------------------


def load_env_key(key_name: str) -> str | None:
    """Load API key from environment or .env.hf fallback."""
    val = os.environ.get(key_name)
    if val:
        return val
    env_path = PROJECT_ROOT / ".env.hf"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith(f"{key_name}="):
                val = line.split("=", 1)[1].strip()
                if val:
                    return val
    return None


def get_fal_client():
    """Initialize fal.ai client. Requires FAL_KEY env var."""
    key = load_env_key("FAL_KEY")
    if not key:
        return None
    # fal_client reads FAL_KEY from env
    os.environ["FAL_KEY"] = key
    import fal_client

    return fal_client


def get_replicate_token() -> str | None:
    """Get Replicate API token."""
    return load_env_key("REPLICATE_API_TOKEN")


def get_meshy_token() -> str | None:
    """Get Meshy API key."""
    return load_env_key("MESHY_API_KEY")


def get_openai_client():
    """Create OpenAI client for QA vision checks."""
    key = load_env_key("OPENAI_API_KEY")
    if not key:
        return None
    from openai import OpenAI

    return OpenAI(api_key=key)


# -- Source image handling ----------------------------------------------------


def find_source_image(sku: str) -> Path | None:
    """Find source image for a SKU using explicit override."""
    info = PRODUCT_CATALOG.get(sku, {})
    if "source_override" in info:
        path = PRODUCTS_DIR / info["source_override"]
        if path.exists():
            return path
        log.warning("Source override %s not found for %s", info["source_override"], sku)
    return None


def preprocess_image(image_path: Path) -> bytes:
    """Prepare source image for 3D generation.

    - Convert to PNG (required by most 3D APIs)
    - Center crop to square (better 3D geometry)
    - Ensure white background for clean silhouette
    - Target 1024x1024 for optimal quality
    """
    from PIL import Image

    img = Image.open(image_path).convert("RGBA")
    w, h = img.size

    # Center-crop to square
    short_edge = min(w, h)
    left = (w - short_edge) // 2
    top = (h - short_edge) // 2
    img = img.crop((left, top, left + short_edge, top + short_edge))

    # Resize to 1024x1024
    img = img.resize((1024, 1024), Image.LANCZOS)

    # Composite onto white background
    bg = Image.new("RGBA", (1024, 1024), (255, 255, 255, 255))
    bg.paste(img, (0, 0), img)
    img = bg.convert("RGB")

    # Export as PNG bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def image_to_data_uri(image_bytes: bytes) -> str:
    """Convert image bytes to a data URI for APIs that accept URLs."""
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/png;base64,{b64}"


# -- 3D Generation Providers -------------------------------------------------


def generate_3d_fal(fal_client, image_bytes: bytes, sku: str) -> bytes | None:
    """Generate 3D GLB using fal.ai Trellis-2 (best quality, $0.02/gen).

    Trellis-2 is Microsoft's 4B-parameter model with PBR textures,
    proper topology, and handles thin surfaces/complex shapes.
    """
    import tempfile

    # fal.ai requires a URL or file upload — use file upload
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name

        # Upload image to fal.ai
        image_url = fal_client.upload_file(tmp_path)
        log.info("[fal.ai] Uploaded image for %s: %s", sku, image_url[:60])

        # Run Trellis-2
        result = fal_client.subscribe(
            FAL_TRELLIS_MODEL,
            arguments={
                "image_url": image_url,
            },
        )

        # Extract GLB URL from result
        glb_url = None
        if isinstance(result, dict):
            # Trellis-2 returns model_mesh.url or glb_file.url
            if "model_mesh" in result and result["model_mesh"]:
                glb_url = result["model_mesh"].get("url") or result["model_mesh"]
            elif "glb_file" in result and result["glb_file"]:
                glb_url = result["glb_file"].get("url") or result["glb_file"]
            elif "model_glb" in result and result["model_glb"]:
                glb_url = result["model_glb"].get("url") or result["model_glb"]

        if not glb_url:
            log.warning(
                "[fal.ai] No GLB URL in response for %s. Keys: %s",
                sku,
                list(result.keys()) if isinstance(result, dict) else type(result),
            )
            log.debug("[fal.ai] Full response: %s", json.dumps(result, default=str)[:500])
            return None

        # Download GLB
        import urllib.request

        with urllib.request.urlopen(glb_url) as resp:
            glb_bytes = resp.read()

        log.info("[fal.ai] Downloaded GLB for %s: %.1fKB", sku, len(glb_bytes) / 1024)
        return glb_bytes

    except Exception as exc:
        log.error("[fal.ai] 3D generation failed for %s: %s", sku, exc)
        return None
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)


def generate_3d_replicate(
    replicate_token: str,
    image_bytes: bytes,
    sku: str,
) -> bytes | None:
    """Generate 3D GLB using Replicate Trellis (direct HTTP API).

    Uses REST API directly to avoid SDK compatibility issues with Python 3.14.
    """
    import urllib.request

    headers = {
        "Authorization": f"Bearer {replicate_token}",
        "Content-Type": "application/json",
        "Prefer": "wait",
    }

    # Convert image to data URI
    data_uri = image_to_data_uri(image_bytes)

    # Create prediction
    payload = json.dumps(
        {
            "version": None,
            "input": {
                "image": data_uri,
            },
        }
    ).encode("utf-8")

    # First, get the latest version of the model
    try:
        model_url = f"https://api.replicate.com/v1/models/{REPLICATE_TRELLIS_MODEL}"
        req = urllib.request.Request(model_url, headers=headers, method="GET")
        with urllib.request.urlopen(req) as resp:
            model_info = json.loads(resp.read())
            latest_version = model_info.get("latest_version", {}).get("id")

        if not latest_version:
            log.error("[Replicate] Could not get latest model version")
            return None

        log.info("[Replicate] Using model version: %s", latest_version[:12])

        # Create prediction with version
        payload = json.dumps(
            {
                "version": latest_version,
                "input": {
                    "image": data_uri,
                },
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            REPLICATE_API_URL, data=payload, headers=headers, method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            prediction = json.loads(resp.read())

    except Exception as exc:
        log.error("[Replicate] Failed to create prediction for %s: %s", sku, exc)
        return None

    prediction_id = prediction.get("id")
    status = prediction.get("status")
    log.info("[Replicate] Prediction %s status: %s", prediction_id, status)

    # Poll for completion
    poll_url = prediction.get("urls", {}).get("get", f"{REPLICATE_API_URL}/{prediction_id}")
    elapsed = 0
    while status not in ("succeeded", "failed", "canceled"):
        time.sleep(POLL_INTERVAL_SEC)
        elapsed += POLL_INTERVAL_SEC
        if elapsed > POLL_TIMEOUT_SEC:
            log.error("[Replicate] Timeout after %ds for %s", elapsed, sku)
            return None

        try:
            req = urllib.request.Request(poll_url, headers=headers, method="GET")
            with urllib.request.urlopen(req) as resp:
                prediction = json.loads(resp.read())
            status = prediction.get("status")
            log.info("[Replicate] %s: %s (%ds)", sku, status, elapsed)
        except Exception as exc:
            log.warning("[Replicate] Poll error: %s", exc)

    if status != "succeeded":
        error = prediction.get("error", "unknown error")
        log.error("[Replicate] Failed for %s: %s", sku, error)
        return None

    # Extract GLB URL from output
    output = prediction.get("output")
    glb_url = None

    if isinstance(output, dict):
        glb_url = output.get("mesh") or output.get("glb") or output.get("model")
    elif isinstance(output, str):
        glb_url = output
    elif isinstance(output, list):
        # Some models return a list of URLs
        for item in output:
            if isinstance(item, str) and ".glb" in item:
                glb_url = item
                break
        if not glb_url and output:
            glb_url = output[0] if isinstance(output[0], str) else None

    if not glb_url:
        log.warning("[Replicate] No GLB URL in output for %s: %s", sku, str(output)[:200])
        return None

    # Download GLB
    try:
        with urllib.request.urlopen(glb_url) as resp:
            glb_bytes = resp.read()
        log.info("[Replicate] Downloaded GLB for %s: %.1fKB", sku, len(glb_bytes) / 1024)
        return glb_bytes
    except Exception as exc:
        log.error("[Replicate] Failed to download GLB for %s: %s", sku, exc)
        return None


def generate_3d_meshy(
    meshy_token: str,
    image_bytes: bytes,
    sku: str,
) -> bytes | None:
    """Generate 3D GLB using Meshy AI (highest texture quality, ~$0.10/gen).

    Meshy excels at PBR textures and handles fabric/clothing well.
    Uses direct REST API.
    """
    import urllib.request

    headers = {
        "Authorization": f"Bearer {meshy_token}",
        "Content-Type": "application/json",
    }

    # Meshy accepts image_url (data URI works)
    data_uri = image_to_data_uri(image_bytes)

    payload = json.dumps(
        {
            "image_url": data_uri,
            "should_remesh": True,
            "should_texture": True,
        }
    ).encode("utf-8")

    # Create task
    try:
        req = urllib.request.Request(MESHY_API_URL, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
        task_id = result.get("result")
        if not task_id:
            log.error("[Meshy] No task ID in response: %s", result)
            return None
        log.info("[Meshy] Task created: %s", task_id)
    except Exception as exc:
        log.error("[Meshy] Failed to create task for %s: %s", sku, exc)
        return None

    # Poll for completion
    poll_url = f"{MESHY_API_URL}/{task_id}"
    elapsed = 0
    while True:
        time.sleep(POLL_INTERVAL_SEC)
        elapsed += POLL_INTERVAL_SEC
        if elapsed > POLL_TIMEOUT_SEC:
            log.error("[Meshy] Timeout after %ds for %s", elapsed, sku)
            return None

        try:
            req = urllib.request.Request(poll_url, headers=headers, method="GET")
            with urllib.request.urlopen(req) as resp:
                task = json.loads(resp.read())
            status = task.get("status")
            log.info("[Meshy] %s: %s (%ds)", sku, status, elapsed)

            if status == "SUCCEEDED":
                break
            elif status in ("FAILED", "EXPIRED"):
                log.error(
                    "[Meshy] Task failed for %s: %s",
                    sku,
                    task.get("task_error", {}).get("message", "unknown"),
                )
                return None
        except Exception as exc:
            log.warning("[Meshy] Poll error: %s", exc)

    # Download GLB
    glb_url = task.get("model_urls", {}).get("glb")
    if not glb_url:
        log.warning("[Meshy] No GLB URL in task result for %s", sku)
        return None

    try:
        with urllib.request.urlopen(glb_url) as resp:
            glb_bytes = resp.read()
        log.info("[Meshy] Downloaded GLB for %s: %.1fKB", sku, len(glb_bytes) / 1024)
        return glb_bytes
    except Exception as exc:
        log.error("[Meshy] Failed to download GLB for %s: %s", sku, exc)
        return None


# -- Quality Gate -------------------------------------------------------------


def quality_gate_3d(glb_bytes: bytes, sku: str) -> bool:
    """Check if generated GLB passes minimum quality requirements."""
    size_kb = len(glb_bytes) / 1024
    if size_kb < MIN_GLB_SIZE_KB:
        log.warning("REJECT %s: %.1fKB < %dKB minimum", sku, size_kb, MIN_GLB_SIZE_KB)
        return False

    # Check GLB magic bytes (glTF binary: 0x676C5446)
    if len(glb_bytes) >= 4:
        magic = glb_bytes[:4]
        if magic != b"glTF":
            log.warning("REJECT %s: invalid GLB magic bytes (not glTF)", sku)
            return False

    log.info("PASS %s: %.1fKB, valid GLB", sku, size_kb)
    return True


# -- QA with Vision -----------------------------------------------------------


def qa_check_3d(openai_client, source_path: Path, glb_path: Path, name: str) -> dict:
    """QA check: verify the source image matches what was sent for 3D generation.

    Note: We can't visually inspect the GLB directly, but we CAN verify:
    - Source image was clean and suitable for 3D
    - GLB file size is reasonable
    - Basic metadata checks
    """
    glb_size = glb_path.stat().st_size / 1024

    src_b64 = base64.b64encode(source_path.read_bytes()).decode("utf-8")
    src_mime = "image/jpeg" if source_path.suffix.lower() in (".jpg", ".jpeg") else "image/webp"

    try:
        response = openai_client.responses.create(
            model="gpt-4.1",
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                f"You are evaluating a source image for 3D model generation.\n"
                                f"Product: {name}\n"
                                f"Generated GLB size: {glb_size:.1f}KB\n\n"
                                "Evaluate the source image for 3D suitability. Return JSON:\n"
                                "{\n"
                                '  "suitable_for_3d": true/false,\n'
                                '  "has_clear_silhouette": true/false,\n'
                                '  "single_product": true/false,\n'
                                '  "clean_background": true/false,\n'
                                '  "garment_visible": true/false,\n'
                                '  "issues": ["list of problems"],\n'
                                '  "confidence": 0.0-1.0,\n'
                                '  "notes": "brief assessment"\n'
                                "}\n"
                                "ONLY return JSON."
                            ),
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:{src_mime};base64,{src_b64}",
                        },
                    ],
                }
            ],
        )
    except Exception as exc:
        log.error("QA check failed for %s: %s", name, exc)
        return {"suitable_for_3d": False, "issues": [str(exc)]}

    text = response.output_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]

    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return {"suitable_for_3d": False, "issues": ["Could not parse QA"], "notes": text[:200]}


# -- Main pipeline ------------------------------------------------------------


def process_product(
    sku: str,
    provider: str,
    fal_client=None,
    replicate_token: str | None = None,
    meshy_token: str | None = None,
) -> dict:
    """Generate 3D model for a single product."""
    info = PRODUCT_CATALOG.get(sku, {})
    name = info.get("name", sku)
    result = {"sku": sku, "name": name}

    # Find source
    src = find_source_image(sku)
    if not src:
        log.warning("SKIP %s: no source image", sku)
        result["status"] = "no_source"
        return result

    # Preprocess
    log.info("Preprocessing %s (%s)...", sku, src.name)
    image_bytes = preprocess_image(src)
    log.info("Preprocessed: %dKB PNG", len(image_bytes) // 1024)

    # Generate
    glb_bytes = None
    provider_used = provider

    for attempt in range(1, MAX_RETRIES + 1):
        if provider in ("fal", "auto") and fal_client:
            log.info("[attempt %d] Generating 3D via fal.ai Trellis-2 for %s...", attempt, sku)
            glb_bytes = generate_3d_fal(fal_client, image_bytes, sku)
            provider_used = "fal.ai"

        if not glb_bytes and provider in ("meshy",) and meshy_token:
            log.info("[attempt %d] Generating 3D via Meshy AI for %s...", attempt, sku)
            glb_bytes = generate_3d_meshy(meshy_token, image_bytes, sku)
            provider_used = "meshy"

        if not glb_bytes and provider in ("replicate", "auto") and replicate_token:
            log.info("[attempt %d] Generating 3D via Replicate Trellis for %s...", attempt, sku)
            glb_bytes = generate_3d_replicate(replicate_token, image_bytes, sku)
            provider_used = "replicate"

        if glb_bytes and quality_gate_3d(glb_bytes, sku):
            break
        else:
            glb_bytes = None
            if attempt < MAX_RETRIES:
                log.info("Retry %d/%d for %s...", attempt + 1, MAX_RETRIES, sku)
                time.sleep(3)

    if not glb_bytes:
        log.error("FAILED %s after %d attempts", sku, MAX_RETRIES)
        result["status"] = "failed"
        return result

    # Save GLB
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    glb_path = OUTPUT_DIR / f"{sku}.glb"
    glb_path.write_bytes(glb_bytes)
    size_kb = len(glb_bytes) / 1024
    log.info("SAVED %s (%.1fKB) [%s]", glb_path.name, size_kb, provider_used)

    result["status"] = "success"
    result["provider"] = provider_used
    result["size_kb"] = round(size_kb, 1)
    result["output"] = str(glb_path.relative_to(PROJECT_ROOT))
    return result


# -- CLI commands -------------------------------------------------------------


def cmd_dry_run(args):
    """List all products and source image status for 3D generation."""
    print(f"\n{'SKU':<10} {'Name':<45} {'Source Image':<40} {'Status'}")
    print("-" * 120)

    found = 0
    missing = 0
    existing_3d = 0

    for sku in sorted(PRODUCT_CATALOG.keys()):
        info = PRODUCT_CATALOG[sku]
        src = find_source_image(sku)
        glb_exists = (OUTPUT_DIR / f"{sku}.glb").exists()

        if src:
            src_str = src.name
            status = "HAS 3D" if glb_exists else "READY"
            found += 1
            if glb_exists:
                existing_3d += 1
        else:
            src_str = "---"
            status = "NO SOURCE"
            missing += 1

        print(f"{sku:<10} {info['name']:<45} {src_str:<40} {status}")

    to_generate = found - existing_3d
    print(f"\nTotal: {len(PRODUCT_CATALOG)} | Ready: {found} | Missing: {missing}")
    print(f"Existing 3D: {existing_3d} | To generate: {to_generate}")
    print(f"Output dir: {OUTPUT_DIR}")


def cmd_generate(args):
    """Generate 3D models."""
    provider = args.provider

    # Initialize providers
    fal = None
    replicate_token = None
    meshy_token = None

    if provider in ("fal", "auto"):
        fal = get_fal_client()
        if provider == "fal" and not fal:
            log.error("fal.ai requested but no FAL_KEY. Set it in .env.hf")
            sys.exit(1)

    if provider == "meshy":
        meshy_token = get_meshy_token()
        if not meshy_token:
            log.error("Meshy requested but no MESHY_API_KEY. Set it in .env.hf")
            sys.exit(1)

    if provider in ("replicate", "auto") or (not fal and not meshy_token):
        replicate_token = get_replicate_token()
        if provider == "replicate" and not replicate_token:
            log.error("Replicate requested but no REPLICATE_API_TOKEN.")
            sys.exit(1)

    if not fal and not replicate_token and not meshy_token:
        log.error(
            "No 3D provider available. Set FAL_KEY, REPLICATE_API_TOKEN, or MESHY_API_KEY in .env.hf"
        )
        sys.exit(1)

    # Select products
    if args.sku:
        skus = [args.sku]
    elif args.collection:
        skus = [
            sku
            for sku, info in sorted(PRODUCT_CATALOG.items())
            if info["collection"] == args.collection
        ]
    else:
        skus = sorted(PRODUCT_CATALOG.keys())

    # Filter to only those with source images
    products = []
    for sku in skus:
        src = find_source_image(sku)
        if not src:
            log.warning("SKIP %s: no source image", sku)
            continue
        # Skip if GLB already exists (unless --force)
        glb_path = OUTPUT_DIR / f"{sku}.glb"
        if glb_path.exists() and not args.force:
            log.info("SKIP %s: GLB already exists (use --force to regenerate)", sku)
            continue
        products.append(sku)

    if not products:
        log.info("Nothing to generate. All products have 3D models or no sources.")
        return

    provider_label = {
        "fal": f"fal.ai Trellis-2 ({FAL_TRELLIS_MODEL})",
        "replicate": f"Replicate Trellis ({REPLICATE_TRELLIS_MODEL})",
        "meshy": "Meshy AI (highest texture quality)",
        "auto": "Auto (fal.ai → Replicate fallback)"
        if fal
        else f"Replicate ({REPLICATE_TRELLIS_MODEL})",
    }[provider]

    log.info("Starting 3D generation: %d products, provider=%s", len(products), provider_label)

    all_results = []
    for i, sku in enumerate(products, 1):
        log.info("[%d/%d] Processing %s (%s)", i, len(products), sku, PRODUCT_CATALOG[sku]["name"])
        result = process_product(
            sku,
            provider,
            fal_client=fal,
            replicate_token=replicate_token,
            meshy_token=meshy_token,
        )
        all_results.append(result)

        if i < len(products):
            time.sleep(2)

    # -- QA Pass --
    if args.qa:
        openai_client = get_openai_client()
        if openai_client:
            log.info("=== QA Pass ===")
            for result in all_results:
                if result.get("status") != "success":
                    continue
                sku = result["sku"]
                src = find_source_image(sku)
                glb_path = OUTPUT_DIR / f"{sku}.glb"
                if not src or not glb_path.exists():
                    continue
                qa = qa_check_3d(openai_client, src, glb_path, result["name"])
                suitable = qa.get("suitable_for_3d", False)
                issues = qa.get("issues", [])
                icon = "PASS" if suitable else "WARN"
                print(f"  [{icon}] {sku} — {qa.get('notes', 'no notes')[:60]}")
                result["qa"] = qa
                time.sleep(1)
        else:
            log.warning("No OPENAI_API_KEY — skipping QA pass")

    # -- Summary --
    print("\n" + "=" * 80)
    print("3D GENERATION SUMMARY")
    print("=" * 80)

    counts = {}
    for r in all_results:
        s = r.get("status", "unknown")
        counts[s] = counts.get(s, 0) + 1

    parts = [f"{k.title()}: {v}" for k, v in sorted(counts.items())]
    print(" | ".join(parts))
    print()

    for r in all_results:
        icon = {
            "success": "OK",
            "failed": "FAIL",
            "no_source": "SKIP",
        }.get(r.get("status", "?"), "?")
        size = f"{r['size_kb']}KB" if "size_kb" in r else ""
        prov = r.get("provider", "")
        print(f"  [{icon:>4}] {r['sku']:<10} {r['name']:<40} {size:<10} {prov}")

    # Save results log
    log_path = PROJECT_ROOT / "scripts" / "nano-banana-3d-results.json"
    with open(log_path, "w") as f:
        json.dump(
            {
                "provider": provider,
                "total": len(all_results),
                "results": all_results,
            },
            f,
            indent=2,
        )
    print(f"\nResults saved to {log_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Nano Banana 3D — Generate 3D GLB models for SkyyRose products"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List products and source status without generating",
    )
    parser.add_argument(
        "--sku",
        type=str,
        default=None,
        help="Process a single SKU (e.g. br-001)",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default=None,
        choices=["black-rose", "love-hurts", "signature"],
        help="Process all SKUs in a collection",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="auto",
        choices=["fal", "replicate", "meshy", "auto"],
        help=(
            "3D generation provider: fal (Trellis-2, best quality $0.02/gen), "
            "replicate (Trellis via HTTP API), meshy (Meshy AI, best textures ~$0.10/gen), "
            "auto (fal → replicate fallback)"
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if GLB already exists",
    )
    parser.add_argument(
        "--qa",
        action="store_true",
        help="Run GPT-4.1 vision QA on source images after generation",
    )

    args = parser.parse_args()

    if args.dry_run:
        cmd_dry_run(args)
    else:
        cmd_generate(args)


if __name__ == "__main__":
    main()
