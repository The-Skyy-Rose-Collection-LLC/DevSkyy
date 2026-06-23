"""EXPORT stage: materialize the final artifact to the canonical output path.

GLB export is provider-agnostic — it is just a copy of the last stage's local
file to ``<output_dir>/<sku>.<fmt>``. This keeps the router uniform (every stage
has an adapter) without a paid call. Non-GLB export (USDZ/FBX) is a later phase
and goes through a provider convert stage, not here.
"""

from __future__ import annotations

import shutil

from ..models import Artifact, Stage
from .base import StageContext


class LocalExportAdapter:
    """Copies the prior artifact to the canonical output location. Cost 0."""

    name = "local"

    def supports(self, stage: Stage) -> bool:
        return stage == Stage.EXPORT

    def available(self) -> bool:
        return True

    def estimate_cost(self, stage: Stage, params: dict) -> float:
        return 0.0

    async def run_stage(self, stage: Stage, ctx: StageContext) -> Artifact:
        prior = ctx.last_artifact
        if prior is None or prior.path is None:
            raise ValueError("export stage requires a prior artifact with a local path")
        ctx.output_dir.mkdir(parents=True, exist_ok=True)
        dest = ctx.output_dir / f"{ctx.sku}.{prior.fmt}"
        shutil.copyfile(prior.path, dest)
        return Artifact(
            provider="local",
            fmt=prior.fmt,
            task_id=prior.task_id,
            model_url=prior.model_url,
            path=dest,
            polycount=prior.polycount,
            bytes=dest.stat().st_size,
            meta={**prior.meta, "exported_from": str(prior.path)},
        )


__all__ = ["LocalExportAdapter"]
