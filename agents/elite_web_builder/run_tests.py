#!/usr/bin/env python3
"""Standalone test runner for elite_web_builder.

Isolates the package from the parent agents/__init__.py by
pre-registering a stub before any imports happen.

Usage:
    python run_tests.py                    # Run tests
    python run_tests.py --cov              # Run tests with coverage
    python run_tests.py -k test_name       # Run specific tests
"""

import sys
import types
from pathlib import Path

# MUST be done before any other imports
# Stub out the parent 'agents' module to avoid its heavy __init__.py
_agents_dir = str(Path(__file__).resolve().parent.parent)
_pkg_dir = str(Path(__file__).resolve().parent)
_stub = types.ModuleType("agents")
_stub.__path__ = [_agents_dir]
_stub.__package__ = "agents"
_stub.__file__ = str(Path(_agents_dir) / "__init__.py")
sys.modules["agents"] = _stub

# Ensure project root is in path
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Also add agents dir so 'elite_web_builder' resolves
if _agents_dir not in sys.path:
    sys.path.insert(0, _agents_dir)

# Now import and run pytest
import pytest

if __name__ == "__main__":
    test_dir = str(Path(__file__).resolve().parent / "tests")

    # Separate --cov flag from other args
    user_args = sys.argv[1:]
    want_coverage = "--cov" in user_args
    if want_coverage:
        user_args.remove("--cov")

    args = [
        test_dir,
        "-v",
        "--tb=short",
        "--override-ini=asyncio_mode=auto",
        "-p", "no:cacheprovider",
        "--rootdir", _pkg_dir,
        "-c", "/dev/null",  # Ignore parent pyproject.toml
    ]

    if want_coverage:
        args.extend([
            f"--cov={_pkg_dir}",
            "--cov-report=term-missing",
            "--cov-config=/dev/null",
        ])

    args.extend(user_args)
    sys.exit(pytest.main(args))
