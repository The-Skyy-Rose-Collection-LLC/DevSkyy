"""Tests for AuditFilter (Stage 1.5 — Path B audit adapter)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

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

_DOSSIER: dict = {
    "name": "Black Rose Crewneck",
    "sku": "br-001",
    "garment_type_lock": "Crewneck sweatshirt",
    "branding_block": "- Front chest (60mm): embossed rose. Technique: embossed.",
    "negative_block": "- No embroidered patches\n- No printed text",
}


# ─── AuditResult model ─────────────────────────────────────────────────────


class TestAuditResult:
    def test_frozen(self) -> None:
        r = AuditResult(passed=True)
        with pytest.raises((AttributeError, TypeError)):
            r.passed = False  # type: ignore[misc]

    def test_needs_inpaint_false_when_passed(self) -> None:
        assert AuditResult(passed=True, violation_regions=["front chest"]).needs_inpaint is False

    def test_needs_inpaint_false_when_no_regions(self) -> None:
        assert AuditResult(passed=False, violation_regions=[]).needs_inpaint is False

    def test_needs_inpaint_true_when_failed_with_regions(self) -> None:
        assert AuditResult(passed=False, violation_regions=["front chest"]).needs_inpaint is True


# ─── AuditFilter.check ─────────────────────────────────────────────────────


def _make_filter_with(audit_result: VisionAuditResult) -> AuditFilter:
    af = AuditFilter()
    af._agent = MagicMock()
    af._agent.audit.return_value = audit_result
    return af


class TestAuditFilterPass:
    def test_returns_passed_true_when_audit_ok(self, tmp_path: Path) -> None:
        img = tmp_path / "render.png"
        img.touch()
        ok_audit = VisionAuditResult(matches_dossier=True, violations=[])
        af = _make_filter_with(ok_audit)

        result = af.check(img, _DOSSIER, view="front")

        assert result.passed is True
        assert result.violation_regions == []

    def test_violation_regions_empty_on_pass(self, tmp_path: Path) -> None:
        img = tmp_path / "render.png"
        img.touch()
        ok_audit = VisionAuditResult(matches_dossier=True, violations=[])
        af = _make_filter_with(ok_audit)

        result = af.check(img, _DOSSIER)
        assert result.violation_regions == []


class TestAuditFilterFail:
    def _make_blocking_audit(self, regions: list[str]) -> VisionAuditResult:
        return VisionAuditResult(
            matches_dossier=False,
            violations=[
                VisionAuditViolation(element="embroidered patch", region=r, severity="high")
                for r in regions
            ],
        )

    def test_returns_passed_false_on_violation(self, tmp_path: Path) -> None:
        img = tmp_path / "render.png"
        img.touch()
        af = _make_filter_with(self._make_blocking_audit(["front chest"]))

        result = af.check(img, _DOSSIER, view="front")
        assert result.passed is False

    def test_violation_regions_extracted(self, tmp_path: Path) -> None:
        img = tmp_path / "render.png"
        img.touch()
        af = _make_filter_with(self._make_blocking_audit(["front chest", "left sleeve"]))

        result = af.check(img, _DOSSIER)
        assert set(result.violation_regions) == {"front chest", "left sleeve"}

    def test_deduplicates_same_region(self, tmp_path: Path) -> None:
        img = tmp_path / "render.png"
        img.touch()
        audit = VisionAuditResult(
            matches_dossier=False,
            violations=[
                VisionAuditViolation(element="patch A", region="front", severity="high"),
                VisionAuditViolation(element="patch B", region="front", severity="medium"),
            ],
        )
        af = _make_filter_with(audit)

        result = af.check(img, _DOSSIER)
        assert result.violation_regions.count("front") == 1

    def test_low_severity_violations_excluded_from_regions(self, tmp_path: Path) -> None:
        img = tmp_path / "render.png"
        img.touch()
        audit = VisionAuditResult(
            matches_dossier=False,
            violations=[
                VisionAuditViolation(element="size label", region="collar", severity="low"),
            ],
        )
        af = _make_filter_with(audit)

        result = af.check(img, _DOSSIER)
        # VisionAuditAgent.ok returns True when only low-severity violations exist —
        # low = "uncertain" tier, not a gate failure. AuditFilter passes it through.
        assert result.passed is True
        assert result.violation_regions == []

    def test_needs_inpaint_false_when_only_low_severity(self, tmp_path: Path) -> None:
        img = tmp_path / "render.png"
        img.touch()
        audit = VisionAuditResult(
            matches_dossier=False,
            violations=[
                VisionAuditViolation(element="label", region="hem", severity="low"),
            ],
        )
        af = _make_filter_with(audit)

        result = af.check(img, _DOSSIER)
        assert result.needs_inpaint is False


class TestAuditFilterError:
    def test_raises_audit_error_on_infrastructure_failure(self, tmp_path: Path) -> None:
        img = tmp_path / "render.png"
        img.touch()
        broken_audit = VisionAuditResult(
            matches_dossier=False,
            error="connection timeout",
        )
        af = _make_filter_with(broken_audit)

        with pytest.raises(AuditError, match="connection timeout"):
            af.check(img, _DOSSIER)

    def test_raises_audit_error_not_returns_failed(self, tmp_path: Path) -> None:
        img = tmp_path / "render.png"
        img.touch()
        broken_audit = VisionAuditResult(
            matches_dossier=False,
            error="parse error",
        )
        af = _make_filter_with(broken_audit)

        with pytest.raises(AuditError):
            result = af.check(img, _DOSSIER)
            # This line must not be reached — audit error must raise, not return
            assert result is None
