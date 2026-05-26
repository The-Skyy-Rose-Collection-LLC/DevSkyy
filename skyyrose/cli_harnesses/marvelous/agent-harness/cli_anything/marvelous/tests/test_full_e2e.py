"""Full E2E tests for cli-anything-marvelous.

These tests require Marvelous Designer to be installed AND
the MARVELOUS_E2E=1 environment variable to be set.

Without MARVELOUS_E2E=1 all tests in this file are skipped cleanly.

Run live tests:
    MARVELOUS_E2E=1 pytest cli_anything/marvelous/tests/test_full_e2e.py -v

The _resolve_cli() helper prefers the installed binary, falls back to
  `python -m cli_anything.marvelous`, and respects
  CLI_ANYTHING_FORCE_INSTALLED=1 to hard-require the installed path.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# ── Gate ─────────────────────────────────────────────────────────────────

_E2E = os.environ.get("MARVELOUS_E2E", "").strip() == "1"
_SKIP = pytest.mark.skipif(not _E2E, reason="Set MARVELOUS_E2E=1 to run live MD tests")


# ── CLI resolver ──────────────────────────────────────────────────────────


def _resolve_cli() -> list[str]:
    """Return argv prefix for invoking cli-anything-marvelous.

    Resolution order:
    1. Installed binary ``cli-anything-marvelous`` (always preferred).
    2. ``python -m cli_anything.marvelous`` (editable / source run).

    If CLI_ANYTHING_FORCE_INSTALLED=1 is set, raises RuntimeError when
    the installed binary is not found (used in CI to catch packaging bugs).
    """
    force_installed = os.environ.get("CLI_ANYTHING_FORCE_INSTALLED", "").strip() == "1"

    installed = shutil.which("cli-anything-marvelous")
    if installed:
        return [installed]

    if force_installed:
        raise RuntimeError(
            "CLI_ANYTHING_FORCE_INSTALLED=1 but 'cli-anything-marvelous' "
            "binary not found on PATH. Run: pip install -e ."
        )

    return [sys.executable, "-m", "cli_anything.marvelous"]


def _run(*args: str, check: bool = True, **kwargs) -> subprocess.CompletedProcess[str]:
    """Run cli-anything-marvelous with *args*."""
    cmd = _resolve_cli() + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, check=check, **kwargs)


# ── Smoke tests (no MD required) ─────────────────────────────────────────


class TestCliSmoke:
    """Basic CLI invocation tests that don't require a running MD instance."""

    def test_version_flag(self):
        result = _run("--version")
        assert result.returncode == 0
        assert "1.0.0" in result.stdout

    def test_help_flag(self):
        result = _run("--help")
        assert result.returncode == 0
        assert "marvelous" in result.stdout.lower()

    def test_config_doctor_json(self):
        """config doctor --json always returns valid JSON."""
        result = _run("config", "doctor", "--json", check=False)
        import json

        data = json.loads(result.stdout)
        assert "md_binary_found" in data
        assert "issues" in data
        assert isinstance(data["issues"], list)

    def test_session_list_json_empty(self, tmp_path):
        """session list --json returns empty list when no sessions exist."""
        import json

        env = {**os.environ, "MARVELOUS_SESSIONS_DIR": str(tmp_path / "sessions")}
        result = _run("session", "list", "--json", env=env)
        data = json.loads(result.stdout)
        assert data == []

    def test_library_list_json_empty(self, tmp_path):
        """library list --json returns empty list when library is empty."""
        import json

        env = {**os.environ, "MARVELOUS_LIBRARY_DIR": str(tmp_path / "library")}
        result = _run("library", "list", "--json", env=env)
        data = json.loads(result.stdout)
        assert data == []

    def test_project_info_missing_file(self):
        result = _run("project", "info", "/nonexistent/path.zpac", check=False)
        assert result.returncode != 0

    def test_project_info_json_valid_zpac(self, tmp_path):
        """project info --json parses a synthetic .zpac."""
        import json
        import zipfile

        zpac = tmp_path / "shirt.zpac"
        with zipfile.ZipFile(zpac, "w") as zf:
            zf.writestr("project.json", json.dumps({"name": "Shirt", "md_version": "12"}))
        result = _run("--json", "project", "info", str(zpac))
        data = json.loads(result.stdout)
        assert data["name"] == "Shirt"
        assert data["file_format"] == "zpac"

    def test_session_save_and_status(self, tmp_path):
        """session save + status round-trip via CLI."""
        import json

        env = {**os.environ, "MARVELOUS_SESSIONS_DIR": str(tmp_path / "sessions")}
        save_result = _run(
            "--json",
            "session",
            "save",
            "--project",
            "/tmp/test.zpac",
            "--garment",
            "TestGarment",
            env=env,
        )
        saved = json.loads(save_result.stdout)
        sid = saved["session_id"]

        status_result = _run("--json", "session", "status", sid, env=env)
        status = json.loads(status_result.stdout)
        assert status["project_path"] == "/tmp/test.zpac"
        assert status["garment_name"] == "TestGarment"

    def test_session_delete(self, tmp_path):
        import json

        env = {**os.environ, "MARVELOUS_SESSIONS_DIR": str(tmp_path / "sessions")}
        save_result = _run("--json", "session", "save", "--garment", "Del", env=env)
        sid = json.loads(save_result.stdout)["session_id"]

        del_result = _run("--json", "session", "delete", sid, env=env)
        data = json.loads(del_result.stdout)
        assert data["deleted"] is True


# ── Live MD tests (require MARVELOUS_E2E=1 + installed MD) ───────────────


@_SKIP
class TestLiveExport:
    """Tests that actually invoke Marvelous Designer via --script."""

    @pytest.fixture
    def sample_zpac(self, tmp_path) -> Path:
        """Return path to a real .zpac fixture.

        Set MARVELOUS_TEST_ZPAC=/path/to/file.zpac to use a real project.
        Falls back to a minimal synthetic .zpac (MD may reject it).
        """
        env_zpac = os.environ.get("MARVELOUS_TEST_ZPAC", "")
        if env_zpac and Path(env_zpac).exists():
            return Path(env_zpac)
        import json
        import zipfile

        p = tmp_path / "sample.zpac"
        with zipfile.ZipFile(p, "w") as zf:
            zf.writestr("project.json", json.dumps({"name": "SampleGarment"}))
        return p

    def test_export_obj(self, sample_zpac, tmp_path):
        output = str(tmp_path / "exported_garment")
        result = _run(
            "--json",
            "export",
            "run",
            str(sample_zpac),
            "--format",
            "obj",
            "--output",
            output,
            check=False,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        import json

        data = json.loads(result.stdout)
        assert data["ok"] is True

    def test_simulate_run(self, sample_zpac, tmp_path):
        output = str(tmp_path / "simulated.zpac")
        result = _run(
            "--json",
            "simulate",
            "run",
            str(sample_zpac),
            "--frames",
            "10",
            "--output",
            output,
            check=False,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        import json

        data = json.loads(result.stdout)
        assert data["frames"] == 10
