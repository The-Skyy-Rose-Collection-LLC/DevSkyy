"""Shared sys.path setup for tool modules.

The render_pipeline tools wrap `nano_banana.*` modules that live under
`scripts/nano_banana/`. They also wrap loaders from the project root
(`skyyrose.core.dossier_loader`, `llm.model_ids`). Importing both sets
requires putting both `<repo>/` and `<repo>/scripts/` on sys.path.

Call `ensure_repo_paths()` once at module import time. Idempotent.
"""

from __future__ import annotations

import sys
from pathlib import Path

# agents/render_pipeline/tools/_paths.py → repo
REPO_ROOT = Path(__file__).resolve().parents[3]


def ensure_repo_paths() -> Path:
    """Insert repo + scripts onto sys.path. Returns the repo root."""
    repo_str = str(REPO_ROOT)
    scripts_str = str(REPO_ROOT / "scripts")
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)
    if scripts_str not in sys.path:
        sys.path.insert(0, scripts_str)
    return REPO_ROOT
