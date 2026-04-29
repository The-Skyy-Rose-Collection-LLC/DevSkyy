"""Unit tests for the Stage 1.5 AuditFilter.

Covers the three decision branches:
  - audit passes    → AuditResult(passed=True, violation_regions=[])
  - audit fails     → AuditResult(passed=False, violation_regions=[...])
  - audit errors    → AuditError raised (fail-loud)

Also verifies:
  - Low-severity violations are excluded from violation_regions
  - Duplicate regions are deduplicated
  - needs_inpaint property
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from skyyrose.elite_studio.agents.vision_audit_agent import (
    VisionAuditResult,
    VisionAuditViolation,
)
from skyyrose.elite_studio.synthesis.stages.audit_filter import (
    AuditError,
    AuditFilter,
    AuditResult,
)

_MOCK_PATH = "skyyrose.elite_studio.synthesis.stages.audit_filter.VisionAuditAgent"
_DOSSIER = {"name": "Black Rose Crewneck", "sku": "br-001"}


def _make_filter(audit_return: VisionAuditResult) -> AuditFilter:
    """Return an AuditFilter whose underlying agent returns a fixed result."""
    with patch(_MOCK_PATH) as MockVA:
        MockVA.return_value.audit.return_value = audit_return
        af = AuditFilter()
        # Patch the already-instantiated agent on the object so the mock persists.
        af._agent = MockVA.return_value
    return af


# ── AuditResult dataclass ────────────────────────────────────────────────────


def test_audit_result_needs_inpaint_true_when_failed_with_regions():
    result = AuditResult(passed=False, violation_regions=["front-center-chest"])
    assert result.needs_inpaint is True


def test_audit_result_needs_inpaint_false_when_passed():
    result = AuditResult(passed=True, violation_regions=[])
    assert result.needs_inpaint is False


def test_audit_result_needs_inpaint_false_when_failed_but_no_regions():
    result = AuditResult(passed=False, violation_regions=[])
    assert result.needs_inpaint is False


# ── AuditFilter.check() — pass branch ───────────────────────────────────────


def test_check_returns_passed_true_when_audit_ok():
    audit = VisionAuditResult(matches_dossier=True, violations=[])
    af = _make_filter(audit)
    result = af.check("stage1.png", _DOSSIER, "front")
    assert result.passed is True


def test_check_returns_empty_violation_regions_when_passed():
    audit = VisionAuditResult(matches_dossier=True, violations=[])
    af = _make_filter(audit)
    result = af.check("stage1.png", _DOSSIER, "front")
    assert result.violation_regions == []


def test_check_needs_inpaint_false_when_passed():
    audit = VisionAuditResult(matches_dossier=True, violations=[])
    af = _make_filter(audit)
    result = af.check("stage1.png", _DOSSIER, "front")
    assert result.needs_inpaint is False


# ── AuditFilter.check() — fail branch ───────────────────────────────────────


def test_check_returns_passed_false_when_audit_fails():
    audit = VisionAuditResult(
        matches_dossier=False,
        violations=[VisionAuditViolation(element="patch", region="front-chest", severity="high")],
    )
    af = _make_filter(audit)
    result = af.check("stage1.png", _DOSSIER, "front")
    assert result.passed is False


def test_check_includes_high_severity_violation_region():
    audit = VisionAuditResult(
        matches_dossier=False,
        violations=[
            VisionAuditViolation(element="logo", region="front-chest", severity="high"),
        ],
    )
    af = _make_filter(audit)
    result = af.check("stage1.png", _DOSSIER, "front")
    assert "front-chest" in result.violation_regions


def test_check_includes_medium_severity_violation_region():
    audit = VisionAuditResult(
        matches_dossier=False,
        violations=[
            VisionAuditViolation(element="embroidery", region="back-yoke", severity="medium"),
        ],
    )
    af = _make_filter(audit)
    result = af.check("stage1.png", _DOSSIER, "front")
    assert "back-yoke" in result.violation_regions


def test_check_excludes_low_severity_violations():
    audit = VisionAuditResult(
        matches_dossier=False,
        violations=[
            VisionAuditViolation(element="size-tag", region="collar-inside", severity="low"),
        ],
    )
    af = _make_filter(audit)
    result = af.check("stage1.png", _DOSSIER, "front")
    assert result.violation_regions == []
    assert result.needs_inpaint is False


def test_check_deduplicates_regions_across_violations():
    audit = VisionAuditResult(
        matches_dossier=False,
        violations=[
            VisionAuditViolation(element="patch-a", region="front-chest", severity="high"),
            VisionAuditViolation(element="patch-b", region="front-chest", severity="medium"),
        ],
    )
    af = _make_filter(audit)
    result = af.check("stage1.png", _DOSSIER, "front")
    assert result.violation_regions.count("front-chest") == 1


def test_check_collects_multiple_distinct_regions():
    audit = VisionAuditResult(
        matches_dossier=False,
        violations=[
            VisionAuditViolation(element="logo", region="front-chest", severity="high"),
            VisionAuditViolation(element="embroidery", region="back-yoke", severity="medium"),
        ],
    )
    af = _make_filter(audit)
    result = af.check("stage1.png", _DOSSIER, "front")
    assert set(result.violation_regions) == {"front-chest", "back-yoke"}


# ── AuditFilter.check() — error branch ──────────────────────────────────────


def test_check_raises_audit_error_on_infrastructure_failure():
    audit = VisionAuditResult(matches_dossier=False, violations=[], error="connection refused")
    af = _make_filter(audit)
    with pytest.raises(AuditError, match="connection refused"):
        af.check("stage1.png", _DOSSIER, "front")
