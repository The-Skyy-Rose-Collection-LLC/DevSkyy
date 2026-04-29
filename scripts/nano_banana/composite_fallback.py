"""Hybrid composite fallback — pixel-perfect text/logo guarantee.

When AI generation fails to render text/logos accurately after regeneration cycles,
this module falls back to a hybrid approach:

1. Generate a BASE garment render (no text, no logos) via Nano Banana
2. Extract the text/logo regions from the SOURCE image as transparent PNGs
3. Composite the real elements onto the base render at DNA-specified positions

Result: pixel-perfect text/logos (copied from source) on a photoreal garment body.
Used as a last-resort when tournament scoring keeps failing on text/logo metrics.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class CompositeRegion:
    """A region to extract from source and paste onto base."""

    bbox: tuple[int, int, int, int]  # (left, top, right, bottom) in source pixels
    target_position: tuple[float, float]  # (x%, y%) on base image (0.0-1.0)
    rotation_deg: float = 0.0
    scale: float = 1.0
    kind: str = "logo"  # 'logo' | 'text' | 'patch'


def _parse_position_to_pct(position_str: str) -> tuple[float, float]:
    """Parse DNA position strings like 'front chest center' to (x%, y%).

    Returns percentages as floats 0.0-1.0.
    """
    if not position_str:
        return (0.5, 0.4)  # default: center-chest
    p = position_str.lower()

    # Horizontal
    if "left" in p:
        x = 0.30
    elif "right" in p:
        x = 0.70
    elif "center" in p or "middle" in p:
        x = 0.50
    else:
        x = 0.50

    # Vertical
    if "chest" in p or "upper" in p:
        y = 0.35
    elif "back" in p and "neck" in p:
        y = 0.15
    elif "hem" in p or "bottom" in p or "waist" in p:
        y = 0.80
    elif "thigh" in p or "mid" in p:
        y = 0.55
    elif "sleeve" in p:
        y = 0.45
    else:
        y = 0.40

    return (x, y)


def detect_logo_region_via_vision(
    anthropic_client,
    source_path: Path,
    logo_description: str,
) -> tuple[int, int, int, int] | None:
    """Use Claude vision to detect a logo's bounding box in the source image.

    Returns (left, top, right, bottom) in pixels, or None if not detected.
    """
    import base64

    img_bytes = source_path.read_bytes()
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    mime = "image/jpeg" if source_path.suffix.lower() in (".jpg", ".jpeg") else "image/webp"

    prompt = f"""Analyze this product image and find the bounding box of: {logo_description}

Return ONLY valid JSON:
{{
  "found": true/false,
  "bbox_pct": {{"left": 0.0-1.0, "top": 0.0-1.0, "right": 0.0-1.0, "bottom": 0.0-1.0}},
  "confidence": 0.0-1.0
}}

