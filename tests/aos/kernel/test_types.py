"""Tests for AOS kernel domain types."""

from __future__ import annotations

import pytest

from aos.kernel.types import (
    AgentProcess,
    ProcessPriority,
    ProcessStatus,
    SpawnRequest,
    can_transition,
    is_terminal,
)


class TestProcessStatusTransitions:
    def test_pending_can_transition_to_ready(self):
        assert can_transition(ProcessStatus.PENDING, ProcessStatus.READY)

    def test_pending_cannot_skip_to_running(self):
        assert not can_transition(ProcessStatus.PENDING, ProcessStatus.RUNNING)

    def test_running_can_pause(self):
        assert can_transition(ProcessStatus.RUNNING, ProcessStatus.PAUSED)

    def test_paused_can_resume(self):
        assert can_transition(ProcessStatus.PAUSED, ProcessStatus.RUNNING)

    def test_completed_can_only_become_zombie(self):
        assert can_transition(ProcessStatus.COMPLETED, ProcessStatus.ZOMBIE)
        assert not can_transition(ProcessStatus.COMPLETED, ProcessStatus.RUNNING)

    def test_zombie_is_terminal(self):
        assert is_terminal(ProcessStatus.ZOMBIE)
        assert is_terminal(ProcessStatus.COMPLETED)
        assert is_terminal(ProcessStatus.FAILED)
        assert not is_terminal(ProcessStatus.RUNNING)


class TestAgentProcess:
    def test_create_default_pending(self):
        p = AgentProcess(pid=1, agent_type="commerce", prompt="hi")
        assert p.status == ProcessStatus.PENDING
        assert p.priority == ProcessPriority.NORMAL
        assert p.spent_usd == 0.0
        assert p.is_alive

    def test_immutable_cannot_mutate(self):
        p = AgentProcess(pid=1, agent_type="commerce", prompt="hi")
        with pytest.raises((ValueError, TypeError)):
            p.status = ProcessStatus.RUNNING

    def test_with_status_returns_new_instance(self):
        p = AgentProcess(pid=1, agent_type="commerce", prompt="hi")
        p2 = p.with_status(ProcessStatus.READY)
        assert p.status == ProcessStatus.PENDING
        assert p2.status == ProcessStatus.READY
        assert p is not p2

    def test_with_status_invalid_raises(self):
        p = AgentProcess(pid=1, agent_type="commerce", prompt="hi")
        with pytest.raises(ValueError, match="Invalid transition"):
            p.with_status(ProcessStatus.RUNNING)

    def test_running_sets_started_at(self):
        p = AgentProcess(pid=1, agent_type="x", prompt="y")
        p = p.with_status(ProcessStatus.READY).with_status(ProcessStatus.RUNNING)
        assert p.started_at is not None

    def test_terminal_sets_completed_at(self):
        p = AgentProcess(pid=1, agent_type="x", prompt="y")
        p = (
            p.with_status(ProcessStatus.READY)
            .with_status(ProcessStatus.RUNNING)
            .with_status(ProcessStatus.COMPLETED, result={"ok": True})
        )
        assert p.completed_at is not None
        assert p.result == {"ok": True}

    def test_add_child_appends(self):
        p = AgentProcess(pid=1, agent_type="x", prompt="y")
        p2 = p.add_child(42).add_child(43)
        assert p2.children == (42, 43)
        assert p.children == ()

    def test_add_spend_accumulates(self):
        p = AgentProcess(pid=1, agent_type="x", prompt="y", budget_usd=10.0)
        p = p.add_spend(3.0).add_spend(4.5)
        assert p.spent_usd == 7.5
        assert not p.is_over_budget

    def test_over_budget_flag(self):
        p = AgentProcess(pid=1, agent_type="x", prompt="y", budget_usd=1.0)
        p = p.add_spend(1.5)
        assert p.is_over_budget


class TestSpawnRequest:
    def test_minimal_spawn(self):
        req = SpawnRequest(agent_type="content", prompt="write blog")
        assert req.priority == ProcessPriority.NORMAL
        assert req.budget_usd == 1.0
        assert req.parent_pid is None
