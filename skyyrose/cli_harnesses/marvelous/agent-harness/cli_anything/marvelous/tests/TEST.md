# cli-anything-marvelous — Test Plan

## Overview

| Metric | Target | Notes |
|--------|--------|-------|
| Unit test count | 40+ | Pure-Python, no MD required |
| E2E test count | 8 | Skipped without `MARVELOUS_E2E=1` |
| Coverage target | 85%+ | `pytest --cov=cli_anything.marvelous` |
| Live MD gate | `MARVELOUS_E2E=1` | Only fires with real MD installed |

## Test Inventory

### test_core.py — Unit Tests

| Class | Tests | Description |
|-------|-------|-------------|
| `TestFabricProperty` | 3 | Default values, dict round-trip, unknown key tolerance |
| `TestPatternPiece` | 3 | Defaults, dict round-trip, extra key tolerance |
| `TestGarment` | 7 | Empty, counts, fabric/pattern lookup, JSON round-trip, from_dict empty |
| `TestReadProjectMeta` | 9 | Missing file, wrong ext, not-a-zip, empty zip, manifest name, pattern/fabric counts, thumbnail detection, zprj format, to_dict keys |
| `TestLoadGarmentFromProject` | 3 | Basic load, string pattern/fabric handling, source_file recorded |
| `TestSession` | 2 | Dict round-trip, from_dict extra keys |
| `TestSessionCrud` | 9 | save/load, missing raises, empty list, sorted list, delete exists, delete not found, new_session persists, atomic write, malformed JSON |
| `TestLibraryEntry` | 2 | Round-trip, bad tags coercion |
| `TestLibraryCrud` | 9 | Empty list, import+list, dup slug raises, missing source, wrong ext, get_entry, not_found, delete, entry_source_path |
| `TestFindMarvelousBinary` | 3 | Env override missing, env override valid, no MD raises |
| `TestRenderScriptTemplate` | 3 | Basic substitution, missing var raises, multiple vars |
| `TestLoadScriptTemplate` | 4 | export/simulate/add_fabric templates load, missing raises |

**Total unit tests: 57**

### test_templates.py — Script Template Rendering (Phase 6)

| Class | Tests | Description |
|-------|-------|-------------|
| `TestExportTemplate` | 9 | Renders project/output/format vars, export_api call, ImportZpac call, missing-var raises, Windows path, Unicode path |
| `TestSimulateTemplate` | 5 | Renders frames, utility_api.Simulate, ExportZpac, missing frames raises, zero frames |
| `TestAddFabricTemplate` | 5 | Renders pattern/fabric name, AssignFabricToPattern call, missing var raises, special chars |

**Subtotal: 19**

### test_garment_edge_cases.py — Garment Dataclass Edges (Phase 6)

| Class | Tests | Description |
|-------|-------|-------------|
| `TestFabricPropertyEdgeCases` | 5 | All-fields round-trip, float type, default color, from_dict only-name, to_dict key completeness |
| `TestPatternPieceEdgeCases` | 3 | All-fields round-trip, default vertex_count, from_dict only-name |
| `TestGarmentEdgeCases` | 11 | frames default/override, notes/source_file round-trip, multi-fabric, case-insensitive lookups, to_json valid JSON, Unicode round-trip, frames coercion |

**Subtotal: 19**

### test_backend_pure.py — Backend Without MD (Phase 6)

| Class | Tests | Description |
|-------|-------|-------------|
| `TestFindMarvelousBinaryExtra` | 4 | Directory path raises, empty env falls through, whitespace env falls through, multiple installs picks last |
| `TestRunMdScriptCleanup` | 4 | Tempfile cleaned on success, on script error, on timeout; error captures returncode+stderr |
| `TestRenderScriptTemplateEdgeCases` | 4 | Empty template, extra vars ignored, bare-$ raises ValueError, numeric value coercion |

**Subtotal: 12**

### test_session_concurrent.py — Session Edge Cases + Concurrency (Phase 6)

| Class | Tests | Description |
|-------|-------|-------------|
| `TestSessionSchemaEdgeCases` | 5 | Malformed JSON raises, unknown fields ignored, missing optional fields use defaults, list_sessions skips corrupt, empty dict raises TypeError, updated_at bumped on save |
| `TestSessionConcurrentWrites` | 3 | Concurrent same-session writes leave valid JSON, concurrent distinct sessions all written, concurrent new_session IDs are unique |

