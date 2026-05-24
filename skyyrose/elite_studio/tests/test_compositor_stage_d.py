"""Unit tests for compositor/stage_d_flux.py — budget gate coverage.

Tests cover:
- flux_fill_fal:        budget pass / exceed / None (warn) / STRICT raise
- flux_kontext:         budget pass / exceed / None (warn) / STRICT raise
- flux_fill_replicate:  budget pass / exceed / None (warn) / STRICT raise
- composite_with_flux:  fallback chain wiring (primary hit / primary miss secondary hit)

No real FAL, Replicate, or httpx calls are made — all external I/O is mocked.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from skyyrose.elite_studio.agents.compositor.stage_d_flux import (
    _FLUX_FILL_FAL_COST_USD,
    _FLUX_FILL_REPLICATE_COST_USD,
    _FLUX_KONTEXT_FALLBACK_COST_USD,
    composite_with_flux,
    flux_fill_fal,
    flux_fill_replicate,
    flux_kontext,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 24  # minimal fake PNG bytes
_SCENE = "https://cdn.fal.ai/scene.jpg"
_MASK = "https://cdn.fal.ai/mask.png"
_REF = "https://cdn.fal.ai/ref.png"
_PROMPT = "Luxury product floating in studio scene"


def _mock_budget(headroom_usd: float = 10.0) -> MagicMock:
    """Create a fake RunBudget-like object with no headroom issues."""
    budget = MagicMock()
    budget.ensure_within_budget.return_value = None
    budget.spend.return_value = None
    return budget


def _tight_budget(exc: Exception) -> MagicMock:
    """Create a fake RunBudget that raises exc from ensure_within_budget."""
    budget = MagicMock()
    budget.ensure_within_budget.side_effect = exc
    return budget


def _fal_result(url: str) -> dict:
    return {"images": [{"url": url}]}


def _httpx_ok(content: bytes = _FAKE_PNG) -> MagicMock:
    resp = MagicMock()
    resp.content = content
    resp.raise_for_status.return_value = None
    return resp


# ---------------------------------------------------------------------------
# flux_fill_fal
# ---------------------------------------------------------------------------


class TestFluxFillFal:
    """Budget gate and success/failure paths for flux_fill_fal."""

    def test_pass_with_budget_calls_spend(self) -> None:
        """When budget has headroom, spend() is called on success."""
        budget = _mock_budget()
        fake_url = "https://cdn.fal.ai/result.png"
        mock_fc = MagicMock()
        mock_fc.run.return_value = _fal_result(fake_url)

        with (
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.fal_client",
                mock_fc,
            ),
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.httpx.get",
                return_value=_httpx_ok(),
            ),
        ):
            result = flux_fill_fal(_SCENE, _MASK, _PROMPT, budget=budget)

        assert result == _FAKE_PNG
        budget.ensure_within_budget.assert_called_once_with(_FLUX_FILL_FAL_COST_USD)
        budget.spend.assert_called_once_with(_FLUX_FILL_FAL_COST_USD)

    def test_exceed_budget_raises(self) -> None:
        """When ensure_within_budget raises, the exception propagates out of flux_fill_fal."""
        exc = RuntimeError("BudgetExceeded: not enough headroom")
        budget = _tight_budget(exc)

        with (
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.fal_client",
                MagicMock(),
            ),
            pytest.raises(RuntimeError, match="BudgetExceeded"),
        ):
            flux_fill_fal(_SCENE, _MASK, _PROMPT, budget=budget)

        budget.spend.assert_not_called()

    def test_none_budget_warns_and_proceeds(self, caplog: pytest.LogCaptureFixture) -> None:
        """When budget=None, a WARNING is emitted and the call proceeds."""
        fake_url = "https://cdn.fal.ai/result.png"
        mock_fc = MagicMock()
        mock_fc.run.return_value = _fal_result(fake_url)

        with (
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.fal_client",
                mock_fc,
            ),
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.httpx.get",
                return_value=_httpx_ok(),
            ),
            caplog.at_level("WARNING"),
        ):
            result = flux_fill_fal(_SCENE, _MASK, _PROMPT, budget=None)

        assert result == _FAKE_PNG
        assert "no RunBudget supplied" in caplog.text

    def test_strict_budget_with_none_raises(self) -> None:
        """When ELITE_STUDIO_STRICT_BUDGET=1 and budget=None, RuntimeError raised."""
        with (
            patch.dict(os.environ, {"ELITE_STUDIO_STRICT_BUDGET": "1"}),
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.fal_client",
                MagicMock(),
            ),
        ):
            with pytest.raises(RuntimeError, match="ELITE_STUDIO_STRICT_BUDGET"):
                flux_fill_fal(_SCENE, _MASK, _PROMPT, budget=None)


# ---------------------------------------------------------------------------
# flux_kontext
# ---------------------------------------------------------------------------


class TestFluxKontext:
    """Budget gate and success/failure paths for flux_kontext."""

    def test_pass_with_budget_calls_spend(self) -> None:
        budget = _mock_budget()
        fake_url = "https://cdn.fal.ai/kontext-result.png"
        mock_fc = MagicMock()
        mock_fc.run.return_value = _fal_result(fake_url)

        with (
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.fal_client",
                mock_fc,
            ),
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.httpx.get",
                return_value=_httpx_ok(),
            ),
        ):
            result = flux_kontext(_SCENE, _MASK, _REF, _PROMPT, budget=budget)

        assert result == _FAKE_PNG
        budget.ensure_within_budget.assert_called_once_with(_FLUX_KONTEXT_FALLBACK_COST_USD)
        budget.spend.assert_called_once_with(_FLUX_KONTEXT_FALLBACK_COST_USD)

    def test_exceed_budget_raises(self) -> None:
        exc = RuntimeError("BudgetExceeded")
        budget = _tight_budget(exc)

        with (
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.fal_client",
                MagicMock(),
            ),
            pytest.raises(RuntimeError, match="BudgetExceeded"),
        ):
            flux_kontext(_SCENE, _MASK, _REF, _PROMPT, budget=budget)

        budget.spend.assert_not_called()

    def test_none_budget_warns_and_proceeds(self, caplog: pytest.LogCaptureFixture) -> None:
        fake_url = "https://cdn.fal.ai/kontext-result.png"
        mock_fc = MagicMock()
        mock_fc.run.return_value = _fal_result(fake_url)

        with (
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.fal_client",
                mock_fc,
            ),
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.httpx.get",
                return_value=_httpx_ok(),
            ),
            caplog.at_level("WARNING"),
        ):
            result = flux_kontext(_SCENE, _MASK, _REF, _PROMPT, budget=None)

        assert result == _FAKE_PNG
        assert "no RunBudget supplied" in caplog.text

    def test_strict_budget_with_none_raises(self) -> None:
        with (
            patch.dict(os.environ, {"ELITE_STUDIO_STRICT_BUDGET": "1"}),
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.fal_client",
                MagicMock(),
            ),
        ):
            with pytest.raises(RuntimeError, match="ELITE_STUDIO_STRICT_BUDGET"):
                flux_kontext(_SCENE, _MASK, _REF, _PROMPT, budget=None)


# ---------------------------------------------------------------------------
# flux_fill_replicate
# ---------------------------------------------------------------------------


class TestFluxFillReplicate:
    """Budget gate and success/failure paths for flux_fill_replicate."""

    def _mock_replicate_success(self) -> tuple[MagicMock, MagicMock]:
        """Return (predict_resp, poll_resp) mocks for a succeeded Replicate run."""
        predict_resp = MagicMock()
        predict_resp.is_success = True
        predict_resp.json.return_value = {
            "urls": {"get": "https://api.replicate.com/v1/predictions/abc123"}
        }

        poll_resp = MagicMock()
        poll_resp.raise_for_status.return_value = None
        poll_resp.json.return_value = {
            "status": "succeeded",
            "output": ["https://cdn.replicate.com/out.png"],
        }

        return predict_resp, poll_resp

    def test_pass_with_budget_calls_spend(self) -> None:
        budget = _mock_budget()
        predict_resp, poll_resp = self._mock_replicate_success()
        img_resp = _httpx_ok()

        call_count = [0]

        def httpx_get_side_effect(url, **kwargs):
            call_count[0] += 1
            if "predictions" in url:
                return poll_resp
            return img_resp

        with (
            patch.dict(os.environ, {"REPLICATE_API_TOKEN": "test-token"}),
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.httpx.post",
                return_value=predict_resp,
            ),
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.httpx.get",
                side_effect=httpx_get_side_effect,
            ),
        ):
            result = flux_fill_replicate(_SCENE, _MASK, _PROMPT, budget=budget)

        assert result == _FAKE_PNG
        budget.ensure_within_budget.assert_called_once_with(_FLUX_FILL_REPLICATE_COST_USD)
        budget.spend.assert_called_once_with(_FLUX_FILL_REPLICATE_COST_USD)

    def test_exceed_budget_raises(self) -> None:
        exc = RuntimeError("BudgetExceeded")
        budget = _tight_budget(exc)

        with (
            patch.dict(os.environ, {"REPLICATE_API_TOKEN": "test-token"}),
            pytest.raises(RuntimeError, match="BudgetExceeded"),
        ):
            flux_fill_replicate(_SCENE, _MASK, _PROMPT, budget=budget)

        budget.spend.assert_not_called()

    def test_none_budget_warns_and_proceeds(self, caplog: pytest.LogCaptureFixture) -> None:
        predict_resp, poll_resp = self._mock_replicate_success()
        img_resp = _httpx_ok()

        def httpx_get_side_effect(url, **kwargs):
            if "predictions" in url:
                return poll_resp
            return img_resp

        with (
            patch.dict(os.environ, {"REPLICATE_API_TOKEN": "test-token"}),
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.httpx.post",
                return_value=predict_resp,
            ),
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.httpx.get",
                side_effect=httpx_get_side_effect,
            ),
            caplog.at_level("WARNING"),
        ):
            result = flux_fill_replicate(_SCENE, _MASK, _PROMPT, budget=None)

        assert result == _FAKE_PNG
        assert "no RunBudget supplied" in caplog.text

    def test_strict_budget_with_none_raises(self) -> None:
        with (
            patch.dict(
                os.environ, {"ELITE_STUDIO_STRICT_BUDGET": "1", "REPLICATE_API_TOKEN": "test-token"}
            ),
        ):
            with pytest.raises(RuntimeError, match="ELITE_STUDIO_STRICT_BUDGET"):
                flux_fill_replicate(_SCENE, _MASK, _PROMPT, budget=None)

    def test_no_replicate_token_returns_none(self) -> None:
        """When REPLICATE_API_TOKEN not set, returns None without making HTTP calls."""
        budget = _mock_budget()
        env = {k: v for k, v in os.environ.items() if k != "REPLICATE_API_TOKEN"}

        with patch.dict(os.environ, env, clear=True):
            result = flux_fill_replicate(_SCENE, _MASK, _PROMPT, budget=budget)

        assert result is None
        # ensure_within_budget IS called (gate happens before token check)
        budget.ensure_within_budget.assert_called_once_with(_FLUX_FILL_REPLICATE_COST_USD)
        # spend NOT called because no success
        budget.spend.assert_not_called()


# ---------------------------------------------------------------------------
# composite_with_flux — fallback chain wiring
# ---------------------------------------------------------------------------


class TestCompositeWithFlux:
    """Verify composite_with_flux routes through the fallback chain correctly."""

    def test_primary_hit_returns_fal_fill(self) -> None:
        """When flux_fill_fal returns bytes, use them and report 'fal-fill'."""
        with (
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.flux_fill_fal",
                return_value=_FAKE_PNG,
            ) as mock_primary,
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.flux_kontext",
            ) as mock_secondary,
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.flux_fill_replicate",
            ) as mock_tertiary,
        ):
            result_bytes, provider = composite_with_flux(
                scene_url=_SCENE,
                subject_url=_REF,
                mask_url=_MASK,
                prompt=_PROMPT,
            )

        assert result_bytes == _FAKE_PNG
        assert provider == "fal-fill"
        mock_primary.assert_called_once()
        mock_secondary.assert_not_called()
        mock_tertiary.assert_not_called()

    def test_primary_miss_secondary_hit_returns_kontext(self) -> None:
        with (
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.flux_fill_fal",
                return_value=None,
            ),
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.flux_kontext",
                return_value=_FAKE_PNG,
            ) as mock_secondary,
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.flux_fill_replicate",
            ) as mock_tertiary,
        ):
            result_bytes, provider = composite_with_flux(
                scene_url=_SCENE,
                subject_url=_REF,
                mask_url=_MASK,
                prompt=_PROMPT,
            )

        assert provider == "kontext"
        mock_secondary.assert_called_once()
        mock_tertiary.assert_not_called()

    def test_all_fail_raises_runtime_error(self) -> None:
        with (
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.flux_fill_fal",
                return_value=None,
            ),
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.flux_kontext",
                return_value=None,
            ),
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.flux_fill_replicate",
                return_value=None,
            ),
        ):
            with pytest.raises(RuntimeError, match="All FLUX providers failed"):
                composite_with_flux(
                    scene_url=_SCENE,
                    subject_url=_REF,
                    mask_url=_MASK,
                    prompt=_PROMPT,
                )

    def test_budget_propagated_to_all_providers(self) -> None:
        """Budget object is forwarded to each provider that is tried."""
        budget = _mock_budget()

        with (
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.flux_fill_fal",
                return_value=None,
            ) as mock_primary,
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.flux_kontext",
                return_value=None,
            ) as mock_secondary,
            patch(
                "skyyrose.elite_studio.agents.compositor.stage_d_flux.flux_fill_replicate",
                return_value=_FAKE_PNG,
            ) as mock_tertiary,
        ):
            composite_with_flux(
                scene_url=_SCENE,
                subject_url=_REF,
                mask_url=_MASK,
                prompt=_PROMPT,
                budget=budget,
            )

        # Each provider call should have received the budget kwarg
        _, kwargs_primary = mock_primary.call_args
        _, kwargs_secondary = mock_secondary.call_args
        _, kwargs_tertiary = mock_tertiary.call_args
        assert kwargs_primary.get("budget") is budget
        assert kwargs_secondary.get("budget") is budget
        assert kwargs_tertiary.get("budget") is budget
