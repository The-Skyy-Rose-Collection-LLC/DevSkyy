"""Tests for SuperAgentAdapter."""

from __future__ import annotations

import pytest

from aos.adapters.superagent_adapter import SuperAgentAdapter
from tests.aos._mocks import MockAgentResult, MockHealEntry, MockSuperAgent


class TestBasicRun:
    @pytest.mark.asyncio
    async def test_successful_execution(self):
        agent = MockSuperAgent(
            agent_type="commerce",
            result=MockAgentResult(content="ok", cost_usd=0.05, latency_ms=120.0),
        )
        adapter = SuperAgentAdapter(agent)
        run = await adapter.run("update br-001 price")
        assert run.success
        assert run.agent_type == "commerce"
        assert run.raw_result.content == "ok"
        assert run.metadata["cost_usd"] == 0.05
        assert run.metadata["latency_ms"] == 120.0
        assert run.error is None

    @pytest.mark.asyncio
    async def test_initialize_called(self):
        agent = MockSuperAgent()
        adapter = SuperAgentAdapter(agent)
        assert not agent._initialized
        await adapter.run("hi")
        assert agent._initialized

    @pytest.mark.asyncio
    async def test_initialize_not_repeated(self):
        agent = MockSuperAgent()
        adapter = SuperAgentAdapter(agent)
        await adapter.run("first")
        agent._initialized = True
        await adapter.run("second")
        assert agent._call_count == 2


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_agent_exception_captured(self):
        agent = MockSuperAgent(raise_on_call=1)
        adapter = SuperAgentAdapter(agent)
        run = await adapter.run("boom")
        assert not run.success
        assert "RuntimeError" in run.error
        assert "simulated failure" in run.error

    @pytest.mark.asyncio
    async def test_result_with_error_field(self):
        agent = MockSuperAgent(result=MockAgentResult(content="", error="api_key_missing"))
        adapter = SuperAgentAdapter(agent)
        run = await adapter.run("x")
        assert not run.success
        assert run.error == "api_key_missing"


class TestHealJournal:
    @pytest.mark.asyncio
    async def test_heal_entries_extracted(self):
        agent = MockSuperAgent(
            heal_entries_to_add=[
                MockHealEntry(
                    category="external", action_taken="retry_with_backoff", succeeded=True
                ),
                MockHealEntry(category="config", action_taken="reload_env", succeeded=False),
            ]
        )
        adapter = SuperAgentAdapter(agent)
        run = await adapter.run("x")
        assert len(run.heal_journal) == 2
        cats = [e.category for e in run.heal_journal]
        assert "external" in cats
        assert "config" in cats

    @pytest.mark.asyncio
    async def test_journal_baseline_isolates_runs(self):
        agent = MockSuperAgent(
            heal_entries_to_add=[MockHealEntry(category="external", action_taken="retry")]
        )
        adapter = SuperAgentAdapter(agent)
        run1 = await adapter.run("first")
        # Second run injects another entry; first run's entries must not reappear
        run2 = await adapter.run("second")
        assert len(run1.heal_journal) == 1
        assert len(run2.heal_journal) == 1

    @pytest.mark.asyncio
    async def test_missing_journal_tolerated(self):
        class BareAgent:
            agent_type = "bare"

            async def execute(self, _prompt, **_):
                return MockAgentResult(content="ok")

        adapter = SuperAgentAdapter(BareAgent())
        run = await adapter.run("x")
        assert run.success
        assert run.heal_journal == ()


class TestTelemetrySnapshot:
    @pytest.mark.asyncio
    async def test_consecutive_failures_captured(self):
        agent = MockSuperAgent()
        agent._consecutive_failures = 7
        adapter = SuperAgentAdapter(agent)
        run = await adapter.run("x")
        assert run.consecutive_failures == 7

    @pytest.mark.asyncio
    async def test_circuit_state_captured(self):
        agent = MockSuperAgent()
        agent._circuit_state = "open"
        adapter = SuperAgentAdapter(agent)
        run = await adapter.run("x")
        assert run.circuit_state == "open"
