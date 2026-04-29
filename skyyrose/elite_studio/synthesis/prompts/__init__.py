"""Prompt templates — physics-described decoration language."""

from .base_prompts import build_base_prompt
from .decoration_prompts import build_decoration_prompt

__all__ = ["build_base_prompt", "build_decoration_prompt"]
