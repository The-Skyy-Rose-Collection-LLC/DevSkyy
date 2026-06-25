# Skill: cli-anything-vercel-config (module-level)

This skill is the embedded reference for agents operating inside the
`cli_anything.vercel_config` Python package.

## Package Layout

```
cli_anything/vercel_config/
├── __init__.py                  __version__ = "1.0.0"
├── vercel_config_cli.py         Click root; _Ctx; REPL; all command groups
├── core/
│   ├── project.py               ProjectRef; _PATCHABLE_FIELDS; build_patch_payload()
│   ├── env_vars.py              EnvVar; EnvVarDiff; diff_env_vars()
│   ├── domains.py               Domain; DomainDiff; diff_domains()
│   ├── manifest.py              Manifest; ManifestPlan; build_plan(); load_manifest()
│   └── session.py               Session; save/load/delete/list_sessions; _locked_save_json
└── utils/
    ├── vercel_backend.py        VercelBackend; _confirm(); resolve_token(); typed exceptions
    └── repl_skin.py             ReplSkin (prompt-toolkit wrapper)
```

## Key Conventions

### Token handling
- Resolution order: `--token` → `VERCEL_TOKEN` → macOS auth.json → Linux auth.json → raise
- Token stored only in `_Ctx.token` (in-memory). Never log. Never write to disk.
- `VercelAuthError` if unresolved.

### HTTP layer (`VercelBackend`)
- All requests use `timeout=30` (configurable via constructor).
- HTTP 429 → exponential backoff, max 3 attempts, honors `Retry-After` header.
- Typed exceptions: `VercelAuthError` (401), `VercelNotFoundError` (404),
  `VercelValidationError` (422), `VercelRateLimitedError` (429), `VercelBackendError` (5xx).

### STOP-AND-SHOW gate
- `_confirm(action, target, payload)` in `vercel_backend.py`.
- Called before every destructive operation in `vercel_config_cli.py`.
- Destructive = anything that mutates Vercel state: env set/remove, domain add/remove/redirect,
  project patch, manifest apply.
- CLI handlers pass `confirm: bool` flag; if `True`, bypass `_confirm()` interactivity.

### Env var masking
- `EnvVar.display_value(reveal=False)` → `"***"`.
- `EnvVar.display_value(reveal=True)` → actual value.
- `--reveal` flag on `env list` and `env get`.

### Manifest diff model
- `build_plan(manifest, actual_project, actual_env_vars, actual_domains)` → `ManifestPlan`.
- Actions: `add`, `update`, `remove`, `unchanged`.
- `removeUnlistedEnv=False` (default) → `remove` actions excluded from env diff.
- `removeUnlistedDomains=False` (default) → `remove` actions excluded from domain diff.

### Session persistence
- Files at `~/.cli_anything/vercel_config/sessions/<name>.json`.
- Schema: `"cli-anything-vercel-config/session/v1"`.
- Atomic write via `_locked_save_json` (temp file + `fcntl.flock` + `os.replace`).
- `MAX_HISTORY = 200` commands.

### Manifest persistence
- Default file: `vercel-config.json` in cwd.
- Schema: `"cli-anything-vercel-config/manifest/v1"`.
- Atomic write via `_atomic_write_json` in `manifest.py` (same pattern as session).

## Test Files

| File | Coverage |
|---|---|
| `tests/test_core.py` | 93 offline unit tests |
| `tests/test_full_e2e.py` | CLI integration tests; live gate: `VERCEL_E2E=1` |

Run offline suite:
```bash
pytest cli_anything/vercel_config/tests/ --tb=short -q
```

## Common Failure Modes

| Error | Cause | Fix |
|---|---|---|
| `VercelAuthError` | No token found | Set `VERCEL_TOKEN` or pass `--token` |
| `VercelNotFoundError` | Wrong project name | Verify with `project list` |
| `VercelRateLimitedError` | Too many requests | Backend retries 3x; if still failing, wait |
| `ValueError: all unknown` | `project patch` with invalid keys | See `patchable_fields()` for valid list |
| Session `FileNotFoundError` | Session name doesn't exist | `session list` to see available sessions |
