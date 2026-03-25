"""Test configuration — completely isolate from parent packages.

Only elite_web_builder/ is on sys.path so that `from core.model_router import ...`
resolves to elite_web_builder/core/ — NOT DevSkyy root's core/ package.
"""

import sys
from pathlib import Path

# elite_web_builder/ directory
_ELITE_DIR = Path(__file__).resolve().parent.parent
if str(_ELITE_DIR) not in sys.path:
    sys.path.insert(0, str(_ELITE_DIR))

# NOTE: DevSkyy root deliberately excluded — its core/ package collides with ours.
