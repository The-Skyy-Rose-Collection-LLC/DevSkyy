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

# Add scripts/ to path so nano_banana package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))
# Add repo root so optional features can import sibling packages like
# `skyyrose.elite_studio.quality.clip_alignment` (used by --score-alignment).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nano_banana.cli import main

if __name__ == "__main__":
    main()
