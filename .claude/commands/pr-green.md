Drive a single pull request to green using the `pr-green-loop` agent. $ARGUMENTS

Dispatch the **pr-green-loop** agent on the DevSkyy repository for the PR number in `$ARGUMENTS`. The agent monitors CI checks AND review comments (human + bots), fixes the root cause on the PR's own head branch, verifies locally, pushes, and loops until every gating check is green and every actionable review thread is resolved.

## Usage

```
/pr-green 582        — loop PR #582 until green + comments resolved
/pr-green            — no number: agent lists your open PRs and asks which
```

## What it does

1. Resolves the PR's head branch and checks it out (pushes directly to it — no worktree, no fix-PRs).
2. Snapshots CI (`gh pr checks`) + mergeability + unresolved review threads (GraphQL).
3. Triages every signal into REAL vs DevSkyy-NOISE (e.g. `PR Agent Analysis` concurrency-cancel, Vercel preview, account-block jobs, `skipping` checks).
4. Fixes the real cause, verifies locally against the DevSkyy matrix (`.venv/bin/python -m pytest`, ruff/black/mypy, frontend build, phpcs), commits, pushes.
5. Resolves review threads only after the code actually addresses them; treats bot reviewers (CodeRabbit/cubic/claude-review) as advisory leads to verify.
6. Loops until green, scheduling wake-ups when CI needs minutes.

## What it will NOT do (boundaries)

- Never merges to `main` (green ≠ merge — that's your call).
- Never force-pushes, deploys to skyyrose.co, writes to WooCommerce/media, or calls a paid API. Those stop and ask for `y`.
- Never overrides a human `CHANGES_REQUESTED` — reports and stops.
- Never weakens a test or suppresses a check to go green.

## Difference from `/pr-auto`

`/pr-auto` (pr-automator) audits ALL PRs in an isolated worktree and opens fix-PRs for your review. `/pr-green` owns ONE PR and pushes fixes straight to its branch until it's merge-ready.
