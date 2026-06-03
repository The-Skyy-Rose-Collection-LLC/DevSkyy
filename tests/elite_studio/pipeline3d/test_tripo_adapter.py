from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skyyrose.elite_studio.pipeline3d.adapters.base import StageContext
from skyyrose.elite_studio.pipeline3d.adapters.tripo import TripoAdapter
from skyyrose.elite_studio.pipeline3d.models import Artifact, Stage


def test_capabilities_and_availability():
    a = TripoAdapter(api_key="tsk_test")
    assert a.name == "tripo"
    assert a.supports(Stage.IMAGE_TO_3D) is True
    assert a.supports(Stage.TEXTURE) is True
    assert a.supports(Stage.REMESH) is True
    assert a.supports(Stage.EXPORT) is False
    assert a.available() is True
    assert TripoAdapter(api_key="").available() is False


def test_estimate_cost_per_stage():
    a = TripoAdapter(api_key="tsk_test")
    assert a.estimate_cost(Stage.IMAGE_TO_3D, {}) > 0
    assert a.estimate_cost(Stage.EXPORT, {}) == 0.0


def _mock_client(tmp_path):
    """Build a mock TripoClient usable as an async context manager."""
    client = MagicMock()
    client.image_to_model = AsyncMock(return_value="img-task-1")
    client.texture_model = AsyncMock(return_value="tex-task-1")
    client.smart_lowpoly = AsyncMock(return_value="remesh-task-1")
    task = MagicMock()
    task.status = "success"
    task.output = MagicMock(model="https://tripo/model.glb")
    client.wait_for_task = AsyncMock(return_value=task)
    downloaded = tmp_path / "dl.glb"
    downloaded.write_bytes(b"glb")
    client.download_task_models = AsyncMock(return_value={"model": str(downloaded)})
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm, client, downloaded


@pytest.mark.asyncio
async def test_image_to_3d_submits_and_downloads(tmp_path):
    cm, client, downloaded = _mock_client(tmp_path)
    ctx = StageContext(
        sku="br-001",
        source_image=tmp_path / "src.png",
        output_dir=tmp_path / "out",
    )
    a = TripoAdapter(api_key="tsk_test", output_dir=tmp_path / "out")
    with patch("skyyrose.elite_studio.pipeline3d.adapters.tripo.TripoClient", return_value=cm):
        art = await a.run_stage(Stage.IMAGE_TO_3D, ctx)
    client.image_to_model.assert_awaited_once()
    assert art.provider == "tripo"
    assert art.task_id == "img-task-1"
    assert art.model_url == "https://tripo/model.glb"
    assert art.path == downloaded


@pytest.mark.asyncio
async def test_texture_chains_prior_task_id(tmp_path):
    cm, client, _ = _mock_client(tmp_path)
    ctx = StageContext(sku="br-001", source_image=tmp_path / "s.png", output_dir=tmp_path / "out")
    ctx.last_artifact = Artifact(provider="tripo", task_id="img-task-1", path=tmp_path / "m.glb")
    a = TripoAdapter(api_key="tsk_test", output_dir=tmp_path / "out")
    with patch("skyyrose.elite_studio.pipeline3d.adapters.tripo.TripoClient", return_value=cm):
        art = await a.run_stage(Stage.TEXTURE, ctx)
    client.texture_model.assert_awaited_once_with(
        original_model_task_id="img-task-1", texture=True, pbr=True
    )
    assert art.task_id == "tex-task-1"


@pytest.mark.asyncio
async def test_remesh_uses_smart_lowpoly_with_face_limit(tmp_path):
    cm, client, _ = _mock_client(tmp_path)
    ctx = StageContext(
        sku="br-001",
        source_image=tmp_path / "s.png",
        output_dir=tmp_path / "out",
        params={"target_polycount": 12000},
    )
    ctx.last_artifact = Artifact(provider="tripo", task_id="tex-task-1", path=tmp_path / "m.glb")
    a = TripoAdapter(api_key="tsk_test", output_dir=tmp_path / "out")
    with patch("skyyrose.elite_studio.pipeline3d.adapters.tripo.TripoClient", return_value=cm):
        art = await a.run_stage(Stage.REMESH, ctx)
    client.smart_lowpoly.assert_awaited_once_with(
        original_model_task_id="tex-task-1", face_limit=12000, quad=False
    )
    assert art.task_id == "remesh-task-1"


@pytest.mark.asyncio
async def test_texture_without_prior_task_id_raises(tmp_path):
    ctx = StageContext(sku="x", source_image=tmp_path / "s.png", output_dir=tmp_path / "out")
    a = TripoAdapter(api_key="tsk_test", output_dir=tmp_path / "out")
    with pytest.raises(ValueError):
        await a.run_stage(Stage.TEXTURE, ctx)
