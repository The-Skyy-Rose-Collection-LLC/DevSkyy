"""Tests for ApprovalGate."""

from __future__ import annotations

import asyncio

import pytest

from aos.governance.approval import (
    ApprovalGate,
    ApprovalRequest,
    ApprovalStatus,
    RiskLevel,
)


@pytest.fixture
def gate() -> ApprovalGate:
    return ApprovalGate()


def _req(risk: RiskLevel = RiskLevel.HIGH, cost: float = 1.0) -> ApprovalRequest:
    return ApprovalRequest(
        requester_pid=1,
        action="fashn.tryon",
        description="Generate try-on for br-001",
        risk=risk,
        estimated_cost_usd=cost,
    )


class TestSubmitWait:
    @pytest.mark.asyncio
    async def test_approve_resolves_wait(self, gate: ApprovalGate):
        req = _req()
        await gate.submit(req)

        async def operator():
            await asyncio.sleep(0.01)
            await gate.approve(req.id, approver="corey")

        op_task = asyncio.create_task(operator())
        decision = await gate.wait(req.id, timeout_seconds=1.0)
        await op_task

        assert decision.status == ApprovalStatus.APPROVED
        assert decision.is_approved
        assert decision.approver == "corey"

    @pytest.mark.asyncio
    async def test_deny_resolves_wait(self, gate: ApprovalGate):
        req = _req()
        await gate.submit(req)
        await gate.deny(req.id, reason="cost too high")
        decision = await gate.wait(req.id, timeout_seconds=1.0)
        assert decision.status == ApprovalStatus.DENIED
        assert not decision.is_approved
        assert decision.reason == "cost too high"

    @pytest.mark.asyncio
    async def test_timeout_marks_expired(self, gate: ApprovalGate):
        req = _req()
        await gate.submit(req)
        decision = await gate.wait(req.id, timeout_seconds=0.05)
        assert decision.status == ApprovalStatus.EXPIRED

    @pytest.mark.asyncio
    async def test_wait_missing_request_raises(self, gate: ApprovalGate):
        with pytest.raises(KeyError):
            await gate.wait("nope")


class TestAutoApprove:
    @pytest.mark.asyncio
    async def test_auto_approve_low_risk(self, gate: ApprovalGate):
        gate.set_auto_approve(RiskLevel.LOW)
        decision = await gate.request_and_wait(_req(risk=RiskLevel.LOW), timeout_seconds=1.0)
        assert decision.status == ApprovalStatus.APPROVED
        assert decision.approver == "auto"

    @pytest.mark.asyncio
    async def test_auto_approve_skips_high_risk(self, gate: ApprovalGate):
        gate.set_auto_approve(RiskLevel.LOW)
        req = _req(risk=RiskLevel.HIGH)
        await gate.submit(req)
        decision = await gate.wait(req.id, timeout_seconds=0.05)
        assert decision.status == ApprovalStatus.EXPIRED

    @pytest.mark.asyncio
    async def test_auto_approve_disabled_by_default(self, gate: ApprovalGate):
        req = _req(risk=RiskLevel.LOW)
        await gate.submit(req)
        decision = await gate.wait(req.id, timeout_seconds=0.05)
        assert decision.status == ApprovalStatus.EXPIRED


class TestQuery:
    @pytest.mark.asyncio
    async def test_list_pending(self, gate: ApprovalGate):
        await gate.submit(_req())
        await gate.submit(_req())
        pending = await gate.list_pending()
        assert len(pending) == 2

    @pytest.mark.asyncio
    async def test_history_records_decisions(self, gate: ApprovalGate):
        r1 = _req()
        r2 = _req()
        await gate.submit(r1)
        await gate.submit(r2)
        await gate.approve(r1.id, approver="op")
        await gate.deny(r2.id, reason="nope")
        assert len(gate.history) == 2
        statuses = {d.status for d in gate.history}
        assert ApprovalStatus.APPROVED in statuses
        assert ApprovalStatus.DENIED in statuses
