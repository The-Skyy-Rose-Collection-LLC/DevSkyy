# cli/ — Stand-alone operator command-line tools

Two Click-based command-line apps that operate against DevSkyy infrastructure without booting the FastAPI app. Designed for hands-on operators: starting/stopping MCP servers, generating tool catalogs, and enhancing prompts through the Claude API. Neither tool imports `main_enterprise.py` or `agents/` — they are intentionally decoupled from the runtime.

## Key files

- `__init__.py` — Package init. Re-exports `prompt_enhance_cli`.
- `mcp_cli.py` — Click group `cli` with two subgroups: `server` (commands `start`, `stop`, `restart`, `start_all`, `stop_all`, `status`, `health`, `list_servers`, `list_tools`) and `catalog` (commands `build`, `export`, `export_all`, `stats`). Entry point `main()`. Imports only from `mcp_servers.orchestrator`, `mcp_servers.catalog_generator`, `mcp_servers.process_manager`.
- `prompt_enhance.py` — Stand-alone Click command with prompt analysis, technique selection, context scanning, and Claude API enhancement. Entry point `cli()`. Lazy-imports `anthropic` inside command bodies so `--help` does not require the package.

## Conventions

- `prompt-enhance` is the only registered console script (`pyproject.toml:319` — `prompt-enhance = "cli.prompt_enhance:cli"`). Invoke `mcp_cli.py` via `python -m cli.mcp_cli` until a console-script entry is added.
- CLIs are stand-alone operator tools. Do not import from `agents/` or `main_enterprise.py` — these commands run without the FastAPI app.
- `mcp_cli.py` only imports from `mcp_servers.*`. Cross-cutting machinery belongs in `mcp_servers/`; the CLI stays a thin shell over it.
- Lazy-import expensive dependencies (`anthropic`, large vendor SDKs) inside command bodies. `--help` should resolve in milliseconds without network or heavy import cost.
- Commands that depend on a running server (e.g., `health`) name that dependency explicitly; commands that don't (e.g., `catalog build`) must run offline.

## Don't

- Don't add cross-cutting CLI machinery here (process pooling, catalog generation, MCP orchestration). Those belong in `mcp_servers/`; the CLI is the thin shell.
- Don't import the FastAPI app (`main_enterprise:main`) from these commands. Booting the API just to run a CLI command burns cold-start cost for no reason.
- Don't make `--help` slow. Lazy-import; never reach for a network at command-construction time.
- Don't shadow the registered console script name (`prompt-enhance`) when adding new commands.

## Related

- `mcp_servers/` — CLI's primary backend (orchestrator, catalog generator, process manager)
- `pyproject.toml:319` — console_scripts table where `prompt-enhance` is registered
- No Makefile target — invoke `python -m cli.mcp_cli` or the installed `prompt-enhance` script