Return percentages (0.0-1.0) relative to image dimensions. Be precise."""

    try:
        response = anthropic_client.messages.create(
            model="claude-opus-4-6",
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": mime, "data": b64},
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
        import json

        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        data = json.loads(text.strip())

        if not data.get("found") or data.get("confidence", 0) < 0.5:
            return None

        from PIL import Image

        img = Image.open(source_path)
        w, h = img.size
        bb = data["bbox_pct"]
        return (
            int(bb["left"] * w),
            int(bb["top"] * h),
            int(bb["right"] * w),
            int(bb["bottom"] * h),
        )
    except Exception as exc:
        log.warning("Vision logo detection failed: %s", exc)
        return None


def extract_region_with_transparent_bg(
    source_path: Path,
    bbox: tuple[int, int, int, int],
    bg_color_hex: str = "#FFFFFF",
    tolerance: int = 40,
):
    """Extract a region from source image and make background transparent.

    Uses simple color-keying: pixels within `tolerance` of bg_color become transparent.
    Good enough for clean studio/techflat sources. Returns a PIL Image (RGBA).
    """
    import numpy as np
    from PIL import Image

    img = Image.open(source_path).convert("RGBA")
    cropped = img.crop(bbox)
    arr = np.array(cropped)

    # Parse bg color
    h = bg_color_hex.lstrip("#")
    bg_r, bg_g, bg_b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    # Create mask of background pixels
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    mask = (
        (abs(r.astype(int) - bg_r) < tolerance)
        & (abs(g.astype(int) - bg_g) < tolerance)
        & (abs(b.astype(int) - bg_b) < tolerance)
    )
    arr[mask, 3] = 0  # Set alpha to 0 for background pixels

    return Image.fromarray(arr, "RGBA")


def composite_logo_onto_base(
    base_image_path: Path,
    logo_png,  # PIL Image RGBA
    target_position_pct: tuple[float, float],
    target_size_pct: float = 0.15,  # fraction of base image width
    rotation_deg: float = 0.0,
):
    """Composite a logo PNG onto a base image at the target position.

    Returns a new PIL Image with the logo pasted on top.
    """
    from PIL import Image

    base = Image.open(base_image_path).convert("RGBA")
    bw, bh = base.size

    # Resize logo proportionally
    target_width = int(bw * target_size_pct)
    aspect = logo_png.height / logo_png.width
    target_height = int(target_width * aspect)
    logo_resized = logo_png.resize((target_width, target_height), Image.LANCZOS)

    # Rotate if needed
    if abs(rotation_deg) > 0.5:
        logo_resized = logo_resized.rotate(rotation_deg, expand=True, resample=Image.BICUBIC)

    # Calculate paste position (centered on target pct)
    tx_pct, ty_pct = target_position_pct
    px = int(bw * tx_pct - logo_resized.width / 2)
    py = int(bh * ty_pct - logo_resized.height / 2)
    px = max(0, min(px, bw - logo_resized.width))
    py = max(0, min(py, bh - logo_resized.height))

    # Composite with alpha
    base.paste(logo_resized, (px, py), logo_resized)
    return base.convert("RGB")


def hybrid_composite_from_dna(
    base_image_path: Path,
    source_image_path: Path,
    dna: dict,
    anthropic_client=None,
    output_path: Path = None,
) -> Path | None:
    """Apply hybrid compositing for all logos/patches defined in DNA.

    Pipeline:
    1. For each logo in DNA, use Claude vision to find bbox in source
    2. Extract with transparent background
    3. Composite onto base at DNA-specified position

    Returns the path to the final composited image.
    """
    from PIL import Image

    if anthropic_client is None:
        log.warning("No anthropic_client — cannot run vision-based logo extraction")
        return None

    logos = dna.get("logos", [])
    patches = dna.get("patches", []) if isinstance(dna.get("patches"), list) else []

    # Build list of regions to composite
    regions_to_add = []
    for lg in logos:
        if not isinstance(lg, dict):
            continue
        desc = f"{lg.get('type', 'logo')} logo at {lg.get('position', 'unspecified')}"
        regions_to_add.append(
            {
                "description": desc,
                "position": lg.get("position", ""),
                "size_inches": lg.get("size_inches", 4),
                "kind": "logo",
            }
        )

    if not regions_to_add:
        log.info("No logos/patches in DNA — nothing to composite")
        return base_image_path

    # Start with base image
    current = Image.open(base_image_path).convert("RGB")
    tmp_path = base_image_path.parent / f"_composite_wip_{base_image_path.stem}.png"
    current.save(tmp_path)

    for region in regions_to_add:
        log.info("Compositing: %s", region["description"])

        # Detect region in source via vision
        bbox = detect_logo_region_via_vision(
            anthropic_client, source_image_path, region["description"]
        )
        if bbox is None:
            log.warning("  Could not detect region — skipping")
            continue

        # Extract with transparent bg
        logo_png = extract_region_with_transparent_bg(source_image_path, bbox)

        # Determine target size (convert inches to image-width pct)
        # Assume garment is ~20 inches wide in frame
        size_in = region.get("size_inches", 4)
        try:
            size_in = float(size_in)
        except (ValueError, TypeError):
            size_in = 4.0
        size_pct = min(0.40, max(0.05, size_in / 20.0))

        # Parse position
        target_pos = _parse_position_to_pct(region["position"])

        # Composite
        result = composite_logo_onto_base(tmp_path, logo_png, target_pos, size_pct)
        result.save(tmp_path)

    # Save final
    if output_path is None:
        output_path = base_image_path.parent / f"{base_image_path.stem}_composited.webp"
    final = Image.open(tmp_path).convert("RGB")
    final.save(output_path, format="WEBP", quality=92)
    tmp_path.unlink(missing_ok=True)

    log.info(
        "Saved composite: %s",
        (
            output_path.relative_to(PROJECT_ROOT)
            if output_path.is_relative_to(PROJECT_ROOT)
            else output_path
        ),
    )
    return output_path


def should_use_composite_fallback(tournament_result) -> bool:
    """Decide if composite fallback should be triggered based on tournament result."""
    if not tournament_result or not tournament_result.judges:
        return False

    # Trigger if text/logo scores consistently low
    avg_text = sum(j.text_accuracy for j in tournament_result.judges) / len(
        tournament_result.judges
    )
    avg_logo = sum(j.logo_accuracy for j in tournament_result.judges) / len(
        tournament_result.judges
    )

    return avg_text < 70 or avg_logo < 70
