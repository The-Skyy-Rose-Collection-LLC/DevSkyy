"""Build a TTF font from a hand-filled-in template scan + its manifest.

Pairs with template.py (which generates the blank template + manifest) and
cli.py (the CLI entry point). See template.py for the manifest JSON schema.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from fontTools.fontBuilder import FontBuilder
from fontTools.misc.transform import Transform
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path
from PIL import Image

RSB = 60  # right side bearing, in font units
MIN_ADVANCE_WIDTH = 300
UNITS_PER_EM = 1000
NOTDEF_ADVANCE_WIDTH = 300

_PATH_D_RE = re.compile(r'<path[^>]*\bd="([^"]+)"')
_GROUP_TRANSFORM_RE = re.compile(r'<g transform="([^"]+)"')
_FLOAT_RE = re.compile(r"-?\d+\.?\d*")


def _validate_manifest(manifest: dict[str, Any]) -> None:
    """Validate manifest shape and internal consistency. Raises ValueError on any problem.

    Catches malformed manifests up front (missing keys, out-of-bounds bboxes,
    duplicate chars/codepoints) so failures are a clear, fail-loud ValueError
    instead of a bare KeyError/AssertionError surfacing deep inside fontTools
    or silently corrupting a glyph via Image.crop's zero-padding of an
    out-of-bounds crop region.
    """
    for key in ("image_size", "cells"):
        if key not in manifest:
            raise ValueError(f"manifest missing required key {key!r}")

    image_w, image_h = manifest["image_size"]
    seen_chars: set[str] = set()
    seen_codepoints: set[int] = set()

    for i, cell in enumerate(manifest["cells"]):
        for key in ("char", "codepoint", "bbox"):
            if key not in cell:
                raise ValueError(f"manifest cell #{i} missing required key {key!r}: {cell}")

        char, codepoint, bbox = cell["char"], cell["codepoint"], cell["bbox"]

        if char in seen_chars:
            raise ValueError(
                f"manifest has duplicate char {char!r} (cell #{i}) — each char must appear once"
            )
        if codepoint in seen_codepoints:
            raise ValueError(
                f"manifest has duplicate codepoint {codepoint} (cell #{i}, char {char!r}) "
                "— each codepoint must appear once"
            )
        seen_chars.add(char)
        seen_codepoints.add(codepoint)

        if len(bbox) != 4:
            raise ValueError(
                f"manifest cell #{i} ({char!r}) bbox must have 4 elements, got {bbox!r}"
            )
        left, top, right, bottom = bbox
        if not (0 <= left < right <= image_w and 0 <= top < bottom <= image_h):
            raise ValueError(
                f"manifest cell #{i} ({char!r}) bbox {bbox!r} is out of bounds for "
                f"image_size {manifest['image_size']!r}"
            )


def _collect_glyphs(
    manifest: dict[str, Any],
    filled_img: Image.Image,
    threshold: int,
    tmpdir_path: Path,
) -> tuple[
    list[str], list[str], dict[str, Any], dict[str, str], dict[int, str], dict[str, tuple[int, int]]
]:
    """Vectorize every non-blank cell. Returns (built, skipped_blank, glyphs, char_to_glyph_name, codepoint_map, metrics)."""
    built: list[str] = []
    skipped_blank: list[str] = []
    glyphs: dict[str, Any] = {}
    char_to_glyph_name: dict[str, str] = {}
    codepoint_map: dict[int, str] = {}
    metrics: dict[str, tuple[int, int]] = {}

    for cell in manifest["cells"]:
        char, codepoint, bbox = cell["char"], cell["codepoint"], cell["bbox"]

        glyph_name, x_min, x_max, status = _build_glyph_for_cell(
            filled_img, bbox, threshold, tmpdir_path, codepoint
        )

        if status == "blank":
            skipped_blank.append(char)
            continue

        glyphs[glyph_name] = status  # status holds the glyph object here
        char_to_glyph_name[char] = glyph_name
        codepoint_map[codepoint] = glyph_name
        advance_width = max(int(round(x_max)) + RSB, MIN_ADVANCE_WIDTH)
        lsb = int(round(x_min))
        metrics[glyph_name] = (advance_width, lsb)
        built.append(char)

    return built, skipped_blank, glyphs, char_to_glyph_name, codepoint_map, metrics


def _assemble_font(
    built: list[str],
    glyphs: dict[str, Any],
    char_to_glyph_name: dict[str, str],
    codepoint_map: dict[int, str],
    metrics: dict[str, tuple[int, int]],
    family: str,
    style: str,
    out_path: Path,
) -> None:
    """Build and save the .ttf from collected glyphs/metrics."""
    notdef_glyph = TTGlyphPen(None).glyph()
    glyph_order = [".notdef"] + [char_to_glyph_name[char] for char in built]

    fb = FontBuilder(UNITS_PER_EM, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(codepoint_map)
    fb.setupGlyf({**glyphs, ".notdef": notdef_glyph})
    fb.setupHorizontalMetrics({**metrics, ".notdef": (NOTDEF_ADVANCE_WIDTH, 0)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": family, "styleName": style})
    fb.setupOS2()
    fb.setupPost()
    fb.save(str(out_path))


def build_font(
    filled_image_path: str | Path,
    manifest_path: str | Path,
    out_path: str | Path,
    family: str = "MyFont",
    style: str = "Regular",
    threshold: int = 140,
) -> dict[str, Any]:
    """Vectorize a filled-in template scan into a TTF font.

    The filled-in image's pixel dimensions MUST exactly match the original
    template's dimensions (recorded in manifest["image_size"]) — cell bboxes
    are pixel coordinates into that exact canvas, so any resize would
    misalign every glyph. Raises ValueError on mismatch; no silent resize.

    Returns {"built": [...chars successfully turned into glyphs...],
             "skipped_blank": [...chars whose cell had no ink, logged not failed...],
             "out_path": str(out_path)}.
    Raises ValueError if the manifest is malformed, the filled image isn't a
    decodable image, or its dimensions don't match manifest["image_size"].
    Raises RuntimeError if zero glyphs were extracted (nothing to build).
    """
    filled_image_path = Path(filled_image_path)
    manifest_path = Path(manifest_path)
    out_path = Path(out_path)

    if not filled_image_path.exists():
        raise FileNotFoundError(f"filled image not found: {filled_image_path}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest not found: {manifest_path}")

    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"manifest is not valid JSON: {manifest_path}") from exc

    _validate_manifest(manifest)

    # Two different --chars strings of the same length can produce an
    # identically-shaped manifest (same image_size/grid), so a dimension
    # match alone can't prove this manifest belongs to this scan. Surfacing
    # the fingerprint here turns that mismatch from a silent miswiring into
    # something the user can catch by eye against what `template` printed.
    fingerprint = manifest.get("chars_fingerprint", "unknown")
    cols = manifest.get("grid", {}).get("cols", "?")
    print(
        f"Building from manifest: {len(manifest['cells'])} cells, {cols} cols, "
        f"fingerprint={fingerprint} — confirm this matches the fingerprint printed "
        "when this manifest's template was generated."
    )

    try:
        with Image.open(filled_image_path) as raw_img:
            filled_img = raw_img.convert("RGB")
    except Exception as exc:
        raise ValueError(
            f"could not open filled image as a valid image file: {filled_image_path} ({exc})"
        ) from exc

    actual_size = list(filled_img.size)
    expected_size = list(manifest["image_size"])
    if actual_size != expected_size:
        raise ValueError(
            "filled image dimensions "
            f"{tuple(actual_size)} do not match template dimensions "
            f"{tuple(expected_size)} recorded in the manifest — the filled-in "
            "scan must be the exact same pixel size as the original template "
            "(no resizing is performed)."
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        built, skipped_blank, glyphs, char_to_glyph_name, codepoint_map, metrics = _collect_glyphs(
            manifest, filled_img, threshold, Path(tmpdir)
        )

    if len(built) == 0:
        raise RuntimeError("no glyphs extracted — every cell was blank or failed to vectorize")

    _assemble_font(
        built, glyphs, char_to_glyph_name, codepoint_map, metrics, family, style, out_path
    )

    print(f"built {len(built)} glyph(s): {', '.join(built)}")
    if skipped_blank:
        print(f"skipped {len(skipped_blank)} blank cell(s): {', '.join(skipped_blank)}")

    return {"built": built, "skipped_blank": skipped_blank, "out_path": str(out_path)}


def _build_glyph_for_cell(
    filled_img: Image.Image,
    bbox: list[int],
    threshold: int,
    tmpdir_path: Path,
    codepoint: int,
) -> tuple[str, float, float, Any]:
    """Vectorize one cell. Returns (glyph_name, xMin, xMax, glyph_or_'blank')."""
    glyph_name = f"uni{codepoint:04X}"

    left, top, right, bottom = bbox
    inset = 10
    cell_img = filled_img.crop((left + inset, top + inset, right - inset, bottom - inset))

    gray = np.array(cell_img.convert("L"))
    # threshold 140 sits far below the template's gray guide value (210),
    # so border/baseline/ghost-label guide marks are excluded automatically.
    ink_mask = gray < threshold

    if not ink_mask.any():
        return glyph_name, 0.0, 0.0, "blank"

    ys, xs = np.where(ink_mask)
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())

    pad = 6
    h, w = ink_mask.shape
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(w - 1, x1 + pad)
    y1 = min(h - 1, y1 + pad)

    cropped_ink = ink_mask[y0 : y1 + 1, x0 : x1 + 1]
    bitmap = Image.fromarray(np.where(cropped_ink, 0, 255).astype(np.uint8)).convert("1")

    bmp_path = tmpdir_path / f"{glyph_name}.bmp"
    svg_path = tmpdir_path / f"{glyph_name}.svg"
    bitmap.save(bmp_path)

    result = subprocess.run(
        ["potrace", "-s", "--tight", "-o", str(svg_path), str(bmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    svg_text = svg_path.read_text()
    path_ds = _PATH_D_RE.findall(svg_text)
    if not path_ds:
        print(f"warning: no <path> elements found for glyph {glyph_name!r}, treating as blank")
        return glyph_name, 0.0, 0.0, "blank"

    group_match = _GROUP_TRANSFORM_RE.search(svg_text)
    tx, ty, sx, sy = (float(v) for v in _FLOAT_RE.findall(group_match.group(1))[:4])

    # potrace's own translate/scale still leaves coordinates in SVG's y-down
    # convention; one more y-flip is required to land in font y-up space.
    xform = Transform().translate(tx, ty).scale(sx, sy).scale(1, -1)

    glyph_set: dict[str, Any] = {}
    pen = TTGlyphPen(glyph_set)
    tpen = TransformPen(pen, xform)
    cpen = Cu2QuPen(tpen, max_err=1.0, reverse_direction=True)
    for d in path_ds:
        parse_path(d, cpen)
    glyph = pen.glyph()

    if not glyph.coordinates:
        print(f"warning: glyph {glyph_name!r} produced no coordinates, treating as blank")
        return glyph_name, 0.0, 0.0, "blank"

    xs_coords = [pt[0] for pt in glyph.coordinates]
    ys_coords = [pt[1] for pt in glyph.coordinates]
    x_min, x_max = min(xs_coords), max(xs_coords)
    _y_min, _y_max = min(ys_coords), max(ys_coords)  # bbox per spec; only x feeds metrics

    return glyph_name, x_min, x_max, glyph
