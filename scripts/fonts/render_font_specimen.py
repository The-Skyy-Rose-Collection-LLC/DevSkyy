"""Render a specimen of the built TTF -- the collection name typeset in the
actual font, plus every available glyph individually -- for final eyes-on QC.

Usage: python -m scripts.fonts.render_font_specimen --ttf PATH --text "Love Hurts" --out PATH
"""

from __future__ import annotations

import argparse
import string
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

# System fallback for the "glyphs: ..." caption -- deliberately NOT the font
# under test, since that font only has the 9 built glyphs and would render
# every other caption character as a blank .notdef box.
_LABEL_FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)


def _load_label_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in _LABEL_FONT_CANDIDATES:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_specimen(ttf_path: str, text: str, out_path: str, size: int = 160) -> Path:
    font = ImageFont.truetype(ttf_path, size)
    tt = TTFont(ttf_path)
    cmap = tt.getBestCmap()
    available = "".join(c for c in string.ascii_letters if ord(c) in cmap)

    label_font = _load_label_font(60)
    lines = [(text, font), (f"glyphs: {available}", label_font)]
    pad = 40
    line_h = size + 30

    probe = Image.new("RGB", (1, 1))
    probe_draw = ImageDraw.Draw(probe)
    max_text_w = max(probe_draw.textbbox((0, 0), line, font=f)[2] for line, f in lines)
    width = pad * 2 + max_text_w

    canvas = Image.new("RGB", (width, pad * 2 + line_h * len(lines)), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    y = pad
    for line, f in lines:
        draw.text((pad, y), line, font=f, fill=(20, 20, 20))
        y += line_h

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ttf", required=True)
    parser.add_argument("--text", default="Love Hurts")
    parser.add_argument("--out", default="assets/fonts-src/love-hurts/specimen.png")
    args = parser.parse_args()
    path = render_specimen(args.ttf, args.text, args.out)
    print(f"Wrote specimen: {path}")


if __name__ == "__main__":
    main()
