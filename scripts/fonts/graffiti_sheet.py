"""Trace AI-generated glyph-grid sheets (gpt-image-2 edit() outputs) into a TTF.

Unlike font_generator/pipeline.py, this does NOT crop each cell to its own
tight ink bounding box before tracing (that's what discards the shared
baseline -- see fix_baseline.py's docstring for the documented bug on the
Black Rose font). Instead it potraces the ENTIRE sheet in ONE call, so every
glyph's coordinates come out of the SAME global potrace transform. Baseline
consistency then falls out of the geometry for free: no per-glyph post-hoc
correction pass is needed (and none would be possible here anyway -- these
are raster-traced glyphs, not the parametric letterforms fix_baseline.py's
approach requires).

Pipeline: threshold sheet -> whole-image potrace (--group) -> classify each
traced connected-component into a nominal grid cell by bbox-centroid
proximity (handles disconnected dots/drips like i/j automatically, since a
letter's dot and stem share the same cell) -> per-row baseline computed
empirically from the row's non-descender letters (grid lines in an
AI-generated sheet are not pixel-exact, so a nominal ratio drifts row to
row; the *measured* ink-bottom of flat letters does not) -> build glyph
outlines via chained TransformPens (potrace pixel-space -> font em-space).
"""

from __future__ import annotations

import re
import statistics
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.svgLib.path import parse_path
from PIL import Image

_PATH_D_RE = re.compile(r'<path[^>]*\bd="([^"]+)"')
_GROUP_TRANSFORM_RE = re.compile(r'<g transform="([^"]+)"')
_FLOAT_RE = re.compile(r"-?\d+\.?\d*")

INK_THRESHOLD = 140  # matches font_generator/pipeline.py; verified against the
# sheets' actual histogram (ink 0-11, grid lines 161-215, background 244-255 --
# a clean gap either side of 140, see .wolf/memory.md).

GRID_COLS = 4
GRID_ROWS = 7


@dataclass(frozen=True)
class Component:
    """One potrace connected-component (a letter body, or a disconnected
    dot/drip), located in the sheet's own pixel space (origin top-left,
    y-down -- matches the source PNG)."""

    path_d: str
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2


def ink_mask(
    png_path: str | Path, threshold: int = INK_THRESHOLD
) -> tuple[np.ndarray, tuple[int, int]]:
    """Returns (bool mask where True=ink, (width, height))."""
    with Image.open(png_path) as raw:
        gray = raw.convert("L")
        size = gray.size
        arr = np.array(gray)
    return arr < threshold, size


