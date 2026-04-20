#!/usr/bin/env python3
"""Nano Banana 2 — SkyyRose AI Image Pipeline.

Clean rebuild using the official Google genai SDK.

Usage:
    source .venv-imagery/bin/activate
    python scripts/nano-banana-run.py dry-run
    python scripts/nano-banana-run.py generate --sku br-001
    python scripts/nano-banana-run.py generate --step all --pro
    python scripts/nano-banana-run.py composite --sku br-001

Models:
    gemini-2.5-flash-image      — Fast, high-quality (default)
    gemini-3-pro-image-preview  — Pro quality, text rendering (--pro)
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Add project root so the skyyrose package is importable, then scripts/ so the
# nano_banana package is importable.
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Load all project env files (including .env.elite-web-builder which holds
# OPENAI_API_KEY, ANTHROPIC_API_KEY) BEFORE the CLI imports resolve any keys.
# Without this, get_openai_client() reads os.getenv("OPENAI_API_KEY") on a
# process that never loaded the dotenv — and GPT-Image silently falls back to
# Gemini, which is exactly what caused April 19's 79%-reject run.
from skyyrose.core.env_loader import load_project_env

load_project_env(PROJECT_ROOT)

from nano_banana.cli import main

if __name__ == "__main__":
    main()
