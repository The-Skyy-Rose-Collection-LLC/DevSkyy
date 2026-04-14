"""Tests for EliteStudioState TypedDict and helper functions."""

from __future__ import annotations


from skyyrose.elite_studio.graph.state import (
    EliteStudioState,
    create_initial_state,
    extract_production_result,
)
from skyyrose.elite_studio.models import ProductionResult
from skyyrose.elite_studio.tests.conftest import (
    make_generation_result,
    make_quality_verification,
    make_synthesized_vision,
)


class TestCreateInitialState:
    def test_required_fields_set(self):
        state = create_initial_state("br-001")
        assert state["sku"] == "br-001"
        assert state["view"] == "front"
        assert state["status"] == "running"

    def test_default_view(self):
        state = create_initial_state("br-001")
        assert state["view"] == "front"

    def test_custom_view(self):
        state = create_initial_state("br-001", view="back")
        assert state["view"] == "back"

    def test_compositor_disabled_by_default(self):
        state = create_initial_state("br-001")
        assert state["enable_compositor"] is False

    def test_compositor_can_be_enabled(self):
        state = create_initial_state("br-001", enable_compositor=True)
        assert state["enable_compositor"] is True

    def test_retry_count_starts_at_zero(self):
        state = create_initial_state("br-001")
        assert state["retry_count"] == 0

    def test_max_retries_default(self):
        state = create_initial_state("br-001")
        assert state["max_retries"] == 2

    def test_max_retries_custom(self):
        state = create_initial_state("br-001", max_retries=5)
        assert state["max_retries"] == 5

    def test_workflow_id_is_unique(self):
        s1 = create_initial_state("br-001")
        s2 = create_initial_state("br-001")
        assert s1["workflow_id"] != s2["workflow_id"]

    def test_stage_timings_empty(self):
        state = create_initial_state("br-001")
        assert state["stage_timings"] == {}

    def test_stage_results_are_none(self):
        state = create_initial_state("br-001")
        assert state["vision_result"] is None
        assert state["generation_result"] is None
        assert state["quality_result"] is None
        assert state["compositor_result"] is None

    def test_error_fields_are_empty(self):
        state = create_initial_state("br-001")
        assert state["error"] == ""
        assert state["failed_step"] == ""


class TestExtractProductionResult:
    def _success_state(self) -> EliteStudioState:
        gen = make_generation_result(success=True, output_path="/tmp/out.jpg")
        return EliteStudioState(
            sku="br-001",
            view="front",
            status="success",
            vision_result=make_synthesized_vision(success=True),
            generation_result=gen,
            quality_result=make_quality_verification(success=True),
            compositor_result=None,
            error="",
            failed_step="",
            retry_count=0,
            max_retries=2,
            workflow_id="test-id",
            stage_timings={"vision": 1.0},
            enable_compositor=False,
        )

    def test_returns_production_result(self):
        state = self._success_state()
        result = extract_production_result(state)
        assert isinstance(result, ProductionResult)

    def test_success_status_propagates(self):
        state = self._success_state()
        result = extract_production_result(state)
        assert result.status == "success"

    def test_output_path_from_generation_result(self):
        state = self._success_state()
        result = extract_production_result(state)
        assert result.output_path == "/tmp/out.jpg"

    def test_sku_and_view_propagate(self):
        state = self._success_state()
        result = extract_production_result(state)
        assert result.sku == "br-001"
        assert result.view == "front"

    def test_error_state_produces_empty_output(self):
        state = EliteStudioState(
            sku="br-002",
            view="front",
            status="error",
            error="Vision failed",
            failed_step="vision",
            generation_result=None,
            vision_result=None,
            quality_result=None,
            compositor_result=None,
            retry_count=0,
            max_retries=2,
            workflow_id="err-id",
            stage_timings={},
            enable_compositor=False,
        )
        result = extract_production_result(state)
        assert result.status == "error"
        assert result.output_path == ""
        assert result.error == "Vision failed"
        assert result.step == "vision"
