"""Tests for tryon_node graph node.

Verifies:
- Skips silently when generation_result is absent
- Skips silently when generation_result.success is False
- Skips silently when no garment image is found for the SKU
- Calls TryOnAgent.try_on() with correct args on the happy path
- Always updates stage_timings["tryon"]
- Returns tryon_result in the state dict
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from skyyrose.elite_studio.graph.nodes import tryon_node
from skyyrose.elite_studio.models import GenerationResult, TryOnResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_state(**overrides) -> dict:
    base = {
        "sku": "br-001",
        "view": "front",
        "enable_tryon": True,
        "tryon_category": "upper_body",
        "stage_timings": {},
        "generation_result": None,
        "tryon_result": None,
        "status": "running",
    }
    base.update(overrides)
    return base


def _successful_gen(output_path: str = "/output/br-001-model.jpg") -> GenerationResult:
    return GenerationResult(success=True, provider="gemini", output_path=output_path)


def _failed_gen() -> GenerationResult:
    return GenerationResult(success=False, error="generation failed")


# ---------------------------------------------------------------------------
# Skip conditions
# ---------------------------------------------------------------------------


class TestTryOnNodeSkip:
    def test_skips_when_no_generation_result(self) -> None:
        state = _make_state(generation_result=None)
        result = tryon_node(state)

        assert result["tryon_result"] is None
        assert "tryon" in result["stage_timings"]

    def test_skips_when_generation_failed(self) -> None:
        state = _make_state(generation_result=_failed_gen())
        result = tryon_node(state)

        assert result["tryon_result"] is None
        assert "tryon" in result["stage_timings"]

    def test_skips_when_no_garment_image_found(self) -> None:
        state = _make_state(generation_result=_successful_gen())

        with patch(
            "skyyrose.elite_studio.graph.nodes._find_garment_image",
            return_value=None,
        ):
            result = tryon_node(state)

        assert result["tryon_result"] is None
        assert "tryon" in result["stage_timings"]


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestTryOnNodeSuccess:
    def test_calls_agent_with_correct_args(self) -> None:
        gen = _successful_gen(output_path="/output/br-001-model.jpg")
        state = _make_state(
            generation_result=gen,
            tryon_category="upper_body",
        )

        mock_tryon_result = TryOnResult(
            success=True,
            output_path="/output/br-001/tryon/br-001-tryon-20260406.jpg",
            garment_sku="br-001",
            model_image_path="/output/br-001-model.jpg",
        )

        mock_agent = MagicMock()
        mock_agent.execute_tryon = AsyncMock(return_value=mock_tryon_result)

        with (
            patch(
                "skyyrose.elite_studio.graph.nodes._find_garment_image",
                return_value="/products/br-001/br-001-render-branding.webp",
            ),
            patch(
                "skyyrose.elite_studio.graph.nodes.TryOnAgent",
                return_value=mock_agent,
            ),
        ):
            result = tryon_node(state)

        mock_agent.execute_tryon.assert_called_once_with(
            garment_image_path="/products/br-001/br-001-render-branding.webp",
            model_image_path="/output/br-001-model.jpg",
            category="upper_body",
            garment_sku="br-001",
        )
        assert result["tryon_result"] is mock_tryon_result
        assert "tryon" in result["stage_timings"]

    def test_returns_failed_tryon_result_without_raising(self) -> None:
        """If TryOnAgent returns success=False, node should NOT raise — just pass it through."""
        gen = _successful_gen()
        state = _make_state(generation_result=gen)

        failed_result = TryOnResult(success=False, garment_sku="br-001", error="API timeout")
        mock_agent = MagicMock()
        mock_agent.execute_tryon = AsyncMock(return_value=failed_result)

        with (
            patch(
                "skyyrose.elite_studio.graph.nodes._find_garment_image",
                return_value="/some/garment.jpg",
            ),
            patch(
                "skyyrose.elite_studio.graph.nodes.TryOnAgent",
                return_value=mock_agent,
            ),
        ):
            result = tryon_node(state)

        assert result["tryon_result"].success is False
        assert result["tryon_result"].error == "API timeout"


# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------


class TestTryOnNodeTiming:
    def test_timing_always_recorded(self) -> None:
        state = _make_state(generation_result=None, stage_timings={"vision": 1.5})
        result = tryon_node(state)

        assert "tryon" in result["stage_timings"]
        assert result["stage_timings"]["tryon"] >= 0.0
        # Existing timings should be preserved
        assert result["stage_timings"]["vision"] == 1.5

    def test_existing_timings_preserved_on_success(self) -> None:
        gen = _successful_gen()
        state = _make_state(generation_result=gen, stage_timings={"generation": 3.2})

        mock_result = TryOnResult(success=True, garment_sku="br-001", output_path="/x.jpg")
        mock_agent = MagicMock()
        mock_agent.execute_tryon = AsyncMock(return_value=mock_result)

        with (
            patch("skyyrose.elite_studio.graph.nodes._find_garment_image", return_value="/g.jpg"),
            patch("skyyrose.elite_studio.graph.nodes.TryOnAgent", return_value=mock_agent),
        ):
            result = tryon_node(state)

        assert result["stage_timings"]["generation"] == 3.2
        assert "tryon" in result["stage_timings"]
