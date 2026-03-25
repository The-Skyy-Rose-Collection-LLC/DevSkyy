#!/usr/bin/env python3
"""Nano Banana Composite v2 — 6-Provider AI Branding Pipeline.

Industry-grade composite pipeline that fixes AI-generated product logos with
material-accurate branding. Uses smart routing across 6 image models + visual QA.

Architecture:
    ORCHESTRATION: Claude Opus 4.6 (prompt engineering) + Gemini 3.1 Pro (visual QA)
    VISION QA:     Gemini 3 Flash (fast gate) → Gemini 2.5 Pro (deep analysis)
    PROVIDERS:
        L1: OpenAI GPT Image 1.5   — best overall editor, text rendering
        L2: Reve (AIML API)        — photorealism, fabric textures, 98% text accuracy
        L3: fal FLUX Kontext       — reference-guided inpainting (proven)
        L4: Ideogram V3 (fal)      — text rendering specialist, mask inpainting
        L5: Replicate FLUX Fill    — text-guided fallback (HTTP API)
        L6: fal FLUX Fill Pro      — final fallback

    SMART ROUTING: Products are routed to the best provider based on treatment type.
        - Fabric textures (embossed, chenille, embroidered) → Reve first
        - Text-heavy (sublimation, numbers) → GPT Image first
        - Default → GPT Image first (best overall)

Usage:
    python scripts/nano-banana-composite.py                     # All products
    python scripts/nano-banana-composite.py --sku br-001        # Single SKU
    python scripts/nano-banana-composite.py --detect-only       # Logo detection only
    python scripts/nano-banana-composite.py --provider gpt      # Force specific provider
    python scripts/nano-banana-composite.py --no-qa             # Skip vision QA

Requires in .env.hf:
    GOOGLE_API_KEY, FAL_KEY, REPLICATE_API_TOKEN, OPENAI_API_KEY, AIML_API_KEY
"""

import argparse
import base64
import csv as _csv
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
log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = (
    PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products"
)
MASKS_CACHE = PROJECT_ROOT / "scripts" / "nano-banana-masks.json"
RESULTS_PATH = PROJECT_ROOT / "scripts" / "nano-banana-composite-results.json"

MIN_FILE_SIZE_KB = 50
MAX_RETRIES = 2


# ── Provider Registry ────────────────────────────────────────────────────────

PROVIDERS = {
    "gpt": {"name": "GPT Image 1.5", "tier": 1, "supports_mask": True, "supports_ref": True},
    "reve": {"name": "Reve (AIML)", "tier": 2, "supports_mask": False, "supports_ref": True},
    "kontext": {"name": "FLUX Kontext", "tier": 3, "supports_mask": True, "supports_ref": True},
    "ideogram": {"name": "Ideogram V3", "tier": 4, "supports_mask": True, "supports_ref": False},
    "replicate": {
        "name": "FLUX Fill (Replicate)",
        "tier": 5,
        "supports_mask": True,
        "supports_ref": False,
    },
    "fal-fill": {
        "name": "FLUX Fill (fal)",
        "tier": 6,
        "supports_mask": True,
        "supports_ref": False,
    },
}

# Treatment keywords → preferred provider order
ROUTING_RULES = {
    # Fabric texture specialists — Reve excels here
    "fabric": {
        "keywords": ["embossed", "chenille", "embroidered", "sherpa", "fleece", "wool"],
        "order": ["reve", "gpt", "kontext", "ideogram", "replicate", "fal-fill"],
    },
    # Text rendering — GPT Image + Ideogram lead
    "text": {
        "keywords": ["sublimation", "number", "alternating", "rose-filled"],
        "order": ["gpt", "ideogram", "reve", "kontext", "replicate", "fal-fill"],
    },
    # Screen print — standard ordering
    "print": {
        "keywords": ["screen-print", "woven label"],
        "order": ["gpt", "kontext", "reve", "ideogram", "replicate", "fal-fill"],
    },
}

# Default ordering when no routing rule matches
DEFAULT_ORDER = ["gpt", "reve", "kontext", "ideogram", "replicate", "fal-fill"]


# ── Product catalog ──────────────────────────────────────────────────────────
# Composite-pipeline treatment descriptions — provider routing depends on these.
# Name + source image are loaded from data/product-catalog.csv; treatment is
# pipeline-specific and stays here as augmentation.

