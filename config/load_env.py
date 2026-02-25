"""
Universal environment loader for DevSkyy.

Usage:
    from config.load_env import load_project_env
    load_project_env()

Loads .env files in priority order (last wins):
    1. Root .env (all keys)
    2. gemini/.env (real API keys, overrides placeholders)

Works from any subdirectory in the project.
"""

from __future__ import annotations

import os
from pathlib import Path


def _find_project_root() -> Path:
    """Walk up from this file to find the DevSkyy project root (.git marker)."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    # Fallback: assume config/ is one level below root
    return Path(__file__).resolve().parent.parent


def load_project_env(*, verbose: bool = False) -> Path:
    """
    Load the root .env and gemini/.env (override=True) so real keys win.

    Returns the project root path for convenience.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        if verbose:
            print("[load_env] python-dotenv not installed, skipping .env loading")
        return _find_project_root()

    root = _find_project_root()

    root_env = root / ".env"
    gemini_env = root / "gemini" / ".env"

    if root_env.exists():
        load_dotenv(root_env, override=False)
        if verbose:
            print(f"[load_env] Loaded {root_env}")
    elif verbose:
        print(f"[load_env] WARNING: {root_env} not found")

    if gemini_env.exists():
        load_dotenv(gemini_env, override=True)
        if verbose:
            print(f"[load_env] Loaded {gemini_env} (override=True)")

    return root


# Auto-load when imported as a module
PROJECT_ROOT = load_project_env()
