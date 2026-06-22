"""Configuration for the Social Media venture."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from skyyrose.elite_studio.config import OUTPUT_DIR

# Canonical platform slugs accepted by SocialMediaAgent (agents.social_media_agent.Platform).
SUPPORTED_PLATFORMS: tuple[str, ...] = ("instagram", "tiktok", "twitter", "facebook")


@dataclass(frozen=True)
class SocialVentureConfig:
    """Static config consumed by the social pipeline.

    The free, template-based publisher (`SocialMediaAgent`) needs no model.
    The two cost-gated nodes (graphics via `CreativeAgent`, strategy via
    `MarketingAgent`) only fire when the corresponding state flag is set,
    so their model names are recorded here for the manifest but never
    invoked on the default (smoke) path. Override per-call by constructing
    a new frozen instance — never mutate.
    """

    output_dir: Path = field(default_factory=lambda: Path(OUTPUT_DIR) / "ventures" / "social")
    default_platforms: tuple[str, ...] = ("instagram", "tiktok", "twitter")
    default_content_type: str = "product_launch"
    graphics_model: str = "gemini-3-pro-image-preview"
    strategist_model: str = "claude-sonnet-4"
    smoke_sku: str = "br-001"
    smoke_timeout_seconds: float = 5.0


DEFAULT_CONFIG = SocialVentureConfig()
