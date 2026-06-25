"""Pipeline state for the Video & Animation venture."""

from __future__ import annotations

from skyyrose.elite_studio.ventures._base import VentureState


class VideoState(VentureState, total=False):
    """Video-venture-specific keys layered onto the shared envelope."""

    source_image: str
    duration_seconds: float
    fps: int
    resolution: tuple[int, int]
    output_clip_path: str
    selected_provider: str
