"""End-to-end tests for cli-anything-trellis.

These tests require a live TRELLIS.2 GPU environment.  They are gated behind
the TRELLIS_E2E=1 environment variable.

IMPORTANT: when TRELLIS_E2E=1 is set, tests MUST run or fail explicitly —
           they MUST NOT silently skip.  This is a hard requirement.

Usage (from repo root, inside the TRELLIS.2 Python environment):
    TRELLIS_E2E=1 TRELLIS_HOME=/path/to/trellis TRELLIS_PYTHON=/path/to/python \
        pytest cli_anything/trellis/tests/test_full_e2e.py -v

Without TRELLIS_E2E=1 the whole module is skipped with a single clear message.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# ── Gate: skip the entire module when TRELLIS_E2E is not set ─────────────────
# When TRELLIS_E2E=1 IS set, pytest.skip is never called — each test must run.

_E2E_ENABLED = os.environ.get("TRELLIS_E2E", "").strip() == "1"

if not _E2E_ENABLED:
    pytest.skip(
        "Set TRELLIS_E2E=1 to run end-to-end TRELLIS tests",
        allow_module_level=True,
    )

# ── Below this line TRELLIS_E2E=1 is guaranteed — no more skip calls ─────────

# Resolve config from environment (must be present when E2E is enabled)
_TRELLIS_HOME = os.environ.get("TRELLIS_HOME", "")
_TRELLIS_PYTHON = os.environ.get("TRELLIS_PYTHON", sys.executable)

# Path to the runner script (co-located with this package)
_RUNNER_PATH = Path(__file__).resolve().parent.parent / "resources" / "trellis_runner.py"

# A small 512×512 solid-white PNG we generate at module level so every test can
# use it without IO.  We keep it in a module-level tmp dir via a session fixture.

_SESSION_TMP: Path | None = None


def _make_white_png(dest: Path) -> Path:
    """Write a 512×512 white PNG to *dest*.  Requires Pillow."""
    try:
        from PIL import Image  # type: ignore[import]
    except ImportError as exc:
        pytest.fail(f"Pillow is required for E2E tests but is not installed: {exc}")
    img = Image.new("RGB", (512, 512), color=(255, 255, 255))
    img.save(str(dest))
    return dest


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def e2e_tmp(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Session-scoped temp directory for E2E artifacts."""
    return tmp_path_factory.mktemp("e2e")


@pytest.fixture(scope="session")
def white_png(e2e_tmp: Path) -> Path:
    """A 512×512 white PNG, created once per session."""
    return _make_white_png(e2e_tmp / "white.png")


@pytest.fixture(scope="session")
def trellis_home() -> Path | None:
    """Return validated TRELLIS_HOME path, or fail the test if invalid."""
    if not _TRELLIS_HOME:
        pytest.fail(
            "TRELLIS_HOME must be set when TRELLIS_E2E=1.  "
            "Export TRELLIS_HOME=/path/to/trellis2/repo"
        )
    p = Path(_TRELLIS_HOME)
    if not p.is_dir():
        pytest.fail(f"TRELLIS_HOME does not exist or is not a directory: {p}")
    return p


# ── Helper ────────────────────────────────────────────────────────────────────


