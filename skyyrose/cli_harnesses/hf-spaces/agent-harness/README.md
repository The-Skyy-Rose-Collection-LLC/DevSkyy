# cli-anything-hf-spaces

CLI harness for HuggingFace Spaces administration. Manages hardware tiers,
env vars, secrets, sleep/restart, logs, README sync, and manifest-driven
desired-state apply.

## Install

```bash
pip install 'cli-anything-hf-spaces[all]'
```

Minimal install (no log streaming, no REPL):

```bash
pip install cli-anything-hf-spaces
```

## Auth

Token resolution order (first wins):

1. `--token <token>` — in-memory only, never written to disk
2. `HF_TOKEN` environment variable
3. `~/.cache/huggingface/token` (from `huggingface-cli login`)

## Quick start

```bash
# Health check
hf-spaces doctor

# Space info
hf-spaces space info owner/my-space

# Change hardware tier (billing — requires --confirm)
hf-spaces hardware set owner/my-space t4-small --confirm

# Set a secret (value prompted interactively)
hf-spaces secrets set owner/my-space MY_API_KEY

# List variables
hf-spaces vars list owner/my-space

# Stream runtime logs (requires httpx extra)
hf-spaces logs run owner/my-space

# Sync README
hf-spaces readme sync owner/my-space ./README.md

# Manifest workflow
hf-spaces manifest init owner/my-space --out ./hf-space-manifest.json
# edit hf-space-manifest.json ...
hf-spaces manifest plan  ./hf-space-manifest.json
hf-spaces manifest apply ./hf-space-manifest.json --confirm

# Interactive REPL
hf-spaces
```

## Command groups

| Group      | Commands                                 |
|------------|------------------------------------------|
| `space`    | info, list, pause, restart, duplicate    |
| `hardware` | get, set, list-tiers                     |
| `secrets`  | set, delete, list (manifest only)        |
| `vars`     | list, get, set, delete                   |
| `logs`     | run, build                               |
| `readme`   | get, set, sync                           |
| `manifest` | init, show, plan, apply                  |
| `session`  | list, show, delete                       |
| `doctor`   | auth + SDK health check                  |

## JSON output

Every command supports `--json` for machine-readable output:

```bash
hf-spaces --json space info owner/my-space | jq .stage
```

## STOP-AND-SHOW gate

The following operations require `--confirm` and print a summary before
executing:

- `hardware set` — billing impact
- `secrets delete` — destructive, write-only API
- `space pause` — takes Space offline
- `manifest apply` — may touch hardware, secrets, variables, README

## Known API limitations

- **Secrets are write-only** via HfApi. `secrets list` reads the local
  manifest only and prints an explicit warning.
- **Log streaming** bypasses HfApi and uses raw httpx SSE. Requires
  `pip install 'cli-anything-hf-spaces[logs]'`.
- **Factory reset** is a web-UI-only operation. Not available via this CLI
  (reported by `doctor`).

## Manifest

A manifest declares the desired state of a Space. Generate one from live
state with `manifest init`, edit it, then `plan` and `apply`.

```json
{
  "schema": "1",
  "repo_id": "owner/my-space",
  "hardware": "t4-small",
  "sleep_time": 300,
  "variables": {
    "DEBUG": "false"
  },
  "secrets": ["MY_API_KEY"],
  "readme_path": "./README.md"
}
```

## Hardware tiers

| Slug            | Description                     |
|-----------------|---------------------------------|
| `cpu-basic`     | 2 vCPU / 16 GB RAM (free)       |
| `cpu-upgrade`   | 8 vCPU / 32 GB RAM              |
| `cpu-xl`        | 32 vCPU / 128 GB RAM            |
| `zero-a10g`     | ZeroGPU A10G (shared)           |
| `t4-small`      | NVIDIA T4 small                 |
| `t4-medium`     | NVIDIA T4 medium                |
| `l4x1`          | NVIDIA L4 ×1                    |
| `l4x4`          | NVIDIA L4 ×4                    |
| `l40sx1`        | NVIDIA L40S ×1                  |
| `l40sx4`        | NVIDIA L40S ×4                  |
| `l40sx8`        | NVIDIA L40S ×8                  |
| `a10g-small`    | NVIDIA A10G small               |
| `a10g-large`    | NVIDIA A10G large               |
| `a10g-largex2`  | NVIDIA A10G large ×2            |
| `a10g-largex4`  | NVIDIA A10G large ×4            |
| `a100-large`    | NVIDIA A100 large               |
| `h100`          | NVIDIA H100                     |
| `h100x8`        | NVIDIA H100 ×8                  |

## Sessions

Completed commands are logged to `~/.cli_anything/hf_spaces/sessions/` for
auditing. Sessions never contain auth tokens.

## Development

```bash
pip install -e '.[dev]'

# Unit tests only (no live HF calls)
pytest cli_anything/hf_spaces/tests/test_core.py -v

# All tests including e2e (requires HF_SPACES_E2E=1 and a valid HF_TOKEN)
HF_SPACES_E2E=1 HF_TOKEN=hf_... pytest cli_anything/hf_spaces/tests/ -v

# Coverage
pytest cli_anything/hf_spaces/tests/test_core.py -v \
  --cov=cli_anything.hf_spaces --cov-report=term-missing
```
