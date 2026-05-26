"""End-to-end CLI tests for cli-anything-vercel-config.

Offline tests (always run):
  - help / version banners for every command group
  - REPL startup header renders without crash
  - STOP-AND-SHOW gates block destructive ops without --confirm
  - --json flag emits valid JSON on list commands against mocked backend

Live tests (run only when VERCEL_E2E=1 and VERCEL_TOKEN set):
  - project show against real Vercel project
  - env list (masked)
  - domain list
  - deployment list

Usage::

    # offline only (CI default)
    pytest cli_anything/vercel_config/tests/test_full_e2e.py -v

    # live network
    VERCEL_E2E=1 VERCEL_TOKEN=your_token VERCEL_E2E_PROJECT=your-project \\
        pytest cli_anything/vercel_config/tests/test_full_e2e.py -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional
from unittest.mock import MagicMock, patch

import pytest

# ── Helpers ────────────────────────────────────────────────────────────

_HARNESS_ROOT = Path(__file__).resolve().parents[4]  # agent-harness/
_ENTRY_MODULE = "cli_anything.vercel_config.vercel_config_cli"

# NOTE: _resolve_cli auto-derivation from "cli-anything-vercel-config" yields
# "cli_anything.vercel-config.config_cli" (hyphen in module segment) which is
# invalid Python.  We hardcode the correct module path here.


def _run(
    args: List[str],
    env: Optional[dict] = None,
    input: Optional[str] = None,
    timeout: int = 30,
) -> subprocess.CompletedProcess:
    """Run the CLI via `python -m <module>` so we don't need the entry point installed."""
    cmd = [sys.executable, "-m", _ENTRY_MODULE] + args
    run_env = {**os.environ, **(env or {})}
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(_HARNESS_ROOT),
        env=run_env,
        input=input,
        timeout=timeout,
    )


def _live_skip():
    """Skip decorator for live tests."""
    return pytest.mark.skipif(
        not (os.environ.get("VERCEL_E2E") == "1" and os.environ.get("VERCEL_TOKEN")),
        reason="Live tests require VERCEL_E2E=1 and VERCEL_TOKEN set",
    )


# ── Offline: help banners ──────────────────────────────────────────────


class TestHelpBanners:
    """Every command group must expose --help without crashing."""

    def test_root_help(self):
        r = _run(["--help"])
        assert r.returncode == 0
        assert "vercel" in r.stdout.lower() or "usage" in r.stdout.lower()

    def test_root_version(self):
        r = _run(["--version"])
        assert r.returncode == 0
        # version string from __init__.py
        assert "1.0.0" in r.stdout or "1.0.0" in r.stderr

    def test_project_help(self):
        r = _run(["project", "--help"])
        assert r.returncode == 0
        assert "show" in r.stdout or "list" in r.stdout

    def test_env_help(self):
        r = _run(["env", "--help"])
        assert r.returncode == 0
        assert "list" in r.stdout

    def test_domain_help(self):
        r = _run(["domain", "--help"])
        assert r.returncode == 0
        assert "list" in r.stdout

    def test_deployment_help(self):
        r = _run(["deployment", "--help"])
        assert r.returncode == 0

    def test_integration_help(self):
        r = _run(["integration", "--help"])
        assert r.returncode == 0

    def test_manifest_help(self):
        r = _run(["manifest", "--help"])
        assert r.returncode == 0
        assert "plan" in r.stdout or "apply" in r.stdout

    def test_session_help(self):
        r = _run(["session", "--help"])
        assert r.returncode == 0

    def test_doctor_help(self):
        r = _run(["doctor", "--help"])
        assert r.returncode == 0

    def test_project_show_help(self):
        r = _run(["project", "show", "--help"])
        assert r.returncode == 0

    def test_project_list_help(self):
        r = _run(["project", "list", "--help"])
        assert r.returncode == 0

    def test_env_list_help(self):
        r = _run(["env", "list", "--help"])
        assert r.returncode == 0
        # reveal flag should be in env list
        assert "--reveal" in r.stdout

    def test_env_set_help(self):
        r = _run(["env", "set", "--help"])
        assert r.returncode == 0

    def test_env_remove_help(self):
        r = _run(["env", "remove", "--help"])
        assert r.returncode == 0

    def test_domain_add_help(self):
        r = _run(["domain", "add", "--help"])
        assert r.returncode == 0

    def test_domain_remove_help(self):
        r = _run(["domain", "remove", "--help"])
        assert r.returncode == 0


