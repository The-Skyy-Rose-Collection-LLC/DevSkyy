"""
Spacing scale generator.

Generates a consistent spacing system based on a base unit.
Produces named sizes from 3xs to 3xl.

Usage:
    scale = generate_spacing_scale(base=4)
    # {'3xs': 2, 'xxs': 4, 'xs': 8, 'sm': 12, 'base': 16, ...}
"""

from __future__ import annotations


def generate_spacing_scale(
    base: int | float = 4,
) -> dict[str, float]:
    """
    Generate a spacing scale based on a base unit.

    Uses a 4px base by default (most common in design systems).
    Each step roughly doubles, with intermediate steps.

    Args:
        base: Base spacing unit in px (default 4)

    Returns:
        Dict with size names → spacing values in px
    """
    return {
        "3xs": round(base * 0.5, 1),
        "xxs": round(base * 1, 1),
        "xs": round(base * 2, 1),
        "sm": round(base * 3, 1),
        "md": round(base * 4, 1),
        "base": round(base * 4, 1),
        "lg": round(base * 6, 1),
        "xl": round(base * 8, 1),
        "xxl": round(base * 12, 1),
        "3xl": round(base * 16, 1),
    }
