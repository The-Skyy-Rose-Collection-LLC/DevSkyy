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
    """Resolve Google API key from env vars or .env files.

    Priority order (first working key wins):
      GOOGLE_API_KEY_2 → the primary GOOGLE_API_KEY project has been
      denied access to generateContent (403), so GOOGLE_API_KEY_2 is
      promoted ahead of GOOGLE_API_KEY until the primary is restored.

    The function does TWO full passes across env + .env files: first
    pass looks exclusively for GOOGLE_API_KEY_2, second pass falls back
    to GOOGLE_API_KEY / GEMINI_API_KEY. This guarantees we never pick
    the banned primary key when a working secondary exists in another
    .env file.
    """
    env_files = (".env.hf", ".env", ".env.secrets", ".env.production")

    def _scan(var_name: str) -> str:
        # 1. process env
        v = os.getenv(var_name, "").strip()
        if v:
            return v
        # 2. .env files in order
        for env_file in env_files:
            env_path = PROJECT_ROOT / env_file
            if not env_path.exists():
                continue
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith(f"{var_name}="):
                    val = line.split("=", 1)[1].strip().strip("'\"")
                    if val:
                        log.info("Loaded API key from %s (%s)", env_file, var_name)
                        return val
        return ""

    # Pass 1: GOOGLE_API_KEY_2 (the known-working fallback)
    key = _scan("GOOGLE_API_KEY_2")
    if key:
        return key
    # Pass 2: GOOGLE_API_KEY
    key = _scan("GOOGLE_API_KEY")
    if key:
        return key
    # Pass 3: GEMINI_API_KEY
    return _scan("GEMINI_API_KEY")


def get_genai_client(timeout_ms: int = 300_000):
    """Create a Google genai Client with the official SDK.

    Returns a configured client or exits if no API key found.
    """
    from google import genai

    api_key = _find_google_api_key()
    if not api_key:
        log.error("No Google API key found. Set GOOGLE_API_KEY in env or .env.hf")
        sys.exit(1)

    return genai.Client(
        api_key=api_key,
        http_options={"timeout": timeout_ms},
    )


def get_openai_client():
    """Create an OpenAI client. Tries multiple key env vars, validates each."""
    import openai

    for var in ("OPENAI_API_KEY", "OPENAI_AGENT107_KEY", "OPENAI_FEB19", "OPENAI_MCP_KEY"):
        key = os.getenv(var, "").strip()
        if not key:
            continue
        client = openai.OpenAI(api_key=key)
        try:
            client.models.list()
            log.info("OpenAI: using %s", var)
            return client
        except openai.AuthenticationError:
            log.warning("OpenAI key %s is invalid, trying next", var)
            continue
        except Exception:
            # Network error etc — key might be fine, use it
            log.info("OpenAI: using %s (could not validate)", var)
            return client

    log.debug("No working OpenAI API key found — GPT engine unavailable")
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
