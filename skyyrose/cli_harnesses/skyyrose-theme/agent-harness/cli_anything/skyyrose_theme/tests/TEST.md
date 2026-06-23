# Test Suite — cli-anything-skyyrose-theme

## Quick start

```bash
# Install into a fresh venv
python3 -m venv /tmp/cli-anything-skyyrose-theme-venv
/tmp/cli-anything-skyyrose-theme-venv/bin/pip install --upgrade pip
cd /Users/theceo/DevSkyy/vendor/cli-anything/skyyrose-theme/agent-harness
/tmp/cli-anything-skyyrose-theme-venv/bin/pip install -e ".[dev]"

# Run unit tests (offline, ~1s)
PATH="/tmp/cli-anything-skyyrose-theme-venv/bin:$PATH" \
  CLI_ANYTHING_FORCE_INSTALLED=1 \
  /tmp/cli-anything-skyyrose-theme-venv/bin/pytest \
  cli_anything/skyyrose_theme/tests/ \
  --tb=short -q
```

## Test files

| File | Type | Count | Gate |
|------|------|-------|------|
| `test_core.py` | Unit (offline) | 58 tests | Always runs |
| `test_stopshow.py` | Unit (offline) | 11 tests | Always runs |
| `test_phpcs.py` | Unit (offline) | 12 tests | Always runs |
| `test_verify.py` | Unit (offline) | 23 tests | Always runs |
| `test_version_atomic.py` | Unit (offline) | 7 tests | Always runs |
| `test_php_parser.py` | Unit (offline) | 26 tests | Always runs |
| `test_full_e2e.py` | E2E (live) | 5 tests | `SKYYROSE_E2E=1` |

## Coverage map

| Module | Tests | Coverage |
|--------|-------|----------|
| `core/version.py` | `TestVersionRead` (6) + `TestVersionWrite` (4) + `TestVersionWriteAtomic` (7) | 17 |
| `utils/php_parser.py` | `TestPhpParser` (6) + `TestExtractVersionConstant` (8) + `TestExtractStyleCssVersion` (4) + `TestExtractReadmeStableTag` (3) + `TestExtractThemeAndDomain` (4) + `TestExtractPhpString` (3) + `TestExtractTemplateMap` (5) | 33 |
| `core/template.py` | `TestTemplateDiscovery` | 5 |
| `core/session.py` | `TestSession` | 9 |
| `core/deploy.py` | `TestDeployManifest` (8) + `TestStopAndShow` (4) + `TestStopShowManifestShape` (11) | 23 |
| `core/verify.py` | `TestVerify` (6) + `TestUrlCheckResult` (7) + `TestVerifyLiveWithResponses` (11) + `TestVerifyReport` (3) | 27 |
| `utils/theme_backend.py` | `TestThemeBackend` (5) + `TestPHPCSArgvAssembly` (12) | 17 |
| CLI runner | `TestCLIRunner` | 5 |

Total offline: **137 tests** (Phase 6 — added 79 new tests)

## Phase 6 results (2026-05-25)

| Metric | Before | After |
|--------|--------|-------|
| Pass | 58 | 137 |
| Skip (E2E gate) | 5 | 5 |
| Fail | 0 | 0 |
| New test files | — | 4 |
| `responses` dep added | — | `>=0.25` |

## E2E prerequisites

```bash
export SKYYROSE_E2E=1
export SKYYROSE_THEME_ROOT=/Users/theceo/DevSkyy/wordpress-theme/skyyrose-flagship
export CLI_ANYTHING_FORCE_INSTALLED=1
```

E2E tests that exercise SSH (cache purge, wp-cli) require `ssh skyyrose.wordpress.com@ssh.wp.com`
to be reachable and authenticated.

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `SKYYROSE_THEME_ROOT` | `~/DevSkyy/wordpress-theme/skyyrose-flagship` | Theme directory |
| `SKYYROSE_DEPLOY_SCRIPT` | `~/DevSkyy/scripts/deploy-theme.sh` | Deploy script path |
| `SKYYROSE_SSH_HOST` | `skyyrose.wordpress.com@ssh.wp.com` | SSH target |
| `SKYYROSE_WP_ROOT` | `/srv/htdocs` | WP root on server |
| `SKYYROSE_WP_CLI` | `/usr/local/bin/wp` | wp-cli path on server |
| `PUBLIC_URL` | `https://skyyrose.co` | Verify base URL |
| `SKYYROSE_E2E` | unset | Set to `1` to enable live tests |
| `CLI_ANYTHING_FORCE_INSTALLED` | unset | Set to `1` to require installed binary |
