"""Tests for graph builder — topology assembly and compilation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from skyyrose.elite_studio.graph.builder import GraphConfig, build_graph
from skyyrose.elite_studio.graph.state import create_initial_state
from skyyrose.elite_studio.tests.conftest import (
    make_generation_result,
    make_quality_verification,
    make_synthesized_vision,
)


class TestGraphConfig:
    def test_defaults(self):
        cfg = GraphConfig()
        assert cfg.max_retries == 2
        assert cfg.enable_compositor is False

    def test_custom_values(self):
        cfg = GraphConfig(max_retries=5, enable_compositor=True)
        assert cfg.max_retries == 5
        assert cfg.enable_compositor is True

    def test_immutable(self):
        cfg = GraphConfig()
        with pytest.raises((AttributeError, TypeError)):
            cfg.max_retries = 99  # type: ignore[misc]


class TestBuildGraph:
    def test_returns_compiled_graph(self):
        graph = build_graph()
        # CompiledGraph from LangGraph has an invoke method
        assert hasattr(graph, "invoke")

    def test_accepts_none_config(self):
        graph = build_graph(None)
        assert hasattr(graph, "invoke")

    def test_accepts_custom_config(self):
        cfg = GraphConfig(max_retries=3, enable_compositor=True)
        graph = build_graph(cfg)
        assert hasattr(graph, "invoke")


class TestGraphIntegration:
    """Full graph invocation with mocked agents."""

    def _mock_agents(
        self,
        vision_success=True,
        gen_success=True,
        qc_recommendation="approve",
    ):
        """Return a context manager that mocks all 3 core agents."""
        vision = make_synthesized_vision(success=vision_success)
        gen = make_generation_result(success=gen_success)
        qc = make_quality_verification(success=True, recommendation=qc_recommendation)

        mock_vision = MagicMock()
        mock_vision.analyze.return_value = vision
        mock_gen = MagicMock()
        mock_gen.generate.return_value = gen
        mock_qc = MagicMock()
        mock_qc.verify.return_value = qc

        return mock_vision, mock_gen, mock_qc

    def test_happy_path_ends_in_success(self):
        mv, mg, mq = self._mock_agents()
        graph = build_graph()
        state = create_initial_state("br-001")

        with (
            patch("skyyrose.elite_studio.graph.nodes.VisionAgent", return_value=mv),
            patch("skyyrose.elite_studio.graph.nodes.GeneratorAgent", return_value=mg),
            patch("skyyrose.elite_studio.graph.nodes.QualityAgent", return_value=mq),
        ):
            final = graph.invoke(state)

        assert final["status"] == "success"

    def test_vision_failure_ends_in_error(self):
        mv, mg, mq = self._mock_agents(vision_success=False)
        graph = build_graph()
        state = create_initial_state("br-001")

        with (
            patch("skyyrose.elite_studio.graph.nodes.VisionAgent", return_value=mv),
            patch("skyyrose.elite_studio.graph.nodes.GeneratorAgent", return_value=mg),
            patch("skyyrose.elite_studio.graph.nodes.QualityAgent", return_value=mq),
        ):
            final = graph.invoke(state)

        assert final["status"] == "error"
        assert final["failed_step"] == "vision"

    def test_generation_failure_ends_in_error(self):
        mv, mg, mq = self._mock_agents(gen_success=False)
        graph = build_graph()
        state = create_initial_state("br-001")

        with (
            patch("skyyrose.elite_studio.graph.nodes.VisionAgent", return_value=mv),
            patch("skyyrose.elite_studio.graph.nodes.GeneratorAgent", return_value=mg),
            patch("skyyrose.elite_studio.graph.nodes.QualityAgent", return_value=mq),
        ):
            final = graph.invoke(state)

        assert final["status"] == "error"
        assert final["failed_step"] == "generation"

    def test_stage_timings_populated(self):
        mv, mg, mq = self._mock_agents()
        graph = build_graph()
        state = create_initial_state("br-001")

        with (
            patch("skyyrose.elite_studio.graph.nodes.VisionAgent", return_value=mv),
            patch("skyyrose.elite_studio.graph.nodes.GeneratorAgent", return_value=mg),
            patch("skyyrose.elite_studio.graph.nodes.QualityAgent", return_value=mq),
        ):
            final = graph.invoke(state)

        timings = final["stage_timings"]
        assert "vision" in timings
        assert "generation" in timings
        assert "quality" in timings
