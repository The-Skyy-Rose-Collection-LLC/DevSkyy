"""Render the final eyes-on QC specimen for SkyyRose Signature Script:
hero lockup text + full a-z / A-Z rows, labeled -- for founder review.
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

TTF = "assets/fonts-src/signature-script/skyyrose-signature-script.ttf"
OUT = "/Users/theceo/.claude/jobs/25588cfb/tmp/sig-font-specimen.png"

LABEL_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
)


def _label_font(size: int) -> ImageFont.FreeTypeFont:
    for path in LABEL_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main() -> None:
    hero_font = ImageFont.truetype(TTF, 150)
    row_font = ImageFont.truetype(TTF, 90)
    label_font = _label_font(28)

    hero_text = "The Signature Collection"
    lower_text = "abcdefghijklmnopqrstuvwxyz"
    upper_text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    probe = Image.new("RGB", (1, 1))
    pd = ImageDraw.Draw(probe)
    pad = 70
    width = pad * 2 + max(
        pd.textbbox((0, 0), hero_text, font=hero_font)[2],
        pd.textbbox((0, 0), lower_text, font=row_font)[2],
        pd.textbbox((0, 0), upper_text, font=row_font)[2],
    )

    hero_h = 260
    label_h = 46
    row_h = 170
    height = pad * 2 + hero_h + (label_h + row_h) * 2

    canvas = Image.new("RGB", (int(width), int(height)), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    y = pad
    draw.text((pad, y), hero_text, font=hero_font, fill=(10, 10, 10))
    y += hero_h

    draw.text((pad, y), "lowercase a–z", font=label_font, fill=(140, 140, 140))
    y += label_h
    draw.text((pad, y), lower_text, font=row_font, fill=(10, 10, 10))
    y += row_h

    draw.text((pad, y), "uppercase A–Z", font=label_font, fill=(140, 140, 140))
    y += label_h
    draw.text((pad, y), upper_text, font=row_font, fill=(10, 10, 10))

    canvas.save(OUT)
    print(f"Wrote {OUT} ({canvas.size})")


if __name__ == "__main__":
    main()
