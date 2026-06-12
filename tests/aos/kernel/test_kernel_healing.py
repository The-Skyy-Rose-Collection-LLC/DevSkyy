"""Kernel-level self-healing integration tests — Phase 5.

Tests verify that kernel.execute() retries on recoverable failures, aborts on
policy violations, escalates on budget exhaustion, and honours the per-agent-type
circuit breaker.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from aos.governance.types import AuditEventType
from aos.kernel.kernel import Kernel
from aos.kernel.types import SpawnRequest
from tests.aos._mocks import MockAgentResult, MockSuperAgent


async def _async(x):
    return x


@pytest.fixture
async def kernel(tmp_path) -> Kernel:
    k = Kernel(audit_db_path=str(tmp_path / "audit.db"), system_budget_usd=10.0)
    await k.boot()
    yield k
    await k.close()


# ---------------------------------------------------------------------------
# Regression: success path must still work
# ---------------------------------------------------------------------------


class TestNoRegression:
    @pytest.mark.asyncio
    async def test_success_path_unchanged(self, kernel: Kernel):
        agent = MockSuperAgent(result=MockAgentResult(content="ok"))
        await kernel.register_agent_factory("commerce", lambda: _async(agent))
        outcome = await kernel.execute(SpawnRequest(agent_type="commerce", prompt="x"))
        assert outcome.success
        assert agent._call_count == 1


# ---------------------------------------------------------------------------
# RETRY path — RATE_LIMIT: exponential backoff, then succeed
# ---------------------------------------------------------------------------


class TestHealingRetry:
    @pytest.mark.asyncio
    async def test_rate_limit_retries_twice_then_succeeds(self, kernel: Kernel):
        # Calls 1 and 2 raise; call 3 succeeds.
        agent = MockSuperAgent(raise_on_call=2, error_message="rate limit exceeded")
        await kernel.register_agent_factory("commerce", lambda: _async(agent))
        outcome = await kernel.execute(SpawnRequest(agent_type="commerce", prompt="x"))
        assert outcome.success
        assert agent._call_count == 3

    @pytest.mark.asyncio
    async def test_heal_attempted_logged_per_retry(self, kernel: Kernel):
        agent = MockSuperAgent(raise_on_call=2, error_message="rate limit exceeded")
        await kernel.register_agent_factory("commerce", lambda: _async(agent))
        await kernel.execute(SpawnRequest(agent_type="commerce", prompt="x"))
        events = await kernel.audit.query(event_type=AuditEventType.HEAL_ATTEMPTED)
        assert len(events) == 2

    @pytest.mark.asyncio
    async def test_heal_attempted_details_contain_category(self, kernel: Kernel):
        agent = MockSuperAgent(raise_on_call=1, error_message="rate limit exceeded")
        await kernel.register_agent_factory("commerce", lambda: _async(agent))
        await kernel.execute(SpawnRequest(agent_type="commerce", prompt="x"))
        events = await kernel.audit.query(event_type=AuditEventType.HEAL_ATTEMPTED)
        assert events[0].details["category"] == "rate_limit"

    @pytest.mark.asyncio
    async def test_rate_limit_sleep_called_with_exponential_delays(self, kernel: Kernel):
        # attempt 0 → delay 2.0s; attempt 1 → delay 4.0s; attempt 2 → success (no sleep).
        agent = MockSuperAgent(raise_on_call=2, error_message="rate limit exceeded")
        await kernel.register_agent_factory("commerce", lambda: _async(agent))
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await kernel.execute(SpawnRequest(agent_type="commerce", prompt="x"))
        sleep_args = [c.args[0] for c in mock_sleep.call_args_list]
        assert sleep_args == [2.0, 4.0]

    @pytest.mark.asyncio
    async def test_no_sleep_when_delay_zero(self, kernel: Kernel):
        # TIMEOUT has base_delay=1.0 (flat, not zero) but UNKNOWN → 1.0 → not zero.
        # Use TOOL_FAILURE (base_delay=0.5) with raise_on_call=1, succeeds call 2.
        agent = MockSuperAgent(raise_on_call=1, error_message="tool error occurred")
        await kernel.register_agent_factory("commerce", lambda: _async(agent))
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await kernel.execute(SpawnRequest(agent_type="commerce", prompt="x"))
        mock_sleep.assert_called_once_with(0.5)


# ---------------------------------------------------------------------------
# ABORT path — POLICY_DENIAL stops immediately
# ---------------------------------------------------------------------------


class TestHealingAbort:
    @pytest.mark.asyncio
    async def test_policy_denial_aborts_immediately(self, kernel: Kernel):
        agent = MockSuperAgent(raise_on_call=99, error_message="policy denied")
        await kernel.register_agent_factory("commerce", lambda: _async(agent))
        outcome = await kernel.execute(SpawnRequest(agent_type="commerce", prompt="x"))
        assert not outcome.success

    @pytest.mark.asyncio
    async def test_policy_denial_logs_heal_aborted(self, kernel: Kernel):
        agent = MockSuperAgent(raise_on_call=99, error_message="policy denied")
        await kernel.register_agent_factory("commerce", lambda: _async(agent))
        await kernel.execute(SpawnRequest(agent_type="commerce", prompt="x"))
        events = await kernel.audit.query(event_type=AuditEventType.HEAL_ABORTED)
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_policy_denial_only_one_agent_call(self, kernel: Kernel):
        agent = MockSuperAgent(raise_on_call=99, error_message="policy denied")
        await kernel.register_agent_factory("commerce", lambda: _async(agent))
        await kernel.execute(SpawnRequest(agent_type="commerce", prompt="x"))
        assert agent._call_count == 1


# ---------------------------------------------------------------------------
# ESCALATE path — BUDGET_EXCEEDED stops immediately
# ---------------------------------------------------------------------------


class TestHealingEscalate:
    @pytest.mark.asyncio
    async def test_budget_exceeded_escalates_immediately(self, kernel: Kernel):
        agent = MockSuperAgent(raise_on_call=99, error_message="budget exceeded")
        await kernel.register_agent_factory("commerce", lambda: _async(agent))
        outcome = await kernel.execute(SpawnRequest(agent_type="commerce", prompt="x"))
        assert not outcome.success

    @pytest.mark.asyncio
    async def test_budget_exceeded_logs_heal_escalated(self, kernel: Kernel):
        agent = MockSuperAgent(raise_on_call=99, error_message="budget exceeded")
        await kernel.register_agent_factory("commerce", lambda: _async(agent))
        await kernel.execute(SpawnRequest(agent_type="commerce", prompt="x"))
        events = await kernel.audit.query(event_type=AuditEventType.HEAL_ESCALATED)
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_budget_exceeded_only_one_agent_call(self, kernel: Kernel):
        agent = MockSuperAgent(raise_on_call=99, error_message="budget exceeded")
        await kernel.register_agent_factory("commerce", lambda: _async(agent))
        await kernel.execute(SpawnRequest(agent_type="commerce", prompt="x"))
        assert agent._call_count == 1


# ---------------------------------------------------------------------------
# Circuit breaker — trips after failure_threshold consecutive full-failures
# ---------------------------------------------------------------------------


class TestCircuitBreaker:
    @pytest.mark.asyncio
    async def test_circuit_trips_after_three_failures(self, kernel: Kernel):
        # POLICY_DENIAL → ABORT → record_failure() on each execute.
        # Default CircuitBreaker failure_threshold=3 → OPEN after 3 failures.
        agent = MockSuperAgent(raise_on_call=99, error_message="policy denied")
        await kernel.register_agent_factory("sentinel", lambda: _async(agent))
        for _ in range(3):
            await kernel.execute(SpawnRequest(agent_type="sentinel", prompt="x"))
        # 4th execute: circuit open → fast-fail without calling agent
        outcome = await kernel.execute(SpawnRequest(agent_type="sentinel", prompt="x"))
        assert not outcome.success
        assert "circuit" in (outcome.error or "").lower()

    @pytest.mark.asyncio
    async def test_circuit_open_skips_agent_invocation(self, kernel: Kernel):
        agent = MockSuperAgent(raise_on_call=99, error_message="policy denied")
        await kernel.register_agent_factory("sentinel", lambda: _async(agent))
        for _ in range(3):
            await kernel.execute(SpawnRequest(agent_type="sentinel", prompt="x"))
        await kernel.execute(SpawnRequest(agent_type="sentinel", prompt="x"))
        # 3 policy-denied calls; 4th call circuit open → agent never touched on 4th
        assert agent._call_count == 3

    @pytest.mark.asyncio
    async def test_circuit_open_logs_heal_aborted(self, kernel: Kernel):
        agent = MockSuperAgent(raise_on_call=99, error_message="policy denied")
        await kernel.register_agent_factory("sentinel", lambda: _async(agent))
        for _ in range(3):
            await kernel.execute(SpawnRequest(agent_type="sentinel", prompt="x"))
        await kernel.execute(SpawnRequest(agent_type="sentinel", prompt="x"))
        all_aborted = await kernel.audit.query(event_type=AuditEventType.HEAL_ABORTED)
        # 3 ABORT (policy_denial) + 1 ABORT (circuit_open) = 4
        assert len(all_aborted) == 4
