"""Side-by-side comparison: SkyyRose Signature Script (bespoke) vs. Pinyon
Script (current production Signature-collection script) -- same text, same
size, stacked -- for an honest founder verdict on whether the bespoke build
beats the incumbent stock face.
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

SIG_TTF = "assets/fonts-src/signature-script/skyyrose-signature-script.ttf"
PINYON = "wordpress-theme/skyyrose-flagship/assets/fonts/pinyon-script-latin.woff2"
OUT = "/tmp/signature_vs_pinyon.png"

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
    hero_text = "The Signature Collection"
    az_text = "abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    sig_hero = ImageFont.truetype(SIG_TTF, 140)
    sig_row = ImageFont.truetype(SIG_TTF, 70)
    pin_hero = ImageFont.truetype(PINYON, 140)
    pin_row = ImageFont.truetype(PINYON, 70)
    label_font = _label_font(30)

    probe = Image.new("RGB", (1, 1))
    pd = ImageDraw.Draw(probe)
    pad = 70
    width = pad * 2 + max(
        pd.textbbox((0, 0), hero_text, font=sig_hero)[2],
        pd.textbbox((0, 0), hero_text, font=pin_hero)[2],
        pd.textbbox((0, 0), az_text, font=sig_row)[2],
        pd.textbbox((0, 0), az_text, font=pin_row)[2],
    )

    label_h, hero_h, row_h, gap = 44, 220, 130, 40
    block_h = label_h + hero_h + row_h + gap
    height = pad * 2 + block_h * 2

    canvas = Image.new("RGB", (int(width), int(height)), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    y = pad
    for name, hero_f, row_f in [
        ("BESPOKE: SkyyRose Signature Script (this build)", sig_hero, sig_row),
        ("INCUMBENT: Pinyon Script (current production)", pin_hero, pin_row),
    ]:
        draw.text((pad, y), name, font=label_font, fill=(120, 120, 120))
        y += label_h
        draw.text((pad, y), hero_text, font=hero_f, fill=(10, 10, 10))
        y += hero_h
        draw.text((pad, y), az_text, font=row_f, fill=(10, 10, 10))
        y += row_h + gap

    canvas.save(OUT)
    print(f"Wrote {OUT} ({canvas.size})")


if __name__ == "__main__":
    main()