def _run_runner(*args: str, stdin_payload: str = "", timeout: int = 600) -> dict:
    """Run trellis_runner.py with *args*, feeding *stdin_payload*.

    Returns the parsed JSON result.  Fails the test explicitly on any error.
    """
    env = os.environ.copy()
    if _TRELLIS_HOME:
        env["TRELLIS_HOME"] = _TRELLIS_HOME
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{_TRELLIS_HOME}{os.pathsep}{existing}" if existing else _TRELLIS_HOME

    cmd = [_TRELLIS_PYTHON, str(_RUNNER_PATH), *args]
    try:
        proc = subprocess.run(
            cmd,
            input=stdin_payload,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired:
        pytest.fail(f"trellis_runner.py {args[0]!r} timed out after {timeout}s")

    stdout = proc.stdout.strip()
    if not stdout:
        pytest.fail(
            f"trellis_runner.py {args[0]!r} produced no stdout.\nstderr: {proc.stderr.strip()}"
        )

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"trellis_runner.py {args[0]!r} stdout is not valid JSON: {exc}\nstdout: {stdout[:500]}"
        )


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestProbeGpu:
    """probe-gpu subcommand — verifies CUDA availability."""

    def test_probe_gpu_returns_dict(self, trellis_home: Path) -> None:
        result = _run_runner("probe-gpu")
        assert isinstance(result, dict), f"Expected dict, got: {type(result)}"

    def test_probe_gpu_has_required_keys(self, trellis_home: Path) -> None:
        result = _run_runner("probe-gpu")
        assert "available" in result, f"Missing 'available' key: {result}"
        assert "device_count" in result, f"Missing 'device_count' key: {result}"
        assert "devices" in result, f"Missing 'devices' key: {result}"

    def test_probe_gpu_cuda_available(self, trellis_home: Path) -> None:
        """TRELLIS.2 requires CUDA — fail clearly if not available."""
        result = _run_runner("probe-gpu")
        if not result.get("available"):
            pytest.fail(
                "CUDA is not available in the TRELLIS Python environment.  "
                "TRELLIS.2 requires a CUDA-capable GPU.  "
                f"probe-gpu result: {result}"
            )

    def test_probe_gpu_at_least_one_device(self, trellis_home: Path) -> None:
        result = _run_runner("probe-gpu")
        device_count = result.get("device_count", 0)
        assert device_count >= 1, (
            f"Expected at least 1 CUDA device, got {device_count}.  probe-gpu result: {result}"
        )

    def test_probe_gpu_devices_have_names(self, trellis_home: Path) -> None:
        result = _run_runner("probe-gpu")
        devices = result.get("devices", [])
        for device in devices:
            assert "name" in device, f"Device missing 'name': {device}"
            assert device["name"], f"Device has empty name: {device}"