_TREATMENTS: dict[str, str] = {
    # Black Rose
    "br-001": "embossed — pressed into fabric creating a raised, dimensional rose texture with subtle shadow depth",
    "br-002": "silicone rubber cut-out — raised 3D rubber logo with clean-cut edges standing proud of the black fabric",
    "br-003": "sublimation print with rose-filled alternating numbers",
    "br-003-oakland": "sublimation print with rose-filled alternating numbers — Oakland colorway",
    "br-003-giants": "sublimation print with rose-filled alternating numbers — Giants black/orange colorway",
    "br-003-white": "sublimation print with rose-filled alternating numbers — white colorway",
    "br-004": "embossed — pressed into hoodie fabric with dimensional depth and shadow",
    "br-005": "embossed — pressed into fabric with subtle dimensional depth",
    "br-006": "embroidered patch on sherpa fleece texture",
    "br-007": "screen-printed logo on mesh athletic fabric",
    "br-008": "sublimation print with rose-filled numbers on red athletic mesh — SF 49ers inspired, 80-piece exclusive",
    "br-009": "sublimation print with rose-filled numbers on white mesh — LAST OAKLAND edition",
    "br-010": "sublimation print with Bay Area graphics on mesh basketball jersey — THE BAY gold text",
    "br-011": "sublimation print with teal rose crest on hooded hockey jersey — San Jose Sharks inspired",
    # Love Hurts
    "lh-002": "embroidered heart-and-thorns logo on athletic fabric",
    "lh-003": "sublimation print with heart motif on mesh fabric",
    "lh-004": "chenille patch letters and embroidered logo on wool/leather varsity jacket",
    "lh-006": "embroidered logo on fanny pack nylon",
    # Signature
    "sg-001": "screen-printed logo on cotton — Bay Bridge shorts",
    "sg-002": "screen-printed golden logo on black cotton shirt",
    "sg-003": "screen-printed SkyyRose script logo on cotton shorts — Stay Golden",
    "sg-004": "embroidered SkyyRose logo on heavyweight cotton hoodie",
    "sg-005": "screen-printed gold logo on navy cotton shirt — Bay Bridge",
    "sg-006": "embroidered colorful logo on mint/lavender pastel hoodie",
    "sg-007": "embroidered signature rose on knit beanie",
    "sg-009": "embroidered patch on cream sherpa fleece jacket",
    "sg-011": "woven label tag on white cotton tee",
    "sg-012": "woven label tag on orchid cotton tee",
    "sg-013": "embroidered logo on mint/lavender crewneck",
    "sg-014": "embroidered logo on mint/lavender sweatpants",
    # Kids Capsule
    "kids-001": "screen-printed V-chevron colorblock design on red/black hoodie and jogger set",
    "kids-002": "screen-printed V-chevron colorblock design on purple/black hoodie and jogger set",
}


def _build_catalog() -> dict:
    """Load product catalog from data/product-catalog.csv, overlay composite treatments."""
    catalog: dict = {}
    csv_path = PROJECT_ROOT / "data" / "product-catalog.csv"
    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in _csv.DictReader(f):
            sku = row["sku"].strip()
            if not sku:
                continue
            source = row["render_source_override"].strip()
            if not source:
                slug = row["render_output_slug"].strip() or sku
                source = f"{slug}.jpg"
            catalog[sku] = {
                "name": row["name"].strip(),
                "source": source,
                "treatment": _TREATMENTS.get(sku, "screen-printed logo"),
            }
    return catalog


PRODUCT_CATALOG = _build_catalog()


# ── Environment setup ────────────────────────────────────────────────────────


def load_env():
    """Load API keys from .env.hf."""
    env_path = PROJECT_ROOT / ".env.hf"
    if not env_path.exists():
        log.error("Missing .env.hf — need API keys")
        sys.exit(1)
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        os.environ.setdefault(key.strip(), val.strip())


def upload_to_fal(image_path: Path) -> str:
    """Upload a local image to fal's CDN and return the URL."""
    import fal_client

    return fal_client.upload_file(image_path)


def upload_bytes_to_fal(data: bytes, content_type: str = "image/png") -> str:
    """Upload raw bytes to fal's CDN and return the URL."""
    import fal_client

    return fal_client.upload(data, content_type)


# ── Smart Routing ────────────────────────────────────────────────────────────


def select_providers(treatment: str, forced_provider: str | None = None) -> list[str]:
    """Select provider order based on product treatment type.

    Routes to the best provider for the material/technique. If a provider
    is forced via CLI, it becomes the sole provider.
    """
    if forced_provider:
        if forced_provider in PROVIDERS:
            return [forced_provider]
        log.warning("Unknown provider '%s', using default order", forced_provider)

    treatment_lower = treatment.lower()
    for rule in ROUTING_RULES.values():
        if any(kw in treatment_lower for kw in rule["keywords"]):
            log.info("  Route: %s", " → ".join(rule["order"]))
            return rule["order"]

    log.info("  Route: default (%s)", " → ".join(DEFAULT_ORDER))
    return DEFAULT_ORDER


# ── Step 1: Logo Detection (Gemini Vision) ───────────────────────────────────


def detect_logo_region(
    client,
    image_path: Path,
    product_name: str,
) -> dict | None:
    """Use Gemini Vision to detect the logo bounding box in an AI render.

    Returns: {"x": float, "y": float, "w": float, "h": float} as percentages
    of image dimensions (0.0 to 1.0), or None on failure.
    """
    from google.genai import types
    from PIL import Image

    img = Image.open(image_path).convert("RGB")

    prompt = (
        f"This is a fashion photo of a model wearing a {product_name}. "
        f"Identify the MAIN logo or branding graphic on the garment. "
        f"Return ONLY a JSON object with the bounding box of the logo area "
        f"as percentages of image width and height (0.0 to 1.0): "
        f'{{"x": <left edge>, "y": <top edge>, "w": <width>, "h": <height>}}. '
        f"Be generous with the bounding box — include some padding around the logo. "
        f"Return ONLY the JSON, no explanation."
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[img, prompt],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT"],
            ),
        )
    except Exception as exc:
        log.error("Logo detection failed for %s: %s", image_path.name, exc)
        return None

    if not response or not response.text:
        return None

    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[: text.rfind("```")]
    text = text.strip()

    try:
        bbox = json.loads(text)
        for key in ("x", "y", "w", "h"):
            if key not in bbox:
                log.error("Missing key '%s' in bbox: %s", key, bbox)
                return None
            bbox[key] = float(bbox[key])
            if not (0.0 <= bbox[key] <= 1.0):
                log.warning("Clamping bbox[%s] = %.3f", key, bbox[key])
                bbox[key] = max(0.0, min(1.0, bbox[key]))
        return bbox
    except (json.JSONDecodeError, ValueError) as exc:
        log.error("Failed to parse bbox JSON: %s — raw: %s", exc, text[:200])
        return None


