"""Integration tests for Kernel with PolicyEngine + ApprovalGate + BudgetController."""

from __future__ import annotations

import asyncio

import pytest

from aos.governance.approval import ApprovalRequest, RiskLevel
from aos.governance.budget import BudgetVerdict
from aos.governance.policy import PolicyRule, PolicyVerdict
from aos.governance.types import AuditEventType
from aos.kernel.kernel import (
    ApprovalRejectedError,
    Kernel,
    PolicyDeniedError,
)
from aos.kernel.types import SpawnRequest


@pytest.fixture
async def kernel(tmp_path) -> Kernel:
    k = Kernel(audit_db_path=str(tmp_path / "audit.db"), system_budget_usd=10.0)
    await k.boot()
    return k


class TestPolicyGate:
    @pytest.mark.asyncio
    async def test_deny_blocks_spawn(self, kernel: Kernel):
        kernel.policies.add_rule(
            PolicyRule(
                name="block-imagery",
                verdict=PolicyVerdict.DENY,
                match={"agent_type": "imagery"},
                reason="imagery agents disabled during incident",
            )
        )
        with pytest.raises(PolicyDeniedError, match="imagery agents disabled"):
            await kernel.spawn(SpawnRequest(agent_type="imagery", prompt="x"))

        violations = await kernel.audit.query(event_type=AuditEventType.POLICY_VIOLATION)
        assert len(violations) == 1
        assert violations[0].details["matched_rule"] == "block-imagery"

    @pytest.mark.asyncio
    async def test_allow_proceeds_silently(self, kernel: Kernel):
        kernel.policies.add_rule(
            PolicyRule(
                name="allow-commerce", verdict=PolicyVerdict.ALLOW, match={"agent_type": "commerce"}
            )
        )
        proc = await kernel.spawn(SpawnRequest(agent_type="commerce", prompt="x"))
        assert proc.pid >= 1
        violations = await kernel.audit.query(event_type=AuditEventType.POLICY_VIOLATION)
        assert len(violations) == 0


class TestApprovalGate:
    @pytest.mark.asyncio
    async def test_require_approval_then_approve(self, kernel: Kernel):
        kernel.policies.add_rule(
            PolicyRule(
                name="prod-write",
                verdict=PolicyVerdict.REQUIRE_APPROVAL,
                match={"agent_type": "deployer"},
            )
        )

        async def operator():
            for _ in range(50):
                pending = await kernel.approvals.list_pending()
                if pending:
                    await kernel.approvals.approve(pending[0].id, approver="corey")
                    return
                await asyncio.sleep(0.01)

        op_task = asyncio.create_task(operator())
        proc = await kernel.spawn(
            SpawnRequest(agent_type="deployer", prompt="deploy theme"),
            approval_timeout_seconds=2.0,
        )
        await op_task

        assert proc.pid >= 1
        granted = await kernel.audit.query(event_type=AuditEventType.APPROVAL_GRANTED)
        assert len(granted) == 1

    @pytest.mark.asyncio
    async def test_require_approval_denied(self, kernel: Kernel):
        kernel.policies.add_rule(
            PolicyRule(
                name="prod-write",
                verdict=PolicyVerdict.REQUIRE_APPROVAL,
                match={"agent_type": "deployer"},
            )
        )

        async def operator():
            for _ in range(50):
                pending = await kernel.approvals.list_pending()
                if pending:
                    await kernel.approvals.deny(pending[0].id, reason="not now")
                    return
                await asyncio.sleep(0.01)

        op_task = asyncio.create_task(operator())
        with pytest.raises(ApprovalRejectedError, match="not now"):
            await kernel.spawn(
                SpawnRequest(agent_type="deployer", prompt="deploy"),
                approval_timeout_seconds=2.0,
            )
        await op_task

        denied = await kernel.audit.query(event_type=AuditEventType.APPROVAL_DENIED)
        assert len(denied) == 1

    @pytest.mark.asyncio
    async def test_approval_timeout_rejects(self, kernel: Kernel):
        kernel.policies.add_rule(
            PolicyRule(
                name="prod-write",
                verdict=PolicyVerdict.REQUIRE_APPROVAL,
                match={"agent_type": "deployer"},
            )
        )
        with pytest.raises(ApprovalRejectedError, match="timeout"):
            await kernel.spawn(
                SpawnRequest(agent_type="deployer", prompt="deploy"),
                approval_timeout_seconds=0.05,
            )


