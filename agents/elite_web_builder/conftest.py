"""Pytest configuration for elite_web_builder.

Pre-registers a lightweight 'agents' module stub in sys.modules to prevent
the heavy parent agents/__init__.py from being imported during test collection.
The parent package imports 30+ agents with deep dependency chains (pydantic,
cryptography, google-adk, etc.) that are not needed for elite_web_builder tests.
"""

import sys
import types
from pathlib import Path

# Register a lightweight stub BEFORE pytest tries to import the real agents/__init__.py
if "agents" not in sys.modules:
    _stub = types.ModuleType("agents")
    _stub.__path__ = [str(Path(__file__).resolve().parent.parent)]
    _stub.__package__ = "agents"
    sys.modules["agents"] = _stub

# Ensure agents.elite_web_builder resolves correctly
_ewb_path = str(Path(__file__).resolve().parent)
_ewb_module_key = "agents.elite_web_builder"
if _ewb_module_key not in sys.modules:
    import importlib
    spec = importlib.util.spec_from_file_location(
        _ewb_module_key,
        str(Path(__file__).resolve().parent / "__init__.py"),
        submodule_search_locations=[_ewb_path],
    )
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        mod.__path__ = [_ewb_path]
        mod.__package__ = _ewb_module_key
        sys.modules[_ewb_module_key] = mod
        # Don't exec the module yet - let normal imports handle it
