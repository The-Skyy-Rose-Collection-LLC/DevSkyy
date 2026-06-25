# TRELLIS.md — cli-anything-trellis Codebase Analysis & Architecture

## Phase 1: Codebase Analysis

### Source material

Microsoft TRELLIS.2 is an image-to-3D generative model.  Key upstream facts
confirmed from the runner implementation and the TRELLIS.2 public API:

| Item | Value |
|------|-------|
| HuggingFace checkpoint | `microsoft/TRELLIS.2-4B` |
| Pipeline class | `trellis2.pipelines.Trellis2ImageTo3DPipeline` |
| Entry method | `pipeline.run(image, seed, preprocess_image, sparse_structure_sampler_params, shape_slat_sampler_params, tex_slat_sampler_params, return_latent)` |
| Mesh output | `outputs[0]` — has `.vertices`, `.faces`, `.attrs`, `.coords`, `.voxel_size` |
| PBR attribute layout | `pipeline.pbr_attr_layout` |
| 3D export | `o_voxel.postprocess.to_glb(vertices, faces, attr_volume, coords, attr_layout, voxel_size, aabb, decimation_target, texture_size, remesh, remesh_band, remesh_project, verbose)` |
| GLB export | `glb.export(path, extension_webp=True)` |
| Compute requirement | CUDA GPU (no CPU mode) |

### Resolution presets

| Preset | sparse_structure steps | shape_slat steps | tex_slat steps |
|--------|----------------------|-----------------|----------------|
| `low` | 12 | 12 | 12 |
| `high` | 50 | 50 | 50 |

All presets use `cfg_strength=7.5, rescale=0.7` (sparse) and
`cfg_strength=3.0, rescale_cfg=0.7, rescale_t=0.25` (shape/tex slat).

### Import constraint

The CLI must be importable in any standard Python 3.10+ environment.
`trellis2`, `torch`, and `o_voxel` are never imported by:
- `trellis_cli.py`
- `core/*.py`
- `utils/trellis_backend.py`
- `utils/repl_skin.py`

Only `resources/trellis_runner.py` imports these heavy dependencies.

---

## Phase 2: Architecture Decisions

### Decision 1: Subprocess runner (not gradio_client, not importlib)

**Options considered:**
1. `gradio_client` — requires a running Gradio server; adds network latency;
   no obvious server to connect to in offline/local use.
2. Direct import via `importlib` at runtime — still requires trellis2 in the
   same Python environment as the CLI; breaks the isolation requirement.
3. **Subprocess runner** — CLI ships `resources/trellis_runner.py`; backend
   invokes `[python, runner_path, "generate"]` with JSON on stdin/stdout.

**Chosen: Subprocess runner.**

Rationale:
- Mirrors the elementor/wp-cli pattern exactly (proven in the sister harness).
- Runner can use a completely different Python interpreter and venv.
- CLI is importable with zero GPU dependencies.
- Errors are communicated as JSON in stdout, not exit codes, so partial results
  (started_at set, pipeline failed mid-run) are always capturable.
- Subprocess args are always lists; `shell=False` is the default.

### Decision 2: Atomic session writes via `_locked_save_json`

Sessions are small (< 10 KB) and written infrequently.  The pattern:

```
mkstemp → write → fsync → os.replace
```

guarantees the reader always sees a complete file.  `fcntl.flock` is applied
where available (POSIX); on Windows it is a no-op.  The same pattern is used
in the elementor harness for consistency.

### Decision 3: Append-only JSONL catalog

Generation jobs are append-only by design: a job's status may change (pending
→ running → done/failed) but the canonical record is the last one written for
a given `job_id`.  `find_record` scans in reverse to return the most recent
entry.  This makes the catalog resilient to partial writes: malformed lines are
silently skipped; good lines behind them are still readable.

### Decision 4: `secrets.token_hex(8)` job IDs

Produces 16-character lowercase hex strings (e.g., `"a1b2c3d4e5f6a7b8"`).
This matches the elementor harness ID convention and is collision-resistant for
practical job volumes (2^64 space).

### Decision 5: Namespace package (`cli_anything.*`)

`cli_anything/` has no `__init__.py` so multiple `cli_anything.*` sub-packages
(trellis, elementor, etc.) can coexist in the same environment without
conflicting.  `setup.py` uses `find_namespace_packages(include=["cli_anything.*"])`.

### Decision 6: Resolution presets baked into the runner, not the CLI

The CLI passes `resolution="low"` or `"high"` as a string.  The runner owns
the sampler parameter lookup table.  This keeps the CLI thin and means sampler
tuning (e.g., adding a "medium" preset) requires only a runner change, not a
CLI release.

---

## File map

```
agent-harness/
├── setup.py                              # Namespace package, entry point
├── README.md                             # User-facing docs
├── TRELLIS.md                            # This file
├── cli_anything/
│   └── trellis/
│       ├── __init__.py                   # Version string only
│       ├── trellis_cli.py                # Click CLI (no trellis2 import)
│       ├── core/
│       │   ├── __init__.py
│       │   ├── generation.py             # GenerationRecord + presets
│       │   ├── session.py                # Session persistence
│       │   └── catalog.py                # JSONL append-only catalog
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── trellis_backend.py        # Subprocess orchestration
│       │   └── repl_skin.py              # prompt-toolkit REPL skin
│       ├── resources/
│       │   └── trellis_runner.py         # ONLY file that imports trellis2
│       ├── skills/
│       │   └── SKILL.md                  # Bundled agent skill
│       └── tests/
│           ├── __init__.py
│           ├── TEST.md                   # Test plan + results
│           ├── test_core.py              # 81 unit tests (no GPU required)
│           └── test_full_e2e.py          # E2E tests (TRELLIS_E2E=1 + GPU)
└── skills/
    └── cli-anything-trellis/
        └── SKILL.md                      # Repo-root canonical skill
```

---

## Backend strategy summary

The CLI harness never imports `trellis2`, `torch`, or `o_voxel`.  When a
generation job is submitted:

1. `trellis_cli.py` builds a `GenerationRecord` and calls
   `trellis_backend.run_generation(record, python_path, trellis_home)`.
2. `trellis_backend` serialises the record to JSON and pipes it as stdin to
   `subprocess.run([python_path, trellis_runner_path, "generate"], ...)`.
3. `trellis_runner.py` (the subprocess) imports `trellis2`, loads the pipeline,
   runs inference, exports the GLB, and writes the result record as JSON to
   stdout.
4. `trellis_backend` parses stdout back into a `GenerationRecord` and returns
   it to the CLI, which persists it to the JSONL catalog and emits it to the
   user.

Errors at any stage are communicated as `status=failed` JSON — the subprocess
always exits 0 when it can write JSON output.  Exit non-zero only occurs when
the runner process itself crashes before it can write any output.

---

## Scope limits

1. **TRELLIS.2 only** — no other image-to-3D backends.
2. **Single-job dispatch** — `generate run` is synchronous; no queue.
3. **CUDA required** — CPU inference is not supported by TRELLIS.2.
4. **GLB output only** — other mesh formats are not exposed.
5. **No model fine-tuning** — uses `microsoft/TRELLIS.2-4B` from HuggingFace Hub.
