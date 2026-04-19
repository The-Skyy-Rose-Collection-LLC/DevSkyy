"""
Color Correction Agent — PIL-Based Brand Palette Alignment

Applies contrast, saturation, and brightness corrections guided
by the SkyyRose brand palette. Uses PIL ImageEnhance only.
"""

from __future__ import annotations

from pathlib import Path

from ..models import ColorCorrectionResult

# SkyyRose brand palette (hex → RGB for reference)
_BRAND_PALETTE: dict[str, str] = {
    "rose_gold": "#B76E79",
    "dark": "#0A0A0A",
    "gold": "#D4AF37",
}

# Correction parameters tuned for luxury fashion editorial
_CONTRAST_FACTOR = 1.15  # slight contrast boost for editorial pop
_SATURATION_FACTOR = 1.08  # subtle saturation push toward rose gold warmth
_BRIGHTNESS_FACTOR = 1.05  # minor brightness lift for clean studio feel
_SHARPNESS_FACTOR = 1.10  # light sharpness for detail clarity


class ColorCorrectionAgent:
    """PIL-based color correction aligned to SkyyRose brand palette.

    Applies a fixed sequence of adjustments: contrast boost,
    saturation nudge toward rose gold warmth, brightness correction,
    and a sharpness pass for garment detail clarity.
    """

    def correct(self, image_path: str) -> ColorCorrectionResult:
        """Apply brand-aligned color corrections to an image.

        Args:
            image_path: Path to source image (any PIL-supported format).

        Returns:
            ColorCorrectionResult with output_path and adjustments applied.
        """
        try:
            return self._correct(image_path)
        except Exception as exc:
            return ColorCorrectionResult(
                success=False,
                error=str(exc),
            )

    def _correct(self, image_path: str) -> ColorCorrectionResult:
        from PIL import Image, ImageEnhance

        src = Path(image_path)
        if not src.exists():
            return ColorCorrectionResult(
                success=False,
                error=f"Source image not found: {image_path}",
            )

        adjustments: list[str] = []

        with Image.open(src) as img:
            # Ensure RGB for consistent enhancement
            if img.mode != "RGB":
                img = img.convert("RGB")

            # 1. Contrast boost — editorial punch
            img = ImageEnhance.Contrast(img).enhance(_CONTRAST_FACTOR)
            adjustments.append(f"contrast_boost:{_CONTRAST_FACTOR}")

            # 2. Saturation nudge — warm rose gold palette alignment
            img = ImageEnhance.Color(img).enhance(_SATURATION_FACTOR)
            adjustments.append(f"saturation_nudge:{_SATURATION_FACTOR}")

            # 3. Brightness correction — clean studio lift
            img = ImageEnhance.Brightness(img).enhance(_BRIGHTNESS_FACTOR)
            adjustments.append(f"brightness_correction:{_BRIGHTNESS_FACTOR}")

            # 4. Sharpness pass — garment detail clarity
            img = ImageEnhance.Sharpness(img).enhance(_SHARPNESS_FACTOR)
            adjustments.append(f"sharpness_pass:{_SHARPNESS_FACTOR}")

            output_path = src.parent / f"{src.stem}-corrected{src.suffix}"
            img.save(str(output_path))

        return ColorCorrectionResult(
            success=True,
            output_path=str(output_path),
            adjustments_applied=tuple(adjustments),
        )
