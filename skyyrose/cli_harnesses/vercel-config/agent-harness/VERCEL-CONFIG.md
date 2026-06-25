# VERCEL-CONFIG.md — Gap Analysis & Architecture

## Phase 1: Gap Analysis — What the Official Vercel CLI Misses

The official `vercel` CLI (v40+) exposes deployment, environment variable, and project-linked commands,
but leaves a significant surface of the Vercel REST API unreachable from the terminal.

### Confirmed Gaps (REST-only)

| Capability | REST Endpoint | Official CLI | This Harness |
|---|---|---|---|
| Project metadata PATCH | `PATCH /v9/projects/{id}` | ✗ | `project patch` |
| Project list (all team projects) | `GET /v9/projects` | partial | `project list` |
| Env var per-environment targeting | `GET /v10/projects/{id}/env` | partial | `env list --target` |
| Env var type (plain/secret/encrypted/sensitive) | `POST /v10/projects/{id}/env` | ✗ | `env set --type` |
| Env var bulk decrypt | `GET /v10/projects/{id}/env/{id}/decrypt` | ✗ | `env get --reveal` |
| Domain redirect config | `PATCH /v9/projects/{id}/domains/{name}` | ✗ | `domain redirect` |
| Domain git-branch binding | `POST /v9/projects/{id}/domains` gitBranch field | ✗ | `domain add --git-branch` |
| Deployment runtime logs | `GET /v3/deployments/{id}/events` | partial (streaming) | `deployment logs` |
| Integration list | `GET /v1/integrations/configurations` | ✗ | `integration list` |
| Declarative manifest plan/apply | N/A (composite) | ✗ | `manifest plan/apply` |

### Known Boundary (not managed by any CLI)

`vercel.json` redirects, rewrites, headers, and build config are **deploy-time artifacts**.
They live in the repository and are applied at build time — not via the REST API.
This harness does NOT manage `vercel.json` content.

### Vercel API Versions Used

| Version | Endpoint Family |
|---|---|
| v9 | Projects (CRUD, domains) |
| v10 | Environment variables |
| v6 | Deployments list |
| v3 | Deployment events / logs |
| v1 | Integrations |

---

## Phase 2: Architecture

### Module Hierarchy

```
cli_anything/vercel_config/
├── __init__.py                  version = "1.0.0"
├── vercel_config_cli.py         Click root; REPL default; _Ctx shared state
├── core/
│   ├── project.py               ProjectRef dataclass; patch payload builder
│   ├── env_vars.py              EnvVar dataclass; masked/reveal; diff helpers
│   ├── domains.py               Domain dataclass; diff helpers
│   ├── manifest.py              Manifest model; ManifestPlan; build_plan()
│   └── session.py               Session persistence; _locked_save_json
└── utils/
    ├── vercel_backend.py        VercelBackend; token resolution; HTTP retry
    └── repl_skin.py             ReplSkin terminal UX (prompt-toolkit)
```

### Token Resolution (in-memory only, never logged)

```
--token flag
  → VERCEL_TOKEN env var
  → ~/Library/Application Support/com.vercel.cli/auth.json  (macOS)
  → ~/.local/share/com.vercel.cli/auth.json                 (Linux XDG)
  → ~/.config/com.vercel.cli/auth.json                      (Linux fallback)
  → VercelAuthError
```

Token is stored only in `_Ctx.token` (in-memory). Never written to disk by this CLI.

### Manifest Diff Model

Three-way comparison:
1. **Declared** — what `vercel-config.json` states (your source of truth)
2. **Actual** — what the Vercel API returns right now (live state)
3. **Proposed** — the change set `build_plan()` produces

Actions per entity:

| Action | Meaning |
|---|---|
| `add` | Declared but not in Actual — will create |
| `update` | In both but differs — will patch |
| `remove` | In Actual but not Declared — will delete (only when `removeUnlistedEnv/Domains: true`) |
| `unchanged` | Identical — no-op |

Default mode is **additive** (`removeUnlistedEnv: false`, `removeUnlistedDomains: false`).
Set `"removeUnlistedEnv": true` in manifest to enable authoritative reconciliation.

### Security Constraints

- Token never logged. `_Ctx.__repr__` returns `<_Ctx project=... token=REDACTED>`.
- STOP-AND-SHOW gate via `_confirm(action, target, payload)` in `vercel_backend.py`.
  Every destructive op (env set, env remove, domain add, domain remove, domain redirect,
  project patch, manifest apply) calls `_confirm()` unless `--confirm` passed.
- `--reveal` required to print secret values. Default masks with `***`.
- HTTP requests use `timeout=30` (default). No infinite waits.
- HTTP 429 retried with exponential backoff, max 3 attempts, honoring `Retry-After`.
- Session files written atomically via `_locked_save_json` (temp + fcntl + os.replace).

### REPL Design

- Entry: `cli-anything-vercel-config` with no subcommand → `_run_repl()`.
- `ReplSkin` (prompt-toolkit) renders a colored prompt showing `project@session`.
- History persisted in active session via `session.push_history(command)`.
- Commands dispatched via `main.main(args=..., standalone_mode=False, obj=app_ctx)`.
- `/quit`, `exit`, `q`, `Ctrl-D`, `Ctrl-C` exit the REPL cleanly.

### Known Gaps for Phase 3

1. **Project-level aliases** — `PATCH /v9/projects/{id}` supports `alias` but the
   semantics differ from domain management; not currently surfaced as a separate command.
2. **Team-scoped project creation** — `POST /v9/projects` (create) is not implemented;
   this CLI manages existing projects only.
3. **Password-protected deployments** — `POST /v9/projects/{id}/protection-bypass` has
   no CLI surface in this harness.
4. **Edge Config** — `GET /v1/edge-config` and `PUT /v1/edge-config/{id}/items` are
   out of scope; a separate `cli-anything-vercel-edge-config` harness is planned.
5. **Streaming deployment logs** — `GET /v3/deployments/{id}/events` returns SSE;
   `deployment logs` currently polls and prints; a streaming follow mode (`--follow`)
   is not yet implemented.
