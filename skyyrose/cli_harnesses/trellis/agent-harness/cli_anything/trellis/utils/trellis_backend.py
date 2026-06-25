"""TRELLIS.2 backend interface — subprocess runner + error hierarchy.

The CLI NEVER imports trellis2, torch, or o_voxel directly. All TRELLIS
operations are dispatched to `resources/trellis_runner.py` via subprocess.

Environment discovery priority (highest first):
  1. Explicit CLI flags (--trellis-home / --trellis-python)
  2. Session-saved paths (session.trellis_home / session.trellis_python)
  3. Environment variables (TRELLIS_HOME / TRELLIS_PYTHON)
  4. Auto-detection heuristics (PATH, well-known install locations)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from cli_anything.trellis.core.generation import GenerationRecord

# ── Error hierarchy ───────────────────────────────────────────────────────────


class BackendError(RuntimeError):
    """Base class for all TRELLIS backend errors."""


class TrellisNotFoundError(BackendError):
    """TRELLIS.2 installation directory not found or invalid."""


class TrellisPythonError(BackendError):
    """The specified Python interpreter could not be found or is unusable."""


class GPUUnavailableError(BackendError):
    """CUDA GPU is required but not available or CUDA drivers are missing."""


class RunnerError(BackendError):
    """The trellis_runner.py subprocess exited with a non-zero status."""

    def __init__(self, message: str, returncode: int = -1, stderr: str = ""):
        super().__init__(message)
        self.returncode = returncode
        self.stderr = stderr


class RunnerTimeoutError(BackendError):
    """The trellis_runner.py subprocess exceeded the timeout."""


# ── Runner script path ────────────────────────────────────────────────────────

_RUNNER_PATH = Path(__file__).resolve().parent.parent / "resources" / "trellis_runner.py"


# ── Environment discovery ─────────────────────────────────────────────────────


def discover_trellis_home(
    explicit: Optional[str] = None,
    session_value: Optional[str] = None,
) -> Optional[Path]:
    """Return the TRELLIS.2 installation directory, or None if not found.

    Args:
        explicit: Value from --trellis-home CLI flag.
        session_value: Value stored in the current session.

    Returns:
        Resolved Path if a valid directory is found, else None.
    """
    candidates = [
        explicit,
        session_value,
        os.environ.get("TRELLIS_HOME"),
    ]
    for candidate in candidates:
        if candidate:
            p = Path(candidate).expanduser().resolve()
            if p.is_dir():
                return p
    return None


def discover_trellis_python(
    explicit: Optional[str] = None,
    session_value: Optional[str] = None,
) -> str:
    """Return the Python interpreter to use for trellis_runner.py.

    Priority: explicit flag > session value > TRELLIS_PYTHON env > sys.executable.

    The returned path is NOT validated here — call validate_python() to check.

    Args:
        explicit: Value from --trellis-python CLI flag.
        session_value: Value stored in the current session.

    Returns:
        Path string for the Python interpreter.
    """
    candidates = [
        explicit,
        session_value,
        os.environ.get("TRELLIS_PYTHON"),
    ]
    for candidate in candidates:
        if candidate:
            return str(Path(candidate).expanduser())
    return sys.executable


def validate_python(python_path: str) -> None:
    """Raise TrellisPythonError if *python_path* is not a usable interpreter.

    Args:
        python_path: Path to the Python executable.

    Raises:
        TrellisPythonError: If the interpreter does not exist or fails to run.
    """
    p = Path(python_path)
    if not p.exists():
        raise TrellisPythonError(f"Python interpreter not found: {python_path}")
    try:
        result = subprocess.run(
            [python_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            raise TrellisPythonError(
                f"Python interpreter unusable ({python_path}): {result.stderr.strip()}"
            )
    except FileNotFoundError:
        raise TrellisPythonError(f"Python interpreter not executable: {python_path}")
    except subprocess.TimeoutExpired:
        raise TrellisPythonError(f"Python interpreter timed out: {python_path}")


def validate_trellis_home(trellis_home: Path) -> None:
    """Raise TrellisNotFoundError if *trellis_home* lacks trellis2.

    Checks for the presence of trellis2/ package directory or setup.py/
    pyproject.toml as proof of a valid installation.

    Args:
        trellis_home: Path to the TRELLIS.2 repo root or install directory.

    Raises:
        TrellisNotFoundError: If the directory does not look like TRELLIS.2.
    """
    markers = [
        trellis_home / "trellis2",
        trellis_home / "trellis2" / "__init__.py",
    ]
    if not any(m.exists() for m in markers):
        raise TrellisNotFoundError(
            f"TRELLIS.2 not found at {trellis_home}. "
            "Expected a 'trellis2/' package directory inside. "
            "Set TRELLIS_HOME or use --trellis-home."
        )


# ── Runner invocation ─────────────────────────────────────────────────────────


def build_runner_env(trellis_home: Optional[Path] = None) -> Dict[str, str]:
    """Build environment dict for the runner subprocess.

    Adds TRELLIS_HOME and the trellis directory to PYTHONPATH so the runner
    can import trellis2 without a pip install.

    Args:
        trellis_home: Path to TRELLIS.2 root directory.

    Returns:
        A copy of os.environ with TRELLIS_HOME and PYTHONPATH set.
    """
    env = os.environ.copy()
    if trellis_home:
        env["TRELLIS_HOME"] = str(trellis_home)
        # Prepend to PYTHONPATH so trellis2 is importable
        existing_pythonpath = env.get("PYTHONPATH", "")
        new_paths = [str(trellis_home)]
        if existing_pythonpath:
            new_paths.append(existing_pythonpath)
        env["PYTHONPATH"] = os.pathsep.join(new_paths)
    return env


def run_generation(
    record: GenerationRecord,
    python_path: str,
    trellis_home: Optional[Path] = None,
    timeout: Optional[int] = None,
) -> GenerationRecord:
    """Invoke trellis_runner.py as a subprocess to generate a GLB from an image.

    The runner receives a JSON payload on stdin and writes a JSON result
    to stdout. This function blocks until the runner exits.

    Args:
        record: The GenerationRecord describing the generation job.
        python_path: Path to the Python interpreter with trellis2 installed.
        trellis_home: Optional TRELLIS.2 root for PYTHONPATH injection.
        timeout: Optional timeout in seconds (None = no limit).

    Returns:
        Updated GenerationRecord with status=done and glb_path set,
        or status=failed with error set.

    Raises:
        RunnerTimeoutError: If the subprocess exceeds *timeout*.
        RunnerError: If the subprocess exits non-zero and stdout has no JSON.
    """
    runner_path = str(_RUNNER_PATH)
    cmd: List[str] = [python_path, runner_path, "generate"]
    env = build_runner_env(trellis_home)

    payload = json.dumps(record.to_dict())

    try:
        proc = subprocess.run(
            cmd,
            input=payload,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise RunnerTimeoutError(
            f"Generation job {record.job_id} timed out after {timeout}s"
        ) from exc

    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()

    # Try to parse JSON result from stdout regardless of returncode
    result: Optional[Dict[str, Any]] = None
    if stdout:
        try:
            result = json.loads(stdout)
        except json.JSONDecodeError:
            pass

    if result is not None:
        try:
            return GenerationRecord.from_dict(result)
        except (ValueError, KeyError) as exc:
            raise RunnerError(
                f"Runner returned invalid record JSON: {exc}",
                returncode=proc.returncode,
                stderr=stderr,
            ) from exc

    # No parseable JSON — treat as failure
    if proc.returncode != 0:
        error_msg = stderr or f"runner exited with code {proc.returncode}"
        raise RunnerError(
            f"Generation job {record.job_id} failed: {error_msg}",
            returncode=proc.returncode,
            stderr=stderr,
        )

    # returncode == 0 but no JSON — unexpected
    raise RunnerError(
        f"Runner exited 0 but produced no JSON output for job {record.job_id}",
        returncode=0,
        stderr=stderr,
    )


def probe_gpu(python_path: str, trellis_home: Optional[Path] = None) -> Dict[str, Any]:
    """Run a quick GPU probe via the runner subprocess.

    Args:
        python_path: Python interpreter with torch installed.
        trellis_home: Optional TRELLIS.2 root.

    Returns:
        Dict with keys: available (bool), device_count (int), devices (list of str).

    Raises:
        TrellisPythonError: If the python interpreter fails to start.
        GPUUnavailableError: If torch reports no CUDA devices.
    """
    runner_path = str(_RUNNER_PATH)
    cmd: List[str] = [python_path, runner_path, "probe-gpu"]
    env = build_runner_env(trellis_home)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
    except FileNotFoundError:
        raise TrellisPythonError(f"Python not found: {python_path}")
    except subprocess.TimeoutExpired:
        raise TrellisPythonError(f"GPU probe timed out for: {python_path}")

    stdout = proc.stdout.strip()
    if stdout:
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            pass

    stderr = proc.stderr.strip()
    raise GPUUnavailableError(f"GPU probe failed (exit {proc.returncode}): {stderr or 'no output'}")
