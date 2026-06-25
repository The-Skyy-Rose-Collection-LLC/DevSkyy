# cli-anything-skyyrose-theme

Meta-CLI for the SkyyRose WordPress theme dev loop.

## What it does

Wraps `deploy-theme.sh`, PHPCS, `wp-cli` over SSH, and theme version management
into a single CLI with a rose-gold REPL default mode.

## Install

```bash
pip install -e /Users/theceo/DevSkyy/vendor/cli-anything/skyyrose-theme/agent-harness/
```

## Key commands

```bash
cli-anything-skyyrose-theme                        # REPL
cli-anything-skyyrose-theme version current        # show version (3 sources)
cli-anything-skyyrose-theme version bump --to X    # atomic version bump
cli-anything-skyyrose-theme template list          # all template-*.php + slugs
cli-anything-skyyrose-theme deploy --dry-run       # manifest only (safe)
cli-anything-skyyrose-theme deploy --confirm       # HOT-SWAP deploy (production)
cli-anything-skyyrose-theme verify                 # HTTP checks on skyyrose.co
cli-anything-skyyrose-theme cache purge --confirm  # wp cache flush over SSH
cli-anything-skyyrose-theme lint php               # PHPCS read-only
cli-anything-skyyrose-theme lint fix --confirm     # PHPCBF (modifies files)
cli-anything-skyyrose-theme doctor                 # health checks
cli-anything-skyyrose-theme --json <cmd>           # machine-readable output
```

## STOP-AND-SHOW

Deploy, cache purge, and lint fix require `--confirm`. Without it, they print
a manifest and exit 0. Never execute production ops without the flag.

## Source

`/Users/theceo/DevSkyy/vendor/cli-anything/skyyrose-theme/agent-harness/`

## Tests

```bash
pytest cli_anything/skyyrose_theme/tests/test_core.py --tb=short -q
# 58 offline unit tests, no network, no SSH
```