**Subtotal: 8**

**Phase 6 total: 58 new tests**

### test_full_e2e.py — CLI + Live Tests

| Class | Tests | Gate |
|-------|-------|------|
| `TestCliSmoke` | 8 | Always (no MD needed) |
| `TestLiveExport` | 2 | `MARVELOUS_E2E=1` only |

**Total E2E tests: 10**

## Unit Test Plan

### Fixtures

```python
def _make_zpac(path, manifest=None, garment=None) -> Path:
    """Create minimal synthetic .zpac ZIP for pure-Python testing."""
    with zipfile.ZipFile(path, "w") as zf:
        if manifest: zf.writestr("project.json", json.dumps(manifest))
        if garment:  zf.writestr("garment.json", json.dumps(garment))
    return path
```

Session tests use `monkeypatch.setattr(session_mod, "SESSIONS_DIR", tmp_path / "sessions")`.
Library tests use `monkeypatch.setattr(library_mod, "LIBRARY_DIR", tmp_path / "library")`.
Backend tests monkeypatch `glob.glob` to simulate no MD installed.

### Key assertions

- `_locked_save_json`: no `.session-*.json` tempfiles left after write
- `load_session("nonexistent")` → `FileNotFoundError`
- `load_session` with corrupt JSON → `ValueError` with "Malformed" message
- `import_project` with duplicate slug → `FileExistsError`
- `render_script_template` missing var → `KeyError`
- All three `.tpl` files loadable and contain expected API calls

## E2E Test Plan

`_resolve_cli()` resolution:
1. `shutil.which("cli-anything-marvelous")` — installed binary
2. `[sys.executable, "-m", "cli_anything.marvelous"]` — editable install
3. If `CLI_ANYTHING_FORCE_INSTALLED=1`: raises `RuntimeError` when binary missing

Smoke tests (`TestCliSmoke`) run without MD:
- `--version` → stdout contains "1.0.0"
- `--help` → stdout contains "marvelous"
- `config doctor --json` → valid JSON with `md_binary_found` and `issues` keys
- `project info --json <synthetic.zpac>` → parses name and format correctly
- `session save/status/delete` round-trip via `--json`

Live tests (`TestLiveExport`) skip unless `MARVELOUS_E2E=1`:
- Use `MARVELOUS_TEST_ZPAC=/path/to/file.zpac` env var for real fixture
- Falls back to synthetic .zpac (MD may reject — expected)
- `export run --format obj` → `{"ok": true}`
- `simulate run --frames 10` → `{"frames": 10}`

## Coverage Targets

```bash
# Install dev deps
pip install -e ".[dev]"

# Unit tests only (no MD)
pytest cli_anything/marvelous/tests/test_core.py -v --tb=short

# All tests (smoke E2E always runs)
pytest cli_anything/marvelous/tests/ -v --tb=short

# With coverage
pytest cli_anything/marvelous/tests/ --cov=cli_anything.marvelous \
  --cov-report=term-missing -q

# Force installed binary path (CI)
CLI_ANYTHING_FORCE_INSTALLED=1 pytest cli_anything/marvelous/tests/ -v

# Full live run (requires MD + real .zpac)
MARVELOUS_E2E=1 MARVELOUS_TEST_ZPAC=/path/to/shirt.zpac \
  pytest cli_anything/marvelous/tests/ -v
```

## Results

_Updated after each test run._

| Date | Unit | E2E (smoke) | E2E (live) | Coverage |
|------|------|-------------|------------|----------|
| TBD  | —    | —           | skipped    | —        |

### Phase 6 — 2026-05-25

| Date | Pass | Skipped | Fail | Notes |
|------|------|---------|------|-------|
| 2026-05-25 | 126 | 2 | 0 | Phase 6 adds 58 new tests across 4 files; 2 skipped are live-MD E2E |

**Production bugs fixed during Phase 6:**
1. **`resources/scripts/*.tpl` comment contained literal `${var}`** — `string.Template.substitute` tried to substitute a variable named `var`, raising `KeyError` every time any of the three templates was rendered. Fixed by escaping to `$${var}` in the comment line of all three `.tpl` files.
2. **`new_session()` timestamp-only IDs collide under concurrent load** — millisecond resolution is insufficient when multiple threads call `new_session()` in the same millisecond. Fixed by appending a process-global monotonic counter (`itertools.count`) to the ID: `md-{ms}-{seq}`.
