---
name: audit-pass2-verifier
description: Read an audit report claiming fixes applied (PASS 2, PASS 3, etc), verify each claim against source code, then execute deferred items. Use when handed an audit markdown that lists "FIX: applied" entries, when asked to "close audit findings", or to "validate audit work to production".
---

# audit-pass2-verifier

## Trigger

User hands you (or you find) an audit/review markdown that:
- Tables findings with severity (CRITICAL/HIGH/MEDIUM/LOW)
- Marks some as `FIX: applied in PASS N`
- Marks others as `DEFERRED`
- Includes file paths + line numbers

User says: "verify the audit", "close the audit", "complete the deferred items", "drive this to production-validated".

## The Rule

**Audit docs lie. Verify every "FIX applied" claim in source before trusting.** Then execute deferred items in priority order.

**Why:** Audit markdown is human/agent-authored. Edits get reverted, hooks reformat them away, parallel sessions overwrite them. Trusting the doc without verification = building on quicksand.

**How to apply:** Source-of-truth pass, then deferred-execution pass, then test-suite delta.

## Workflow

### Step 1 — Read audit doc ONCE

Capture: findings table, status column, file paths, line numbers. Do NOT re-read.

### Step 2 — Verify each "applied" claim

For each PASS N "FIX: applied" entry:

```bash
grep -n "<expected-symbol>" <file-path>
```

Use `grep -n` not `rg` when pattern has special chars (parens, backslashes) — shell escape eats `\(` in unquoted rg patterns and silently returns 0 matches. Match: claim verified. No match: doc lied or work got reverted.

**Build a verification table:**

| Finding ID | Claim | Verified? | Evidence |
|---|---|---|---|
| C-01 | budget gate added L555 | YES | `nodes.py:559` matches |
| C-02 | `_find_garment_image` returns "" if missing | YES | `tryon_agent.py:171` `is_file()` |
| ... | | | |

### Step 3 — Execute deferred items

For each `DEFERRED` finding, decide:
- (a) **Do the work** if scope fits the current pass.
- (b) **Defer with a concrete plan** in a follow-up task file.
- (c) **Partial work** if a clean subset can ship.

Apply the project's existing pattern (e.g., for a budget gate, mirror the pattern at `graph/nodes.py:294-325`). Don't invent.

### Step 4 — Test delta

```bash
pytest <scope> -v --timeout=15 -q 2>&1 | tail -10
```

Compare to audit's baseline. Report: before X/Y → after X/Y. Categorize remaining failures: pre-existing-out-of-scope vs new-and-bad.

### Step 5 — Final report

Structured output:

```
## Verified (PASS N)
<table: ID | file:line | evidence>

## Executed Deferred
<table: ID | files changed | scope>

## Tests
<before → after delta>

## Still Deferred (with reason)
<table: ID | why deferred | next action>
```

## Anti-Patterns

- Don't trust the audit doc without grep verification
- Don't re-read the audit markdown after the initial pass — it's static
- Don't fix LOW findings unless trivial — they sit on the deferred list for a reason
- Don't run paid APIs to "test" the fix — code path verification + unit tests only
- Don't refactor in scope — audit fixes are surgical

## Example invocation

Audit lists 3 CRITICAL + 4 HIGH + 4 MEDIUM. PASS 2 claims 3 CRITICAL + 3 MEDIUM applied; 4 HIGH deferred.

You: grep each of the 6 "applied" claims → 6/6 verified → take H-01 + H-02 (FLUX budget gate ripple), wire the gate at orchestrator level (cleaner than the audit's stage-level suggestion since grep shows compositor_agent doesn't call flux_pipeline) → run tests, 479 pass / 0 fail → report shows H-03 / H-04 (file size splits) still deferred with note.

## Related

- `verification-before-completion`
- `systematic-debugging` (for treating audit doc as hypothesis, not fact)
- `commit-batch-sweep` (for landing verified work)
