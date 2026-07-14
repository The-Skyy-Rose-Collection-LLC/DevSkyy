---
name: self-healing
description: Use when an authoritative signal reports a regression (failing test, live HTTP/size/PHP-error, canon drift) — diagnose the ROOT CAUSE, fix the source, and confirm the heal by INDEPENDENTLY re-deriving fresh evidence, not by trusting the fix's self-report.
origin: SkyyRose
---

# Self-Healing

A heal that trusts its own self-report is not a heal — it is a claim. The failure mode is
symmetric with fail-open gates: a doctor patches the symptom, marks `healed: true`, and the
next authoritative check (a fresh test run, a cache-busted curl) shows the regression never
left. This skill governs the loop from detection to a heal that has been proven, not
asserted — by a party other than the one who made the fix.

> **Boot first:** read `.wolf/buglog.json` — the fix may already be known — then `SOT.md`
> for canonical product/imagery/brand facts and `CLAUDE.md`'s verification matrix (pick the
> authoritative method by the *kind* of regression; never verify a live page with a grep or
> a test failure with a screenshot). Do not heal from memory.

## When to Use

- A failing test or broken build (pytest, phpcs, `npm run build`).
- A live-page regression on skyyrose.co — HTTP status, response size, PHP-error markers
  (theme-heal's S1 class).
- Canon drift — brand tokens, catalog/dossier facts, or collection copy diverged from SOT
  (S2), or a stale asset version serving a cached/superseded build (S3).
- Any broken gate that itself needs healing (pair with [[fail-closed-audit]] first — don't
  heal a gate by loosening it).

Composable surfaces already in this repo: the `theme-heal-doctor` / `theme-heal-verifier`
agent pair for live skyyrose.co regressions, `autonomous-issue-diagnose-fix` for the
harder-issue tier, and the `devskyy_self_healing` MCP tool for programmatic dispatch. This
skill is the doctrine those surfaces implement — read it before dispatching any of them.

## Method

1. **Detect from an authoritative signal** — a real test run, a cache-busted `curl`, a
   `phpcs`/`php -l` pass, a fresh screenshot. Never start from a stale report or a
   self-graded "looks fixed."
2. **Diagnose the ROOT CAUSE, not the symptom.** This is the theme-heal-doctor discipline:
   reproduce the fault against both live and source before touching anything. A patch that
   makes the symptom disappear without explaining why it appeared is not a diagnosis.
3. **Fix the SOURCE.** Edit the originating file (not a downstream cache, not the `.min`
   build, not the test that observes it). For WordPress theme regressions: edit source PHP,
   then rebuild `.min` — never hand-edit the built artifact.
4. **Independently re-verify** — see below. The fix is not done until someone other than the
   fixer (a fresh agent, a fresh command) re-derives the evidence.
5. **Loop or escalate** — see the bounded loop below. Escalation is not failure: a genuinely
   uncertain root cause is exactly what `autonomous-issue-diagnose-fix` exists for — it runs
   parallel independent fix hypotheses through adversarial verification instead of one
   agent's self-graded pass.

## Loop until healed

Bounded, like [[drive-to-green]] — never more than 5 turns, stop if the same failure
repeats twice in a row (that's guessing, not healing):

```
1. Fix the source.  2. Re-run the EXACT authoritative check that first reported the
   regression (same test, same cache-busted URL, same phpcs target — not a paraphrase).
3. Independently re-derive evidence (see below) — do not accept the fixer's self-report.
4. Still broken → repeat from 1.  5. Same error twice in a row → STOP, escalate to
   autonomous-issue-diagnose-fix (parallel independent hypotheses + adversarial grading)
   rather than guessing a third time.
```

## Verify from an authoritative source

The heal is confirmed ONLY by INDEPENDENT re-derivation of FRESH evidence — never the
healer's self-graded report. This is the theme-heal-verifier pattern: it re-runs a fresh
`curl` (cache-busted), a fresh `grep` against source, a fresh `phpcs`/`php -l`, and a fresh
screenshot itself — it does not read the doctor's "healed: true" and nod along.

- **Re-run, don't re-read.** A second pass over the doctor's own transcript is not
  verification; a fresh command invocation is.
- **Default to skeptical** — the verifier's starting assumption is STILL BROKEN. The doctor
  must produce evidence that survives independent re-derivation, not merely restate its fix.
- **Match the check to the claim** — per `CLAUDE.md`'s verification matrix: live-page claim
  → cache-busted `curl` + Playwright eyes-on (mobile + desktop); test claim → `pytest -v`
  output from this session; canon-drift claim → catalog CSV / dossier / SOT.md diff, not
  memory.
- **Cite `file:line`** for the fixed branch and the fresh command's literal output — not a
  paraphrase of what should happen.

## Adversarial pass

- The verifier **IS** the adversary — [[adversarial-verification]] is not an optional extra
  step here, it *is* the re-verify step. Try to REFUTE "it's healed"; a heal that survives
  one honest attempt to break it again is real, one that doesn't survive is not.
- Pair with [[fail-closed-audit]] before declaring a gate healed: a "fix" that makes the
  gate pass by loosening its check (widening a threshold, catching-and-ignoring an
  exception, deleting the assertion) is a fail-open regression wearing a heal's clothes —
  reject it the same way you'd reject any other fail-open defect.

## Guardrails · Handoff · Log

- Fix the code, never the test. Fix the ROOT CAUSE, never the symptom — a patch that only
  suppresses the symptom will resurface, and resurfacing is what trips the ×2 escalation.
- Neither the doctor nor the verifier deploys, commits, bumps versions, or edits
  permissions — those steps happen only after independent verification passes, per the
  STOP-AND-SHOW gate in `CLAUDE.md`.
- Route backend↔theme fixes per `CROSS-PLUGIN.md`: `skyyrose-core` owns backend/security
  root causes, `skyyrose-design` owns imagery/theme root causes — hand off, then
  **re-verify here** after the handoff returns.
- Log every heal to `.wolf/buglog.json` (root_cause, fix, occurrences — bump, never
  duplicate), run `scripts/wolf_recurring_sync.py` when `occurrences >= 2`, and record the
  lesson via [[continuous-learning]].
