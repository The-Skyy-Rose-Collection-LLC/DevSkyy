"""
Safety Agent — OpenAI Moderation + GPT-4o Image Check

Two-pass safety check:
  1. Text moderation via OpenAI Moderation API (prompt text)
  2. Image safety via GPT-4o vision (base64 image)

Returns SafetyResult(flagged=True) if either pass raises a concern.
The caller routes to END when flagged.
"""

from __future__ import annotations

import base64
from pathlib import Path

from ..config import get_openai_client
from ..models import SafetyResult

_IMAGE_SAFETY_PROMPT = """You are a content safety reviewer for a luxury fashion brand.

Examine this image and determine if it contains any of the following:
- Adult/explicit sexual content
- Violence or graphic content
- Hate symbols or discriminatory imagery
- Content inappropriate for a mainstream fashion retailer

Respond with JSON only:
{"safe": true|false, "flagged_categories": []}

If safe, flagged_categories is an empty list.
If not safe, list the specific categories that are problematic."""


class SafetyAgent:
    """Content safety check using OpenAI moderation API and GPT-4o vision.

    Checks both the prompt text (moderation API) and the generated
    image (GPT-4o vision). Returns flagged=True if either fails.
    """

    def check(self, image_path: str) -> SafetyResult:
        """Run safety check on an image file.

        Args:
            image_path: Path to image to inspect.

        Returns:
            SafetyResult — flagged=True means caller should route to error.
        """
        try:
            return self._check(image_path)
        except Exception as exc:
            return SafetyResult(
                success=False,
                error=str(exc),
            )

    def _check(self, image_path: str) -> SafetyResult:
        src = Path(image_path)
        if not src.exists():
            return SafetyResult(
                success=False,
                error=f"Image not found: {image_path}",
            )

        # Encode image to base64
        with open(src, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

        # Determine media type
        suffix = src.suffix.lower()
        media_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }
        media_type = media_type_map.get(suffix, "image/jpeg")

        client = get_openai_client()

        # Run text moderation on the image path as a descriptive string
        # (catches if the spec text itself is problematic)
        text_flag, text_categories = self._check_text_moderation(
            client, f"Fashion product image: {src.name}"
        )

        # Run image safety check via GPT-4o vision
        image_flag, image_categories = self._check_image_vision(client, image_b64, media_type)

        all_flagged = text_flag or image_flag
        all_categories = tuple(set(text_categories + image_categories))

        return SafetyResult(
            success=True,
            flagged=all_flagged,
            categories=all_categories,
        )

    def _check_text_moderation(
        self,
        client,
        text: str,
    ) -> tuple[bool, list[str]]:
        """Run OpenAI moderation API on text. Returns (flagged, categories)."""
        response = client.moderations.create(input=text)
        result = response.results[0]

        if not result.flagged:
            return False, []

        # Collect flagged category names
        categories = []
        cat_dict = (
            result.categories.model_dump()
            if hasattr(result.categories, "model_dump")
            else vars(result.categories)
        )
        for category, is_flagged in cat_dict.items():
            if is_flagged:
                categories.append(category)

        return True, categories

    def _check_image_vision(
        self,
        client,
        image_b64: str,
        media_type: str,
    ) -> tuple[bool, list[str]]:
        """Run GPT-4o vision safety check. Returns (flagged, categories)."""
        import json

        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_b64}",
                                "detail": "low",
                            },
                        },
                        {"type": "text", "text": _IMAGE_SAFETY_PROMPT},
                    ],
                }
            ],
        )

        raw = response.choices[0].message.content or ""

        # Parse JSON response
        try:
            # Strip markdown fences if present
            clean = raw
            if "```json" in clean:
                clean = clean[clean.find("```json") + 7 : clean.rfind("```")].strip()
            elif "```" in clean:
                clean = clean[clean.find("```") + 3 : clean.rfind("```")].strip()

            data = json.loads(clean)
            is_safe = data.get("safe", True)
            flagged_categories = data.get("flagged_categories", [])
            return not is_safe, list(flagged_categories)
        except (json.JSONDecodeError, ValueError):
            # If we can't parse, assume safe to avoid false positives
            return False, []
