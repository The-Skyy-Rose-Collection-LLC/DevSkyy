---
name: cli-anything-hf-spaces
description: >
  CLI harness for HuggingFace Spaces administration. Manages hardware tiers,
  env vars, secrets, sleep/restart, logs, README sync, and manifest-driven
  desired-state apply.
---

# cli-anything-hf-spaces

## When to use this skill

Use this skill when you need to:
- Administer HuggingFace Spaces from the command line
- Change hardware tiers (with billing awareness)
- Manage Space secrets and environment variables
- Stream runtime or build logs
- Sync README.md files
- Apply manifest-driven desired state to a Space

## Prerequisites

```bash
pip install 'cli-anything-hf-spaces[all]'
# or for minimal install:
pip install cli-anything-hf-spaces
```

Auth (in priority order):
1. `--token <token>` (in-memory only, never written to disk)
2. `HF_TOKEN` environment variable
3. `~/.cache/huggingface/token` (from `huggingface-cli login`)

## Command groups

| Group      | Description                                      |
|------------|--------------------------------------------------|
| `space`    | info, list, pause, restart, duplicate            |
| `hardware` | get, set (STOP-AND-SHOW), list-tiers             |
| `secrets`  | set, delete (STOP-AND-SHOW), list (manifest only)|
| `vars`     | list, get, set, delete                           |
| `logs`     | run, build (httpx SSE streaming)                 |
| `readme`   | get, set, sync                                   |
| `manifest` | init, show, plan, apply (STOP-AND-SHOW)          |
| `session`  | list, show, delete                               |
| `doctor`   | auth + SDK health check                          |

## Key constraints

- **Secrets are write-only** via HfApi. `secrets list` reads local manifest only.
- **Log streaming** requires `httpx`: `pip install 'cli-anything-hf-spaces[logs]'`
- **Factory reset** is web-UI only — not available in this CLI.
- **STOP-AND-SHOW gate** on: `hardware set`, `secrets delete`, `space pause`, `manifest apply`
- Token is **never** written to disk by the CLI.

## Quick reference

```bash
# Space info
hf-spaces space info owner/my-space

# Change hardware (billing — requires --confirm)
hf-spaces hardware set owner/my-space t4-small --confirm

# Set a secret (value prompted interactively)
hf-spaces secrets set owner/my-space MY_API_KEY

# List variables
hf-spaces vars list owner/my-space

# Stream runtime logs
hf-spaces logs run owner/my-space

# Sync README
hf-spaces readme sync owner/my-space ./README.md

# Manifest workflow
hf-spaces manifest init owner/my-space --out ./hf-space-manifest.json
# edit hf-space-manifest.json ...
hf-spaces manifest plan ./hf-space-manifest.json
hf-spaces manifest apply ./hf-space-manifest.json --confirm

# Health check
hf-spaces doctor

# Interactive REPL
hf-spaces
```

## JSON output

Every command supports `--json` for machine-readable output:

```bash
hf-spaces --json space info owner/my-space | jq .stage
```