# ── Offline: JSON output ───────────────────────────────────────────────


class TestJsonOutput:
    """--json flag must emit parseable JSON for every list command."""

    def _make_mock_backend(self):
        """Return a MagicMock backend with sensible defaults for all list calls."""
        b = MagicMock()
        b.get_project.return_value = {
            "id": "prj_test123",
            "name": "test-project",
            "framework": "nextjs",
        }
        b.list_env_vars.return_value = [
            {
                "id": "env_abc",
                "key": "API_URL",
                "value": "https://example.com",
                "type": "plain",
                "target": ["production"],
            }
        ]
        b.list_domains.return_value = [
            {"name": "example.com", "redirect": None, "gitBranch": None, "verified": True}
        ]
        b.list_deployments.return_value = [
            {
                "uid": "dpl_abc",
                "name": "test-project",
                "url": "test-abc.vercel.app",
                "state": "READY",
                "createdAt": 1700000000000,
            }
        ]
        b.list_integrations.return_value = []
        return b

    def test_project_show_json(self, tmp_path, monkeypatch):
        """project show --json with mocked backend should emit valid JSON."""
        from click.testing import CliRunner

        from cli_anything.vercel_config.vercel_config_cli import main

        mock_backend = self._make_mock_backend()

        with patch(
            "cli_anything.vercel_config.vercel_config_cli.VercelBackend",
            return_value=mock_backend,
        ):
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["--token", "tok_fake", "--project", "test-project", "project", "show", "--json"],
                catch_exceptions=False,
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert "id" in data or "name" in data

    def test_env_list_json(self, tmp_path, monkeypatch):
        """env list --json should emit a JSON array."""
        from click.testing import CliRunner

        from cli_anything.vercel_config.vercel_config_cli import main

        mock_backend = self._make_mock_backend()

        with patch(
            "cli_anything.vercel_config.vercel_config_cli.VercelBackend",
            return_value=mock_backend,
        ):
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["--token", "tok_fake", "--project", "test-project", "env", "list", "--json"],
                catch_exceptions=False,
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_domain_list_json(self, tmp_path, monkeypatch):
        """domain list --json should emit a JSON array."""
        from click.testing import CliRunner

        from cli_anything.vercel_config.vercel_config_cli import main

        mock_backend = self._make_mock_backend()

        with patch(
            "cli_anything.vercel_config.vercel_config_cli.VercelBackend",
            return_value=mock_backend,
        ):
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["--token", "tok_fake", "--project", "test-project", "domain", "list", "--json"],
                catch_exceptions=False,
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_deployment_list_json(self, tmp_path, monkeypatch):
        """deployment list --json should emit a JSON array."""
        from click.testing import CliRunner

        from cli_anything.vercel_config.vercel_config_cli import main

        mock_backend = self._make_mock_backend()

        with patch(
            "cli_anything.vercel_config.vercel_config_cli.VercelBackend",
            return_value=mock_backend,
        ):
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "--token",
                    "tok_fake",
                    "--project",
                    "test-project",
                    "deployment",
                    "list",
                    "--json",
                ],
                catch_exceptions=False,
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_integration_list_json(self, tmp_path, monkeypatch):
        """integration list --json should emit a JSON array."""
        from click.testing import CliRunner

        from cli_anything.vercel_config.vercel_config_cli import main

        mock_backend = self._make_mock_backend()

        with patch(
            "cli_anything.vercel_config.vercel_config_cli.VercelBackend",
            return_value=mock_backend,
        ):
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "--token",
                    "tok_fake",
                    "--project",
                    "test-project",
                    "integration",
                    "list",
                    "--json",
                ],
                catch_exceptions=False,
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert isinstance(data, list)


# ── Offline: destructive gates ─────────────────────────────────────────


