# cli-anything-marvelous

CLI harness for [Marvelous Designer](https://marvelousdesigner.com/) — the 3D garment
tailoring application by CLO Virtual Fashion.

Wraps the MD scripting API in a composable CLI with JSON output, session management,
a local garment library, and an interactive REPL.

---

## Installation

```bash
pip install -e ".[dev]"
```

**Hard dependency:** Marvelous Designer must be installed for `simulate run`,
`export run`, and `garment add-fabric` commands. All other commands work without MD.

---

## Quick Start

```bash
# Inspect a project file (no MD needed)
cli-anything-marvelous project info shirt.zpac
cli-anything-marvelous --json project info shirt.zpac

# Export to OBJ (requires MD)
cli-anything-marvelous export run shirt.zpac --format obj --output ./exports/shirt

# Simulate 30 frames and save (requires MD)
cli-anything-marvelous simulate run shirt.zpac --frames 30 --output ./renders/shirt_sim.zpac

# Assign a fabric texture (requires MD)
cli-anything-marvelous garment add-fabric shirt.zpac \
  --pattern "Front Bodice" --fabric "Cotton Twill" --texture ./textures/cotton.jpg \
  --output ./modified_shirt.zpac

# Import into local library
cli-anything-marvelous library import shirt.zpac --slug my-shirt --name "Sample Shirt"

# Interactive REPL
cli-anything-marvelous
```

---

## Commands

### `project info <file>`
Parse `.zpac` or `.zprj` metadata without launching MD.

```
Options:
  --json  Output as JSON
```

### `project new`
Create a new session with optional project association.

### `garment list <file>`
List pattern pieces and fabric assignments from a project file.

### `garment add-fabric <file>`
Assign a fabric texture to a pattern piece via MD script injection.

```
Options:
  --pattern TEXT   Pattern piece name (required)
  --fabric TEXT    Fabric display name (required)
  --texture PATH   Texture image path (required)
  --output PATH    Output .zpac path (required)
  --timeout INT    MD timeout in seconds (default: 300)
```

### `simulate run <file>`
Run MD cloth simulation for N frames.

```
Options:
  --frames INT   Frame count (default: 30)
  --output PATH  Output .zpac path (required)
  --timeout INT  MD timeout in seconds (default: 600)
```

### `export run <file>`
Export garment to a standard format.

```
Options:
  --format [obj|fbx|alembic|usd|zpac|zprj]  Export format (default: obj)
  --output PATH                              Output path (required)
  --timeout INT                              MD timeout in seconds (default: 300)
```

### `library list`
List imported garment templates.

### `library import <file>`
Import a `.zpac` file into the local template library.

```
Options:
  --slug TEXT    Library identifier (required)
  --name TEXT    Display name (required)
  --description TEXT
  --tags TEXT    Comma-separated tags
```

### `config doctor`
Check MD binary discovery and storage directory health.

### `session status <id>`
Show state of a saved session.

### `session save`
Save current session state.

### `session list`
List all saved sessions.

### `session delete <id>`
Delete a session by ID.

### `repl`
Interactive REPL (default command when invoked with no arguments).

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `MARVELOUS_DESIGNER_BIN` | Override path to MD binary |
| `MARVELOUS_E2E` | Set to `1` to enable live E2E tests |
| `MARVELOUS_TEST_ZPAC` | Path to real `.zpac` for E2E live tests |
| `CLI_ANYTHING_FORCE_INSTALLED` | Set to `1` to require installed binary in tests |

---

## Storage Locations

| Path | Contents |
|------|----------|
| `~/.cli-anything-marvelous/sessions/` | Saved sessions (JSON, atomic writes) |
| `~/.cli_anything/marvelous/library/` | Imported garment templates |
| `~/.cli-anything-marvelous/repl_history` | REPL command history |

---

## Testing

```bash
# Unit tests only (no MD required)
pytest cli_anything/marvelous/tests/test_core.py -v

# All tests including CLI smoke tests
pytest cli_anything/marvelous/tests/ -v

# With coverage
pytest cli_anything/marvelous/tests/ --cov=cli_anything.marvelous --cov-report=term-missing

# Full live run (requires MD installed + real .zpac)
MARVELOUS_E2E=1 MARVELOUS_TEST_ZPAC=/path/to/shirt.zpac \
  pytest cli_anything/marvelous/tests/ -v
```

---

## Architecture Notes

Script templates in `resources/scripts/` are injected into MD at runtime using
Python's `string.Template` with `${var}` substitution. The templates use the real
MD Python API (`import_api`, `export_api`, `utility_api`, `fabric_api`) and will
execute correctly once the `--script` invocation path is confirmed.

**Known limitation:** MD's `--script` flag is not officially documented as of MD 12.
The invocation `"Marvelous Designer" --script /tmp/script.py` is based on user
workflow reports. If the actual syntax differs, update `run_md_script()` in
`cli_anything/marvelous/utils/marvelous_backend.py`.

See `MARVELOUS.md` for full API research and architectural decision log.
