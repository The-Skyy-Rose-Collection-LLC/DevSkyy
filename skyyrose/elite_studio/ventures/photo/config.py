"""Configuration for the Editorial Photography venture."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from skyyrose.elite_studio.config import OUTPUT_DIR


@dataclass(frozen=True)
class PhotoVentureConfig:
    """Static config consumed by the photo pipeline.

    Values default to the project's canonical output dir and model
    assignments from `skyyrose.elite_studio.config`. Override per-call
    by constructing a new frozen instance — never mutate.
    """

    output_dir: Path = field(default_factory=lambda: Path(OUTPUT_DIR) / "ventures" / "photo")
    vision_model: str = "gemini-3-flash-preview"
    generator_model: str = "gemini-3-pro-image-preview"
    quality_model: str = "claude-sonnet-4"
    default_style: str = "editorial"
    smoke_timeout_seconds: float = 5.0


DEFAULT_CONFIG = PhotoVentureConfig()
