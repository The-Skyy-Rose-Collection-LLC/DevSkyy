"""Core image generation — one clean function per provider.

Each function takes a client + inputs, returns image bytes or None.
No retry logic inside — the caller (CLI) handles retries.
"""

from __future__ import annotations

import base64
import logging
from pathlib import Path

log = logging.getLogger(__name__)

# -- Model IDs (official Google genai SDK) ------------------------------------
GEMINI_FAST = "gemini-2.5-flash-image"
GEMINI_PRO = "gemini-3-pro-image-preview"
FLUX_MODEL = "black-forest-labs/FLUX.2-pro"
FLUX_FREE = "black-forest-labs/FLUX.1-schnell-Free"
GPT_IMAGE_MODEL = "gpt-image-1.5"


def generate_gemini(
    client,
    source_path: Path | None,
    prompt: str,
    *,
    model: str = GEMINI_FAST,
    aspect_ratio: str = "3:4",
    enhanced: bool = False,
) -> bytes | None:
    """Generate an image using the official Google genai SDK.

    Args:
        client: google.genai.Client instance
        source_path: Reference image (None for text-to-image)
        prompt: Generation prompt
        model: Gemini model ID
        aspect_ratio: Output aspect ratio (3:4 for product shots)
        enhanced: Append extra fidelity constraints on retries

    Returns:
        WebP image bytes on success, None on failure.
    """
    from google.genai import types
    from nano_banana.prompts import ENHANCED_SUFFIX
    from nano_banana.utils import enhance_source_image, to_webp

    full_prompt = prompt
    if enhanced:
        full_prompt += ENHANCED_SUFFIX

    # Build contents: reference image + prompt, or just prompt
    if source_path and source_path.exists():
        src_img = enhance_source_image(source_path)
        contents = [
            "REFERENCE PHOTO of the exact product (study every detail):",
            src_img,
            full_prompt,
        ]
    else:
        contents = [full_prompt]

    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                ),
            ),
        )
    except Exception as exc:
        log.error("Gemini API call failed: %s", exc)
        return None

    if not response or not response.candidates:
        log.warning("Empty response from Gemini")
        return None

    # Extract image bytes from response
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            raw = part.inline_data.data
            if isinstance(raw, str):
                raw = base64.b64decode(raw)
            return to_webp(raw)

    log.warning("No image in Gemini response parts")
    return None


def generate_flux(
    together_client,
    prompt: str,
    *,
    use_free: bool = False,
) -> bytes | None:
    """Generate an image using FLUX via Together AI.

    FLUX excels at text rendering and color fidelity.
    Returns WebP image bytes on success, None on failure.
    """
    from nano_banana.utils import to_webp

    model = FLUX_FREE if use_free else FLUX_MODEL

    try:
        response = together_client.images.generate(
            model=model,
            prompt=prompt,
            width=768,
            height=1024,
            response_format="b64_json",
        )
    except Exception as exc:
        log.error("FLUX API call failed: %s", exc)
        return None

    if not response or not response.data:
        log.warning("Empty FLUX response")
        return None

    img_data = response.data[0]
    raw_bytes = None

    if hasattr(img_data, "b64_json") and img_data.b64_json:
        raw_bytes = base64.b64decode(img_data.b64_json)
    elif hasattr(img_data, "url") and img_data.url:
        import urllib.request

        try:
            with urllib.request.urlopen(img_data.url, timeout=30) as resp:
                raw_bytes = resp.read()
        except Exception as e:
            log.error("FLUX image URL download failed: %s", e)
            return None

    if not raw_bytes:
        log.warning("No image data in FLUX response")
        return None

    return to_webp(raw_bytes)


def generate_gpt(
    openai_client,
    prompt: str,
    source_path: Path | None = None,
) -> bytes | None:
    """Generate an image using GPT-Image-1.5.

    Supports reference-based editing: source photo + instructions.
    Returns WebP image bytes on success, None on failure.
    """
    from nano_banana.utils import to_webp

    kwargs = {
        "model": GPT_IMAGE_MODEL,
        "prompt": prompt,
        "size": "1024x1536",
        "quality": "high",
    }

    # GPT Image 1.5 uses images.edit() for reference-based editing,
    # images.generate() for text-to-image only.
    use_edit = source_path and source_path.exists()

    try:
        if use_edit:
            # Use edit endpoint with reference image as input
            with open(source_path, "rb") as img_file:
                response = openai_client.images.edit(
                    model=GPT_IMAGE_MODEL,
                    image=img_file,
                    prompt=prompt,
                    size="1024x1536",
                )
        else:
            response = openai_client.images.generate(**kwargs)
    except Exception as exc:
        log.error("GPT-Image API call failed: %s", exc)
        return None

    if not response or not response.data:
        log.warning("Empty GPT-Image response")
        return None

    img_data = response.data[0]
    raw_bytes = None

    if hasattr(img_data, "b64_json") and img_data.b64_json:
        raw_bytes = base64.b64decode(img_data.b64_json)
    elif hasattr(img_data, "url") and img_data.url:
        import urllib.request

        try:
            with urllib.request.urlopen(img_data.url, timeout=30) as resp:
                raw_bytes = resp.read()
        except Exception as e:
            log.error("GPT image URL download failed: %s", e)
            return None

    if not raw_bytes:
        return None

    return to_webp(raw_bytes)


def composite_gemini(
    client,
    ai_render_path: Path,
    source_path: Path,
    prompt: str,
    *,
    model: str = GEMINI_FAST,
) -> bytes | None:
    """Composite real branding onto an AI lifestyle shot.

    Sends both images (AI render + real product) to Gemini and asks
    it to fix the branding to match the real product.
    """
    from google.genai import types
    from nano_banana.utils import enhance_source_image, to_webp
    from PIL import Image as PILImage

    ai_img = PILImage.open(ai_render_path).convert("RGB")
    src_img = enhance_source_image(source_path)

    try:
        response = client.models.generate_content(
            model=model,
            contents=[
                "IMAGE 1 — the AI-generated lifestyle photo (keep this composition):",
                ai_img,
                "IMAGE 2 — the REAL product reference (match this branding exactly):",
                src_img,
                prompt,
            ],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            ),
        )
    except Exception as exc:
        log.error("Composite API call failed: %s", exc)
        return None

    if not response or not response.candidates:
        log.warning("Empty composite response")
        return None

    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            raw = part.inline_data.data
            if isinstance(raw, str):
                raw = base64.b64decode(raw)
            return to_webp(raw)

    log.warning("No image in composite response")
    return None
