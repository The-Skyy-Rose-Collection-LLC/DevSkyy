"""Pipeline state for the Editorial Photography venture."""

from __future__ import annotations

from typing import TypedDict

from skyyrose.elite_studio.ventures._base import VentureState


class PhotoState(VentureState, total=False):
    """Photo-venture-specific keys layered onto the shared envelope."""

    style: str
    lighting: str
    background: str
    photography_standard: dict[str, object]
    selected_frames: list[str]


class _NodeReport(TypedDict):
    node: str
    ok: bool
    detail: str