# ── Step 2: Mask Generation (Pillow) ─────────────────────────────────────────


def create_mask(
    image_path: Path,
    bbox: dict,
    feather_px: int = 20,
) -> bytes:
    """Create a binary mask PNG from a bounding box.

    White (255) = logo region to edit, Black (0) = preserve.
    Gaussian-blurred edges for seamless blending.
    Returns PNG bytes.
    """
    from PIL import Image, ImageDraw, ImageFilter

    img = Image.open(image_path)
    w, h = img.size

    x1 = int(bbox["x"] * w)
    y1 = int(bbox["y"] * h)
    x2 = int((bbox["x"] + bbox["w"]) * w)
    y2 = int((bbox["y"] + bbox["h"]) * h)

    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle([x1, y1, x2, y2], fill=255)

    if feather_px > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(radius=feather_px))
        import numpy as np

        arr = np.array(mask)
        arr = np.where(arr > 128, 255, arr * 2).astype(np.uint8)
        mask = Image.fromarray(arr)

    buf = io.BytesIO()
    mask.save(buf, format="PNG")
    return buf.getvalue()


def create_rgba_mask(image_path: Path, bbox: dict, feather_px: int = 20) -> bytes:
    """Create an RGBA mask for OpenAI (transparent = edit region).

    OpenAI convention: transparent pixels (alpha=0) = area to replace.
    Returns RGBA PNG bytes.
    """
    from PIL import Image, ImageDraw, ImageFilter

    img = Image.open(image_path)
    w, h = img.size

    x1 = int(bbox["x"] * w)
    y1 = int(bbox["y"] * h)
    x2 = int((bbox["x"] + bbox["w"]) * w)
    y2 = int((bbox["y"] + bbox["h"]) * h)

    # Start fully opaque (preserve everything)
    mask = Image.new("L", (w, h), 255)
    draw = ImageDraw.Draw(mask)
    # Draw black rectangle where we want to edit (will become transparent)
    draw.rectangle([x1, y1, x2, y2], fill=0)

    if feather_px > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(radius=feather_px))

    # Create RGBA: RGB doesn't matter, only alpha channel
    rgba = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    rgba.putalpha(mask)

    buf = io.BytesIO()
    rgba.save(buf, format="PNG")
    return buf.getvalue()


def create_inverted_mask(image_path: Path, bbox: dict, feather_px: int = 20) -> bytes:
    """Create a mask where BLACK = edit region (for Ideogram).

    Ideogram convention: black = area to edit, white = preserve.
    Returns grayscale PNG bytes.
    """
    from PIL import Image, ImageDraw, ImageFilter

    img = Image.open(image_path)
    w, h = img.size

    x1 = int(bbox["x"] * w)
    y1 = int(bbox["y"] * h)
    x2 = int((bbox["x"] + bbox["w"]) * w)
    y2 = int((bbox["y"] + bbox["h"]) * h)

    # White background (preserve), black rectangle (edit)
    mask = Image.new("L", (w, h), 255)
    draw = ImageDraw.Draw(mask)
    draw.rectangle([x1, y1, x2, y2], fill=0)

    if feather_px > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(radius=feather_px))

    buf = io.BytesIO()
    mask.save(buf, format="PNG")
    return buf.getvalue()


# ── Step 3: Inpainting Providers ─────────────────────────────────────────────


