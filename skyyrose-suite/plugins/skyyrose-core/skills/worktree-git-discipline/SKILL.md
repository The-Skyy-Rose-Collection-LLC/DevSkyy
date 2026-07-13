---
name: worktree-git-discipline
description: Use before any git commit/stash/history operation in a repo that multiple Claude sessions may share — never rewrite another session's HEAD, never pop a shared stash. Prevents cross-session commit corruption.
origin: SkyyRose
---

# Worktree Git Discipline

One git worktree is one HEAD, but this repo routinely has more than one Claude
session pointed at the same worktree — a Ralph loop and a foreground session both
committing to the same branch is normal, not an edge case. History rewrites assume
the last commit is yours. It might not be. `git commit --amend` in a shared worktree
rewrites **whichever commit HEAD currently points to** — if another session landed
one while you were composing your edit, `--amend` silently folds your staged file
into *their* commit. The symptom is subtle: no error, just someone else's diff
gaining content they never wrote. `reset` and `rebase` carry the same risk in the
other direction — they can discard a commit another session is mid-way through
building on.

> **Boot first:** read `CLAUDE.md`'s **Shared-worktree git discipline** critical
> rule → run `git worktree list` to see every checkout attached to this repo →
> run `git log -1` to see whose commit HEAD is right now. Do not commit against
> your memory of where HEAD was a few tool calls ago — it moves without you.

## When to Use

- Immediately before any `git commit` in a worktree you did not create exclusively
  for this task (i.e. not a fresh `EnterWorktree`).
- Before any `git stash` — the stash ref (`refs/stash`) lives in the **shared**
  `.git` common dir, not per-worktree; a bare `git stash pop` can pop a different
  session's WIP.
- Before `reset`, `rebase`, `checkout --`, or any history-rewriting command,
  in any worktree.
- When a hook (husky, pre-commit) hangs — before reaching for `--no-verify`.

## Method

1. **New commits only.** Never `--amend` / `reset` / `rebase` in a shared
   worktree. If a commit needs correcting, make a new commit that corrects it —
   the git-log noise is cheaper than corrupting another session's work.
2. **Real isolation is a separate worktree, not discipline alone.** If the task
   genuinely needs freedom to rewrite history, use the `EnterWorktree` tool to get
   its own checkout and branch — don't try to out-discipline a shared HEAD.
3. **Stash with a tag, apply by SHA, never pop.** `refs/stash` is shared across
   every worktree of this repo (verified: `git rev-parse --git-path refs/stash`
   resolves to the common `.git`, identical for every worktree). Bare
   `git stash` / `git stash pop` touch the top of a stack you don't own. Instead:
   `git stash push -u -m "<unique-task-tag>"`, capture the resulting SHA from
   `git stash list`, then `git stash apply <sha>` — apply, not pop, so a stale
   reference never silently deletes another session's entry.
4. **Hook hangs bypass the hook path, not verification.** A wedged husky/pre-commit
   process is an infrastructure problem, not a reason to skip checks:
   `git -c core.hooksPath=/dev/null commit …` — never `--no-verify` /
   `--no-gpg-sign` per the Bash tool's Git Safety Protocol.
5. **Never push to main/master, never force-push, never merge** without explicit
   user instruction — same protocol, no shared-worktree exception.

## Loop until committed cleanly

Bounded, like [[drive-to-green]] — cap at 5 turns, stop if the same HEAD mismatch
repeats twice (that's a race you need to name to the user, not out-loop):

```
1. git log -1 --oneline                      # who owns HEAD right now
2. git add <only-your-task's-files>          # never -A / .
3. git commit -m "<type>: <description>"
4. git status --short && git log -1 --oneline
5. If HEAD's parent isn't the SHA you saw in step 1 → someone else landed a
   commit mid-loop. Do NOT amend to fix it. Re-run from step 1.
```

## Verify from an authoritative source

Never assume HEAD is what you last saw — run and read, every time:

- `git log -1 --oneline` **immediately before** the commit call, not five tool
  calls earlier — confirm the parent you expect is still the parent.
- `git status --short` scope check — every path listed should trace to *this*
  task. A file you didn't touch appearing staged means you're about to commit
  on top of someone else's WIP.
- `git worktree list` to confirm which checkouts are attached to this repo and
  that you're operating in the one you think you are — a stale `cd` from an
  earlier command can leave you committing in the wrong tree entirely.

## Adversarial pass

- [[adversarial-verification]] — before claiming a commit landed clean, have a
  skeptical pass assume another session moved HEAD between your last `git log -1`
  and the actual commit, and try to prove it happened (diff the commit's parent
  against what you expected, check `git reflog` for interleaved entries).

## Guardrails · Handoff · Log

- A commit that required `--amend`, `reset`, or `rebase` to "clean up" in a
  shared worktree is not clean — it's a corruption risk that happened to not
  collide this time. Redo it as a new commit.
- Dependency or lockfile churn discovered mid-commit → hand to
  [[dependency-hygiene]] rather than folding an unrelated fix into your commit.
- Log any HEAD-race near-miss or actual corruption to `.wolf/buglog.json` and
  record the lesson via [[continuous-learning]]; cross-plugin handoffs follow
  `CROSS-PLUGIN.md`.
