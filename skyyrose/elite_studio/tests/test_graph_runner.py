"""Tests for run_single and run_batch — graph runner public API."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from skyyrose.elite_studio.graph.builder import GraphConfig
from skyyrose.elite_studio.graph.runner import run_batch, run_single
from skyyrose.elite_studio.models import ProductionResult
from skyyrose.elite_studio.tests.conftest import (
    make_generation_result,
    make_quality_verification,
    make_synthesized_vision,
)


def _mock_graph(status="success", output_path="/tmp/out.jpg"):
    """Build a mock compiled graph that returns a predictable state."""
    vision = make_synthesized_vision(success=True)
    gen = make_generation_result(success=(status == "success"), output_path=output_path)
    qc = make_quality_verification(success=True, recommendation="approve")

    final_state = {
        "sku": "br-001",
        "view": "front",
        "status": status,
        "vision_result": vision,
        "generation_result": gen if status == "success" else None,
        "quality_result": qc if status == "success" else None,
        "compositor_result": None,
        "error": "" if status == "success" else "Mock error",
        "failed_step": "" if status == "success" else "generation",
        "retry_count": 0,
        "max_retries": 2,
        "workflow_id": "test-wf-id",
        "stage_timings": {"vision": 0.5, "generation": 1.2, "quality": 0.8},
        "enable_compositor": False,
    }
    mock = MagicMock()
    mock.invoke.return_value = final_state
    return mock


class TestRunSingle:
    def test_returns_production_result(self):
        graph = _mock_graph(status="success")
        result = run_single("br-001", graph=graph)
        assert isinstance(result, ProductionResult)

    def test_success_status_propagates(self):
        graph = _mock_graph(status="success")
        result = run_single("br-001", graph=graph)
        assert result.status == "success"

    def test_output_path_set_on_success(self):
        graph = _mock_graph(status="success", output_path="/tmp/br-001.jpg")
        result = run_single("br-001", graph=graph)
        assert result.output_path == "/tmp/br-001.jpg"

    def test_error_status_propagates(self):
        graph = _mock_graph(status="error")
        result = run_single("br-001", graph=graph)
        assert result.status == "error"

    def test_sku_and_view_set_correctly(self):
        graph = _mock_graph()
        run_single("lh-001", view="back", graph=graph)
        # The mock returns sku=br-001 so we check the graph was invoked correctly
        call_state = graph.invoke.call_args[0][0]
        assert call_state["sku"] == "lh-001"
        assert call_state["view"] == "back"

    def test_uses_config_max_retries(self):
        cfg = GraphConfig(max_retries=5)
        graph = _mock_graph()
        run_single("br-001", config=cfg, graph=graph)
        call_state = graph.invoke.call_args[0][0]
        assert call_state["max_retries"] == 5

    def test_builds_graph_when_none_provided(self):
        """run_single builds a graph if none is passed (smoke test)."""
        # Just verify it doesn't crash calling build_graph
        with patch("skyyrose.elite_studio.graph.runner.build_graph") as mock_build:
            mock_build.return_value = _mock_graph()
            result = run_single("br-001")
            mock_build.assert_called_once()
            assert isinstance(result, ProductionResult)


class TestRunBatch:
    def test_returns_list_of_results(self):
        graph = _mock_graph()
        results = run_batch(skus=["br-001", "br-002"], graph=graph)
        assert len(results) == 2
        assert all(isinstance(r, ProductionResult) for r in results)

    def test_skips_existing_when_enabled(self, tmp_path):
        # Create a fake output file so br-001 is "already generated"
        out_dir = tmp_path / "br-001"
        out_dir.mkdir()
        (out_dir / "br-001-model-front-gemini.jpg").touch()

        graph = _mock_graph()
        with patch("skyyrose.elite_studio.graph.runner.OUTPUT_DIR", tmp_path):
            results = run_batch(skus=["br-001"], graph=graph, skip_existing=True)

        assert results[0].status == "skipped"
        graph.invoke.assert_not_called()

    def test_does_not_skip_when_disabled(self, tmp_path):
        out_dir = tmp_path / "br-001"
        out_dir.mkdir()
        (out_dir / "br-001-model-front-gemini.jpg").touch()

        graph = _mock_graph()
        with patch("skyyrose.elite_studio.graph.runner.OUTPUT_DIR", tmp_path):
            run_batch(skus=["br-001"], graph=graph, skip_existing=False)

        graph.invoke.assert_called_once()

    def test_no_batch_delay_on_single_item(self):
        graph = _mock_graph()
        with patch("skyyrose.elite_studio.graph.runner.time") as mock_time:
            run_batch(skus=["br-001"], graph=graph)
            mock_time.sleep.assert_not_called()

    def test_batch_delay_between_items(self):
        graph = _mock_graph()
        with patch("skyyrose.elite_studio.graph.runner.time") as mock_time:
            run_batch(skus=["br-001", "br-002"], graph=graph)
            mock_time.sleep.assert_called_once()

    def test_empty_skus_returns_empty(self):
        results = run_batch(skus=[])
        assert results == []
