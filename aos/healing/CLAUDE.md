# aos/healing/ — circuit breaker and healing director

Decides how to respond to agent failures — retry, abort, or escalate — without storing per-agent state itself. The healing director is stateless; mutable state (consecutive failure counts, breaker open/closed) lives in `CircuitBreaker` instances keyed by agent_type.

## Key files

- `director.py` — `HealingDirector.decide(category, attempt) → HealDecision`: stateless. Two hard invariants checked first: `BUDGET_EXCEEDED → ESCALATE`, `POLICY_DENIAL → ABORT`. Otherwise consults `policy.get_policy(category)` for retry config; when `attempt >= max_retries` returns `ABORT` for `UNKNOWN` and `ESCALATE` for everything else; otherwise returns `RETRY` with `delay_seconds` from `compute_delay`.
- `circuit_breaker.py` — `CircuitBreaker`: tracks consecutive failures per agent_type. `CircuitState(StrEnum)` values `CLOSED` / `OPEN` / `HALF_OPEN`. Defaults `failure_threshold=3`, `recovery_timeout_seconds=30.0`. Methods `allow_request()`, `record_success()`, `record_failure()`. Injectable `time_fn` enables deterministic tests.
- `policy.py` — `_POLICY: dict[FailureCategory, RetryConfig]` retry table keyed on `aos.cognition.reflector.FailureCategory`. Public surface: `get_policy(category) → RetryConfig`, `compute_delay(config, attempt) → float`. `RATE_LIMIT` uses exponential backoff; others are linear.
- `types.py` — `HealAction(StrEnum)`: `RETRY`, `ABORT`, `ESCALATE`. `RetryConfig` `@dataclass(frozen=True)` with `max_retries`, `base_delay_seconds`, `exponential=False`. `HealDecision` `@dataclass(frozen=True)` with `action: HealAction`, `delay_seconds: float`, `reason: str` — all three fields are required.

## Conventions

- `HealingDirector.decide()` is pure — no I/O, no side effects, no async. Tests call it synchronously.
- `HealAction` and `CircuitState` are `StrEnum` — human-readable string values, not integers.
- `HealDecision` and `RetryConfig` are frozen dataclasses (not Pydantic). Construct new instances; never mutate.
- Two hard invariants in `director.decide()`: `BUDGET_EXCEEDED` always escalates; `POLICY_DENIAL` always aborts. Both bypass the retry table entirely.

## Don't

- Don't add per-agent_type mutable state to `director.py` — that state belongs in `CircuitBreaker` instances or in `aos/kernel/process_manager.py`.
- Don't change the `BUDGET_EXCEEDED → ESCALATE` or `POLICY_DENIAL → ABORT` mappings without updating `aos/governance/` and the matching tests in `tests/aos/healing/`.
- Don't import from `agents/` here — healing knows nothing about specific agent implementations.
- Don't widen `HealAction` beyond `RETRY / ABORT / ESCALATE` without updating `director.decide()` exhaustively — the kernel acts on every returned action.

## Related

- `aos/cognition/reflector.py` — defines `FailureCategory(StrEnum)`, the enum that keys `_POLICY`
- `aos/kernel/process_manager.py` — acts on each `HealDecision` by retrying, aborting, or escalating processes
- `aos/adapters/superagent_adapter.py` — surfaces `_circuit_state` and `_consecutive_failures` that `CircuitBreaker` observes
- `aos/governance/budget.py` — source of the `BUDGET_EXCEEDED` failure category
