# cli-anything-comfyui

**Tier 2 #7** — CLI harness for [ComfyUI](https://github.com/comfyanonymous/ComfyUI).
Manage nodes, models, queue, history, workflows, sessions, and manifests from the command line.

## Install

```bash
pip install -e ".[dev]"
# or with REPL support:
pip install -e ".[all]"
```

## Quick Start

```bash
# Point at your ComfyUI instance (default: http://127.0.0.1:8188)
export COMFYUI_HOST=http://127.0.0.1:8188

comfyui system stats
comfyui nodes list --filter KSampler
comfyui models list checkpoints
comfyui queue list
comfyui history list
comfyui workflow validate my_workflow.json
comfyui queue submit my_workflow.json
comfyui doctor check
```

## Command Groups

| Group | Commands | Description |
|-------|----------|-------------|
| `system` | `stats`, `embeddings` | Server stats and embedding list |
| `nodes` | `list [--filter]`, `info <class>` | Node registry browser |
| `models` | `list [type]`, `types` | Model listing by type |
| `queue` | `list`, `submit <file>`, `interrupt --confirm`, `clear --confirm` | Execution queue |
| `history` | `list`, `show <id>`, `extract-outputs <id>`, `clear --confirm` | Completed prompts |
| `workflow` | `validate`, `show`, `save`, `nodes` | Workflow JSON tools |
| `session` | `new`, `list`, `show <id>`, `delete --confirm <id>` | Persistent sessions |
| `manifest` | `plan`, `show`, `apply --confirm` | Batched operations |
| `doctor` | `check`, `deps` | Health checks |

## Global Flags

| Flag | Env Var | Default | Description |
|------|---------|---------|-------------|
| `--host` | `COMFYUI_HOST` | `http://127.0.0.1:8188` | ComfyUI base URL |
| `--token` | `COMFYUI_AUTH_TOKEN` | — | Bearer token for auth |
| `--json` | `COMFYUI_JSON=1` | — | Machine-readable JSON output |
| `-V` / `--version` | — | — | Print version |

## Interactive REPL

```bash
comfyui repl
# > system stats
# > queue list
# > exit
```

## Testing

```bash
# Offline unit tests (no server required)
pytest cli_anything/comfyui/tests/ -v

# Full E2E with live ComfyUI
COMFYUI_E2E=1 pytest cli_anything/comfyui/tests/ -v
```

See [`cli_anything/comfyui/tests/TEST.md`](cli_anything/comfyui/tests/TEST.md) for the full 9-phase test plan.
