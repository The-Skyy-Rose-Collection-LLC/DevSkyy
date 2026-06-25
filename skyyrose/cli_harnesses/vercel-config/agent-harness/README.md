# cli-anything-vercel-config

CLI harness for Vercel project settings that are web-only or unavailable in the official `vercel` CLI.

Manages: project metadata, build config, env vars per environment, custom domains, deployments, runtime logs, and integrations — all via the Vercel REST API.

## Install

```bash
pip install -e ".[dev]"
```

## Authentication

Token resolution order (in-memory only — never written to disk):

1. `--token <tok>` flag
2. `VERCEL_TOKEN` environment variable
3. `~/Library/Application Support/com.vercel.cli/auth.json` (macOS)
4. `~/.local/share/com.vercel.cli/auth.json` (Linux XDG)

## Quick Start

```bash
# Interactive REPL (default when no subcommand given)
cli-anything-vercel-config --project my-project

# Or pipe commands
cli-anything-vercel-config --token $VERCEL_TOKEN --project my-project project show --json
```

## Commands

### project

```bash
project show [--json]              # Show project metadata
project list [--json] [--limit N]  # List all projects in team
project patch KEY=VALUE ...        # Patch project metadata (requires --confirm)
```

### env

```bash
env list [--target ENV] [--json] [--reveal]   # List env vars (values masked by default)
env get KEY [--target ENV] [--reveal]          # Get a single env var
env set KEY=VALUE --target production,preview  # Set env var (requires --confirm)
env remove KEY [--target ENV]                  # Remove env var (requires --confirm)
```

### domain

```bash
domain list [--json]                           # List domains
domain add HOSTNAME [--git-branch BRANCH]      # Add domain (requires --confirm)
domain redirect HOSTNAME --to TARGET           # Configure redirect (requires --confirm)
domain remove HOSTNAME                         # Remove domain (requires --confirm)
```

### deployment

```bash
deployment list [--json] [--limit N]           # List deployments
deployment logs DEPLOYMENT_ID [--json]         # Get deployment runtime logs
```

### integration

```bash
integration list [--json]                      # List installed integrations
```

### manifest

```bash
manifest plan --file vercel-config.json        # Diff declared vs live state
manifest apply --file vercel-config.json       # Apply changes (requires --confirm)
```

### session

```bash
session status                                 # Show active session
session save --name my-session                 # Save current project ref as session
session list [--json]                          # List saved sessions
session load NAME                              # Restore a session
session delete NAME                            # Delete a session
```

### doctor

```bash
doctor                                         # Verify token + API connectivity
```

## Manifest File Format

`vercel-config.json` lets you declare the desired state of a Vercel project:

```json
{
  "schema": "cli-anything-vercel-config/manifest/v1",
  "project": "my-project",
  "teamId": null,
  "projectPatch": {
    "framework": "nextjs",
    "buildCommand": "npm run build"
  },
  "envVars": [
    {
      "key": "API_URL",
      "value": "https://api.example.com",
      "type": "plain",
      "targets": ["production", "preview"]
    }
  ],
  "domains": [
    {
      "name": "example.com",
      "redirect": null
    }
  ],
  "removeUnlistedEnv": false,
  "removeUnlistedDomains": false
}
```

By default, manifest apply is **additive only** — env vars and domains not in the manifest
are left alone. Set `"removeUnlistedEnv": true` for authoritative reconciliation.

## Security

- Token is **never logged, never written to disk** by this CLI.
- Every destructive operation shows a **STOP-AND-SHOW confirmation** before executing.
- Env var values are **masked by default** (`***`). Use `--reveal` to see them.
- HTTP 429 retried with exponential backoff (max 3 attempts).

## What This CLI Does NOT Manage

- `vercel.json` redirects, rewrites, headers — these are deploy-time artifacts.
- Project creation (`POST /v9/projects`) — manages existing projects only.
- Edge Config (`/v1/edge-config`) — out of scope.

## Run Tests

```bash
# Offline unit + integration tests
pytest cli_anything/vercel_config/tests/ --tb=short -q

# Live tests (read-only, safe against production)
VERCEL_E2E=1 VERCEL_TOKEN=<tok> VERCEL_E2E_PROJECT=<project> \
    pytest cli_anything/vercel_config/tests/test_full_e2e.py::TestLiveVercel -v
```

## See Also

- `VERCEL-CONFIG.md` — Phase 1 gap analysis + Phase 2 architecture
- `cli_anything/vercel_config/tests/TEST.md` — Full test plan
