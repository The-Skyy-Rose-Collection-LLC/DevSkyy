"""Shared utilities — image preprocessing, quality gates, file I/O."""

from __future__ import annotations

import io
import logging
from pathlib import Path

log = logging.getLogger(__name__)

ENHANCE_TARGET_PX = 1536
MIN_FILE_SIZE_KB = 15


def enhance_source_image(image_path: Path):
    """Upscale, sharpen, and boost contrast on source image.

    Returns a PIL Image ready to send as reference.
    """
    from PIL import Image, ImageEnhance, ImageFilter

    img = Image.open(image_path).convert("RGB")

    # Upscale short edge to at least ENHANCE_TARGET_PX
    w, h = img.size
    short_edge = min(w, h)
    if short_edge < ENHANCE_TARGET_PX:
        scale = ENHANCE_TARGET_PX / short_edge
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    img = img.filter(ImageFilter.SHARPEN)
    img = ImageEnhance.Contrast(img).enhance(1.15)
    img = ImageEnhance.Color(img).enhance(1.1)

    return img


def quality_gate(image_bytes: bytes, sku: str, view: str) -> bool:
    """Check if generated image passes minimum size requirement."""
    size_kb = len(image_bytes) / 1024
    if size_kb < MIN_FILE_SIZE_KB:
        log.warning("REJECT %s %s: %.1fKB < %dKB minimum", sku, view, size_kb, MIN_FILE_SIZE_KB)
        return False
    log.info("PASS %s %s: %.1fKB", sku, view, size_kb)
    return True


def to_webp(image_bytes: bytes, quality: int = 92) -> bytes:
    """Convert any image bytes to WebP format."""
    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes))
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=quality)
    return buf.getvalue()


def save_image(image_bytes: bytes, output_path: Path) -> None:
    """Save image bytes to disk and log the result."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image_bytes)
    size_kb = len(image_bytes) / 1024
    log.info("Saved %s (%.0fKB)", output_path.name, size_kb)


def get_output_filename(sku: str, view: str, output_slug: str) -> str:
    """Map SKU + view to output filename."""
    if view.startswith("render3d_"):
        suffix = view.replace("render3d_", "")
        return f"{output_slug}-{suffix}-model.webp"
    if view == "branding":
        return f"{output_slug}-branding.webp"
    return f"{output_slug}-{view}-model.webp"
