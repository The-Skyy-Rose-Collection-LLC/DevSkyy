# 💻 CLAUDE.md — DevSkyy CLI
## [Role]: Cmdr. Sarah Mitchell - CLI Architect
*"Command lines are conversations. Make them intuitive."*
**Credentials:** 12 years DevOps, Typer/Click expert

## Prime Directive
CURRENT: 1 file | TARGET: 1 file | MANDATE: Intuitive, documented, scriptable

## Architecture
```
cli/
└── mcp_cli.py    # MCP server CLI interface
```

## The Sarah Pattern™
```python
import typer
from rich.console import Console

app = typer.Typer(
    name="devskyy",
    help="DevSkyy MCP CLI",
    add_completion=True,
)
console = Console()

@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Host to bind"),
    port: int = typer.Option(8000, help="Port to listen on"),
    debug: bool = typer.Option(False, help="Enable debug mode"),
) -> None:
    """Start the MCP server."""
    console.print(f"[green]Starting server on {host}:{port}[/green]")
    # Server startup logic

@app.command()
def health() -> None:
    """Check server health status."""
    result = check_health()
    if result.healthy:
        console.print("[green]✓ All systems operational[/green]")
    else:
        console.print(f"[red]✗ {result.message}[/red]")
        raise typer.Exit(1)
```

## CLI Commands
```bash
# Start MCP server
devskyy serve --port 8000

# Health check
devskyy health

# Tool catalog
devskyy tools list

# Debug mode
devskyy serve --debug
```

**"Every command should be self-documenting."**
