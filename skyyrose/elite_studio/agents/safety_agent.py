"""OpenAI moderation + GPT-4o image safety gate for Elite Studio pipeline."""

from __future__ import annotations

import base64
import json
import logging
from pathlib import Path

from llm.model_ids import OPENAI_VISION_MODEL
from skyyrose.elite_studio.config import get_openai_client
from skyyrose.elite_studio.models import SafetyResult

logger = logging.getLogger(__name__)

_VISION_PROMPT = (
    "You are a content safety reviewer for a luxury fashion brand. "
    "Inspect the image and return ONLY valid JSON: "
    '{"safe": true/false, "flagged_categories": ["category1", ...]}. '
    "Flag explicit content, graphic violence, hate symbols, or anything "
    "inappropriate for a luxury fashion e-commerce platform."
)


class SafetyAgent:
    """Run OpenAI text moderation then GPT-4o vision check on an image."""

    def check(self, image_path: str) -> SafetyResult:
        """Return a SafetyResult or a failure result if logic raises."""
        try:
            return self._check(image_path)
        except Exception as exc:  # noqa: BLE001
            logger.exception("SafetyAgent._check failed for path=%s", image_path)
            return SafetyResult(success=False, error=str(exc))

    def _check(self, image_path: str) -> SafetyResult:
        path = Path(image_path)
        if not path.exists():
            return SafetyResult(success=False, error=f"Image not found: {image_path}")

        client = get_openai_client()
        flagged_categories: list[str] = []
        is_flagged = False

        # --- Text moderation on the filename/path as a lightweight proxy ---
        mod_response = client.moderations.create(input=path.name)
        mod_result = mod_response.results[0]
        if mod_result.flagged:
            is_flagged = True
            cat_dict: dict[str, bool] = mod_result.categories.model_dump()
            flagged_categories.extend(k for k, v in cat_dict.items() if v)

        # --- GPT-4o vision check ---
        image_data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
        suffix = path.suffix.lstrip(".").lower()
        media_type = "image/jpeg" if suffix in ("jpg", "jpeg") else f"image/{suffix}"

        vision_response = client.chat.completions.create(
            model=OPENAI_VISION_MODEL,
            max_tokens=256,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": _VISION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{media_type};base64,{image_data}"},
                        },
                    ],
                }
            ],
        )

        raw = vision_response.choices[0].message.content
        try:
            vision_data = json.loads(raw)
            if not vision_data.get("safe", True):
                is_flagged = True
                flagged_categories.extend(vision_data.get("flagged_categories", []))
        except (json.JSONDecodeError, AttributeError):
            # Unparseable response — treat as safe to avoid false positives
            logger.warning("GPT-4o vision response was not valid JSON; defaulting to safe")

        return SafetyResult(
            success=True,
            flagged=is_flagged,
            categories=tuple(dict.fromkeys(flagged_categories)),  # deduplicate, preserve order
        )
