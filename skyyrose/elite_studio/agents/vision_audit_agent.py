"""VisionAuditAgent — H4 post-render fidelity gate.

After the RAS pipeline produces a render, this agent re-reads the dossier's
NEGATIVE block and asks Gemini Flash Vision: *"does this rendered image
contain anything from the negative list?"* If yes, the pipeline rejects the
render and either auto-retries (up to 2x) or quarantines the output.

Cost: ~$0.005 per audit using ``gemini-3-flash-preview`` — negligible vs the
cost of a wrong render reaching production. The audit is the difference
between trusting Gemini's text-following on a single pass vs. verifying
the output independently.

Returns a structured ``VisionAuditResult`` with:
  - ``matches_dossier``: bool (False = render rejected)
  - ``violations``: list of {element, region, severity}
  - ``raw_text``: the model's full reply (for the forensic manifest)
"""

from __future__ import annotations

import base64
import json
import logging
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from ..config import GEMINI_VISION_MODEL
from ..gemini_rest import analyze_vision as gemini_analyze_vision

logger = logging.getLogger(__name__)


@dataclass
class VisionAuditViolation:
    element: str
    region: str
    severity: Literal["low", "medium", "high"]

    @property
    def is_blocking(self) -> bool:
        return self.severity in ("medium", "high")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class VisionAuditResult:
    matches_dossier: bool
    violations: list[VisionAuditViolation] = field(default_factory=list)
    raw_text: str = ""
    model: str = ""
    error: str = ""

    @property
    def has_blocking_violations(self) -> bool:
        """True if any violation is medium or high severity.

        Low-severity violations are the auditor's "uncertain" tier and
        commonly false-positive on universal positive elements (e.g. the
        woven brand size tag, which every product carries per the
        dossier system's universal rule). Treat them as warnings, not
        gate-failures.
        """
        return any(v.is_blocking for v in self.violations)

    @property
    def ok(self) -> bool:
        if self.error:
            return False
        if self.matches_dossier:
            return True
        return not self.has_blocking_violations

    def to_dict(self) -> dict:
        return {
            "matches_dossier": self.matches_dossier,
            "violations": [v.to_dict() for v in self.violations],
            "raw_text": self.raw_text,
            "model": self.model,
            "error": self.error,
        }


def _build_audit_prompt(dossier: dict, view: str = "front") -> str:
    full_branding = dossier.get("branding_block", "")
    # Filter the branding block to only the entries visible in this view so
    # back renders are not failed for missing front-only decorations.
    # Lazy import breaks the circular: synthesis.__init__ → flux_pipeline → vision_audit_agent.
    try:
        from ..synthesis.stages.mask_deriver import parse_branding_entries  # noqa: PLC0415

        all_entries = parse_branding_entries(full_branding)
        view_entries = [e for e in all_entries if e.matches_view(view)]
        if view_entries:
            branding_block = "\n".join(
                f"- {e.region} ({e.technique}): {e.description}" for e in view_entries
            )
        else:
            branding_block = full_branding
    except ImportError:
        branding_block = full_branding
    except Exception:
        logger.warning("branding filter failed for view=%s; using full block", view, exc_info=True)
        branding_block = full_branding

    return (
        f"You are an independent fidelity auditor for SkyyRose product renders. "
        f"You are inspecting a generated image of: {dossier.get('name', '<unknown>')} "
        f"({view.upper()} VIEW).\n\n"
        f"GARMENT LOCK (the garment IS this and ONLY this):\n"
        f"{dossier.get('garment_type_lock', '')}\n\n"
        f"BRANDING — exactly what SHOULD appear on this product's {view.upper()} view:\n"
        f"{branding_block}\n\n"
        f"NEGATIVE — what MUST NOT appear on this product:\n"
        f"{dossier.get('negative_block', '')}\n\n"
        f"INSPECT the attached rendered image. Identify ANY element that:\n"
        f"  (a) appears in the NEGATIVE list, or\n"
        f"  (b) appears in the render but is not authorized by the {view.upper()} VIEW BRANDING list, or\n"
        f"  (c) contradicts the GARMENT LOCK (wrong garment type).\n\n"
        f"IMPORTANT: This is a {view.upper()} VIEW render. Do NOT flag missing elements "
        f"that belong to other views (e.g. back-view branding on a front-view render).\n\n"
        f"Reply with VALID JSON, no prose, no code fences:\n"
        f'{{"matches_dossier": <bool>, "violations": '
        f'[{{"element": "<short description>", "region": "<exact-region-key>", '
        f'"severity": "<low|medium|high>"}}, ...]}}\n\n'
        f"SCHEMA RULES:\n"
        f"- Use the exact region key from the BRANDING list above (e.g. 'front-center-chest', not 'chest').\n"
        f"- Each violation entry must name exactly ONE region. "
        f"For symmetric violations (e.g. both cuffs wrong), emit one entry per region.\n\n"
        f"If the render is clean and matches the dossier, return "
        f'{{"matches_dossier": true, "violations": []}}.'
    )


