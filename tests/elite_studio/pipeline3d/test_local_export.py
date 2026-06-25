import pytest

from skyyrose.elite_studio.pipeline3d.adapters.base import StageContext
from skyyrose.elite_studio.pipeline3d.adapters.local_export import LocalExportAdapter
from skyyrose.elite_studio.pipeline3d.models import Artifact, Stage


def test_supports_only_export():
    a = LocalExportAdapter()
    assert a.supports(Stage.EXPORT) is True
    assert a.supports(Stage.IMAGE_TO_3D) is False
    assert a.available() is True
    assert a.estimate_cost(Stage.EXPORT, {}) == 0.0


@pytest.mark.asyncio
async def test_export_copies_prior_artifact_to_canonical_path(tmp_path):
    src = tmp_path / "intermediate.glb"
    src.write_bytes(b"glTF-bytes")
    out = tmp_path / "out"
    ctx = StageContext(sku="br-001", source_image=tmp_path / "s.png", output_dir=out)
    ctx.last_artifact = Artifact(provider="tripo", task_id="t9", path=src, fmt="glb")

    a = LocalExportAdapter()
    art = await a.run_stage(Stage.EXPORT, ctx)

    dest = out / "br-001.glb"
    assert dest.is_file()
    assert dest.read_bytes() == b"glTF-bytes"
    assert art.path == dest
    assert art.provider == "local"
    assert art.task_id == "t9"  # carries provenance forward


@pytest.mark.asyncio
async def test_export_without_prior_path_raises(tmp_path):
    ctx = StageContext(sku="x", source_image=tmp_path / "s.png", output_dir=tmp_path / "o")
    a = LocalExportAdapter()
    with pytest.raises(ValueError):
        await a.run_stage(Stage.EXPORT, ctx)
