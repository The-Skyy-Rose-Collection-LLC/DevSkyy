# cli-anything-trellis

CLI harness for [Microsoft TRELLIS.2](https://github.com/microsoft/TRELLIS) image-to-3D generation.

## Overview

`cli-anything-trellis` wraps TRELLIS.2 behind a clean Click CLI following the
cli-anything methodology: the CLI itself never imports `trellis2`, `torch`, or
`o_voxel`.  All GPU work is dispatched to `resources/trellis_runner.py` via
subprocess, keeping the CLI importable in any Python environment.

## Installation

```bash
# Inside a Python 3.10+ environment (trellis2 NOT required at this step)
pip install -e ".[dev]"
```

## Quick start

```bash
# Check GPU availability
trellis config probe-gpu

# Generate a GLB from an image (low resolution, ~30 s on an A100)
trellis generate run \
  --image /path/to/product.png \
  --output-dir /tmp/trellis-out \
  --resolution low \
  --seed 42

# List recent jobs
trellis jobs list

# Interactive REPL
trellis
```

## Environment variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TRELLIS_HOME` | Path to TRELLIS.2 repo/install root | — |
| `TRELLIS_PYTHON` | Python interpreter with trellis2 installed | `sys.executable` |

Both can also be set with `--trellis-home` / `--trellis-python` flags or
persisted per-session with `trellis session set trellis_home /path/to`.

## Commands

| Command | Description |
|---------|-------------|
| `trellis generate run` | Submit a new generation job |
| `trellis jobs list` | List recent jobs from the catalog |
| `trellis jobs show <job_id>` | Show details of a specific job |
| `trellis catalog list` | Browse the append-only catalog |
| `trellis catalog stats` | Aggregated catalog statistics |
| `trellis session show` | Show current session settings |
| `trellis session set <key> <value>` | Persist a session setting |
| `trellis session list` | List saved sessions |
| `trellis config show` | Show current config |
| `trellis config probe-gpu` | Check GPU availability |
| `trellis config validate` | Validate TRELLIS.2 installation |

Append `--json` to any command for machine-readable output.

## Architecture

```
cli_anything/trellis/
├── trellis_cli.py          # Click CLI — never imports trellis2
├── core/
│   ├── generation.py       # GenerationRecord dataclass + job IDs
│   ├── session.py          # Session persistence (atomic writes)
│   └── catalog.py          # Append-only JSONL job history
├── utils/
│   ├── trellis_backend.py  # Subprocess orchestration + error hierarchy
│   └── repl_skin.py        # Rich prompt-toolkit REPL skin
├── resources/
│   └── trellis_runner.py   # ONLY file that imports trellis2/torch/o_voxel
├── skills/
│   └── SKILL.md            # Bundled skill for agent use
└── tests/
    ├── test_core.py         # 40+ unit tests (no GPU required)
    └── test_full_e2e.py     # E2E tests (requires TRELLIS_E2E=1 + GPU)
```

## Running tests

```bash
# Unit tests only (no GPU required)
pytest cli_anything/trellis/tests/test_core.py -v

# E2E tests (requires TRELLIS.2 Python env + CUDA GPU)
TRELLIS_E2E=1 \
TRELLIS_HOME=/path/to/trellis \
TRELLIS_PYTHON=/path/to/trellis/venv/bin/python \
  pytest cli_anything/trellis/tests/test_full_e2e.py -v
```

## Sessions

Sessions are stored at `~/.cli_anything/trellis/sessions/`.
The append-only job catalog lives at `~/.cli_anything/trellis/catalog.jsonl`.

## Scope limits

1. **TRELLIS.2 only** — no other image-to-3D backends are supported.
2. **Single-job dispatch** — no job queue or batch API; each `generate run`
   runs synchronously and blocks until the GLB is exported.
3. **CUDA required** — CPU inference is not supported by TRELLIS.2.
4. **GLB output only** — other mesh formats (OBJ, FBX, USD) are not exposed.
5. **No model fine-tuning** — the harness calls `from_pretrained` with the
   public Microsoft checkpoint; custom weights require direct use of the runner.
