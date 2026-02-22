"""Root conftest for elite_web_builder — fully isolated from parent packages.

Prevents two namespace collisions:
1. Parent agents/__init__.py (eager imports with missing deps)
2. DevSkyy root core/ package (auth, services, etc. — heavy deps)

We shim both in sys.modules and keep ONLY elite_web_builder/ on sys.path
so `from core.model_router import ...` resolves to OUR core/ package.
"""

import sys
import types
from pathlib import Path

# Make elite_web_builder importable as a standalone package
_ELITE_DIR = Path(__file__).resolve().parent
if str(_ELITE_DIR) not in sys.path:
    sys.path.insert(0, str(_ELITE_DIR))

# Shim "agents" as a proper package pointing to OUR local agents/ dir.
# This prevents the parent DevSkyy agents/__init__.py (with heavy deps)
# from loading, while still allowing `from agents.base import ...`.
_agents_mod = types.ModuleType("agents")
_agents_mod.__path__ = [str(_ELITE_DIR / "agents")]
_agents_mod.__package__ = "agents"
sys.modules["agents"] = _agents_mod

# NOTE: DevSkyy root is NOT added here to avoid core/ namespace collision.
# When ralph_integration tests need utils/, they'll add it selectively.
