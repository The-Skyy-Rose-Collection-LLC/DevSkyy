from pathlib import Path

from skyyrose.elite_studio.pipeline3d.adapters.base import Adapter, StageContext
from skyyrose.elite_studio.pipeline3d.models import Artifact, Stage


class _FakeAdapter:
    name = "fake"

    def supports(self, stage: Stage) -> bool:
        return stage in (Stage.IMAGE_TO_3D, Stage.TEXTURE)

    def available(self) -> bool:
        return True

    def estimate_cost(self, stage: Stage, params: dict) -> float:
        return 1.0

    async def run_stage(self, stage: Stage, ctx: StageContext) -> Artifact:
        return Artifact(provider=self.name, task_id="t", path=ctx.output_dir / "x.glb")


def test_fake_satisfies_protocol():
    assert isinstance(_FakeAdapter(), Adapter)


def test_stage_context_defaults():
    ctx = StageContext(sku="br-001", source_image=Path("s.png"), output_dir=Path("/tmp/out"))
    assert ctx.last_artifact is None
    assert ctx.params == {}
