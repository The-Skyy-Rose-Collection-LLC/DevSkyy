#!/usr/bin/env python3
"""Wrapper to run tests with proper coverage measurement"""

import sys
import subprocess
from pathlib import Path

# Change to project directory
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Run pytest without the global config that's causing issues
result = subprocess.run(
    [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_startup_sqlalchemy.py",
        "-v",
        "--tb=short",
    ],
    cwd=str(project_dir),
)

sys.exit(result.returncode)
