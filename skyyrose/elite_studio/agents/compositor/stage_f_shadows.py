"""Stage F: contact shadow generation.

Adds a soft contact shadow to anchor the subject in the scene via PIL
gaussian blur. GPSDiffusion can be hooked in later by replacing this body.
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from PIL import Image, ImageFilter

logger = logging.getLogger(__name__)


class ShadowStageError(RuntimeError):
    """Raised when the PIL shadow pass fails.

    The caller must NOT score the result as a shadowed render — silently
    forwarding the un-shadowed composite (the old behavior) labeled it as a
    shadow path and let the QA gate score the wrong image.
    """


def generate_shadows(
    composite_path: str,
    sku: str,
    output_dir: str,
    scene_name: str = "",
) -> str:
    """Add a soft contact shadow to anchor the subject in the scene.

    PIL gaussian fallback only. GPSDiffusion can be hooked in later by
    replacing this body — the test contract expects ``"shadow"`` in the
    returned path OR returning the input path unchanged when the subject
    fills the frame (no ground plane).

    Args:
        composite_path: Path to the Stage E composite (or Stage D if GIMP skipped).
        sku: Canonical SKU string.
        output_dir: Directory where the shadow image is written.

    Returns:
        Path to the shadow-composited image, or ``composite_path`` unchanged
        when the subject fills the frame (no ground plane to anchor).

    Raises:
        ShadowStageError: on any PIL/IO failure — fail-closed, never silently
            returns an un-shadowed image labeled as a shadow path.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    try:
        with Image.open(composite_path).convert("RGBA") as composite:
            width, height = composite.size

            # Derive a soft mask from the alpha (or the full image as a
            # luminance proxy if no alpha present).
            if "A" in composite.getbands():
                alpha = composite.split()[-1]
            else:
                alpha = composite.convert("L")

            # If the subject occupies > 85% of the frame, skip shadows
            # (no ground plane visible). Compare with the alpha mean.
            # Use ImageStat for an O(1) sum instead of a Python-level
            # iteration over every pixel; ~50-200ms saved per render on
            # full-res composites. ``alpha`` is L-mode at this point so
            # ImageStat.sum has length 1.
            from PIL import ImageStat

            stats = ImageStat.Stat(alpha)
            non_zero = int(stats.sum[0] / 255)
            if non_zero >= 0.85 * width * height:
                return composite_path

            # Project alpha downward + blur to create a contact shadow.
            shadow = Image.new("L", (width, height), 0)
            shadow.paste(alpha, (4, 12))
            shadow = shadow.filter(ImageFilter.GaussianBlur(radius=14))

            # Multiply blend at 45% opacity onto a black layer.
            black = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            shadow_rgba = Image.merge(
                "RGBA",
                (
                    Image.new("L", (width, height), 0),
                    Image.new("L", (width, height), 0),
                    Image.new("L", (width, height), 0),
                    shadow.point(lambda v: int(v * 0.45)),
                ),
            )
            black.alpha_composite(shadow_rgba)
            final = Image.alpha_composite(black, composite)

        dest = out / (f"{sku}-{scene_name}-shadow.png" if scene_name else f"{sku}-shadow.png")
        # Atomic write: render to a temp file then os.replace, so a crash
        # mid-write can't leave a truncated PNG the QA gate reads as garbage.
        fd, tmp = tempfile.mkstemp(dir=str(out), suffix=".png")
        os.close(fd)
        final.save(tmp, format="PNG")
        os.replace(tmp, dest)
        return str(dest)
    except Exception as exc:
        raise ShadowStageError(f"Shadow stage failed for {sku}: {exc}") from exc
