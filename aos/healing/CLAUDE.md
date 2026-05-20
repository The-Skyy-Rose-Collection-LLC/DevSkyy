<claude-mem-context>

</claude-mem-context>

# aos/healing/ — circuit breaker and healing director

Decides how to respond to agent failures — retry, pause, kill, or escalate — without storing per-agent state itself. The healing director is stateless; state lives in the kernel's process records.

## Key files

- `director.py` — `HealingDirector.decide(category, attempt) → HealDecision`: stateless decision function. `BUDGET_EXCEEDED` always maps to `ESCALATE`. `POLICY_DENIAL` maps to a separate non-retry path.
- `circuit_breaker.py` — tracks consecutive failure counts per agent PID; trips the breaker after threshold crossings, blocking further spawns until reset.
- `policy.py` — retry backoff schedule, failure thresholds, breaker reset window.
- `types.py` — `HealAction(StrEnum)`: `RETRY`, `PAUSE`, `KILL`, `ESCALATE`. `HealDecision` frozen Pydantic model with `action: HealAction` and optional `delay_s`.

## Conventions

- `HealingDirector.decide()` is pure — no I/O, no side effects, no async. Tests can call it synchronously.
- `HealAction` is `StrEnum` — values are human-readable strings, not integers.
- `HealDecision` uses `model_config = {"frozen": True}`.
- `BUDGET_EXCEEDED` is never retried — always `ESCALATE`. This is a hard invariant.

## Don't

- Don't add per-agent mutable state to `director.py` — state belongs in `aos/kernel/process_manager.py`.
- Don't change `BUDGET_EXCEEDED → ESCALATE` mapping without updating `aos/governance/budget.py` and the IPC signal contract.
- Don't import from `agents/` here — the healing layer knows nothing about specific agent implementations.

## Related

- `aos/ipc/message_bus.py` — delivers `BUDGET_EXCEEDED` / `KILL` signals that trigger healing decisions
- `aos/kernel/process_manager.py` — acts on `HealDecision` by pausing, retrying, or terminating processes
- `aos/adapters/superagent_adapter.py` — exposes `_circuit_state` and `_consecutive_failures` read by circuit_breaker
