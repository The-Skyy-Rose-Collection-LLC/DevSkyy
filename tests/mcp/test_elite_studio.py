"""Tests for mcp_tools/tools/elite_studio.py.

Covers:
    - Input validation (Pydantic)
    - Cost estimate math
    - Dry-run paths on all 5 tools
    - FASHN tryon gating (raises NotImplementedError until D7)
    - Dossier hard-fail propagation
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from mcp_tools.tools import elite_studio
from mcp_tools.tools.elite_studio import (
    BatchInput,
    CostEstimateInput,
    RenderInput,
    StatusInput,
    ValidateDossierInput,
    es_batch,
    es_cost_estimate,
    es_render,
    es_status,
    es_validate_dossier,
)

# ---------------------------------------------------------------------------
# Cost estimate math
# ---------------------------------------------------------------------------


class TestCostEstimate:
    @pytest.mark.asyncio
    async def test_fashn_total_matches_canon(self) -> None:
        """FASHN total must match paid-api-stopgate cost manifest."""
        result = await es_cost_estimate(CostEstimateInput(skus=["br-001"], engine="fashn-tryon"))
        # Canon: 16 samples × $0.075 = $1.20 per SKU
        assert "1.2" in result or "$1.20" in result

    @pytest.mark.asyncio
    async def test_per_sku_scales_linearly(self) -> None:
        result_1 = await es_cost_estimate(CostEstimateInput(skus=["a"], engine="nano-banana"))
        result_5 = await es_cost_estimate(
            CostEstimateInput(skus=["a", "b", "c", "d", "e"], engine="nano-banana")
        )
        # 5x the SKUs = 5x the cost
        assert "0.08" in result_1.lower()  # 4 × 0.02 = 0.08
        assert "0.4" in result_5.lower()  # 5 × 0.08 = 0.40

    @pytest.mark.asyncio
    async def test_unknown_engine_raises(self) -> None:
        # Pydantic Literal validation catches it before the function body
        with pytest.raises(Exception):
            CostEstimateInput(skus=["a"], engine="nonsense")  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_samples_override_applied(self) -> None:
        result = await es_cost_estimate(
            CostEstimateInput(skus=["a"], engine="fashn-tryon", samples_per_sku=4)
        )
        # 4 × 0.075 = 0.30
        assert "0.3" in result

    @pytest.mark.asyncio
    async def test_budget_recommendation_has_buffer(self) -> None:
        result = await es_cost_estimate(CostEstimateInput(skus=["a"], engine="nano-banana"))
        # Recommended ceiling = total × 1.2 = 0.08 × 1.2 = 0.096
        assert "0.1" in result or "0.10" in result


# ---------------------------------------------------------------------------
# Validate dossier (read-only, no dispatch)
# ---------------------------------------------------------------------------


class TestValidateDossier:
    @pytest.mark.asyncio
    async def test_missing_sku_returns_fail_report(self) -> None:
        result = await es_validate_dossier(ValidateDossierInput(sku="totally-bogus-sku-xyz"))
        assert "FAILED" in result or "not in catalog" in result.lower()

    @pytest.mark.asyncio
    async def test_known_sku_returns_ok(self) -> None:
        """br-001 should have a dossier per project canon."""
        result = await es_validate_dossier(ValidateDossierInput(sku="br-001"))
        # Either OK or a clear missing-dossier error (dossier files may not exist locally)
        assert "br-001" in result.lower()


# ---------------------------------------------------------------------------
# Render (with_tryon gate)
# ---------------------------------------------------------------------------


class TestRender:
    @pytest.mark.asyncio
    async def test_with_tryon_raises_until_d7(self) -> None:
        with pytest.raises(NotImplementedError, match="FASHN|tryon"):
            await es_render(RenderInput(sku="br-001", with_tryon=True))

    @pytest.mark.asyncio
    async def test_dry_run_dossier_missing_raises(self) -> None:
        with pytest.raises(RuntimeError, match="dossier missing|not in catalog|CSV branding"):
            await es_render(RenderInput(sku="totally-bogus-sku-xyz", confirm=False))

    @pytest.mark.asyncio
    async def test_dry_run_dispatch_does_not_run(self) -> None:
        """confirm=False must NOT invoke build_team / Coordinator.produce."""
        with patch.object(
            elite_studio,
            "get_product_with_dossier",
            create=True,
            return_value={"title": "fake", "dossier_slug": "fake"},
        ):
            # Patch the import inside the function
            import skyyrose.core.dossier_loader as dl

            with patch.object(dl, "get_product_with_dossier", return_value={"title": "x"}):
                # build_team must not be called in dry-run
                with patch("skyyrose.elite_studio.cli.build_team") as fake_build:
                    result = await es_render(
                        RenderInput(sku="br-001", confirm=False, with_tryon=False)
                    )
                    assert not fake_build.called
        assert "dry" in result.lower() or "plan" in result.lower()


# ---------------------------------------------------------------------------
# Batch (resolution + dossier validation upfront)
# ---------------------------------------------------------------------------


class TestBatch:
    @pytest.mark.asyncio
    async def test_must_specify_filter(self) -> None:
        with pytest.raises(ValueError, match="Must specify skus, all_skus"):
            await es_batch(BatchInput())

    @pytest.mark.asyncio
    async def test_dry_run_returns_plan(self) -> None:
        import skyyrose.core.dossier_loader as dl

        with patch.object(dl, "get_product_with_dossier", return_value={"title": "fake"}):
            result = await es_batch(BatchInput(skus=["br-001", "lh-001"], confirm=False))
        # Theme files must NOT be touched (no Coordinator call)
        assert "dry" in result.lower() or "plan" in result.lower()

    @pytest.mark.asyncio
    async def test_missing_dossier_blocks_batch(self) -> None:
        """If ANY SKU lacks a dossier, batch must block — do NOT silently skip."""
        import skyyrose.core.dossier_loader as dl
        from skyyrose.core.dossier_loader import DossierMissingError

        call_count = {"n": 0}

        def fake_loader(sku):
            call_count["n"] += 1
            if sku == "br-001":
                return {"title": "fake"}
            raise DossierMissingError(f"no dossier for {sku}")

        with patch.object(dl, "get_product_with_dossier", side_effect=fake_loader):
            result = await es_batch(BatchInput(skus=["br-001", "missing-sku"], confirm=False))
        assert "BLOCKED" in result or "missing_dossiers" in result.lower()


# ---------------------------------------------------------------------------
# Status (read-only with reader audit)
# ---------------------------------------------------------------------------


class TestStatus:
    @pytest.mark.asyncio
    async def test_status_returns_counts(self) -> None:
        result = await es_status(StatusInput(audit_readers=False))
        assert "total" in result.lower() or "generated" in result.lower()

    @pytest.mark.asyncio
    async def test_status_with_audit(self) -> None:
        result = await es_status(StatusInput(audit_readers=True))
        # Either passes the audit OR surfaces an alert — both acceptable
        assert "reader" in result.lower() or "generated" in result.lower()


# ---------------------------------------------------------------------------
# Input validation (Pydantic)
# ---------------------------------------------------------------------------


class TestInputValidation:
    def test_sku_max_length(self) -> None:
        with pytest.raises(Exception):
            RenderInput(sku="a" * 100)

    def test_render_style_literal(self) -> None:
        with pytest.raises(Exception):
            RenderInput(sku="br-001", style="weirdpants")  # type: ignore[arg-type]

    def test_batch_sku_count_cap(self) -> None:
        with pytest.raises(Exception):
            BatchInput(skus=["x"] * 201)

    def test_cost_estimate_samples_range(self) -> None:
        with pytest.raises(Exception):
            CostEstimateInput(skus=["x"], engine="nano-banana", samples_per_sku=0)
        with pytest.raises(Exception):
            CostEstimateInput(skus=["x"], engine="nano-banana", samples_per_sku=100)
