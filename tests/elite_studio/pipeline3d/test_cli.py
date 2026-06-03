from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from skyyrose.elite_studio.pipeline3d import cli
from skyyrose.elite_studio.pipeline3d.models import (
    Artifact,
    PipelineResult,
    Stage,
    TaskStatus,
)


def test_parse_stages_default_and_explicit():
    assert cli.parse_stages("image-to-3d,texture,remesh,export") == (
        Stage.IMAGE_TO_3D,
        Stage.TEXTURE,
        Stage.REMESH,
        Stage.EXPORT,
    )
    assert cli.parse_stages("image-to-3d,export") == (Stage.IMAGE_TO_3D, Stage.EXPORT)


def test_parse_stages_rejects_unknown():
    with pytest.raises(SystemExit):
        cli.parse_stages("image-to-3d,fly-to-moon")


def test_build_router_has_tripo_and_local():
    router = cli.build_router(api_key="tsk_test", output_dir=Path("/tmp/x"))
    names = {a.name for a in router._adapters}
    assert {"tripo", "local"} <= names


@pytest.mark.asyncio
async def test_dry_run_estimates_without_dispatch(tmp_path, capsys):
    img = tmp_path / "src.png"
    img.write_bytes(b"x")
    rc = await cli.run(
        [
            "--sku",
            "br-001",
            "--image",
            str(img),
            "--stages",
            "image-to-3d,texture,remesh,export",
            "--output-dir",
            str(tmp_path / "out"),
            "--api-key",
            "tsk_test",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "DRY RUN" in out
    assert "total" in out.lower()
    # nothing written to output dir on a dry run
    assert not (tmp_path / "out" / "br-001.glb").exists()


def test_preflight_failure_returns_exit_2(tmp_path, capsys):
    import asyncio

    rc = asyncio.run(
        cli.run(["--sku", "zz-999", "--image", str(tmp_path / "missing.png"), "--api-key", "k"])
    )
    err = capsys.readouterr().err
    assert rc == 2
    assert "preflight failed" in err


@pytest.mark.asyncio
async def test_go_path_dispatches_and_reports(tmp_path, capsys):
    img = tmp_path / "src.png"
    img.write_bytes(b"x")
    out_dir = tmp_path / "out"
    final = Artifact(provider="local", path=out_dir / "br-001.glb")
    fake_result = PipelineResult(
        job_id="run1",
        sku="br-001",
        status=TaskStatus.SUCCEEDED,
        results=(),
        final_artifact=final,
        total_cost_usd=0.75,
    )
    # stdin is not a TTY under pytest, so _confirm auto-approves; run_job is mocked
    # so NO paid call happens.
    with patch(
        "skyyrose.elite_studio.pipeline3d.cli.run_job",
        new=AsyncMock(return_value=fake_result),
    ) as mock_run:
        rc = await cli.run(
            [
                "--sku",
                "br-001",
                "--image",
                str(img),
                "--stages",
                "image-to-3d,texture,remesh,export",
                "--output-dir",
                str(out_dir),
                "--api-key",
                "tsk_test",
                "--go",
            ]
        )
    out = capsys.readouterr().out
    assert rc == 0
    mock_run.assert_awaited_once()
    assert "status: succeeded" in out
    assert "0.75" in out
