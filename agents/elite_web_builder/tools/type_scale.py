"""
Typography scale generator.

Generates a modular type scale based on a base size and ratio.
Produces sizes for body, h6→h1, small, and caption.

Usage:
    scale = generate_type_scale(base_size=16, ratio=1.25)
    # {'caption': 12.8, 'small': 14.4, 'body': 16, 'h6': 20.0, ...}
"""

from __future__ import annotations


def generate_type_scale(
    base_size: int | float = 16,
    ratio: float = 1.25,  # Major third
) -> dict[str, float]:
    """
    Generate a modular type scale.

    Args:
        base_size: Base font size in px (default 16)
        ratio: Scale ratio (1.25 = major third, 1.333 = perfect fourth,
               1.5 = perfect fifth, 1.618 = golden ratio)

    Returns:
        Dict with element names → font sizes in px
    """
    return {
        "caption": round(base_size / (ratio ** 2), 1),
        "small": round(base_size / ratio, 1),
        "body": base_size,
        "h6": round(base_size * ratio, 1),
        "h5": round(base_size * ratio ** 2, 1),
        "h4": round(base_size * ratio ** 3, 1),
        "h3": round(base_size * ratio ** 4, 1),
        "h2": round(base_size * ratio ** 5, 1),
        "h1": round(base_size * ratio ** 6, 1),
    }
