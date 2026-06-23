from pathlib import Path

from skyyrose.elite_studio.pipeline3d.estimator import estimate
from skyyrose.elite_studio.pipeline3d.models import Artifact, JobSpec, Stage
from skyyrose.elite_studio.pipeline3d.router import Router


class _Stub:
    def __init__(self, name, costs, available=True):
        self.name = name
        self._costs = costs  # dict[Stage, float]
        self._available = available

    def supports(self, stage):
        return stage in self._costs

    def available(self):
        return self._available

    def estimate_cost(self, stage, params):
        return self._costs[stage]

    async def run_stage(self, stage, ctx):
        return Artifact(provider=self.name)


def test_estimate_sums_per_stage_from_top_priority():
    tripo = _Stub("tripo", {Stage.IMAGE_TO_3D: 0.40, Stage.TEXTURE: 0.20, Stage.REMESH: 0.15})
    local = _Stub("local", {Stage.EXPORT: 0.0})
    router = Router([tripo, local], priority=["tripo", "local"])
    job = JobSpec(
        sku="br-001",
        source_image=Path("s.png"),
        stages=(Stage.IMAGE_TO_3D, Stage.TEXTURE, Stage.REMESH, Stage.EXPORT),
    )
    out = estimate(job, router)
    assert out["by_stage"] == {
        "image_to_3d": 0.40,
        "texture": 0.20,
        "remesh": 0.15,
        "export": 0.0,
    }
    assert out["total_usd"] == 0.75


def test_estimate_zero_when_no_candidate():
    router = Router([_Stub("tripo", {Stage.IMAGE_TO_3D: 0.40})], priority=["tripo"])
    job = JobSpec(sku="x", source_image=Path("s.png"), stages=(Stage.EXPORT,))
    out = estimate(job, router)
    assert out["by_stage"] == {"export": 0.0}
    assert out["total_usd"] == 0.0


def test_estimate_prices_capable_engine_even_when_unavailable():
    # Regression: dry-run must show real cost even with no API key loaded.
    tripo = _Stub("tripo", {Stage.IMAGE_TO_3D: 0.40, Stage.REMESH: 0.15}, available=False)
    router = Router([tripo], priority=["tripo"])
    job = JobSpec(
        sku="br-001",
        source_image=Path("s.png"),
        stages=(Stage.IMAGE_TO_3D, Stage.REMESH),
    )
    out = estimate(job, router)
    assert out["by_stage"] == {"image_to_3d": 0.40, "remesh": 0.15}
    assert out["total_usd"] == 0.55