class TestRunnerGenerate:
    """generate subcommand — full pipeline smoke test."""

    def _make_record(
        self,
        image_path: str,
        output_dir: str,
        resolution: str = "low",
        seed: int = 42,
        decimation_target: int = 50_000,
        texture_size: int = 512,
    ) -> str:
        """Return a JSON-serialised minimal GenerationRecord payload."""
        import secrets

        record = {
            "job_id": secrets.token_hex(8),
            "image_path": image_path,
            "output_dir": output_dir,
            "resolution": resolution,
            "seed": seed,
            "decimation_target": decimation_target,
            "texture_size": texture_size,
            "status": "pending",
            "created_at": 0.0,
            "started_at": None,
            "finished_at": None,
            "glb_path": None,
            "error": None,
            "extra": {},
        }
        return json.dumps(record)

    def test_generate_low_resolution(
        self,
        white_png: Path,
        e2e_tmp: Path,
        trellis_home: Path,
    ) -> None:
        """Full pipeline run at low resolution (12 steps)."""
        output_dir = str(e2e_tmp / "generate_low")
        payload = self._make_record(
            image_path=str(white_png),
            output_dir=output_dir,
            resolution="low",
            seed=42,
            decimation_target=50_000,
            texture_size=512,
        )

        result = _run_runner("generate", stdin_payload=payload, timeout=600)

        assert result.get("status") == "done", (
            f"Expected status=done, got: {result.get('status')!r}\nerror: {result.get('error')}"
        )
        glb_path = result.get("glb_path")
        assert glb_path, f"glb_path is empty in result: {result}"
        assert Path(glb_path).exists(), f"GLB file does not exist on disk: {glb_path}"
        assert Path(glb_path).suffix == ".glb", (
            f"Expected .glb extension, got: {Path(glb_path).suffix}"
        )
        assert Path(glb_path).stat().st_size > 0, f"GLB file is empty: {glb_path}"

    def test_generate_sets_finished_at(
        self,
        white_png: Path,
        e2e_tmp: Path,
        trellis_home: Path,
    ) -> None:
        output_dir = str(e2e_tmp / "generate_finished_at")
        payload = self._make_record(
            image_path=str(white_png),
            output_dir=output_dir,
            resolution="low",
            seed=7,
        )
        result = _run_runner("generate", stdin_payload=payload, timeout=600)
        assert result.get("status") == "done", f"Generation failed: {result.get('error')}"
        finished_at = result.get("finished_at")
        assert finished_at is not None, "finished_at not set in done result"
        assert isinstance(finished_at, (int, float)), (
            f"finished_at should be numeric, got: {type(finished_at)}"
        )
        assert finished_at > 0, f"finished_at should be positive: {finished_at}"

    def test_generate_seed_preserved(
        self,
        white_png: Path,
        e2e_tmp: Path,
        trellis_home: Path,
    ) -> None:
        """If a positive seed is supplied, it should be echoed back."""
        output_dir = str(e2e_tmp / "generate_seed")
        payload = self._make_record(
            image_path=str(white_png),
            output_dir=output_dir,
            resolution="low",
            seed=1234,
        )
        result = _run_runner("generate", stdin_payload=payload, timeout=600)
        assert result.get("status") == "done", f"Generation failed: {result.get('error')}"
        assert result.get("seed") == 1234, (
            f"Seed not preserved: expected 1234, got {result.get('seed')}"
        )

    def test_generate_negative_seed_randomised(
        self,
        white_png: Path,
        e2e_tmp: Path,
        trellis_home: Path,
    ) -> None:
        """seed=-1 should be replaced with a positive random seed."""
        output_dir = str(e2e_tmp / "generate_neg_seed")
        payload = self._make_record(
            image_path=str(white_png),
            output_dir=output_dir,
            resolution="low",
            seed=-1,
        )
        result = _run_runner("generate", stdin_payload=payload, timeout=600)
        assert result.get("status") == "done", f"Generation failed: {result.get('error')}"
        returned_seed = result.get("seed")
        assert returned_seed is not None, "seed not in result"
        assert returned_seed >= 0, (
            f"Expected non-negative seed after randomisation, got: {returned_seed}"
        )

    def test_generate_missing_image_fails_gracefully(
        self,
        e2e_tmp: Path,
        trellis_home: Path,
    ) -> None:
        """Missing image path → status=failed with descriptive error."""
        output_dir = str(e2e_tmp / "generate_missing")
        payload = self._make_record(
            image_path="/nonexistent/path/image.png",
            output_dir=output_dir,
            resolution="low",
            seed=1,
        )
        result = _run_runner("generate", stdin_payload=payload, timeout=60)
        assert result.get("status") == "failed", (
            f"Expected status=failed, got: {result.get('status')!r}"
        )
        error = result.get("error", "")
        assert error, "Expected a non-empty error message"
        # Should mention the image path
        assert "/nonexistent/path/image.png" in error or "image" in error.lower(), (
            f"Error message should reference the bad path.  Got: {error}"
        )

    def test_generate_empty_stdin_fails_gracefully(
        self,
        trellis_home: Path,
    ) -> None:
        """Empty stdin → status=failed."""
        result = _run_runner("generate", stdin_payload="", timeout=60)
        assert result.get("status") == "failed", (
            f"Expected status=failed for empty stdin, got: {result.get('status')!r}"
        )

    def test_generate_invalid_json_stdin_fails_gracefully(
        self,
        trellis_home: Path,
    ) -> None:
        """Malformed JSON on stdin → status=failed."""
        result = _run_runner("generate", stdin_payload="{not valid json}", timeout=60)
        assert result.get("status") == "failed", (
            f"Expected status=failed for invalid JSON, got: {result.get('status')!r}"
        )

    def test_generate_glb_filename_matches_job_id(
        self,
        white_png: Path,
        e2e_tmp: Path,
        trellis_home: Path,
    ) -> None:
        """GLB filename should be <job_id>.glb."""
        import json as _json

        output_dir = str(e2e_tmp / "generate_filename")
        raw_payload = self._make_record(
            image_path=str(white_png),
            output_dir=output_dir,
            resolution="low",
            seed=99,
        )
        job_id = _json.loads(raw_payload)["job_id"]
        result = _run_runner("generate", stdin_payload=raw_payload, timeout=600)
        assert result.get("status") == "done", f"Generation failed: {result.get('error')}"
        glb_path = result.get("glb_path", "")
        glb_name = Path(glb_path).name
        assert glb_name == f"{job_id}.glb", f"Expected {job_id}.glb, got: {glb_name}"


