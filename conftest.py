"""Pytest configuration for DevSkyy test suite."""

import os
import sys
from pathlib import Path

# macOS fork-safety: a multi-threaded pytest parent that has initialized Apple's
# Network.framework (armed by the _scproxy system-proxy lookup in urllib/requests/
# httpx) SIGSEGVs in nw_settings_child_has_forked() on the child side of every
# subprocess fork — and CPython on macOS takes the fork path whenever
# close_fds=True (the default), because _HAVE_POSIX_SPAWN_CLOSEFROM is False.
# no_proxy="*" makes getproxies_environment() non-empty so _scproxy is never
# consulted. Observed macOS 26.4 + Python 3.14.3; see .wolf/buglog.json.
if sys.platform == "darwin":
    os.environ.setdefault("no_proxy", "*")
    os.environ.setdefault("NO_PROXY", "*")

    # Belt-and-suspenders for fork paths we cannot route around Popen at all
    # (e.g. multiprocessing.resource_tracker, which calls
    # _posixsubprocess.fork_exec directly — no Popen call to patch). Tells the
    # Objective-C runtime not to abort/crash a fork from a multi-threaded
    # process. Free and harmless off darwin/off-ObjC; does not by itself fix
    # the CPython posix_spawn gate below (kept for that reason), but covers
    # fork() call sites this file structurally cannot intercept.
    os.environ.setdefault("OBJC_DISABLE_INITIALIZE_FORK_SAFETY", "YES")

    # Second layer (Apple-confirmed the only reliable fix — DTS, forums thread
    # 737464): fork() after ANY higher-level framework arming is unsupported;
    # posix_spawn is a syscall, so no atfork handler ever runs in the child.
    # CPython only takes posix_spawn when close_fds is False (no closefrom on
    # macOS), so default close_fds=False for test subprocesses. Safe per
    # PEP 446: Python-created fds are CLOEXEC/non-inheritable regardless.
    # Callers that pass close_fds/preexec_fn/pass_fds explicitly are untouched
    # (they opt into the fork path knowingly).
    #
    # Third layer (bug-263 follow-up): close_fds=False is necessary but NOT
    # sufficient. CPython's own posix_spawn fast-path gate in
    # subprocess.py:_execute_child additionally requires
    # `os.path.dirname(executable)` to be non-empty — i.e. the executable must
    # already be an absolute/relative PATH, not a bare command name. Every
    # `subprocess.run(["git", ...])` / `["bash", ...])` call (the overwhelming
    # majority in this repo — git, bash, npm, shellcheck) passes a bare name
    # resolved via $PATH, so `os.path.dirname("git") == ""` and CPython
    # silently falls through to the fork() path regardless of close_fds.
    # Verified empirically: importing agents.analytics_agent (pulls in
    # numpy/scipy/sklearn/torch transitively via ml_module) is enough to arm
    # a fork-unsafe framework; a subsequent bare `["git", "--version"]` call
    # then SIGSEGVs (-11) even with close_fds=False, while the identical call
    # with `executable=shutil.which("git")` returns 0. Resolve bare names to
    # an absolute path via shutil.which so the fast path actually engages;
    # Popen still presents the original argv[0] to the child, so behavior is
    # unchanged for callers. shell=True is left alone — CPython already
    # defaults its `executable` to /bin/sh (absolute) in that case.
    import shutil as _shutil
    import subprocess as _subprocess

    _orig_popen_init = _subprocess.Popen.__init__

    def _resolve_bare_executable(args, kwargs):  # type: ignore[no-untyped-def]
        if kwargs.get("shell") or kwargs.get("executable") is not None:
            return
        if len(args) >= 3:  # executable passed positionally (3rd positional arg)
            return
        cmd = kwargs["args"] if "args" in kwargs else (args[0] if args else None)
        if isinstance(cmd, (list, tuple)) and cmd:
            prog = cmd[0]
        elif isinstance(cmd, (str, bytes, os.PathLike)):
            prog = cmd
        else:
            return
        prog = os.fspath(prog) if isinstance(prog, os.PathLike) else prog
        if not isinstance(prog, str) or os.path.dirname(prog):
            return  # already absolute/relative, or not a plain string name
        env = kwargs.get("env")
        search_path = env.get("PATH") if env is not None else None
        resolved = _shutil.which(prog, path=search_path)
        if resolved:
            kwargs["executable"] = resolved

    def _spawn_friendly_init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        if (
            len(args) <= 6  # close_fds/preexec_fn not passed positionally
            and "close_fds" not in kwargs
            and kwargs.get("preexec_fn") is None
            and not kwargs.get("pass_fds")
        ):
            kwargs["close_fds"] = False
        _resolve_bare_executable(args, kwargs)
        _orig_popen_init(self, *args, **kwargs)

    _subprocess.Popen.__init__ = _spawn_friendly_init  # type: ignore[method-assign]

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Add sdk/python to path for ADK imports
SDK_PATH = PROJECT_ROOT / "sdk" / "python"
if str(SDK_PATH) not in sys.path:
    sys.path.insert(0, str(SDK_PATH))

# Configure pytest plugins and fixtures
pytest_plugins = []

# Skip modules with missing dependencies during collection
collect_ignore_glob = []

# Check if wordpress module exists
try:
    import wordpress  # noqa: F401
except ImportError:
    # WordPress module being rebuilt - skip ALL dependent tests
    collect_ignore_glob.extend(
        [
            "tests/api/*.py",
            "tests/api/**/*.py",
            "tests/orchestration/*.py",
            "tests/integrations/*.py",
            "tests/wordpress/*.py",
            "tests/sync/*.py",
            "tests/services/test_three_d*.py",
            "tests/test_agents.py",
            "tests/test_conversation_editor.py",
            "tests/test_gemini*.py",
            "tests/test_huggingface*.py",
            "tests/test_new_api_endpoints.py",
            "tests/test_orchestration*.py",
            "tests/test_rag*.py",
            "tests/test_reference_manager.py",
            "tests/test_threed*.py",
            "tests/test_tripo*.py",
            "tests/test_gdpr*.py",
            "tests/test_orm_alembic.py",
            "tests/test_wordpress*.py",
            "tests/test_database_validation.py",
            "tests/test_sync_api.py",
            "tests/test_ai_3d_api.py",
            "tests/test_admin_dashboard_api.py",
            "tests/test_pipeline.py",
        ]
    )
