"""
scripts.flux_lora.config — All constants; zero business logic.

Follows the pattern established in scripts/oai_render/config.py:
  - load_project_env() for env loading
  - get_api_key() raises if key absent
  - api_key_present() returns bool (for dry-run paths)
  - PROJECT_ROOT derived at module load
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Project root + env loading
# ---------------------------------------------------------------------------
try:
    from config.load_env import load_project_env

    PROJECT_ROOT: Path = load_project_env()
except Exception:
    # Fallback when running outside the project tree (e.g., isolated pytest)
    PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Replicate model / version
# ---------------------------------------------------------------------------
REPLICATE_MODEL_OWNER: str = "ostris"
REPLICATE_MODEL_NAME: str = "flux-dev-lora-trainer"

# Set to a pinned version SHA to lock behaviour; None = use latest.
REPLICATE_VERSION: str | None = None

REPLICATE_BASE_URL: str = "https://api.replicate.com"

# ---------------------------------------------------------------------------
# Training defaults (override per-run via CLI flags)
# ---------------------------------------------------------------------------
DEFAULT_TRIGGER_WORD: str = "SKYYROSE"
DEFAULT_STEPS: int = 1000
DEFAULT_LORA_RANK: int = 16
DEFAULT_OPTIMIZER: str = "adamw8bit"
DEFAULT_BATCH_SIZE: int = 1
DEFAULT_RESOLUTION: str = "512,768,1024"
DEFAULT_LR_SCHEDULER: str = "constant"
DEFAULT_LEARNING_RATE: float = 4e-4

# Autocaptioning is disabled; we supply hand-crafted captions.
DEFAULT_AUTOCAPTION: bool = False
DEFAULT_AUTOCAPTION_PREFIX: str = ""

# ---------------------------------------------------------------------------
# Cost guard
# ---------------------------------------------------------------------------
# Rough estimate per training run at default steps.
EST_COST_PER_RUN_USD: float = 2.50
HARD_COST_CAP_USD: float = 10.00

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATASET_DIR: Path = PROJECT_ROOT / "datasets" / "skyyrose_lora_v5"
RUNS_DIR: Path = PROJECT_ROOT / "models" / "training-runs"
MODELS_DIR: Path = PROJECT_ROOT / "models"


# ---------------------------------------------------------------------------
# API key helpers
# ---------------------------------------------------------------------------
def get_api_key() -> str:
    """Return REPLICATE_API_TOKEN from env. Raises RuntimeError if absent."""
    key = os.environ.get("REPLICATE_API_TOKEN")
    if not key:
        raise RuntimeError("REPLICATE_API_TOKEN is not set. Export it or add it to your .env file.")
    return key


def api_key_present() -> bool:
    """Return True if REPLICATE_API_TOKEN is set (for dry-run checks)."""
    return bool(os.environ.get("REPLICATE_API_TOKEN"))