def inpaint_gpt(
    image_path: Path,
    mask_rgba_bytes: bytes,
    prompt: str,
    reference_path: Path | None = None,
) -> bytes | None:
    """L1: OpenAI GPT Image 1.5 — best overall editor.

    Uses RGBA mask (transparent = edit region). Accepts file uploads via
    multipart/form-data. Bypasses OpenAI SDK (broken on Python 3.14) —
    calls the REST API directly with httpx.

    DALL-E 2 requires: square PNG, same dimensions for image+mask, <4MB each.
    gpt-image-1 is more flexible but may not be available on all accounts.
    """
    import httpx

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        log.warning("  GPT skipped: no OPENAI_API_KEY")
        return None

    log.info("  L1: GPT Image (OpenAI REST API — httpx)...")

    try:
        from PIL import Image as PILImage

        src_img = PILImage.open(image_path).convert("RGBA")
        mask_img = PILImage.open(io.BytesIO(mask_rgba_bytes)).convert("RGBA")

        # Try gpt-image-1 first (flexible sizes), then dall-e-2 (square only)
        for model in ("gpt-image-1", "dall-e-2"):
            target_size = (1024, 1024)  # Works for both models

            # Resize image to target
            img_resized = src_img.resize(target_size, PILImage.LANCZOS)
            img_buf = io.BytesIO()
            img_buf_fmt = "PNG"
            img_resized.save(img_buf, format=img_buf_fmt)
            image_bytes = img_buf.getvalue()

            # Resize mask to SAME dimensions as image (critical for DALL-E 2)
            mask_resized = mask_img.resize(target_size, PILImage.LANCZOS)
            mask_buf = io.BytesIO()
            mask_resized.save(mask_buf, format="PNG")
            mask_bytes = mask_buf.getvalue()

            log.info(
                "  Trying %s — image=%dKB mask=%dKB (both %dx%d)",
                model,
                len(image_bytes) // 1024,
                len(mask_bytes) // 1024,
                *target_size,
            )

            files = [
                ("image", ("render.png", image_bytes, "image/png")),
                ("mask", ("mask.png", mask_bytes, "image/png")),
            ]
            data = {
                "model": model,
                "prompt": prompt,
                "size": "1024x1024",
                "response_format": "b64_json",
                "n": "1",
            }

            resp = httpx.post(
                "https://api.openai.com/v1/images/edits",
                headers={"Authorization": f"Bearer {api_key}"},
                files=files,
                data=data,
                timeout=180,
            )

            if resp.status_code == 400 and "invalid_value" in resp.text.lower():
                log.info("  %s not available, trying fallback...", model)
                continue

            if resp.status_code == 400:
                log.warning("  GPT %s failed (%d): %s", model, resp.status_code, resp.text[:300])
                continue  # Try next model instead of giving up

            if not resp.is_success:
                log.warning("  GPT failed (%d): %s", resp.status_code, resp.text[:300])
                return None

            result = resp.json()
            if result.get("data") and result["data"][0].get("b64_json"):
                log.info("  GPT succeeded via model=%s", model)
                return base64.b64decode(result["data"][0]["b64_json"])

    except Exception as exc:
        log.warning("  GPT failed: %s", exc)
    return None


def inpaint_reve(
    image_url: str,
    reference_url: str,
    prompt: str,
) -> bytes | None:
    """L2: Reve via AIML API — photorealism + fabric texture king.

    No mask support. Uses remix mode with reference image for brand guidance.
    Best for: embossed, chenille, embroidered, sherpa textures.

    Two models available:
        reve/edit-image       — single image edit (image_url param)
        reve/remix-edit-image — multi-image remix (image_urls array)
    """
    import httpx

    api_key = os.environ.get("AIML_API_KEY", "")
    if not api_key:
        log.warning("  Reve skipped: no AIML_API_KEY")
        return None

    log.info("  L2: Reve (AIML API — remix with reference)...")

    # Try remix first (uses reference), then single-edit as fallback
    models_payloads = [
        (
            "reve/remix-edit-image",
            {
                "model": "reve/remix-edit-image",
                "image_urls": [image_url, reference_url],
                "prompt": (
                    f"Take the garment from <img>0</img> and replace the logo/branding "
                    f"region with the EXACT logo from <img>1</img>. "
                    f"{prompt} "
                    f"Keep the rest of the image identical. Photorealistic quality."
                ),
                "aspect_ratio": "3:4",
            },
        ),
        (
            "reve/edit-image",
            {
                "model": "reve/edit-image",
                "image_url": image_url,
                "prompt": (
                    f"Replace the logo/branding on this garment with the correct brand logo. "
                    f"{prompt} "
                    f"Photorealistic fabric texture. Keep everything else identical."
                ),
                "aspect_ratio": "3:4",
            },
        ),
    ]

    for model_name, payload in models_payloads:
        try:
            log.info("  Trying %s...", model_name)
            resp = httpx.post(
                "https://api.aimlapi.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=120,
            )

            if resp.status_code == 500 and "api key" in resp.text.lower():
                log.warning("  Reve API key rejected — verify AIML_API_KEY is valid")
                return None  # No point trying fallback with same key

            if not resp.is_success:
                log.warning(
                    "  Reve %s failed (%d): %s", model_name, resp.status_code, resp.text[:300]
                )
                continue  # Try next model

            data = resp.json()
            if data.get("data") and data["data"][0].get("url"):
                img_url = data["data"][0]["url"]
                img_resp = httpx.get(img_url, timeout=30)
                img_resp.raise_for_status()
                log.info("  Reve succeeded via %s", model_name)
                return img_resp.content

        except Exception as exc:
            log.warning("  Reve %s failed: %s", model_name, exc)
    return None


def inpaint_kontext(
    image_url: str,
    mask_url: str,
    reference_url: str,
    prompt: str,
) -> bytes | None:
    """L3: fal FLUX Kontext Inpaint — reference-guided inpainting.

    Takes a REFERENCE IMAGE showing what the logo should actually look like.
    Best quality for mask-based work because the model can SEE the real product.
    """
    import fal_client

    log.info("  L3: fal FLUX Kontext Inpaint (reference-guided)...")
    try:
        result = fal_client.run(
            "fal-ai/flux-kontext-lora/inpaint",
            arguments={
                "image_url": image_url,
                "mask_url": mask_url,
                "reference_image_url": reference_url,
                "prompt": prompt,
                "num_inference_steps": 35,
                "guidance_scale": 3.0,
                "strength": 0.85,
                "output_format": "png",
                "num_images": 1,
            },
        )
        if result and "images" in result and result["images"]:
            img_url = result["images"][0]["url"]
            import httpx

            resp = httpx.get(img_url, timeout=30)
            resp.raise_for_status()
            return resp.content
    except Exception as exc:
        log.warning("  L3 Kontext failed: %s", exc)
    return None


