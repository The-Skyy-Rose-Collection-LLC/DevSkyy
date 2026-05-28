"""Configuration for the 3D / Immersive venture.

TRELLIS-only / self-hosted: the venture generates 3D replicas on our own
compute (microsoft/TRELLIS.2-4B in the isolated `trellis2` conda env) via
`agents.trellis_agent.TrellisAgent`. Tripo and Meshy remain registered in
`agents.py` as legacy SaaS providers but are NOT invoked from this venture
— per the product directive: own the engine, don't refer out to a vendor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from skyyrose.elite_studio.config import OUTPUT_DIR


@dataclass(frozen=True)
class ThreeDVentureConfig:
    """Static config consumed by the self-hosted 3D pipeline.

    Defaults mirror `agents.trellis_agent` module constants so the venture
    and the engine agree on env/model/quality without duplication drift.
    Override per-call by constructing a new frozen instance — never mutate.
    """

    output_dir: Path = field(default_factory=lambda: Path(OUTPUT_DIR) / "ventures" / "threed")
    # The only engine the venture invokes. Self-hosted, our compute.
    engine: str = "trellis"
    conda_env: str = "trellis2"
    model_repo: str = "microsoft/TRELLIS.2-4B"
    default_decimation_target: int = 1_000_000
    default_texture_size: int = 4096
    # A real catalog SKU whose techflat/source image the smoke + verify paths
    # reference (resolution proof only — never generates without the gate).
    smoke_sku: str = "br-001"
    smoke_timeout_seconds: float = 5.0


DEFAULT_CONFIG = ThreeDVentureConfig()
