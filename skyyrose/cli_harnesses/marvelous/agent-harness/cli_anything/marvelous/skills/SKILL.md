---
name: cli-anything-marvelous
description: >
  Operate the cli-anything-marvelous harness for Marvelous Designer.
  Use when the user wants to parse .zpac/.zprj files, run simulations,
  export garments, manage sessions, or interact with the local garment library.
---

# cli-anything-marvelous Skill

## When to Use

- User wants to inspect a `.zpac` or `.zprj` project file
- User wants to simulate, export, or add fabrics via Marvelous Designer
- User wants to manage garment sessions or the local template library
- User wants to run the interactive REPL

## Package Location

```
/Users/theceo/DevSkyy/vendor/cli-anything/marvelous/agent-harness/
```

Key files:
- `cli_anything/marvelous/marvelous_cli.py` — all Click commands
- `cli_anything/marvelous/core/` — project, garment, session, library modules
- `cli_anything/marvelous/utils/marvelous_backend.py` — subprocess + script runner
- `cli_anything/marvelous/resources/scripts/` — MD script templates

## Command Reference

```bash
cli-anything-marvelous project info <file.zpac>          # Parse metadata
cli-anything-marvelous --json project info <file.zpac>   # JSON output
cli-anything-marvelous export run <file.zpac> --format obj --output ./out
cli-anything-marvelous simulate run <file.zpac> --frames 30 --output ./sim.zpac
cli-anything-marvelous garment add-fabric <file.zpac> \
  --pattern "Front Bodice" --fabric "Cotton" --texture ./t.jpg --output ./out.zpac
cli-anything-marvelous library import <file.zpac> --slug my-shirt --name "My Shirt"
cli-anything-marvelous library list
cli-anything-marvelous session save --project /path/to.zpac --garment "Shirt"
cli-anything-marvelous session list
cli-anything-marvelous session status <session-id>
cli-anything-marvelous session delete <session-id>
cli-anything-marvelous config doctor
cli-anything-marvelous              # launches REPL
```

## Commands That Need MD Installed

`export run`, `simulate run`, `garment add-fabric` — all require Marvelous Designer.

All other commands work without MD.

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `MARVELOUS_DESIGNER_BIN` | Override MD binary path |
| `MARVELOUS_E2E=1` | Enable live E2E tests |
| `MARVELOUS_TEST_ZPAC` | Real .zpac path for live tests |

## Running Tests

```bash
cd /Users/theceo/DevSkyy/vendor/cli-anything/marvelous/agent-harness
pytest cli_anything/marvelous/tests/test_core.py -v           # unit only
pytest cli_anything/marvelous/tests/ -v                       # + smoke E2E
pytest cli_anything/marvelous/tests/ --cov=cli_anything.marvelous
```

## Python API (for programmatic use)

```python
from cli_anything.marvelous.core.project import read_project_meta
from cli_anything.marvelous.core.garment import Garment
from cli_anything.marvelous.core.session import new_session, save_session, load_session
from cli_anything.marvelous.core.library import import_project, list_library
from cli_anything.marvelous.utils.marvelous_backend import (
    find_marvelous_binary,
    load_script_template,
    render_script_template,
    run_md_script,
)

# Parse a .zpac without MD
meta = read_project_meta(Path("shirt.zpac"))
print(meta.name, meta.pattern_count, meta.fabric_count)

# Run a script (requires MD)
binary = find_marvelous_binary()
tpl = load_script_template("export")
script = render_script_template(tpl, {
    "project_path": "/path/to/shirt.zpac",
    "output_path": "/out/shirt",
    "export_format": "obj",
})
run_md_script(script, binary=binary)
```

## Exceptions

```python
from cli_anything.marvelous.utils.marvelous_backend import (
    MarvelousNotFoundError,   # MD binary not on PATH / not installed
    MarvelousScriptError,     # MD ran but script exited non-zero
    MarvelousTimeoutError,    # MD exceeded timeout
)
```

## Key Design Decisions

- `.zpac`/`.zprj` parsing uses stdlib `zipfile` — no MD required
- Session writes are atomic (`fcntl.flock` + `tempfile` + `os.replace`)
- Script templates use `string.Template` with `${var}` — no Jinja2 dependency
- REPL dispatches back into Click via `main.main(args=parts, standalone_mode=False)`
- Export formats: obj, fbx, alembic, usd, zpac, zprj (GLB is NOT in MD API)
- `--script` invocation is unconfirmed in MD 12 official docs; update `run_md_script()` if syntax differs
