"""The orchestration heart: run a JobSpec stage-by-stage.

Spine: synchronous-within-stage. Each stage's adapter blocks until the provider
returns an artifact. Job-level concurrency lives at the worker layer, not here.

Guarantees:
  * stages run in canonical dependency order (ordered_stages)
  * a stage already in the store is skipped (idempotent resume)
  * RunBudget.ensure_within_budget() gates BEFORE each paid dispatch
  * each stage is wrapped in a telemetry span
  * ctx.last_artifact threads one stage's output into the next (chaining)
  * a stage exception -> FAILED PipelineResult with partial results persisted
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from skyyrose.elite_studio import telemetry
from skyyrose.elite_studio.budget import BudgetExceededError, RunBudget

from .adapters.base import StageContext
from .models import JobSpec, PipelineResult, StageResult, TaskStatus, ordered_stages
from .router import Router
from .store import StageStore


async def run_job(
    job: JobSpec,
    *,
    router: Router,
    store: StageStore,
    budget: RunBudget,
    run_id: str | None = None,
    input_hash: str | None = None,
) -> PipelineResult:
    """Execute all requested stages and return a PipelineResult."""
    run_id = run_id or telemetry.new_run_id()
    # Fold params into the cache key so a re-run with different params (e.g. a new
    # target_polycount) never returns a stale cached mesh. Conservative by design:
    # any param change invalidates ALL stages for this input — correctness over
    # re-bill avoidance. Phase 3's store can refine to per-stage param fingerprints.
    input_hash = input_hash or telemetry.hash_inputs(
        str(job.source_image),
        job.sku,
        json.dumps(job.params, sort_keys=True, default=str),
    )

    ctx = StageContext(
        sku=job.sku,
        source_image=job.source_image,
        output_dir=Path(job.output_dir),
        params=dict(job.params),
    )
    results: list[StageResult] = []

    for stage in ordered_stages(job.stages):
        # Idempotent resume: skip stages already completed for this input.
        if store.has(input_hash, stage):
            cached = store.get(input_hash, stage)
            if cached is not None:
                ctx.last_artifact = cached.artifact
                results.append(cached)
                continue

        adapter = router.pick(stage)
        cost = adapter.estimate_cost(stage, ctx.params)

        # Budget gate raises BEFORE the paid call. Let it propagate — a job that
        # cannot afford a stage should halt loudly, not silently truncate.
        budget.ensure_within_budget(cost, stage.value)

        started = time.monotonic()
        try:
            with telemetry.stage(
                run_id=run_id,
                stage_name=stage.value,
                sku=job.sku,
                input_hash=input_hash,
            ) as span:
                span.set(provider=adapter.name)
                artifact = await adapter.run_stage(stage, ctx)
        except BudgetExceededError:
            raise
        except Exception as exc:  # noqa: BLE001 - stage isolation is intentional
            return PipelineResult(
                job_id=run_id,
                sku=job.sku,
                status=TaskStatus.FAILED,
                results=tuple(results),
                final_artifact=results[-1].artifact if results else None,
                total_cost_usd=round(sum(r.cost_usd for r in results), 4),
                error=f"{stage.value}: {exc}",
            )

        duration_ms = int((time.monotonic() - started) * 1000)
        budget.spend(cost, stage.value)
        result = StageResult(stage=stage, artifact=artifact, cost_usd=cost, duration_ms=duration_ms)
        store.put(input_hash, result)
        results.append(result)
        ctx.last_artifact = artifact

    return PipelineResult(
        job_id=run_id,
        sku=job.sku,
        status=TaskStatus.SUCCEEDED,
        results=tuple(results),
        final_artifact=results[-1].artifact if results else None,
        total_cost_usd=round(sum(r.cost_usd for r in results), 4),
    )


__all__ = ["run_job"]
