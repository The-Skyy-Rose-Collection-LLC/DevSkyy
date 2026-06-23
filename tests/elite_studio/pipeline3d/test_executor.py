import pytest

from skyyrose.elite_studio.budget import BudgetExceededError, RunBudget
from skyyrose.elite_studio.pipeline3d.executor import run_job
from skyyrose.elite_studio.pipeline3d.models import (
    Artifact,
    JobSpec,
    Stage,
    StageResult,
    TaskStatus,
)
from skyyrose.elite_studio.pipeline3d.router import Router
from skyyrose.elite_studio.pipeline3d.store import StageStore


class _RecordingAdapter:
    """Records calls; produces a deterministic artifact carrying the prior task_id."""

    def __init__(self, name, stages, cost=0.5, fail_on=None):
        self.name = name
        self._stages = set(stages)
        self._cost = cost
        self._fail_on = fail_on
        self.calls = []

    def supports(self, stage):
        return stage in self._stages

    def available(self):
        return True

    def estimate_cost(self, stage, params):
        return self._cost

    async def run_stage(self, stage, ctx):
        self.calls.append((stage, ctx.last_artifact.task_id if ctx.last_artifact else None))
        if self._fail_on is not None and stage == self._fail_on:
            raise RuntimeError(f"boom at {stage.value}")
        return Artifact(
            provider=self.name, task_id=f"{stage.value}-id", path=ctx.output_dir / "m.glb"
        )


def _job(tmp_path, stages):
    return JobSpec(
        sku="br-001",
        source_image=tmp_path / "src.png",
        stages=stages,
        output_dir=tmp_path / "out",
    )


@pytest.mark.asyncio
async def test_runs_stages_in_order_and_chains_task_id(tmp_path):
    adapter = _RecordingAdapter("tripo", [Stage.IMAGE_TO_3D, Stage.TEXTURE, Stage.REMESH])
    router = Router([adapter], priority=["tripo"])
    store = StageStore(tmp_path / "store")
    budget = RunBudget(ceiling_usd=10.0)
    job = _job(tmp_path, (Stage.REMESH, Stage.IMAGE_TO_3D, Stage.TEXTURE))

    result = await run_job(job, router=router, store=store, budget=budget)

    assert result.status is TaskStatus.SUCCEEDED
    assert [s for s, _ in adapter.calls] == [Stage.IMAGE_TO_3D, Stage.TEXTURE, Stage.REMESH]
    # chaining: texture saw image_to_3d's task_id; remesh saw texture's
    assert adapter.calls[1][1] == "image_to_3d-id"
    assert adapter.calls[2][1] == "texture-id"
    assert result.total_cost_usd == 1.5


@pytest.mark.asyncio
async def test_budget_blocks_before_paid_call(tmp_path):
    adapter = _RecordingAdapter("tripo", [Stage.IMAGE_TO_3D], cost=99.0)
    router = Router([adapter], priority=["tripo"])
    store = StageStore(tmp_path / "store")
    budget = RunBudget(ceiling_usd=1.0)
    job = _job(tmp_path, (Stage.IMAGE_TO_3D,))

    with pytest.raises(BudgetExceededError):
        await run_job(job, router=router, store=store, budget=budget)
    assert adapter.calls == []  # never dispatched


@pytest.mark.asyncio
async def test_cached_stage_is_skipped(tmp_path):
    adapter = _RecordingAdapter("tripo", [Stage.IMAGE_TO_3D, Stage.TEXTURE])
    router = Router([adapter], priority=["tripo"])
    store = StageStore(tmp_path / "store")
    budget = RunBudget(ceiling_usd=10.0)
    h = "fixedhash"
    # pre-seed IMAGE_TO_3D
    store.put(
        h,
        StageResult(
            stage=Stage.IMAGE_TO_3D,
            artifact=Artifact(provider="tripo", task_id="cached-id", path=tmp_path / "c.glb"),
            cost_usd=0.4,
            duration_ms=5,
        ),
    )
    job = _job(tmp_path, (Stage.IMAGE_TO_3D, Stage.TEXTURE))

    result = await run_job(job, router=router, store=store, budget=budget, input_hash=h)

    # image_to_3d skipped; only texture ran, and it chained the cached task_id
    assert [s for s, _ in adapter.calls] == [Stage.TEXTURE]
    assert adapter.calls[0][1] == "cached-id"
    assert result.results[0].cached is True
    assert budget.spent_usd == 0.5  # only texture charged


@pytest.mark.asyncio
async def test_stage_failure_returns_partial_failed_result(tmp_path):
    adapter = _RecordingAdapter("tripo", [Stage.IMAGE_TO_3D, Stage.TEXTURE], fail_on=Stage.TEXTURE)
    router = Router([adapter], priority=["tripo"])
    store = StageStore(tmp_path / "store")
    budget = RunBudget(ceiling_usd=10.0)
    job = _job(tmp_path, (Stage.IMAGE_TO_3D, Stage.TEXTURE))

    result = await run_job(job, router=router, store=store, budget=budget)

    assert result.status is TaskStatus.FAILED
    assert result.error is not None and "boom" in result.error
    assert len(result.results) == 1  # image_to_3d succeeded and is persisted
    # image_to_3d cost charged, texture not
    assert budget.spent_usd == 0.5


class _BudgetBombAdapter:
    """An adapter whose run_stage itself raises BudgetExceededError."""

    name = "tripo"

    def supports(self, stage):
        return True

    def available(self):
        return True

    def estimate_cost(self, stage, params):
        return 0.0

    async def run_stage(self, stage, ctx):
        raise BudgetExceededError("hard stop inside stage")


@pytest.mark.asyncio
async def test_budget_error_from_within_stage_propagates(tmp_path):
    # A BudgetExceededError raised DURING run_stage must propagate, not be
    # swallowed into a soft FAILED result by the generic except.
    router = Router([_BudgetBombAdapter()], priority=["tripo"])
    store = StageStore(tmp_path / "store")
    budget = RunBudget(ceiling_usd=10.0)
    job = _job(tmp_path, (Stage.IMAGE_TO_3D,))
    with pytest.raises(BudgetExceededError):
        await run_job(job, router=router, store=store, budget=budget)


@pytest.mark.asyncio
async def test_present_but_unreadable_cache_record_is_not_skipped(tmp_path):
    # store.has() True but store.get() None (falsy on-disk record) -> the stage is
    # re-run rather than silently skipped (executor branch 54->59).
    adapter = _RecordingAdapter("tripo", [Stage.IMAGE_TO_3D])
    router = Router([adapter], priority=["tripo"])
    store_root = tmp_path / "store"
    store = StageStore(store_root)
    h = "fixedhash"
    # Write a record where the stage key exists but maps to a falsy value.
    (store_root / f"{h}.json").write_text('{"image_to_3d": null}', encoding="utf-8")
    assert store.has(h, Stage.IMAGE_TO_3D) is True
    assert store.get(h, Stage.IMAGE_TO_3D) is None

    budget = RunBudget(ceiling_usd=10.0)
    job = _job(tmp_path, (Stage.IMAGE_TO_3D,))
    result = await run_job(job, router=router, store=store, budget=budget, input_hash=h)

    assert [s for s, _ in adapter.calls] == [Stage.IMAGE_TO_3D]  # re-ran, not skipped
    assert result.status is TaskStatus.SUCCEEDED
