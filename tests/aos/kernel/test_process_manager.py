"""Tests for ProcessManager."""

from __future__ import annotations

import pytest

from aos.kernel.process_manager import ProcessManager, ProcessNotFoundError
from aos.kernel.types import ProcessPriority, ProcessStatus, SpawnRequest


@pytest.fixture
def pm() -> ProcessManager:
    return ProcessManager()


class TestSpawn:
    @pytest.mark.asyncio
    async def test_spawn_assigns_unique_pid(self, pm: ProcessManager):
        p1 = await pm.spawn(SpawnRequest(agent_type="commerce", prompt="a"))
        p2 = await pm.spawn(SpawnRequest(agent_type="content", prompt="b"))
        assert p1.pid != p2.pid
        assert p1.pid >= 1
        assert p2.pid == p1.pid + 1

    @pytest.mark.asyncio
    async def test_spawn_starts_pending(self, pm: ProcessManager):
        p = await pm.spawn(SpawnRequest(agent_type="x", prompt="y"))
        assert p.status == ProcessStatus.PENDING

    @pytest.mark.asyncio
    async def test_spawn_child_links_to_parent(self, pm: ProcessManager):
        parent = await pm.spawn(SpawnRequest(agent_type="orchestrator", prompt="root"))
        child = await pm.spawn(
            SpawnRequest(agent_type="worker", prompt="task", parent_pid=parent.pid)
        )
        parent_after = await pm.get(parent.pid)
        assert child.parent_pid == parent.pid
        assert child.pid in parent_after.children

    @pytest.mark.asyncio
    async def test_spawn_orphan_parent_raises(self, pm: ProcessManager):
        with pytest.raises(ProcessNotFoundError):
            await pm.spawn(SpawnRequest(agent_type="x", prompt="y", parent_pid=9999))


class TestLifecycle:
    @pytest.mark.asyncio
    async def test_transition_pending_to_running(self, pm: ProcessManager):
        p = await pm.spawn(SpawnRequest(agent_type="x", prompt="y"))
        await pm.transition(p.pid, ProcessStatus.READY)
        await pm.transition(p.pid, ProcessStatus.RUNNING)
        cur = await pm.get(p.pid)
        assert cur.status == ProcessStatus.RUNNING
        assert cur.started_at is not None

    @pytest.mark.asyncio
    async def test_pause_resume(self, pm: ProcessManager):
        p = await pm.spawn(SpawnRequest(agent_type="x", prompt="y"))
        await pm.transition(p.pid, ProcessStatus.READY)
        await pm.transition(p.pid, ProcessStatus.RUNNING)
        await pm.pause(p.pid)
        assert (await pm.get(p.pid)).status == ProcessStatus.PAUSED
        await pm.resume(p.pid)
        assert (await pm.get(p.pid)).status == ProcessStatus.RUNNING

    @pytest.mark.asyncio
    async def test_kill_terminates(self, pm: ProcessManager):
        p = await pm.spawn(SpawnRequest(agent_type="x", prompt="y"))
        await pm.transition(p.pid, ProcessStatus.READY)
        await pm.transition(p.pid, ProcessStatus.RUNNING)
        await pm.kill(p.pid, reason="user_requested")
        cur = await pm.get(p.pid)
        assert cur.status == ProcessStatus.FAILED
        assert "user_requested" in (cur.error or "")

    @pytest.mark.asyncio
    async def test_complete_with_result(self, pm: ProcessManager):
        p = await pm.spawn(SpawnRequest(agent_type="x", prompt="y"))
        await pm.transition(p.pid, ProcessStatus.READY)
        await pm.transition(p.pid, ProcessStatus.RUNNING)
        await pm.complete(p.pid, result={"data": 42})
        cur = await pm.get(p.pid)
        assert cur.status == ProcessStatus.COMPLETED
        assert cur.result == {"data": 42}


class TestQuery:
    @pytest.mark.asyncio
    async def test_list_processes(self, pm: ProcessManager):
        await pm.spawn(SpawnRequest(agent_type="a", prompt="1"))
        await pm.spawn(SpawnRequest(agent_type="b", prompt="2"))
        all_procs = await pm.list_processes()
        assert len(all_procs) == 2

    @pytest.mark.asyncio
    async def test_list_filters_by_status(self, pm: ProcessManager):
        p1 = await pm.spawn(SpawnRequest(agent_type="a", prompt="1"))
        p2 = await pm.spawn(SpawnRequest(agent_type="b", prompt="2"))
        await pm.transition(p1.pid, ProcessStatus.READY)
        await pm.transition(p1.pid, ProcessStatus.RUNNING)
        running = await pm.list_processes(status=ProcessStatus.RUNNING)
        pending = await pm.list_processes(status=ProcessStatus.PENDING)
        assert len(running) == 1
        assert running[0].pid == p1.pid
        assert len(pending) == 1
        assert pending[0].pid == p2.pid

    @pytest.mark.asyncio
    async def test_get_missing_raises(self, pm: ProcessManager):
        with pytest.raises(ProcessNotFoundError):
            await pm.get(9999)

    @pytest.mark.asyncio
    async def test_count_alive(self, pm: ProcessManager):
        p1 = await pm.spawn(SpawnRequest(agent_type="a", prompt="1"))
        await pm.spawn(SpawnRequest(agent_type="b", prompt="2"))
        await pm.transition(p1.pid, ProcessStatus.READY)
        await pm.transition(p1.pid, ProcessStatus.RUNNING)
        await pm.complete(p1.pid, result=None)
        assert await pm.count_alive() == 1


class TestBudget:
    @pytest.mark.asyncio
    async def test_record_spend(self, pm: ProcessManager):
        p = await pm.spawn(SpawnRequest(agent_type="x", prompt="y", budget_usd=5.0))
        await pm.record_spend(p.pid, 1.5)
        await pm.record_spend(p.pid, 2.0)
        cur = await pm.get(p.pid)
        assert cur.spent_usd == 3.5

    @pytest.mark.asyncio
    async def test_over_budget_detection(self, pm: ProcessManager):
        p = await pm.spawn(SpawnRequest(agent_type="x", prompt="y", budget_usd=1.0))
        await pm.record_spend(p.pid, 1.5)
        cur = await pm.get(p.pid)
        assert cur.is_over_budget
