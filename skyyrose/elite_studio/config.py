"""
Elite Studio configuration — paths, provider clients, constants.

Provider clients use @lru_cache for lazy singleton initialization.
Tests can import config without requiring live API keys.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Environment loading (authoritative key last with override=True)
# ---------------------------------------------------------------------------

_BASE_DIR = Path(__file__).parent.parent  # skyyrose/
_REPO_DIR = _BASE_DIR.parent  # DevSkyy/

_LOCAL_ENV = _BASE_DIR / ".env"
if _LOCAL_ENV.exists():
    load_dotenv(_LOCAL_ENV, override=False)

_PARENT_ENV = _REPO_DIR / ".env"
if _PARENT_ENV.exists():
    load_dotenv(_PARENT_ENV, override=True)

_GEMINI_ENV = _REPO_DIR / "gemini" / ".env"
if _GEMINI_ENV.exists():
    load_dotenv(_GEMINI_ENV, override=True)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

OVERRIDES_DIR = _BASE_DIR / "assets" / "data" / "prompts" / "overrides"
SOURCE_DIR = _BASE_DIR / "assets" / "images" / "source-products"
OUTPUT_DIR = _BASE_DIR / "assets" / "images" / "products"

# ---------------------------------------------------------------------------
# Provider configuration
# ---------------------------------------------------------------------------

# Vision providers
VISION_GEMINI_MODEL = "gemini-3-flash-preview"
VISION_OPENAI_MODEL = "gpt-4o"

# Generation provider
GENERATION_MODEL = "gemini-3-pro-image-preview"
GENERATION_ASPECT_RATIO = "3:4"

# Quality control provider
QC_MODEL = "claude-sonnet-4-20250514"

# Timeouts (seconds)
GEMINI_TIMEOUT = 90.0
OPENAI_TIMEOUT = 60.0
ANTHROPIC_TIMEOUT = 60.0

# Rate limiting
BATCH_DELAY_SECONDS = 10
RETRY_DELAY_SECONDS = 5
MAX_RETRIES = 2

# ---------------------------------------------------------------------------
# Compositor configuration
# ---------------------------------------------------------------------------

COMPOSITOR_OPUS_MODEL = "claude-opus-4-6"
COMPOSITOR_QA_MODEL = "gemini-3-pro-image-preview"  # visual QA (deep analysis)
COMPOSITOR_STAGE_DELAY = 2
SCENES_DIR = _BASE_DIR / "assets" / "scenes"
EDITORIAL_STAGING_DIR = _BASE_DIR / "assets" / "images" / "editorial-staging"
COMPOSITOR_FLUX_PROVIDERS = ["fal-fill", "kontext", "replicate"]

# Product source images (for compositor subject lookup)
PRODUCT_IMAGES_DIR = (
    _REPO_DIR / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products"
)

# IC-Light relighting
ICLIGHT_WEIGHTS_PATH = _BASE_DIR / "assets" / "models" / "ic-light" / "iclight_sd15_fbc.safetensors"
ICLIGHT_BASE_MODEL = "stablediffusionapi/realistic-vision-v51"
ICLIGHT_STEPS = 25
ICLIGHT_CFG = 2.0
ICLIGHT_RESOLUTION = 384

# ---------------------------------------------------------------------------
# Lazy provider clients (cached singletons — no mutable globals)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_openai_client():
    """Lazy-init OpenAI client (cached singleton)."""
    import openai

    return openai.OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        timeout=OPENAI_TIMEOUT,
    )


@lru_cache(maxsize=1)
def get_anthropic_client():
    """Lazy-init Anthropic client (cached singleton)."""
    import anthropic

    return anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        timeout=ANTHROPIC_TIMEOUT,
    )
