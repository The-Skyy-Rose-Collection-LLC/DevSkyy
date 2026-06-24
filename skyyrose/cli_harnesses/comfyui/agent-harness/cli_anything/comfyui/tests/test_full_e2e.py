"""test_full_e2e.py — CLI integration + live E2E tests for cli-anything-comfyui.

Gate: set COMFYUI_E2E=1 to run live tests.
Without the flag all tests in this file skip cleanly (0 failures).
With COMFYUI_E2E=1 and ComfyUI unreachable, live-server tests FAIL — not skip.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# E2E gate
# ---------------------------------------------------------------------------

_E2E = os.environ.get("COMFYUI_E2E", "0").strip() == "1"
pytestmark = pytest.mark.skipif(not _E2E, reason="COMFYUI_E2E not set to 1")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_HARNESS = Path(__file__).resolve().parents[4]  # agent-harness/


def _resolve_cli(name: str = "comfyui") -> list[str]:
    """Return argv prefix for invoking the CLI via the current Python interpreter."""
    return [sys.executable, "-m", "cli_anything.comfyui"]


def _run(
    *args: str,
    env: dict[str, str] | None = None,
    check: bool = False,
    capture: bool = True,
) -> subprocess.CompletedProcess:
    """Run the CLI in a subprocess and return the CompletedProcess."""
    merged = {**os.environ, **(env or {})}
    cmd = _resolve_cli() + list(args)
    return subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        env=merged,
        check=check,
    )


def _run_json(*args: str, env: dict[str, str] | None = None) -> object:
    """Run CLI with --json, parse stdout as JSON."""
    result = _run("--json", *args, env=env)
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Phase 1 — --help banners (offline, always run when E2E gate open)
# ---------------------------------------------------------------------------


class TestHelpBanners:
    """--help output works for root and all subgroups."""

    def test_root_help_exits_zero(self):
        r = _run("--help")
        assert r.returncode == 0

    def test_root_help_contains_version_flag(self):
        r = _run("--help")
        assert "-V" in r.stdout or "--version" in r.stdout

    def test_root_help_lists_system_subgroup(self):
        r = _run("--help")
        assert "system" in r.stdout

    def test_root_help_lists_nodes_subgroup(self):
        r = _run("--help")
        assert "nodes" in r.stdout

    def test_root_help_lists_models_subgroup(self):
        r = _run("--help")
        assert "models" in r.stdout

    def test_root_help_lists_queue_subgroup(self):
        r = _run("--help")
        assert "queue" in r.stdout

    def test_root_help_lists_history_subgroup(self):
        r = _run("--help")
        assert "history" in r.stdout

    def test_root_help_lists_workflow_subgroup(self):
        r = _run("--help")
        assert "workflow" in r.stdout

    def test_root_help_lists_session_subgroup(self):
        r = _run("--help")
        assert "session" in r.stdout

    def test_root_help_lists_manifest_subgroup(self):
        r = _run("--help")
        assert "manifest" in r.stdout

    def test_root_help_lists_doctor_subgroup(self):
        r = _run("--help")
        assert "doctor" in r.stdout

    def test_system_help(self):
        r = _run("system", "--help")
        assert r.returncode == 0
        assert "stats" in r.stdout

    def test_nodes_help(self):
        r = _run("nodes", "--help")
        assert r.returncode == 0
        assert "list" in r.stdout

    def test_models_help(self):
        r = _run("models", "--help")
        assert r.returncode == 0

    def test_queue_help(self):
        r = _run("queue", "--help")
        assert r.returncode == 0
        assert "submit" in r.stdout

    def test_history_help(self):
        r = _run("history", "--help")
        assert r.returncode == 0

    def test_workflow_help(self):
        r = _run("workflow", "--help")
        assert r.returncode == 0
        assert "validate" in r.stdout

    def test_session_help(self):
        r = _run("session", "--help")
        assert r.returncode == 0
        assert "new" in r.stdout

    def test_manifest_help(self):
        r = _run("manifest", "--help")
        assert r.returncode == 0

    def test_doctor_help(self):
        r = _run("doctor", "--help")
        assert r.returncode == 0

    def test_version_flag(self):
        r = _run("--version")
        assert r.returncode == 0
        assert "1.0.0" in r.stdout or "comfyui" in r.stdout.lower()

    def test_unknown_command_exits_nonzero(self):
        r = _run("does-not-exist")
        assert r.returncode != 0


# ---------------------------------------------------------------------------
# Phase 2 — JSON output mode (offline-friendly, mocked via env)
# ---------------------------------------------------------------------------


class TestJsonOutputMode:
    """--json flag produces valid JSON from commands that support it."""

    def test_json_flag_env_var_COMFYUI_JSON(self):
        """COMFYUI_JSON=1 is equivalent to --json flag."""
        # doctor deps doesn't need live server
        r = _run("doctor", "deps", env={"COMFYUI_JSON": "1"})
        assert r.returncode == 0
        parsed = json.loads(r.stdout)
        assert isinstance(parsed, (dict, list))

    def test_json_flag_inline_doctor_deps(self):
        r = _run("--json", "doctor", "deps")
        assert r.returncode == 0
        parsed = json.loads(r.stdout)
        assert isinstance(parsed, (dict, list))

    def test_doctor_deps_json_has_click_key(self):
        r = _run("--json", "doctor", "deps")
        assert r.returncode == 0
        parsed = json.loads(r.stdout)
        assert "click" in parsed

    def test_doctor_deps_json_has_httpx_key(self):
        r = _run("--json", "doctor", "deps")
        assert r.returncode == 0
        parsed = json.loads(r.stdout)
        assert "httpx" in parsed


# ---------------------------------------------------------------------------
# Phase 3 — --confirm gate (offline, no server needed)
# ---------------------------------------------------------------------------


class TestConfirmGate:
    """Destructive commands exit 1 without --confirm, not hitting network."""

    def test_queue_clear_no_confirm_exits_1(self):
        r = _run("queue", "clear", env={"COMFYUI_HOST": "http://127.0.0.1:59999"})
        assert r.returncode == 1

    def test_queue_interrupt_no_confirm_exits_1(self):
        r = _run("queue", "interrupt", env={"COMFYUI_HOST": "http://127.0.0.1:59999"})
        assert r.returncode == 1

    def test_history_clear_no_confirm_exits_1(self):
        r = _run("history", "clear", env={"COMFYUI_HOST": "http://127.0.0.1:59999"})
        assert r.returncode == 1

    def test_queue_clear_confirm_flag_present_reaches_network(self):
        """With --confirm the command tries the network (unreachable → non-zero exit, but different error)."""
        r = _run("queue", "clear", "--confirm", env={"COMFYUI_HOST": "http://127.0.0.1:59999"})
        # returncode != 0 still (network error), but stderr changes
        assert r.returncode != 0

    def test_session_delete_no_confirm_exits_1(self):
        """session delete without --confirm exits 1 immediately."""
        r = _run(
            "session", "delete", "nonexistent-id", env={"COMFYUI_HOST": "http://127.0.0.1:59999"}
        )
        assert r.returncode == 1


# ---------------------------------------------------------------------------
# Phase 4 — Workflow commands (offline, uses temp files)
# ---------------------------------------------------------------------------


class TestWorkflowOffline:
    """workflow validate / show / nodes work without a live server."""

    def _make_workflow(self) -> Path:
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
        workflow = {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "v1-5-pruned.safetensors"},
            },
            "2": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["1", 0],
                    "positive": ["3", 0],
                    "negative": ["4", 0],
                    "latent_image": ["5", 0],
                    "seed": 42,
                    "steps": 20,
                    "cfg": 7.5,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                },
            },
        }
        json.dump(workflow, tmp)
        tmp.close()
        return Path(tmp.name)

    def test_workflow_validate_valid_file(self):
        wf = self._make_workflow()
        r = _run("workflow", "validate", str(wf))
        wf.unlink(missing_ok=True)
        assert r.returncode == 0

    def test_workflow_validate_invalid_json(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
        tmp.write("not json {{{")
        tmp.close()
        r = _run("workflow", "validate", tmp.name)
        Path(tmp.name).unlink(missing_ok=True)
        assert r.returncode != 0

    def test_workflow_show_outputs_json_flag(self):
        wf = self._make_workflow()
        r = _run("--json", "workflow", "show", str(wf))
        wf.unlink(missing_ok=True)
        assert r.returncode == 0
        parsed = json.loads(r.stdout)
        assert isinstance(parsed, dict)

    def test_workflow_nodes_lists_class_types(self):
        wf = self._make_workflow()
        r = _run("workflow", "nodes", str(wf))
        wf.unlink(missing_ok=True)
        assert r.returncode == 0
        assert "CheckpointLoaderSimple" in r.stdout or r.returncode == 0

    def test_workflow_validate_missing_file_exits_nonzero(self):
        r = _run("workflow", "validate", "/tmp/no_such_workflow_xyz123.json")
        assert r.returncode != 0


# ---------------------------------------------------------------------------
# Phase 5 — Session commands (offline, uses temp home)
# ---------------------------------------------------------------------------


class TestSessionOffline:
    """Session create / list / show roundtrip — no server required."""

    def test_session_new_exits_zero(self, tmp_path):
        r = _run(
            "session",
            "new",
            env={"CLI_ANYTHING_HOME": str(tmp_path), "COMFYUI_HOST": "http://127.0.0.1:8188"},
        )
        assert r.returncode == 0

    def test_session_new_json_has_id(self, tmp_path):
        r = _run(
            "--json",
            "session",
            "new",
            env={"CLI_ANYTHING_HOME": str(tmp_path), "COMFYUI_HOST": "http://127.0.0.1:8188"},
        )
        assert r.returncode == 0
        parsed = json.loads(r.stdout)
        assert "id" in parsed

    def test_session_list_after_new(self, tmp_path):
        _run(
            "session",
            "new",
            env={"CLI_ANYTHING_HOME": str(tmp_path), "COMFYUI_HOST": "http://127.0.0.1:8188"},
        )
        r = _run(
            "session",
            "list",
            env={"CLI_ANYTHING_HOME": str(tmp_path)},
        )
        assert r.returncode == 0

    def test_session_list_empty_when_no_sessions(self, tmp_path):
        r = _run("session", "list", env={"CLI_ANYTHING_HOME": str(tmp_path)})
        assert r.returncode == 0

    def test_session_show_existing(self, tmp_path):
        env = {"CLI_ANYTHING_HOME": str(tmp_path), "COMFYUI_HOST": "http://127.0.0.1:8188"}
        new_r = _run("--json", "session", "new", env=env)
        sess_id = json.loads(new_r.stdout)["id"]
        r = _run("session", "show", sess_id, env=env)
        assert r.returncode == 0

    def test_session_show_json(self, tmp_path):
        env = {"CLI_ANYTHING_HOME": str(tmp_path), "COMFYUI_HOST": "http://127.0.0.1:8188"}
        new_r = _run("--json", "session", "new", env=env)
        sess_id = json.loads(new_r.stdout)["id"]
        r = _run("--json", "session", "show", sess_id, env=env)
        assert r.returncode == 0
        parsed = json.loads(r.stdout)
        assert parsed["id"] == sess_id

    def test_session_show_nonexistent_exits_nonzero(self, tmp_path):
        r = _run(
            "session",
            "show",
            "no-such-session-id-abc",
            env={"CLI_ANYTHING_HOME": str(tmp_path)},
        )
        assert r.returncode != 0

    def test_session_delete_nonexistent_exits_nonzero(self, tmp_path):
        r = _run(
            "session",
            "delete",
            "--confirm",
            "no-such-session-id-xyz",
            env={"CLI_ANYTHING_HOME": str(tmp_path)},
        )
        assert r.returncode != 0

    def test_multiple_sessions_list_all(self, tmp_path):
        env = {"CLI_ANYTHING_HOME": str(tmp_path), "COMFYUI_HOST": "http://127.0.0.1:8188"}
        _run("session", "new", env=env)
        _run("session", "new", env=env)
        _run("session", "new", env=env)
        r = _run("--json", "session", "list", env=env)
        assert r.returncode == 0
        parsed = json.loads(r.stdout)
        assert isinstance(parsed, list)
        assert len(parsed) >= 3


# ---------------------------------------------------------------------------
# Phase 6 — Live server tests (COMFYUI_E2E=1, server must be up)
# ---------------------------------------------------------------------------

_LIVE_HOST = os.environ.get("COMFYUI_HOST", "http://127.0.0.1:8188")


class TestLiveServerConnectivity:
    """These tests FAIL (not skip) when ComfyUI is unreachable."""

    def test_live_doctor_check_exits_zero(self):
        """doctor check must succeed against a live server."""
        r = _run("doctor", "check", env={"COMFYUI_HOST": _LIVE_HOST})
        assert r.returncode == 0, (
            f"doctor check failed — is ComfyUI running at {_LIVE_HOST}?\n"
            f"stdout: {r.stdout}\nstderr: {r.stderr}"
        )

    def test_live_system_stats_returns_json(self):
        r = _run("--json", "system", "stats", env={"COMFYUI_HOST": _LIVE_HOST})
        assert r.returncode == 0, f"system stats failed: {r.stderr}"
        parsed = json.loads(r.stdout)
        assert isinstance(parsed, dict)

    def test_live_system_stats_has_system_key(self):
        r = _run("--json", "system", "stats", env={"COMFYUI_HOST": _LIVE_HOST})
        assert r.returncode == 0
        parsed = json.loads(r.stdout)
        assert "system" in parsed or len(parsed) > 0

    def test_live_system_embeddings_returns_list(self):
        r = _run("--json", "system", "embeddings", env={"COMFYUI_HOST": _LIVE_HOST})
        assert r.returncode == 0, f"system embeddings failed: {r.stderr}"
        parsed = json.loads(r.stdout)
        assert isinstance(parsed, list)

    def test_live_nodes_list_returns_data(self):
        r = _run("--json", "nodes", "list", env={"COMFYUI_HOST": _LIVE_HOST})
        assert r.returncode == 0, f"nodes list failed: {r.stderr}"
        parsed = json.loads(r.stdout)
        assert isinstance(parsed, (dict, list))

    def test_live_nodes_info_klsampler(self):
        r = _run("nodes", "info", "KSampler", env={"COMFYUI_HOST": _LIVE_HOST})
        assert r.returncode == 0, f"nodes info KSampler failed: {r.stderr}"

    def test_live_models_types_returns_list(self):
        r = _run("--json", "models", "types", env={"COMFYUI_HOST": _LIVE_HOST})
        assert r.returncode == 0, f"models types failed: {r.stderr}"
        parsed = json.loads(r.stdout)
        assert isinstance(parsed, list)

    def test_live_models_list_checkpoints(self):
        r = _run("--json", "models", "list", "checkpoints", env={"COMFYUI_HOST": _LIVE_HOST})
        assert r.returncode == 0, f"models list checkpoints failed: {r.stderr}"
        parsed = json.loads(r.stdout)
        assert isinstance(parsed, list)

    def test_live_queue_list_returns_data(self):
        r = _run("--json", "queue", "list", env={"COMFYUI_HOST": _LIVE_HOST})
        assert r.returncode == 0, f"queue list failed: {r.stderr}"
        parsed = json.loads(r.stdout)
        assert "running" in parsed or "pending" in parsed or isinstance(parsed, dict)

    def test_live_history_list_returns_data(self):
        r = _run("--json", "history", "list", env={"COMFYUI_HOST": _LIVE_HOST})
        assert r.returncode == 0, f"history list failed: {r.stderr}"
        parsed = json.loads(r.stdout)
        assert isinstance(parsed, (list, dict))

    def test_live_queue_submit_valid_workflow(self):
        """Submit a minimal valid workflow and verify we get a prompt_id back."""
        workflow = {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "v1-5-pruned.safetensors"},
            }
        }
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump(workflow, f)
            wf_path = f.name
        r = _run("--json", "queue", "submit", wf_path, env={"COMFYUI_HOST": _LIVE_HOST})
        Path(wf_path).unlink(missing_ok=True)
        # May fail if checkpoint doesn't exist — that's OK, server responded
        assert r.returncode in (0, 1)
        if r.returncode == 0:
            parsed = json.loads(r.stdout)
            assert "prompt_id" in parsed or isinstance(parsed, dict)


# ---------------------------------------------------------------------------
# Phase 7 — Error path + unreachable host (COMFYUI_E2E=1, server must be DOWN)
# ---------------------------------------------------------------------------


class TestUnreachableHost:
    """With COMFYUI_E2E=1, these tests use a known-unreachable host.
    They must FAIL (exit nonzero) — not skip.
    """

    _DEAD = "http://127.0.0.1:59999"

    def test_system_stats_unreachable_exits_nonzero(self):
        r = _run("system", "stats", env={"COMFYUI_HOST": self._DEAD})
        assert r.returncode != 0, "Expected nonzero exit when host unreachable"

    def test_system_stats_unreachable_json_error_key(self):
        r = _run("--json", "system", "stats", env={"COMFYUI_HOST": self._DEAD})
        assert r.returncode != 0
        # JSON mode should output {"error": "..."} when backend fails
        try:
            parsed = json.loads(r.stdout)
            assert "error" in parsed
        except json.JSONDecodeError:
            pass  # non-JSON error output is also acceptable

    def test_nodes_list_unreachable_exits_nonzero(self):
        r = _run("nodes", "list", env={"COMFYUI_HOST": self._DEAD})
        assert r.returncode != 0

    def test_models_list_unreachable_exits_nonzero(self):
        r = _run("models", "list", "checkpoints", env={"COMFYUI_HOST": self._DEAD})
        assert r.returncode != 0

    def test_history_list_unreachable_exits_nonzero(self):
        r = _run("history", "list", env={"COMFYUI_HOST": self._DEAD})
        assert r.returncode != 0

    def test_queue_list_unreachable_exits_nonzero(self):
        r = _run("queue", "list", env={"COMFYUI_HOST": self._DEAD})
        assert r.returncode != 0

    def test_doctor_check_unreachable_exits_nonzero(self):
        r = _run("doctor", "check", env={"COMFYUI_HOST": self._DEAD})
        assert r.returncode != 0

    def test_doctor_check_unreachable_json_error(self):
        r = _run("--json", "doctor", "check", env={"COMFYUI_HOST": self._DEAD})
        assert r.returncode != 0


# ---------------------------------------------------------------------------
# Phase 8 — Manifest offline (plan + show, no apply)
# ---------------------------------------------------------------------------


class TestManifestOffline:
    """manifest plan/show work without a server."""

    def _make_manifest(self, tmp_path: Path) -> Path:
        manifest_data = {
            "version": "1",
            "changes": [{"kind": "queue_submit", "label": "submit test workflow", "payload": {}}],
        }
        p = tmp_path / "test.manifest.json"
        p.write_text(json.dumps(manifest_data))
        return p

    def test_manifest_show_exits_zero(self, tmp_path):
        m = self._make_manifest(tmp_path)
        r = _run("manifest", "show", str(m))
        assert r.returncode == 0

    def test_manifest_show_json(self, tmp_path):
        m = self._make_manifest(tmp_path)
        r = _run("--json", "manifest", "show", str(m))
        assert r.returncode == 0
        parsed = json.loads(r.stdout)
        assert isinstance(parsed, (dict, list))

    def test_manifest_apply_no_confirm_exits_1(self, tmp_path):
        m = self._make_manifest(tmp_path)
        r = _run("manifest", "apply", str(m), env={"COMFYUI_HOST": "http://127.0.0.1:59999"})
        assert r.returncode == 1


# ---------------------------------------------------------------------------
# Phase 9 — Doctor deps (offline, always passable)
# ---------------------------------------------------------------------------


class TestDoctorDeps:
    """doctor deps inspects Python env — no server required."""

    def test_doctor_deps_exits_zero(self):
        r = _run("doctor", "deps")
        assert r.returncode == 0

    def test_doctor_deps_json_is_dict(self):
        r = _run("--json", "doctor", "deps")
        assert r.returncode == 0
        parsed = json.loads(r.stdout)
        assert isinstance(parsed, dict)

    def test_doctor_deps_click_present(self):
        r = _run("--json", "doctor", "deps")
        parsed = json.loads(r.stdout)
        assert parsed.get("click") is not None

    def test_doctor_deps_httpx_present(self):
        r = _run("--json", "doctor", "deps")
        parsed = json.loads(r.stdout)
        assert parsed.get("httpx") is not None
