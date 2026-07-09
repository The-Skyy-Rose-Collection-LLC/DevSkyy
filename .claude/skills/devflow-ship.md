---
name: devflow-ship
description: Composite pre-push gate — runs lint → security → tests fail-fast, then advisory clean-tree + changelog checks. The single yes/no answer before pushing. Use right before git push or opening a PR.
---

# Devflow Ship

The final gate. Composes `review.sh` + `security.sh` + `tdd.sh` in cheap→expensive order and **stops at the first hard failure** — so an obvious lint error never burns time running the full test suite.

It is not the iteration tool. Iterate with `devflow-review` / `devflow-security` / `devflow-tdd`. `ship` only answers: *can this be pushed, yes or no.*

## Run the gate

```bash
# Gate this branch vs main (or working changes when on main)
bash scripts/devworkflows/ship.sh

# Override base branch
bash scripts/devworkflows/ship.sh --base develop

# Make changelog + clean-tree HARD failures
bash scripts/devworkflows/ship.sh --strict
```

**Exit 0** = ready to push. **Exit 1** = blocked — the message names the exact stage.

## Stage order

| # | Stage | Tool | Type | On fail |
|---|-------|------|------|---------|
| 1 | lint | `review.sh` | hard | stop, exit 1 |
| 2 | security | `security.sh` | hard | stop, exit 1 |
| 3 | tests | `tdd.sh` (full suite) | hard | stop, exit 1 |
| 4 | clean-tree | `git status` | advisory* | warn (or block with `--strict`) |
| 5 | changelog touched | `git diff` vs base | advisory* | warn (or block with `--strict`) |

\* advisory by default → `--strict` promotes 4 & 5 to hard failures.

Scope auto-detected: on a feature branch it gates the full `--base <main>` diff; on `main` it gates the working-tree changes. If there's genuinely nothing to ship (clean tree, no unpushed commits) it prints `nothing to ship` and exits 0 — a clean no-op, not an error.

## Loop until green

```bash
bash scripts/devworkflows/ship.sh
# Blocked at "lint"     → run devflow-review, fix, loop, re-run ship
# Blocked at "security" → run devflow-security, fix/rotate, re-run ship
# Blocked at "tests"    → run devflow-tdd, fix impl, re-run ship
# Advisory: changelog   → add a CHANGELOG.md entry for this change
```

Re-run `ship.sh` after each fix. The gate is fail-fast, so it surfaces the next blocker only once the prior one is clear. Termination: `READY TO SHIP` + `exit: 0`.

## Hard rules

- Never `git push` while `ship.sh` exits 1.
- Do not bypass a hard stage by editing `ship.sh` — fix the code.
- `--strict` is the right mode for release branches (changelog discipline enforced).
- This gate does not deploy and does not push. It says yes/no. Pushing/deploying still follows the project STOP-AND-SHOW protocol for production targets.
