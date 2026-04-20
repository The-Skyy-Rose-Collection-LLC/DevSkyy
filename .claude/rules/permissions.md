# Permissions & Autonomy Model

This repo uses `auto` permission mode with a narrow deny list and verification-driven trust. The harness (not Claude) enforces these rules — see `.claude/settings.json`.

## The model

**Trust + verify, not prompt + hope.** Instead of interrupting for each deploy, git push, or test run, the harness lets Claude act and relies on OS-level sandboxing plus a Stop-hook verification gate.

| Action | Handled how |
|--------|-------------|
| Read/Edit/Write source files | auto (sandbox blocks secrets) |
| Run tests, linters, formatters, build, type-check | auto |
| `git commit` / `git push` to feature branches | auto (but `--force`, `--no-verify`, hard reset are denied) |
| WordPress deploy via `scripts/deploy-theme.sh` | auto — script has built-in `verify_live()` gate (HTTP 200 + size ≥ 50KB + no PHP error markers) |
| Paid API call (FASHN, fal.ai, OpenAI, Gemini, Anthropic) | **ask** — money is not verifiable after the fact |
| Read `.env*`, `~/.ssh`, `~/.aws`, `~/.gcp`, `*.pem`, `*.key` | **deny** (permission rule + sandbox `denyRead`) |
| `git push --force`, `rm -rf /`, `sudo *`, `git branch -D main` | **deny** |
| `bypassPermissions` mode | **disabled** globally |

## Why this is safer than the old prompt-based model

1. **Sandbox > prompt.** `denyRead` on `.env*` blocks `cat .env` in a Bash subprocess, not just the Read tool. A promise to "stop and confirm" in a prompt can be talked around; a file the process cannot open cannot be opened.
2. **Verification is mechanical.** The Stop hook (`.claude/hooks/verify-gate.sh`) refuses to let the turn end if source files changed but `tasks/.last-verify-passed` isn't fresh. Claude can't declare "done" without proof.
3. **`verify_live()` is real.** The deploy script already curls the live homepage after cache flush and fails non-zero on HTTP != 200 or size < 50 KB or presence of PHP error markers. That's a better gate than "please confirm before deploying".

## What still prompts

Only paid APIs and truly destructive commands. Cost cannot be recovered by a test; `git push --force` to a protected branch cannot be undone by linting. Those stay on the `ask`/`deny` list.

## How to run the loop

1. Edit code.
2. Run `/go` — workspace-aware: Python runs `make lint`+`make test-fast`, frontend runs type-check+build, WordPress runs PHPCS+php-lint+dry-deploy.
3. `/go` writes `tasks/.last-verify-passed`, commits, pushes. If you asked for a PR, it creates one.
4. Stop hook validates the marker is fresh. If not: you get `BLOCKED: run /go before ending turn`.

## Escape hatches

- **Docs-only edits** that don't warrant verification: `touch tasks/.last-verify-passed` and the gate allows end. The hook detects that no source extensions changed and skips verification automatically for pure-doc turns — the manual touch is only needed if you also edited `.sh` or similar but it's not meaningful.
- **A genuine verify failure you can't fix immediately**: do not force-touch the marker. Report what broke, leave the turn blocked, come back with a fix.

## What to change if a routine action prompts

- If the classifier in `auto` mode repeatedly stops on the same safe command, add the pattern to `permissions.allow` in `.claude/settings.json` (not `autoMode.environment` — keep the two distinct).
- If a paid API should occasionally run unattended (e.g. scheduled cron via CI, not interactive), handle it in CI with scoped credentials, not by loosening the `ask` list.

## What `auto` mode cannot decide

The classifier handles routine dev commands by pattern. It does not recognize:
- "This deploy happens on a Friday at 5pm" — the harness has no concept of calendar risk. Humans still choose when to ship.
- "This refactor touches 40 files across 3 workspaces" — large blast radius is a judgment call; the operator decides whether to split it.

Use the harness to remove friction from the first 95% of work, not to replace the operator on the last 5%.
