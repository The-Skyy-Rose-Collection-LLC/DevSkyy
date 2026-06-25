# MARVELOUS.md — cli-anything-marvelous Research + Architecture

## Phase 1 — API Research

### Marvelous Designer Scripting API

Marvelous Designer (CLO Virtual Fashion, MD 12+) exposes a Python scripting interface
through internal modules available only within the application process:

| Module | Key Functions |
|--------|--------------|
| `import_api` | `ImportFile(path)`, `ImportZpac(path)`, `ImportZprj(path)` |
| `export_api` | `ExportOBJ(path)`, `ExportFBX(path)`, `ExportAlembic(path)`, `ExportUSD(path)`, `ExportZpac(path)`, `ExportZprj(path)` |
| `utility_api` | `NewProject()`, `Simulate(frames)`, `GetVersion()` |
| `fabric_api` | `GetFabricCount()`, `AssignFabricToPattern(patternName, fabricName, texturePath)` |
| `pattern_api` | `GetPatternPieceNames()`, `GetPatternPieceCount()` |
| `ApiTypes` | Enum types for export format options |

**Reference:** https://developer.marvelousdesigner.com/scenario.html

### File Formats

| Extension | Description |
|-----------|-------------|
| `.zpac` | Primary project bundle — ZIP archive containing `project.json`, `garment.json`, texture assets |
| `.zprj` | Legacy project format — similar ZIP structure |

Both are readable with Python's stdlib `zipfile` module without MD installed.

### Headless / Batch Execution

**Important caveat:** As of MD 12, Marvelous Designer does not officially expose a
headless mode or documented `--script` CLI flag. The `--script` behavior assumed by
this harness is based on user workflow reports and is NOT confirmed in official
developer documentation. Official docs state: *"No command-line/batch session is
available as of Marvelous Designer 12."*

The `marvelous_backend.run_md_script()` function wraps the assumed invocation:
```
"Marvelous Designer" --script /tmp/script.py
```

If MD's actual invocation syntax differs, only `marvelous_backend.py` needs updating.
All script templates are valid Python and will work once the invocation path is known.

### macOS Binary Location

```
/Applications/CLO Virtual Fashion/Marvelous Designer*/Marvelous Designer.app/Contents/MacOS/Marvelous Designer
```

Override via `MARVELOUS_DESIGNER_BIN` env var.

### Export Format Coverage

| Format | API Function | Notes |
|--------|-------------|-------|
| obj | `ExportOBJ()` | Most compatible |
| fbx | `ExportFBX()` | Maya/3ds Max/Blender |
| alembic | `ExportAlembic()` | VFX pipelines |
| usd | `ExportUSD()` | Pixar Universal Scene Description |
| zpac | `ExportZpac()` | MD native round-trip |
| zprj | `ExportZprj()` | MD legacy round-trip |

Note: GLB/GLTF is **not** in the MD Python API. Use FBX + Blender CLI for GLB conversion.

---

## Phase 2 — Architecture

### Package Layout

```
cli_anything/marvelous/
├── __init__.py               # __version__ = "1.0.0"
├── __main__.py               # python -m cli_anything.marvelous entry
├── marvelous_cli.py          # Click root group + all command groups
├── core/
│   ├── garment.py            # FabricProperty, PatternPiece, Garment dataclasses
│   ├── project.py            # .zpac/.zprj parser (zipfile, no MD needed)
│   ├── session.py            # Atomic session CRUD (fcntl + tmpfile + os.replace)
│   └── library.py            # Local garment template library
├── utils/
│   ├── marvelous_backend.py  # subprocess wrapper, find_marvelous_binary, script runner
│   └── repl_skin.py          # prompt-toolkit REPL skin (marvelous accent: violet)
├── resources/
│   └── scripts/
│       ├── export.py.tpl     # MD export script template (${var} substitution)
│       ├── simulate.py.tpl   # MD simulation script template
│       └── add_fabric.py.tpl # MD fabric-assignment script template
└── tests/
    ├── TEST.md               # Test plan and inventory
    ├── test_core.py          # 57 unit tests (pure Python, no MD needed)
    └── test_full_e2e.py      # Smoke + live tests (MARVELOUS_E2E=1 gate)
```

