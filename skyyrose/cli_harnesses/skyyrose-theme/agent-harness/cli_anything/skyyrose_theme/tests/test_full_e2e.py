"""
Full end-to-end tests for cli-anything-skyyrose-theme.

These tests require:
  - SKYYROSE_E2E=1 environment variable
  - The cli-anything-skyyrose-theme binary on PATH (or CLI_ANYTHING_FORCE_INSTALLED=1)
  - Real theme root at SKYYROSE_THEME_ROOT (or default ~/DevSkyy/wordpress-theme/skyyrose-flagship)
  - SSH access to skyyrose.wordpress.com@ssh.wp.com for cache/wp tests

Without SKYYROSE_E2E=1, all tests in this file are skipped automatically.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Skip guard
# ---------------------------------------------------------------------------

_E2E = os.environ.get("SKYYROSE_E2E", "").strip() == "1"
pytestmark = pytest.mark.skipif(not _E2E, reason="SKYYROSE_E2E=1 not set")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CLI_NAME = "cli-anything-skyyrose-theme"


def _resolve_cli(name: str) -> list[str]:
    """
    Resolve the CLI binary path.

    If CLI_ANYTHING_FORCE_INSTALLED=1 and the binary is not found, raises.
    Otherwise falls back to python -m invocation.
    """
    force = os.environ.get("CLI_ANYTHING_FORCE_INSTALLED", "").strip() == "1"
    path = shutil.which(name)
    if path:
        return [path]
    if force:
        raise RuntimeError(f"{name} not found in PATH. Install with: pip install -e .")
    module = "cli_anything.skyyrose_theme"
    return [sys.executable, "-m", module]


_CLI = _resolve_cli(_CLI_NAME)

_THEME_ROOT = os.environ.get(
    "SKYYROSE_THEME_ROOT",
    str(Path.home() / "DevSkyy/wordpress-theme/skyyrose-flagship"),
)
_THEME_ROOT_PATH = Path(_THEME_ROOT)

_skip_no_theme = pytest.mark.skipif(
    not _THEME_ROOT_PATH.exists(),
    reason=f"Theme root not found: {_THEME_ROOT}",
)


@pytest.fixture
def isolated_home(tmp_path, monkeypatch):
    """Redirect HOME so sessions don't pollute the real ~/.cli_anything."""
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path


# ---------------------------------------------------------------------------
# E2E tests
# ---------------------------------------------------------------------------


@_skip_no_theme
def test_e2e_version_current():
    """version current returns consistent version from real theme files."""
    result = subprocess.run(
        [*_CLI, "--json", "--theme-root", _THEME_ROOT, "version", "current"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["consistent"] is True
    assert re.match(r"\d+\.\d+\.\d+", data["functions_php"])


@_skip_no_theme
def test_e2e_template_list():
    """template list returns at least 10 templates from the real theme."""
    result = subprocess.run(
        [*_CLI, "--json", "--theme-root", _THEME_ROOT, "template", "list"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["total"] >= 10


@_skip_no_theme
def test_e2e_doctor():
    """doctor passes all critical checks on the real theme root."""
    result = subprocess.run(
        [*_CLI, "--json", "--theme-root", _THEME_ROOT, "doctor"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    # theme_root, style_css, functions_php must be ok
    checks = {c["name"]: c["status"] for c in data["checks"]}
    assert checks.get("theme_root") == "ok"
    assert checks.get("style_css") == "ok"
    assert checks.get("functions_php") == "ok"


@_skip_no_theme
def test_e2e_deploy_dry_run_no_confirm():
    """deploy --dry-run without --confirm prints manifest and exits 0."""
    result = subprocess.run(
        [
            *_CLI,
            "--theme-root",
            _THEME_ROOT,
            "deploy",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "confirm" in result.stdout.lower() or "deploy" in result.stdout.lower()


def test_e2e_session_save_and_list(isolated_home):
    """session save + list roundtrip works."""
    # save
    result = subprocess.run(
        [*_CLI, "--json", "session", "save", "--name", "e2e-test"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["ok"] is True

    # list
    result2 = subprocess.run(
        [*_CLI, "--json", "session", "list"],
        capture_output=True,
        text=True,
    )
    assert result2.returncode == 0, result2.stderr
    data2 = json.loads(result2.stdout)
    names = [s["name"] for s in data2["sessions"]]
    assert "e2e-test" in names


# ---------------------------------------------------------------------------
# re import needed for test_e2e_version_current
# ---------------------------------------------------------------------------
import re  # noqa: E402
