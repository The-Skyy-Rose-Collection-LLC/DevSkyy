"""Configuration for the Video & Animation venture."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from skyyrose.elite_studio.config import OUTPUT_DIR


@dataclass(frozen=True)
class VideoVentureConfig:
    """Static config consumed by the video pipeline.

    Video is the least-built venture. This config tracks output dir,
    default duration/fps, and provider defaults pulled from the
    existing `anigen_agent` (animation generation) and Elite Studio's
    `tryon_agent` (which produces video try-on output when wired to a
    video-capable backend).
    """

    output_dir: Path = field(default_factory=lambda: Path(OUTPUT_DIR) / "ventures" / "video")
    default_duration_seconds: float = 5.0
    default_fps: int = 24
    default_resolution: tuple[int, int] = (1080, 1920)  # vertical, 9:16
    providers: tuple[str, ...] = ("anigen", "tryon_video")
    smoke_timeout_seconds: float = 5.0


DEFAULT_CONFIG = VideoVentureConfig()
