# DevSkyy CLI

> Intuitive, documented, scriptable | 1 file

## Architecture
```
cli/
└── mcp_cli.py    # MCP server CLI
```

## Commands
```bash
devskyy serve --port 8000    # Start server
devskyy health               # Health check
devskyy tools list           # List tools
devskyy serve --debug        # Debug mode
```

## Pattern
```python
app = typer.Typer(name="devskyy", help="DevSkyy MCP CLI")

@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000, debug: bool = False):
    console.print(f"[green]Starting server on {host}:{port}[/green]")

@app.command()
def health():
    result = check_health()
    console.print("[green]✓ All systems operational[/green]" if result.healthy else f"[red]✗ {result.message}[/red]")
```

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change

## USE THESE TOOLS
| Task | Tool |
|------|------|
| Health check | **MCP**: `health_check` |
| Tool listing | **MCP**: `tool_catalog` |

**"Every command should be self-documenting."**
