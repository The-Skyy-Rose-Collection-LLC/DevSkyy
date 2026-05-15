"""Kernel — wires ProcessManager + MessageBus + AuditTrail into a single coordinator.

The Kernel is the entry point for the AOS runtime. It owns the three subsystems
and emits audit events on every state-changing operation.

Lifecycle:
    kernel = Kernel(audit_db_path="aos.db")
    await kernel.boot()
    proc = await kernel.spawn(SpawnRequest(...))
    ...
    await kernel.shutdown()
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from aos.adapters.superagent_adapter import SuperAgentAdapter
from aos.governance.approval import ApprovalDecision, ApprovalGate, ApprovalRequest
from aos.governance.audit import AuditTrail
from aos.governance.budget import BudgetController, BudgetDecision, BudgetVerdict
from aos.governance.policy import PolicyDecision, PolicyEngine, PolicyVerdict
from aos.governance.types import AuditEntry, AuditEventType
from aos.ipc.message_bus import MessageBus
from aos.kernel.process_manager import ProcessManager
from aos.kernel.types import AgentProcess, ProcessStatus, SpawnRequest
from aos.observability.learning_hook import LearningHook, LearningTrace
from aos.runtime.container import AgentContainer
from aos.runtime.executor import ExecutionOutcome, NoFactoryError
from aos.runtime.types import ResourceLimits

AgentFactory = Callable[[], Awaitable[Any]]


class PolicyDeniedError(PermissionError):
    """Raised when a kernel action is rejected by the PolicyEngine."""


class ApprovalRejectedError(PermissionError):
    """Raised when an approval request is denied or times out."""


class BudgetDeniedError(PermissionError):
    """Raised when a spend would exceed budget."""


class Kernel:
    """Central kernel coordinator.

    Wires the three core subsystems (process table, message bus, audit log)
    and ensures every lifecycle event is audited.
    """

    KERNEL_PID = 0

    def __init__(
        self,
        *,
        audit_db_path: str | Path = "aos_audit.db",
        bus_queue_size: int = 1024,
        system_budget_usd: float = 100.0,
        default_limits: ResourceLimits | None = None,
    ) -> None:
        self.processes = ProcessManager()
        self.bus = MessageBus(queue_size=bus_queue_size)
        self.audit = AuditTrail(db_path=audit_db_path)
        self.budget = BudgetController(system_budget_usd=system_budget_usd)
        self.approvals = ApprovalGate()
        self.policies = PolicyEngine()
        self.default_limits = default_limits or ResourceLimits()
        self._agent_factories: dict[str, AgentFactory] = {}
        self.learning = LearningHook(
            learning_module_resolver=self._resolve_learning_module,
        )
        self._learning_modules: dict[str, Any] = {}
        self._booted = False

    async def boot(self) -> None:
        """Initialize subsystems. Must be called before spawn/transition."""
        if self._booted:
            return
        await self.audit.initialize()
        await self.audit.log(
            AuditEntry(event_type=AuditEventType.SYSTEM_BOOT, actor_pid=self.KERNEL_PID)
        )
        self._booted = True

    async def shutdown(self) -> None:
        """Graceful shutdown. Flushes learning buffers; audit stays queryable for forensics."""
        if not self._booted:
            return
        flushed = await self.learning.flush_all()
        if flushed:
            await self.audit.log(
                AuditEntry(
                    event_type=AuditEventType.LEARNING_FLUSHED,
                    actor_pid=self.KERNEL_PID,
                    details={"trace_count": flushed},
                )
            )
        await self.audit.log(
            AuditEntry(event_type=AuditEventType.SYSTEM_SHUTDOWN, actor_pid=self.KERNEL_PID)
        )
        self._booted = False

    async def close(self) -> None:
        """Full teardown — closes the audit connection. Call after shutdown()."""
        if self._booted:
            await self.shutdown()
        await self.audit.close()

    def _require_booted(self) -> None:
        if not self._booted:
            msg = "Kernel not booted — call await kernel.boot() first"
            raise RuntimeError(msg)

    async def spawn(
        self,
        request: SpawnRequest,
        *,
        approval_timeout_seconds: float | None = 300.0,
    ) -> AgentProcess:
        """Spawn a new process after policy + audit checks.

        Raises PolicyDeniedError when a DENY rule matches the spawn descriptor.
        Raises ApprovalRejectedError when REQUIRE_APPROVAL is rejected or expires.
        """
        self._require_booted()
        descriptor = {
            "action": "spawn",
            "agent_type": request.agent_type,
            "priority": request.priority.name,
            "parent_pid": request.parent_pid,
            **request.metadata,
        }
        decision = self.policies.evaluate(descriptor)
        await self._audit_policy(descriptor, decision)

        if decision.verdict == PolicyVerdict.DENY:
            msg = f"Policy denied spawn: {decision.reason}"
            raise PolicyDeniedError(msg)

        if decision.verdict == PolicyVerdict.REQUIRE_APPROVAL:
            await self._require_spawn_approval(
                request,
                policy_reason=decision.reason,
                timeout_seconds=approval_timeout_seconds,
            )

        proc = await self.processes.spawn(request)
        await self.audit.log(
            AuditEntry(
                event_type=AuditEventType.PROCESS_SPAWN,
                actor_pid=request.parent_pid or self.KERNEL_PID,
                target_pid=proc.pid,
                correlation_id=proc.correlation_id,
                details={
                    "agent_type": request.agent_type,
                    "priority": request.priority.name,
                    "budget_usd": request.budget_usd,
                },
            )
        )
        return proc

    async def transition(
        self,
        pid: int,
        new_status: ProcessStatus,
        **kwargs: Any,
    ) -> AgentProcess:
        """Transition a process + audit lifecycle events."""
        self._require_booted()
        prior = await self.processes.get(pid)
        prior_status = prior.status
        proc = await self.processes.transition(pid, new_status, **kwargs)
        event_type = _resolve_event_type(prior_status, new_status)
        if event_type is not None:
            await self.audit.log(
                AuditEntry(
                    event_type=event_type,
                    target_pid=pid,
                    correlation_id=proc.correlation_id,
                    details={
                        "from_status": prior_status.name,
                        "to_status": new_status.name,
                        **{k: str(v) for k, v in kwargs.items()},
                    },
                )
            )
        return proc

    async def complete(self, pid: int, result: Any) -> AgentProcess:
        """Complete a process and audit."""
        return await self.transition(pid, ProcessStatus.COMPLETED, result=result)

    async def fail(self, pid: int, error: str) -> AgentProcess:
        """Fail a process and audit."""
        return await self.transition(pid, ProcessStatus.FAILED, error=error)

    async def kill(self, pid: int, reason: str = "killed") -> AgentProcess:
        """Force-kill a process and audit."""
        self._require_booted()
        proc = await self.processes.kill(pid, reason=reason)
        await self.audit.log(
            AuditEntry(
                event_type=AuditEventType.PROCESS_KILL,
                target_pid=pid,
                correlation_id=proc.correlation_id,
                details={"reason": reason},
            )
        )
        return proc

    async def record_spend(self, pid: int, amount: float) -> AgentProcess:
        """Record process spend (after a check has cleared) and audit on overflow."""
        self._require_booted()
        proc = await self.processes.record_spend(pid, amount)
        await self.budget.record(amount)
        if proc.is_over_budget:
            await self.audit.log(
                AuditEntry(
                    event_type=AuditEventType.BUDGET_EXCEEDED,
                    target_pid=pid,
                    correlation_id=proc.correlation_id,
                    details={
                        "spent_usd": proc.spent_usd,
                        "budget_usd": proc.budget_usd,
                    },
                )
            )
        return proc

    async def check_spend(self, pid: int, projected_cost_usd: float) -> BudgetDecision:
        """Check if a process can incur projected_cost. Audits WARN/DENY."""
        self._require_booted()
        proc = await self.processes.get(pid)
        decision = await self.budget.check(
            process_budget_usd=proc.budget_usd,
            process_spent_usd=proc.spent_usd,
            projected_cost_usd=projected_cost_usd,
        )
        if decision.verdict == BudgetVerdict.WARN:
            await self.audit.log(
                AuditEntry(
                    event_type=AuditEventType.BUDGET_WARNING,
                    target_pid=pid,
                    correlation_id=proc.correlation_id,
                    details={
                        "projected_usd": decision.projected_spend_usd,
                        "limit_usd": decision.limit_usd,
                    },
                )
            )
        elif decision.verdict == BudgetVerdict.DENY:
            await self.audit.log(
                AuditEntry(
                    event_type=AuditEventType.BUDGET_EXCEEDED,
                    target_pid=pid,
                    correlation_id=proc.correlation_id,
                    details={
                        "projected_usd": decision.projected_spend_usd,
                        "limit_usd": decision.limit_usd,
                        "reason": decision.reason,
                    },
                )
            )
        return decision

    async def request_approval(
        self,
        request: ApprovalRequest,
        *,
        timeout_seconds: float | None = 300.0,
    ) -> ApprovalDecision:
        """Submit an approval request, audit it, and wait for resolution."""
        self._require_booted()
        await self.approvals.submit(request)
        await self.audit.log(
            AuditEntry(
                event_type=AuditEventType.APPROVAL_REQUESTED,
                actor_pid=request.requester_pid,
                details={
                    "request_id": request.id,
                    "action": request.action,
                    "risk": request.risk.value,
                    "estimated_cost_usd": request.estimated_cost_usd,
                },
            )
        )
        decision = await self.approvals.wait(request.id, timeout_seconds=timeout_seconds)
        event = (
            AuditEventType.APPROVAL_GRANTED
            if decision.is_approved
            else AuditEventType.APPROVAL_DENIED
        )
        await self.audit.log(
            AuditEntry(
                event_type=event,
                actor_pid=request.requester_pid,
                details={
                    "request_id": request.id,
                    "approver": decision.approver,
                    "status": decision.status.value,
                    "reason": decision.reason,
                },
            )
        )
        return decision

    def make_container(
        self,
        limits: ResourceLimits | None = None,
    ) -> AgentContainer:
        """Build a fresh AgentContainer using kernel defaults when no limits passed."""
        return AgentContainer(limits=limits or self.default_limits)

    async def register_agent_factory(
        self,
        agent_type: str,
        factory: AgentFactory,
    ) -> None:
        """Register an async factory that builds an agent of the given type on demand."""
        self._require_booted()
        self._agent_factories[agent_type] = factory
        await self.audit.log(
            AuditEntry(
                event_type=AuditEventType.AGENT_REGISTERED,
                actor_pid=self.KERNEL_PID,
                details={"agent_type": agent_type},
            )
        )

    def _resolve_learning_module(self, agent_type: str) -> Any | None:
        """Cache hook used by LearningHook to look up an agent_type's SelfLearningModule."""
        return self._learning_modules.get(agent_type)

    async def execute(
        self,
        request: SpawnRequest,
        *,
        approval_timeout_seconds: float | None = 300.0,
        limits: ResourceLimits | None = None,
    ) -> ExecutionOutcome:
        """End-to-end: spawn → run inside container → audit retries → record learning.

        Raises NoFactoryError if no factory is registered for the agent_type.
        """
        self._require_booted()
        proc = await self.spawn(request, approval_timeout_seconds=approval_timeout_seconds)

        factory = self._agent_factories.get(request.agent_type)
        if factory is None:
            await self.fail(proc.pid, error=f"no factory registered for {request.agent_type}")
            msg = f"No agent factory registered for {request.agent_type!r}"
            raise NoFactoryError(msg)

        agent = await factory()
        learning_module = getattr(agent, "learning_module", None)
        if learning_module is not None:
            self._learning_modules[request.agent_type] = learning_module
        adapter = SuperAgentAdapter(agent)

        await self.transition(proc.pid, ProcessStatus.READY)
        await self.transition(proc.pid, ProcessStatus.RUNNING)

        container = self.make_container(limits=limits)
        container_result = await container.run(lambda _c: adapter.run(request.prompt))
        adapter_run = container_result.result
        if adapter_run is None:
            adapter_run = _empty_adapter_run(
                request.agent_type,
                container_result.error or "container_failure",
            )

        for entry in adapter_run.heal_journal:
            await self.audit.log(
                AuditEntry(
                    event_type=AuditEventType.PROCESS_RETRY,
                    target_pid=proc.pid,
                    correlation_id=proc.correlation_id,
                    details={
                        "category": entry.category,
                        "action": entry.action_taken,
                        "succeeded": entry.succeeded,
                    },
                )
            )

        await self.learning.record(
            LearningTrace(
                agent_type=request.agent_type,
                prompt=request.prompt,
                result=adapter_run.raw_result,
                success=adapter_run.success and container_result.success,
                error=adapter_run.error or container_result.error,
                retry_count=len(adapter_run.heal_journal),
                heal_categories=tuple(e.category for e in adapter_run.heal_journal),
                cost_usd=float(adapter_run.metadata.get("cost_usd", 0.0) or 0.0),
                latency_ms=float(adapter_run.metadata.get("latency_ms", 0.0) or 0.0),
                metadata={
                    "consecutive_failures": adapter_run.consecutive_failures,
                    "circuit_state": adapter_run.circuit_state,
                    "container_timed_out": container_result.timed_out,
                    "tool_calls": container_result.usage.tool_call_count,
                },
            )
        )

        overall_success = adapter_run.success and container_result.success
        if overall_success:
            await self.complete(proc.pid, result=adapter_run.raw_result)
        else:
            error = adapter_run.error or container_result.error or "unknown failure"
            await self.fail(proc.pid, error=error)

        return ExecutionOutcome(
            pid=proc.pid,
            success=overall_success,
            agent_run=adapter_run,
            container_result=container_result,
            heal_entries=adapter_run.heal_journal,
            error=adapter_run.error or container_result.error,
            metadata={
                "agent_type": request.agent_type,
                "container_timed_out": container_result.timed_out,
            },
        )

    async def _audit_policy(
        self,
        descriptor: dict[str, Any],
        decision: PolicyDecision,
    ) -> None:
        if decision.verdict == PolicyVerdict.DENY:
            await self.audit.log(
                AuditEntry(
                    event_type=AuditEventType.POLICY_VIOLATION,
                    details={
                        "matched_rule": decision.matched_rule,
                        "reason": decision.reason,
                        "descriptor": descriptor,
                    },
                )
            )

    async def _require_spawn_approval(
        self,
        request: SpawnRequest,
        *,
        policy_reason: str,
        timeout_seconds: float | None,
    ) -> None:
        from aos.governance.approval import RiskLevel

        approval_req = ApprovalRequest(
            requester_pid=request.parent_pid or self.KERNEL_PID,
            action=f"spawn:{request.agent_type}",
            description=f"Spawn {request.agent_type} — {policy_reason}",
            risk=RiskLevel.MEDIUM,
            estimated_cost_usd=request.budget_usd,
            details={"prompt": request.prompt[:200], "policy_reason": policy_reason},
        )
        decision = await self.request_approval(approval_req, timeout_seconds=timeout_seconds)
        if not decision.is_approved:
            msg = f"Approval rejected: {decision.reason or decision.status.value}"
            raise ApprovalRejectedError(msg)

    @property
    def is_booted(self) -> bool:
        """Check whether the kernel has been booted."""
        return self._booted


