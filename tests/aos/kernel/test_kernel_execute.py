"""End-to-end tests for kernel.execute() — Phase 3 task execution."""

from __future__ import annotations

import pytest

from aos.governance.types import AuditEventType
from aos.kernel.kernel import Kernel
from aos.kernel.types import ProcessStatus, SpawnRequest
from aos.runtime.executor import NoFactoryError
from aos.runtime.types import ResourceLimits
from tests.aos._mocks import MockAgentResult, MockHealEntry, MockSuperAgent


@pytest.fixture
async def kernel(tmp_path) -> Kernel:
    k = Kernel(audit_db_path=str(tmp_path / "audit.db"), system_budget_usd=10.0)
    await k.boot()
    yield k
    await k.close()


class TestSuccessfulRun:
    @pytest.mark.asyncio
    async def test_execute_runs_agent_end_to_end(self, kernel: Kernel):
        agent = MockSuperAgent(
            agent_type="commerce",
            result=MockAgentResult(content="price updated", cost_usd=0.03, latency_ms=85.0),
        )
        await kernel.register_agent_factory("commerce", lambda: _async(agent))
        outcome = await kernel.execute(
            SpawnRequest(agent_type="commerce", prompt="bump br-001 to $285")
        )
        assert outcome.success
        assert outcome.agent_run.raw_result.content == "price updated"
        assert agent.executed_prompts == ["bump br-001 to $285"]
        final = await kernel.processes.get(outcome.pid)
        assert final.status == ProcessStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_logs_lifecycle(self, kernel: Kernel):
        agent = MockSuperAgent(result=MockAgentResult(content="ok"))
        await kernel.register_agent_factory("commerce", lambda: _async(agent))
        outcome = await kernel.execute(SpawnRequest(agent_type="commerce", prompt="x"))
        spawns = await kernel.audit.query(event_type=AuditEventType.PROCESS_SPAWN)
        completes = await kernel.audit.query(event_type=AuditEventType.PROCESS_COMPLETE)
        assert any(e.target_pid == outcome.pid for e in spawns)
        assert any(e.target_pid == outcome.pid for e in completes)


class TestFactoryMissing:
    @pytest.mark.asyncio
    async def test_unknown_agent_type_raises(self, kernel: Kernel):
        with pytest.raises(NoFactoryError, match="(?i)no agent factory"):
            await kernel.execute(SpawnRequest(agent_type="ghost", prompt="x"))
        # Process should be marked FAILED even though we raised
        all_procs = await kernel.processes.list_processes()
        assert all_procs
        assert all_procs[0].status == ProcessStatus.FAILED


class TestFailureCapture:
    @pytest.mark.asyncio
    async def test_agent_exception_marks_failed(self, kernel: Kernel):
        agent = MockSuperAgent(raise_on_call=99)
        await kernel.register_agent_factory("commerce", lambda: _async(agent))
        outcome = await kernel.execute(SpawnRequest(agent_type="commerce", prompt="x"))
        assert not outcome.success
        assert "RuntimeError" in (outcome.error or "")
        final = await kernel.processes.get(outcome.pid)
        assert final.status == ProcessStatus.FAILED

    @pytest.mark.asyncio
    async def test_agent_result_with_error_field(self, kernel: Kernel):
        agent = MockSuperAgent(result=MockAgentResult(error="rate_limited"))
        await kernel.register_agent_factory("commerce", lambda: _async(agent))
        outcome = await kernel.execute(SpawnRequest(agent_type="commerce", prompt="x"))
        assert not outcome.success
        assert outcome.error == "rate_limited"


class TestHealJournalAudit:
    @pytest.mark.asyncio
    async def test_each_retry_emits_audit_row(self, kernel: Kernel):
        agent = MockSuperAgent(
            heal_entries_to_add=[
                MockHealEntry(category="external", action_taken="retry_backoff", succeeded=True),
                MockHealEntry(category="config", action_taken="reload_env", succeeded=False),
            ]
        )
        await kernel.register_agent_factory("imagery", lambda: _async(agent))
        outcome = await kernel.execute(SpawnRequest(agent_type="imagery", prompt="x"))
        retries = await kernel.audit.query(event_type=AuditEventType.PROCESS_RETRY)
        assert len(retries) == 2
        cats = {r.details["category"] for r in retries}
        assert {"external", "config"}.issubset(cats)
        assert len(outcome.heal_entries) == 2


class TestLearningIntegration:
    @pytest.mark.asyncio
    async def test_learning_module_receives_completed_trace(self, kernel: Kernel):
        agent = MockSuperAgent(
            agent_type="commerce",
            result=MockAgentResult(content="ok", cost_usd=0.05),
        )
        await kernel.register_agent_factory("commerce", lambda: _async(agent))
        # Buffer up enough completions to force a flush
        for _ in range(10):
            await kernel.execute(SpawnRequest(agent_type="commerce", prompt="x"))
        assert agent.learning_module is not None
        assert len(agent.learning_module.records) == 10
        assert agent.learning_module.records[0]["cost_usd"] == 0.05

    @pytest.mark.asyncio
    async def test_shutdown_flushes_pending_learning(self, kernel: Kernel):
        agent = MockSuperAgent(agent_type="commerce", result=MockAgentResult(content="ok"))
        await kernel.register_agent_factory("commerce", lambda: _async(agent))
        # Only 3 runs — buffer not full, no flush
        for _ in range(3):
            await kernel.execute(SpawnRequest(agent_type="commerce", prompt="x"))
        assert len(agent.learning_module.records) == 0
        await kernel.shutdown()
        assert len(agent.learning_module.records) == 3
        flushed = await kernel.audit.query(event_type=AuditEventType.LEARNING_FLUSHED)
        assert len(flushed) == 1
        assert flushed[0].details["trace_count"] == 3


class TestContainerBoundary:
    @pytest.mark.asyncio
    async def test_container_timeout_marks_failed(self, kernel: Kernel):
        import asyncio

        class SlowAgent:
            agent_type = "slow"
            _initialized = False
            learning_module = None

            async def initialize(self):
                self._initialized = True

            async def execute(self, _prompt, **_):
                await asyncio.sleep(5.0)
                return MockAgentResult(content="never")

        agent = SlowAgent()
        await kernel.register_agent_factory("slow", lambda: _async(agent))
        outcome = await kernel.execute(
            SpawnRequest(agent_type="slow", prompt="x"),
            limits=ResourceLimits(max_runtime_seconds=0.1),
        )
        assert not outcome.success
        assert outcome.container_result.timed_out
        final = await kernel.processes.get(outcome.pid)
        assert final.status == ProcessStatus.FAILED


class TestRegistration:
    @pytest.mark.asyncio
    async def test_register_emits_audit(self, kernel: Kernel):
        await kernel.register_agent_factory("commerce", lambda: _async(MockSuperAgent()))
        entries = await kernel.audit.query(event_type=AuditEventType.AGENT_REGISTERED)
        assert len(entries) == 1
        assert entries[0].details["agent_type"] == "commerce"


async def _async(value):
    return value
