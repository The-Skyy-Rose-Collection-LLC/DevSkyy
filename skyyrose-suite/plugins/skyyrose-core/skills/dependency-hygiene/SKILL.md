---
name: dependency-hygiene
description: Use when adding, upgrading, or resolving Python/Node dependencies — declare every import, cap majors to stop silent drift, and keep the resolver consistent. Prevents undeclared-import and silent-major-bump defects.
origin: SkyyRose
---

# Dependency Hygiene

An honest dependency graph is not "the install works" — it is **declare-what-you-import**
plus **cap-majors-that-matter**, so the resolver's output is deterministic instead of
whatever the last `pip install` happened to land on. This is **bug-254**: a shared venv
silently drifted from openai 1.x to openai 2.45.0 because nothing capped it, and the graph
had a load-bearing import (`litellm`) that was never declared at all.

> **Boot first:** read `pyproject.toml` (the dependency groups and their inline rationale
> comments) → `.wolf/buglog.json` (grep `bug-254` — the reference case is already logged)
> → `CLAUDE.md`. Do not pin from memory of what a library "usually" needs.

## When to Use

- Adding a new `import`/`require` that isn't already in `pyproject.toml` / `package.json`.
- Upgrading any dependency, especially a transitive one pulled in by another package.
- `pip check` / `npm ls` reports a conflict, or `pip install -e ".[all]"` takes 20+ minutes
  backtracking.
- Before trusting a green install after adding an optional extras group.

## Method

1. **Every top-level import is declared.** If a file does `import litellm` or
   `require("boto3")`, that package name is in `pyproject.toml` (or `package.json`) in a
   group that actually gets installed for that code path — not assumed present because a
   sibling dependency happens to pull it in transitively. `litellm/providers/
   litellm_provider.py` imported `litellm` while it was undeclared in every group; the
   only reason `pip check` ever saw it was because something else's transitive graph
   happened to install it.
2. **Cap majors on load-bearing libraries.** A library your codebase has a specific client
   contract with (the openai 1.x SDK surface, in this repo's case) gets an explicit
   `<major+1` ceiling — `"openai>=1.6,<2"` — not just a floor. Without the ceiling, a
   transitive pin from an unrelated package (litellm's own `openai==2.30.0` requirement)
   can silently bump the whole shared venv to a major your code was never verified against.
   Document *why* the cap sits where it does, inline, next to the pin — see
   `pyproject.toml:93-97` (`litellm>=1.80,<1.81` — 1.80.x is the last line admitting
   openai 1.x; 1.81+ requires openai>=2.8) as the pattern to follow.
3. **Prefer `uv pip install` when pip's resolver backtracks.** Plain `pip install -e
   ".[all]"` spent 20+ minutes backtracking through the openai/litellm conflict; `uv pip
   install` resolved the same graph in seconds. Reach for `uv` first on any group with
   more than a few pinned ranges.
4. **Never hardcode secrets while touching dependency config.** API keys some new
   integration needs go in `.env` / `.env.secrets` via env vars, never inline in
   `pyproject.toml`, a lockfile, or a test fixture — see `CLAUDE.md` Critical Rules.

## Loop until pip check is clean

Bounded, like [[drive-to-green]] — never more than 5 turns, stop if the same conflict
repeats twice (that's guessing, not resolving):

```
1. Change one dependency (declare / bump / cap).
2. Run `pip check` (or `npm ls` for Node).
3. Run the test suite for the affected module.
4. On conflict: cap the offending major or declare the missing import — never delete
   the constraint that's complaining just to make the tool quiet.
5. Repeat from step 2. Stop when `pip check` prints clean AND the affected suite passes.
```

## Verify from an authoritative source

- **`pip check` must print "No broken requirements found."** Not "fewer errors than
  before" — clean, full stop. Same bar for `npm ls` (no `UNMET DEPENDENCY` / `invalid`
  lines).
- **Grep every top-level import against `pyproject.toml`** to prove each is declared in a
  group that's actually installed for that code path — don't trust that an editable
  install "just has it." This is how bug-254's undeclared `litellm` import and the
  installed-but-undeclared `boto3` fallback (`integrations/cloudflare_r2_manager.py:6`)
  were both found.
- **Re-run the affected test suite after any dependency change** — a clean resolver
  doesn't prove the code still behaves against the newly-resolved version.
- **Use Context7 for version facts** (`resolve-library-id` → `query-docs`) before pinning
  a range — never trust training data on what a library's current major requires; that's
  exactly how the openai/litellm version boundary got missed the first time.

## Adversarial pass

Link [[adversarial-verification]] before calling the graph settled — have an independent
pass try to refute "the dependency graph is consistent": pick one declared pin and ask
whether its stated reason (the inline comment next to it) is still true today, and whether
any *other* installed package's transitive requirement could silently violate it on the
next `pip install`.

## Guardrails · Handoff · Log

- An undeclared import is a **fail-open in the dependency graph** — the install "works"
  today only by accident of some other package's transitive pull. Cross-ref
  [[fail-closed-audit]]: the same "absent input silently passes" pattern, just at the
  resolver layer instead of a runtime gate.
- Backend dependency changes stay in `skyyrose-core`; if a fix requires touching imagery
  or theme build tooling, hand off per `CROSS-PLUGIN.md`, then **re-verify `pip check`
  here** after the handoff lands.
- Log every undeclared-import or silent-major-bump find to `.wolf/buglog.json` under the
  `bug-254` lineage (bump `occurrences`, never duplicate), run
  `scripts/wolf_recurring_sync.py`, and record the lesson via [[continuous-learning]].
