# cli-anything-comfyui — Test Plan

## Phase 1 — Help Banners & Entrypoints

Verify `comfyui --help` and `cli-anything-comfyui --help` exit 0 and list all
9 subgroups (system, nodes, models, queue, history, workflow, session, manifest,
doctor). Each subgroup's `--help` also exits 0. `--version` prints `1.0.0`.
Unknown commands exit nonzero.

**Files:** `test_full_e2e.py::TestHelpBanners`
**Requires server:** No

## Phase 2 — JSON Output Mode

`--json` flag and `COMFYUI_JSON=1` env var produce valid JSON on stdout.
`doctor deps` is used as an offline proxy; output is `{"click": "...", ...}`.

**Files:** `test_full_e2e.py::TestJsonOutputMode`
**Requires server:** No

## Phase 3 — --confirm Gate

Destructive commands (`queue clear`, `queue interrupt`, `history clear`,
`session delete`) exit 1 immediately without `--confirm` — before touching the
network. With `--confirm` + unreachable host they still fail, but with a
network error (different code path confirms the gate was passed).

**Files:** `test_full_e2e.py::TestConfirmGate`
**Requires server:** No

## Phase 4 — Workflow Commands (Offline)

`workflow validate` / `show` / `nodes` operate on local JSON files with no
server. Valid workflow files exit 0; invalid JSON exits nonzero; missing files
exit nonzero.

**Files:** `test_full_e2e.py::TestWorkflowOffline`
**Requires server:** No

## Phase 5 — Session Roundtrip (Offline)

`session new` creates a session file, `session list` returns it, `session show`
returns full detail with the correct ID, `session delete --confirm` removes it.
Multiple creates are all listed. Nonexistent session IDs exit nonzero.
Uses `CLI_ANYTHING_HOME` env var to isolate temp dirs per test.

**Files:** `test_full_e2e.py::TestSessionOffline`
**Requires server:** No

## Phase 6 — Live Server Tests

With `COMFYUI_E2E=1` and a real ComfyUI instance at `COMFYUI_HOST`:

- `doctor check` exits 0
- `system stats` returns a dict with keys
- `system embeddings` returns a list
- `nodes list` returns data
- `nodes info KSampler` succeeds
- `models types` returns list
- `models list checkpoints` returns list
- `queue list` returns running/pending structure
- `history list` returns data
- `queue submit` with a minimal workflow returns prompt_id

**Files:** `test_full_e2e.py::TestLiveServerConnectivity`
**Requires server:** Yes — `COMFYUI_E2E=1 COMFYUI_HOST=http://127.0.0.1:8188`

## Phase 7 — Unreachable Host (FAIL, Not Skip)

With `COMFYUI_E2E=1` and a known-dead port (59999):

All network commands (`system stats`, `nodes list`, `models list`, `history list`,
`queue list`, `doctor check`) exit nonzero. JSON mode outputs `{"error": "..."}`.
These tests **FAIL** (not skip) when COMFYUI_E2E=1 — proving the live gate is real.

**Files:** `test_full_e2e.py::TestUnreachableHost`
**Requires server:** No (intentionally unreachable)

## Phase 8 — Manifest Offline

`manifest show` on a local manifest file exits 0 and returns JSON.
`manifest apply` without `--confirm` exits 1 before touching the network.

**Files:** `test_full_e2e.py::TestManifestOffline`
**Requires server:** No

## Phase 9 — Doctor Deps (Offline)

`doctor deps` exits 0 and returns a dict with `click` and `httpx` keys
showing installed versions. No server required.

**Files:** `test_full_e2e.py::TestDoctorDeps`
**Requires server:** No

---

## Running Tests

```bash
# Offline unit tests only (CI default)
pytest cli_anything/comfyui/tests/test_core.py -v

# All tests, no server (e2e tests skip)
pytest cli_anything/comfyui/tests/ -v

# Full e2e suite with live ComfyUI
COMFYUI_E2E=1 COMFYUI_HOST=http://127.0.0.1:8188 pytest cli_anything/comfyui/tests/ -v

# Quick smoke — just banners and deps
COMFYUI_E2E=1 pytest cli_anything/comfyui/tests/test_full_e2e.py::TestHelpBanners \
  cli_anything/comfyui/tests/test_full_e2e.py::TestDoctorDeps -v
```

## Test Count Summary

| File | Classes | Tests |
|------|---------|-------|
| `test_core.py` | 15 | ~110 |
| `test_full_e2e.py` | 9 | ~55 |
| **Total** | **24** | **~165** |