def _resolve_event_type(
    prior: ProcessStatus,
    new: ProcessStatus,
) -> AuditEventType | None:
    """Map a (prior, new) status pair to its audit event type.

    RUNNING from READY = first start. RUNNING from PAUSED/WAITING = resume.
    Other transitions map by target status alone.
    """
    if new == ProcessStatus.RUNNING:
        if prior == ProcessStatus.READY:
            return AuditEventType.PROCESS_START
        if prior in {ProcessStatus.PAUSED, ProcessStatus.WAITING}:
            return AuditEventType.PROCESS_RESUME
        return None
    return _TERMINAL_EVENT_MAP.get(new)


_TERMINAL_EVENT_MAP: dict[ProcessStatus, AuditEventType] = {
    ProcessStatus.PAUSED: AuditEventType.PROCESS_PAUSE,
    ProcessStatus.COMPLETED: AuditEventType.PROCESS_COMPLETE,
    ProcessStatus.FAILED: AuditEventType.PROCESS_FAIL,
}


def _empty_adapter_run(agent_type: str, error: str) -> Any:
    """Build an AdapterRun representing a container-level failure (no agent run captured)."""
    from aos.adapters.superagent_adapter import AdapterRun

    return AdapterRun(
        agent_type=agent_type,
        success=False,
        raw_result=None,
        error=error,
        heal_journal=(),
        consecutive_failures=0,
        circuit_state="closed",
        metadata={},
    )
