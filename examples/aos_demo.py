"""Live demo of the AOS kernel — Phase 1 + 2.

Run with: python -m examples.aos_demo

Walks through:
  1. Boot the kernel (audit DB created)
  2. Spawn a process (allowed by default)
  3. Add a policy rule that DENIES imagery agents — verify it blocks
  4. Add a policy rule that REQUIRE_APPROVALs deployer agents — operator approves it
  5. Budget gate: check_spend → ALLOW, WARN, DENY
  6. Force-kill a running process
  7. Print the full audit log

No paid APIs are called. No external services. Everything runs in-memory + a temp SQLite file.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from aos.governance.policy import PolicyRule, PolicyVerdict
from aos.kernel.kernel import (
    ApprovalRejectedError,
    Kernel,
    PolicyDeniedError,
)
from aos.kernel.types import ProcessPriority, ProcessStatus, SpawnRequest


def banner(text: str) -> None:
    print(f"\n\033[1;36m━━━ {text} ━━━\033[0m")


def kv(label: str, value: object) -> None:
    print(f"  \033[2m{label:.<24}\033[0m {value}")


async def main() -> None:
    tmpdir = Path(tempfile.mkdtemp(prefix="aos_demo_"))
    db_path = tmpdir / "audit.db"

    banner("BOOT")
    kernel = Kernel(audit_db_path=str(db_path), system_budget_usd=10.0)
    await kernel.boot()
    kv("audit db", db_path)
    kv("system budget", f"${kernel.budget.system_budget_usd:.2f}")
    kv("booted", kernel.is_booted)

    banner("SPAWN — allowed by default")
    p1 = await kernel.spawn(
        SpawnRequest(
            agent_type="commerce",
            prompt="update br-001 price",
            priority=ProcessPriority.HIGH,
            budget_usd=2.0,
        )
    )
    kv("pid", p1.pid)
    kv("status", p1.status.name)
    kv("priority", p1.priority.name)
    kv("budget", f"${p1.budget_usd:.2f}")

    banner("POLICY: DENY imagery agents (incident response)")
    kernel.policies.add_rule(
        PolicyRule(
            name="block-imagery",
            verdict=PolicyVerdict.DENY,
            match={"agent_type": "imagery"},
            reason="paused during cost incident",
        )
    )
    try:
        await kernel.spawn(SpawnRequest(agent_type="imagery", prompt="render br-001"))
        kv("imagery spawn", "UNEXPECTED — allowed")
    except PolicyDeniedError as exc:
        kv("imagery spawn", f"BLOCKED — {exc}")

    banner("POLICY: REQUIRE_APPROVAL for deployer (production write)")
    kernel.policies.add_rule(
        PolicyRule(
            name="approve-deploy",
            verdict=PolicyVerdict.REQUIRE_APPROVAL,
            match={"agent_type": "deployer"},
            reason="touches skyyrose.co",
        )
    )

    async def operator_approver() -> None:
        # Operator approves any pending request after a short delay
        for _ in range(50):
            pending = await kernel.approvals.list_pending()
            if pending:
                req = pending[0]
                kv("approval queued", req.id)
                kv("  action", req.action)
                kv("  risk", req.risk.value)
                kv("  est cost", f"${req.estimated_cost_usd:.2f}")
                await kernel.approvals.approve(req.id, approver="corey")
                kv("approved by", "corey")
                return
            await asyncio.sleep(0.02)

    op_task = asyncio.create_task(operator_approver())
    p2 = await kernel.spawn(
        SpawnRequest(
            agent_type="deployer",
            prompt="bump SKYYROSE_VERSION + deploy",
            parent_pid=p1.pid,
            budget_usd=0.5,
        )
    )
    await op_task
    kv("deployer pid", p2.pid)
    kv("parent_pid", p2.parent_pid)

    banner("BUDGET — ALLOW / WARN / DENY")
    for projected in (0.5, 1.7, 3.0):
        d = await kernel.check_spend(p1.pid, projected_cost_usd=projected)
        kv(f"check ${projected:.2f}", f"{d.verdict.value.upper():6} — {d.reason}")
    await kernel.record_spend(p1.pid, 0.5)
    kv("recorded spend", "$0.50")
    kv("system spent", f"${kernel.budget.system_spent_usd:.2f}")

    banner("LIFECYCLE — start, pause, resume, complete")
    await kernel.transition(p1.pid, ProcessStatus.READY)
    await kernel.transition(p1.pid, ProcessStatus.RUNNING)
    await kernel.transition(p1.pid, ProcessStatus.PAUSED)
    await kernel.transition(p1.pid, ProcessStatus.RUNNING)
    await kernel.complete(p1.pid, result={"updated_price": "$285"})
    final = await kernel.processes.get(p1.pid)
    kv("p1 final status", final.status.name)
    kv("p1 result", final.result)
    kv("p1 spent", f"${final.spent_usd:.2f}")

    banner("KILL — force-terminate p2")
    await kernel.transition(p2.pid, ProcessStatus.READY)
    await kernel.transition(p2.pid, ProcessStatus.RUNNING)
    await kernel.kill(p2.pid, reason="user_cancelled")
    p2_final = await kernel.processes.get(p2.pid)
    kv("p2 final status", p2_final.status.name)
    kv("p2 error", p2_final.error)

    banner("REQUIRE_APPROVAL — timeout path")
    try:
        await kernel.spawn(
            SpawnRequest(agent_type="deployer", prompt="late-night deploy"),
            approval_timeout_seconds=0.1,
        )
    except ApprovalRejectedError as exc:
        kv("blocked by", f"{exc}")

    banner("AUDIT LOG — full history")
    entries = await kernel.audit.query(limit=100)
    for e in reversed(entries):
        actor = f"PID{e.actor_pid}" if e.actor_pid is not None else "—"
        target = f"PID{e.target_pid}" if e.target_pid is not None else "—"
        details = ", ".join(f"{k}={v}" for k, v in list(e.details.items())[:2])
        print(
            f"  {e.timestamp.strftime('%H:%M:%S.%f')[:-3]}  "
            f"\033[1;33m{e.event_type.value:22}\033[0m  "
            f"actor={actor:5}  target={target:5}  {details[:60]}"
        )

    banner("SUMMARY")
    counts = {}
    for e in entries:
        counts[e.event_type.value] = counts.get(e.event_type.value, 0) + 1
    for event_type, n in sorted(counts.items(), key=lambda x: -x[1]):
        kv(event_type, n)

    await kernel.shutdown()
    print("\n\033[1;32m✓ Demo complete. Audit DB:\033[0m", db_path)


if __name__ == "__main__":
    asyncio.run(main())
