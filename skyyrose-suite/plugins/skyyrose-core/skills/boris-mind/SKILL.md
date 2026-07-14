---
name: boris-mind
description: Use to work the way the Claude Code team works — parallelize aggressively across worktrees and subagents, plan before non-trivial work, verify everything, and reach for /loop, /batch, /simplify, and effort:max on the right tasks. The power-user operating posture, distilled.
origin: SkyyRose
---

# Boris Mind

The single biggest productivity unlock is **parallelism** — the Claude Code team runs
3-5 sessions at once, one per git worktree, and delegates independent work to subagents.
This skill makes that posture the team default: spread work wide, plan before you build,
and prove every result. It distills the `boris` skill (Boris Cherny's workflow tips) into
an operating stance the SkyyRose pods practice, not a tip sheet you read once.

> **Boot first:** `CLAUDE.md` (autonomy boundary + STOP-AND-SHOW), `.wolf/cerebrum.md`
> (User Preferences), and `CROSS-PLUGIN.md` (which pod owns what). Parallelism without
> the guardrails is just faster mistakes.

## When to Use

- Any task with independent sub-parts (fan them out — never serialize independent work).
- Before starting anything non-trivial (3+ steps or an architectural call) → plan first.
- A recurring or scheduled job → `/loop`; a repeated migration across many files → `/batch`.
- Hard reasoning (design, gnarly bug) → raise reasoning effort (`effort:max`).
- After writing code → dispatch a review agent; before shipping → verify.

## The posture

1. **Parallelize by default.** Decompose into independent units and dispatch them in ONE
   message as parallel subagents (or separate worktrees). Reserve `isolation: worktree`
   for agents that mutate files concurrently. Never run in series what has no shared state.
2. **Plan before building.** For non-trivial work, plan first (state it, get the shape
   right), then execute the whole plan without pausing between steps. Pair with
   [[adversarial-planning]] when a wrong plan is expensive to discover late.
3. **Delegate, don't hoard context.** Offload research, exploration, and per-file work to
   subagents; keep the main thread clean. One task per subagent, focused.
4. **Right tool for the task.** `/simplify` for quality passes, `/batch` for parallel
   migrations, `/loop` for recurring jobs, code-review agents after writing, higher effort
   for the hardest reasoning. Match the instrument to the work.
5. **Memory is context.** Keep `CLAUDE.md` / `.wolf/*` current so every session and
   subagent starts oriented — see [[memory-system]] and [[self-learning]].

## Loop until the work is spread and proven

Bounded, like [[drive-to-green]] — ≤5 turns, stop if the shape stops improving:

```
1. Decompose the task into independent units.
2. Fan them out (parallel subagents / worktrees) — plan-first for non-trivial ones.
3. Collect results; a review agent checks the code, a verifier re-derives evidence.
4. If a unit is wrong → re-dispatch just that unit → re-verify.  Stop when all pass.
```

## Verify from an authoritative source

Parallel speed is worthless if the results are unchecked:

- **Never trust a subagent's word.** The main thread independently re-derives every
  "done" — re-run the exact test, re-grep the footprint, re-check `git diff` scope — the
  [[adversarial-verification]] and [[self-healing]] pattern. A green report is a claim,
  not proof.
- **Confirm the fan-out actually converged** — read each unit's real output/diff, not its
  summary; a subagent that returned `null` (skipped or died) is a hole, not a success.
- **Scope check** — `git diff --name-only` shows only the paths this task should touch.

## Adversarial pass

- **Before** a big fan-out: [[adversarial-planning]] — a genuinely different model
  (Codex via `codex exec`) challenges the decomposition before you spend the compute.
- **After**: [[adversarial-verification]] — default to "not done" until independently proven.

## Guardrails · Handoff · Log

- Parallelism does not relax the [[cost-governance-gate]]: money / production / irreversible
  actions still STOP-AND-SHOW, even mid-fan-out.
- Autonomy means finishing without hand-holding **after** the plan and inputs are set — it
  never means deciding what to deploy or spend without checking (`CLAUDE.md`).
- Route each unit to its owning pod per `CROSS-PLUGIN.md`; log reusable workflow lessons via
  [[continuous-learning]]. Pairs with [[efficient-production]] and [[token-aware-behavior]]
  for tool- and context-discipline while running wide.
