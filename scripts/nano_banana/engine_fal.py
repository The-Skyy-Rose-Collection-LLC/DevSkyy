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


def _fal_available() -> bool:
    """Check if fal_client is installed and API key is set."""
    try:
        import fal_client  # noqa: F401
        import os

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

    Best for fixing logos/text on an otherwise good render.
    Sends the source image as reference and a prompt describing what to fix.

    Args:
        source_path: The image to refine (the AI render with issues)
        prompt: Description of what to fix

    Returns:
        WebP image bytes on success, None on failure.
    """
    from nano_banana.utils import to_webp

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

    try:
        log.info("Refining via FLUX Kontext Pro...")
        result = fal_client.subscribe(
            model,
            arguments={
                "prompt": prompt,
                "image_url": f"data:{mime};base64,{b64}",
            },
        )
    except Exception as exc:
        log.error("Kontext refinement failed: %s", exc)
        return None

    if not result or "images" not in result or not result["images"]:
        log.warning("Empty Kontext response")
        return None

    image_url = result["images"][0].get("url")
    if not image_url:
        return None

    raw_bytes = _download_image(image_url)
    if not raw_bytes:
        return None

    return to_webp(raw_bytes)
