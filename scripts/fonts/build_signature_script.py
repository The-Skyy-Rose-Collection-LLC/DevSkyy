"""Build "SkyyRose Signature Script" TTF/woff2 from the gpt-image-2 glyph sheets.

Formal Copperplate/Engrosser's script register -- style reference is the gold
"Skyy Rose Collection" wordmark lockup (fine hairline entry/exit strokes,
thick tapered pressure downstrokes, ~55 degree forward slant, elegant closed
loops). Same build route as the sibling "SkyyRose Love Hurts Graffiti" font
(scripts/fonts/build_love_hurts_graffiti.py): whole-sheet potrace (one call
per sheet, not one per cell) -> classify each traced component into a grid
cell by centroid proximity -> per-row baseline measured from that row's
non-descender letters' actual traced ink-bottom -> per-glyph font-space
transform (potrace pixel-space, re-zeroed per glyph on X, baseline-zeroed
per row on Y, uniformly scaled) -> FontBuilder assembly with
dynamically-computed ascent/descent (this script's descender/flourish tails
would clip under the shared pipeline's hardcoded ascent=800/descent=-200) ->
woff2. No kerning table -- not requested for this build.

Descender classification below is a best-effort read of the two source
sheets (assets/fonts-src/signature-script/sheets/{lowercase,uppercase}.png);
compute_row_baselines' median-of-row is robust to a single misclassified
letter per 4-letter row, and the rendered specimen is the real check.
"""

from __future__ import annotations

import string
import tempfile
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.misc.transform import Transform
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont

from scripts.fonts.graffiti_sheet import (
    classify_components,
    compute_row_baselines,
    font_space_transform,
    ink_mask,
    parse_components,
    trace_sheet,
)

SHEETS_DIR = Path("assets/fonts-src/signature-script/sheets")
OUT_DIR = Path("assets/fonts-src/signature-script")
OUT_TTF = OUT_DIR / "skyyrose-signature-script.ttf"
OUT_WOFF2 = OUT_DIR / "skyyrose-signature-script.woff2"
FAMILY = "SkyyRose Signature Script"
STYLE = "Regular"

UNITS_PER_EM = 1000
TARGET_CAP_HEIGHT = 700.0  # font units -- matches the sibling sheet-trace builds
LSB_PAD_PX = 8  # left side bearing, in ORIGINAL sheet pixels (before scaling)
RSB_UNITS = 55  # right side bearing, in font units -- matches sibling builds
MIN_ADVANCE_UNITS = 40  # catches a genuinely degenerate trace only, not a
# normalization floor (see build_love_hurts_graffiti.py docstring for why a
# high floor monospaces a sheet-traced script).

# Best-effort read of the sheets: letters whose swash tail visibly dips below
# the row's baseline (excluded from that row's baseline measurement so the
# tail doesn't drag the measured baseline down).
LOWER_DESCENDERS = {"f", "g", "j", "p", "q", "y", "z"}
UPPER_DESCENDERS = {"D", "F", "G", "J", "P", "Q", "Y", "Z"}

# gpt-image-2's thin light-gray grid lines antialias to isolated pixel
# clusters that dip below INK_THRESHOLD at scattered points along the line
# (verified empirically on this sheet pair: 33 of 68 traced lowercase
# components have a bbox min-dimension of 0.4-0.8px, clustered exactly at
# the row3/row4 nominal boundary y-coordinate -- these corrupted the m/n/o/p
# row's measured baseline, rendering that row's letters visibly floating
# above the true baseline in the first build). Real glyph ink at this trace
# scale is never this thin: the smallest genuine component (the i/j dot) is
# 13.6px in its narrowest dimension. A 5px floor drops the noise with a wide
# safety margin either side and does not touch any real component in either
# sheet (uppercase had zero sub-3px components; lowercase's next-smallest
# real component after the dots is 29px).
MIN_COMPONENT_DIM_PX = 5.0


def _filter_noise(components: list) -> list:
    """Drop sub-pixel grid-line-antialiasing fragments (see
    MIN_COMPONENT_DIM_PX docstring above) before they can pollute a glyph's
    or a row's measured ink bounds."""
    return [c for c in components if min(c.x1 - c.x0, c.y1 - c.y0) >= MIN_COMPONENT_DIM_PX]


def _build_glyph(
    components_by_char: dict[str, list],
    char: str,
    pixel_xform: Transform,
    baseline_px: float,
    scale: float,
) -> tuple[object, float, float]:
    """Returns (glyph, advance_width_units, lsb_units) for one character."""
    comps = components_by_char[char]
    x_origin_px = min(c.x0 for c in comps) - LSB_PAD_PX
    x_max_px = max(c.x1 for c in comps)

    xform = font_space_transform(pixel_xform, x_origin_px, baseline_px, scale)

    glyph_set: dict[str, object] = {}
    pen = TTGlyphPen(glyph_set)
    tpen = TransformPen(pen, xform)
    cpen = Cu2QuPen(tpen, max_err=1.0, reverse_direction=True)
    for comp in comps:
        parse_path(comp.path_d, cpen)
    glyph = pen.glyph()

    ink_width_units = (x_max_px - x_origin_px) * scale
    advance_width = max(int(round(ink_width_units + RSB_UNITS)), MIN_ADVANCE_UNITS)
    lsb = int(round(LSB_PAD_PX * scale))
    return glyph, advance_width, lsb


