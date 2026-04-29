---
phase: 16
slug: 3d-replica-architect-purge
status: completed
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-24
revalidated: 2026-04-25
---

# Phase 16 — Validation Strategy

> Per-phase validation contract for Phase 16 3D-First architecture.
> **Re-issued 2026-04-25** with literal test counts after the post-sign-off CLI regression was discovered, fixed, and re-verified. See "Post-Sign-Off Corrections" at the bottom.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Python** | 3.14.3 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `python3 -m pytest skyyrose/elite_studio/tests/test_three_d_agent.py -x -q` |
| **Full suite command** | `python3 -m pytest skyyrose/elite_studio/tests/test_cli.py skyyrose/elite_studio/tests/test_three_d_agent.py skyyrose/elite_studio/tests/test_purge_hallucinations.py skyyrose/elite_studio/tests/test_graph_topology.py skyyrose/elite_studio/tests/test_dual_vision_gate.py skyyrose/elite_studio/tests/test_gemini_rest.py -q` |
| **Measured runtime (2026-04-25)** | **23.10s** |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest skyyrose/elite_studio/tests/test_three_d_agent.py -x -q`
- **After every plan wave:** Run `python3 -m pytest skyyrose/elite_studio/tests/test_three_d_agent.py skyyrose/elite_studio/tests/test_purge_hallucinations.py -q`
- **Before final check:** Full suite must be green (currently 34 tests across 6 files — see table below)

---

## Per-Task Verification Map

> Counts captured **2026-04-25**. The "Tests" column lists collected/passed/failed/skipped. The "Command" column is the literal pytest invocation that backs the Status — when narrower than the file (e.g., `-k "3d"`), the broader file count is shown in the "File total" column for honesty.

| Task ID | Plan | Wave | Requirement | Test File | Tests (file total) | Status | Command |
|---------|------|------|-------------|-----------|--------------------|--------|---------|
| 16-01 | 01 | 1 | PURGE-01 | `test_purge_hallucinations.py` | 1 / 1 / 0 / 0 | ✅ green | `python3 -m pytest skyyrose/elite_studio/tests/test_purge_hallucinations.py` |
| 16-02 | 01 | 1 | CLI-01 | `test_cli.py` | 8 / 8 / 0 / 0 | ✅ green (after fix — see below) | `python3 -m pytest skyyrose/elite_studio/tests/test_cli.py` |
| 16-03 | 01 | 1 | THREE-01 | `test_three_d_agent.py` | 5 / 5 / 0 / 0 | ✅ green (3 async-mock warnings) | `python3 -m pytest skyyrose/elite_studio/tests/test_three_d_agent.py` |
| 16-04 | 01 | 1 | VISION-01 | `test_dual_vision_gate.py` | 5 / 5 / 0 / 0 | ✅ green (1 async-mock warning) | `python3 -m pytest skyyrose/elite_studio/tests/test_dual_vision_gate.py` |
| 16-05 | 01 | 1 | ROTATE-01 | `test_gemini_rest.py` | 13 / 13 / 0 / 0 | ✅ green | `python3 -m pytest skyyrose/elite_studio/tests/test_gemini_rest.py` |
| 16-06 | 01 | 1 | GRAPH-01 | `test_graph_topology.py` | 2 / 2 / 0 / 0 | ✅ green | `python3 -m pytest skyyrose/elite_studio/tests/test_graph_topology.py` |
| **Total** | — | — | — | **6 files** | **34 / 34 / 0 / 0** | ✅ all green | full suite command above |

*Status legend: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_three_d_agent.py` — Smoke test for `ThreeDAgent` initialization and `generate_replica` mocking.
- [x] `tests/test_purge_hallucinations.py` — Test `scripts/purge_hallucinations.py` logic (dry-run).
- [x] `tests/test_graph_topology.py` — Test `skyyrose/elite_studio/graph/builder.py` correctly wires `three_d_node`.

---

## Post-Sign-Off Corrections (2026-04-25)

The original sign-off (2026-04-24) marked all six tasks ✅ green, but the table covered the 16-02 row with the narrower `-k "3d"` filter that ran 1 test out of 8 in `test_cli.py`. A subsequent code review surfaced two correctness issues that the original validation did not catch. Both are now fixed and the validation re-run.

### 1. CLI regression in `cmd_batch` legacy path — FIXED
- **Symptom**: `python -m skyyrose.elite_studio produce-batch --all` (without `--graph`) was a silent no-op. The function built the team but never called `team.produce_batch(...)`, so the CLI returned successfully without doing any work.
- **Root cause**: When the `--graph` branch was added, the legacy branch's terminal call was lost. There was no test exercising the legacy `--all` path through the real method (the `-k "3d"` filter only ran the graph-flag test).
- **Fix**: `skyyrose/elite_studio/cli.py` `cmd_batch` now discovers/filters SKUs and invokes `team.produce_batch(skus=..., view=..., skip_existing=...)` on the legacy path.
- **Verification**: `test_cli.py` now runs all 8 tests including `test_batch_all` and `test_batch_with_prefix`, which assert the method was called. All green.

### 2. `three_d_node` async correctness — FIXED
- **Symptom**: Under `graph.ainvoke()` (async invocation), `three_d_node` would crash with `RuntimeError: This event loop is already running`. Its `try: loop.run_until_complete(...)` / `except RuntimeError: asyncio.run(...)` pattern is unsafe — both branches raise when called inside a running loop, since `asyncio.run()` also rejects an already-running loop.
- **Root cause**: The node was authored as sync calling an async agent (`ThreeDAgent.generate_replica`). The graph supports async nodes natively in both `invoke()` and `ainvoke()`, so the workaround was unnecessary and incorrect.
- **Fix**: `skyyrose/elite_studio/graph/nodes.py` `three_d_node` is now `async def` and `await`s the agent directly.

### 3. `subprocess.run` blocking the event loop in `ThreeDAgent` — FIXED
- **Symptom**: `ThreeDAgent.generate_replica` is `async def` but called blocking `subprocess.run(blender, ..., timeout=120)`. Under any concurrent async load, this stalls the event loop for up to 120 s while Blender renders, serializing all other graph nodes and triggering LangGraph timeouts.
- **Fix**: `skyyrose/elite_studio/agents/three_d_agent.py` wraps the call with `await asyncio.to_thread(subprocess.run, render_cmd, ...)`. Identical exception types and return value, but the event loop is freed for the duration of the render. Existing test patches on `subprocess.run` continue to work via the thread executor.

### Known caveat — async-mock RuntimeWarnings (lower priority)

The full suite emits **6 `RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited`** warnings, originating from:

- `test_three_d_agent.py::test_generate_replica_success`
- `test_three_d_agent.py::test_meshy_failure_returns_error`
- `test_three_d_agent.py::test_none_synth_result_returns_error`
- `test_dual_vision_gate.py::test_consensus_both_yes`
- (2 emitted from Python internals during AsyncMock construction)

These are test-code artifacts (un-awaited `AsyncMock` side effects), not production bugs. Tracked as a follow-up cleanup pass. They do **not** affect the assertions, the test outcomes, or the underlying production code paths.

---

## Dropped Scope Reference

The original Phase 16 plan ("Jersey OCR Gate", requirement QA-03) was dropped in favor of this 3D-Replica architecture. The 3D scaffold-grounded synthesis produces verifiable text/number rendering at generation time, removing the need for a post-hoc OCR verification node. See `ROADMAP.md` Phase 16 note for details. `REQUIREMENTS.md` QA-03 status is still "Pending" and should be reconciled in a follow-up doc-only pass.
