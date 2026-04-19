"""Project-wide dotenv loader for the SkyyRose agent stack.

Loads the dedicated Elite Web Builder key file first (if present), then
falls back to the root .env and .env.hf. Returns the set of .env files
actually loaded so callers can log them.

Keeps key-lookup alias logic in one place: Gemini SDK accepts GEMINI_API_KEY,
GOOGLE_API_KEY, or GOOGLE_AI_API_KEY — we normalize to GEMINI_API_KEY so
caller code doesn't have to check all three.
"""

from __future__ import annotations

import os
from pathlib import Path

# Default load order: most-specific first, fallbacks with override=False
# so earlier files win. Tuple of (relative_path, override_flag).
DEFAULT_ENV_FILES: tuple[tuple[str, bool], ...] = (
    (".env.elite-web-builder", False),  # Dedicated team file (primary)
    (".env", False),  # Project root
    (".env.hf", False),  # HF Spaces secrets
    ("skyyrose/.env", False),  # Legacy (rarely exists)
    ("gemini/.env", True),  # Legacy override (rarely exists)
)

GEMINI_ALIASES: tuple[str, ...] = ("GOOGLE_API_KEY", "GOOGLE_AI_API_KEY")


def load_project_env(
    project_root: Path,
    env_files: tuple[tuple[str, bool], ...] = DEFAULT_ENV_FILES,
) -> list[Path]:
    """Load dotenv files from project_root in priority order.

    Silently no-ops if python-dotenv is not installed. Returns the list
    of files that existed and were loaded.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return []

    loaded: list[Path] = []
    for rel_path, override in env_files:
        path = project_root / rel_path
        if path.is_file():
            load_dotenv(path, override=override)
            loaded.append(path)

    _alias_gemini_key()
    return loaded


def _alias_gemini_key() -> None:
    """Normalize Google Gemini key env-var names to GEMINI_API_KEY."""
    if os.getenv("GEMINI_API_KEY"):
        return
    for alias in GEMINI_ALIASES:
        value = os.getenv(alias)
        if value:
            os.environ["GEMINI_API_KEY"] = value
            return
