"""
WCAG contrast ratio calculator.

Computes contrast ratios between two colors and checks against
WCAG 2.2 AA and AAA thresholds for normal and large text.

Usage:
    result = check_contrast("#B76E79", "#FFFFFF")
    print(f"Ratio: {result.ratio:.2f}:1 — Level: {result.level}")
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContrastResult:
    """Immutable result of a contrast check."""

    foreground: str
    background: str
    ratio: float
    level: str  # "AAA", "AA", "AA-Large", "Fail"
    aa_normal: bool
    aa_large: bool
    aaa_normal: bool
    aaa_large: bool


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color (#RGB or #RRGGBB) to (r, g, b) tuple."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    """Calculate relative luminance per WCAG 2.0 formula."""

    def linearize(channel: int) -> float:
        c = channel / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = linearize(rgb[0]), linearize(rgb[1]), linearize(rgb[2])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg_hex: str, bg_hex: str) -> float:
    """Calculate WCAG contrast ratio between two hex colors."""
    l1 = relative_luminance(hex_to_rgb(fg_hex))
    l2 = relative_luminance(hex_to_rgb(bg_hex))
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def wcag_level(ratio: float) -> str:
    """Determine WCAG conformance level from contrast ratio."""
    if ratio >= 7.0:
        return "AAA"
    if ratio >= 4.5:
        return "AA"
    if ratio >= 3.0:
        return "AA-Large"
    return "Fail"


def check_contrast(foreground: str, background: str) -> ContrastResult:
    """
    Check contrast between two hex colors against WCAG thresholds.

    Thresholds:
    - AA normal text:  4.5:1
    - AA large text:   3.0:1
    - AAA normal text: 7.0:1
    - AAA large text:  4.5:1
    """
    ratio = contrast_ratio(foreground, background)
    level = wcag_level(ratio)

    return ContrastResult(
        foreground=foreground,
        background=background,
        ratio=round(ratio, 2),
        level=level,
        aa_normal=ratio >= 4.5,
        aa_large=ratio >= 3.0,
        aaa_normal=ratio >= 7.0,
        aaa_large=ratio >= 4.5,
    )
