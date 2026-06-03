from pathlib import Path

from skyyrose.elite_studio.pipeline3d.models import Artifact, Stage, StageResult
from skyyrose.elite_studio.pipeline3d.store import StageStore


def _result(tmp_path: Path) -> StageResult:
    art = Artifact(provider="tripo", task_id="t1", path=tmp_path / "m.glb", meta={"k": "v"})
    return StageResult(stage=Stage.IMAGE_TO_3D, artifact=art, cost_usd=0.4, duration_ms=123)


def test_miss_then_hit_roundtrip(tmp_path):
    store = StageStore(tmp_path / "store")
    h = "abc123"
    assert store.has(h, Stage.IMAGE_TO_3D) is False
    store.put(h, _result(tmp_path))
    assert store.has(h, Stage.IMAGE_TO_3D) is True
    got = store.get(h, Stage.IMAGE_TO_3D)
    assert got is not None
    assert got.cached is True
    assert got.artifact.task_id == "t1"
    assert got.artifact.path == tmp_path / "m.glb"
    assert got.artifact.meta == {"k": "v"}
    assert got.cost_usd == 0.4


def test_different_input_hash_is_isolated(tmp_path):
    store = StageStore(tmp_path / "store")
    store.put("hashA", _result(tmp_path))
    assert store.has("hashB", Stage.IMAGE_TO_3D) is False


def test_get_missing_returns_none(tmp_path):
    store = StageStore(tmp_path / "store")
    assert store.get("nope", Stage.REMESH) is None
