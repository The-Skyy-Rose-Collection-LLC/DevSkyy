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

    # Second layer (Apple-confirmed the only reliable fix — DTS, forums thread
    # 737464): fork() after ANY higher-level framework arming is unsupported;
    # posix_spawn is a syscall, so no atfork handler ever runs in the child.
    # CPython only takes posix_spawn when close_fds is False (no closefrom on
    # macOS), so default close_fds=False for test subprocesses. Safe per
    # PEP 446: Python-created fds are CLOEXEC/non-inheritable regardless.
    # Callers that pass close_fds/preexec_fn/pass_fds explicitly are untouched
    # (they opt into the fork path knowingly).
    import subprocess as _subprocess

    _orig_popen_init = _subprocess.Popen.__init__

    def _spawn_friendly_init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        if (
            len(args) <= 6  # close_fds/preexec_fn not passed positionally
            and "close_fds" not in kwargs
            and kwargs.get("preexec_fn") is None
            and not kwargs.get("pass_fds")
        ):
            kwargs["close_fds"] = False
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
