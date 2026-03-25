"""
Multi-Agent configuration — paths, models, defaults.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_DIR = Path(__file__).parent.parent.parent  # DevSkyy/
THEME_DIR = REPO_DIR / "wordpress-theme" / "skyyrose-flagship"
FRONTEND_DIR = REPO_DIR / "frontend"
ASSETS_DIR = THEME_DIR / "assets"
PRODUCT_DATA_DIR = REPO_DIR / "skyyrose" / "assets" / "data"

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

ORCHESTRATOR_MODEL = "claude-opus-4-6"
SUBAGENT_MODEL = "claude-sonnet-4-6"  # Cost-efficient for subagents
FAST_MODEL = "claude-haiku-4-5"  # Classification, simple tasks

# ---------------------------------------------------------------------------
# Agent defaults
# ---------------------------------------------------------------------------

MAX_TURNS_ORCHESTRATOR = 50
MAX_TURNS_SUBAGENT = 25
MAX_BUDGET_USD = 5.0

# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

AUDIT_LOG_DIR = REPO_DIR / ".multi-agent"
AUDIT_LOG_DIR.mkdir(exist_ok=True)
