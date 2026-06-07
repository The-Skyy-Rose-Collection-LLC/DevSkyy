# ci-env — Local CI mirror (stopgap while GitHub Actions is billing-blocked)

GitHub Actions is currently billing-blocked, so pushes don't get checked by the
cloud pipeline. This directory + `scripts/ci-local.sh` reproduce the **same
gating checks** locally, with no cloud dependency, until billing is restored.

## What it mirrors

`scripts/ci-local.sh` runs the six jobs the `.github/workflows/ci.yml` summary
gates on:

| Job | What runs | Tooling |
|-----|-----------|---------|
| `wordpress-theme` | `php -l` on every theme `.php`; build + min-drift (opt-in) | PHP |
| `lint` | `ruff` · `black --check` · `isort --check` · `mypy` | `ci-env/.venv` |
| `python-tests` | `pytest tests/` (excludes e2e) | `ci-env/.venv` |
| `security` | `bandit` (HIGH/HIGH blocks) · `pip-audit --strict` | `ci-env/.venv` |
| `frontend-tests` | `npm run lint` · `type-check` · `build` in `frontend/` | Node |
| `threejs-tests` | `npm run test:collections` (root) | Node |

**Intentionally skipped** (cloud-only, can't run offline, don't validate code):
Codecov upload, artifact upload, Docker build/push, Vercel / Render deploy,
CodeQL, GitGuardian, Playwright E2E, semgrep (`--config=auto` needs network).

## Setup (once)

```bash
bash ci-env/setup.sh               # full: Python tools + editable project (for pytest)
bash ci-env/setup.sh --tools-only  # fast: lint/format/security only (enough for pre-commit)
```

This creates `ci-env/.venv` (gitignored). `scripts/ci-local.sh` auto-activates it.

## Run

```bash
bash scripts/ci-local.sh                 # all gating jobs
bash scripts/ci-local.sh wordpress-theme # one job
bash scripts/ci-local.sh lint security   # several jobs
FAST=1 bash scripts/ci-local.sh          # skip heavy installs; SKIP jobs whose deps are absent
```

Exit code is `0` only if every **non-skipped** job passes. A `SKIP` means a tool
or directory wasn't present — it does **not** fail the run, but it also wasn't
verified, so install the dep for full coverage.

### WordPress build / minification drift

The `wordpress-theme` job runs `php -l` by default. The `npm run build` +
minification-drift check is **opt-in**:

```bash
WITH_BUILD=1 bash scripts/ci-local.sh wordpress-theme
```

It's off by default because `npm run build` regenerates every `.min.css`/`.min.js`
into the worktree and minifier output is **node-version-sensitive** — local Node
may differ from CI's Node 22, producing a *spurious* drift failure. Only run it
with `WITH_BUILD=1` when you actually changed source CSS/JS, ideally under the
Node-22 `act`/Docker path below.

## Pre-push hook (stopgap gate)

`.husky/pre-push` routes pushes through a **fast subset** of this mirror so they
get checked while the cloud pipeline is paused. `core.hooksPath` is an absolute
path, so the hook is **shared across every worktree** — it fires only when:

1. `.ci-local-gate` exists in the pushing worktree — opt-in, **one `rm` to disable**.
2. a `ci-local.sh` is resolvable (see below) — else it skips silently.

It runs `php -l` against the **worktree being pushed**, regardless of branch. The
script is resolved branch-independently: prefer the pushing worktree's own
`scripts/ci-local.sh`, else fall back to the canonical ci-mirror copy; `CI_LOCAL_ROOT="$PWD"`
makes the canonical script check *this* worktree, not its own. The fallback stops
being needed once the tooling reaches `main` (every branch then ships the script)
— self-healing. The gate file is ignored repo-wide via `.git/info/exclude`.

**Python `lint` is intentionally not push-gated** — `ruff/black/isort` run repo-wide
and the tree currently has pre-existing drift that would false-block unrelated
pushes. Run lint on demand instead (`bash scripts/ci-local.sh lint` or `act -j lint`).

```bash
touch .ci-local-gate    # enable the stopgap in THIS worktree
rm .ci-local-gate       # disable it
git push --no-verify    # bypass for a single push
```

The gate file is gitignored (per-worktree). The hook block lives in `.husky/pre-push`
and reaches `main` when this branch merges; remove it (or the gate files) once
GitHub Actions billing is restored.

## Fidelity ladder

This mirror trades exactness for zero-setup speed. From least to most faithful:

1. **`ci-local.sh` on host tools** — fastest. Caveat: host Python is 3.14, CI is
   3.11; host Node may differ from CI's 22. Catches the vast majority of breaks.
2. **`ci-local.sh` + `ci-env/.venv`** (this dir) — pins the Python toolchain.
   Use `PYTHON_BIN=python3.11 bash ci-env/setup.sh` for interpreter parity.
3. **`act`** (installed: `/opt/homebrew/bin/act`) — runs the *actual* `ci.yml`
   jobs in Docker containers matching the runner image. Highest fidelity, slowest:
   ```bash
   act -j wordpress-theme        # run one ci.yml job locally in Docker
   act -j lint -j python-tests
   ```
   Use this before relying on a green result for anything load-bearing, and for
   the `WITH_BUILD` minification-drift check (Node-22 parity).

## When GitHub billing is restored

This is a stopgap. Once the cloud pipeline runs again:

- Keep `ci-local.sh` + `ci-env/` — they're a fast pre-push gate regardless.
- If git hooks were wired to route through `ci-local.sh` (see project hook config),
  revert or relax them so the cloud pipeline is authoritative again.