class TestBudgetGate:
    @pytest.mark.asyncio
    async def test_check_spend_allow(self, kernel: Kernel):
        proc = await kernel.spawn(SpawnRequest(agent_type="x", prompt="y", budget_usd=5.0))
        d = await kernel.check_spend(proc.pid, 1.0)
        assert d.verdict == BudgetVerdict.ALLOW

    @pytest.mark.asyncio
    async def test_check_spend_warn_audits(self, kernel: Kernel):
        proc = await kernel.spawn(SpawnRequest(agent_type="x", prompt="y", budget_usd=5.0))
        d = await kernel.check_spend(proc.pid, 4.5)
        assert d.verdict == BudgetVerdict.WARN
        warnings = await kernel.audit.query(event_type=AuditEventType.BUDGET_WARNING)
        assert len(warnings) == 1
        assert warnings[0].target_pid == proc.pid

    @pytest.mark.asyncio
    async def test_check_spend_deny_audits(self, kernel: Kernel):
        proc = await kernel.spawn(SpawnRequest(agent_type="x", prompt="y", budget_usd=1.0))
        d = await kernel.check_spend(proc.pid, 5.0)
        assert d.verdict == BudgetVerdict.DENY
        exceeded = await kernel.audit.query(event_type=AuditEventType.BUDGET_EXCEEDED)
        assert len(exceeded) == 1

    @pytest.mark.asyncio
    async def test_record_spend_updates_system_total(self, kernel: Kernel):
        proc = await kernel.spawn(SpawnRequest(agent_type="x", prompt="y", budget_usd=5.0))
        await kernel.record_spend(proc.pid, 1.5)
        await kernel.record_spend(proc.pid, 2.0)
        assert kernel.budget.system_spent_usd == 3.5


class TestApprovalAPI:
    @pytest.mark.asyncio
    async def test_request_approval_audits_lifecycle(self, kernel: Kernel):
        req = ApprovalRequest(
            requester_pid=1,
            action="fashn.tryon",
            description="generate try-on",
            risk=RiskLevel.HIGH,
            estimated_cost_usd=1.20,
        )

        async def operator():
            await asyncio.sleep(0.01)
            await kernel.approvals.approve(req.id, approver="corey")

        op_task = asyncio.create_task(operator())
        decision = await kernel.request_approval(req, timeout_seconds=2.0)
        await op_task

        assert decision.is_approved
        requested = await kernel.audit.query(event_type=AuditEventType.APPROVAL_REQUESTED)
        granted = await kernel.audit.query(event_type=AuditEventType.APPROVAL_GRANTED)
        assert len(requested) == 1
        assert len(granted) == 1
        assert requested[0].details["estimated_cost_usd"] == 1.20


class TestContainerFactory:
    @pytest.mark.asyncio
    async def test_make_container_uses_defaults(self, kernel: Kernel):
        c = kernel.make_container()
        assert c.limits is kernel.default_limits

    @pytest.mark.asyncio
    async def test_make_container_respects_override(self, kernel: Kernel):
        from aos.runtime.types import ResourceLimits

        custom = ResourceLimits(max_runtime_seconds=1.0, max_tool_calls=5)
        c = kernel.make_container(limits=custom)
        assert c.limits.max_runtime_seconds == 1.0
        assert c.limits.max_tool_calls == 5