def _extract_json(text: str) -> dict | None:
    """Extract the first JSON object from possibly-wrapped model output."""
    if not text:
        return None
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    obj_match = re.search(r"\{.*\}", text, re.DOTALL)
    if not obj_match:
        return None
    try:
        return json.loads(obj_match.group(0))
    except json.JSONDecodeError:
        return None


class VisionAuditAgent:
    """Independent post-render fidelity verifier.

    Use:
        agent = VisionAuditAgent()
        result = agent.audit(rendered_image_path, dossier)
        if not result.ok:
            for v in result.violations:
                logger.warning(f"violation: {v.element} on {v.region} ({v.severity})")
    """

    def __init__(self, model: str | None = None) -> None:
        self.model = model or GEMINI_VISION_MODEL

    def audit(
        self, image_path: str | Path, dossier: dict, view: str = "front"
    ) -> VisionAuditResult:
        path = Path(image_path)
        if not path.is_file():
            return VisionAuditResult(
                matches_dossier=False,
                error=f"render not found at {path}",
                model=self.model,
            )

        ext = path.suffix.lower().lstrip(".")
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
        raw_bytes = path.read_bytes()
        b64 = base64.standard_b64encode(raw_bytes).decode("utf-8")
        del raw_bytes
        prompt = _build_audit_prompt(dossier, view)

        try:
            response = gemini_analyze_vision(
                model=self.model, prompt=prompt, image_b64=b64, mime_type=mime
            )
        except Exception as exc:
            logger.exception("vision audit call failed")
            return VisionAuditResult(
                matches_dossier=False,
                error=f"audit call failed: {exc}",
                model=self.model,
            )

        if not response.get("success"):
            return VisionAuditResult(
                matches_dossier=False,
                error=response.get("error", "audit returned no success flag"),
                raw_text=str(response.get("text", "")),
                model=self.model,
            )

        raw = response.get("text", "")
        parsed = _extract_json(raw)
        if not parsed:
            # Fail closed — if we cannot parse the auditor's reply, treat as a
            # rejection. Better to quarantine and re-render than ship an
            # un-audited image.
            return VisionAuditResult(
                matches_dossier=False,
                error="could not parse audit JSON reply",
                raw_text=raw,
                model=self.model,
            )

        violations = [
            VisionAuditViolation(
                element=str(v.get("element", "")),
                region=str(v.get("region", "")),
                severity=str(v.get("severity", "")).lower(),
            )
            for v in parsed.get("violations", [])
            if isinstance(v, dict)
        ]
        return VisionAuditResult(
            matches_dossier=bool(parsed.get("matches_dossier", False)),
            violations=violations,
            raw_text=raw,
            model=self.model,
        )


__all__ = [
    "VisionAuditAgent",
    "VisionAuditResult",
    "VisionAuditViolation",
]
