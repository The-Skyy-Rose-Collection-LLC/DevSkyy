# cli-anything-trellis — Test Plan

## Phase 4 Plan (Unit Tests)

### Scope

All unit tests in `test_core.py` must pass without:
- A CUDA-capable GPU
- TRELLIS.2 installed (`trellis2`, `torch`, `o_voxel`)
- Network access

Tests use `tmp_path`, `monkeypatch`, and mocked `run_generation` to remain
fully isolated from the GPU environment.

### Test classes and coverage targets

| Class | Tests | What is covered |
|-------|-------|-----------------|
| `TestJobId` | 3 | `new_job_id()` length, hex charset, uniqueness |
| `TestResolutionPresets` | 4 | Preset keys, default ("high"), positive step counts |
| `TestGenerationRecord` | 13 | Construction, status transitions, serialisation, immutability |
| `TestValidateStatus` | 2 | Valid status strings, invalid raises ValueError |
| `TestLockedSaveJson` | 4 | File creation, content, atomic replace via `os.replace`, parent-dir creation |
| `TestSession` | 14 | Default session, save/load roundtrip, missing=fresh, corrupted=fresh, history push/cap, set/unset settings, delete, list, repr |
| `TestCatalog` | 9 | Append+iter, empty catalog, malformed-line skip, limit, status filter, find_record, stats, empty stats, multiple append |
| `TestBackendErrors` | 3 | Error hierarchy, `RunnerError` fields, `is RuntimeError` |
| `TestDiscovery` | 10 | `discover_trellis_home` (explicit/env/session/missing), `discover_trellis_python` (explicit/env/fallback), `build_runner_env` variants |
| `TestCliImport` | 3 | CLI importable without trellis2, `--version` flag, `--help` flag |
| `TestCliSessionCommands` | 6 | `session show`, JSON mode, `session set`+show, `session list` JSON, `clear-history`, delete missing |
| `TestCliCatalogCommands` | 2 | `catalog list` empty, `catalog stats --json` |
| `TestCliConfigCommands` | 3 | `config show`, JSON mode, `config validate --json` |
| `TestCliJobsCommands` | 3 | `jobs list` empty, JSON empty, `jobs show` missing |
| `TestGenerateRunDryMock` | 3 | `generate run` success (mock), failure (mock), JSON success (mock) |

**Total: 81 unit tests**

### Invariants enforced

- `new_job_id()` → always 16-character hex string
- `GenerationRecord` transitions are immutable (original unchanged)
- `_locked_save_json` writes via temp file + `os.replace` (never partial write)
- Session `push_history` caps at `MAX_HISTORY = 50`
- Backend errors all subclass `BackendError(RuntimeError)`
- CLI is importable without `trellis2` / `torch` in `sys.modules`

---

## Phase 6 Results

### Command

```bash
cd /path/to/trellis/agent-harness
/tmp/cli-anything-trellis-venv/bin/pytest \
  cli_anything/trellis/tests/test_core.py \
  --tb=short -q
```

### Results

```
92 passed in 0.18s
```

All 92 unit tests passed.  `test_full_e2e.py` was collected but skipped at
module level with `"Set TRELLIS_E2E=1 to run end-to-end TRELLIS tests"` — no
silent passes, no false failures.

### E2E gate verification

```bash
# Verify E2E module skips cleanly without the flag:
pytest cli_anything/trellis/tests/test_full_e2e.py -v
# → "SKIPPED [module]: Set TRELLIS_E2E=1 to run end-to-end TRELLIS tests"

# Verify E2E module fails explicitly when flag is set (no GPU/torch in venv):
TRELLIS_E2E=1 pytest cli_anything/trellis/tests/test_full_e2e.py -v
# → 16 explicit ERRORs — fixture setup fails because TRELLIS_HOME is unset
# → No silent passes; every test errors visibly
```

**TRELLIS_E2E=1 output (no GPU env):**
```
ERROR test_full_e2e.py::TestProbeGpu::test_probe_gpu_returns_dict
ERROR test_full_e2e.py::TestProbeGpu::test_probe_gpu_has_required_keys
... (16 total ERRORs — 0 passes, 0 silent skips)
```

### Environment

```
Python: 3.11+
click: 8.1+
prompt-toolkit: 3.0+
pytest: 7.4+
trellis2: NOT INSTALLED (unit tests do not require it)
torch: NOT INSTALLED
CUDA: NOT REQUIRED for unit tests
```
