# aos/cognition/ — Goal decomposition, planning, reflection

Deterministic, rule-based cognitive layer. Turns a free-form goal string into a typed `TaskGraph`, orders the graph into an executable `DecomposedPlan`, and after execution scores the outcome and classifies failures. Stays LLM-free on purpose: the kernel's cognition surface must be reproducible across test runs.

## Key files

- `goal_decomposer.py` — `GoalDecomposer`: rule-based keyword matcher that maps a goal into a `TaskGraph`. Three domain templates (`product`, `marketing`, `analytics`) plus a default fallback. Output is a typed graph, never free-form text.
- `planner.py` — `Planner`: converts a `TaskGraph` into a `DecomposedPlan` via Kahn's-algorithm topological wavefront. Cycles raise; otherwise each wave runs in parallel inside the kernel.
- `reflector.py` — `Reflector`: takes an `ExecutionOutcome + LearningTrace` and produces a quality-scored `Reflection`. Exports `FailureCategory(StrEnum)` — the contract surface that `aos/healing/policy.py` keys retry behavior on. Categories include `RATE_LIMIT`, `BUDGET_EXCEEDED`, `POLICY_DENIAL`, `TIMEOUT`, `UNKNOWN`.
- `types.py` — `TaskNode`, `TaskGraph`, `DecomposedPlan`, `PlanStep`. All Pydantic with `model_config = {"frozen": True}`.

## Conventions

- Rule-based, never LLM-based. Determinism is a hard requirement — tests assert exact graph shapes against fixed goals.
- All models are `frozen=True` Pydantic. Construct new instances rather than mutating.
- `FailureCategory` is the cross-package contract between `cognition` and `healing`. Adding a category requires a matching entry in `aos/healing/policy.py:_POLICY` and updated tests in both `tests/aos/cognition/` and `tests/aos/healing/`.
- `Planner` raises on cycles in the `TaskGraph` — callers handle by surfacing through the kernel, not by silent acyclic projection.

## Don't

- Don't add LLM calls anywhere in this directory. The decomposer is rule-based by design; LLM-backed planning belongs in `orchestration/`, not the kernel.
- Don't import from `aos/healing/`. Cognition feeds healing through `FailureCategory`; the reverse direction creates a cycle.
- Don't widen `FailureCategory` without updating `aos/healing/policy.py:_POLICY` in the same commit. The retry policy keys off this enum.
- Don't bypass `Planner` to execute a `TaskGraph` directly — the wavefront ordering is what makes parallel kernel execution safe.

## Related

- `aos/healing/policy.py` — consumes `FailureCategory` to drive retry/abort/escalate decisions
- `aos/kernel/` — calls `Planner.plan(graph)` at spawn time
- `aos/CLAUDE.md` — parent kernel doc
- `tests/aos/cognition/` — full coverage for decomposer / planner / reflector


<claude-mem-context>

</claude-mem-context>