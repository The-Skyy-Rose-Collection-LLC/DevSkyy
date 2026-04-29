"""Integration tests for flux_pipeline Stage E (Stage 1.5 AuditFilter wiring).

Verifies three branches:
  - Stage 1.5 passes   → Stage 1 output accepted, zero inpaint calls, attempts=0
  - Stage 1.5 fails    → Stage 3 inpaint runs, first attempt passes, attempts=1
  - Stage 1.5 fails × 3 → all attempts exhausted, render quarantined, ok=False
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


from skyyrose.elite_studio.agents.vision_audit_agent import (
    VisionAuditResult,
    VisionAuditViolation,
)
from skyyrose.elite_studio.synthesis.stages.audit_filter import AuditResult

_DOSSIER = {
    "name": "Black Rose Crewneck",
    "_dossier_path": "",
    "sku": "br-001",
    "garment_type_lock": "Crewneck sweatshirt",
    "branding_block": "- Front chest (60mm): embossed rose.",
    "negative_block": "- No embroidered patches",
}


def _fake_base_result(tmp_path: Path, filename: str = "stage1.png") -> MagicMock:
    """Return a render-base result mock with a real file on disk."""
    p = tmp_path / filename
    p.write_bytes(b"\x89PNG\r\n")
    r = MagicMock()
    r.output_path = p
    return r


def _fake_inpaint_result(tmp_path: Path, attempt: int) -> MagicMock:
    p = tmp_path / f"inpaint_attempt{attempt}.png"
    p.write_bytes(b"\x89PNG\r\n")
    r = MagicMock()
    r.output_path = p
    return r


def _audit_ok() -> VisionAuditResult:
    return VisionAuditResult(matches_dossier=True, violations=[])


def _audit_fail() -> VisionAuditResult:
    return VisionAuditResult(
        matches_dossier=False,
        violations=[
            VisionAuditViolation(element="embroidered patch", region="front chest", severity="high")
        ],
    )


# ─── Helper: run render() with controllable mocks ──────────────────────────


def _run(
    tmp_path: Path,
    *,
    stage1_audit_passed: bool,
    inpaint_audit_results: list[VisionAuditResult] | None = None,
):
    """Run render() with full mock substitution, return RenderResult."""
    from skyyrose.elite_studio.synthesis import flux_pipeline

    techflat = tmp_path / "techflat.png"
    techflat.write_bytes(b"\x89PNG\r\n")

    base_result = _fake_base_result(tmp_path)
    stage1_audit = AuditResult(
        passed=stage1_audit_passed,
        violation_regions=[] if stage1_audit_passed else ["front chest"],
    )

    # Build MaskDeriver mock
    mask_mock = MagicMock()
    mask_mock.mask_path = tmp_path / "mask.png"
    mask_mock.mask_path.write_bytes(b"\x89PNG\r\n")
    mask_mock.method = "heatmap"
    mask_mock.coverage_frac = 0.12

    inpaint_results = inpaint_audit_results or []
    inpaint_mocks = [_fake_inpaint_result(tmp_path, i + 1) for i in range(len(inpaint_results))]

    with (
        patch.object(flux_pipeline, "render_base", new=AsyncMock(return_value=base_result)),
        patch("skyyrose.elite_studio.synthesis.flux_pipeline.AuditFilter") as MockAF,
        patch("skyyrose.elite_studio.synthesis.flux_pipeline.MaskDeriver") as MockMD,
        patch(
            "skyyrose.elite_studio.synthesis.flux_pipeline.inpaint_decoration",
            new=AsyncMock(side_effect=inpaint_mocks),
        ),
        patch("skyyrose.elite_studio.synthesis.flux_pipeline.VisionAuditAgent") as MockVA,
        patch("skyyrose.elite_studio.synthesis.flux_pipeline._write_manifest"),
        patch(
            "skyyrose.elite_studio.synthesis.flux_pipeline._quarantine",
            side_effect=lambda path, sku, view: path,
        ),
    ):
        af_instance = MagicMock()
        af_instance.check.return_value = stage1_audit
        MockAF.return_value = af_instance

        md_instance = MagicMock()
        md_instance.derive.return_value = mask_mock
        MockMD.return_value = md_instance

        va_instance = MagicMock()
        va_instance.audit.side_effect = inpaint_results
        MockVA.return_value = va_instance

        return asyncio.run(
            flux_pipeline.render(
                sku="br-001",
                view="front",
                dossier=_DOSSIER,
                techflat_path=techflat,
                out_dir=tmp_path / "output",
                fal_client=MagicMock(),
            )
        )


# ─── Tests ─────────────────────────────────────────────────────────────────


class TestStage15Pass:
    def test_ok_true_when_stage1_audit_passes(self, tmp_path: Path) -> None:
        result = _run(tmp_path, stage1_audit_passed=True)
        assert result.ok is True

    def test_attempts_zero_when_stage1_accepted(self, tmp_path: Path) -> None:
        result = _run(tmp_path, stage1_audit_passed=True)
        assert result.attempts == 0

    def test_output_path_is_stage1_when_accepted(self, tmp_path: Path) -> None:
        result = _run(tmp_path, stage1_audit_passed=True)
        assert result.output_path is not None
        assert result.output_path.exists()

    def test_no_quarantine_path_when_stage1_accepted(self, tmp_path: Path) -> None:
        result = _run(tmp_path, stage1_audit_passed=True)
        assert result.quarantine_path is None

    def test_audit_result_none_when_stage1_accepted(self, tmp_path: Path) -> None:
        # No VisionAuditAgent call happens on the Stage 1 output in this path.
        result = _run(tmp_path, stage1_audit_passed=True)
        assert result.audit_result is None


class TestStage15FailThenInpaintPass:
    def test_ok_true_when_inpaint_first_attempt_passes(self, tmp_path: Path) -> None:
        result = _run(
            tmp_path,
            stage1_audit_passed=False,
            inpaint_audit_results=[_audit_ok()],
        )
        assert result.ok is True

    def test_attempts_one_when_inpaint_first_attempt_passes(self, tmp_path: Path) -> None:
        result = _run(
            tmp_path,
            stage1_audit_passed=False,
            inpaint_audit_results=[_audit_ok()],
        )
        assert result.attempts == 1

    def test_audit_result_populated_from_stage5(self, tmp_path: Path) -> None:
        result = _run(
            tmp_path,
            stage1_audit_passed=False,
            inpaint_audit_results=[_audit_ok()],
        )
        assert result.audit_result is not None
        assert result.audit_result.ok is True


class TestStage15FailAllAttemptsExhausted:
    def test_ok_false_when_all_attempts_fail(self, tmp_path: Path) -> None:
        result = _run(
            tmp_path,
            stage1_audit_passed=False,
            inpaint_audit_results=[_audit_fail(), _audit_fail(), _audit_fail()],
        )
        assert result.ok is False

    def test_attempts_max_when_exhausted(self, tmp_path: Path) -> None:
        from skyyrose.elite_studio.synthesis.flux_pipeline import MAX_ATTEMPTS

        result = _run(
            tmp_path,
            stage1_audit_passed=False,
            inpaint_audit_results=[_audit_fail()] * MAX_ATTEMPTS,
        )
        assert result.attempts == MAX_ATTEMPTS

    def test_quarantine_path_set_when_exhausted(self, tmp_path: Path) -> None:
        result = _run(
            tmp_path,
            stage1_audit_passed=False,
            inpaint_audit_results=[_audit_fail(), _audit_fail(), _audit_fail()],
        )
        assert result.quarantine_path is not None

    def test_output_path_none_when_exhausted(self, tmp_path: Path) -> None:
        result = _run(
            tmp_path,
            stage1_audit_passed=False,
            inpaint_audit_results=[_audit_fail(), _audit_fail(), _audit_fail()],
        )
        assert result.output_path is None
