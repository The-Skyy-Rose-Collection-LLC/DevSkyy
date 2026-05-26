"""Unit tests for cli-anything-trellis core modules.

All tests run without GPU, CUDA, torch, trellis2, or o_voxel.
E2E tests that require the actual TRELLIS.2 runtime are in test_full_e2e.py
and are gated behind TRELLIS_E2E=1.

Coverage targets:
    - cli_anything.trellis.core.generation  (GenerationRecord, helpers)
    - cli_anything.trellis.core.session     (Session, _locked_save_json)
    - cli_anything.trellis.core.catalog     (append, iter, list, find, stats)
    - cli_anything.trellis.utils.trellis_backend (error types, discovery, env)
    - cli_anything.trellis.trellis_cli      (CLI commands via Click test runner)
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from cli_anything.trellis.core.catalog import (append_record, catalog_stats,
                                               find_record, iter_records,
                                               list_records)
from cli_anything.trellis.core.generation import (DEFAULT_RESOLUTION,
                                                  RESOLUTION_PRESETS,
                                                  STATUS_DONE, STATUS_FAILED,
                                                  STATUS_PENDING,
                                                  STATUS_RUNNING,
                                                  GenerationRecord, new_job_id,
                                                  validate_status)
from cli_anything.trellis.core.session import (MAX_HISTORY, SCHEMA, Session,
                                               _locked_save_json)
from cli_anything.trellis.trellis_cli import cli
from cli_anything.trellis.utils.trellis_backend import (
    BackendError, GPUUnavailableError, RunnerError, RunnerTimeoutError,
    TrellisNotFoundError, TrellisPythonError, build_runner_env,
    discover_trellis_home, discover_trellis_python)
from click.testing import CliRunner

# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture()
def tmp_image(tmp_path: Path) -> Path:
    """Create a minimal valid PNG file."""
    img = tmp_path / "test.png"
    # Minimal 1×1 white PNG (89 bytes, valid header)
    img.write_bytes(
        b"\x89PNG\r\n\x1a\n"  # PNG signature
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return img


@pytest.fixture()
def tmp_catalog(tmp_path: Path) -> Path:
    """Return a path for a temporary catalog file."""
    return tmp_path / "catalog.jsonl"


@pytest.fixture()
def sample_record(tmp_image: Path, tmp_path: Path) -> GenerationRecord:
    """Return a pending GenerationRecord with real file paths."""
    return GenerationRecord.new(
        image_path=str(tmp_image),
        output_dir=str(tmp_path / "output"),
    )


@pytest.fixture()
def done_record(sample_record: GenerationRecord, tmp_path: Path) -> GenerationRecord:
    """Return a done GenerationRecord."""
    glb = tmp_path / "output" / f"{sample_record.job_id}.glb"
    glb.parent.mkdir(parents=True, exist_ok=True)
    glb.write_bytes(b"GLB")
    running = sample_record.mark_running()
    return running.mark_done(str(glb))


# ═══════════════════════════════════════════════════════════════════════════════
# TestJobId
# ═══════════════════════════════════════════════════════════════════════════════


class TestJobId:
    def test_length(self):
        """job_id is exactly 16 hex chars (8 bytes)."""
        jid = new_job_id()
        assert len(jid) == 16

    def test_hex_chars(self):
        """job_id contains only lowercase hex characters."""
        jid = new_job_id()
        assert all(c in "0123456789abcdef" for c in jid)

    def test_unique(self):
        """Two consecutive job IDs are different."""
        ids = {new_job_id() for _ in range(100)}
        assert len(ids) == 100


# ═══════════════════════════════════════════════════════════════════════════════
# TestResolutionPresets
# ═══════════════════════════════════════════════════════════════════════════════


class TestResolutionPresets:
    def test_presets_exist(self):
        assert "low" in RESOLUTION_PRESETS
        assert "high" in RESOLUTION_PRESETS

    def test_preset_keys(self):
        for preset in RESOLUTION_PRESETS.values():
            assert "sparse_structure_sampler_params" in preset
            assert "shape_slat_sampler_params" in preset
            assert "tex_slat_sampler_params" in preset

    def test_default_resolution(self):
        assert DEFAULT_RESOLUTION in RESOLUTION_PRESETS

    @pytest.mark.parametrize("preset", ["low", "high"])
    def test_steps_positive(self, preset):
        p = RESOLUTION_PRESETS[preset]
        assert p["sparse_structure_sampler_params"]["steps"] > 0
        assert p["shape_slat_sampler_params"]["steps"] > 0


# ═══════════════════════════════════════════════════════════════════════════════
# TestGenerationRecord
# ═══════════════════════════════════════════════════════════════════════════════


class TestGenerationRecord:
    def test_new_creates_pending(self, tmp_image: Path, tmp_path: Path):
        r = GenerationRecord.new(
            image_path=str(tmp_image),
            output_dir=str(tmp_path / "out"),
        )
        assert r.status == STATUS_PENDING
        assert r.glb_path is None
        assert r.error is None

    def test_new_resolves_paths(self, tmp_image: Path, tmp_path: Path):
        r = GenerationRecord.new(
            image_path=str(tmp_image),
            output_dir=str(tmp_path),
        )
        assert Path(r.image_path).is_absolute()
        assert Path(r.output_dir).is_absolute()

    def test_new_invalid_resolution_raises(self, tmp_image: Path, tmp_path: Path):
        with pytest.raises(ValueError, match="Unknown resolution preset"):
            GenerationRecord.new(
                image_path=str(tmp_image),
                output_dir=str(tmp_path),
                resolution="ultra",
            )

    def test_mark_running(self, sample_record: GenerationRecord):
        r = sample_record.mark_running()
        assert r.status == STATUS_RUNNING
        assert r.started_at is not None
        # original unchanged (immutability)
        assert sample_record.status == STATUS_PENDING

    def test_mark_done(self, sample_record: GenerationRecord, tmp_path: Path):
        glb = tmp_path / "out.glb"
        glb.write_bytes(b"GLB")
        running = sample_record.mark_running()
        done = running.mark_done(str(glb))
        assert done.status == STATUS_DONE
        assert done.glb_path is not None
        assert done.finished_at is not None

    def test_mark_failed(self, sample_record: GenerationRecord):
        failed = sample_record.mark_failed("GPU exploded")
        assert failed.status == STATUS_FAILED
        assert failed.error == "GPU exploded"
        assert failed.finished_at is not None

    def test_is_terminal_done(self, done_record: GenerationRecord):
        assert done_record.is_terminal is True

    def test_is_terminal_pending(self, sample_record: GenerationRecord):
        assert sample_record.is_terminal is False

    def test_is_terminal_running(self, sample_record: GenerationRecord):
        r = sample_record.mark_running()
        assert r.is_terminal is False

    def test_duration_seconds(self, sample_record: GenerationRecord, tmp_path: Path):
        glb = tmp_path / "x.glb"
        glb.write_bytes(b"g")
        running = sample_record.mark_running()
        time.sleep(0.01)
        done = running.mark_done(str(glb))
        assert done.duration_seconds is not None
        assert done.duration_seconds >= 0

    def test_duration_seconds_none_when_not_started(self, sample_record: GenerationRecord):
        assert sample_record.duration_seconds is None

    def test_sampler_params(self, sample_record: GenerationRecord):
        params = sample_record.sampler_params
        assert "sparse_structure_sampler_params" in params

    def test_roundtrip_serialization(self, sample_record: GenerationRecord):
        d = sample_record.to_dict()
        restored = GenerationRecord.from_dict(d)
        assert restored.job_id == sample_record.job_id
        assert restored.status == sample_record.status
        assert restored.image_path == sample_record.image_path

    def test_from_dict_missing_keys_raises(self):
        with pytest.raises(ValueError, match="missing keys"):
            GenerationRecord.from_dict({"job_id": "abc"})

    def test_repr(self, sample_record: GenerationRecord):
        r = repr(sample_record)
        assert "GenerationRecord" in r
        assert sample_record.job_id in r

    def test_extra_field_roundtrip(self, sample_record: GenerationRecord):
        """extra dict survives serialization."""
        d = sample_record.to_dict()
        d["extra"] = {"custom": "value"}
        r = GenerationRecord.from_dict(d)
        assert r.extra == {"custom": "value"}


# ═══════════════════════════════════════════════════════════════════════════════
# TestValidateStatus
# ═══════════════════════════════════════════════════════════════════════════════


class TestValidateStatus:
    @pytest.mark.parametrize("status", ["pending", "running", "done", "failed"])
    def test_valid(self, status):
        assert validate_status(status) == status

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Unknown status"):
            validate_status("exploded")


# ═══════════════════════════════════════════════════════════════════════════════
# TestLockedSaveJson
# ═══════════════════════════════════════════════════════════════════════════════


class TestLockedSaveJson:
    def test_creates_file(self, tmp_path: Path):
        path = tmp_path / "sub" / "data.json"
        _locked_save_json(path, {"hello": "world"})
        assert path.exists()

    def test_content_correct(self, tmp_path: Path):
        path = tmp_path / "data.json"
        _locked_save_json(path, {"key": 42})
        data = json.loads(path.read_text())
        assert data["key"] == 42

    def test_atomic_replace(self, tmp_path: Path):
        """Writing twice overwrites cleanly."""
        path = tmp_path / "data.json"
        _locked_save_json(path, {"v": 1})
        _locked_save_json(path, {"v": 2})
        data = json.loads(path.read_text())
        assert data["v"] == 2

    def test_creates_parent_dirs(self, tmp_path: Path):
        path = tmp_path / "a" / "b" / "c" / "data.json"
        _locked_save_json(path, {})
        assert path.exists()


# ═══════════════════════════════════════════════════════════════════════════════
# TestSession
# ═══════════════════════════════════════════════════════════════════════════════


class TestSession:
    def test_default_session(self):
        s = Session()
        assert s.name == "default"
        assert s.default_resolution == "high"
        assert s.history == []

    def test_schema_constant(self):
        assert SCHEMA.startswith("cli-anything-trellis/session/")

    def test_session_path(self, tmp_path: Path):
        p = Session.session_path("mysession")
        assert p.name == "mysession.json"

    def test_save_and_load(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("cli_anything.trellis.core.session.SESSIONS_DIR", tmp_path)
        s = Session(name="test_save")
        s.save()
        loaded = Session.load("test_save")
        assert loaded.name == "test_save"
        assert loaded.schema == SCHEMA

    def test_load_missing_returns_fresh(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("cli_anything.trellis.core.session.SESSIONS_DIR", tmp_path)
        s = Session.load("nonexistent")
        assert s.name == "nonexistent"
        assert s.history == []

    def test_load_corrupted_returns_fresh(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("cli_anything.trellis.core.session.SESSIONS_DIR", tmp_path)
        bad = tmp_path / "corrupt.json"
        bad.write_text("NOT JSON {{{{")
        s = Session.load("corrupt")
        assert s.history == []

    def test_push_history(self):
        s = Session()
        s2 = s.push_history("aabbccdd11223344")
        assert "aabbccdd11223344" in s2.history
        # original unchanged
        assert s.history == []

    def test_push_history_cap(self):
        s = Session()
        for i in range(MAX_HISTORY + 10):
            s = s.push_history(f"job{i:04d}0000000000")
        assert len(s.history) == MAX_HISTORY

    def test_set_setting(self):
        s = Session()
        s2 = s.set_setting("foo", "bar")
        assert s2.settings["foo"] == "bar"
        assert "foo" not in s.settings

    def test_unset_setting(self):
        s = Session()
        s2 = s.set_setting("foo", "bar")
        s3 = s2.unset_setting("foo")
        assert "foo" not in s3.settings

    def test_unset_missing_key_noop(self):
        s = Session()
        s2 = s.unset_setting("nonexistent")
        assert s2.settings == {}

    def test_delete_existing(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("cli_anything.trellis.core.session.SESSIONS_DIR", tmp_path)
        s = Session(name="todel")
        s.save()
        assert s.delete() is True

    def test_delete_missing_returns_false(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("cli_anything.trellis.core.session.SESSIONS_DIR", tmp_path)
        s = Session(name="ghost")
        assert s.delete() is False

    def test_list_sessions(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("cli_anything.trellis.core.session.SESSIONS_DIR", tmp_path)
        Session(name="alpha").save()
        Session(name="beta").save()
        names = Session.list_sessions()
        assert "alpha" in names
        assert "beta" in names

    def test_repr(self):
        s = Session(name="mytest")
        assert "mytest" in repr(s)


# ═══════════════════════════════════════════════════════════════════════════════
# TestCatalog
# ═══════════════════════════════════════════════════════════════════════════════


class TestCatalog:
    def test_append_and_iter(self, done_record: GenerationRecord, tmp_catalog: Path):
        append_record(done_record, catalog_path=tmp_catalog)
        records = list(iter_records(catalog_path=tmp_catalog))
        assert len(records) == 1
        assert records[0].job_id == done_record.job_id

    def test_iter_empty(self, tmp_catalog: Path):
        records = list(iter_records(catalog_path=tmp_catalog))
        assert records == []

    def test_iter_skips_bad_lines(self, tmp_catalog: Path):
        tmp_catalog.parent.mkdir(parents=True, exist_ok=True)
        tmp_catalog.write_text('NOT JSON\n{"job_id":"abc","image_path":"x","output_dir":"y"}\n')
        records = list(iter_records(catalog_path=tmp_catalog))
        assert len(records) == 1

    def test_list_records_limit(
        self, done_record: GenerationRecord, tmp_catalog: Path, tmp_image: Path, tmp_path: Path
    ):
        for i in range(5):
            r = GenerationRecord.new(str(tmp_image), str(tmp_path / f"out{i}"))
            append_record(r, catalog_path=tmp_catalog)
        records = list_records(catalog_path=tmp_catalog, limit=3)
        assert len(records) == 3

    def test_list_records_status_filter(
        self, sample_record: GenerationRecord, done_record: GenerationRecord, tmp_catalog: Path
    ):
        append_record(sample_record, catalog_path=tmp_catalog)
        append_record(done_record, catalog_path=tmp_catalog)
        done_only = list_records(catalog_path=tmp_catalog, status_filter="done")
        assert all(r.status == "done" for r in done_only)

    def test_find_record(self, done_record: GenerationRecord, tmp_catalog: Path):
        append_record(done_record, catalog_path=tmp_catalog)
        found = find_record(done_record.job_id, catalog_path=tmp_catalog)
        assert found is not None
        assert found.job_id == done_record.job_id

    def test_find_record_missing(self, tmp_catalog: Path):
        result = find_record("nonexistent0000", catalog_path=tmp_catalog)
        assert result is None

    def test_catalog_stats(
        self, sample_record: GenerationRecord, done_record: GenerationRecord, tmp_catalog: Path
    ):
        append_record(sample_record, catalog_path=tmp_catalog)
        append_record(done_record, catalog_path=tmp_catalog)
        stats = catalog_stats(catalog_path=tmp_catalog)
        assert stats["total"] == 2
        assert stats["done"] == 1
        assert stats["pending"] == 1

    def test_catalog_stats_empty(self, tmp_catalog: Path):
        stats = catalog_stats(catalog_path=tmp_catalog)
        assert stats["total"] == 0

    def test_append_multiple(self, tmp_image: Path, tmp_path: Path, tmp_catalog: Path):
        for i in range(3):
            r = GenerationRecord.new(str(tmp_image), str(tmp_path / f"o{i}"))
            append_record(r, catalog_path=tmp_catalog)
        assert len(list(iter_records(catalog_path=tmp_catalog))) == 3


# ═══════════════════════════════════════════════════════════════════════════════
# TestBackendErrors
# ═══════════════════════════════════════════════════════════════════════════════


class TestBackendErrors:
    def test_backend_error_hierarchy(self):
        assert issubclass(TrellisNotFoundError, BackendError)
        assert issubclass(TrellisPythonError, BackendError)
        assert issubclass(GPUUnavailableError, BackendError)
        assert issubclass(RunnerError, BackendError)
        assert issubclass(RunnerTimeoutError, BackendError)

    def test_runner_error_fields(self):
        exc = RunnerError("boom", returncode=42, stderr="stderr text")
        assert exc.returncode == 42
        assert exc.stderr == "stderr text"
        assert "boom" in str(exc)

    def test_backend_error_is_runtime(self):
        assert issubclass(BackendError, RuntimeError)


# ═══════════════════════════════════════════════════════════════════════════════
# TestDiscovery
# ═══════════════════════════════════════════════════════════════════════════════


class TestDiscovery:
    def test_discover_trellis_home_explicit(self, tmp_path: Path):
        result = discover_trellis_home(explicit=str(tmp_path))
        assert result == tmp_path.resolve()

    def test_discover_trellis_home_missing(self, tmp_path: Path):
        result = discover_trellis_home(explicit=str(tmp_path / "nonexistent"))
        assert result is None

    def test_discover_trellis_home_env(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("TRELLIS_HOME", str(tmp_path))
        result = discover_trellis_home()
        assert result == tmp_path.resolve()

    def test_discover_trellis_home_session_value(self, tmp_path: Path):
        result = discover_trellis_home(session_value=str(tmp_path))
        assert result == tmp_path.resolve()

    def test_discover_python_explicit(self):
        result = discover_trellis_python(explicit="/usr/bin/python3")
        assert result == "/usr/bin/python3"

    def test_discover_python_env(self, monkeypatch):
        monkeypatch.setenv("TRELLIS_PYTHON", "/opt/venv/bin/python")
        result = discover_trellis_python()
        assert result == "/opt/venv/bin/python"

    def test_discover_python_fallback_sys(self, monkeypatch):
        import sys

        monkeypatch.delenv("TRELLIS_PYTHON", raising=False)
        result = discover_trellis_python()
        assert result == sys.executable

    def test_build_runner_env_sets_trellis_home(self, tmp_path: Path):
        env = build_runner_env(trellis_home=tmp_path)
        assert env["TRELLIS_HOME"] == str(tmp_path)

    def test_build_runner_env_pythonpath(self, tmp_path: Path):
        env = build_runner_env(trellis_home=tmp_path)
        assert str(tmp_path) in env["PYTHONPATH"]

    def test_build_runner_env_no_home(self):
        original = os.environ.get("TRELLIS_HOME")
        env = build_runner_env(trellis_home=None)
        # TRELLIS_HOME should not be set by build_runner_env if not provided
        # (it may exist from outer env, that's fine)
        assert isinstance(env, dict)

    def test_build_runner_env_preserves_existing_pythonpath(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("PYTHONPATH", "/existing/path")
        env = build_runner_env(trellis_home=tmp_path)
        assert "/existing/path" in env["PYTHONPATH"]
        assert str(tmp_path) in env["PYTHONPATH"]


# ═══════════════════════════════════════════════════════════════════════════════
# TestCliImport
# ═══════════════════════════════════════════════════════════════════════════════


class TestCliImport:
    def test_cli_importable_without_trellis(self):
        """The CLI must be importable without trellis2/torch installed."""
        from cli_anything.trellis.trellis_cli import cli as _cli

        assert _cli is not None

    def test_version_flag(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output

    def test_help_flag(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "trellis" in result.output.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# TestCliSessionCommands
# ═══════════════════════════════════════════════════════════════════════════════


class TestCliSessionCommands:
    def _make_runner(self, tmp_path: Path):
        runner = CliRunner(mix_stderr=False)
        return runner

    def test_session_show(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("cli_anything.trellis.core.session.SESSIONS_DIR", tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["session", "show"])
        assert result.exit_code == 0

    def test_session_show_json(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("cli_anything.trellis.core.session.SESSIONS_DIR", tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["--json", "session", "show"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "name" in data

    def test_session_set_and_show(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("cli_anything.trellis.core.session.SESSIONS_DIR", tmp_path)
        runner = CliRunner()
        runner.invoke(cli, ["session", "set", "mykey", "myvalue"])
        result = runner.invoke(cli, ["--json", "session", "show"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data.get("settings", {}).get("mykey") == "myvalue"

    def test_session_list_json(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("cli_anything.trellis.core.session.SESSIONS_DIR", tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["--json", "session", "list"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_session_clear_history(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("cli_anything.trellis.core.session.SESSIONS_DIR", tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["session", "clear-history"])
        assert result.exit_code == 0

    def test_session_delete_missing(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("cli_anything.trellis.core.session.SESSIONS_DIR", tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["session", "delete", "ghost"])
        assert result.exit_code == 0


# ═══════════════════════════════════════════════════════════════════════════════
# TestCliCatalogCommands
# ═══════════════════════════════════════════════════════════════════════════════


class TestCliCatalogCommands:
    def test_catalog_list_empty(self, tmp_path: Path, monkeypatch):
        catalog_file = tmp_path / "catalog.jsonl"
        monkeypatch.setattr("cli_anything.trellis.core.catalog.CATALOG_FILE", catalog_file)
        monkeypatch.setattr(
            "cli_anything.trellis.trellis_cli.list_records",
            lambda **kw: [],
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["catalog", "list"])
        assert result.exit_code == 0

    def test_catalog_stats_json(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(
            "cli_anything.trellis.trellis_cli.catalog_stats",
            lambda: {"total": 0, "done": 0, "failed": 0, "pending": 0, "running": 0},
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["--json", "catalog", "stats"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total" in data


# ═══════════════════════════════════════════════════════════════════════════════
# TestCliConfigCommands
# ═══════════════════════════════════════════════════════════════════════════════


class TestCliConfigCommands:
    def test_config_show(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("cli_anything.trellis.core.session.SESSIONS_DIR", tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "show"])
        assert result.exit_code == 0

    def test_config_show_json(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("cli_anything.trellis.core.session.SESSIONS_DIR", tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["--json", "config", "show"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "version" in data

    def test_config_validate_json(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("cli_anything.trellis.core.session.SESSIONS_DIR", tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["--json", "config", "validate"])
        # May succeed or fail depending on python path — just check JSON output
        data = json.loads(result.output)
        assert "valid" in data
        assert "errors" in data


# ═══════════════════════════════════════════════════════════════════════════════
# TestCliJobsCommands
# ═══════════════════════════════════════════════════════════════════════════════


class TestCliJobsCommands:
    def test_jobs_list_empty_session(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("cli_anything.trellis.core.session.SESSIONS_DIR", tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["jobs", "list"])
        assert result.exit_code == 0

    def test_jobs_list_json_empty(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("cli_anything.trellis.core.session.SESSIONS_DIR", tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["--json", "jobs", "list"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data == []

    def test_jobs_show_missing(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("cli_anything.trellis.core.session.SESSIONS_DIR", tmp_path)
        monkeypatch.setattr("cli_anything.trellis.trellis_cli.find_record", lambda jid: None)
        runner = CliRunner()
        result = runner.invoke(cli, ["jobs", "show", "deadbeef12345678"])
        assert result.exit_code == 1


# ═══════════════════════════════════════════════════════════════════════════════
# TestGenerateRunDryMock
# ═══════════════════════════════════════════════════════════════════════════════


class TestGenerateRunDryMock:
    """Test generate run command with mocked backend — no GPU required."""

    def test_generate_run_success(self, tmp_path: Path, tmp_image: Path, monkeypatch):
        monkeypatch.setattr("cli_anything.trellis.core.session.SESSIONS_DIR", tmp_path)
        glb_path = str(tmp_path / "output" / "fake.glb")

        def mock_run_generation(record, python_path, trellis_home, timeout):
            return record.mark_running().mark_done(glb_path)

        monkeypatch.setattr("cli_anything.trellis.trellis_cli.run_generation", mock_run_generation)
        monkeypatch.setattr("cli_anything.trellis.trellis_cli.append_record", lambda r, **kw: None)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["generate", "run", str(tmp_image), "--output-dir", str(tmp_path / "output")],
        )
        assert result.exit_code == 0

    def test_generate_run_failure(self, tmp_path: Path, tmp_image: Path, monkeypatch):
        monkeypatch.setattr("cli_anything.trellis.core.session.SESSIONS_DIR", tmp_path)

        def mock_run_generation(record, python_path, trellis_home, timeout):
            raise RunnerError("CUDA OOM", returncode=1)

        monkeypatch.setattr("cli_anything.trellis.trellis_cli.run_generation", mock_run_generation)
        monkeypatch.setattr("cli_anything.trellis.trellis_cli.append_record", lambda r, **kw: None)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["generate", "run", str(tmp_image), "--output-dir", str(tmp_path / "output")],
        )
        assert result.exit_code == 1

    def test_generate_run_json_success(self, tmp_path: Path, tmp_image: Path, monkeypatch):
        monkeypatch.setattr("cli_anything.trellis.core.session.SESSIONS_DIR", tmp_path)
        glb_path = str(tmp_path / "output" / "fake.glb")

        def mock_run_generation(record, python_path, trellis_home, timeout):
            return record.mark_running().mark_done(glb_path)

        monkeypatch.setattr("cli_anything.trellis.trellis_cli.run_generation", mock_run_generation)
        monkeypatch.setattr("cli_anything.trellis.trellis_cli.append_record", lambda r, **kw: None)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--json", "generate", "run", str(tmp_image), "--output-dir", str(tmp_path)],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "done"
