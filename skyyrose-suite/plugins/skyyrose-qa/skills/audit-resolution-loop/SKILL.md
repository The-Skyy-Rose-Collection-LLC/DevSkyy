---
name: audit-resolution-loop
description: End-to-end audit closure pipeline — read audit doc, verify claimed fixes, execute deferred items, drive-to-green per remediation, surface remaining. Composes audit-pass2-verifier + drive-to-green + verification-before-completion + code-review. Use when handed an audit report and asked to "close it", "drive to production-validated", "complete the audit", or "verify and finish".
---

# audit-resolution-loop

## Trigger

User says: "close the audit", "drive the audit to green", "complete the audit work", "verify + finish", "production-validate this", "audit-to-prod". Or you find an audit MD with `DEFERRED` items.

## The Rule

**Audit doc is a hypothesis, not a truth source. Verify every claim → execute every deferred → drive each remediation to green → produce one final report.** One audit, one closure.

Why: Audit reports get stale within hours. Sessions edit code, parallel work overwrites. A 24-hour-old "all fixes applied" claim needs grep verification before you trust it. Deferred items often require their own drive-to-green loops since fixes ripple.

How to apply: Three-pass workflow — VERIFY → EXECUTE → DRIVE.

## Workflow

### PASS A — Verify claimed fixes (audit-pass2-verifier semantics)

For each finding marked `FIX: applied`:

```bash
grep -n "<expected-symbol-from-fix-description>" <claimed-file-path>
```

Build verification table:

| Finding ID | Claim | Verified | Evidence |
|---|---|---|---|
| C-01 | budget gate at L555 | ✓ | nodes.py:559 matches |
| C-02 | stub replaced w/ is_file() | ✓ | tryon_agent.py:171 |
| M-01 | lazy logger format | ✗ | gone — reverted by parallel session |

Re-apply any reverted fixes IF still relevant (check git log for intentional revert first).

### PASS B — Execute deferred (per audit dispositions)

For each `DEFERRED` finding, decide:

1. **Execute now** — fits current pass scope, has clear pattern
2. **Partial work** — pull obvious subset, document rest
3. **Document plan** — write follow-up task file, don't execute

Selection criteria:
- Bounded scope (<500 lines touched) → execute
- Has existing pattern to mirror → execute
- Multi-file refactor (>1000 lines) → partial OR plan-only
- Requires architectural decision → plan-only + escalate

For each "execute now" item, dispatch via `Agent` tool w/ `budgeted-subagent-dispatch` discipline:

```
Agent(subagent_type="Senior Developer", prompt="""
H-01: Wire FLUX synthesis budget gate.
Pattern to mirror: graph/nodes.py:294-325
Target: flux_pipeline.render()
Budget: 5 reads, 3 edits, 1 test run
Forbidden: catch BudgetExceededError, --no-verify, mock budget primitive
""")
```

### PASS C — Drive to green (per remediation)

After EACH execution, run the goal command:

```bash
pytest <scope> --timeout=15 -q
```

If GREEN → mark resolved, continue.
If RED → invoke `drive-to-green` skill semantics inline:
  - Budget: 3 iterations per remediation
  - Forbidden: skip / xfail / silence
  - Surface root cause + fix

### PASS D — Final report

```
AUDIT RESOLUTION
================
audit doc       : <path/to/audit.md>
verified PASS-N : <N>/<M> claimed fixes confirmed in source
re-applied      : <table of reverted fixes restored>
executed        : <table of deferred items now fixed>
documented      : <table of items deferred-again with reasons>
test delta      : <before X/Y → after X/Y>
new commits     : <SHA + subject for each commit landed>
prod-ready      : <YES | NO + why>
```

## Decision Matrix (per Finding)

| Severity | Default Action |
|---|---|
| CRITICAL | Execute now (block all other work) |
| HIGH | Execute now if pattern clear, else partial |
| MEDIUM | Execute if bounded, else defer-with-plan |
| LOW | Defer unless trivial (<10 lines) |

Override per user direction — they may want HIGH/MEDIUM only, skipping LOW entirely.

## Anti-Patterns

- Don't trust the audit doc without grep verification (PASS A is non-optional)
- Don't execute ALL deferred items if scope blows budget — partial w/ clear escalation beats half-broken full pass
- Don't claim "production-validated" without test delta + zero new failures
- Don't auto-commit each fix — let `commit-pipeline-mega` handle commit batching at the end
- Don't re-audit (recursive) within same loop — separate session

## Interaction w/ Other Skills

- Invoked AFTER an audit MD exists (don't generate audit + close in same loop)
- Calls `audit-pass2-verifier` for PASS A
- Calls `budgeted-subagent-dispatch` for PASS B
- Calls `drive-to-green` for PASS C
- Calls `commit-pipeline-mega` after PASS D if user said "ship"
- Calls `stalled-agent-recovery` if any dispatched subagent stalls

## Hard NOs (project-aligned)

- Do NOT mark `xfail` / `skip` to mask failures
- Do NOT delete tests to make suite green
- Do NOT catch + swallow the failing exception
- Do NOT bypass `--no-verify` to land "fixed" commit
- Do NOT call paid APIs to "test" the fix — code path verification + unit tests only

## Example

Audit MD: `tasks/elite-studio-audit-2026-05-22.md` — 3 CRITICAL + 4 HIGH + 4 MEDIUM. Three CRITICAL + 3 MEDIUM marked PASS 2 applied; 4 HIGH deferred.

PASS A: grep 6 "applied" claims → 6/6 verified.

PASS B: H-01 + H-02 (FLUX budget gate, orchestrator level — pattern at nodes.py:294-325). H-03 + H-04 (file splits) → defer-with-plan (1241L and 1081L files, scope > 1000 lines).

PASS C: dispatch Senior Dev w/ budget 10 reads / 4 edits / 1 test run. Stalls at 706s/64K → invoke `stalled-agent-recovery` → recover partial work → wire remaining 4 budget gates inline → pytest = 479 pass / 0 fail.

PASS D: report:
- verified: 6/6
- executed: H-01, H-02
- documented: H-03, H-04 (plan in tasks/elite-studio-h3-h4-split-plan.md)
- test delta: 25/53 → 479/0
- new commits: b8ac132cc fix(elite-studio): FLUX budget gate
- prod-ready: YES for H-01/H-02 scope; H-03/H-04 remain as maintenance debt (no runtime risk)

User: "ship" → invoke `commit-pipeline-mega` → branch + PR.

## Related component skills

- `audit-pass2-verifier` (PASS A)
- `drive-to-green` (PASS C)
- `budgeted-subagent-dispatch` (PASS B dispatch)
- `stalled-agent-recovery` (recovery within PASS B)
- `verification-before-completion`
- `commit-pipeline-mega` (post-resolution shipping)
- `code-review` / `polyglot-code-reviewer` (optional final pass before ship)