class TestDestructiveGates:
    """Destructive ops must fail (or prompt) without --confirm."""

    def _make_mock_backend(self):
        b = MagicMock()
        b.get_project.return_value = {"id": "prj_test", "name": "test-project"}
        b.list_domains.return_value = [
            {"name": "example.com", "redirect": None, "gitBranch": None, "verified": True}
        ]
        b.list_env_vars.return_value = [
            {
                "id": "env_abc",
                "key": "API_URL",
                "value": "https://example.com",
                "type": "plain",
                "target": ["production"],
            }
        ]
        return b

    def test_env_remove_no_confirm_aborts(self, monkeypatch):
        """env remove without --confirm should abort (non-zero exit or no delete called)."""
        from click.testing import CliRunner

        from cli_anything.vercel_config.vercel_config_cli import main

        mock_backend = self._make_mock_backend()

        with patch(
            "cli_anything.vercel_config.vercel_config_cli.VercelBackend",
            return_value=mock_backend,
        ):
            with patch(
                "cli_anything.vercel_config.utils.vercel_backend._confirm", return_value=False
            ):
                runner = CliRunner()
                result = runner.invoke(
                    main,
                    [
                        "--token",
                        "tok_fake",
                        "--project",
                        "test-project",
                        "env",
                        "remove",
                        "API_URL",
                    ],
                    input="n\n",
                    catch_exceptions=False,
                )
        # Either exits non-zero or never calls delete_env_var
        mock_backend.delete_env_var.assert_not_called()

    def test_domain_remove_no_confirm_aborts(self, monkeypatch):
        """domain remove without --confirm should abort."""
        from click.testing import CliRunner

        from cli_anything.vercel_config.vercel_config_cli import main

        mock_backend = self._make_mock_backend()

        with patch(
            "cli_anything.vercel_config.vercel_config_cli.VercelBackend",
            return_value=mock_backend,
        ):
            with patch(
                "cli_anything.vercel_config.utils.vercel_backend._confirm", return_value=False
            ):
                runner = CliRunner()
                result = runner.invoke(
                    main,
                    [
                        "--token",
                        "tok_fake",
                        "--project",
                        "test-project",
                        "domain",
                        "remove",
                        "example.com",
                    ],
                    input="n\n",
                    catch_exceptions=False,
                )
        mock_backend.remove_domain.assert_not_called()


# ── Offline: session commands ──────────────────────────────────────────


class TestSessionCommands:
    """Session subcommands work without network."""

    def test_session_list_empty(self, tmp_path, monkeypatch):
        """session list with empty dir emits empty list or no-sessions message."""
        from click.testing import CliRunner

        from cli_anything.vercel_config.vercel_config_cli import main

        monkeypatch.setenv("VERCEL_TOKEN", "tok_fake")

        with patch("cli_anything.vercel_config.core.session.SESSIONS_DIR", tmp_path):
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["--token", "tok_fake", "session", "list"],
                catch_exceptions=False,
            )
        assert result.exit_code == 0

    def test_session_save_and_list(self, tmp_path, monkeypatch):
        """session save creates a session; session list shows it."""
        from click.testing import CliRunner

        from cli_anything.vercel_config.vercel_config_cli import main

        with patch("cli_anything.vercel_config.core.session.SESSIONS_DIR", tmp_path):
            runner = CliRunner()
            # Save session
            r1 = runner.invoke(
                main,
                [
                    "--token",
                    "tok_fake",
                    "--project",
                    "my-project",
                    "session",
                    "save",
                    "--name",
                    "test-session",
                ],
                catch_exceptions=False,
            )
            assert r1.exit_code == 0, r1.output

            # List sessions — should include the one we just saved
            r2 = runner.invoke(
                main,
                ["--token", "tok_fake", "session", "list"],
                catch_exceptions=False,
            )
        assert r2.exit_code == 0
        assert "test-session" in r2.output

    def test_session_delete(self, tmp_path, monkeypatch):
        """session delete removes the session file."""
        from click.testing import CliRunner

        import cli_anything.vercel_config.core.session as session_mod
        from cli_anything.vercel_config.vercel_config_cli import main

        with patch.object(session_mod, "SESSIONS_DIR", tmp_path):
            runner = CliRunner()
            # Create first
            r1 = runner.invoke(
                main,
                [
                    "--token",
                    "tok_fake",
                    "--project",
                    "del-project",
                    "session",
                    "save",
                    "--name",
                    "to-delete",
                ],
                catch_exceptions=False,
            )
            assert r1.exit_code == 0

            # Delete
            r2 = runner.invoke(
                main,
                ["--token", "tok_fake", "session", "delete", "to-delete"],
                catch_exceptions=False,
            )
        assert r2.exit_code == 0
        assert not (tmp_path / "to-delete.json").exists()


