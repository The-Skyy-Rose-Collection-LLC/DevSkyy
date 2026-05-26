# HF-SPACES — Phase 1 Analysis + Phase 2 Architecture

## Phase 1: API Landscape Analysis

### SDK Version Target
`huggingface_hub >= 0.26.0, < 1.0` — `SpaceHardware` enum is stable, `HfApi` is the
authoritative client.

### Available HfApi Methods (confirmed)

| Operation | Method | Notes |
|-----------|--------|-------|
| Space info | `space_info(repo_id)` | Returns `SpaceInfo` with `.runtime.stage`, `.runtime.hardware.current` |
| Pause | `pause_space(repo_id)` | Sets stage → `PAUSED` |
| Restart | `restart_space(repo_id, factory_reboot=False)` | Warm restart |
| Set hardware | `request_space_hardware(repo_id, hardware)` | `SpaceHardware` enum |
| Set sleep time | `set_space_sleep_time(repo_id, sleep_time)` | seconds, -1 = never |
| Add secret | `add_space_secret(repo_id, key, value)` | Write-only |
| Delete secret | `delete_space_secret(repo_id, key)` | Destructive — STOP-AND-SHOW |
| Add variable | `add_space_variable(repo_id, key, value)` | Env var (not secret) |
| Delete variable | `delete_space_variable(repo_id, key)` | |
| Get variables | `get_space_variables(repo_id)` | Returns `{key: {"value": ..., "description": ...}}` |
| List spaces | `list_spaces(author=..., search=...)` | Generator of `SpaceInfo` |
| Upload README | `upload_file(path_or_fileobj, path_in_repo="README.md", repo_id, repo_type="space")` | |
| Duplicate | `duplicate_space(from_id, to_id, private=True, exist_ok=False)` | |

### Known API Gaps (Phase 1 findings — locked)

#### 1. Secret Enumeration — NOT POSSIBLE via HfApi
`HfApi` has **no** `get_space_secrets` or equivalent. Secrets are write-only by design
(HF security model: values must never be readable after write). The `secrets list` command
reads from the **local manifest only**. This is documented explicitly — users must maintain
their manifest to track what secrets are deployed. The API will return an explicit message
stating this limitation.

#### 2. Streaming Logs — NOT in HfApi public surface
Neither `get_space_runtime_logs` nor any log-streaming method exists in `HfApi`. Implemented
via raw `httpx` SSE calls:
- Run logs: `GET https://huggingface.co/api/spaces/{owner}/{name}/logs/run`
- Build logs: `GET https://huggingface.co/api/spaces/{owner}/{name}/logs/build`
Headers: `Authorization: Bearer {token}`. Documented as bypassing HfApi.
Falls back gracefully when `httpx` is not installed (install extra: `pip install cli-anything-hf-spaces[logs]`).

#### 3. Factory Reset — NOT in HfApi
No `factory_reset_space` method exists. This is a web-UI only operation. **Not exposed**
in this CLI. Documented in the `doctor` command output.

#### 4. Secret Values — Write-Only
`add_space_secret` accepts a value but `get_space_variables` does NOT return secrets.
Manifest drift detection for secrets is one-way: we can know what we *want* deployed
(from manifest), but cannot verify what is *currently* deployed. Manifest apply always
re-writes secrets to ensure desired state.

#### 5. `Repository` Class — Deprecated
`huggingface_hub >= 0.16` deprecated `Repository`. All file operations use `upload_file`.

---

## Phase 2: Architecture

### Namespace Layout

```
cli_anything/hf_spaces/
├── __init__.py               # empty
├── hf_spaces_cli.py          # Click root group + REPL entry + CliState
├── core/
│   ├── __init__.py
│   ├── hardware.py           # SpaceHardware enum proxy + cost table
│   ├── space.py              # SpaceRef dataclass + URL/slug parser
│   ├── secrets.py            # SecretEntry / VariableEntry dataclasses
│   ├── session.py            # Session + _locked_save_json (atomic writes)
│   └── manifest.py           # ManifestSpec + plan/apply diff logic
├── utils/
│   ├── __init__.py
│   ├── hf_backend.py         # HfApi wrapper, auth resolution, typed exceptions
│   └── repl_skin.py          # Vendor copy of ReplSkin (prompt-toolkit)
├── commands/
│   ├── __init__.py
│   ├── space_cmds.py         # space info / list / duplicate / pause / restart
│   ├── hardware_cmds.py      # hardware get / set / list-tiers
│   ├── secrets_cmds.py       # secrets set / delete / list (manifest-only)
│   ├── vars_cmds.py          # vars get / set / delete / list
│   ├── logs_cmds.py          # logs run / build (httpx SSE)
│   ├── readme_cmds.py        # readme get / set / sync
│   ├── manifest_cmds.py      # manifest init / plan / apply / show
│   ├── session_cmds.py       # session list / show / delete
│   └── doctor_cmds.py        # doctor check
├── tests/
│   ├── TEST.md
│   ├── test_core.py          # 40+ unit tests (no live HF)
│   └── test_full_e2e.py      # subprocess e2e (HF_SPACES_E2E=1 gate)
└── skills/
    └── SKILL.md
```

### CliState + emit() Pattern

```python
class CliState:
    json_output: bool
    token: str | None   # in-memory only, never written to disk

def emit(state, payload, *, human): ...   # json or human print
def handle_backend_error(state, exc): ... # returns exit code 1
```

### STOP-AND-SHOW Gate Protocol

Any command tagged `@destructive` must:
1. Print manifest of exact changes with `[STOP]` prefix
2. Exit 0 if `--confirm` not passed (shows manifest only)
3. Execute only when `--confirm` is passed

Destructive commands: `hardware set`, `secrets delete`, `manifest apply`, `space pause`.

### Session Storage

`~/.cli_anything/hf_spaces/sessions/{session_id}.json` — atomic writes via
`_locked_save_json`. Token is **never** included in session JSON.

### Auth Resolution Order

1. `--token` flag (in-memory, never written)
2. `HF_TOKEN` env var
3. `~/.cache/huggingface/token` (written by `huggingface-cli login`)
4. Unauthenticated (public spaces only)

### Manifest Model

`manifest.json` at user-specified path (default `./hf-space-manifest.json`):
```json
{
  "schema_version": "1",
  "space_id": "owner/name",
  "hardware": "cpu-basic",
  "sleep_time": 300,
  "variables": {"KEY": "value"},
  "secrets": ["SECRET_KEY_1", "SECRET_KEY_2"],
  "readme_path": "./README.md"
}
```

`manifest plan`: diff desired vs actual (hardware via `get_space_runtime`,
vars via `get_space_variables`, README via file comparison). Secrets: always flagged
as "cannot verify — will re-apply on apply".

`manifest apply`: STOP-AND-SHOW of all changes, requires `--confirm`.
