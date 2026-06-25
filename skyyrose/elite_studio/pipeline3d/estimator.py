"""Whole-job cost estimate, computed ONCE before the job starts.

Sums the top-priority candidate's per-stage cost across the requested stages.
The CLI shows the single total via the STOP-AND-SHOW gate — not one prompt
per stage.
"""

from __future__ import annotations

from .models import JobSpec, ordered_stages
from .router import Router


def estimate(job: JobSpec, router: Router) -> dict:
    """Return ``{"by_stage": {stage: usd}, "total_usd": float}``."""
    by_stage: dict[str, float] = {}
    for stage in ordered_stages(job.stages):
        # Estimate from the priority-first CAPABLE engine (ignore availability) so
        # the dry-run shows real cost even before an API key is loaded.
        supporting = router.supporting(stage)
        cost = supporting[0].estimate_cost(stage, job.params) if supporting else 0.0
        by_stage[stage.value] = round(cost, 4)
    total = round(sum(by_stage.values()), 4)
    return {"by_stage": by_stage, "total_usd": total}


__all__ = ["estimate"]
