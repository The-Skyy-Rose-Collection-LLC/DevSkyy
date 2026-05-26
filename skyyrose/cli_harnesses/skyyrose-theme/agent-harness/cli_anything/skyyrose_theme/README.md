# cli-anything-skyyrose-theme

Meta-CLI unifying the SkyyRose WordPress theme dev loop.

Wraps `deploy-theme.sh`, PHPCS/PHPCBF, `wp-cli` over SSH, and version management
into a single scriptable interface with an optional interactive REPL.

**Real software is a hard dependency.** This CLI does not reimplement deployment,
PHP linting, or WordPress cache management — it orchestrates the real tools:

| Capability | Tool |
|-----------|------|
| Deploy | `scripts/deploy-theme.sh` (hot-swap default) |
| PHP lint | `vendor/bin/phpcs` + `vendor/bin/phpcbf` |
| Cache flush | `wp cache flush` over SSH |
| Version management | Atomic writes to `functions.php`, `style.css`, `readme.txt` |
| Live HTTP verify | `requests` — mirrors `verify_live()` in deploy script |

---

## Install

```bash
python3 -m venv /tmp/cli-anything-skyyrose-theme-venv
/tmp/cli-anything-skyyrose-theme-venv/bin/pip install --upgrade pip
pip install -e ".[dev]"   # from agent-harness/
```

## Usage

```bash
# Interactive REPL (default — no subcommand)
cli-anything-skyyrose-theme

# Version management
cli-anything-skyyrose-theme version current
cli-anything-skyyrose-theme version bump --to 1.5.21

# Template discovery
cli-anything-skyyrose-theme template list
cli-anything-skyyrose-theme template render about

# Deploy (STOP-AND-SHOW required)
cli-anything-skyyrose-theme deploy --dry-run               # print manifest, exit
cli-anything-skyyrose-theme deploy --dry-run --confirm     # execute dry run
cli-anything-skyyrose-theme deploy --confirm               # hot-swap deploy
cli-anything-skyyrose-theme deploy --with-maintenance --confirm

# Live HTTP checks
cli-anything-skyyrose-theme verify
cli-anything-skyyrose-theme verify --url https://staging.skyyrose.co

# Cache
cli-anything-skyyrose-theme cache purge --confirm

# PHP lint
cli-anything-skyyrose-theme lint php
cli-anything-skyyrose-theme lint fix --confirm

# Health check
cli-anything-skyyrose-theme doctor

# Sessions
cli-anything-skyyrose-theme session status
cli-anything-skyyrose-theme session save
cli-anything-skyyrose-theme session list
cli-anything-skyyrose-theme session delete <id>

# JSON output (all commands)
cli-anything-skyyrose-theme --json version current
```

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `SKYYROSE_THEME_ROOT` | `~/DevSkyy/wordpress-theme/skyyrose-flagship` | Theme directory |
| `SKYYROSE_DEPLOY_SCRIPT` | `~/DevSkyy/scripts/deploy-theme.sh` | Deploy script |
| `SKYYROSE_SSH_HOST` | `skyyrose.wordpress.com@ssh.wp.com` | SSH target |
| `SKYYROSE_WP_ROOT` | `/srv/htdocs` | WP root on server |
| `SKYYROSE_WP_CLI` | `/usr/local/bin/wp` | wp-cli path on server |
| `PUBLIC_URL` | `https://skyyrose.co` | Verify base URL |

## Deploy prerequisites

Before `deploy --confirm` works:

1. `SKYYROSE_DEPLOY_SCRIPT` must point to the real `scripts/deploy-theme.sh`
2. SSH key `~/.ssh/skyyrose-deploy` must be loaded and authorized on `ssh.wp.com`
3. `doctor` must pass all critical checks
4. `version current` must show consistent version across all three files

## Architecture

```
skyyrose_theme_cli.py   — Click root + REPL entry point
core/
  version.py            — Atomic version reads/writes (3 files)
  template.py           — PHP regex template discovery
  deploy.py             — deploy-theme.sh wrapper + STOP-AND-SHOW
  verify.py             — HTTP live checks
  session.py            — fcntl-locked session persistence
utils/
  theme_backend.py      — PHPCS, php -l, wp-cli SSH wrappers
  php_parser.py         — Regex PHP source parsers
  repl_skin.py          — ANSI rose-gold REPL UI
tests/
  test_core.py          — 58 offline unit tests
  test_full_e2e.py      — 5 live tests (SKYYROSE_E2E=1)
```

## STOP-AND-SHOW contract

Commands that touch production always:
1. Print a manifest (action, target, cost, irreversible flag)
2. Exit 0 if `--confirm` is absent
3. Execute only when `--confirm` is present

This mirrors the `STOP AND SHOW` protocol in `CLAUDE.md`.
