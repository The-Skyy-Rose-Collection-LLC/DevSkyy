"""Pipeline state for the 3D / Immersive venture (TRELLIS-only / self-hosted)."""

from __future__ import annotations

from skyyrose.elite_studio.ventures._base import VentureState


class ThreeDState(VentureState, total=False):
    """3D-venture-specific keys layered onto the shared envelope.

    Compute gate: `generate_3d` defaults to False. The generation node runs
    the self-hosted TRELLIS.2 model (heavy GPU + minutes per mesh) only when
    the flag is True. The default path — every smoke run and test — exercises
    the free capability-verification path and never spins up the model.
    """

    source_image: str
    product_name: str
    generate_3d: bool
    connectivity: dict[str, object]
    winning_mesh_path: str
    selected_provider: str
    decimation_target: int
    texture_size: int
