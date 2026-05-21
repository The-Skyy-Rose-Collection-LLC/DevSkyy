"""Tests for the Kernel coordinator."""

from __future__ import annotations

import pytest

from aos.governance.types import AuditEventType
from aos.kernel.kernel import Kernel
from aos.kernel.types import ProcessStatus, SpawnRequest


@pytest.fixture
async def kernel(tmp_path) -> Kernel:
    k = Kernel(audit_db_path=str(tmp_path / "audit.db"))
    await k.boot()
    return k


class TestBoot:
    @pytest.mark.asyncio
    async def test_boot_logs_system_event(self, tmp_path):
        k = Kernel(audit_db_path=str(tmp_path / "audit.db"))
        assert not k.is_booted
        await k.boot()
        assert k.is_booted
        events = await k.audit.query(event_type=AuditEventType.SYSTEM_BOOT)
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_double_boot_is_idempotent(self, tmp_path):
        k = Kernel(audit_db_path=str(tmp_path / "audit.db"))
        await k.boot()
        await k.boot()
        events = await k.audit.query(event_type=AuditEventType.SYSTEM_BOOT)
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_spawn_before_boot_raises(self, tmp_path):
        k = Kernel(audit_db_path=str(tmp_path / "audit.db"))
        with pytest.raises(RuntimeError, match="not booted"):
            await k.spawn(SpawnRequest(agent_type="x", prompt="y"))


class TestSpawnAudit:
    @pytest.mark.asyncio
    async def test_spawn_creates_audit_entry(self, kernel: Kernel):
        proc = await kernel.spawn(
            SpawnRequest(agent_type="commerce", prompt="task", budget_usd=2.5)
        )
        entries = await kernel.audit.query(event_type=AuditEventType.PROCESS_SPAWN)
        assert len(entries) == 1
        assert entries[0].target_pid == proc.pid
        assert entries[0].details["agent_type"] == "commerce"
        assert entries[0].details["budget_usd"] == 2.5

    @pytest.mark.asyncio
    async def test_spawn_with_parent_audits_actor(self, kernel: Kernel):
        parent = await kernel.spawn(SpawnRequest(agent_type="orchestrator", prompt="root"))
        child = await kernel.spawn(
            SpawnRequest(agent_type="worker", prompt="sub", parent_pid=parent.pid)
        )
        entries = await kernel.audit.query(
            event_type=AuditEventType.PROCESS_SPAWN, target_pid=child.pid
        )
        assert entries[0].actor_pid == parent.pid


class TestLifecycleAudit:
    @pytest.mark.asyncio
    async def test_complete_audits(self, kernel: Kernel):
        proc = await kernel.spawn(SpawnRequest(agent_type="x", prompt="y"))
        await kernel.transition(proc.pid, ProcessStatus.READY)
        await kernel.transition(proc.pid, ProcessStatus.RUNNING)
        await kernel.complete(proc.pid, result={"ok": True})
        entries = await kernel.audit.query(event_type=AuditEventType.PROCESS_COMPLETE)
        assert len(entries) == 1
        assert entries[0].target_pid == proc.pid

    @pytest.mark.asyncio
    async def test_first_run_emits_start_not_resume(self, kernel: Kernel):
        proc = await kernel.spawn(SpawnRequest(agent_type="x", prompt="y"))
        await kernel.transition(proc.pid, ProcessStatus.READY)
        await kernel.transition(proc.pid, ProcessStatus.RUNNING)
        starts = await kernel.audit.query(event_type=AuditEventType.PROCESS_START)
        resumes = await kernel.audit.query(event_type=AuditEventType.PROCESS_RESUME)
        assert len(starts) == 1
        assert starts[0].target_pid == proc.pid
        assert len(resumes) == 0

    @pytest.mark.asyncio
    async def test_pause_then_resume_emits_resume(self, kernel: Kernel):
        proc = await kernel.spawn(SpawnRequest(agent_type="x", prompt="y"))
        await kernel.transition(proc.pid, ProcessStatus.READY)
        await kernel.transition(proc.pid, ProcessStatus.RUNNING)
        await kernel.transition(proc.pid, ProcessStatus.PAUSED)
        await kernel.transition(proc.pid, ProcessStatus.RUNNING)
        resumes = await kernel.audit.query(event_type=AuditEventType.PROCESS_RESUME)
        starts = await kernel.audit.query(event_type=AuditEventType.PROCESS_START)
        assert len(resumes) == 1
        assert len(starts) == 1

    @pytest.mark.asyncio
    async def test_kill_audits(self, kernel: Kernel):
        proc = await kernel.spawn(SpawnRequest(agent_type="x", prompt="y"))
        await kernel.transition(proc.pid, ProcessStatus.READY)
        await kernel.transition(proc.pid, ProcessStatus.RUNNING)
        await kernel.kill(proc.pid, reason="budget_exceeded")
        entries = await kernel.audit.query(event_type=AuditEventType.PROCESS_KILL)
        assert len(entries) == 1
        assert entries[0].details["reason"] == "budget_exceeded"


class TestBudgetAudit:
    @pytest.mark.asyncio
    async def test_over_budget_emits_event(self, kernel: Kernel):
        proc = await kernel.spawn(SpawnRequest(agent_type="x", prompt="y", budget_usd=1.0))
        await kernel.record_spend(proc.pid, 0.5)
        events_under = await kernel.audit.query(event_type=AuditEventType.BUDGET_EXCEEDED)
        assert len(events_under) == 0

        await kernel.record_spend(proc.pid, 0.8)
        events_over = await kernel.audit.query(event_type=AuditEventType.BUDGET_EXCEEDED)
        assert len(events_over) == 1
        assert events_over[0].details["spent_usd"] == 1.3
        assert events_over[0].details["budget_usd"] == 1.0


class TestCorrelationId:
    @pytest.mark.asyncio
    async def test_all_lifecycle_events_share_correlation_id(self, kernel: Kernel):
        proc = await kernel.spawn(SpawnRequest(agent_type="x", prompt="y"))
        await kernel.transition(proc.pid, ProcessStatus.READY)
        await kernel.transition(proc.pid, ProcessStatus.RUNNING)
        await kernel.complete(proc.pid, result=None)

        entries = await kernel.audit.query(correlation_id=proc.correlation_id)
        # spawn + complete (transitions to READY/RUNNING aren't mapped to audit events)
        assert len(entries) >= 2
        assert all(e.correlation_id == proc.correlation_id for e in entries)


class TestShutdown:
    @pytest.mark.asyncio
    async def test_shutdown_logs(self, kernel: Kernel):
        await kernel.shutdown()
        assert not kernel.is_booted
        events = await kernel.audit.query(event_type=AuditEventType.SYSTEM_SHUTDOWN)
        assert len(events) == 1
