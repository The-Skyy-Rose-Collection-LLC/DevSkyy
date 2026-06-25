---
name: drive-to-green
description: Bounded auto-fix loop targeting a green-state goal (tests passing, lint clean, build succeeding, type-check clean). Iterates run → diagnose → fix → re-run with progress detection, iteration cap, and per-attempt time budget. Use when the user says "drive it to green", "fix until tests pass", "make the build pass", "auto-fix until clean", or "loop until X passes".
---

# drive-to-green

## Trigger

User says any of:
- "drive it to green" / "drive to green"
- "fix until tests pass" / "loop until X passes"
- "make the build pass" / "make the lint clean"
- "auto-fix until clean"
- "iterate until <goal>"
- "keep fixing"

Or you finish a task and a verification command fails — wrap the recovery in this loop.

## The Rule

**Bounded iteration with progress detection. Never infinite-loop. Never paper over the failure.** Fix root causes; if you can't, surface the failure to the user with diagnostic context.

**Why:** Auto-fix loops without bounds run forever or oscillate (fix A breaks B, fix B breaks A). Without progress detection you can't tell "stuck" from "still working." Without root-cause discipline you ship failing code with the assertion stripped.

**How to apply:** Define goal + budget + forbidden fixes upfront. Run. Diagnose. Fix. Re-run. Track delta. Stop on green, on budget, or on no-progress.

## Goal Definition (required before starting)

```
GOAL          : <exact command + expected exit code 0>
SUCCESS       : <text marker that proves green, e.g. "479 passed, 0 failed">
BUDGET        : <max iterations, default 5>
TIME PER RUN  : <max seconds per command, default 180>
FORBIDDEN FIX : <what you must NOT do — defaults below>
ESCALATION    : <when to stop and ask user>
```

**Default forbidden fixes (always):**
- Marking failing tests `@pytest.skip` / `xfail` without explicit user OK
- Deleting tests to make the suite green
- Catching + silently swallowing the error
- `git reset --hard` / `git checkout --` to discard work
- Skipping pre-commit hooks (`--no-verify`)
- Disabling lint rules globally
- Mocking out the broken integration to bypass it

**Default escalation triggers:**
- Same failure signature appears on 2 consecutive iterations (no progress)
- Iteration budget exhausted
- A fix would require touching out-of-scope files (>10 unrelated paths)
- A fix would require a secret / credential you don't have

## Loop Workflow

### Step 1 — State the goal

Echo back the resolved goal block so the user can intervene early:

```
DRIVE TO GREEN
GOAL    : pytest skyyrose/elite_studio/tests/ -v --timeout=15
SUCCESS : "0 failed" in summary line
BUDGET  : 5 iterations
TIME    : 180s/run
```

### Step 2 — Run baseline

Execute the goal command. Capture exit code + tail output. Record:

```
ITER 0 (baseline)
  exit  : <code>
  output: <last 10 lines>
  status: <RED|GREEN>
  signature: <hash of failure type — file:line:error-class>
```

If GREEN → done, report.

### Step 3 — Diagnose

For each failure in the output:
- Identify error class (ImportError, AssertionError, TypeError, lint rule, test failure)
- Identify file + line
- Identify likely root cause from error message + surrounding code

Do NOT batch-fix. Pick the FIRST failure or the one blocking the most downstream work.

### Step 4 — Fix (one logical change per iteration)

Apply the fix:
- Lint failures: `<linter> --fix` first, manual only for non-auto-fixable
- Format: `black` + `isort`
- Type errors: fix the actual type, don't add `# type: ignore`
- Test failures: read the test, read the code under test, fix the bug
- Import errors: add the missing export, don't paper over with `try/except ImportError`

### Step 5 — Re-run + compare

Run the goal command again. Compare:

```
ITER N
  exit       : <code>
  signature  : <hash>
  delta      : <previous count → current count>
  progress?  : YES (different signature) | NO (same signature)
```

### Step 6 — Decide next action

```
IF status == GREEN:
  report success + landed fixes + commits to make
ELIF iteration >= BUDGET:
  escalate: budget exhausted, here's what I tried
ELIF progress == NO and same signature twice:
  escalate: stuck on same failure — need user input
ELIF a fix would violate FORBIDDEN list:
  escalate: forbidden fix needed — confirm or change approach
ELSE:
  loop to Step 3
```