### Command Hierarchy

```
cli-anything-marvelous [--json] [--verbose]
├── project
│   ├── info <file>           # Parse .zpac/.zprj metadata
│   └── new --name            # Create new session
├── garment
│   ├── list <file>           # List patterns + fabrics from project
│   └── add-fabric <file>     # Assign fabric via MD script (requires MD)
├── simulate
│   └── run <file>            # Run MD simulation for N frames (requires MD)
├── export
│   └── run <file>            # Export to obj/fbx/alembic/usd/zpac/zprj (requires MD)
├── library
│   ├── list                  # List locally imported garment templates
│   └── import <file>         # Import .zpac into local library
├── config
│   └── doctor                # Check MD binary + directory health
├── session
│   ├── status <id>           # Show session state
│   ├── save                  # Save current session
│   ├── list                  # List all sessions
│   └── delete <id>           # Delete session
└── repl                      # Interactive REPL (default when no subcommand)
```

### Data Flow

```
.zpac file
    └── zipfile.ZipFile
        ├── project.json  →  ProjectMeta (core/project.py)
        └── garment.json  →  Garment     (core/garment.py)

CLI command
    └── marvelous_cli.py
        ├── Pure operations  →  core/* (no MD needed)
        └── MD operations    →  marvelous_backend.py
                                    ├── load_script_template(name)   resources/scripts/*.tpl
                                    ├── render_script_template(vars) string.Template
                                    └── run_md_script(text)          subprocess ["MD", "--script", tmpfile]
```

### Session + Library Storage

```
~/.cli-anything-marvelous/
└── sessions/
    └── session-{uuid}.json   # Atomic writes via _locked_save_json

~/.cli_anything/marvelous/
└── library/
    ├── {slug}/
    │   ├── source.zpac        # Copied project file
    │   └── meta.json          # LibraryEntry metadata
    └── ...
```

### Atomic Write Pattern

All JSON writes use `_locked_save_json(path, payload)`:

1. `fcntl.flock(fd, LOCK_EX)` — acquire exclusive lock on lock file
2. `tempfile.mkstemp(dir=path.parent)` — write to temp file in same directory
3. `os.replace(tmp, path)` — atomic rename (POSIX guarantee: readers never see partial write)
4. `finally: fcntl.flock(fd, LOCK_UN)` — release lock

### Script Template Rendering

```python
from string import Template
t = Template(open("export.py.tpl").read())
script = t.substitute(project_path="/path/to.zpac", output_path="/out/dir", export_format="obj")
```

Missing variable → `KeyError` (surfaces to CLI as error, not silent failure).

### REPL Architecture

`repl` command uses `prompt_toolkit.PromptSession` with:
- History: `FileHistory("~/.cli-anything-marvelous/repl_history")`
- Accent: `"\033[38;5;171m"` (violet) via `ReplSkin("marvelous")`
- Dispatch: `main.main(args=parts, standalone_mode=False)` on each input line
- Exit: `exit`, `quit`, or `Ctrl-D`

### Exception Hierarchy

```
MarvelousError (base)
├── MarvelousNotFoundError    # MD binary not found
├── MarvelousScriptError      # MD ran but script failed (returncode + stderr)
└── MarvelousTimeoutError     # MD process exceeded timeout
```

All exceptions translate to `emit_error()` in `marvelous_cli.py`; `--json` mode
outputs `{"error": "...", "code": "..."}`.

### Test Strategy

**Unit tests** (`test_core.py`) — 57 tests, zero MD dependency:
- Synthetic `.zpac` via `zipfile.ZipFile(tmp_path / "x.zpac", "w")`
- Session/library dirs monkeypatched to `tmp_path`
- `glob.glob` monkeypatched to simulate missing MD binary

**E2E tests** (`test_full_e2e.py`) — gated on `MARVELOUS_E2E=1`:
- Smoke tests (8) run always — no MD needed
- Live tests (2) need real MD + optionally `MARVELOUS_TEST_ZPAC=/path/to.zpac`