class TestCliE2E:
    """Full CLI command round-trip — uses the installed `trellis` entry point."""

    def _cli(self, *args: str, timeout: int = 30) -> subprocess.CompletedProcess:
        """Run the CLI via `python -m cli_anything.trellis.trellis_cli`."""
        env = os.environ.copy()
        if _TRELLIS_HOME:
            env["TRELLIS_HOME"] = _TRELLIS_HOME
        cmd = [_TRELLIS_PYTHON, "-m", "cli_anything.trellis.trellis_cli", *args]
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )

    def test_cli_probe_gpu_json(self, trellis_home: Path) -> None:
        """config probe-gpu --json should return valid JSON with 'available'."""
        proc = self._cli("config", "probe-gpu", "--json")
        assert proc.returncode == 0, f"probe-gpu exited {proc.returncode}.\nstderr: {proc.stderr}"
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            pytest.fail(f"probe-gpu --json output is not valid JSON: {exc}\n{proc.stdout[:200]}")
        assert "available" in data, f"'available' not in probe-gpu JSON: {data}"

    def test_cli_generate_run(
        self,
        white_png: Path,
        e2e_tmp: Path,
        trellis_home: Path,
    ) -> None:
        """generate run → JSON result with status=done and glb_path."""
        output_dir = str(e2e_tmp / "cli_generate")
        proc = self._cli(
            "--json",
            "--trellis-home",
            str(trellis_home),
            "--trellis-python",
            _TRELLIS_PYTHON,
            "generate",
            "run",
            "--image",
            str(white_png),
            "--output-dir",
            output_dir,
            "--resolution",
            "low",
            "--seed",
            "42",
            timeout=600,
        )
        assert proc.returncode == 0, (
            f"generate run exited {proc.returncode}.\nstderr: {proc.stderr}\nstdout: {proc.stdout}"
        )
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            pytest.fail(f"generate run --json output is not valid JSON: {exc}\n{proc.stdout[:500]}")
        assert data.get("status") == "done", (
            f"Expected status=done, got: {data.get('status')!r}\nerror: {data.get('error')}"
        )
        glb = data.get("glb_path", "")
        assert glb and Path(glb).exists(), f"glb_path absent or file missing: {glb!r}"

    def test_cli_jobs_list_after_generate(
        self,
        white_png: Path,
        e2e_tmp: Path,
        trellis_home: Path,
    ) -> None:
        """After a successful generate run the job appears in jobs list."""
        output_dir = str(e2e_tmp / "cli_jobs_list")
        # Run a generation so there is something in the catalog
        proc = self._cli(
            "--json",
            "--trellis-home",
            str(trellis_home),
            "--trellis-python",
            _TRELLIS_PYTHON,
            "generate",
            "run",
            "--image",
            str(white_png),
            "--output-dir",
            output_dir,
            "--resolution",
            "low",
            "--seed",
            "11",
            timeout=600,
        )
        if proc.returncode != 0:
            pytest.fail(
                f"Pre-condition generate failed (exit {proc.returncode}).\nstderr: {proc.stderr}"
            )
        gen_data = json.loads(proc.stdout)
        job_id = gen_data.get("job_id")
        assert job_id, "job_id not in generate output"

        # Now list jobs
        list_proc = self._cli("--json", "jobs", "list")
        assert list_proc.returncode == 0, (
            f"jobs list exited {list_proc.returncode}.\nstderr: {list_proc.stderr}"
        )
        try:
            jobs = json.loads(list_proc.stdout)
        except json.JSONDecodeError as exc:
            pytest.fail(f"jobs list --json output is not valid JSON: {exc}")
        job_ids = [j.get("job_id") for j in jobs]
        assert job_id in job_ids, f"job_id {job_id!r} not found in jobs list: {job_ids}"
