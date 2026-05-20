# aos/governance/ — Policy, approval, budget, audit

The control plane the kernel consults before every spawn and every paid/destructive action. Five modules covering approval gates, append-only audit, spend ceilings, and declarative policy rules. This is where the project-wide STOP-AND-SHOW protocol is enforced for agents running inside AOS.

## Key files

- `approval.py` — `ApprovalGate`, `ApprovalRequest`, `ApprovalStatus(StrEnum)`, `RiskLevel(StrEnum)`. The STOP-AND-SHOW enforcement point: paid or destructive actions must pass through `ApprovalGate.request(...)` before the kernel will execute them.
- `audit.py` — `AuditTrail`: append-only SQLite-backed log. Indexed on `event_type`, `actor_pid`, `target_pid`, `correlation_id`, `timestamp`. No update or delete operations.
- `budget.py` — `BudgetController`, `BudgetVerdict(StrEnum)`, `BudgetDecision`. Tracks per-process spend and a system-wide ceiling; emits a warning verdict before the hard cutoff.
- `policy.py` — `PolicyEngine`, `PolicyRule`, `PolicyVerdict(StrEnum)`. Declarative ALLOW / DENY / REQUIRE_APPROVAL rules. Precedence is hard: `DENY > REQUIRE_APPROVAL > ALLOW` inside `PolicyEngine.evaluate()`.
- `types.py` — `AuditEntry`, `AuditEventType`. Shared types consumed by all four modules.

## Conventions

- Precedence order in `PolicyEngine` is load-bearing. `DENY` short-circuits; `REQUIRE_APPROVAL` defers to `ApprovalGate`; `ALLOW` falls through. Reordering changes safety semantics.
- Every paid or destructive action consults `ApprovalGate` first. The repo root `CLAUDE.md` STOP-AND-SHOW protocol is enforced here for AOS-resident agents.
- `AuditTrail` is append-only. Operators reconstructing history rely on completeness; an UPDATE would break that contract.
- `BudgetController` issues a `WARN` verdict before `EXCEED`. Callers must surface the warning, not silently continue to the ceiling.
- All four modules are independently testable — they hold no shared mutable state across instances.

## Don't

- Don't bypass `ApprovalGate` for "trusted" internal callers. Trust is a property of the policy rule, not the call site.
- Don't reorder the `DENY > REQUIRE_APPROVAL > ALLOW` precedence in `PolicyEngine.evaluate()`. The order is the safety property.
- Don't add UPDATE or DELETE operations to `AuditTrail`. Append-only is the audit guarantee.
- Don't write secrets into audit row fields. `AuditEntry` is meant to be readable by operators; redact at the source.

## Related

- `aos/kernel/` — gates every spawn through `PolicyEngine` + `BudgetController`; routes `REQUIRE_APPROVAL` verdicts to `ApprovalGate`
- `aos/healing/director.py` — observes `BUDGET_EXCEEDED` → always escalates (hard invariant)
- `aos/CLAUDE.md` — parent kernel doc
- Repo root `CLAUDE.md` — defines the STOP-AND-SHOW protocol enforced here
