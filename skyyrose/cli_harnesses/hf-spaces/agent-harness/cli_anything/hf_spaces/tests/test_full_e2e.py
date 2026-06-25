"""
End-to-end subprocess tests for cli-anything-hf-spaces.

Gated by HF_SPACES_E2E=1.  Requires a valid HF_TOKEN and a test Space
specified via HF_TEST_SPACE (defaults to damBruh/cli-anything-e2e-test).

Gate behaviour:
    HF_SPACES_E2E=0 (default) : all tests in this file are SKIPPED.
    HF_SPACES_E2E=1 + HfApi unreachable : tests FAIL (not skip).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from typing import List

import pytest

# ---------------------------------------------------------------------------
# Gate
# ---------------------------------------------------------------------------

_E2E = os.environ.get("HF_SPACES_E2E", "0").strip() == "1"
pytestmark = pytest.mark.skipif(not _E2E, reason="HF_SPACES_E2E not set to 1")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_cli(name: str = "hf-spaces") -> List[str]:
    """Return the command vector for the CLI.

    Resolution order:
      1. If CLI_ANYTHING_FORCE_INSTALLED=1, require the installed binary.
      2. If the binary is on PATH, use it.
      3. Fall back to `python -m cli_anything.hf_spaces`.
    """
    force = os.environ.get("CLI_ANYTHING_FORCE_INSTALLED", "").strip() == "1"
    path = shutil.which(name)
    if path:
        return [path]
    if force:
        raise RuntimeError(f"{name!r} not found in PATH and CLI_ANYTHING_FORCE_INSTALLED=1.")
    return [sys.executable, "-m", "cli_anything.hf_spaces"]


def _run(
    *args: str,
    token: str | None = None,
    expect_exit: int = 0,
    json_output: bool = False,
) -> subprocess.CompletedProcess:
    """Run the CLI with the given args.  Asserts exit code matches ``expect_exit``."""
    cmd = _resolve_cli()
    if json_output:
        cmd = cmd + ["--json"]
    if token:
        cmd = cmd + ["--token", token]
    cmd = cmd + list(args)
    env = os.environ.copy()
    # Ensure token env var is set for the subprocess when not passed explicitly.
    if not token and "HF_TOKEN" not in env:
        tok = _get_token()
        if tok:
            env["HF_TOKEN"] = tok
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert result.returncode == expect_exit, (
        f"Exit {result.returncode!r} != {expect_exit!r}\n"
        f"stdout: {result.stdout!r}\n"
        f"stderr: {result.stderr!r}"
    )
    return result


def _get_token() -> str:
    """Resolve HF token from env or ~/.cache/huggingface/token."""
    tok = os.environ.get("HF_TOKEN", "").strip()
    if tok:
        return tok
    fallback = os.path.expanduser("~/.cache/huggingface/token")
    if os.path.isfile(fallback):
        with open(fallback) as fh:
            return fh.read().strip()
    return ""


def _test_space() -> str:
    return os.environ.get("HF_TEST_SPACE", "damBruh/cli-anything-e2e-test")


def _require_reachable() -> None:
    """Fail (not skip) if HfApi is unreachable when gate is ON."""
    try:
        from huggingface_hub import HfApi

        HfApi(token=_get_token() or None).whoami()
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"HF_SPACES_E2E=1 but HfApi is unreachable: {exc}")


# Run the reachability check once when the gate is active.
if _E2E:
    _require_reachable()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def space() -> str:
    return _test_space()


@pytest.fixture(scope="module")
def token() -> str:
    tok = _get_token()
    if not tok:
        pytest.fail("No HF_TOKEN set and ~/.cache/huggingface/token not found.")
    return tok


# ---------------------------------------------------------------------------
# Doctor
# ---------------------------------------------------------------------------


class TestDoctorE2E:
    def test_doctor_exits_zero(self, token: str) -> None:
        _run("doctor", token=token)

    def test_doctor_json(self, token: str) -> None:
        result = _run("doctor", token=token, json_output=True)
        data = json.loads(result.stdout)
        assert "checks" in data
        assert isinstance(data["checks"], list)

    def test_doctor_shows_token_masked(self, token: str) -> None:
        result = _run("doctor", token=token)
        # Token must NOT appear verbatim in stdout.
        assert token not in result.stdout
        assert token not in result.stderr


# ---------------------------------------------------------------------------
# Space info
# ---------------------------------------------------------------------------


class TestSpaceInfoE2E:
    def test_info_exits_zero(self, space: str, token: str) -> None:
        _run("space", "info", space, token=token)

    def test_info_json_has_repo_id(self, space: str, token: str) -> None:
        result = _run("space", "info", space, token=token, json_output=True)
        data = json.loads(result.stdout)
        assert data.get("repo_id") == space or data.get("id") == space or space in str(data)

    def test_info_unknown_space_fails(self, token: str) -> None:
        _run(
            "space",
            "info",
            "damBruh/cli-anything-does-not-exist-xyzzy",
            token=token,
            expect_exit=1,
        )


# ---------------------------------------------------------------------------
# Hardware
# ---------------------------------------------------------------------------


class TestHardwareE2E:
    def test_hardware_get(self, space: str, token: str) -> None:
        _run("hardware", "get", space, token=token)

    def test_hardware_get_json(self, space: str, token: str) -> None:
        result = _run("hardware", "get", space, token=token, json_output=True)
        data = json.loads(result.stdout)
        assert "hardware" in data or "current" in data or "requested" in data or data

    def test_hardware_list_tiers(self, token: str) -> None:
        _run("hardware", "list-tiers", token=token)

    def test_hardware_set_without_confirm_rejected(self, space: str, token: str) -> None:
        # Omitting --confirm must result in a non-zero exit (STOP-AND-SHOW gate).
        _run("hardware", "set", space, "cpu-basic", token=token, expect_exit=1)

    def test_hardware_set_invalid_slug_rejected(self, space: str, token: str) -> None:
        _run("hardware", "set", space, "not-a-real-tier", "--confirm", token=token, expect_exit=2)


# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------


class TestVariablesE2E:
    _VAR_KEY = "CLI_ANYTHING_E2E_TEST_VAR"
    _VAR_VAL = "hello-e2e-value"

    def test_vars_set(self, space: str, token: str) -> None:
        _run("vars", "set", space, self._VAR_KEY, self._VAR_VAL, token=token)

    def test_vars_list_contains_key(self, space: str, token: str) -> None:
        result = _run("vars", "list", space, token=token, json_output=True)
        data = json.loads(result.stdout)
        # data may be a dict keyed by var name or a list of objects.
        text = json.dumps(data)
        assert self._VAR_KEY in text

    def test_vars_get(self, space: str, token: str) -> None:
        result = _run("vars", "get", space, self._VAR_KEY, token=token)
        assert self._VAR_VAL in result.stdout

    def test_vars_delete_without_confirm_rejected(self, space: str, token: str) -> None:
        _run("vars", "delete", space, self._VAR_KEY, token=token, expect_exit=1)

    def test_vars_delete_with_confirm(self, space: str, token: str) -> None:
        # Clean up the variable created by test_vars_set.
        _run("vars", "delete", space, self._VAR_KEY, "--confirm", token=token)


# ---------------------------------------------------------------------------
# Secrets (write-only — only set/delete can be verified, not read)
# ---------------------------------------------------------------------------


class TestSecretsE2E:
    _SECRET_KEY = "CLI_ANYTHING_E2E_TEST_SECRET"

    def test_secrets_set(self, space: str, token: str) -> None:
        _run("secrets", "set", space, self._SECRET_KEY, "--value", "e2e-secret-val", token=token)

    def test_secrets_list_shows_manifest_warning(self, space: str, token: str) -> None:
        # secrets list reads local manifest only — should warn about API gap.
        with tempfile.TemporaryDirectory() as td:
            manifest_path = os.path.join(td, "manifest.json")
            _run("manifest", "init", space, "--out", manifest_path, token=token)
            result = _run("secrets", "list", space, "--manifest", manifest_path, token=token)
        combined = result.stdout + result.stderr
        # Should mention the limitation.
        assert any(
            phrase in combined.lower()
            for phrase in ("write-only", "manifest", "api does not", "local")
        )

    def test_secrets_delete_without_confirm_rejected(self, space: str, token: str) -> None:
        _run("secrets", "delete", space, self._SECRET_KEY, token=token, expect_exit=1)

    def test_secrets_delete_with_confirm(self, space: str, token: str) -> None:
        _run("secrets", "delete", space, self._SECRET_KEY, "--confirm", token=token)


# ---------------------------------------------------------------------------
# README
# ---------------------------------------------------------------------------


class TestReadmeE2E:
    def test_readme_get(self, space: str, token: str) -> None:
        result = _run("readme", "get", space, token=token)
        assert result.stdout.strip()

    def test_readme_get_to_file(self, space: str, token: str) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_path = os.path.join(td, "README.md")
            _run("readme", "get", space, "--out", out_path, token=token)
            assert os.path.isfile(out_path)
            with open(out_path) as fh:
                content = fh.read()
            assert content.strip()

    def test_readme_sync_noop_when_identical(self, space: str, token: str) -> None:
        with tempfile.TemporaryDirectory() as td:
            readme_path = os.path.join(td, "README.md")
            # Get the current README.
            _run("readme", "get", space, "--out", readme_path, token=token)
            # Syncing the same content should be a no-op (exit 0).
            result = _run("readme", "sync", space, readme_path, token=token)
            combined = result.stdout + result.stderr
            assert any(
                w in combined.lower() for w in ("no change", "identical", "up to date", "skipped")
            )


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


class TestManifestE2E:
    def test_manifest_init(self, space: str, token: str) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "manifest.json")
            _run("manifest", "init", space, "--out", out, token=token)
            assert os.path.isfile(out)
            with open(out) as fh:
                data = json.load(fh)
            assert data.get("schema") == "1"
            assert data.get("repo_id") == space

    def test_manifest_show(self, space: str, token: str) -> None:
        with tempfile.TemporaryDirectory() as td:
            mpath = os.path.join(td, "manifest.json")
            _run("manifest", "init", space, "--out", mpath, token=token)
            _run("manifest", "show", mpath, token=token)

    def test_manifest_plan(self, space: str, token: str) -> None:
        with tempfile.TemporaryDirectory() as td:
            mpath = os.path.join(td, "manifest.json")
            _run("manifest", "init", space, "--out", mpath, token=token)
            # plan should exit 0 even when there are no changes.
            _run("manifest", "plan", mpath, token=token)

    def test_manifest_apply_without_confirm_rejected(self, space: str, token: str) -> None:
        with tempfile.TemporaryDirectory() as td:
            mpath = os.path.join(td, "manifest.json")
            _run("manifest", "init", space, "--out", mpath, token=token)
            _run("manifest", "apply", mpath, token=token, expect_exit=1)


# ---------------------------------------------------------------------------
# Space list
# ---------------------------------------------------------------------------


class TestSpaceListE2E:
    def test_list_returns_results(self, token: str) -> None:
        result = _run("space", "list", "--author", "damBruh", token=token, json_output=True)
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_list_limit(self, token: str) -> None:
        result = _run(
            "space", "list", "--author", "damBruh", "--limit", "1", token=token, json_output=True
        )
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) <= 1


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


class TestSessionE2E:
    def test_session_list_exits_zero(self, token: str) -> None:
        _run("session", "list", token=token)

    def test_session_list_json(self, token: str) -> None:
        result = _run("session", "list", token=token, json_output=True)
        data = json.loads(result.stdout)
        assert isinstance(data, list)