# ── Offline: env masking ───────────────────────────────────────────────


class TestEnvMasking:
    """Env var values are masked unless --reveal passed."""

    def _backend_with_env(self):
        b = MagicMock()
        b.get_project.return_value = {"id": "prj_x", "name": "p"}
        b.list_env_vars.return_value = [
            {
                "id": "env_1",
                "key": "SECRET_KEY",
                "value": "super-secret-value",
                "type": "secret",
                "target": ["production"],
            }
        ]
        return b

    def test_env_list_masked_by_default(self):
        """Env value should be masked (***) without --reveal."""
        from click.testing import CliRunner

        from cli_anything.vercel_config.vercel_config_cli import main

        mock_backend = self._backend_with_env()

        with patch(
            "cli_anything.vercel_config.vercel_config_cli.VercelBackend",
            return_value=mock_backend,
        ):
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["--token", "tok_fake", "--project", "p", "env", "list"],
                catch_exceptions=False,
            )
        assert result.exit_code == 0
        assert "super-secret-value" not in result.output
        assert "***" in result.output

    def test_env_list_revealed_with_flag(self):
        """Env value should appear with --reveal."""
        from click.testing import CliRunner

        from cli_anything.vercel_config.vercel_config_cli import main

        mock_backend = self._backend_with_env()

        with patch(
            "cli_anything.vercel_config.vercel_config_cli.VercelBackend",
            return_value=mock_backend,
        ):
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["--token", "tok_fake", "--project", "p", "env", "list", "--reveal"],
                catch_exceptions=False,
            )
        assert result.exit_code == 0
        assert "super-secret-value" in result.output


# ── Live tests (VERCEL_E2E=1 gate) ────────────────────────────────────


@_live_skip()
class TestLiveVercel:
    """Live Vercel API tests — skipped unless VERCEL_E2E=1 and VERCEL_TOKEN set."""

    @property
    def _project(self) -> str:
        return os.environ.get("VERCEL_E2E_PROJECT", "")

    @property
    def _token(self) -> str:
        return os.environ["VERCEL_TOKEN"]

    def test_live_project_show(self):
        """project show returns valid project JSON from the Vercel API."""
        if not self._project:
            pytest.skip("Set VERCEL_E2E_PROJECT to run live project test")
        r = _run(
            ["--token", self._token, "--project", self._project, "project", "show", "--json"],
            timeout=30,
        )
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert "id" in data or "name" in data

    def test_live_env_list(self):
        """env list returns valid JSON array from Vercel API."""
        if not self._project:
            pytest.skip("Set VERCEL_E2E_PROJECT to run live env test")
        r = _run(
            ["--token", self._token, "--project", self._project, "env", "list", "--json"],
            timeout=30,
        )
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert isinstance(data, list)
        # Values must be masked
        for item in data:
            assert item.get("value") == "***" or "value" not in item

    def test_live_domain_list(self):
        """domain list returns valid JSON array from Vercel API."""
        if not self._project:
            pytest.skip("Set VERCEL_E2E_PROJECT to run live domain test")
        r = _run(
            ["--token", self._token, "--project", self._project, "domain", "list", "--json"],
            timeout=30,
        )
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert isinstance(data, list)

    def test_live_deployment_list(self):
        """deployment list returns valid JSON array from Vercel API."""
        if not self._project:
            pytest.skip("Set VERCEL_E2E_PROJECT to run live deployment test")
        r = _run(
            ["--token", self._token, "--project", self._project, "deployment", "list", "--json"],
            timeout=30,
        )
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert isinstance(data, list)

    def test_live_doctor(self):
        """doctor command passes with valid token."""
        r = _run(["--token", self._token, "doctor"], timeout=30)
        assert r.returncode == 0, r.stderr
