---
name: adversarial-planning
description: Have two genuinely different models (a Claude model, e.g. Fable, and Codex/OpenAI) debate a plan before anything gets built — one drafts, the other challenges, capped at 3 rounds, then the strongest coding model actually executes the converged plan and the planner reviews the real result. Use for any task where a wrong plan is expensive to discover late (rigging/animation work, architecture decisions, migrations) — not for small, obviously-correct changes.
---

# Adversarial Planning

## The problem

A single model planning alone has one blind spot: its own. It can catch its own typos,
not its own bad assumptions — the plan sounds coherent because the same reasoning that
wrote it is the reasoning checking it. [[adversarial-verification]]
solves this for "did the fix work"; this skill solves it one step earlier, for "is the
plan itself sound before anyone spends an hour building the wrong thing."

## The pattern

1. **Planner drafts** (Claude, e.g. `model: 'fable'`) — a real plan: steps, files touched,
   what could go wrong, how each step is verified. Not a paragraph of vibes.
2. **Challenger is a genuinely different model** (Codex/OpenAI, via `codex exec`) — different
   training, different failure modes. It challenges the plan's assumptions, not its prose.
3. **Debate is capped at 3 rounds** — rounds 1-2 are argument, round 3 is a forcing function.
4. **Execution goes to the strongest coding model for the job** (here, Codex), not
   automatically back to the planner.
5. **Planner reviews the real executed result** — the actual diff/output, not the plan in
   the abstract. Closing the loop against ground truth, not against more argument.

```
Plan (Fable)  →  Debate (Fable vs Codex, ≤3 rounds)  →  Execute (Codex)  →  Review (Fable)
```

## Round structure (mirrors adversarial-verification's 3-round cap)

1. **Round 1 — proposal + challenge.** Planner drafts. Challenger reads it skeptically and
   must name specifically what would change its mind (a missing edge case, an untested
   assumption, a step that can't actually be verified as described).
2. **Round 2 — revision + recheck.** Planner addresses the _specific_ challenge, not a full
   rewrite. Challenger rechecks. If satisfied, stop — don't burn round 3 on agreement.
3. **Round 3 — mandatory, no more argument.** If rounds 1-2 didn't converge, stop debating in
   the abstract and **execute** — the real build is the tie-breaker. Lock in whichever plan
   exists and hand it to the executor; don't let round 3 become "argue again, harder."

## Codex is not reachable via `agent()`'s `model` option

`agent()` (Workflow tool) only spawns Claude models (`sonnet`/`opus`/`haiku`/`fable`). Codex
is a separate CLI with its own auth; a Workflow script has no shell access, so it can't
invoke `codex` directly. **Fix:** dispatch a Claude subagent whose entire job is to shell out
to `codex exec` via Bash and relay the raw output **verbatim** — not paraphrased. A Claude
summary of Codex's judgment defeats the whole point of a second model. The runnable script
(below) does this and preserves Codex's exact words in a `codex_verbatim` field.

```bash
# Verified CLI mechanics (codex-cli 0.144.1, re-checked via --help 2026-07-12, not assumed):
codex exec -m <MODEL> -s <read-only|workspace-write> --json -o /tmp/out.json < prompt.txt
# -m/--model     explicit model string
# -s/--sandbox   read-only for challenge/review turns; workspace-write ONLY for execution
# --json         machine-readable event stream
# -o             final message written to a file, easy to read back
# Pipe the prompt over stdin (as shown) — never interpolate plan JSON into the shell command.
```

## Model verification — do not hardcode a guessed model string

Re-verified live 2026-07-12: `~/.codex/config.toml` now has `model = "gpt-5.6-sol"` (the
"GPT-5.6 Sol" this skill only speculated about at first writing is now the real, configured,
callable default; the old `gpt-5.5` is stale). This is exactly why the string is verified at
runtime, never hardcoded blind — it moved once already. Before a debate that depends on a
specific Codex model:

1. Run `codex doctor` — it once caught a real "required provider endpoint unreachable" failure
   despite valid auth. If reachability fails, surface it; don't silently retry or fall back.
2. **STOP-AND-SHOW** a tiny test call (`codex exec -m <candidate> "reply with the single word
OK"`) — a real paid call, gated like any other. If it errors on the model string, fall back
   to the confirmed default and tell the user which model actually ran — never silently
   substitute.
3. Pass the confirmed string as `args.codexModel` to the script.

## Running it

The full loop — the three schemas, the 3-round debate, the Codex relay, execute, and review —
lives in a runnable Workflow script: **[`scripts/adversarial-planning.wf.js`](scripts/adversarial-planning.wf.js)**.
`PLAN_SCHEMA` forces structured steps (action / files / per-step verification / risks) so each
revision has something concrete to diff. `CHALLENGE_SCHEMA` returns `{ codex_verbatim,
satisfied, specific_challenge }` — the verbatim preserves what Codex said, `satisfied` drives
early convergence. `REVIEW_SCHEMA` forces a ship/no-ship boolean plus specific deviations.

**This run spends real money** — every challenge round and the execution turn is a paid Codex
call. Pre-flight per "Model verification" above, then **STOP-AND-SHOW the launch** (model +
rounds + est. cost) before invoking:

```js
Workflow({
  scriptPath: "<skill-dir>/scripts/adversarial-planning.wf.js",
  args: {
    task: "<the plan/task to debate>",
    codexModel: "gpt-5.6-sol" /* the CONFIRMED string */,
  },
});
```

It returns `{ rounds, converged, plan, transcript, execution, review }`. Read `review.ship`
and `review.deviations` against `execution.codex_verbatim` before trusting the result.

## When not to use this

Small, obviously-correct changes don't need two models arguing — that's
adversarial-verification's territory (verify after, cheaply) or just doing the thing. Reserve
the full debate-then-execute loop for plans where being wrong is expensive to discover late:
new rigs/animation pipelines, architecture decisions, migrations — anything where "the plan
looked fine and then three hours in it wasn't" is a real risk this project has hit (see
`.wolf/buglog.json` bug-198/214/215 for exactly that pattern on the mascot rig work).
