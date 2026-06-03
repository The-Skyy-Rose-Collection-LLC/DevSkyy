"""Adapter port and the per-job mutable StageContext.

An Adapter wraps one provider (Tripo, Meshy, TRELLIS, local). The executor
holds a StageContext and threads each stage's output into the next via
``ctx.last_artifact`` — that is the chaining seam.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

from ..models import Artifact, Stage


@dataclass
class StageContext:
    """Per-job context threaded through stages.

    Intentionally NOT frozen — unlike every other dataclass in the package.
    ``last_artifact`` is the chaining seam the executor reassigns after each
    stage. Do not "fix" this to ``frozen=True``; that would break chaining.
    """

    sku: str
    source_image: Path
    output_dir: Path
    last_artifact: Artifact | None = None
    params: dict = field(default_factory=dict)


@runtime_checkable
class Adapter(Protocol):
    """A provider behind one or more pipeline stages."""

    name: str

    def supports(self, stage: Stage) -> bool:
        """True if this adapter can run the given stage."""
        ...

    def available(self) -> bool:
        """True if this adapter is usable now (e.g. API key present)."""
        ...

    def estimate_cost(self, stage: Stage, params: dict) -> float:
        """Estimated USD cost for running the given stage."""
        ...

    async def run_stage(self, stage: Stage, ctx: StageContext) -> Artifact:
        """Execute the stage (blocking: submit -> poll -> download) and return the artifact."""
        ...
