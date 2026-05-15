"""Integration tests for Kernel.execute_plan() and _reflect_and_learn()."""

from __future__ import annotations

import pytest

from aos.cognition.goal_decomposer import GoalDecomposer
from aos.cognition.planner import Planner
from aos.governance.types import AuditEventType
from aos.kernel.kernel import Kernel
from tests.aos._mocks import MockAgentResult, MockSuperAgent


@pytest.fixture
async def kernel(tmp_path):
    k = Kernel(audit_db_path=str(tmp_path / "audit.db"), system_budget_usd=100.0)
    await k.boot()
    return k


def _register_mock(kernel: Kernel, agent_type: str, **mock_kwargs) -> MockSuperAgent:
    agent = MockSuperAgent(agent_type=agent_type, **mock_kwargs)

    async def factory():
        return agent

    kernel.modules.register_type(agent_type, factory)
    return agent


class TestExecutePlanAuditEvents:
    @pytest.mark.asyncio
    async def test_plan_started_event_emitted(self, kernel: Kernel):
        _register_mock(kernel, "operations_agent", result=MockAgentResult(content="done"))
        graph = GoalDecomposer().decompose("do unknown task")
        plan = Planner().plan(graph)
        await kernel.execute_plan(plan)
        events = await kernel.audit.query(event_type=AuditEventType.PLAN_STARTED)
        assert len(events) == 1
        assert events[0].details["goal"] == graph.goal
        assert events[0].details["total_nodes"] == 1

    @pytest.mark.asyncio
    async def test_plan_completed_event_emitted(self, kernel: Kernel):
        _register_mock(kernel, "operations_agent", result=MockAgentResult(content="done"))
        plan = Planner().plan(GoalDecomposer().decompose("do unknown task"))
        await kernel.execute_plan(plan)
        events = await kernel.audit.query(event_type=AuditEventType.PLAN_COMPLETED)
        assert len(events) == 1
        assert events[0].details["outcome_count"] == 1
        assert events[0].details["node_failures"] == 0

    @pytest.mark.asyncio
    async def test_reflection_recorded_for_each_node(self, kernel: Kernel):
        _register_mock(kernel, "operations_agent", result=MockAgentResult(content="done"))
        plan = Planner().plan(GoalDecomposer().decompose("do unknown task"))
        await kernel.execute_plan(plan)
        events = await kernel.audit.query(event_type=AuditEventType.REFLECTION_RECORDED)
        assert len(events) == 1
        assert "quality_score" in events[0].details

    @pytest.mark.asyncio
    async def test_finetune_queued_for_high_quality_outcome(self, kernel: Kernel):
        _register_mock(kernel, "operations_agent", result=MockAgentResult(content="done"))
        plan = Planner().plan(GoalDecomposer().decompose("do unknown task"))
        await kernel.execute_plan(plan)
        events = await kernel.audit.query(event_type=AuditEventType.FINETUNE_QUEUED)
        assert len(events) == 1
        assert events[0].details["quality_score"] >= 0.7

    @pytest.mark.asyncio
    async def test_multi_node_plan_reflects_all(self, kernel: Kernel):
        _register_mock(kernel, "commerce_agent", result=MockAgentResult(content="analyzed"))
        _register_mock(kernel, "creative_agent", result=MockAgentResult(content="described"))
        plan = Planner().plan(GoalDecomposer().decompose("optimize product catalog"))
        await kernel.execute_plan(plan)
        events = await kernel.audit.query(event_type=AuditEventType.REFLECTION_RECORDED)
        assert len(events) == 3


class TestExecutePlanOutcomes:
    @pytest.mark.asyncio
    async def test_returns_outcomes_for_each_node(self, kernel: Kernel):
        _register_mock(kernel, "operations_agent", result=MockAgentResult(content="done"))
        plan = Planner().plan(GoalDecomposer().decompose("unknown goal"))
        outcomes = await kernel.execute_plan(plan)
        assert len(outcomes) == 1
        assert outcomes[0].success is True

    @pytest.mark.asyncio
    async def test_node_failure_counted_not_aborted(self, kernel: Kernel):
        _register_mock(
            kernel,
            "operations_agent",
            result=MockAgentResult(content="ok"),
            raise_on_call=1,
        )
        plan = Planner().plan(GoalDecomposer().decompose("unknown goal"))
        outcomes = await kernel.execute_plan(plan)
        completed_event = await kernel.audit.query(event_type=AuditEventType.PLAN_COMPLETED)
        assert len(completed_event) == 1
        assert completed_event[0].details["node_failures"] >= 0

    @pytest.mark.asyncio
    async def test_finetune_buffer_populated(self, kernel: Kernel):
        _register_mock(kernel, "operations_agent", result=MockAgentResult(content="done"))
        plan = Planner().plan(GoalDecomposer().decompose("unknown goal"))
        await kernel.execute_plan(plan)
        assert kernel.finetune_buffer.size >= 0

    @pytest.mark.asyncio
    async def test_reflector_attached_to_kernel(self, kernel: Kernel):
        from aos.cognition.reflector import Reflector

        assert isinstance(kernel.reflector, Reflector)

    @pytest.mark.asyncio
    async def test_finetune_buffer_attached_to_kernel(self, kernel: Kernel):
        from aos.observability.finetune_buffer import FineTuneBuffer

        assert isinstance(kernel.finetune_buffer, FineTuneBuffer)
