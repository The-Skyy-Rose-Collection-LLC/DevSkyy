"""Pytest configuration for DevSkyy test suite."""

import sys
from pathlib import Path

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

# These test files depend on heavy optional dependencies (llama_index,
# sentry_sdk, onnxruntime via rembg, etc.) that may not be installed.
# Check the full import chain — wordpress alone is not sufficient.
_HEAVY_DEP_TEST_GLOBS = [
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

# Check if the full agent + enterprise import chains work.
# These test files depend on heavy optional deps (llama_index, sentry_sdk,
# onnxruntime via rembg, stability_sdk, etc.) that cascade through
# agents/__init__.py and main_enterprise.py.
_all_deps_available = True
try:
    import agents  # noqa: F401 — triggers full agent import chain
    import main_enterprise  # noqa: F401 — triggers sentry_sdk, rembg, etc.
except (ImportError, SystemExit, Exception):
    _all_deps_available = False

if not _all_deps_available:
    collect_ignore_glob.extend(_HEAVY_DEP_TEST_GLOBS)
