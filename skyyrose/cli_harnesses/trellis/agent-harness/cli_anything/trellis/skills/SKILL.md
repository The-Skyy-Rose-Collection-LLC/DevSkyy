---
name: cli-anything-trellis
description: >
  Operate the cli-anything-trellis harness: submit image-to-3D generation jobs
  via Microsoft TRELLIS.2, inspect job history, manage sessions, and probe GPU
  availability — all from the CLI without importing trellis2 directly.
triggers:
  - /trellis
  - generate 3d from image
  - trellis generate
  - image to glb
  - probe-gpu trellis
---

# cli-anything-trellis Skill

## When to use

Invoke this skill when:
- Submitting an image-to-3D generation job via TRELLIS.2
- Checking GPU availability in the TRELLIS Python environment
- Inspecting job history or catalog statistics
- Managing trellis session settings (home, python, resolution defaults)
- Writing agent code that calls the trellis CLI programmatically

## Prerequisites

1. `pip install -e ".[dev]"` from the harness root
2. TRELLIS.2 installed in a separate Python environment
3. `TRELLIS_HOME` pointing to the TRELLIS.2 repo/install root
4. `TRELLIS_PYTHON` pointing to the Python interpreter with trellis2 installed
5. A CUDA-capable GPU (required by TRELLIS.2; CPU inference not supported)

## Install

```bash
cd /path/to/cli-anything/trellis/agent-harness
pip install -e ".[dev]"
```

Verify:
```bash
trellis --version
trellis config probe-gpu
```

## Command groups

| Group | Subcommands | Purpose |
|-------|-------------|---------|
| `generate` | `run` | Submit image-to-3D job |
| `jobs` | `list`, `show` | Browse/inspect job history |
| `catalog` | `list`, `stats` | Read append-only JSONL catalog |
| `session` | `show`, `set`, `unset`, `list`, `delete`, `clear-history` | Persist settings |
| `config` | `show`, `validate`, `probe-gpu` | Installation/GPU checks |
| *(bare)* | — | Launch interactive REPL |

## Agent-facing JSON contract

All commands accept `--json` for machine-readable output.

### `generate run --json`

```json
{
  "job_id": "a1b2c3d4e5f6a7b8",
  "image_path": "/abs/path/to/image.png",
  "output_dir": "/abs/path/to/output",
  "resolution": "low",
  "seed": 42,
  "decimation_target": 1000000,
  "texture_size": 4096,
  "status": "done",
  "created_at": 1716000000.0,
  "started_at": 1716000001.0,
  "finished_at": 1716000045.0,
  "glb_path": "/abs/path/to/output/a1b2c3d4e5f6a7b8.glb",
  "error": null,
  "extra": {}
}
```

Status values: `pending` | `running` | `done` | `failed`

### `config probe-gpu --json`

```json
{
  "available": true,
  "device_count": 1,
  "devices": [
    {"index": 0, "name": "NVIDIA A100-SXM4-80GB", "total_memory_gb": 79.2}
  ]
}
```

### `catalog stats --json`

```json
{
  "total": 12,
  "done": 10,
  "failed": 1,
  "pending": 0,
  "running": 1
}
```

## Worked examples

### Submit a low-resolution job and capture the GLB path

```bash
result=$(trellis --json \
  --trellis-home "$TRELLIS_HOME" \
  --trellis-python "$TRELLIS_PYTHON" \
  generate run \
  --image /path/to/product.png \
  --output-dir /tmp/trellis-out \
  --resolution low \
  --seed 42)

echo "$result" | python -c "import sys,json; d=json.load(sys.stdin); print(d['glb_path'])"
```

### Persist TRELLIS settings in the current session

```bash
trellis session set trellis_home "$TRELLIS_HOME"
trellis session set trellis_python "$TRELLIS_PYTHON"
trellis session set default_resolution low
# Now generate without flags:
trellis generate run --image product.png --output-dir /tmp/out
```

### Probe GPU from a Python agent

```python
import subprocess, json, sys

result = subprocess.run(
    [sys.executable, "-m", "cli_anything.trellis.trellis_cli",
     "--json", "config", "probe-gpu"],
    capture_output=True, text=True, timeout=30,
)
gpu_info = json.loads(result.stdout)
if not gpu_info["available"]:
    raise RuntimeError("No CUDA GPU — cannot run TRELLIS.2")
```

### Programmatic generation from Python

```python
import subprocess, json, sys, os

proc = subprocess.run(
    [sys.executable, "-m", "cli_anything.trellis.trellis_cli",
     "--json",
     "--trellis-home", os.environ["TRELLIS_HOME"],
     "--trellis-python", os.environ["TRELLIS_PYTHON"],
     "generate", "run",
     "--image", "/path/to/image.png",
     "--output-dir", "/tmp/trellis-out",
     "--resolution", "high",
     "--seed", "-1"],
    capture_output=True, text=True, timeout=900,
)
record = json.loads(proc.stdout)
if record["status"] != "done":
    raise RuntimeError(f"TRELLIS generation failed: {record['error']}")
glb_path = record["glb_path"]
```

## Error handling

| Error class | Cause | Resolution |
|-------------|-------|------------|
| `TrellisNotFoundError` | `TRELLIS_HOME` not set or no `trellis2/` dir inside | Set `TRELLIS_HOME` correctly |
| `TrellisPythonError` | Python interpreter not found or fails `--version` | Set `TRELLIS_PYTHON` to the trellis2 venv python |
| `GPUUnavailableError` | `torch.cuda.is_available()` returned False | Ensure CUDA drivers installed and a GPU is available |
| `RunnerError` | Runner subprocess exited non-zero with no JSON | Check `stderr` attribute for details |
| `RunnerTimeoutError` | Generation exceeded `--timeout` seconds | Increase timeout or use a lower resolution preset |

All errors are reflected in the JSON result when using `--json`:

```json
{"status": "failed", "error": "CUDA is not available ...", ...}
```

## Dry-run discipline

There is no `--dry-run` flag for generation (TRELLIS.2 is GPU-only with no
mock mode).  To test connectivity and environment without a GPU job:

```bash
trellis config validate     # checks TRELLIS_HOME + Python interpreter
trellis config probe-gpu    # checks CUDA via subprocess
```

## Session model

Sessions are persisted at `~/.cli_anything/trellis/sessions/<name>.json`.
The default session is named `default`.  Each session stores:

- `trellis_home` — path override
- `trellis_python` — interpreter override
- `default_resolution` — `"low"` or `"high"`
- `default_output_dir` — default output directory
- `history` — last 50 commands (capped)

The append-only job catalog lives at `~/.cli_anything/trellis/catalog.jsonl`.
One JSON record per line; never modified after append.

## Scope limits

1. **TRELLIS.2 only** — no other image-to-3D backends are wired.
2. **Single-job dispatch** — `generate run` is synchronous; no queue or batch.
3. **CUDA required** — CPU inference is not supported by TRELLIS.2.
4. **GLB output only** — OBJ, FBX, USD are not exposed; change the runner if needed.
5. **No model fine-tuning** — the harness uses `microsoft/TRELLIS.2-4B` from
   HuggingFace Hub; custom checkpoints require modifying `trellis_runner.py`.
