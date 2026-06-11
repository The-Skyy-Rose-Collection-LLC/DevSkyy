#!/usr/bin/env python3
"""Selective colorway recolor of the canonical three-rose-cluster art.

The base art (``data/brand-logos/three-rose-cluster.jpeg``) is greyscale roses +
saturated green stems/thorns + pale-blue cloud on white. The brand canon recolors
ONLY the rose petals per product (Black Rose = greyscale, sg-002 = purple,
sg-005 = blue, sg-006/sg-014 = lavender/pink). Today that recolor is a text
instruction to the image model with a GREYSCALE reference attached — the model
has to invent the color. This produces colorway-correct REFERENCE variants so
the render attaches a reference that already shows the right color.

Method: recolor only achromatic (grey) mid-value pixels — the rose petals —
leaving the green stems, blue cloud, white ground, and black ink outlines
untouched, and preserving each petal's value (shading depth). Deterministic,
free, no AI. Output is for founder review; it does not enter canon until approved.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent
BASE = (
    REPO_ROOT
    / "wordpress-theme"
    / "skyyrose-flagship"
    / "data"
    / "brand-logos"
    / "three-rose-cluster.jpeg"
)
OUT_DIR = REPO_ROOT / "renders" / "colorway-review"

# (name, PIL hue 0-255, PIL saturation 0-255) — target rose-petal colorways.
COLORWAYS = [
    ("lavender", 195, 70),  # sg-006/sg-014 per the techflat (light purple)
    ("pink", 235, 105),  # sg-006/sg-014 per three-rose-cluster.md (to settle the conflict)
    ("purple", 200, 150),  # sg-002 'Stay Golden' Shirt
    ("blue-cyan", 150, 150),  # sg-005 'Bay Bridge' Shirt
]


# Petal-mask tuning thresholds (all in 0-255 uint8 space).
_CHROMA_ACHROMATIC_CEIL = (
    30  # max chroma to count a pixel as grey (rose petal); green stems exceed it
)
_VALUE_INK_FLOOR = 25  # below this = black ink outline → skip
_VALUE_GROUND_CEIL = 240  # above this = white ground / cloud highlight → skip
_CLOUD_BLUE_OFFSET = 12  # min (B − max(R,G)) to count as pale-blue cloud shading → skip


def _rose_mask(rgb: np.ndarray) -> np.ndarray:
    """True for rose-petal pixels: achromatic (grey), mid value, not blue cloud."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    chroma = rgb.max(-1) - rgb.min(-1)  # uint8, always ≥0 (max≥min) → no underflow
    value = rgb.max(-1)
    grey = chroma < _CHROMA_ACHROMATIC_CEIL
    midval = (value > _VALUE_INK_FLOOR) & (value < _VALUE_GROUND_CEIL)
    bluey = (b.astype(int) - np.maximum(r, g)) > _CLOUD_BLUE_OFFSET
    return grey & midval & ~bluey


def recolor(base_rgb: np.ndarray, mask: np.ndarray, target_h: int, target_s: int) -> Image.Image:
    """Tint the masked (rose-petal) pixels to a colorway, preserving value (shading)."""
    hsv = np.asarray(Image.fromarray(base_rgb, "RGB").convert("HSV")).astype(np.uint8).copy()
    hsv[..., 0][mask] = target_h  # hue → colorway
    hsv[..., 1][mask] = target_s  # saturation → colorway (value preserved = shading)
    return Image.fromarray(hsv, "HSV").convert("RGB")


def _label_font(size: int = 18) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """First available system font, else PIL's default (keeps the sheet OS-portable)."""
    for path in (
        "/System/Library/Fonts/Helvetica.ttc",  # macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux/CI
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def contact_sheet(base: Image.Image, variants: list[tuple[str, Image.Image]]) -> Image.Image:
    """base + variants in a labeled row for one-glance founder review."""
    cell_w, cell_h, pad, label_h = 300, 382, 16, 28
    tiles = [("base (greyscale)", base)] + variants
    sheet_w = len(tiles) * (cell_w + pad) + pad
    sheet = Image.new("RGB", (sheet_w, cell_h + label_h + 2 * pad), "white")
    draw = ImageDraw.Draw(sheet)
    font = _label_font()
    for i, (name, img) in enumerate(tiles):
        x = pad + i * (cell_w + pad)
        thumb = img.copy()
        thumb.thumbnail((cell_w, cell_h))
        sheet.paste(thumb, (x + (cell_w - thumb.width) // 2, pad))
        draw.text((x, cell_h + pad + 4), name, fill="black", font=font)
    return sheet


def main() -> int:
    if not BASE.exists():
        print(f"base art not found: {BASE}", file=sys.stderr)
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Load the base + compute the petal mask ONCE; reuse across every colorway.
    base_im = Image.open(BASE).convert("RGB")
    base_rgb = np.asarray(base_im)
    mask = _rose_mask(base_rgb)
    variants: list[tuple[str, Image.Image]] = []
    for name, h, s in COLORWAYS:
        img = recolor(base_rgb, mask, h, s)
        out = OUT_DIR / f"three-rose-cluster-{name}.png"
        img.save(out)
        variants.append((name, img))
        print(f"  wrote {out.relative_to(REPO_ROOT)}")
    sheet = contact_sheet(base_im, variants)
    sheet_path = OUT_DIR / "colorway-contact-sheet.png"
    sheet.save(sheet_path)
    print(f"  wrote {sheet_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
