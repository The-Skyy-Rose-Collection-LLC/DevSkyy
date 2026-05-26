# cli-anything-comfyui — Claude Skill Brief

**Tier 2 #7 — ComfyUI CLI harness**

## Purpose

Manage ComfyUI from the command line: queue workflows, inspect nodes and models,
browse history, run health checks, manage persistent sessions, and apply batched
operation manifests.

## Package

```
cli-anything-comfyui 1.0.0
Entry points: comfyui | cli-anything-comfyui
Source: vendor/cli-anything/comfyui/agent-harness/
```

## Quick Install

```bash
pip install -e vendor/cli-anything/comfyui/agent-harness/
# or with REPL:
pip install -e "vendor/cli-anything/comfyui/agent-harness/[all]"
```

## Environment

| Variable | Purpose | Default |
|----------|---------|---------|
| `COMFYUI_HOST` | Server URL | `http://127.0.0.1:8188` |
| `COMFYUI_AUTH_TOKEN` | Bearer token | — |
| `COMFYUI_JSON` | JSON output globally | — |
| `CLI_ANYTHING_HOME` | Session/manifest data dir | `~/.cli_anything` |

## Command Map

```
comfyui
├── system    stats | embeddings
├── nodes     list [--filter] | info <class>
├── models    list [type] | types
├── queue     list | submit <file> | interrupt --confirm | clear --confirm
├── history   list | show <id> | extract-outputs <id> | clear --confirm [id]
├── workflow  validate | show | save | nodes
├── session   new | list | show <id> | delete --confirm <id>
├── manifest  plan | show | apply --confirm
├── doctor    check | deps
└── repl      (interactive REPL)
```

## Key Patterns

- `--json` flag → all output as JSON (machine-readable)
- `--confirm` required for: `queue clear`, `queue interrupt`, `history clear`, `session delete`, `manifest apply`
- `--host` overrides `COMFYUI_HOST` per invocation
- `--token` overrides `COMFYUI_AUTH_TOKEN` per invocation
- 429 rate-limit → automatic retry (up to 3× with backoff, honors `Retry-After`)
- Session files → `~/.cli_anything/comfyui/sessions/<uuid>.json`
- Manifest files → local JSON, plan/show/apply workflow

## Architecture

```
cli_anything/comfyui/
├── comfyui_cli.py       Root Click group + REPL
├── core/
│   ├── secrets.py       ComfyUISecrets (host + token resolution)
│   ├── workflow.py      NodeInfo + Workflow data model
│   ├── queue.py         QueueItem + build_prompt_payload
│   ├── history.py       HistoryItem + OutputFile parsing
│   ├── manifest.py      ActionManifest plan/apply with atomic JSON write
│   └── session.py       Session persistence (MAX_HISTORY=50)
├── utils/
│   ├── comfyui_backend.py  Full REST client (14 endpoints, retry logic)
│   └── repl_skin.py     ReplSkin — emerald #10B981 accent, table formatter
└── commands/
    ├── system_cmds.py   doctor_cmds.py   history_cmds.py
    ├── manifest_cmds.py models_cmds.py   nodes_cmds.py
    ├── queue_cmds.py    session_cmds.py  workflow_cmds.py
    └── doctor_cmds.py
```

## Testing

```bash
# Offline (no server) — CI default
pytest vendor/cli-anything/comfyui/agent-harness/cli_anything/comfyui/tests/ -v

# With live ComfyUI
COMFYUI_E2E=1 pytest vendor/cli-anything/comfyui/agent-harness/cli_anything/comfyui/tests/ -v
```

~165 tests across `test_core.py` (offline unit) + `test_full_e2e.py` (integration).
E2E gate: skip when `COMFYUI_E2E` unset; FAIL (not skip) when set + server unreachable.