def trace_sheet(mask: np.ndarray, workdir: Path, name: str) -> str:
    """Potraces the whole ink mask in one call. Returns the raw SVG text."""
    bitmap = Image.fromarray(np.where(mask, 0, 255).astype(np.uint8)).convert("1")
    bmp_path = workdir / f"{name}.bmp"
    svg_path = workdir / f"{name}.svg"
    bitmap.save(bmp_path)

    result = subprocess.run(
        ["potrace", "-s", "--group", "-o", str(svg_path), str(bmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"potrace failed on {name}: {result.stderr}")
    return svg_path.read_text()


def parse_components(svg_text: str) -> tuple[list[Component], Transform]:
    """Extracts potrace's own group transform (translate then scale -- NOT an
    extra y-flip; that transform alone already lands in the source image's
    own pixel space, origin top-left, y-down) plus every top-level <path>'s
    bbox in that pixel space.

    Deliberately does NOT add pipeline.py's extra `.scale(1, -1)` -- that
    flip is what converts pixel-space into y-up font-space, and doing it
    here (per whole-sheet call) rather than per-glyph is exactly what keeps
    every glyph on the same baseline. The y-up conversion happens once,
    globally, in `font_transform_for_row` below.
    """
    group_match = _GROUP_TRANSFORM_RE.search(svg_text)
    if not group_match:
        raise ValueError("no <g transform=...> found in potrace SVG output")
    tx, ty, sx, sy = (float(v) for v in _FLOAT_RE.findall(group_match.group(1))[:4])
    pixel_xform = Transform().translate(tx, ty).scale(sx, sy)

    components: list[Component] = []
    for path_d in _PATH_D_RE.findall(svg_text):
        bp = BoundsPen(None)
        parse_path(path_d, bp)
        if bp.bounds is None:
            continue
        xmin, ymin, xmax, ymax = bp.bounds
        p0 = pixel_xform.transformPoint((xmin, ymin))
        p1 = pixel_xform.transformPoint((xmax, ymax))
        x0, x1 = sorted((p0[0], p1[0]))
        y0, y1 = sorted((p0[1], p1[1]))
        components.append(Component(path_d, x0, y0, x1, y1))
    return components, pixel_xform


def classify_components(
    components: list[Component],
    chars: str,
    image_size: tuple[int, int],
    cols: int = GRID_COLS,
    rows: int = GRID_ROWS,
) -> dict[str, list[Component]]:
    """Buckets each component into the nominal grid cell nearest its bbox
    center. Two components can land in the same cell (a disconnected dot +
    its stem, e.g. i/j) -- both get merged into that char's glyph later."""
    image_w, image_h = image_size
    cell_w, cell_h = image_w / cols, image_h / rows

    by_char: dict[str, list[Component]] = {}
    for comp in components:
        col = min(cols - 1, max(0, int(comp.cx // cell_w)))
        row = min(rows - 1, max(0, int(comp.cy // cell_h)))
        idx = row * cols + col
        if idx >= len(chars):
            continue  # blank trailing cell (e.g. row 7 cols 3-4) -- no char assigned
        char = chars[idx]
        by_char.setdefault(char, []).append(comp)
    return by_char


def compute_row_baselines(
    by_char: dict[str, list[Component]],
    chars: str,
    descenders: set[str],
    cols: int = GRID_COLS,
) -> dict[int, float]:
    """Per-row baseline_px = median ink-bottom of that row's non-descender
    letters, measured directly (not a nominal-grid ratio -- an AI-generated
    sheet's grid lines are not pixel-exact, so a ratio drifts row to row;
    the measured bottom of flat letters does not, verified empirically:
    within-row spread is 1-5px out of a ~219px cell)."""
    row_bottoms: dict[int, list[float]] = {}
    for i, char in enumerate(chars):
        if char not in by_char:
            continue
        row = i // cols
        bottom = max(c.y1 for c in by_char[char])
        if char not in descenders:
            row_bottoms.setdefault(row, []).append(bottom)

    # Fallback: a row with zero non-descender letters (shouldn't happen with
    # the current 26-letter layout, but stay correct if chars/grid change)
    # uses every letter in that row instead of failing.
    for i, char in enumerate(chars):
        if char not in by_char:
            continue
        row = i // cols
        if row not in row_bottoms:
            bottom = max(c.y1 for c in by_char[char])
            row_bottoms.setdefault(row, []).append(bottom)

    return {row: statistics.median(vals) for row, vals in row_bottoms.items()}


def font_space_transform(
    pixel_xform: Transform,
    x_origin_px: float,
    baseline_px: float,
    scale: float,
) -> Transform:
    """Composes potrace's pixel-space transform with the font-space mapping
    (per-glyph x re-zeroed at x_origin_px, y flipped + shifted so
    baseline_px -> font y=0, both axes scaled uniformly by `scale`)."""
    font_map = (
        Transform().translate(0, 0).scale(scale, -scale).translate(-x_origin_px, -baseline_px)
    )
    # font_map applied to a pixel-space point (x,y):
    #   translate(-x_origin,-baseline) first (innermost call, applied first)
    #   then scale(scale,-scale)
    # -> ((x - x_origin) * scale, (y - baseline) * -scale)
    #   = ((x - x_origin) * scale, (baseline - y) * scale)   <- y-up, baseline=0. Correct.
    return font_map.transform(pixel_xform)
