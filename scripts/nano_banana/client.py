"""API client factories — centralized credential handling.

Each factory reads from environment variables and returns None
if the required key is missing (allowing graceful fallback).
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _find_google_api_key() -> str:
    """Resolve Google API key from env vars or .env files."""
    for var in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
        key = os.getenv(var, "").strip()
        if key:
            return key

    # Check .env files in project root
    for env_file in (".env.hf", ".env", ".env.secrets"):
        env_path = PROJECT_ROOT / env_file
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("GOOGLE_API_KEY=") or line.startswith("GEMINI_API_KEY="):
                    val = line.split("=", 1)[1].strip().strip("'\"")
                    if val:
                        log.info("Loaded API key from %s", env_file)
                        return val
    return ""


def get_genai_client(timeout_ms: int = 300_000):
    """Create a Google genai Client with the official SDK.

    Returns a configured client or exits if no API key found.
    """
    from google import genai

    api_key = _find_google_api_key()
    if not api_key:
        log.error(
            "No Google API key found. Set GOOGLE_API_KEY in env or .env.hf"
        )
        sys.exit(1)

    return genai.Client(
        api_key=api_key,
        http_options={"timeout": timeout_ms},
    )


def get_openai_client():
    """Create an OpenAI client. Returns None if no API key."""
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        log.debug("No OPENAI_API_KEY — GPT Image engine unavailable")
        return None

    try:
        import openai
        return openai.OpenAI(api_key=key)
    except ImportError:
        log.warning("openai package not installed — GPT Image unavailable")
        return None


def get_together_client():
    """Create a Together AI client for FLUX. Returns None if no API key."""
    key = os.getenv("TOGETHER_API_KEY", "").strip()
    if not key:
        log.debug("No TOGETHER_API_KEY — FLUX engine unavailable")
        return None

    try:
        import together
        return together.Together(api_key=key)
    except ImportError:
        log.warning("together package not installed — FLUX unavailable")
        return None
