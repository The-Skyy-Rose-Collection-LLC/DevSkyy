"""Generate the SkyyRose Signature Script glyph sheets via gpt-image-2 edit().

PAID. One call per sheet (lowercase / uppercase), sequenced so lowercase is
eyes-on verified before uppercase is spent -- mirrors the Black Rose /
Love Hurts Graffiti sheet-generation precedent (scripts/fonts/CLAUDE.local.md
on feat/custom-fonts), adapted for a formal Copperplate/Engrosser's script
register instead of a brush-script or graffiti register.

Usage:
    python -m scripts.fonts.gen_signature_sheets lowercase
    python -m scripts.fonts.gen_signature_sheets uppercase
"""

from __future__ import annotations

import sys
from pathlib import Path

from scripts.oai_render.client import OAIImageClient

REF_IMAGE = Path("wordpress-theme/skyyrose-flagship/assets/branding/signature-logo-transparent.png")
OUT_DIR = Path("assets/fonts-src/signature-script/sheets")

_STYLE_STUDY = (
    'A reference image shows the SkyyRose gold wordmark lockup "The Skyy Rose '
    'Collection": a flowing, formal cursive script with fine hairline entry/exit '
    "strokes, dramatic thick tapered pressure downstrokes (heavy thick/thin stroke "
    "contrast), elegant closed loops on ascenders and descenders, rounded bowls, "
    "and elaborate swash flourishes on the capital letters, all rendered in a "
    "metallic gold gradient with a bevel/emboss finish. Study the LETTERFORM STYLE "
    "ONLY: this is a formal Copperplate / Engrosser's script -- a consistent "
    "moderate forward slant of about 55 degrees, extreme thick/thin stroke "
    "contrast as if drawn with a flexible pointed pen (fine hairline upstrokes on "
    "light pressure, thick shaded downstrokes on heavy pressure), rounded "
    "compound-curve loops, elegant restrained terminals. Ignore the specific "
    "words, ignore the small rose illustration, and ignore the metallic gold "
    "gradient and bevel/emboss finish entirely -- no gloss, no gradient, no color."
)

_GRID_RULE = (
    "Generate a NEW image: a clean grid template on a pure white background, "
    "exactly 4 columns by 7 rows (28 cells total), separated by thin light-gray "
    "grid lines, each cell approximately 256px wide by 219px tall."
)

_ISOLATION_RULE = (
    "Each letter must be fully self-contained and complete within its own cell "
    "boundary -- do NOT let any stroke, loop, or flourish cross into a "
    "neighboring cell or touch a grid line, do NOT connect letters across cells, "
    "keep any flourish small and restrained enough to stay fully inside the cell. "
    "Hold the same ~55 degree forward slant and the same thick/thin stroke "
    "contrast consistently across all 26 letters -- do not let the slant drift "
    "letter to letter."
)

_INK_RULE = (
    "CRITICAL rendering rule: every hairline stroke must be a SOLID, "
    "FULLY-FILLED, UNBROKEN flat black line from end to end -- no gray, no faint "
    "or broken hairlines, no anti-aliased fading to gray, no gloss, no bevel, no "
    "gradient, no drop shadow, no color. Flat matte black ink on white paper, "
    "like a hand-inked copperplate calligraphy practice sheet. No text labels, "
    "no letter captions, no watermark -- just the thin gray grid lines and the "
    "26 solid flat-black glyphs, one per cell. Leave the last 2 cells (row 7, "
    "columns 3 and 4) completely blank and empty."
)

PROMPTS = {
    "lowercase": (
        f"{_STYLE_STUDY}\n\n{_GRID_RULE} Fill the first 26 cells, reading "
        "left-to-right then top-to-bottom, with the lowercase Latin alphabet in "
        "this exact order: a b c d e f g h i j k l m n o p q r s t u v w x y z -- "
        "one letter per cell, each letter drawn large and centered in its cell, "
        "in that same formal copperplate/engrosser's cursive style (fine hairline "
        "entry and exit strokes, thick tapered pressure downstrokes, elegant "
        "closed loops, rounded bowls).\n\n"
        f"{_ISOLATION_RULE}\n\n{_INK_RULE}"
    ),
    "uppercase": (
        f"{_STYLE_STUDY}\n\n{_GRID_RULE} Fill the first 26 cells, reading "
        "left-to-right then top-to-bottom, with the uppercase Latin alphabet in "
        "this exact order: A B C D E F G H I J K L M N O P Q R S T U V W X Y Z -- "
        "one letter per cell, each letter drawn large and centered in its cell, "
        "in that same formal copperplate/engrosser's capital style (bold hairline "
        "entry strokes, thick tapered pressure downstrokes, a restrained loop "
        "flourish where natural for that capital -- as seen in the reference "
        "lockup's capital S and R -- but noticeably smaller than the reference so "
        "it stays fully inside the cell).\n\n"
        f"{_ISOLATION_RULE}\n\n{_INK_RULE}"
    ),
}


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in PROMPTS:
        print("Usage: python -m scripts.fonts.gen_signature_sheets {lowercase|uppercase}")
        sys.exit(1)
    which = sys.argv[1]

    if not REF_IMAGE.exists():
        raise SystemExit(f"Reference image not found: {REF_IMAGE}")

    client = OAIImageClient()
    print(f"Calling gpt-image-2 edit() for {which} sheet (reference: {REF_IMAGE}) ...")
    image_bytes = client.edit(prompt=PROMPTS[which], image_paths=[REF_IMAGE])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{which}.png"
    out_path.write_bytes(image_bytes)
    print(f"Wrote {out_path} ({len(image_bytes)} bytes)")


if __name__ == "__main__":
    main()
