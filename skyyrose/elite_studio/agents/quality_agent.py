"""
Quality Agent — Claude Sonnet Verification

Verifies generated images match product specifications.
Returns pass/warn/fail status with detailed assessment.
"""

from __future__ import annotations

import json
from typing import Any

from ..config import QC_MODEL, get_anthropic_client
from ..models import QualityVerification
from ..retry import retry_on_transient
from ..utils import resize_for_claude


class QualityAgent:
    """Quality control agent using Claude Sonnet vision.

    Compares generated images against product specifications
    and returns structured pass/warn/fail assessment.
    """

    def verify(
        self,
        image_path: str,
        expected_spec: str,
    ) -> QualityVerification:
        """Verify generated image quality and accuracy.

        Args:
            image_path: Path to generated image
            expected_spec: What the image should contain

        Returns:
            QualityVerification with status and details.
        """
        prompt = self._build_qc_prompt(expected_spec)

        try:
            def _call():
                image_b64 = resize_for_claude(image_path)
                client = get_anthropic_client()
                response = client.messages.create(
                    model=QC_MODEL,
                    max_tokens=1500,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/jpeg",
                                        "data": image_b64,
                                    },
                                },
                                {"type": "text", "text": prompt},
                            ],
                        }
                    ],
                )
                return response.content[0].text

            raw_text = retry_on_transient(_call, label="[QC]")
            return self._parse_response(raw_text)

        except Exception as exc:
            return QualityVerification(
                success=False,
                provider="anthropic",
                model=QC_MODEL,
                error=str(exc),
            )

    def _build_qc_prompt(self, expected_spec: str) -> str:
        """Build quality control prompt."""
        return f"""Quality Control: Verify this AI-generated fashion photo.

EXPECTED SPECIFICATIONS:
{expected_spec}

Inspect the image and return JSON:
{{
  "overall_status": "pass|warn|fail",
  "logo_accuracy": {{"status": "pass|warn|fail", "notes": "..."}},
  "garment_accuracy": {{"status": "pass|warn|fail", "notes": "..."}},
  "photo_quality": {{"status": "pass|warn|fail", "notes": "..."}},
  "recommendation": "approve|regenerate|manual_review"
}}"""

    def _parse_response(self, text: str) -> QualityVerification:
        """Parse Claude's QC response into structured result."""
        json_text = text
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            json_text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            json_text = text[start:end].strip()

        try:
            data: dict[str, Any] = json.loads(json_text)
        except (json.JSONDecodeError, ValueError):
            return QualityVerification(
                success=True,
                provider="anthropic",
                model=QC_MODEL,
                overall_status="unknown",
                recommendation="manual_review",
                details={"raw_text": text, "parsed": False},
            )

        return QualityVerification(
            success=True,
            provider="anthropic",
            model=QC_MODEL,
            overall_status=data.get("overall_status", "unknown"),
            recommendation=data.get("recommendation", "manual_review"),
            details=data,
        )