def inpaint_ideogram(
    image_url: str,
    mask_url: str,
    prompt: str,
) -> bytes | None:
    """L4: Ideogram V3 via fal.ai — text rendering specialist.

    Best for products with text/numbers that need crisp rendering.
    Uses fal.ai wrapper (already authenticated via FAL_KEY).
    """
    import fal_client

    log.info("  L4: Ideogram V3 Edit (fal.ai — text specialist)...")
    try:
        result = fal_client.run(
            "fal-ai/ideogram/v3/edit",
            arguments={
                "prompt": prompt,
                "image_url": image_url,
                "mask_url": mask_url,
                "rendering_speed": "BALANCED",
                "num_images": 1,
            },
        )
        if result and "images" in result and result["images"]:
            img_url = result["images"][0]["url"]
            import httpx

            resp = httpx.get(img_url, timeout=30)
            resp.raise_for_status()
            return resp.content
    except Exception as exc:
        log.warning("  L4 Ideogram failed: %s", exc)
    return None


def inpaint_replicate(
    image_url: str,
    mask_url: str,
    prompt: str,
) -> bytes | None:
    """L5: Replicate FLUX Fill Pro via HTTP API — text-guided fallback.

    Uses CDN URLs (not base64) to avoid payload size limits.
    """
    import httpx

    token = os.environ.get("REPLICATE_API_TOKEN", "")
    if not token:
        log.warning("  L5 Replicate skipped: no REPLICATE_API_TOKEN")
        return None

    log.info("  L5: Replicate FLUX Fill Pro (HTTP API)...")

    try:
        resp = httpx.post(
            "https://api.replicate.com/v1/models/black-forest-labs/flux-fill-pro/predictions",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Prefer": "wait",
            },
            json={
                "input": {
                    "image": image_url,
                    "mask": mask_url,
                    "prompt": prompt,
                },
            },
            timeout=120,
        )
        if not resp.is_success:
            log.warning("  L5 Replicate failed (%d): %s", resp.status_code, resp.text[:300])
            return None
        prediction = resp.json()

        poll_url = prediction.get("urls", {}).get("get", "")
        if not poll_url:
            log.warning("  L5: no poll URL in response")
            return None

        for _ in range(60):
            time.sleep(5)
            poll_resp = httpx.get(
                poll_url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )
            poll_resp.raise_for_status()
            status = poll_resp.json()

            if status["status"] == "succeeded":
                output = status.get("output")
                if isinstance(output, list) and output:
                    output = output[0]
                if isinstance(output, str) and output.startswith("http"):
                    img_resp = httpx.get(output, timeout=30)
                    img_resp.raise_for_status()
                    return img_resp.content
                return None
            elif status["status"] == "failed":
                log.warning("  L5 Replicate failed: %s", status.get("error", "unknown"))
                return None

        log.warning("  L5 Replicate timed out")
    except Exception as exc:
        log.warning("  L5 Replicate failed: %s", exc)
    return None


def inpaint_fal_fill(
    image_url: str,
    mask_url: str,
    prompt: str,
) -> bytes | None:
    """L6: fal FLUX Fill Pro — text-guided inpainting (final fallback)."""
    import fal_client

    log.info("  L6: fal FLUX Fill Pro (text-guided — final fallback)...")
    try:
        result = fal_client.run(
            "fal-ai/flux-pro/v1/fill",
            arguments={
                "image_url": image_url,
                "mask_url": mask_url,
                "prompt": prompt,
                "output_format": "png",
                "num_images": 1,
            },
        )
        if result and "images" in result and result["images"]:
            img_url = result["images"][0]["url"]
            import httpx

            resp = httpx.get(img_url, timeout=30)
            resp.raise_for_status()
            return resp.content
    except Exception as exc:
        log.warning("  L6 fal Fill failed: %s", exc)
    return None


# ── Provider dispatch ────────────────────────────────────────────────────────

# Maps provider key → (function, required_args)
PROVIDER_DISPATCH = {
    "gpt": "dispatch_gpt",
    "reve": "dispatch_reve",
    "kontext": "dispatch_kontext",
    "ideogram": "dispatch_ideogram",
    "replicate": "dispatch_replicate",
    "fal-fill": "dispatch_fal_fill",
}


def dispatch_provider(
    provider_key: str,
    *,
    image_path: Path,
    image_url: str,
    mask_url: str,
    mask_rgba_bytes: bytes,
    inverted_mask_url: str,
    reference_url: str,
    reference_path: Path,
    prompt: str,
) -> bytes | None:
    """Dispatch to the correct provider with the right mask format."""
    if provider_key == "gpt":
        return inpaint_gpt(image_path, mask_rgba_bytes, prompt, reference_path)
    elif provider_key == "reve":
        return inpaint_reve(image_url, reference_url, prompt)
    elif provider_key == "kontext":
        return inpaint_kontext(image_url, mask_url, reference_url, prompt)
    elif provider_key == "ideogram":
        # Ideogram uses inverted mask (black = edit)
        return inpaint_ideogram(image_url, inverted_mask_url, prompt)
    elif provider_key == "replicate":
        return inpaint_replicate(image_url, mask_url, prompt)
    elif provider_key == "fal-fill":
        return inpaint_fal_fill(image_url, mask_url, prompt)
    else:
        log.warning("  Unknown provider: %s", provider_key)
        return None


