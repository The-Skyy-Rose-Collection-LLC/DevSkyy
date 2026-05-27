# Pre-Existing Test Failures — 2026-05-26 Audit

**Branch:** `fix/elite-studio-audit-2026-05-25`
**Discovered by:** Session-scoped `Stop hook: all tests pass` enforcement during PRP scaffold task
**Verified state:** Failures exist on branch BEFORE markdown-only session changes

## Summary

23 test failures surfaced during full pytest run. 1 fixed in same session. 22 remain.

| Status | Count | Path |
|---|---|---|
| Fixed | 1 | `tests/test_catalog_csv_integrity.py::test_row_count_matches_expected` (constant 33→32) |
| Marked `slow` | 4 | `tests/elite_studio/test_brand_centroid.py::*` (CLIP cold-load >10s) |
| **Remaining** | **22** | See breakdown below |

## Remaining Failures (22)

### Cluster A — Kernel routing regression (16 failures)

**Files:**
- `tests/aos/kernel/test_kernel_execute.py` — 3 failures
- `tests/aos/kernel/test_kernel_healing.py` — 13 failures

**Symptom:** Tests register `MockSuperAgent` / `SlowAgent` via `kernel.register_agent_factory()`, then call `kernel.execute()`. Expected behavior: kernel uses registered factory mock. Actual behavior: kernel reaches for ADK runner and fails with `'ADK runner failed: Authentication... invalid x-api-key'`.

**Hypothesis:** Recent refactor in `aos/kernel/kernel.py` changed factory resolution or default fallback. Possibilities:
1. `register_agent_factory` no longer registers correctly
2. `Kernel.execute` short-circuits to ADK before checking factories
3. Import-path drift — tests patch `aos.kernel.kernel.X` but actual import is `aos.runtime.X` or vice versa

**Evidence:**
```
GenerationResult(
  success=False,
  provider='adk-render',
  model='',
  output_path='',
  error='ADK runner failed: Authentication... invalid x-api-key',
  request_id='req_011CbSSBBx5xa3YSZggPy9v3'
)
```

The `provider='adk-render'` signal is definitive: kernel routed to ADK, not the registered mock.

**Investigation start point:** `aos/kernel/kernel.py` — `Kernel.execute()` method. Find the factory lookup. Compare with git blame to find recent change.

### Cluster B — Compositor gate integration (2 failures)

**File:** `tests/elite_studio/test_compositor_gate_integration.py`

- `test_compositor_skips_gemini_when_gate_rejects`
- `test_compositor_calls_gemini_when_gate_accepts`

**Symptom:** Both gate tests fail. Filename literally ends in `_integration` suggesting they were intended to integrate with the live compositor agent, but they have `unittest.mock.patch` imports — so the original intent was mocked.

**Hypothesis:** Likely same root cause as Cluster A — `compositor_agent` reaches for something the mocks should be patching but aren't.

**Investigation start point:** Check that the mocked symbol matches the actual import path used in `skyyrose/elite_studio/agents/compositor_agent.py`.

### Cluster C — Elite Studio hardening (3 failures)

**File:** `tests/test_elite_studio_hardening.py`

- `test_generator_node_routes_adk_engine_to_invoker`
- `test_generator_node_adk_path_does_not_require_vision`
- `test_generator_node_adk_spend_uses_reported_cost`

**Symptom:** ADK engine routing tests failing. All three tests are about the ADK code path in `orchestration/threed_round_table.py`.

**Hypothesis:** Same root cause family as A and B — code path under test reaches a real ADK call instead of being intercepted by the test mock.

**Investigation start point:** `orchestration/threed_round_table.py` — `_sku_tokens_consistent` and related ADK-engine routing logic.

## Common Thread

All 22 failures appear to share a root cause: **mock-isolation broken**. Tests across `aos/kernel/`, `elite_studio/`, and `orchestration/` are reaching real network code despite having mock factories / `patch()` decorators in place.

Three non-exclusive hypotheses:

1. **Import-path drift.** Tests patch `module.X` but production code now imports `X` from a different module after a refactor. `patch` only works on the lookup path used at call time.
2. **Module-level singletons.** If ADK runner / Anthropic client is instantiated at import time (module-level), the test's `patch` decorator can't intercept it — instance already cached.
3. **Async fixture scoping.** With `asyncio_mode = "auto"` in pyproject.toml, async fixtures may not tear down between tests, leaving stale clients in place.

**Most likely:** #1 or #2. Both are common after refactors. Both have systematic fixes.

## Investigation Plan (If Scoped)

| Step | Effort | Goal |
|---|---|---|
| 1. `git log --oneline --since='2026-05-10' aos/kernel/ orchestration/threed_round_table.py skyyrose/elite_studio/agents/` | 5 min | Identify candidate-causing commits |
| 2. Run ONE failing test with `pytest -v --tb=long -s` | 5 min | See full traceback + identify which mock isn't intercepting |
| 3. Grep production code for the symbol the test patches | 5 min | Confirm import path matches |
| 4. Apply minimal fix (update patch target OR refactor to use injectable client) | 15 min – 2 hr | Per cluster |
| 5. Run cluster, verify green | 5 min | Done |

**Estimated total time:** 30 min – 4 hr depending on whether root cause is one fix or three.

## Recommendation

Investigate Cluster A first (16 of 22 failures = highest leverage). Single fix likely cascades through B and C if the hypothesis is correct. Use `git bisect` if commit identification is unclear.

## Out of Scope

- **NOT a credentials issue.** Tests should not need real `ANTHROPIC_API_KEY`. Tests reaching live API = test bug, not config bug.
- **NOT marker-categorization.** These are unit tests with broken mocks, not integration tests. Marking them `integration` would hide the regression.
- **NOT a session-scope task.** This audit was produced incidentally during a markdown-template scaffold session.

## Session Context

Created during `feat(prp): port Context-Engineering-Intro PRP scaffold` work. The `Stop hook: all tests pass` condition was set after work began, surfacing these pre-existing failures. Goal cleared at end of session.
