---
name: mutation-testing
description: Use before trusting any green test — prove the test can actually FAIL by mutating the code it covers. A test that still passes when its target is broken tested nothing.
origin: SkyyRose
---

# Mutation Testing

A passing test is worthless if it cannot fail. Green is not evidence — it is a claim.
The only way to cash that claim is to break the code the test claims to cover and watch
the test catch it. If the test stays green while the code is provably broken, the test
never exercised the code; it was decoration, not verification. This session proved two
real fixes this way: an AES fail-closed guard and a brand-assets bulk-ingestion job.

> **Boot first:** read the canonical sources — `SOT.md` → `.wolf/anatomy.md` →
> `.wolf/cerebrum.md` → `.wolf/buglog.json` → `CLAUDE.md`. Do not trust a green suite
> from memory; re-run it this session before mutating anything.

## When to Use

- Before marking any bug fix or new guard "done" — pair with [[fail-closed-audit]] when
  the code under test is a gate/validator.
- Any test whose assertion you did not personally watch fail at least once.
- A test that was written to match the implementation instead of the requirement (the
  classic trap: code and test were authored together and agree by construction).
- Reviewing someone else's "tests pass" claim before accepting a PR or a subagent's report.

## Method

1. **Pick a critical assertion** — the one line that, if false, means the fix does not
   hold. Not every assertion in the file; the one that carries the claim.
2. **Apply the smallest plausible mutation** to the code it covers — the kind of bug a
   careless edit would actually introduce. Real examples from this repo:
   - AES fail-closed: `elif os.getenv("ENVIRONMENT", "").lower() == "production": raise
     EncryptionError(...)` mutated to `elif False:` — deletes the guard without touching
     surrounding structure.
   - Brand-assets bulk ingestion finalize branch: `if job_row.failed == 0:` mutated to
     `if job_row.failed >= 0:` (always true), and the counter `job_row.failed += 1`
     mutated to `job_row.failed += 0` (never increments) — two independent ways the same
     branch could silently stop tracking failures.
3. **Run only that test** — not the whole suite. Isolate signal.
4. **It MUST fail.** If it passes, the test is inert — go to Guardrails, do not proceed.
5. **Restore the mutation immediately** and re-run to confirm baseline green. A mutation
   left in place is a bug you just introduced, not a finding.

## Loop until every assertion is proven

Bounded, like [[drive-to-green]] — never more than 5 turns per assertion, stop if the same
result repeats twice (that is guessing, not testing):

```
1. Pick the next critical assertion.  2. Mutate the smallest plausible thing it covers.
3. Run that one test → does it FAIL?  4. If it passes → the test is inert, fix the test.
5. Restore → confirm baseline green.  Repeat for every critical assertion. Stop when all
   are proven falsifiable.
```

## Verify from an authoritative source

The proof is only real if the failure was **observed**, never assumed:

- **Run the mutated code and read the output** — do not predict the failure, capture it.
  The AES mutation produced the literal assertion message `DID NOT RAISE EncryptionError`;
  the brand-assets mutation produced `assert 'completed' == 'partial'`. Cite the exact
  failing message, not a paraphrase of what you expected it to say.
- **A mutation that leaves the test green proves the test is inert — it proves nothing
  about whether the original code is right.** Do not read "still passes" as "code is
  correct"; read it as "this test cannot see this bug."
- **Restore-and-reconfirm is not optional** — baseline green after restoring the mutation
  is the other half of the proof; skipping it means you don't know whether you fixed the
  mutation or broke something else.

## Adversarial pass

- [[adversarial-verification]] — before calling an assertion proven, have a skeptic
  propose the mutation you would miss: an off-by-one in the opposite direction, a
  boundary condition (`==` vs `>=`), a counter that increments the wrong variable, an
  error swallowed instead of raised. The two brand-assets mutations above are exactly
  this pattern — same branch, two different ways to defeat it.
- If the skeptic's mutation also gets caught, the test is stronger than the one you
  picked alone. If it slips through, you found a real gap — fix the test, not the mutation.

## Guardrails · Handoff · Log

- Never weaken a test to make it pass under mutation — that is hiding the gap, not
  closing it. Strengthen the assertion until the mutation is caught.
- A test that stays green under every mutation you tried has not "passed the mutation
  test" — it has failed it. Fix the test before trusting the fix.
- Gate/guard code whose fail-open branch you're mutating → [[fail-closed-audit]] first,
  mutation-testing second, to confirm the fix both fails closed AND is falsifiable.
- Cross-plugin fixes (backend vs imagery vs theme) hand off per `CROSS-PLUGIN.md`, then
  **re-verify here** before trusting the receiving plugin's green.
- Bounded loops that don't converge → [[drive-to-green]]; final claim of "done" still
  needs [[verification-loop]].
- Log every inert-test finding to `.wolf/buglog.json` (tag `mutation-testing`, cross-link
  `bug-230` lineage if the inert test was covering a fail-open gate), and record the
  lesson via [[continuous-learning]].
