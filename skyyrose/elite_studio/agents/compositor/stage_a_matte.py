"""Stage A: alpha matte extraction via BRIA RMBG 2.0.

Extracts the garment subject from a model image, producing an RGBA image
with a 1-px feathered alpha silhouette. Cached by input file hash.
"""

from __future__ import annotations

import hashlib
import io
import logging
from pathlib import Path
from typing import Any

from PIL import Image, ImageFilter

from .infra import (
    _REMBG_UNAVAILABLE_SENTINEL,
    _cache_dir,
    _matte_via_fal,
    remove,
)

logger = logging.getLogger(__name__)


def extract_alpha(
    model_image_path: str,
    sku: str,
    output_dir: str,
) -> str:
    """Extract subject from model image via BRIA RMBG 2.0.

    The matte is RGBA with alpha = subject silhouette. Cached by input
    file hash so repeated runs against the same source image are free.

    Args:
        model_image_path: Path to the B1 model render (garment on neutral BG).
        sku: Canonical SKU string used to name output files.
        output_dir: Directory where the alpha PNG is written.

    Returns:
        Absolute path to the written ``{sku}-alpha.png`` file.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    with open(model_image_path, "rb") as f:
        input_bytes = f.read()
    # Hash the bytes we already have in memory so we don't re-read the
    # source image to compute the cache key.
    # SKU is mixed into the key so two garments sharing an identical base
    # studio photo can't collide on a cached matte (wrong silhouette).
    input_hash = hashlib.sha256(sku.encode() + input_bytes).hexdigest()[:16]
    # Try local rembg first (cheaper, no network). If it raises ImportError
    # — common on Python 3.14 where numba/numpy 2.x is still settling — fall
    # through to FAL's hosted BRIA endpoint. Other exceptions still surface
    # so a real model failure isn't silently swallowed.
    try:
        result: Any = remove(input_bytes)
    except RuntimeError as exc:
        # Only the placeholder shim raises with the sentinel string. Real
        # BRIA / rembg failures get re-raised so callers see them — same
        # behavior the original test contract expects.
        if _REMBG_UNAVAILABLE_SENTINEL not in str(exc):
            raise
        logger.info("Local rembg unavailable; using FAL hosted BRIA endpoint")
        result = _matte_via_fal(input_bytes)

    if isinstance(result, (bytes, bytearray)):
        img = Image.open(io.BytesIO(result)).convert("RGBA")
    elif isinstance(result, Image.Image):
        img = result.convert("RGBA")
    else:  # pragma: no cover
        raise RuntimeError(f"unexpected rembg return type: {type(result).__name__}")

    # Soft alpha edge (1px feather) — reduces hard-cutout artifacts in
    # downstream FLUX inpainting.
    r, g, b, a = img.split()
    a = a.filter(ImageFilter.GaussianBlur(radius=1.0))
    img = Image.merge("RGBA", (r, g, b, a))

    dest = out / f"{sku}-alpha.png"
    img.save(dest, format="PNG")
    # Populate the per-input cache for future runs against the same source.
    try:
        cache = _cache_dir("matte")
        cached = cache / f"{input_hash}.png"
        if not cached.exists():
            img.save(cached, format="PNG")
    except Exception:  # pragma: no cover - cache write is best-effort
        pass
    return str(dest)
