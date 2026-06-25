"""Social Media venture — Elite Studio."""

from __future__ import annotations

from .agents import SOCIAL_AGENTS
from .config import DEFAULT_CONFIG, SUPPORTED_PLATFORMS, SocialVentureConfig
from .pipeline import MANIFEST, SocialPipeline, build_pipeline
from .state import SocialState

__all__ = [
    "DEFAULT_CONFIG",
    "MANIFEST",
    "SOCIAL_AGENTS",
    "SUPPORTED_PLATFORMS",
    "SocialPipeline",
    "SocialState",
    "SocialVentureConfig",
    "build_pipeline",
]