# ── Vision QA (Gemini) ───────────────────────────────────────────────────────


def vision_qa_flash(
    client,
    original_bytes: bytes,
    composite_bytes: bytes,
    product_name: str,
    treatment: str,
) -> dict:
    """Fast QA gate with Gemini 3 Flash.

    Checks: logo present, correct size, material accuracy, text legibility.
    Returns: {"pass": bool, "score": int (0-100), "issues": [str]}
    """
    from google.genai import types
    from PIL import Image

    original = Image.open(io.BytesIO(original_bytes)).convert("RGB")
    composite = Image.open(io.BytesIO(composite_bytes)).convert("RGB")

    prompt = (
        f"Compare these two images of a {product_name}. "
        f"Image 1 is the ORIGINAL AI render. Image 2 is the COMPOSITE with inpainted branding. "
        f"The logo treatment should be: {treatment}. "
        f"Rate the composite on a scale of 0-100 for: "
        f"1) Logo presence and correct placement "
        f"2) Material accuracy (does it look like {treatment}?) "
        f"3) Text legibility (if any text/numbers are present) "
        f"4) Overall quality (blending, lighting match) "
        f"Return ONLY a JSON object: "
        f'{{"pass": true/false, "score": 0-100, "issues": ["issue1", ...]}}'
        f" Pass if score >= 70. Return ONLY the JSON."
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[original, composite, prompt],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT"],
            ),
        )

        if not response or not response.text:
            return {"pass": True, "score": 50, "issues": ["QA response empty"]}

        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[: text.rfind("```")]

        return json.loads(text.strip())
    except Exception as exc:
        log.warning("  QA Flash error: %s", exc)
        return {"pass": True, "score": 50, "issues": [f"QA error: {exc}"]}


def vision_qa_deep(
    client,
    composite_bytes: bytes,
    reference_bytes: bytes,
    product_name: str,
    treatment: str,
) -> dict:
    """Deep analysis with Gemini 2.5 Pro when Flash flags issues.

    Compares composite against the REAL product reference photo.
    Returns specific prompt refinement suggestions.
    """
    from google.genai import types
    from PIL import Image

    composite = Image.open(io.BytesIO(composite_bytes)).convert("RGB")
    reference = Image.open(io.BytesIO(reference_bytes)).convert("RGB")

    prompt = (
        f"Image 1 is an AI composite of a {product_name}. "
        f"Image 2 is the REAL product reference photo. "
        f"The logo treatment should be: {treatment}. "
        f"Analyze the logo/branding area specifically: "
        f"1) Does the logo SHAPE match the reference? "
        f"2) Does the MATERIAL TEXTURE match ({treatment})? "
        f"3) Is text/typography accurate? "
        f"4) Are colors correct? "
        f"Return ONLY a JSON object: "
        f'{{"match_score": 0-100, "shape_ok": bool, "texture_ok": bool, '
        f'"text_ok": bool, "color_ok": bool, '
        f'"prompt_fix": "specific prompt adjustment to improve the result"}}'
        f" Return ONLY the JSON."
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[composite, reference, prompt],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT"],
            ),
        )

        if not response or not response.text:
            return {"match_score": 50, "prompt_fix": ""}

        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[: text.rfind("```")]

        return json.loads(text.strip())
    except Exception as exc:
        log.warning("  QA Deep error: %s", exc)
        return {"match_score": 50, "prompt_fix": ""}


# ── Quality Gate + Post-Processing ───────────────────────────────────────────


def quality_gate(image_bytes: bytes, sku: str) -> bool:
    """Check if composite image passes minimum file size."""
    size_kb = len(image_bytes) / 1024
    if size_kb < MIN_FILE_SIZE_KB:
        log.warning("  REJECT %s: %.1fKB < %dKB min", sku, size_kb, MIN_FILE_SIZE_KB)
        return False
    log.info("  PASS %s: %.1fKB", sku, size_kb)
    return True


def composite_blend(
    original_path: Path,
    result_bytes: bytes,
    bbox: dict,
    feather_px: int = 20,
) -> bytes:
    """Composite: blend the inpainted region back onto the original image.

    This handles GPT Image's soft-mask behavior where the entire image gets
    regenerated. We take only the masked region from the result and blend it
    back onto the untouched original.
    """
    import numpy as np
    from PIL import Image, ImageFilter

    original = Image.open(original_path).convert("RGB")
    result = Image.open(io.BytesIO(result_bytes)).convert("RGB")

    # Resize result to match original if needed
    if result.size != original.size:
        result = result.resize(original.size, Image.LANCZOS)

    w, h = original.size
    x1 = int(bbox["x"] * w)
    y1 = int(bbox["y"] * h)
    x2 = int((bbox["x"] + bbox["w"]) * w)
    y2 = int((bbox["y"] + bbox["h"]) * h)

    # Create soft blend mask
    blend_mask = Image.new("L", (w, h), 0)
    from PIL import ImageDraw

    draw = ImageDraw.Draw(blend_mask)
    draw.rectangle([x1, y1, x2, y2], fill=255)
    if feather_px > 0:
        blend_mask = blend_mask.filter(ImageFilter.GaussianBlur(radius=feather_px))

    # Composite: original * (1 - mask) + result * mask
    orig_arr = np.array(original, dtype=np.float32)
    result_arr = np.array(result, dtype=np.float32)
    mask_arr = np.array(blend_mask, dtype=np.float32) / 255.0
    mask_arr = mask_arr[:, :, np.newaxis]  # Broadcast to RGB

    blended = orig_arr * (1.0 - mask_arr) + result_arr * mask_arr
    blended = np.clip(blended, 0, 255).astype(np.uint8)

    final = Image.fromarray(blended)
    buf = io.BytesIO()
    final.save(buf, format="PNG")
    return buf.getvalue()


