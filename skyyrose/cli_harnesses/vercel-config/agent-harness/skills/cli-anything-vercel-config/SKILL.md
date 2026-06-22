# Skill: cli-anything-vercel-config

Use this skill when working with the `cli-anything-vercel-config` harness — adding commands,
modifying the backend, extending the manifest model, or writing tests.

## What This Harness Does

Wraps the Vercel REST API for settings that the official `vercel` CLI doesn't expose:
project metadata PATCH, env var per-target management, domain redirect config,
declarative manifest plan/apply, deployment logs, and integration listing.

## Install

```bash
cd /path/to/agent-harness
pip install -e ".[dev]"
```

Entry point: `cli-anything-vercel-config`

Module path (use for `python -m` invocation in tests):
`cli_anything.vercel_config.vercel_config_cli`

> **Note:** `_resolve_cli` auto-derivation from "cli-anything-vercel-config" yields an
> invalid module name. Always hardcode `cli_anything.vercel_config.vercel_config_cli`
> in subprocess/e2e tests.

## Architecture Snapshot

```
cli_anything/vercel_config/
├── vercel_config_cli.py    CLI root; _Ctx; all command groups; REPL
├── core/
│   ├── project.py          ProjectRef; 13 patchable fields
│   ├── env_vars.py         EnvVar; diff_env_vars()
│   ├── domains.py          Domain; diff_domains()
│   ├── manifest.py         Manifest; build_plan(); load_manifest()
│   └── session.py          Session persistence; _locked_save_json
└── utils/
    ├── vercel_backend.py   HTTP layer; token resolution; _confirm(); retry
    └── repl_skin.py        prompt-toolkit REPL skin
```

## Adding a New Command

1. Add method to `VercelBackend` in `vercel_backend.py` — use `_request()` for all HTTP.
2. Add Click command to the appropriate group in `vercel_config_cli.py`.
3. If destructive: call `_confirm(action, target, payload)` before executing.
4. If list command: add `--json` flag; emit `json.dumps(data)` when set.
5. Add unit test in `test_core.py` (mock the backend method).
6. Add CLI test in `test_full_e2e.py` (mock `VercelBackend`).

## Security Rules (non-negotiable)

- Token never logged. Never written to disk by this CLI.
- STOP-AND-SHOW `_confirm()` on every destructive op.
- `--reveal` required to print env values; default `"***"`.
- `timeout=` on every `requests` call (default 30s).
- HTTP 429 → exponential backoff, max 3 attempts.
- Atomic session writes: `_locked_save_json` only.

## Vercel API Versions

| Version | Used For |
|---|---|
| v9 | Projects, domains |
| v10 | Environment variables |
| v6 | Deployments list |
| v3 | Deployment events/logs |
| v1 | Integrations |

## Run Tests

```bash
# Full offline suite
pytest cli_anything/vercel_config/tests/ --tb=short -q

# Live (read-only, safe against production)
VERCEL_E2E=1 VERCEL_TOKEN=<tok> VERCEL_E2E_PROJECT=<project> \
    pytest cli_anything/vercel_config/tests/test_full_e2e.py::TestLiveVercel -v
```

## Key Files to Read Before Editing

| Task | File |
|---|---|
| Add REST method | `utils/vercel_backend.py` |
| Add CLI command | `vercel_config_cli.py` |
| Extend manifest | `core/manifest.py` |
| Extend env diff | `core/env_vars.py` |
| Extend domain diff | `core/domains.py` |
| Gap analysis + architecture | `VERCEL-CONFIG.md` |
| Test plan | `tests/TEST.md` |
