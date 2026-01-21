# services/ml/prompts/__init__.py
"""ML prompts package."""

from services.ml.prompts.vision_prompts import (
    BULLET_POINTS_PROMPT,
    DESCRIPTION_PROMPTS,
    FEATURE_EXTRACTION_PROMPT,
    SEO_PROMPT,
    TAGS_PROMPT,
    get_description_prompt,
    get_feature_prompt,
)

__all__ = [
    "BULLET_POINTS_PROMPT",
    "DESCRIPTION_PROMPTS",
    "FEATURE_EXTRACTION_PROMPT",
    "SEO_PROMPT",
    "TAGS_PROMPT",
    "get_description_prompt",
    "get_feature_prompt",
]
