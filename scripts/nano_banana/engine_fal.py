"""fal.ai generation engine — FLUX 2 Pro and Kontext Pro.

Cheaper than Together AI ($0.03/megapixel), access to full FLUX suite
including reference-guided editing via Kontext.

Requires: pip install fal-client
API key: FAL_KEY environment variable (auto-detected by fal_client)
"""

from __future__ import annotations

import base64
import logging
import urllib.request
from pathlib import Path

log = logging.getLogger(__name__)

FLUX_PRO_MODEL = "fal-ai/flux-pro/v1.1"
FLUX_KONTEXT_MODEL = "fal-ai/flux-pro/kontext"

# Kontext Pro's `aspect_ratio` accepts only this fixed enum (verified
# 2026-05-04 against fal.ai/models/fal-ai/flux-pro/kontext docs). We map
# input dimensions to the closest entry to preserve output framing —
# without it, Kontext silently chose ~1:1 and shrank our 2000×1800
# inputs to 1104×944 in the Layer 1 validation run.
_KONTEXT_ASPECT_RATIOS: list[tuple[str, float]] = [
    ("21:9", 21 / 9),
    ("16:9", 16 / 9),
    ("4:3", 4 / 3),
    ("3:2", 3 / 2),
    ("1:1", 1.0),
    ("2:3", 2 / 3),
    ("3:4", 3 / 4),
    ("9:16", 9 / 16),
    ("9:21", 9 / 21),
]


def _closest_kontext_aspect_ratio(width: int, height: int) -> str:
    """Pick the closest Kontext-supported aspect ratio for input dims.

    Compares input ratio against the 9 enum values and returns the
    string with minimum log-ratio distance. Log distance is the right
    metric here (a 2× over-tall mistake is equally bad as 2× over-wide),
    not absolute distance.
    """
    if width <= 0 or height <= 0:
        return "1:1"
    target = width / height
    import math

    best_label = "1:1"
    best_distance = float("inf")
    for label, ratio in _KONTEXT_ASPECT_RATIOS:
        distance = abs(math.log(target / ratio))
        if distance < best_distance:
            best_distance = distance
            best_label = label
    return best_label


def _is_png_bytes(data: bytes) -> bool:
    """Validate PNG magic header. First 8 bytes are 0x89 P N G \\r \\n 0x1a \\n."""
    return len(data) >= 8 and data[:8] == b"\x89PNG\r\n\x1a\n"


def _fal_available() -> bool:
    """Check if fal_client is installed and API key is set."""
    try:
        import os

        import fal_client  # noqa: F401

        return bool(os.getenv("FAL_KEY", "").strip())
    except ImportError:
        return False


def _download_image(url: str) -> bytes | None:
    """Download image from fal.ai result URL."""
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            return resp.read()
    except Exception as exc:
        log.error("Failed to download fal.ai image: %s", exc)
        return None


def generate_flux_fal(
    source_path: Path | None,
    prompt: str,
    *,
    model: str = FLUX_PRO_MODEL,
    width: int = 768,
    height: int = 1024,
    num_inference_steps: int = 28,
    guidance_scale: float = 3.5,
) -> bytes | None:
    """Generate image via FLUX Pro on fal.ai.

    Args:
        source_path: Optional reference image (used as image_url for img2img if model supports it)
        prompt: Generation prompt
        model: fal.ai model endpoint
        width: Output width
        height: Output height

    Returns:
        WebP image bytes on success, None on failure.
    """
    from nano_banana.utils import to_webp

    if not _fal_available():
        log.warning("fal.ai not available (missing fal-client or FAL_KEY)")
        return None

    import fal_client

    arguments = {
        "prompt": prompt,
        "image_size": {"width": width, "height": height},
        "num_inference_steps": num_inference_steps,
        "guidance_scale": guidance_scale,
        "output_format": "jpeg",
        "num_images": 1,
    }

    # If source image provided and model supports image input, include it
    if source_path and source_path.exists() and "kontext" not in model:
        img_bytes = source_path.read_bytes()
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        ext = source_path.suffix.lower()
        mime = (
            "image/jpeg"
            if ext in (".jpg", ".jpeg")
            else "image/png" if ext == ".png" else "image/webp"
        )
        arguments["image_url"] = f"data:{mime};base64,{b64}"

    try:
        log.info("Generating via fal.ai %s (%dx%d)...", model, width, height)
        result = fal_client.subscribe(model, arguments=arguments)
    except Exception as exc:
        log.error("fal.ai API call failed: %s", exc)
        return None

    if not result or "images" not in result or not result["images"]:
        log.warning("Empty fal.ai response")
        return None

    image_url = result["images"][0].get("url")
    if not image_url:
        log.warning("No image URL in fal.ai response")
        return None

    raw_bytes = _download_image(image_url)
    if not raw_bytes:
        return None

    return to_webp(raw_bytes)


