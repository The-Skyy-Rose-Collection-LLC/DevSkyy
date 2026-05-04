"""
QualityAgent — Phase 16 Legendary QA Architect.

Promoted to ADK SuperAgent for comprehensive "Back Data" (telemetry) and
high-fidelity dual-agent QA consensus.

Inherits from BaseSuperAgent to leverage standardized enterprise tools
and observability via Google ADK.
"""

from __future__ import annotations

import asyncio
import base64
import logging
from pathlib import Path
from typing import Any, Literal

from adk.base import ADKProvider, AgentConfig, AgentResult
from adk.super_agents import BaseSuperAgent

from ..config import COMPOSITOR_QA_MODEL, GEMINI_VISION_MODEL, QC_CLAUDE_MODEL
from ..gemini_rest import analyze_vision as gemini_analyze_vision
from ..models import QualityVerification

logger = logging.getLogger(__name__)

# Model IDs are imported from config (single source of truth) to prevent the
# Phase 16 model-drift class of bugs. Do NOT add hardcoded model strings here.
_PASS_THRESHOLD = 80

_SCENE_QA_PROMPT = """You are QA-scoring a SCENE COMPOSITE render for SkyyRose luxury fashion.

Expected spec:
{spec}

Score on a 0-100 scale across three dimensions:
1. Lighting consistency (35%): Does the subject's lighting (direction, color
   temperature, intensity) match the scene's? Score 0 and flag IDENTITY_MISMATCH
   if the subject looks pasted-on with no lighting integration.
2. Edge integration (30%): Are subject edges naturally blended? No halo, no
   hard cutout artifacts, no chromatic fringing where subject meets scene.
3. Contact shadow presence (35%): Is there a believable contact shadow
   anchoring the subject to the scene? Score 0 if the subject appears to
   float in space.

Reply in this exact format:
IDENTITY_SCORE: <0-100>
IDENTITY_MISMATCH: <YES/NO>
LIGHTING_SCORE: <0-100>
EDGE_SCORE: <0-100>
SHADOW_SCORE: <0-100>
OVERALL: <weighted average>
NOTES: <one sentence>
"""

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


