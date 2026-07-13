---
name: fail-closed-audit
description: Use when reviewing any gate, guard, validator, or permission check — audit that it FAILS CLOSED (absent input/config/token/manifest → block, never pass). Prevents the fail-open pattern (bug-230) where a gate silently succeeds because its input is missing.
origin: SkyyRose
---

# Fail-Closed Audit

The most dangerous defect in this codebase is not a gate that fails — it is a gate that
**passes when it should not**. A guard whose input is absent, whose config is missing, or
whose token is unset, and which therefore returns "OK", is unfalsifiable: it looks green
while protecting nothing. This is **bug-230** (recurred ×6) and it has bitten imagery
gates, embedding gates, encryption-key loading, and the per-collection SOT drift check.

> **Boot first:** read the canonical sources — `SOT.md` → `.wolf/anatomy.md` →
> `.wolf/cerebrum.md` → `.wolf/buglog.json` (grep `bug-230` — the offender may already be
> logged) → `CLAUDE.md`. Do not audit from memory.

## When to Use

- Reviewing any `verify_*` / `validate_*` / `check_*` / `require_*` / `_gate` function.
- Any `if not X: return ok`, `except: return default`, `getenv(...) or <fallback>`.
- Before trusting a green test that exercises a guard — pair with [[mutation-testing]].
- Any manifest / credential / config load that has a "not present" branch.

## The one rule

**Every gate fails CLOSED. Absent manifest / config / token / key = BLOCK, never pass.**
A check that cannot return "no" is not verification — it is a guess with a citation.

## Method

1. **Find the absent-input branch** — what does the guard do when its input is missing,
   empty, unreadable, or unparseable? Trace the `else` / `except` / `... or default` path.
2. **Classify** — does that branch BLOCK (raise / return a failing verdict / refuse) or
   PASS (return ok / generate an ephemeral fallback / skip silently)?
3. **If it passes → fail-open defect.** Rewrite it to block. Real repo precedents:
   - Encryption: `ENCRYPTION_MASTER_KEY` unset in production must `raise`, not mint an
     ephemeral key (silent data loss on restart) — mirror JWT's `_require_secret()`
     `ENVIRONMENT=production` guard.
   - Asset/imagery manifest: a missing `manifest.json` returns a `manifest_missing`
     finding that blocks the paid run — not "zero drift → clean".
   - Generated-artifact guard: never regenerate-then-verify its **own** output (it always
     agrees with itself); compare against the committed tree.
4. **Allow a deliberate skip only when provably deliberate** — e.g. skip in a sparse
   worktree *only* when `core.sparseCheckout=true` AND the path is absent; a full checkout
   with a genuinely missing tree must still fail (see [[test-isolation]]).

## Loop until closed

Bounded, like [[drive-to-green]] — never more than 5 turns, stop if the same result
repeats twice (that is guessing, not auditing):

```
1. Pick a guard.  2. Delete/empty its input (env unset, file removed, token blank).
3. Run the guard → does it BLOCK?  4. If it passes → fix the branch to raise/refuse.
5. Re-run step 2-3.  Repeat for every guard in the surface.  Stop when all block.
```

## Verify from an authoritative source

The audit is only real if the "block" is **observed**, never assumed:

- **Run it with the input removed and read the outcome** — `monkeypatch.delenv(...)` /
  delete the manifest / blank the token, then assert it raises / returns a failing verdict.
  The check must be able to return "no".
- **Prove falsifiability** — disable the guard (mutate it to a no-op) and confirm the
  test now FAILS; restore. If the test still passes with the guard gone, the test never
  tested the guard. This is [[mutation-testing]].
- **Cite `file:line`** for the fixed branch; quote the raising code, not a paraphrase.

## Adversarial pass

- **Before** wide audits: [[adversarial-planning]] — have a genuinely different model
  (Codex via `codex exec`) name the guard you'd *miss*.
- **After** the fix: [[adversarial-verification]] — try to REFUTE "it fails closed now";
  default to fail-open until independently proven otherwise. For security/credential
  guards, use ≥2 skeptics.

## Guardrails · Handoff · Log

- A fix that leaves any absent-input branch returning "ok" is not a fix.
- Backend/security fail-open → hand to `skyyrose-core`; imagery/theme → `skyyrose-design`
  (see `CROSS-PLUGIN.md`), then **re-verify here**.
- Log every fail-open to `.wolf/buglog.json` under the `bug-230` lineage (bump
  `occurrences`, never duplicate), run `scripts/wolf_recurring_sync.py`, and record the
  lesson via [[continuous-learning]].
