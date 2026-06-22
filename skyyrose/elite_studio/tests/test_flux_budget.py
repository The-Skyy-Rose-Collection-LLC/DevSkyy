"""Budget-gate tests for H-01 / H-02 — flux_pipeline.render() + render_base().

Three behavioural cases per the audit spec:
  (a) within budget  → FAL call dispatched, budget.spend() called
  (b) over budget    → FAL call skipped, RenderResult(ok=False, error="budget_exceeded …")
  (c) budget=None    → no gate applied, FAL call dispatched, WARNING logged

All FAL / network I/O is mocked — no paid API calls in tests.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skyyrose.elite_studio.budget import BudgetExceededError, RunBudget
from skyyrose.elite_studio.synthesis.stages.audit_filter import AuditResult

# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------

_DOSSIER: dict = {
    "name": "Black Rose Crewneck",
    "_dossier_path": "",
    "sku": "br-001",
    "garment_type_lock": "Crewneck sweatshirt",
    "branding_block": "- Front chest (60mm): embossed rose.",
    "negative_block": "- No embroidered patches",
}


def _make_base_result(tmp_path: Path) -> MagicMock:
    p = tmp_path / "stage1.png"
    p.write_bytes(b"\x89PNG\r\n")
    r = MagicMock()
    r.output_path = p
    return r


def _make_inpaint_result(tmp_path: Path) -> MagicMock:
    p = tmp_path / "inpaint.png"
    p.write_bytes(b"\x89PNG\r\n")
    r = MagicMock()
    r.output_path = p
    return r


def _audit_ok() -> MagicMock:
    from skyyrose.elite_studio.agents.vision_audit_agent import VisionAuditResult

    return VisionAuditResult(matches_dossier=True, violations=[])


def _run_render(
    tmp_path: Path,
    *,
    budget: RunBudget | None,
    stage1_audit_passed: bool = True,
) -> RenderResult:  # noqa: F821
    """Invoke flux_pipeline.render() with fully-mocked FAL and audit layers."""
    from skyyrose.elite_studio.synthesis import flux_pipeline

    techflat = tmp_path / "techflat.png"
    techflat.write_bytes(b"\x89PNG\r\n")

    base_result = _make_base_result(tmp_path)
    stage1_audit = AuditResult(
        passed=stage1_audit_passed,
        violation_regions=[] if stage1_audit_passed else ["front chest"],
    )

    mask_mock = MagicMock()
    mask_mock.mask_path = tmp_path / "mask.png"
    mask_mock.mask_path.write_bytes(b"\x89PNG\r\n")
    mask_mock.method = "heatmap"
    mask_mock.coverage_frac = 0.10

    with (
        patch.object(flux_pipeline, "render_base", new=AsyncMock(return_value=base_result)),
        patch("skyyrose.elite_studio.synthesis.flux_pipeline.AuditFilter") as MockAF,
        patch("skyyrose.elite_studio.synthesis.flux_pipeline.MaskDeriver") as MockMD,
        patch(
            "skyyrose.elite_studio.synthesis.flux_pipeline.inpaint_decoration",
            new=AsyncMock(return_value=_make_inpaint_result(tmp_path)),
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
        va_instance.audit.return_value = _audit_ok()
        MockVA.return_value = va_instance

        return asyncio.run(
            flux_pipeline.render(
                sku="br-001",
                view="front",
                dossier=_DOSSIER,
                techflat_path=techflat,
                out_dir=tmp_path / "output",
                budget=budget,
                fal_client=MagicMock(),
            )
        )


# ---------------------------------------------------------------------------
# Case (a): within budget — FAL dispatched, spend() called
# ---------------------------------------------------------------------------


class TestBudgetWithinCeiling:
    """When the run has headroom, both Stage 1 and Stage 3 dispatch normally."""

    def test_render_ok_when_budget_has_headroom(self, tmp_path: Path) -> None:
        budget = RunBudget(ceiling_usd=10.0)
        result = _run_render(tmp_path, budget=budget)
        assert result.ok is True

    def test_budget_spend_called_for_stage1(self, tmp_path: Path) -> None:
        from skyyrose.elite_studio.synthesis.flux_pipeline import _FLUX_KONTEXT_EST_COST_USD

        budget = RunBudget(ceiling_usd=10.0)
        _run_render(tmp_path, budget=budget)
        # Stage 1 spend must be recorded
        assert budget.by_stage.get("flux_stage1_kontext", 0.0) == pytest.approx(
            _FLUX_KONTEXT_EST_COST_USD
        )

    def test_budget_spent_usd_positive_after_render(self, tmp_path: Path) -> None:
        budget = RunBudget(ceiling_usd=10.0)
        _run_render(tmp_path, budget=budget)
        assert budget.spent_usd > 0.0

    def test_stage1_audit_pass_skips_fill_spend(self, tmp_path: Path) -> None:
        """When Stage 1.5 passes, Stage 3 never fires — Fill cost not recorded."""
        budget = RunBudget(ceiling_usd=10.0)
        _run_render(tmp_path, budget=budget, stage1_audit_passed=True)
        # Stage 3 key must be absent (Stage 1 accepted, no inpaint)
        assert "flux_stage3_fill" not in budget.by_stage


# ---------------------------------------------------------------------------
# Case (b): over budget — FAL call skipped, structured failure returned
# ---------------------------------------------------------------------------


class TestBudgetExceeded:
    """When ceiling is exhausted, render() returns ok=False without firing FAL."""

    def test_render_ok_false_when_budget_exhausted(self, tmp_path: Path) -> None:
        budget = RunBudget(ceiling_usd=0.0)  # zero headroom
        result = _run_render(tmp_path, budget=budget)
        assert result.ok is False

    def test_render_error_contains_budget_keyword(self, tmp_path: Path) -> None:
        budget = RunBudget(ceiling_usd=0.0)
        result = _run_render(tmp_path, budget=budget)
        # BudgetExceededError message format: "stage=... would push run to $X, ceiling=$Y ..."
        assert any(
            kw in result.error for kw in ("ceiling", "BudgetExceeded", "budget_exceeded", "stage=")
        )

    def test_render_output_path_none_on_budget_exceeded(self, tmp_path: Path) -> None:
        budget = RunBudget(ceiling_usd=0.0)
        result = _run_render(tmp_path, budget=budget)
        assert result.output_path is None

    def test_render_base_not_called_when_budget_exhausted(self, tmp_path: Path) -> None:
        """render_base (the FAL upload+dispatch) must NOT be invoked on budget failure."""
        from skyyrose.elite_studio.synthesis import flux_pipeline

        techflat = tmp_path / "techflat.png"
        techflat.write_bytes(b"\x89PNG\r\n")
        budget = RunBudget(ceiling_usd=0.0)

        with patch.object(
            flux_pipeline, "render_base", new=AsyncMock(return_value=MagicMock())
        ) as mock_rb:
            asyncio.run(
                flux_pipeline.render(
                    sku="br-001",
                    view="front",
                    dossier=_DOSSIER,
                    techflat_path=techflat,
                    out_dir=tmp_path / "output",
                    budget=budget,
                    fal_client=MagicMock(),
                )
            )
            mock_rb.assert_not_called()

    def test_no_spend_recorded_when_budget_exceeded(self, tmp_path: Path) -> None:
        budget = RunBudget(ceiling_usd=0.0)
        _run_render(tmp_path, budget=budget)
        assert budget.spent_usd == pytest.approx(0.0)

    def test_stage3_budget_exceeded_after_stage1_succeeds(self, tmp_path: Path) -> None:
        """Stage 1 passes; Stage 3 budget check fails because ceiling is tight."""
        from skyyrose.elite_studio.synthesis.flux_pipeline import _FLUX_KONTEXT_EST_COST_USD

        # Ceiling exactly covers Stage 1 but not Stage 3
        budget = RunBudget(ceiling_usd=_FLUX_KONTEXT_EST_COST_USD)
        result = _run_render(tmp_path, budget=budget, stage1_audit_passed=False)
        # Stage 1 spend consumed the ceiling; Stage 3 should be blocked
        assert result.ok is False
        assert "flux_stage3_fill" not in budget.by_stage


# ---------------------------------------------------------------------------
# Case (c): budget=None — no gate, FAL dispatched, WARNING logged
# ---------------------------------------------------------------------------


class TestBudgetNone:
    """When budget=None, the pipeline runs without a ceiling and logs a warning."""

    def test_render_ok_without_budget(self, tmp_path: Path) -> None:
        result = _run_render(tmp_path, budget=None)
        assert result.ok is True

    def test_render_base_called_without_budget(self, tmp_path: Path) -> None:
        from skyyrose.elite_studio.synthesis import flux_pipeline

        techflat = tmp_path / "techflat.png"
        techflat.write_bytes(b"\x89PNG\r\n")
        base_result = _make_base_result(tmp_path)

        with (
            patch.object(
                flux_pipeline, "render_base", new=AsyncMock(return_value=base_result)
            ) as mock_rb,
            patch("skyyrose.elite_studio.synthesis.flux_pipeline.AuditFilter") as MockAF,
            patch("skyyrose.elite_studio.synthesis.flux_pipeline._write_manifest"),
        ):
            af_instance = MagicMock()
            af_instance.check.return_value = AuditResult(passed=True, violation_regions=[])
            MockAF.return_value = af_instance

            asyncio.run(
                flux_pipeline.render(
                    sku="br-001",
                    view="front",
                    dossier=_DOSSIER,
                    techflat_path=techflat,
                    out_dir=tmp_path / "output",
                    budget=None,
                    fal_client=MagicMock(),
                )
            )
            mock_rb.assert_called_once()


# ---------------------------------------------------------------------------
# H-02: render_base() accepts budget kwarg and warns when None
# ---------------------------------------------------------------------------


class TestRenderBaseBudgetKwarg:
    """render_base() must accept budget= and emit WARNING when it is None."""

    def test_render_base_warns_when_budget_none(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """render_base(budget=None) must emit a WARNING about the unbudgeted call."""
        from skyyrose.elite_studio.synthesis.stages import base_render

        client = MagicMock()
        client.upload = AsyncMock(return_value="https://fal.cdn/fake.png")
        client.subscribe = AsyncMock(
            return_value=MagicMock(primary_url="https://fal.cdn/out.png", seed=42)
        )

        techflat = tmp_path / "tech.png"
        techflat.write_bytes(b"\x89PNG\r\n")

        async def _download_stub(url: str, dest: Path) -> None:
            dest.write_bytes(b"\x89PNG\r\n")

        with (
            caplog.at_level(
                logging.WARNING, logger="skyyrose.elite_studio.synthesis.stages.base_render"
            ),
            patch.object(base_render, "_download_to", new=AsyncMock(side_effect=_download_stub)),
        ):
            asyncio.run(
                base_render.render_base(
                    client=client,
                    techflat_path=techflat,
                    dossier=_DOSSIER,
                    out_dir=tmp_path / "out",
                    sku="br-001",
                    view="front",
                    budget=None,
                )
            )

        warning_texts = [r.message for r in caplog.records if r.levelno == logging.WARNING]
        assert any(
            "unbudgeted" in t or "RunBudget" in t for t in warning_texts
        ), f"Expected unbudgeted-call warning; got: {warning_texts}"

    def test_render_base_no_warning_when_budget_provided(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """render_base(budget=RunBudget(...)) must NOT emit the unbudgeted warning."""
        from skyyrose.elite_studio.synthesis.stages import base_render

        client = MagicMock()
        client.upload = AsyncMock(return_value="https://fal.cdn/fake.png")
        client.subscribe = AsyncMock(
            return_value=MagicMock(primary_url="https://fal.cdn/out.png", seed=42)
        )

        techflat = tmp_path / "tech.png"
        techflat.write_bytes(b"\x89PNG\r\n")

        async def _download_stub(url: str, dest: Path) -> None:
            dest.write_bytes(b"\x89PNG\r\n")

        budget = RunBudget(ceiling_usd=10.0)

        with (
            caplog.at_level(
                logging.WARNING, logger="skyyrose.elite_studio.synthesis.stages.base_render"
            ),
            patch.object(base_render, "_download_to", new=AsyncMock(side_effect=_download_stub)),
        ):
            asyncio.run(
                base_render.render_base(
                    client=client,
                    techflat_path=techflat,
                    dossier=_DOSSIER,
                    out_dir=tmp_path / "out",
                    sku="br-001",
                    view="front",
                    budget=budget,
                )
            )

        unbudgeted_warnings = [
            r
            for r in caplog.records
            if r.levelno == logging.WARNING
            and ("unbudgeted" in r.message or "RunBudget" in r.message)
        ]
        assert (
            not unbudgeted_warnings
        ), f"Unexpected unbudgeted warning when budget was supplied: {unbudgeted_warnings}"


# ---------------------------------------------------------------------------
# Strict-budget enforcement — ELITE_STUDIO_STRICT_BUDGET env gate
# ---------------------------------------------------------------------------


class TestStrictBudgetEnforcement:
    """ELITE_STUDIO_STRICT_BUDGET=1 must promote the unbudgeted-call WARNING
    into a hard refusal so production deploys cannot silently dispatch
    unbudgeted FAL calls."""

    def test_render_base_raises_when_strict_and_budget_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from skyyrose.elite_studio.synthesis.stages import base_render

        monkeypatch.setenv("ELITE_STUDIO_STRICT_BUDGET", "1")

        client = MagicMock()
        client.upload = AsyncMock(return_value="https://fal.cdn/fake.png")
        client.subscribe = AsyncMock(
            return_value=MagicMock(primary_url="https://fal.cdn/out.png", seed=42)
        )
        techflat = tmp_path / "tech.png"
        techflat.write_bytes(b"\x89PNG\r\n")

        with pytest.raises(BudgetExceededError, match="STRICT_BUDGET"):
            asyncio.run(
                base_render.render_base(
                    client=client,
                    techflat_path=techflat,
                    dossier=_DOSSIER,
                    out_dir=tmp_path / "out",
                    sku="br-001",
                    view="front",
                    budget=None,
                )
            )
        # FAL must not have been touched.
        client.upload.assert_not_called()
        client.subscribe.assert_not_called()

    def test_render_base_passes_when_strict_off_and_budget_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Default (env unset) keeps WARN-only back-compat."""
        from skyyrose.elite_studio.synthesis.stages import base_render

        monkeypatch.delenv("ELITE_STUDIO_STRICT_BUDGET", raising=False)

        client = MagicMock()
        client.upload = AsyncMock(return_value="https://fal.cdn/fake.png")
        client.subscribe = AsyncMock(
            return_value=MagicMock(primary_url="https://fal.cdn/out.png", seed=42)
        )
        techflat = tmp_path / "tech.png"
        techflat.write_bytes(b"\x89PNG\r\n")

        async def _download_stub(url: str, dest: Path) -> None:
            dest.write_bytes(b"\x89PNG\r\n")

        with patch.object(base_render, "_download_to", new=AsyncMock(side_effect=_download_stub)):
            result = asyncio.run(
                base_render.render_base(
                    client=client,
                    techflat_path=techflat,
                    dossier=_DOSSIER,
                    out_dir=tmp_path / "out",
                    sku="br-001",
                    view="front",
                    budget=None,
                )
            )
        assert result is not None
        client.upload.assert_called_once()

    def test_render_base_runs_when_strict_and_budget_provided(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Strict mode allows dispatch when a real RunBudget is supplied."""
        from skyyrose.elite_studio.synthesis.stages import base_render

        monkeypatch.setenv("ELITE_STUDIO_STRICT_BUDGET", "1")

        client = MagicMock()
        client.upload = AsyncMock(return_value="https://fal.cdn/fake.png")
        client.subscribe = AsyncMock(
            return_value=MagicMock(primary_url="https://fal.cdn/out.png", seed=42)
        )
        techflat = tmp_path / "tech.png"
        techflat.write_bytes(b"\x89PNG\r\n")

        async def _download_stub(url: str, dest: Path) -> None:
            dest.write_bytes(b"\x89PNG\r\n")

        budget = RunBudget(ceiling_usd=10.0)
        with patch.object(base_render, "_download_to", new=AsyncMock(side_effect=_download_stub)):
            result = asyncio.run(
                base_render.render_base(
                    client=client,
                    techflat_path=techflat,
                    dossier=_DOSSIER,
                    out_dir=tmp_path / "out",
                    sku="br-001",
                    view="front",
                    budget=budget,
                )
            )
        assert result is not None
        client.upload.assert_called_once()


# ---------------------------------------------------------------------------
# Budget passthrough — flux_pipeline.render forwards budget into render_base
# ---------------------------------------------------------------------------


class TestFluxPipelineBudgetPassthrough:
    """flux_pipeline.render() must forward its budget into render_base()
    so direct callers cannot bypass the gate by going around the wrapper."""

    def test_render_forwards_budget_to_render_base(self, tmp_path: Path) -> None:
        from skyyrose.elite_studio.synthesis import flux_pipeline

        techflat = tmp_path / "tech.png"
        techflat.write_bytes(b"\x89PNG\r\n")
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        budget = RunBudget(ceiling_usd=10.0)
        base_result = MagicMock()
        base_result.output_path = out_dir / "stage1.png"
        base_result.output_path.write_bytes(b"\x89PNG\r\n")
        base_result.seed = 0

        captured_kwargs: dict = {}

        async def _render_base_capture(**kwargs):
            captured_kwargs.update(kwargs)
            return base_result

        with (
            patch.object(flux_pipeline, "render_base", side_effect=_render_base_capture),
            patch.object(
                flux_pipeline,
                "AuditFilter",
                return_value=MagicMock(check=lambda *_a, **_k: MagicMock(passed=True)),
            ),
        ):
            asyncio.run(
                flux_pipeline.render(
                    sku="br-001",
                    view="front",
                    dossier=_DOSSIER,
                    techflat_path=techflat,
                    out_dir=out_dir,
                    budget=budget,
                    fal_client=MagicMock(),
                )
            )

        assert captured_kwargs.get("budget") is budget, (
            "flux_pipeline.render must forward the same RunBudget instance "
            "to render_base — otherwise direct callers can bypass the gate."
        )
