"""Per-stage FAL budget gate coverage for the live FluxProviderMixin.

These tests exercise the actual code path used in production:
``CompositorAgent`` inherits ``FluxProviderMixin``; the orchestrator's
``_composite_with_flux`` calls ``self._flux_fill_fal``,
``self._flux_kontext``, ``self._flux_fill_replicate``. Patching at the
``compositor_agent`` shim namespace mirrors what graph/nodes.py does at
runtime (FAL / httpx are imported through the shim so they're patchable
at one canonical location).

Tests cover, per FAL provider method:
  - within budget   -> dispatch, ``budget.spend`` called with the right cost
  - over budget     -> ``BudgetExceededError`` raised, FAL never touched
  - budget is None  -> dispatch proceeds (WARN-only back-compat)
  - STRICT mode     -> ``BudgetExceededError`` raised when budget is None

Plus a fallback-chain test on ``_composite_with_flux`` that proves the
budget kwarg threads through to each provider in turn.

No real FAL, Replicate, or httpx calls are made.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from skyyrose.elite_studio.agents.compositor.infra import (
    _FLUX_FILL_FAL_COST_USD,
    _FLUX_KONTEXT_FALLBACK_COST_USD,
)
from skyyrose.elite_studio.agents.compositor_agent import CompositorAgent
from skyyrose.elite_studio.budget import BudgetExceededError, RunBudget

# ---------------------------------------------------------------------------
# Constants / helpers
# ---------------------------------------------------------------------------

_FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 24
_SCENE = "https://cdn.fal.ai/scene.jpg"
_MASK = "https://cdn.fal.ai/mask.png"
_REF = "https://cdn.fal.ai/ref.png"
_PROMPT = "Luxury product floating in studio scene"

_SHIM = "skyyrose.elite_studio.agents.compositor_agent"


def _agent() -> CompositorAgent:
    """Construct a CompositorAgent with a stubbed Anthropic client.

    Anthropic instantiation hits a real client constructor on __init__; tests
    don't exercise the Sonnet QA path so a MagicMock is sufficient.
    """
    with patch(f"{_SHIM}.get_anthropic_client", return_value=MagicMock()):
        return CompositorAgent()


def _fal_client_returning(bytes_url: str = "https://cdn.fal.ai/out.png") -> MagicMock:
    """Create a fake fal_client whose .run() returns a result with images=[bytes_url]."""
    fal = MagicMock()
    result = MagicMock()
    result.get = MagicMock(
        side_effect=lambda key, default=None: {"images": [{"url": bytes_url}]}.get(key, default)
    )
    # fal_client.run returns dict-like; _extract_first_image_url tries .get('images')
    fal.run.return_value = {"images": [{"url": bytes_url}]}
    return fal


def _httpx_returning_bytes(payload: bytes = _FAKE_PNG) -> MagicMock:
    """Create a fake httpx module whose .get(url).content is `payload`."""
    httpx = MagicMock()
    resp = MagicMock()
    resp.content = payload
    resp.raise_for_status = MagicMock(return_value=None)
    httpx.get.return_value = resp
    # _flux_fill_replicate uses httpx.post + httpx.get
    post_resp = MagicMock()
    post_resp.json.return_value = {"urls": {"get": "https://api.replicate.com/poll/abc"}}
    post_resp.raise_for_status = MagicMock(return_value=None)
    httpx.post.return_value = post_resp
    return httpx


# ===========================================================================
# _flux_fill_fal — primary FLUX inpaint
# ===========================================================================


class TestFluxFillFalBudget:
    def test_within_budget_dispatches_and_spends(self) -> None:
        agent = _agent()
        budget = RunBudget(ceiling_usd=1.0)
        with (
            patch(f"{_SHIM}.fal_client", _fal_client_returning()),
            patch(f"{_SHIM}.httpx", _httpx_returning_bytes()),
        ):
            out = agent._flux_fill_fal(_SCENE, _MASK, _PROMPT, budget=budget)
        assert out == _FAKE_PNG
        assert budget.spent_usd == pytest.approx(_FLUX_FILL_FAL_COST_USD)

    def test_exceeds_budget_raises_before_dispatch(self) -> None:
        agent = _agent()
        budget = RunBudget(ceiling_usd=0.0)
        fal_mock = _fal_client_returning()
        with (
            patch(f"{_SHIM}.fal_client", fal_mock),
            patch(f"{_SHIM}.httpx", _httpx_returning_bytes()),
        ):
            with pytest.raises(BudgetExceededError):
                agent._flux_fill_fal(_SCENE, _MASK, _PROMPT, budget=budget)
        fal_mock.run.assert_not_called()

    def test_none_budget_warn_only_back_compat(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ELITE_STUDIO_STRICT_BUDGET", raising=False)
        agent = _agent()
        with (
            patch(f"{_SHIM}.fal_client", _fal_client_returning()),
            patch(f"{_SHIM}.httpx", _httpx_returning_bytes()),
        ):
            out = agent._flux_fill_fal(_SCENE, _MASK, _PROMPT, budget=None)
        assert out == _FAKE_PNG

    def test_strict_mode_raises_on_none_budget(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ELITE_STUDIO_STRICT_BUDGET", "1")
        agent = _agent()
        fal_mock = _fal_client_returning()
        with (
            patch(f"{_SHIM}.fal_client", fal_mock),
            patch(f"{_SHIM}.httpx", _httpx_returning_bytes()),
        ):
            with pytest.raises(BudgetExceededError):
                agent._flux_fill_fal(_SCENE, _MASK, _PROMPT, budget=None)
        fal_mock.run.assert_not_called()


# ===========================================================================
# _flux_kontext — secondary FLUX provider
# ===========================================================================


class TestFluxKontextBudget:
    def test_within_budget_dispatches_and_spends(self) -> None:
        agent = _agent()
        budget = RunBudget(ceiling_usd=1.0)
        with (
            patch(f"{_SHIM}.fal_client", _fal_client_returning()),
            patch(f"{_SHIM}.httpx", _httpx_returning_bytes()),
        ):
            out = agent._flux_kontext(_SCENE, _MASK, _REF, _PROMPT, budget=budget)
        assert out == _FAKE_PNG
        assert budget.spent_usd == pytest.approx(_FLUX_KONTEXT_FALLBACK_COST_USD)

    def test_exceeds_budget_raises_before_dispatch(self) -> None:
        agent = _agent()
        budget = RunBudget(ceiling_usd=0.0)
        fal_mock = _fal_client_returning()
        with (
            patch(f"{_SHIM}.fal_client", fal_mock),
            patch(f"{_SHIM}.httpx", _httpx_returning_bytes()),
        ):
            with pytest.raises(BudgetExceededError):
                agent._flux_kontext(_SCENE, _MASK, _REF, _PROMPT, budget=budget)
        fal_mock.run.assert_not_called()

    def test_strict_mode_raises_on_none_budget(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ELITE_STUDIO_STRICT_BUDGET", "1")
        agent = _agent()
        fal_mock = _fal_client_returning()
        with (
            patch(f"{_SHIM}.fal_client", fal_mock),
            patch(f"{_SHIM}.httpx", _httpx_returning_bytes()),
        ):
            with pytest.raises(BudgetExceededError):
                agent._flux_kontext(_SCENE, _MASK, _REF, _PROMPT, budget=None)
        fal_mock.run.assert_not_called()


# ===========================================================================
# _flux_fill_replicate — tertiary fallback
# ===========================================================================


class TestFluxFillReplicateBudget:
    def test_exceeds_budget_raises_before_dispatch(self) -> None:
        agent = _agent()
        budget = RunBudget(ceiling_usd=0.0)
        httpx_mock = _httpx_returning_bytes()
        with patch(f"{_SHIM}.httpx", httpx_mock):
            with pytest.raises(BudgetExceededError):
                agent._flux_fill_replicate(_SCENE, _MASK, _PROMPT, budget=budget)
        httpx_mock.post.assert_not_called()

    def test_strict_mode_raises_on_none_budget(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ELITE_STUDIO_STRICT_BUDGET", "1")
        agent = _agent()
        httpx_mock = _httpx_returning_bytes()
        with patch(f"{_SHIM}.httpx", httpx_mock):
            with pytest.raises(BudgetExceededError):
                agent._flux_fill_replicate(_SCENE, _MASK, _PROMPT, budget=None)
        httpx_mock.post.assert_not_called()


# ===========================================================================
# _composite_with_flux — budget threads to every provider in the chain
# ===========================================================================


class TestCompositeWithFluxBudgetThreading:
    """The dispatcher must forward `budget=` to every provider call so the
    per-stage gates fire on any provider that runs. Regression guard for the
    code-review CRITICAL where the dispatcher dropped budget on the floor.
    """

    def test_primary_hit_passes_budget_to_kontext(self) -> None:
        # kontext is the PRIMARY provider (flux_methods order: kontext → fal-fill
        # → replicate; promoted in da951f494 because kontext conditions on the
        # relit garment reference). When it succeeds, fal-fill/replicate never run.
        agent = _agent()
        budget = RunBudget(ceiling_usd=1.0)
        with (
            patch.object(agent, "_flux_kontext", return_value=_FAKE_PNG) as kontext,
            patch.object(agent, "_flux_fill_fal") as fal,
            patch.object(agent, "_flux_fill_replicate") as replicate,
        ):
            out, provider = agent._composite_with_flux(
                scene_url=_SCENE,
                subject_url=_REF,
                mask_url=_MASK,
                prompt=_PROMPT,
                budget=budget,
            )
        assert provider == "kontext"
        assert out == _FAKE_PNG
        kontext.assert_called_once_with(_SCENE, _MASK, _REF, _PROMPT, budget=budget)
        fal.assert_not_called()
        replicate.assert_not_called()

    def test_fallback_chain_threads_budget_through_all_providers(self) -> None:
        agent = _agent()
        budget = RunBudget(ceiling_usd=1.0)
        with (
            patch.object(agent, "_flux_fill_fal", return_value=None) as fal,
            patch.object(agent, "_flux_kontext", return_value=None) as kontext,
            patch.object(agent, "_flux_fill_replicate", return_value=_FAKE_PNG) as replicate,
        ):
            out, provider = agent._composite_with_flux(
                scene_url=_SCENE,
                subject_url=_REF,
                mask_url=_MASK,
                prompt=_PROMPT,
                budget=budget,
            )
        assert provider == "replicate"
        assert out == _FAKE_PNG
        fal.assert_called_once_with(_SCENE, _MASK, _PROMPT, budget=budget)
        kontext.assert_called_once_with(_SCENE, _MASK, _REF, _PROMPT, budget=budget)
        replicate.assert_called_once_with(_SCENE, _MASK, _PROMPT, budget=budget)

    def test_none_budget_threads_none_to_providers(self) -> None:
        agent = _agent()
        with (patch.object(agent, "_flux_fill_fal", return_value=_FAKE_PNG) as fal,):
            agent._composite_with_flux(
                scene_url=_SCENE,
                subject_url=_REF,
                mask_url=_MASK,
                prompt=_PROMPT,
                budget=None,
            )
        fal.assert_called_once_with(_SCENE, _MASK, _PROMPT, budget=None)
