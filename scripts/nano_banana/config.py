"""Pipeline configuration — exportable JSON for dashboard embedding.

All pipeline settings in one place. Serializable to JSON so the
dashboard image team can consume and modify settings.

Usage:
    from nano_banana.config import PipelineConfig
    cfg = PipelineConfig.production()
    cfg.to_json(Path("data/pipeline-config.json"))
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

from llm.model_ids import (
    NANO_BANANA_2_MODEL,
    NANO_BANANA_MODEL,
    NANO_BANANA_PRO_MODEL,
    OPENAI_IMAGE_2_MODEL,
    OPENAI_IMAGE_15_MODEL,
    OPENAI_IMAGE_MINI_MODEL,
    OPENAI_VISION_MODEL,
)

log = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Complete pipeline configuration."""

    # -- Model IDs --
    gemini_pro_model: str = NANO_BANANA_PRO_MODEL
    gemini_flash_model: str = NANO_BANANA_MODEL
    # Nano Banana 2 — gemini-3.1-flash-image-preview, the new flash variant
    # with thinking-mode. Distinct from gemini_flash_model (the original NB)
    # so callers and the dashboard can pick between generations explicitly.
    nano_banana_2_model: str = NANO_BANANA_2_MODEL
    gemini_vision_model: str = "gemini-2.5-flash"
    gpt_image_model: str = OPENAI_IMAGE_15_MODEL
    # OpenAI's cheap mini variant of gpt-image-1 — exposed for cost-tier
    # workflows. The dashboard can route low-priority generation here when
    # prefer_cost_efficiency is set.
    gpt_image_mini_model: str = OPENAI_IMAGE_MINI_MODEL
    flux_pro_model: str = "fal-ai/flux-pro/v1.1"
    flux_kontext_model: str = "fal-ai/flux-pro/kontext"

    # -- QA Judge models --
    gpt_judge_model: str = OPENAI_VISION_MODEL
    claude_judge_model: str = "claude-opus-4-6"
    gemini_judge_model: str = "gemini-2.5-flash"

    # -- QA Thresholds --
    qa_auto_approve: float = 80.0
    qa_auto_reject: float = 50.0
    qa_refine_text_threshold: float = 70.0
    qa_refine_logo_threshold: float = 70.0

    # -- Generation settings --
    max_attempts: int = 3
    retry_delay_seconds: float = 3.0
    aspect_ratio: str = "3:4"
    output_format: str = "webp"
    output_quality: int = 90

    # -- Routing --
    prefer_cost_efficiency: bool = False

    # -- Rate limits (requests per minute) --
    gemini_rpm: int = 10
    openai_rpm: int = 7
    fal_rpm: int = 10

    # -- Output directories (relative to project root) --
    output_dir: str = "wordpress-theme/skyyrose-flagship/assets/images/products"
    vision_cache_dir: str = "data/product-vision"
    qa_results_dir: str = "data/verify-results"

    # -- Views to generate --
    default_views: list = field(default_factory=lambda: ["front", "back", "branding"])

    def to_dict(self) -> dict:
        """Export as plain dict."""
        return asdict(self)

    def to_json(self, path: Path | None = None) -> str:
        """Export as formatted JSON string. Optionally save to file."""
        data = self.to_dict()
        text = json.dumps(data, indent=2, sort_keys=False)
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
            log.info("Config saved to %s", path)
        return text

    @classmethod
    def from_dict(cls, d: dict) -> PipelineConfig:
        """Create config from dict, ignoring unknown keys."""
        valid = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in valid}
        return cls(**filtered)

    @classmethod
    def from_json(cls, path: Path) -> PipelineConfig:
        """Load config from JSON file."""
        data = json.loads(path.read_text())
        return cls.from_dict(data)

    @classmethod
    def production(cls) -> PipelineConfig:
        """Production preset — maximum quality, full QA."""
        return cls(
            max_attempts=3,
            qa_auto_approve=80.0,
            qa_auto_reject=50.0,
            prefer_cost_efficiency=False,
        )

    @classmethod
    def fast(cls) -> PipelineConfig:
        """Fast preset — speed and cost efficiency."""
        # Override the pro slot with the operator's current best image model
        # for the job. Field is named gemini_pro_model for legacy reasons but
        # the dashboard treats it as the provider-agnostic "pro tier" value;
        # consumers do not dispatch APIs based on the field name.
        return cls(
            gemini_pro_model=OPENAI_IMAGE_2_MODEL,
            max_attempts=1,
            retry_delay_seconds=1.0,
            qa_auto_approve=65.0,
            qa_auto_reject=40.0,
            prefer_cost_efficiency=True,
        )
