"""QualityAgent — Phase B2 dual-agent QA consensus.

Agent A: Claude Opus 4.6 (Anthropic SDK)
Agent B: Gemini 2.0 Flash (gemini_rest.py)
Mode:    Consensus — min(score_A, score_B) ≥ 80 to pass.
         Either model flagging product identity mismatch = auto-reject.

Ghost-mannequin rubric:
  - Product identity: correct garment type (0–100, plus mismatch flag)
  - Ghost-mannequin fidelity: no mannequin visible, correct 3D volume (0–100)
  - Branding placement: logos/text match spec (0–100)
  Overall = weighted average of three dimensions.
"""
from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any

import anthropic

from ..gemini_rest import analyze_vision as gemini_analyze_vision
from ..models import QualityVerification

logger = logging.getLogger(__name__)

_CLAUDE_MODEL = "claude-opus-4-6"
_GEMINI_VISION_MODEL = "gemini-2.0-flash-001"
_PASS_THRESHOLD = 80

_GHOST_QA_PROMPT = """You are QA-scoring a ghost-mannequin fashion product render for SkyyRose brand.

Expected spec:
{spec}

Score on a 0-100 scale across three dimensions:
1. Product identity (30%): Is this the EXACT correct garment type described in the spec?
   If the spec says "hockey jersey" and the image shows a baseball jersey, score 0 and flag IDENTITY_MISMATCH.
2. Ghost-mannequin fidelity (40%): Is there NO mannequin visible? Does the garment have correct 3D volume/drape?
   Is the neck-in (collar interior) visible for appropriate garment types?
3. Branding placement (30%): Are logos/text in the correct positions per the spec?

Reply in this exact format:
IDENTITY_SCORE: <0-100>
IDENTITY_MISMATCH: <YES/NO>
FIDELITY_SCORE: <0-100>
BRANDING_SCORE: <0-100>
OVERALL: <weighted average>
NOTES: <one sentence>
"""


class QualityAgent:
    """Dual-agent QA gate for generated imagery."""

    def __init__(self) -> None:
        self._claude = anthropic.Anthropic()

    def verify(
        self,
        image_path: str,
        expected_spec: str,
        style: str = "flat_lay",
    ) -> QualityVerification:
        prompt = _GHOST_QA_PROMPT.format(spec=expected_spec)

        try:
            score_a, mismatch_a, notes_a = self._score_claude(image_path, prompt)
        except Exception as exc:
            score_a, mismatch_a, notes_a = 0, False, f"Claude QA failed: {exc}"
            logger.warning("Claude QA failed for %s: %s", image_path, exc)

        try:
            score_b, mismatch_b, notes_b = self._score_gemini(image_path, prompt)
        except Exception as exc:
            score_b, mismatch_b, notes_b = 0, False, f"Gemini QA failed: {exc}"
            logger.warning("Gemini QA failed for %s: %s", image_path, exc)

        identity_mismatch = mismatch_a or mismatch_b
        min_score = min(score_a, score_b)

        details: dict[str, Any] = {
            "score_claude": score_a,
            "score_gemini": score_b,
            "min_score": min_score,
            "notes_claude": notes_a,
            "notes_gemini": notes_b,
        }

        if identity_mismatch:
            details["reject_reason"] = "identity mismatch flagged by vision model"
            return QualityVerification(
                success=True,
                provider="dual_vision",
                model=f"{_CLAUDE_MODEL}+{_GEMINI_VISION_MODEL}",
                overall_status="fail",
                recommendation="regenerate",
                details=details,
            )

        passed = min_score >= _PASS_THRESHOLD
        return QualityVerification(
            success=True,
            provider="dual_vision",
            model=f"{_CLAUDE_MODEL}+{_GEMINI_VISION_MODEL}",
            overall_status="pass" if passed else "fail",
            recommendation="approve" if passed else "regenerate",
            details=details,
        )

    # ------------------------------------------------------------------
    # Private — patchable in tests; each returns (score: int, identity_mismatch: bool, notes: str)
    # ------------------------------------------------------------------

    def _score_claude(self, image_path: str, prompt: str) -> tuple[int, bool, str]:
        ext = Path(image_path).suffix.lower().lstrip(".")
        media_type = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
        with open(image_path, "rb") as f:
            b64 = base64.standard_b64encode(f.read()).decode("utf-8")
        msg = self._claude.messages.create(
            model=_CLAUDE_MODEL,
            max_tokens=256,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                    {"type": "text", "text": prompt},
                ],
            }],
        )
        return _parse_qa_response(msg.content[0].text)

    def _score_gemini(self, image_path: str, prompt: str) -> tuple[int, bool, str]:
        ext = Path(image_path).suffix.lower().lstrip(".")
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
        with open(image_path, "rb") as f:
            b64 = base64.standard_b64encode(f.read()).decode("utf-8")
        result = gemini_analyze_vision(
            model=_GEMINI_VISION_MODEL, prompt=prompt, image_b64=b64, mime_type=mime
        )
        if not result.get("success"):
            raise RuntimeError(result.get("error", "Gemini QA failed"))
        return _parse_qa_response(result["text"])


def _parse_qa_response(text: str) -> tuple[int, bool, str]:
    """Parse the structured QA response into (overall_score, identity_mismatch, notes)."""
    lines = {
        line.split(":")[0].strip(): line.split(":", 1)[1].strip()
        for line in text.splitlines()
        if ":" in line
    }
    try:
        overall_str = lines.get("OVERALL", lines.get("IDENTITY_SCORE", "50"))
        # Handle cases where score might have % or other chars
        overall_val = "".join(c for c in overall_str if c.isdigit() or c == ".")
        overall = int(float(overall_val)) if overall_val else 50
    except (ValueError, TypeError):
        overall = 50
    mismatch = lines.get("IDENTITY_MISMATCH", "NO").strip().upper() == "YES"
    notes = lines.get("NOTES", "")
    return overall, mismatch, notes