class QualityAgent(BaseSuperAgent):
    """Dual-agent QA gate promoted to ADK SuperAgent."""

    def __init__(self, config: AgentConfig | None = None) -> None:
        if config is None:
            config = AgentConfig(
                name="legendary_qa_architect",
                provider=ADKProvider.GOOGLE,
                model=GEMINI_VISION_MODEL,
                system_prompt="You are the Legendary QA Architect for SkyyRose. Your mission is absolute visual perfection.",
            )
        super().__init__(config)

    async def verify(
        self,
        image_path: str,
        expected_spec: str,
        style: str = "flat_lay",
        *,
        mode: Literal["flat_lay", "scene_composite"] = "flat_lay",
    ) -> QualityVerification:
        """Run the dual-judge consensus QA gate.

        The two scorers (Claude vision + Gemini vision) run in parallel via
        ``asyncio.gather`` so wall-clock latency is the slower of the two,
        not the sum. Each scorer is wrapped with its own try/except so a
        provider outage degrades to a single-judge verdict instead of
        crashing the whole pipeline. Pass requires ``min(score_a, score_b) >=
        80`` AND no identity-mismatch flag from either judge.

        Args:
            image_path: render to verify.
            expected_spec: textual contract the render must satisfy.
            style: legacy parameter; kept for backward compatibility.
            mode: ``flat_lay`` for B1 ghost-mannequin renders (the original
                contract), ``scene_composite`` for B2 outputs where lighting
                consistency, contact-shadow presence, and edge-blend artifacts
                matter more than pure ghost-mannequin fidelity.
        """
        # Trigger ADK for observability
        adk_prompt = f"QA TASK: Image={image_path}, Spec={expected_spec}, Mode={mode}"
        logger.info("Running Legendary QA for %s via ADK (mode=%s)...", image_path, mode)
        adk_result = await self.execute(adk_prompt)

        rubric = _SCENE_QA_PROMPT if mode == "scene_composite" else _GHOST_QA_PROMPT
        prompt = rubric.format(spec=expected_spec)

        # Run both scorers in parallel — return_exceptions=True so a failure
        # in one judge doesn't sink the other's verdict.
        score_a_task = self._score_claude(image_path, prompt)
        score_b_task = self._score_gemini(image_path, prompt)
        result_a, result_b = await asyncio.gather(
            score_a_task, score_b_task, return_exceptions=True
        )

        if isinstance(result_a, BaseException):
            score_a, mismatch_a, notes_a = 0, False, f"Claude QA failed: {result_a}"
            logger.warning("Claude QA failed for %s: %s", image_path, result_a)
        else:
            score_a, mismatch_a, notes_a = result_a

        if isinstance(result_b, BaseException):
            score_b, mismatch_b, notes_b = 0, False, f"Gemini QA failed: {result_b}"
            logger.warning("Gemini QA failed for %s: %s", image_path, result_b)
        else:
            score_b, mismatch_b, notes_b = result_b

        identity_mismatch = mismatch_a or mismatch_b
        min_score = min(score_a, score_b)

        details: dict[str, Any] = {
            "score_claude": score_a,
            "score_gemini": score_b,
            "min_score": min_score,
            "notes_claude": notes_a,
            "notes_gemini": notes_b,
            "mode": mode,
        }

        # Check if adk_result is an AgentResult object
        metadata = {}
        if isinstance(adk_result, AgentResult):
            metadata = {
                "status": adk_result.status,
                "agent": adk_result.agent_name,
                "started_at": str(adk_result.started_at),
            }

        if identity_mismatch:
            details["reject_reason"] = "identity mismatch flagged by vision model"
            return QualityVerification(
                success=True,
                provider="dual_vision",
                model=f"{QC_CLAUDE_MODEL}+{COMPOSITOR_QA_MODEL}",
                overall_status="fail",
                recommendation="regenerate",
                details=details,
                metadata=metadata,
            )

        passed = min_score >= _PASS_THRESHOLD
        return QualityVerification(
            success=True,
            provider="dual_vision",
            model=f"{QC_CLAUDE_MODEL}+{COMPOSITOR_QA_MODEL}",
            overall_status="pass" if passed else "fail",
            recommendation="approve" if passed else "regenerate",
            details=details,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Private — each returns (score: int, identity_mismatch: bool, notes: str)
    # ------------------------------------------------------------------

    async def _score_claude(self, image_path: str, prompt: str) -> tuple[int, bool, str]:
        from ..config import get_anthropic_client

        client = get_anthropic_client()
        ext = Path(image_path).suffix.lower().lstrip(".")
        media_type = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
        with open(image_path, "rb") as f:
            b64 = base64.standard_b64encode(f.read()).decode("utf-8")

        # Anthropic SDK's messages.create() is a synchronous network call —
        # wrap it in to_thread so it doesn't block the event loop while the
        # parallel Gemini scorer runs.
        # Anthropic's SDK declares strict TypedDicts for content blocks. The
        # plain-dict shape below is the documented and runtime-accepted form;
        # pyright's strict check rejects it. Cast through Any at the boundary.
        messages: Any = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": b64},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        msg = await asyncio.to_thread(
            client.messages.create,
            model=QC_CLAUDE_MODEL,
            max_tokens=256,
            messages=messages,
        )
        return _parse_qa_response(msg.content[0].text)

    async def _score_gemini(self, image_path: str, prompt: str) -> tuple[int, bool, str]:
        ext = Path(image_path).suffix.lower().lstrip(".")
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
        with open(image_path, "rb") as f:
            b64 = base64.standard_b64encode(f.read()).decode("utf-8")

        # gemini_rest.analyze_vision is sync — same to_thread treatment.
        result = await asyncio.to_thread(
            gemini_analyze_vision,
            model=COMPOSITOR_QA_MODEL,
            prompt=prompt,
            image_b64=b64,
            mime_type=mime,
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