def refine_with_kontext(
    source_path: Path,
    prompt: str,
    *,
    model: str = FLUX_KONTEXT_MODEL,
) -> bytes | None:
    """Refine an image using FLUX Kontext Pro — reference-guided editing.

    Best for fixing logos/text on an otherwise good render. Sends the
    source image as reference and a prompt describing what to fix.

    Format/dimension contract (fixed 2026-05-04):
    - Output is **PNG bytes** (Kontext's `output_format` defaults to
      `"jpeg"` if not set; we explicitly request `"png"`).
    - Output **aspect ratio** matches the closest Kontext-supported
      enum to the input image's dimensions (Kontext Pro doesn't accept
      a "match input" option, only the fixed enum).
    - Returns raw bytes from FAL untouched — no `to_webp()` re-encode
      that previously double-corrupted the format. The caller saves
      the bytes; the `.png` extension matches the actual format.

    Args:
        source_path: The image to refine (the AI render with issues).
        prompt: Description of what to fix.

    Returns:
        PNG image bytes on success, None on failure.
    """
    if not _fal_available():
        log.warning("fal.ai not available for Kontext refinement")
        return None

    if not source_path or not source_path.exists():
        log.error("No source image for Kontext refinement")
        return None

    import fal_client

    img_bytes = source_path.read_bytes()
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    ext = source_path.suffix.lower()
    mime = (
        "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png" if ext == ".png" else "image/webp"
    )

    # Compute closest aspect ratio to input image.
    aspect_ratio = "1:1"
    input_dims: tuple[int, int] | None = None
    try:
        from PIL import Image

        with Image.open(source_path) as im:
            input_dims = im.size  # (width, height)
            aspect_ratio = _closest_kontext_aspect_ratio(*im.size)
    except Exception as exc:
        log.warning(
            "Could not read input dimensions from %s; defaulting aspect_ratio=1:1 (%s)",
            source_path.name,
            exc,
        )

    try:
        log.info(
            "Refining via FLUX Kontext Pro (input=%s, aspect=%s, format=png)...",
            input_dims,
            aspect_ratio,
        )
        result = fal_client.subscribe(
            model,
            arguments={
                "prompt": prompt,
                "image_url": f"data:{mime};base64,{b64}",
                "aspect_ratio": aspect_ratio,
                "output_format": "png",
            },
        )
    except Exception as exc:
        log.error("Kontext refinement failed: %s", exc)
        return None

    if not result or "images" not in result or not result["images"]:
        log.warning("Empty Kontext response")
        return None

    image_obj = result["images"][0]
    image_url = image_obj.get("url")
    if not image_url:
        return None

    raw_bytes = _download_image(image_url)
    if not raw_bytes:
        return None

    # Validate the bytes match what we asked for. PNG magic header is
    # 8 bytes; if Kontext returned anything else despite output_format=png,
    # log it loudly so the storefront doesn't ship mislabeled WebP/JPEG.
    if not _is_png_bytes(raw_bytes):
        log.warning(
            "Kontext returned non-PNG bytes despite output_format=png "
            "(first 16 bytes: %s). Check fal_client/Kontext version.",
            raw_bytes[:16].hex(),
        )

    out_w = image_obj.get("width")
    out_h = image_obj.get("height")
    if input_dims and out_w and out_h:
        in_w, in_h = input_dims
        shrink_x = out_w / in_w if in_w else 1.0
        shrink_y = out_h / in_h if in_h else 1.0
        if shrink_x < 0.6 or shrink_y < 0.6:
            log.warning(
                "Kontext output %dx%d is much smaller than input %dx%d "
                "(scale x=%.2f y=%.2f). Storefront images may need upscaling.",
                out_w,
                out_h,
                in_w,
                in_h,
                shrink_x,
                shrink_y,
            )

    return raw_bytes
