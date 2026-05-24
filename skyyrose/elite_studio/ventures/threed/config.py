"""Configuration for the 3D / Immersive venture."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from skyyrose.elite_studio.config import OUTPUT_DIR


@dataclass(frozen=True)
class ThreeDVentureConfig:
    """Static config consumed by the 3D pipeline.

    The venture composes the round-table tournament (Tripo, Meshy,
    TRELLIS) plus Elite Studio's internal `three_d_agent`. Provider
    selection is delegated to the tournament — this config tracks
    defaults, output path, and the smoke-pass timeout.
    """

    output_dir: Path = field(default_factory=lambda: Path(OUTPUT_DIR) / "ventures" / "threed")
    providers: tuple[str, ...] = ("tripo", "meshy", "trellis")
    default_polycount: int = 30_000
    default_texture_size: int = 2048
    smoke_timeout_seconds: float = 5.0


DEFAULT_CONFIG = ThreeDVentureConfig()