def build() -> dict[str, object]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        lower_mask, lower_size = ink_mask(SHEETS_DIR / "lowercase.png")
        lower_svg = trace_sheet(lower_mask, tmpdir_path, "lowercase")
        lower_components, lower_xform = parse_components(lower_svg)
        lower_components = _filter_noise(lower_components)
        lower_by_char = classify_components(lower_components, string.ascii_lowercase, lower_size)
        missing_lower = set(string.ascii_lowercase) - set(lower_by_char)
        if missing_lower:
            raise RuntimeError(
                f"lowercase sheet: no component classified for {sorted(missing_lower)!r}"
            )
        lower_baselines = compute_row_baselines(
            lower_by_char, string.ascii_lowercase, LOWER_DESCENDERS
        )

        upper_mask, upper_size = ink_mask(SHEETS_DIR / "uppercase.png")
        upper_svg = trace_sheet(upper_mask, tmpdir_path, "uppercase")
        upper_components, upper_xform = parse_components(upper_svg)
        upper_components = _filter_noise(upper_components)
        upper_by_char = classify_components(upper_components, string.ascii_uppercase, upper_size)
        missing_upper = set(string.ascii_uppercase) - set(upper_by_char)
        if missing_upper:
            raise RuntimeError(
                f"uppercase sheet: no component classified for {sorted(missing_upper)!r}"
            )
        upper_baselines = compute_row_baselines(
            upper_by_char, string.ascii_uppercase, UPPER_DESCENDERS
        )

    # Pass 1 (scale=1.0): measure raw cap height from the uppercase trace.
    raw_cap_heights = []
    for i, char in enumerate(string.ascii_uppercase):
        row = i // 4
        glyph, _adv, _lsb = _build_glyph(
            upper_by_char, char, upper_xform, upper_baselines[row], 1.0
        )
        if char not in UPPER_DESCENDERS and glyph.coordinates:
            ys = [pt[1] for pt in glyph.coordinates]
            raw_cap_heights.append(max(ys) - min(ys))
    mean_raw_cap_height = sum(raw_cap_heights) / len(raw_cap_heights)
    scale = TARGET_CAP_HEIGHT / mean_raw_cap_height
    print(f"mean raw cap height={mean_raw_cap_height:.1f}px -> scale={scale:.4f}")

    # Pass 2 (real scale): build every glyph for real.
    built: list[str] = []
    glyphs: dict[str, object] = {}
    char_to_glyph_name: dict[str, str] = {}
    codepoint_map: dict[int, str] = {}
    metrics: dict[str, tuple[int, int]] = {}

    def _add(char: str, by_char, xform, baselines, cols=4):
        row = (
            string.ascii_lowercase.index(char) // cols
            if char.islower()
            else string.ascii_uppercase.index(char) // cols
        )
        glyph, advance, lsb = _build_glyph(by_char, char, xform, baselines[row], scale)
        glyph_name = f"uni{ord(char):04X}"
        glyphs[glyph_name] = glyph
        char_to_glyph_name[char] = glyph_name
        codepoint_map[ord(char)] = glyph_name
        metrics[glyph_name] = (advance, lsb)
        built.append(char)

    for char in string.ascii_lowercase:
        _add(char, lower_by_char, lower_xform, lower_baselines)
    for char in string.ascii_uppercase:
        _add(char, upper_by_char, upper_xform, upper_baselines)

    lower_advances = [metrics[char_to_glyph_name[c]][0] for c in string.ascii_lowercase]
    space_advance = int(round(0.55 * (sum(lower_advances) / len(lower_advances))))
    glyphs["uni0020"] = TTGlyphPen(None).glyph()
    char_to_glyph_name[" "] = "uni0020"
    codepoint_map[0x20] = "uni0020"
    metrics["uni0020"] = (space_advance, 0)
    built.append(" ")

    # Dynamic ascent/descent from actual glyph bounds (+ headroom) -- avoids
    # clipping this style's ascender loops / descender tails.
    all_y = []
    for name, g in glyphs.items():
        if g.coordinates:
            all_y.extend(pt[1] for pt in g.coordinates)
    y_max, y_min = max(all_y), min(all_y)
    ascent = int(round(y_max + 60))
    descent = int(round(y_min - 60))
    print(f"glyph Y range: [{y_min:.0f}, {y_max:.0f}] -> ascent={ascent} descent={descent}")

    notdef_glyph = TTGlyphPen(None).glyph()
    glyph_order = [".notdef"] + [char_to_glyph_name[c] for c in built]

    fb = FontBuilder(UNITS_PER_EM, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(codepoint_map)
    fb.setupGlyf({**glyphs, ".notdef": notdef_glyph})
    fb.setupHorizontalMetrics({**metrics, ".notdef": (300, 0)})
    fb.setupHorizontalHeader(ascent=ascent, descent=descent)
    fb.setupNameTable({"familyName": FAMILY, "styleName": STYLE})
    fb.setupOS2(sTypoAscender=ascent, usWinAscent=ascent, usWinDescent=-descent)
    fb.setupPost()

    fb.save(str(OUT_TTF))

    ttf = TTFont(str(OUT_TTF))
    ttf.flavor = "woff2"
    ttf.save(str(OUT_WOFF2))

    print(f"built {len(built)} glyphs (52 letters + space) -> {OUT_TTF}")
    print(f"woff2 -> {OUT_WOFF2}")
    all_advances = [metrics[char_to_glyph_name[c]][0] for c in built if c != " "]
    print(
        f"advance width range: {min(all_advances)}-{max(all_advances)} units (space={space_advance})"
    )

    return {"scale": scale, "ascent": ascent, "descent": descent, "advances": metrics}


if __name__ == "__main__":
    build()
