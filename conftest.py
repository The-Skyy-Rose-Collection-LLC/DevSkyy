"""Pytest configuration for DevSkyy test suite."""

import sys
from pathlib import Path

# Add sdk/python to path for ADK imports
SDK_PATH = Path(__file__).parent / "sdk" / "python"
if str(SDK_PATH) not in sys.path:
    sys.path.insert(0, str(SDK_PATH))

# Configure pytest plugins and fixtures
pytest_plugins = []
