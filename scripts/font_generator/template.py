"""Generate a printable PNG template whose cells the user fills in by hand.

Each cell carries light-gray guide marks (border, baseline, ghost label) that
``pipeline.py`` strips out via thresholding once the user submits their
filled-in scan.
"""

import hashlib
import json
import math
import string
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DEFAULT_CHARS = string.ascii_uppercase + string.ascii_lowercase + string.digits + ".,!?'-"

# Guide-mark gray. Kept far above pipeline.py's default ink threshold (140)
# so border/baseline/ghost-label pixels never get mistaken for hand-drawn ink.
_GUIDE_GRAY = (210, 210, 210)
_BACKGROUND_WHITE = (255, 255, 255)
_BORDER_INSET = 2
_BASELINE_RATIO = 0.72
_GHOST_FONT_SIZE = 28
_GHOST_MARGIN = 6

_SYSTEM_FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:\\Windows\\Fonts\\arial.ttf",
)


def _load_ghost_font(size: int) -> "ImageFont.FreeTypeFont | ImageFont.ImageFont":
    """Try a handful of common system TTFs; fall back to PIL's bitmap default."""
    for candidate in _SYSTEM_FONT_CANDIDATES:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def generate_template(
    chars: str = DEFAULT_CHARS,
    cols: int = 10,
    cell_size: tuple[int, int] = (240, 240),
) -> tuple[Image.Image, dict]:
    """Returns (template_image, manifest_dict). Does NOT write to disk."""
    if not chars:
        raise ValueError("chars must be a non-empty string")
    if cols < 1:
        raise ValueError("cols must be >= 1")

    cell_w, cell_h = cell_size
    rows = math.ceil(len(chars) / cols)
    image_w = cols * cell_w
    image_h = rows * cell_h

    image = Image.new("RGB", (image_w, image_h), _BACKGROUND_WHITE)
    draw = ImageDraw.Draw(image)
    font = _load_ghost_font(_GHOST_FONT_SIZE)

    cells = []
    for index, char in enumerate(chars):
        col = index % cols
        row = index // cols
        x0 = col * cell_w
        y0 = row * cell_h
        x1 = x0 + cell_w
        y1 = y0 + cell_h

        # Border rectangle inset 2px from the cell's grid lines.
        draw.rectangle(
            [
                x0 + _BORDER_INSET,
                y0 + _BORDER_INSET,
                x1 - _BORDER_INSET - 1,
                y1 - _BORDER_INSET - 1,
            ],
            outline=_GUIDE_GRAY,
            width=1,
        )

        # Baseline guide spanning the inner width of the cell.
        baseline_y = y0 + int(cell_h * _BASELINE_RATIO)
        draw.line(
            [
                (x0 + _BORDER_INSET, baseline_y),
                (x1 - _BORDER_INSET - 1, baseline_y),
            ],
            fill=_GUIDE_GRAY,
            width=1,
        )

        # Ghost label of the target character, top-left corner of the cell.
        draw.text((x0 + _GHOST_MARGIN, y0 + _GHOST_MARGIN), char, fill=_GUIDE_GRAY, font=font)

        cells.append(
            {
                "char": char,
                "codepoint": ord(char),
                "bbox": [x0, y0, x1, y1],
            }
        )

    # Identifies which (chars, cols, cell_size) generated this manifest. Two
    # different --chars strings of the same length can produce an
    # identically-shaped manifest (same image_size/grid) — this fingerprint
    # lets build_font surface that mismatch to the user instead of silently
    # mapping glyphs to the wrong codepoints.
    fingerprint = hashlib.sha256(f"{chars}|{cols}|{cell_w}x{cell_h}".encode()).hexdigest()[:12]

    manifest = {
        "version": 1,
        "chars_fingerprint": fingerprint,
        "image_size": [image_w, image_h],
        "cell_size": [cell_w, cell_h],
        "grid": {"cols": cols, "rows": rows},
        "cells": cells,
    }
    return image, manifest


def save_template(
    out_dir: str | Path,
    chars: str = DEFAULT_CHARS,
    cols: int = 10,
    cell_size: tuple[int, int] = (240, 240),
) -> tuple[Path, Path]:
    """Writes out_dir/template.png and out_dir/manifest.json (creates out_dir if missing). Returns (png_path, manifest_path)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    image, manifest = generate_template(chars=chars, cols=cols, cell_size=cell_size)

    png_path = out_dir / "template.png"
    manifest_path = out_dir / "manifest.json"

    image.save(png_path)
    manifest_path.write_text(json.dumps(manifest, indent=2))

    return png_path, manifest_path
