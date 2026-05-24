# Local CI Sandbox

While GitHub Actions billing is locked or the runner is otherwise unavailable, use the local CI sandbox to validate PRs before merge.

## Quick reference

```bash
# Run every job (lint, python, security, frontend, threejs, wordpress)
make ci-local

# Run a single job
make ci-local JOB=lint
make ci-local JOB=python
make ci-local JOB=frontend

# Run several jobs
bash scripts/ci-local.sh --only lint,python

# Stream output instead of capturing to logs
bash scripts/ci-local.sh --verbose

# Don't auto-install missing pip tools
bash scripts/ci-local.sh --no-install

# List jobs
bash scripts/ci-local.sh --list
```

## What it mirrors

The script mirrors the 6 parallel **gating jobs** from `.github/workflows/ci.yml` — the ones that determine the PR's pass/fail status:

| Local job | GitHub job | Commands |
|---|---|---|
| `lint` | 🔍 Lint & Static Analysis | `ruff check .` + `black --check` + `isort --check` + `mypy --ignore-missing-imports` |
| `python` | 🐍 Python Tests | `pytest tests/ --ignore=tests/e2e` (coverage skipped locally — too noisy on partial envs) |
| `security` | 🔐 Security Scan | `pip-audit` + `bandit -ll` + `safety check` + `semgrep --config=auto` |
| `frontend` | ⚛️ Frontend Tests | `npm ci` + `npm run lint` + `npm run type-check` + `npm run build` (in `frontend/`) |
| `threejs` | 🎮 Three.js Tests | `npm run test:collections` (root) |
| `wordpress` | 🏗️ WordPress Theme | `php -l` on every `*.php` in the theme; theme `npm build` skipped cleanly (theme has no `package.json` today) |

## What it does NOT run (and why)

These CI jobs aren't worth mirroring locally:

| GitHub job | Why skipped locally |
|---|---|
| 🎭 Playwright E2E | Needs a running stack (API + dashboard + Redis). Run `docker compose up` first, then invoke Playwright directly. |
| 🔌 API Integration | Needs Redis service. Spin up via `docker compose up redis -d` and run `pytest tests/test_*api*.py` manually. |
| 🐳 Docker Build | Builds container images. Use `make docker-build` if you actually need them. |
| 🚀 Deploy Staging / 🌐 Deploy Production | Real deploys. Never local. |
| 📊 Pipeline Summary / 📊 Security Summary | Generated from upstream results; the local summary is in `ci-local-output/summary.md`. |

## Outputs

Every run writes to `ci-local-output/`:

- `<job>.log` — full output for each job (always captured, even on pass)
- `summary.md` — Markdown table you can paste into a PR comment

`ci-local-output/` is gitignored — it's regenerated on every run.

## Exit codes

- `0` — all jobs passed or were intentionally skipped (clean signal)
- `1` — at least one job failed
- `2` — invalid arguments

The script does **not** treat skipped jobs as failures. A skip means the local environment can't run that job (e.g., `php` not installed, or `wordpress-theme/skyyrose-flagship/` has no `package.json`). Skips are tracked in the summary so you can see what was *not* validated locally.

## Honest limits

The local sandbox is **not a perfect replica** of the GitHub runner. Known differences:

- **Coverage** — the GitHub `python` job runs `pytest --cov` with parallel workers (`-n auto`). The local job skips coverage to avoid noisy failures on partial dev envs. Run `make test-cov` separately if you need the coverage report.
- **Caching** — GitHub jobs cache pip / npm / mypy between runs. Local runs use whatever's on your machine; cold runs will be slower than the GitHub timings suggest.
- **Network** — `pip-audit` and `safety check` query upstream advisory databases. If you're offline, those tools will fail and the security job will be marked failed. Use `--only` to skip security when working offline.
- **WordPress theme `npm build`** — the actual theme has no `package.json`, so the local job logs "theme npm build skipped (no package.json)" rather than running. The GitHub job currently fails for the same reason; this is a pre-existing CI issue independent of the billing block.

## Higher fidelity option: `act`

For a closer-to-real run, [`act`](https://github.com/nektos/act) executes `.github/workflows/*.yml` inside Docker containers that mirror the GitHub runner images.

```bash
# Install act (macOS)
brew install act

# Run the CI workflow locally (uses Docker)
act pull_request -W .github/workflows/ci.yml
```

`act` is heavier (downloads multi-GB images on first run) and slower than the local sandbox but matches the GitHub environment more closely. We don't ship `act` as the default because:

- It requires Docker running
- First-run image pulls take 5–10 minutes
- For most PRs, the lightweight sandbox catches the same issues in 30–60 seconds

## When to use which

- **Bumping a dependency / changing a workflow YAML** → use `act` for fidelity
- **Touching Python or frontend code** → use `make ci-local` for speed
- **End-to-end behavior testing** → run the stack via `docker compose up` and exercise it directly
- **Pre-push gate** → consider wiring `make ci-local JOB=lint,python,frontend` into a `.husky/pre-push` hook (not yet implemented in this repo)
