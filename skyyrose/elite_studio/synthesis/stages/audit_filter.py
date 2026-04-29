"""Stage 1.5 — Audit filter for Path B (Audit-Driven Targeted Masking).

After FLUX Kontext produces a candidate render (Stage 1), this module checks
it against the dossier before any FLUX Fill budget is spent.

VisionAuditAgent already implements the full H4 gate (gemini-3-flash-preview,
JSON-structured reply, fail-closed on parse error).  AuditFilter is a thin
adapter that extracts blocking violation regions so they can feed
MaskDeriver.derive(allowed_regions=...) in Stage 3.

Decision tree:
  - audit.ok is True  → AuditResult(passed=True, violation_regions=[])
    Stage 1 is clean; no FLUX Fill budget spent.
  - audit.ok is False → AuditResult(passed=False, violation_regions=[...])
    Stage 3 inpaints only the violated regions, leaving clean areas untouched.
  - audit.error != "" → raises AuditError (fail-loud; infrastructure failure
    must not silently bypass the gate).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from ...agents.vision_audit_agent import VisionAuditAgent, VisionAuditResult

logger = logging.getLogger(__name__)


class AuditError(Exception):
    """Raised when the audit call itself fails (infrastructure, not a violation)."""


@dataclass(frozen=True)
class AuditResult:
    passed: bool
    violation_regions: list[str] = field(default_factory=list)

    @property
    def needs_inpaint(self) -> bool:
        return not self.passed and bool(self.violation_regions)


def _blocking_regions(audit: VisionAuditResult) -> list[str]:
    """Return unique region names for medium/high-severity violations only.

    Low-severity is the auditor's "uncertain" tier and frequently
    false-positives on universal elements (e.g. woven size label).
    Feeding those to the mask would inpaint correct areas needlessly.

    Gemini is instructed (via _build_audit_prompt SCHEMA RULES) to emit one
    entry per region. The split below is a defensive fallback for non-compliant
    responses — do not remove.
    """
    seen: set[str] = set()
    regions: list[str] = []
    for v in audit.violations:
        if not v.is_blocking:
            continue
        parts = v.region.split(",")
        if len(parts) > 1:
            logger.warning(
                "audit returned compound region %r — model ignored SCHEMA RULES; splitting defensively",
                v.region,
            )
        for part in parts:
            region = part.strip()
            if region and region not in seen:
                seen.add(region)
                regions.append(region)
    return regions


class AuditFilter:
    """Stage 1.5 adapter between VisionAuditAgent and MaskDeriver.

    Usage::

        af = AuditFilter()
        result = af.check(stage1_output_path, dossier, view="front")

        if result.passed:
            return stage1_output_path          # accept — no FLUX Fill needed

        mask = MaskDeriver().derive(
            image_path=stage1_output_path,
            dossier=dossier,
            view=view,
            out_dir=out_dir,
            allowed_regions=result.violation_regions,
        )
        # proceed to Stage 3 FLUX Fill with surgical mask
    """

    def __init__(self, model: str | None = None) -> None:
        self._agent = VisionAuditAgent(model=model)

    def check(
        self,
        image_path: str | Path,
        dossier: dict,
        view: str = "front",
    ) -> AuditResult:
        """Audit a Stage 1 render against the dossier.

        Returns AuditResult with passed=True (accept render) or
        passed=False + violation_regions (proceed to Stage 3).
        Raises AuditError on infrastructure failure.
        """
        audit = self._agent.audit(image_path, dossier, view=view)

        if audit.error:
            raise AuditError(
                f"audit infrastructure failed for {image_path}: {audit.error}. "
                "Stage 1.5 must succeed before Stage 3 can proceed."
            )

        if audit.ok:
            return AuditResult(passed=True, violation_regions=[])

        regions = _blocking_regions(audit)
        logger.info(
            "Stage 1.5 audit failed — %d blocking violation(s) in region(s) %s",
            len(regions),
            regions,
        )
        return AuditResult(passed=False, violation_regions=regions)


__all__ = ["AuditFilter", "AuditResult", "AuditError"]
