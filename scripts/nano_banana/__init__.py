"""Nano Banana 2 — SkyyRose AI Image Pipeline.

Clean, modular rebuild using the official Google genai SDK.

Models:
    gemini-2.5-flash-image      — Fast, high-quality (default)
    gemini-3-pro-image-preview  — Pro quality, text rendering (--pro)
"""

from nano_banana.client import get_genai_client, get_openai_client, get_together_client

__all__ = ["get_genai_client", "get_openai_client", "get_together_client"]