### Step 7 — Final report

```
DRIVE-TO-GREEN RESULT
status       : GREEN | RED-EXHAUSTED | RED-ESCALATED
iterations   : <N>/<BUDGET>
duration     : <total seconds>
fixes landed : <count + one-line each>
final state  : <last command output, last 10 lines>
commits      : <if any committed during loop>
```

## Common Loop Patterns

### Pattern A — Lint clean

```
GOAL    : ruff check . && black --check . && isort --check .
BUDGET  : 3
TYPICAL : 1-2 iterations (ruff --fix + black + isort gets there)
```

### Pattern B — Tests passing

```
GOAL    : pytest <scope> --timeout=15
BUDGET  : 5
TYPICAL : 2-4 iterations
WATCH   : real-clock tests that hang — set --timeout aggressively
```

### Pattern C — Build succeeding

```
GOAL    : npm run build (or pnpm/cargo/make build)
BUDGET  : 5
TYPICAL : 3-5 iterations
WATCH   : fixing one error often reveals next — count downward as progress
```

### Pattern D — Pre-commit hook green

```
GOAL    : git commit --dry-run -m "test"  # or stage + commit + rollback
BUDGET  : 4
TYPICAL : 2-3 iterations (ruff + black + isort + maybe one manual)
NOTE    : NEW commit after each fix, never --amend the failed-hook commit
```

### Pattern E — Type-check clean

```
GOAL    : mypy <scope> --strict (or tsc --noEmit)
BUDGET  : 5
TYPICAL : 3-5 iterations
WATCH   : Don't paper with `Any` or `# type: ignore` — fix the actual type
```

## Progress Detection Heuristics

A failure SIGNATURE is the tuple: `(error_class, file, line, normalized_message)`.

- **Progress made** = signature changed OR failure count decreased.
- **Stuck** = same signature N consecutive iterations (default N=2).
- **Oscillating** = signature A → signature B → signature A. Stop, surface both.
- **Cascade** = each fix reveals next error in a chain (this IS progress, keep going).

## Anti-Patterns

- Don't run the loop without an explicit goal command — "make it work" is not a goal
- Don't skip Step 1 (echo goal) — user needs the chance to intervene
- Don't auto-commit between iterations unless the user explicitly asked — wait for green, commit all fixes as one logical commit
- Don't tighten the budget mid-loop to "force" success — that's gaming the metric
- Don't suppress / `--no-verify` / `# noqa` away the error — that's not green, it's hidden red
- Don't catch + log + continue inside the loop — the loop's own diagnostics are the catch
- Don't run the full project test suite when the failing scope is one module — local scope first, broader scope after green

## Interaction with Other Skills

- `commit-batch-sweep` uses this when pre-commit hooks fail
- `audit-pass2-verifier` uses this to drive deferred items to test-green
- `budget-gate-wirer` uses this after wiring to verify no regression
- `stalled-agent-recovery` may invoke this after recovering partial work

## Example Invocation

User: "drive the elite_studio tests to green"

You:
```
DRIVE TO GREEN
GOAL    : pytest skyyrose/elite_studio/tests/ -v --timeout=15
SUCCESS : "0 failed" in summary
BUDGET  : 5
TIME    : 180s/run
```

ITER 0: 28 failed (catalog schema + asyncio mock + tryon mock-target mismatch)

ITER 1: fix tryon test mock-target (`agent.try_on` → `agent.execute_tryon`). Re-run: 25 failed (3 fewer). Progress.

ITER 2: fix asyncio non-coroutine mocks → AsyncMock. Re-run: 14 failed (11 fewer, catalog schema remains).

ITER 3: catalog CSV schema fix — out of scope per audit. Escalate.

Report:
```
status     : RED-ESCALATED
iterations : 3/5
fixes      : tryon mock target, AsyncMock migration
remaining  : 14 catalog schema failures (out-of-scope per audit C-04)
recommend  : separate task to align catalog test fixtures with current schema
```

## Related

- `verification-before-completion`
- `commit-batch-sweep`
- `systematic-debugging`
- `audit-pass2-verifier`
