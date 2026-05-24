"""Pipeline state for the 3D / Immersive venture."""

from __future__ import annotations

from skyyrose.elite_studio.ventures._base import VentureState


class ThreeDState(VentureState, total=False):
    """3D-venture-specific keys layered onto the shared envelope."""

    source_image: str
    selected_provider: str
    candidate_meshes: list[dict[str, object]]
    winning_mesh_path: str
    polycount: int
    texture_size: int
