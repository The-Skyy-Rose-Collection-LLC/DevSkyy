---
name: test-isolation
description: Use when writing or debugging tests that pass alone but fail (or mutate the repo) in a full-suite run — enforce per-test isolation and environment-aware gating so tests never share state or depend on excluded trees.
origin: SkyyRose
---

# Test Isolation

The most dangerous test in this codebase is not one that fails — it is one that passes
**only because of who ran before it**. A test that is green alone but red in the full
suite is not tested, it is lucky. Worse: a test that silently rewrites tracked files isn't
a test at all, it's an uncommitted mutation wearing a green checkmark. This is **bug-231**
(recurred ×4) — shared-state pollution surfacing only in full-suite runs — and **bug-250**
(today) — a `test_verify_drift` run that executed the collection-SOT builder IN-TREE and
silently rewrote tracked `wordpress-theme/.../collections/*/sot.json`.

> **Boot first:** read the canonical sources — `SOT.md` → `.wolf/anatomy.md` →
> `.wolf/cerebrum.md` → `.wolf/buglog.json` (grep `bug-231` and `bug-250` — the leak may
> already be logged) → `CLAUDE.md`. Do not fix an isolation bug from memory.

## When to Use

- A test passes with `pytest tests/test_x.py -v` but fails inside `pytest tests/ -v`.
- Any test that reads/writes `/tmp` directly, sets `os.environ[...]`, or touches a module-
  level cache, singleton, or class attribute.
- Any test that reads `assets/`, `archive/`, `renders/`, or `screenshots/` — sparse
  worktrees deliberately exclude these trees; see [[fail-closed-audit]] for why an absent
  path must not silently mean "skip everywhere."
- Before trusting a green test that runs a generator/builder against real repo files —
  pair with [[fail-closed-audit]]'s rule on never regenerating-then-verifying its own output.
- After any session where you edited the same test file more than twice to get it green.

## Method

1. **Per-test `tmp_path`, never a hardcoded path.** Use the `tmp_path` / `tmp_path_factory`
   fixture for every file the test writes. A literal `/tmp/...` string is shared across
   parallel test workers and across runs — that's the bug-231 signature.
2. **`monkeypatch.setenv` / `monkeypatch.delenv`, never `os.environ[...] = ...`.** Direct
   environment mutation leaks into every test that runs after it in the same process;
   `monkeypatch` reverts automatically at test teardown even on failure.
3. **Reset shared singletons and caches in a fixture, not by convention.** If a module
   holds a cache, a connection pool, or a class-level registry, the fixture must reset it
   on setup (and ideally teardown) — "the next test will probably reset it" is how bug-231
   recurred four times.
4. **Sparse-aware skips must stay fail-closed.** A test that needs `assets/`, `archive/`,
   `renders/`, or `screenshots/` may skip **only** when `git config core.sparseCheckout`
   is `true` **and** the path is genuinely absent — use `tests/sparse_guard.py::requires_tree`
   for this check. A full checkout or CI runner with a genuinely missing tree must still
   **fail**, not skip. Skipping unconditionally on "path not found" hides real regressions
   the moment someone runs the suite from a non-sparse clone. This is the fail-closed rule
   from [[fail-closed-audit]] applied to test collection itself.
5. **Never write to the tracked tree from a test.** If a test exercises a builder/generator
   that writes to a real repo path (e.g. `collections/*/sot.json`), redirect its output to
   `tmp_path` via a fixture-injected output root or dependency override — do not let it run
   against the live working tree, in-place, ever. bug-250 is what happens when this is
   skipped: a "verify drift" test became a silent write.

## Loop until isolated

Bounded, like [[drive-to-green]] — never more than 5 turns, stop if the same result
repeats twice (that is guessing, not isolating):

```
1. Run the test ALONE (pytest tests/test_x.py::test_name -v) → read the result.
2. Run the FULL suite (pytest tests/ -v) → read the result for the same test.
3. Run `git status --short` after the full suite → must be empty. Non-empty = mutation.
4. If alone≠full-suite or git status is dirty → find the leak (env, cache, file, order
   dependency) and fix it per Method above.
5. Repeat 1-3. Stop when alone == full-suite AND git status --short is clean.
```

## Verify from an authoritative source

The fix is only real if both runs are **observed**, never assumed:

- **Run the test both ways and READ both results** — don't infer full-suite behavior from
  the isolated pass. `rtk proxy pytest` gives the true exit code; a bare `pytest` can
  falsely report "no tests collected" on a broken collection.
- **Run twice** — a fix that isolates state should be deterministic; if the second run
  differs from the first, the leak isn't fixed, it's relocated.
- **`git status --short` after the full suite must show zero tracked-file changes.** Any
  diff — even a whitespace-only rewrite of a generated file — is a hard fail. This is the
  check that would have caught bug-250 before it shipped.
- **Cite `file:line`** for the fixture or `monkeypatch` call that closed the leak; quote
  the actual code, not a paraphrase.

## Adversarial pass

- **After** the fix: [[adversarial-verification]] — try to REFUTE "it's isolated now." Run
  the suite in a different order (`pytest tests/ -p no:randomly` vs. shuffled), from a
  non-sparse clone, and from a fresh `tmp_path` root. Default to "still leaking" until
  independently proven otherwise.

## Guardrails · Handoff · Log

- Never hardcode `/tmp` or a literal path a test writes to — `tmp_path` only.
- Never mutate the real environment or the tracked working tree from a test — `monkeypatch`
  and injected output roots only.
- Fail-open skip logic (a sparse-tree skip that also skips in full checkouts) is a
  [[fail-closed-audit]] defect — audit it there, fix it here.
- A test-isolation fix that leaves the suite green only by accident → drive it properly
  with [[drive-to-green]], then re-verify with this skill.
- Log every isolation leak or tree-mutation to `.wolf/buglog.json` under the `bug-231` (or
  `bug-250`) lineage — bump `occurrences`, never duplicate — run
  `scripts/wolf_recurring_sync.py`, and record the lesson via [[continuous-learning]].
- Handoff per `CROSS-PLUGIN.md`: isolation defects that trace to backend/service code go to
  `skyyrose-core`; theme/build-output defects go to `skyyrose-design` — then **re-verify
  here** before calling the suite closed.
