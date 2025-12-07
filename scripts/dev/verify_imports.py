#!/usr/bin/env python3
"""
Import Verification Script
Verifies that all critical files can import successfully
"""

import importlib.util
from pathlib import Path
import sys


# Critical files to verify
CRITICAL_FILES = [
    "main.py",
    "database.py",
    "config/unified_config.py",
    "core/error_ledger.py",
    "core/exceptions.py",
    "api/v1/agents.py",
    "api/v1/dashboard.py",
    "api/v1/luxury_fashion_automation.py",
    "agent/modules/backend/self_learning_system.py",
]


def verify_imports(file_path: str) -> tuple[bool, str]:
    """
    Verify that a file's imports work correctly.
    Returns (success, message)
    """
    try:
        # Try to import the module
        spec = importlib.util.spec_from_file_location("temp_module", file_path)
        if spec is None or spec.loader is None:
            return False, f"Could not load spec for {file_path}"

        module = importlib.util.module_from_spec(spec)
        sys.modules["temp_module"] = module

        # This will execute imports but not the main code
        # (assuming code is properly guarded with if __name__ == "__main__")
        spec.loader.exec_module(module)

        # Clean up
        del sys.modules["temp_module"]

        return True, "OK"
    except ImportError as e:
        return False, f"Import error: {e!s}"
    except Exception as e:
        return False, f"Error: {e!s}"


def main():
    """Main verification function"""

    base_path = Path("/home/user/DevSkyy")
    passed = 0
    failed = 0

    for file_path in CRITICAL_FILES:
        full_path = base_path / file_path

        if not full_path.exists():
            failed += 1
            continue

        success, _message = verify_imports(str(full_path))

        if success:
            passed += 1
        else:
            failed += 1

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
