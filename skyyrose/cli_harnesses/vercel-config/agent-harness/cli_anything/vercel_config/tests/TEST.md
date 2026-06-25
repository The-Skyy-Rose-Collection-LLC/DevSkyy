# TEST.md — cli-anything-vercel-config Test Plan

## Phase 1 — Offline Unit Tests (`test_core.py`)

**Target:** 93 tests, zero network calls, fully deterministic.

| Class | Tests | Covers |
|---|---|---|
| TestProjectRef | 10 | URL parsing, `is_id`/`is_slug`, empty/whitespace rejection |
| TestBuildPatchPayload | 4 | Valid/unknown/mixed keys, empty-after-filter error |
| TestEnvVar | 11 | target/type validation, `masked_value`, `display_value`, `to_create_payload`, `from_api` |
| TestDiffEnvVars | 6 | add/update/remove/unchanged/multi-target diff |
| TestDomain | 8 | hostname normalization, redirect/gitBranch, empty name rejection |
| TestDiffDomains | 4 | add/remove/update/unchanged |
| TestManifest | 4 | `to_dict` round-trip, `save`/load atomic write |
| TestLoadManifest | 7 | valid load, missing required keys, bad schema, corrupt JSON, unknown action |
| TestBuildPlan | 8 | project-only, env-only, domain-only, combined, additive flags, no-changes |
| TestSession | 6 | round-trip, `push_history` cap at MAX_HISTORY, empty name/project |
| TestSessionPersistence | 7 | save/load/delete/list, missing file, corrupt JSON |
| TestLockedSaveJson | 3 | atomic write, directory auto-create, error cleanup |
| TestResolveToken | 7 | flag → env → macOS auth.json → Linux auth.json → fail priority |
| TestVercelBackendErrors | 6 | typed exception mapping for 401/404/422/429/5xx |
| TestVercelBackend429Retry | 2 | exponential backoff, Retry-After header honor |

**Run:**
```bash
pytest cli_anything/vercel_config/tests/test_core.py -v --tb=short
```

## Phase 2 — CLI Integration Tests (`test_full_e2e.py`, offline subset)

**Target:** All tests in offline classes pass without network or VERCEL_TOKEN.

| Class | Tests | Covers |
|---|---|---|
| TestHelpBanners | 17 | --help on root + every command group + key subcommands |
| TestJsonOutput | 5 | --json flag emits parseable JSON (mocked backend) |
| TestDestructiveGates | 2 | env remove / domain remove abort without --confirm |
| TestSessionCommands | 3 | session list/save/delete round-trip |
| TestEnvMasking | 2 | values masked by default, revealed with --reveal |

**Run:**
```bash
pytest cli_anything/vercel_config/tests/test_full_e2e.py -v --tb=short -k "not TestLiveVercel"
```

## Phase 3 — Full Suite (offline)

```bash
pytest cli_anything/vercel_config/tests/ --tb=short -q
```

Expected: 120+ tests pass, 0 failures, live tests skip cleanly.

## Phase 4 — Live Network Tests (VERCEL_E2E=1)

**Prerequisites:**
- `VERCEL_TOKEN` — valid Vercel personal access token
- `VERCEL_E2E=1` — enables live test class
- `VERCEL_E2E_PROJECT` — Vercel project name or ID

```bash
VERCEL_E2E=1 VERCEL_TOKEN=<tok> VERCEL_E2E_PROJECT=<project> \
    pytest cli_anything/vercel_config/tests/test_full_e2e.py::TestLiveVercel -v
```

| Test | Validates |
|---|---|
| `test_live_project_show` | GET /v9/projects/{id_or_name} returns project dict |
| `test_live_env_list` | GET /v10/projects/{id}/env returns list, values masked |
| `test_live_domain_list` | GET /v9/projects/{id}/domains returns list |
| `test_live_deployment_list` | GET /v6/deployments returns list |
| `test_live_doctor` | Token resolves, API is reachable, project exists |

**Cost:** No writes — all live tests are read-only. Safe to run against production.

## Phase 5 — Coverage Report

```bash
pytest cli_anything/vercel_config/tests/ --cov=cli_anything.vercel_config \
    --cov-report=term-missing --cov-report=html:htmlcov -q
```

Target: ≥ 85% line coverage.

## Phase 6 — Results (auto-appended)

<!-- Results appended here after each test run -->
