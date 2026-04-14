"""Tests for VariantAgent — multi-angle variant generation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from skyyrose.elite_studio.agents.variant_agent import VariantAgent, _get_prompt_modifier
from skyyrose.elite_studio.models import GenerationResult, VariantResult, VariantSpec


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestVariantResultModel:
    def test_frozen(self):
        r = VariantResult(success=True)
        with pytest.raises((AttributeError, TypeError)):
            r.success = False  # type: ignore[misc]

    def test_defaults(self):
        r = VariantResult(success=False)
        assert r.variant_name == ""
        assert r.output_path == ""
        assert r.error == ""


class TestVariantSpecModel:
    def test_frozen(self):
        s = VariantSpec(name="back_view", prompt_modifier="show back")
        with pytest.raises((AttributeError, TypeError)):
            s.name = "other"  # type: ignore[misc]

    def test_fields(self):
        s = VariantSpec(name="side_view", prompt_modifier="90 degree profile")
        assert s.name == "side_view"
        assert s.prompt_modifier == "90 degree profile"


# ---------------------------------------------------------------------------
# _get_prompt_modifier helper
# ---------------------------------------------------------------------------


class TestGetPromptModifier:
    def test_known_variants_have_modifiers(self):
        for name in ("back_view", "side_view", "detail_shot", "flat_lay", "lifestyle"):
            mod = _get_prompt_modifier(name)
            assert len(mod) > 10, f"Modifier for {name} is too short"

    def test_unknown_variant_returns_generic(self):
        mod = _get_prompt_modifier("underwater_shot")
        assert "UNDERWATER SHOT" in mod or "underwater_shot" in mod.lower() or "UNDERWATER" in mod

    def test_back_view_mentions_back(self):
        mod = _get_prompt_modifier("back_view")
        assert "BACK" in mod or "back" in mod.lower()

    def test_side_view_mentions_side(self):
        mod = _get_prompt_modifier("side_view")
        assert "SIDE" in mod or "side" in mod.lower() or "profile" in mod.lower()


# ---------------------------------------------------------------------------
# VariantAgent — happy path
# ---------------------------------------------------------------------------


def _make_gen_result(success=True, path="/tmp/out.jpg", error="") -> GenerationResult:
    return GenerationResult(
        success=success,
        provider="google",
        model="gemini-3-pro-image-preview",
        output_path=path if success else "",
        error=error,
    )


class TestVariantAgentSuccess:
    def setup_method(self):
        self.agent = VariantAgent()

    def test_empty_variants_returns_empty_list(self):
        results = self.agent.generate_variants("br-001", "/base.jpg", "spec", [])
        assert results == []

    def test_single_variant_returns_one_result(self):
        mock_gen = MagicMock()
        mock_gen.generate.return_value = _make_gen_result(path="/tmp/br-001-back.jpg")

        with patch(
            "skyyrose.elite_studio.agents.variant_agent.GeneratorAgent",
            return_value=mock_gen,
        ):
            results = self.agent.generate_variants("br-001", "/base.jpg", "spec", ["back_view"])

        assert len(results) == 1
        assert results[0].success is True
        assert results[0].variant_name == "back_view"
        assert results[0].output_path == "/tmp/br-001-back.jpg"

    def test_multiple_variants_all_attempted(self):
        mock_gen = MagicMock()
        mock_gen.generate.return_value = _make_gen_result(path="/tmp/out.jpg")

        with patch(
            "skyyrose.elite_studio.agents.variant_agent.GeneratorAgent",
            return_value=mock_gen,
        ):
            results = self.agent.generate_variants(
                "br-001", "/base.jpg", "spec", ["back_view", "side_view", "flat_lay"]
            )

        assert len(results) == 3
        names = [r.variant_name for r in results]
        assert "back_view" in names
        assert "side_view" in names
        assert "flat_lay" in names

    def test_variant_name_stored_in_result(self):
        mock_gen = MagicMock()
        mock_gen.generate.return_value = _make_gen_result()

        with patch(
            "skyyrose.elite_studio.agents.variant_agent.GeneratorAgent",
            return_value=mock_gen,
        ):
            results = self.agent.generate_variants("sg-005", "/base.jpg", "spec", ["lifestyle"])

        assert results[0].variant_name == "lifestyle"

    def test_prompt_modifier_injected_into_spec(self):
        """Generator should be called with enriched spec containing the modifier."""
        mock_gen = MagicMock()
        mock_gen.generate.return_value = _make_gen_result()

        with patch(
            "skyyrose.elite_studio.agents.variant_agent.GeneratorAgent",
            return_value=mock_gen,
        ):
            self.agent.generate_variants("br-001", "/base.jpg", "original spec", ["back_view"])

        call_kwargs = mock_gen.generate.call_args
        spec_arg = call_kwargs[1].get("generation_spec") or call_kwargs[0][2]
        assert "original spec" in spec_arg
        assert "BACK" in spec_arg or "back" in spec_arg.lower()


# ---------------------------------------------------------------------------
# VariantAgent — partial failure
# ---------------------------------------------------------------------------


class TestVariantAgentPartialFailure:
    def setup_method(self):
        self.agent = VariantAgent()

    def test_partial_success_allowed(self):
        """One variant can fail without stopping the rest."""
        call_count = 0

        def side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_gen_result(success=False, error="API timeout")
            return _make_gen_result(path="/tmp/side.jpg")

        mock_gen = MagicMock()
        mock_gen.generate.side_effect = side_effect

        with patch(
            "skyyrose.elite_studio.agents.variant_agent.GeneratorAgent",
            return_value=mock_gen,
        ):
            results = self.agent.generate_variants(
                "br-001", "/base.jpg", "spec", ["back_view", "side_view"]
            )

        assert len(results) == 2
        assert results[0].success is False
        assert results[1].success is True

    def test_generation_failure_captured_in_result(self):
        mock_gen = MagicMock()
        mock_gen.generate.return_value = _make_gen_result(success=False, error="No reference image")

        with patch(
            "skyyrose.elite_studio.agents.variant_agent.GeneratorAgent",
            return_value=mock_gen,
        ):
            results = self.agent.generate_variants("br-001", "/base.jpg", "spec", ["back_view"])

        assert results[0].success is False
        assert "No reference image" in results[0].error

    def test_exception_in_variant_captured_not_raised(self):
        mock_gen = MagicMock()
        mock_gen.generate.side_effect = RuntimeError("Crash!")

        with patch(
            "skyyrose.elite_studio.agents.variant_agent.GeneratorAgent",
            return_value=mock_gen,
        ):
            results = self.agent.generate_variants("br-001", "/base.jpg", "spec", ["back_view"])

        assert results[0].success is False
        assert "Crash!" in results[0].error

    def test_all_variants_attempted_even_after_exception(self):
        call_count = 0

        def side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("First fails")
            return _make_gen_result(path="/tmp/ok.jpg")

        mock_gen = MagicMock()
        mock_gen.generate.side_effect = side_effect

        with patch(
            "skyyrose.elite_studio.agents.variant_agent.GeneratorAgent",
            return_value=mock_gen,
        ):
            results = self.agent.generate_variants(
                "br-001", "/base.jpg", "spec", ["back_view", "side_view", "flat_lay"]
            )

        assert len(results) == 3
        assert results[0].success is False
        assert results[1].success is True
        assert results[2].success is True

    def test_results_are_frozen(self):
        mock_gen = MagicMock()
        mock_gen.generate.return_value = _make_gen_result()

        with patch(
            "skyyrose.elite_studio.agents.variant_agent.GeneratorAgent",
            return_value=mock_gen,
        ):
            results = self.agent.generate_variants("br-001", "/base.jpg", "spec", ["back_view"])

        with pytest.raises((AttributeError, TypeError)):
            results[0].success = False  # type: ignore[misc]
