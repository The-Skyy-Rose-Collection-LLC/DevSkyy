import builtins
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


def test_parse_stages_skips_empty_tokens():
    # trailing/double commas are tolerated, not errors
    assert cli.parse_stages("image-to-3d,,export,") == (Stage.IMAGE_TO_3D, Stage.EXPORT)


def test_parse_stages_empty_raises():
    with pytest.raises(SystemExit):
        cli.parse_stages(" , , ")


def test_build_router_has_tripo_and_local():
    router = cli.build_router(api_key="tsk_test", output_dir=Path("/tmp/x"))
    names = {a.name for a in router._adapters}
    assert {"tripo", "local"} <= names


# --------------------------------------------------------------------------- #
# _confirm — the STOP-AND-SHOW money gate                                      #
# --------------------------------------------------------------------------- #

_EST = {"by_stage": {"image_to_3d": 0.40, "export": 0.0}, "total_usd": 0.40}


def test_confirm_auto_confirm_env_prints_banner_and_proceeds(monkeypatch, capsys):
    monkeypatch.setenv("SKYYROSE_AUTO_CONFIRM", "1")
    ok = cli._confirm(sku="br-001", source=Path("s.png"), est=_EST)
    out = capsys.readouterr().out
    assert ok is True
    assert "STOP — Confirm before proceeding" in out  # banner ALWAYS prints
    assert "auto-confirmed" in out


def test_confirm_non_tty_aborts_after_printing_banner(monkeypatch, capsys):
    monkeypatch.delenv("SKYYROSE_AUTO_CONFIRM", raising=False)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: False)
    ok = cli._confirm(sku="br-001", source=Path("s.png"), est=_EST)
    out = capsys.readouterr().out
    assert ok is False  # fail-closed: no silent paid dispatch
    assert "STOP — Confirm before proceeding" in out
    assert "non-interactive context — aborting" in out


def test_confirm_interactive_yes(monkeypatch):
    monkeypatch.delenv("SKYYROSE_AUTO_CONFIRM", raising=False)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(builtins, "input", lambda: "y")
    assert cli._confirm(sku="br-001", source=Path("s.png"), est=_EST) is True


def test_confirm_interactive_no(monkeypatch):
    monkeypatch.delenv("SKYYROSE_AUTO_CONFIRM", raising=False)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(builtins, "input", lambda: "n")
    assert cli._confirm(sku="br-001", source=Path("s.png"), est=_EST) is False


def test_confirm_interactive_eof_aborts(monkeypatch):
    monkeypatch.delenv("SKYYROSE_AUTO_CONFIRM", raising=False)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)

    def _raise():
        raise EOFError

    monkeypatch.setattr(builtins, "input", _raise)
    assert cli._confirm(sku="br-001", source=Path("s.png"), est=_EST) is False


# --------------------------------------------------------------------------- #
# run() — end-to-end CLI paths                                                 #
# --------------------------------------------------------------------------- #


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
    captured = capsys.readouterr()
    assert rc == 0
    assert "DRY RUN" in captured.out
    assert "total" in captured.out.lower()
    # --api-key emits a process-listing warning
    assert "process listings" in captured.err
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


def test_invalid_sku_returns_exit_2(tmp_path, capsys):
    import asyncio

    rc = asyncio.run(cli.run(["--sku", "../etc", "--image", str(tmp_path / "x.png")]))
    err = capsys.readouterr().err
    assert rc == 2
    assert "invalid sku format" in err


@pytest.mark.asyncio
async def test_go_over_budget_aborts_before_dispatch(tmp_path, capsys):
    img = tmp_path / "src.png"
    img.write_bytes(b"x")
    with patch("skyyrose.elite_studio.pipeline3d.cli.run_job", new=AsyncMock()) as mock_run:
        rc = await cli.run(
            [
                "--sku",
                "br-001",
                "--image",
                str(img),
                "--stages",
                "image-to-3d,texture,remesh",
                "--budget",
                "0.10",
                "--api-key",
                "tsk_test",
                "--go",
            ]
        )
    err = capsys.readouterr().err
    assert rc == 1
    assert "exceeds budget ceiling" in err
    mock_run.assert_not_awaited()  # never dispatched


@pytest.mark.asyncio
async def test_go_aborted_by_user(tmp_path, capsys):
    img = tmp_path / "src.png"
    img.write_bytes(b"x")
    with (
        patch("skyyrose.elite_studio.pipeline3d.cli._confirm", return_value=False),
        patch("skyyrose.elite_studio.pipeline3d.cli.run_job", new=AsyncMock()) as mock_run,
    ):
        rc = await cli.run(
            ["--sku", "br-001", "--image", str(img), "--api-key", "tsk_test", "--go"]
        )
    out = capsys.readouterr().out
    assert rc == 1
    assert "aborted by user" in out
    mock_run.assert_not_awaited()


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
    # Patch the gate explicitly (do NOT rely on TTY absence) so this test exercises
    # the dispatch path, and run_job is mocked so NO paid call happens.
    with (
        patch("skyyrose.elite_studio.pipeline3d.cli._confirm", return_value=True),
        patch(
            "skyyrose.elite_studio.pipeline3d.cli.run_job",
            new=AsyncMock(return_value=fake_result),
        ) as mock_run,
    ):
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


@pytest.mark.asyncio
async def test_go_path_reports_failure(tmp_path, capsys):
    img = tmp_path / "src.png"
    img.write_bytes(b"x")
    fake_result = PipelineResult(
        job_id="run1",
        sku="br-001",
        status=TaskStatus.FAILED,
        results=(),
        final_artifact=None,
        total_cost_usd=0.40,
        error="image_to_3d: boom",
    )
    with (
        patch("skyyrose.elite_studio.pipeline3d.cli._confirm", return_value=True),
        patch(
            "skyyrose.elite_studio.pipeline3d.cli.run_job",
            new=AsyncMock(return_value=fake_result),
        ),
    ):
        rc = await cli.run(
            ["--sku", "br-001", "--image", str(img), "--api-key", "tsk_test", "--go"]
        )
    captured = capsys.readouterr()
    assert rc == 1
    assert "status: failed" in captured.out
    assert "error: image_to_3d: boom" in captured.err


def test_main_invokes_run(monkeypatch):
    monkeypatch.setattr(cli.sys, "argv", ["gen3d", "--sku", "br-001", "--image", "nope.png"])
    monkeypatch.setattr(cli, "run", AsyncMock(return_value=2))
    assert cli.main() == 2


def test_module_entrypoint_imports():
    # Covers the `python -m ...pipeline3d` shim module body.
    import skyyrose.elite_studio.pipeline3d.__main__ as entry

    assert entry.main is cli.main
