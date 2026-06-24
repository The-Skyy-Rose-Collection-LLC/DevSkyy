import pytest

from skyyrose.elite_studio.pipeline3d.models import Artifact, Stage
from skyyrose.elite_studio.pipeline3d.router import NoAdapterError, Router


class _Stub:
    def __init__(self, name, stages, available=True):
        self.name = name
        self._stages = set(stages)
        self._available = available

    def supports(self, stage):
        return stage in self._stages

    def available(self):
        return self._available

    def estimate_cost(self, stage, params):
        return 0.0

    async def run_stage(self, stage, ctx):
        return Artifact(provider=self.name)


def test_pick_respects_priority():
    a = _Stub("tripo", [Stage.IMAGE_TO_3D])
    b = _Stub("meshy", [Stage.IMAGE_TO_3D])
    r = Router([b, a], priority=["tripo", "meshy"])
    assert r.pick(Stage.IMAGE_TO_3D).name == "tripo"


def test_pick_skips_unavailable():
    a = _Stub("tripo", [Stage.IMAGE_TO_3D], available=False)
    b = _Stub("meshy", [Stage.IMAGE_TO_3D])
    r = Router([a, b], priority=["tripo", "meshy"])
    assert r.pick(Stage.IMAGE_TO_3D).name == "meshy"


def test_pick_skips_incapable():
    a = _Stub("tripo", [Stage.TEXTURE])
    b = _Stub("local", [Stage.EXPORT])
    r = Router([a, b])
    assert r.pick(Stage.EXPORT).name == "local"


def test_exclude_enables_fallback():
    a = _Stub("tripo", [Stage.REMESH])
    b = _Stub("meshy", [Stage.REMESH])
    r = Router([a, b], priority=["tripo", "meshy"])
    assert r.pick(Stage.REMESH, exclude={"tripo"}).name == "meshy"


def test_no_adapter_raises():
    r = Router([_Stub("tripo", [Stage.IMAGE_TO_3D])])
    with pytest.raises(NoAdapterError):
        r.pick(Stage.EXPORT)


def test_supporting_ignores_availability_but_candidates_respects_it():
    a = _Stub("tripo", [Stage.IMAGE_TO_3D], available=False)
    r = Router([a], priority=["tripo"])
    # capability view includes the unavailable engine; dispatch view excludes it
    assert [x.name for x in r.supporting(Stage.IMAGE_TO_3D)] == ["tripo"]
    assert r.candidates(Stage.IMAGE_TO_3D) == []
    with pytest.raises(NoAdapterError):
        r.pick(Stage.IMAGE_TO_3D)