def save_as_webp(image_bytes: bytes, out_path: Path, quality: int = 92) -> int:
    """Convert image bytes to WebP and save. Returns file size in bytes."""
    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=quality)
    webp_bytes = buf.getvalue()
    out_path.write_bytes(webp_bytes)
    return len(webp_bytes)


# ── Build inpainting prompts ────────────────────────────────────────────────


def build_prompt(name: str, treatment: str) -> str:
    """Build a material-specific inpainting prompt.

    Claude Opus 4.6 articulated — precise material descriptions that
    guide each provider to render physically accurate branding.
    """
    return (
        f"The logo/branding area of a {name} from SkyyRose luxury streetwear. "
        f"The logo treatment is {treatment}. "
        f"Generate ONLY the logo region with accurate material texture — "
        f"this is NOT a flat print, it has real physical dimensionality. "
        f"The branding must show depth, shadow, and surface interaction with the fabric. "
        f"Match the garment's color, lighting, and camera angle exactly. "
        f"Photorealistic luxury fashion product photography quality."
    )


# ── Main Pipeline ───────────────────────────────────────────────────────────


def run_pipeline(args):
    """Run the full 6-provider composite pipeline."""
    from google import genai

    load_env()
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    # Load cached masks
    masks_cache = {}
    if MASKS_CACHE.exists():
        masks_cache = json.loads(MASKS_CACHE.read_text())

    # Filter products
    skus = [args.sku] if args.sku else sorted(PRODUCT_CATALOG.keys())

    log.info("=" * 60)
    log.info("NANO BANANA COMPOSITE v2 — 6-Provider Pipeline")
    log.info(
        "Products: %d | QA: %s | Max providers: %d",
        len(skus),
        "ON" if not args.no_qa else "OFF",
        args.max_providers,
    )
    log.info("=" * 60)

    all_results = []
    success = 0
    failed = 0

    for i, sku in enumerate(skus, 1):
        info = PRODUCT_CATALOG.get(sku)
        if not info:
            log.warning("[%d/%d] Unknown SKU: %s", i, len(skus), sku)
            continue

        name = info["name"]
        treatment = info["treatment"]
        source_path = PRODUCTS_DIR / info["source"]

        # Find the AI render
        ai_render = PRODUCTS_DIR / f"{sku}-front-model.webp"
        if not ai_render.exists():
            log.warning("[%d/%d] SKIP %s: no AI render", i, len(skus), sku)
            all_results.append({"sku": sku, "name": name, "status": "no_render"})
            continue

        if not source_path.exists():
            log.warning("[%d/%d] SKIP %s: no source image", i, len(skus), sku)
            all_results.append({"sku": sku, "name": name, "status": "no_source"})
            continue

        log.info("[%d/%d] %s — %s", i, len(skus), sku, name)

        # ── Step 1: Logo detection ──
        bbox = masks_cache.get(sku)
        if not bbox:
            log.info("  Detecting logo region...")
            bbox = detect_logo_region(client, ai_render, name)
            if bbox:
                masks_cache[sku] = bbox
                MASKS_CACHE.write_text(json.dumps(masks_cache, indent=2))
                log.info(
                    "  Logo at (%.1f%%, %.1f%%) size %.1f%% x %.1f%%",
                    bbox["x"] * 100,
                    bbox["y"] * 100,
                    bbox["w"] * 100,
                    bbox["h"] * 100,
                )
            else:
                log.error("  Failed to detect logo for %s", sku)
                all_results.append({"sku": sku, "name": name, "status": "no_logo_detected"})
                failed += 1
                continue
        else:
            log.info("  Using cached logo bbox")

        if args.detect_only:
            all_results.append({"sku": sku, "name": name, "status": "detected", "bbox": bbox})
            continue

        # ── Step 2: Generate all mask formats ──
        log.info("  Generating masks (3 formats)...")
        mask_bytes = create_mask(ai_render, bbox)  # White = edit (FLUX/Replicate)
        mask_rgba_bytes = create_rgba_mask(ai_render, bbox)  # Transparent = edit (OpenAI)
        inverted_mask_bytes = create_inverted_mask(ai_render, bbox)  # Black = edit (Ideogram)

        # ── Step 3: Upload images to fal CDN ──
        log.info("  Uploading to fal CDN (image + 2 masks + reference)...")
        image_url = upload_to_fal(ai_render)
        mask_url = upload_bytes_to_fal(mask_bytes, "image/png")
        inverted_mask_url = upload_bytes_to_fal(inverted_mask_bytes, "image/png")
        reference_url = upload_to_fal(source_path)

        prompt = build_prompt(name, treatment)

        # ── Step 4: Smart route + cascade through providers ──
        provider_order = select_providers(treatment, args.provider)
        if args.max_providers:
            provider_order = provider_order[: args.max_providers]

        result_bytes = None
        provider_used = None
        qa = None

        for provider_key in provider_order:
            pinfo = PROVIDERS.get(provider_key, {})
            log.info(
                "  Trying %s (tier %d)...", pinfo.get("name", provider_key), pinfo.get("tier", 0)
            )

            raw_result = dispatch_provider(
                provider_key,
                image_path=ai_render,
                image_url=image_url,
                mask_url=mask_url,
                mask_rgba_bytes=mask_rgba_bytes,
                inverted_mask_url=inverted_mask_url,
                reference_url=reference_url,
                reference_path=source_path,
                prompt=prompt,
            )

            if raw_result and quality_gate(raw_result, sku):
                # Post-process: blend inpainted region onto original
                result_bytes = composite_blend(ai_render, raw_result, bbox)
                provider_used = provider_key

                # ── Vision QA ──
                if not args.no_qa:
                    log.info("  Running Vision QA (Gemini Flash)...")
                    original_bytes = ai_render.read_bytes()
                    qa = vision_qa_flash(client, original_bytes, result_bytes, name, treatment)
                    log.info(
                        "  QA: score=%d pass=%s issues=%s",
                        qa.get("score", 0),
                        qa.get("pass", True),
                        qa.get("issues", []),
                    )

                    if qa.get("score", 100) < 70:
                        # ── Deep QA: get prompt refinement ──
                        log.warning(
                            "  QA FAILED (score %d) — running deep analysis for prompt fix...",
                            qa.get("score", 0),
                        )
                        ref_bytes = source_path.read_bytes()
                        deep = vision_qa_deep(client, result_bytes, ref_bytes, name, treatment)
                        prompt_fix = deep.get("prompt_fix", "")
                        if prompt_fix:
                            log.info("  Deep QA prompt fix: %s", prompt_fix)
                            # Rebuild prompt with QA feedback for next provider
                            issues_text = "; ".join(qa.get("issues", []))
                            prompt = (
                                f"{build_prompt(name, treatment)} "
                                f"CRITICAL: Previous attempt had these issues: {issues_text}. "
                                f"Specific fix needed: {prompt_fix}"
                            )
                            log.info("  Enhanced prompt for next provider")
                        else:
                            # Even without deep fix, add issues to prompt
                            issues_text = "; ".join(qa.get("issues", []))
                            if issues_text:
                                prompt = f"{build_prompt(name, treatment)} IMPORTANT: {issues_text}"
                        result_bytes = None
                        provider_used = None
                        continue

                break  # Success — stop trying providers

            time.sleep(1)  # Brief pause between providers

        # ── Step 5: Save output ──
        if result_bytes:
            out_path = PRODUCTS_DIR / f"{sku}-composite-front.webp"
            size = save_as_webp(result_bytes, out_path)
            tier = PROVIDERS.get(provider_used, {}).get("tier", 0)
            log.info(
                "  SAVED %s (%.0fKB) via %s (tier %d)",
                out_path.name,
                size / 1024,
                PROVIDERS.get(provider_used, {}).get("name", provider_used),
                tier,
            )
            result_entry = {
                "sku": sku,
                "name": name,
                "status": "success",
                "provider": provider_used,
                "tier": tier,
                "size_kb": round(size / 1024, 1),
            }
            if not args.no_qa and qa:
                result_entry["qa_score"] = qa.get("score", 0)
                result_entry["qa_pass"] = qa.get("pass", True)
                result_entry["qa_issues"] = qa.get("issues", [])
            all_results.append(result_entry)
            success += 1
        else:
            log.error("  FAILED %s — all providers exhausted", sku)
            all_results.append({"sku": sku, "name": name, "status": "failed"})
            failed += 1

        # Rate limit between products
        time.sleep(2)

    # ── Summary ──
    log.info("=" * 60)
    log.info("DONE: %d success, %d failed, %d total", success, failed, len(skus))
    if all_results:
        providers_used = {}
        for r in all_results:
            p = r.get("provider")
            if p:
                providers_used[p] = providers_used.get(p, 0) + 1
        if providers_used:
            log.info("Provider breakdown: %s", providers_used)

    RESULTS_PATH.write_text(
        json.dumps(
            {
                "total": len(skus),
                "success": success,
                "failed": failed,
                "results": all_results,
            },
            indent=2,
        )
    )
    log.info("Results → %s", RESULTS_PATH)


def main():
    parser = argparse.ArgumentParser(
        description="Nano Banana Composite v2 — 6-Provider AI Branding Pipeline"
    )
    parser.add_argument(
        "--sku",
        type=str,
        default=None,
        help="Process a single SKU (e.g. br-001)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        choices=list(PROVIDERS.keys()),
        help="Force a specific provider (skip smart routing)",
    )
    parser.add_argument(
        "--max-providers",
        type=int,
        default=6,
        help="Maximum number of providers to try before giving up (default: 6)",
    )
    parser.add_argument(
        "--detect-only",
        action="store_true",
        help="Run logo detection only (no inpainting)",
    )
    parser.add_argument(
        "--no-qa",
        action="store_true",
        help="Skip Gemini vision QA checks",
    )
    parser.add_argument(
        "--no-blend",
        action="store_true",
        help="Skip post-composite blending (save raw provider output)",
    )

    args = parser.parse_args()
    run_pipeline(args)


if __name__ == "__main__":
    main()
