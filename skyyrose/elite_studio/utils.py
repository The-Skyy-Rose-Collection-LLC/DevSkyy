"""
Shared utilities for the Elite Studio pipeline.

Pure functions — no side effects, no provider dependencies.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from .config import OVERRIDES_DIR, SOURCE_DIR
from .models import ProductData


def load_product_data(sku: str) -> ProductData:
    """Load product data from override JSON.

    Returns a frozen ProductData dataclass.
    """
    sku = sku.strip().lower()
    override_path = OVERRIDES_DIR / f"{sku}.json"

    if not override_path.exists():
        return ProductData(sku=sku, collection="unknown")

    with open(override_path, "r") as f:
        data = json.load(f)

    return ProductData.from_override(sku, data)


def get_reference_image_path(sku: str, view: str) -> str:
    """Get path to reference product image.

    Source images follow descriptive naming: {sku}-{product-name}-{view}.{ext}
    e.g. br-001-crewneck-front.png, sg-001-bay-set-1.jpg

    Lookup priority:
      1. Exact: {sku}-{view}.{ext}
      2. Glob:  {sku}-*{view}*.{ext}  (matches descriptive names)
      3. Fallback (front only): any {sku}-*.{ext} excluding 'back'
      4. Override referenceImages: check override JSON for explicit paths
    """
    sku = sku.strip().lower()
    product = load_product_data(sku)
    col_dir = SOURCE_DIR / product.collection
    image_exts = {".jpg", ".jpeg", ".png"}

    if col_dir.is_dir():
        # Priority 1: Exact match
        for ext in ("jpg", "jpeg", "png"):
            exact = col_dir / f"{sku}-{view}.{ext}"
            if exact.exists():
                return str(exact)

        # Priority 2: Glob for descriptive names containing view keyword
        view_matches = sorted(col_dir.glob(f"{sku}-*{view}*.*"))
        view_matches = [p for p in view_matches if p.suffix.lower() in image_exts]
        if view_matches:
            return str(view_matches[0])

        # Priority 3: For front view — fall back to any image for this SKU
        if view == "front":
            all_matches = sorted(col_dir.glob(f"{sku}-*.*"))
            all_matches = [
                p
                for p in all_matches
                if p.suffix.lower() in image_exts
                and "back" not in p.stem.lower()
            ]
            if all_matches:
                return str(all_matches[0])

    # Priority 4: Check override's referenceImages field
    for ref_path in product.reference_images:
        full_path = SOURCE_DIR / ref_path
        if full_path.exists():
            return str(full_path)

    return ""


def image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def resize_for_claude(image_path: str, max_size: int = 1568) -> str:
    """Resize and convert image for Claude vision API.

    Returns base64 JPEG string, resized to fit within max_size pixels.
    """
    import io

    from PIL import Image

    img = Image.open(image_path)

    # Convert to RGB if needed
    if img.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(
            img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None
        )
        img = background

    # Resize if too large
    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        new_size = tuple(int(dim * ratio) for dim in img.size)
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    # Convert to JPEG base64
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def discover_all_skus() -> list[str]:
    """Discover all SKUs from the overrides directory."""
    return sorted(p.stem for p in OVERRIDES_DIR.glob("*.json"))
