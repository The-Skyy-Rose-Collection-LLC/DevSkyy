"""
HuggingFace Spaces hardware tier definitions.

Uses huggingface_hub.SpaceHardware enum as the authoritative source.
The cost table is a reference snapshot (2024 pricing) — never scraped at runtime.
"""

from __future__ import annotations

from typing import Dict, Optional

try:
    from huggingface_hub import \
        SpaceHardware as _HfSpaceHardware  # type: ignore[import-untyped]

    HARDWARE_ENUM_AVAILABLE = True
except ImportError:
    _HfSpaceHardware = None  # type: ignore[assignment]
    HARDWARE_ENUM_AVAILABLE = False


# Canonical hardware slug list — kept in sync with huggingface_hub.SpaceHardware.
# Used for validation when the SDK is not installed.
HARDWARE_SLUGS: tuple[str, ...] = (
    "cpu-basic",
    "cpu-upgrade",
    "cpu-xl",
    "zero-a10g",
    "t4-small",
    "t4-medium",
    "l4x1",
    "l4x4",
    "l40sx1",
    "l40sx4",
    "l40sx8",
    "a10g-small",
    "a10g-large",
    "a10g-largex2",
    "a10g-largex4",
    "a100-large",
    "h100",
    "h100x8",
)

# Reference cost snapshot (USD / hour, community tier pricing, 2024).
# These values are informational only — verify on https://huggingface.co/pricing before billing.
HARDWARE_COST_PER_HOUR: Dict[str, Optional[float]] = {
    "cpu-basic": 0.00,
    "cpu-upgrade": 0.03,
    "cpu-xl": 0.05,
    "zero-a10g": 0.00,  # ZeroGPU — shared quota, not billed per-hour
    "t4-small": 0.60,
    "t4-medium": 0.90,
    "l4x1": 0.80,
    "l4x4": 3.15,
    "l40sx1": 1.80,
    "l40sx4": 7.20,
    "l40sx8": 14.40,
    "a10g-small": 1.05,
    "a10g-large": 3.15,
    "a10g-largex2": 5.70,
    "a10g-largex4": 10.80,
    "a100-large": 10.80,
    "h100": 10.80,
    "h100x8": 79.99,
}

HARDWARE_DESCRIPTIONS: Dict[str, str] = {
    "cpu-basic": "2 vCPU / 16 GB RAM — free tier",
    "cpu-upgrade": "8 vCPU / 32 GB RAM",
    "cpu-xl": "32 vCPU / 128 GB RAM",
    "zero-a10g": "NVIDIA A10G via ZeroGPU shared quota (free)",
    "t4-small": "NVIDIA T4 / 4 vCPU / 15 GB RAM",
    "t4-medium": "NVIDIA T4 / 8 vCPU / 30 GB RAM",
    "l4x1": "NVIDIA L4 × 1 / 8 vCPU / 30 GB RAM",
    "l4x4": "NVIDIA L4 × 4 / 48 vCPU / 186 GB RAM",
    "l40sx1": "NVIDIA L40S × 1",
    "l40sx4": "NVIDIA L40S × 4",
    "l40sx8": "NVIDIA L40S × 8",
    "a10g-small": "NVIDIA A10G / 4 vCPU / 15 GB RAM",
    "a10g-large": "NVIDIA A10G / 12 vCPU / 46 GB RAM",
    "a10g-largex2": "NVIDIA A10G × 2",
    "a10g-largex4": "NVIDIA A10G × 4",
    "a100-large": "NVIDIA A100 / 12 vCPU / 142 GB RAM",
    "h100": "NVIDIA H100 / 16 vCPU / 80 GB HBM3",
    "h100x8": "NVIDIA H100 × 8 (node)",
}


def validate_hardware_slug(slug: str) -> str:
    """
    Validate a hardware slug.

    Returns the slug unchanged if valid.
    Raises ValueError with a helpful message if invalid.
    """
    if slug not in HARDWARE_SLUGS:
        valid = ", ".join(HARDWARE_SLUGS)
        raise ValueError(f"Unknown hardware tier '{slug}'. Valid options: {valid}")
    return slug


def hardware_to_sdk_enum(slug: str) -> object:
    """
    Convert a slug string to the huggingface_hub SpaceHardware enum value.

    Raises ImportError if huggingface_hub is not installed.
    Raises ValueError if the slug is invalid.
    """
    if not HARDWARE_ENUM_AVAILABLE or _HfSpaceHardware is None:
        raise ImportError("huggingface_hub is required. Install with: pip install huggingface_hub")
    validate_hardware_slug(slug)
    return _HfSpaceHardware(slug)


def hardware_table_rows() -> list[dict]:
    """
    Return a list of dicts suitable for tabular display.

    Each dict has keys: slug, cost_usd_hr, description.
    """
    rows = []
    for slug in HARDWARE_SLUGS:
        cost = HARDWARE_COST_PER_HOUR.get(slug)
        cost_str = "free" if cost == 0.00 else (f"${cost:.2f}" if cost is not None else "N/A")
        rows.append(
            {
                "slug": slug,
                "cost_usd_hr": cost_str,
                "description": HARDWARE_DESCRIPTIONS.get(slug, ""),
            }
        )
    return rows
