"""
MCP CLI - Command-Line Interface for MCP Management
====================================================

Provides CLI commands for managing MCP servers, tools, and catalogs.

Commands:
- start/stop/restart: Server lifecycle management
- status/health: Server health monitoring
- list: List servers and tools
- catalog: Generate and export tool catalogs
- config: Manage server configurations

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from mcp_servers.catalog_generator import ExportFormat
from mcp_servers.orchestrator import MCPOrchestrator
from mcp_servers.process_manager import ProcessStatus

console = Console()


# =============================================================================
# Helpers
# =============================================================================


def get_orchestrator(config: str | None) -> MCPOrchestrator:
    """Get orchestrator instance with optional config."""
    if config:
        return MCPOrchestrator(config_path=config)
    return MCPOrchestrator.get_instance()


def status_color(status: ProcessStatus | str) -> str:
    """Get color for status display."""
    if status == ProcessStatus.RUNNING or status == "remote":
        return "green"
    elif status == ProcessStatus.STOPPED:
        return "gray"
    elif status == ProcessStatus.FAILED:
        return "red"
    elif status == ProcessStatus.STARTING or status == ProcessStatus.STOPPING:
        return "yellow"
    else:
        return "blue"


def print_json(data: Any) -> None:
    """Pretty print JSON data."""
    console.print_json(json.dumps(data, indent=2))


# =============================================================================
# CLI Groups
# =============================================================================


@click.group()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.pass_context
def cli(ctx: click.Context, config: str | None) -> None:
    """DevSkyy MCP Management CLI."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = config


# =============================================================================
# Server Commands
# =============================================================================


@cli.group()
def server() -> None:
    """Manage MCP servers."""
    pass


@server.command()
@click.argument("server_id")
@click.pass_context
def start(ctx: click.Context, server_id: str) -> None:
    """Start an MCP server."""
    orchestrator = get_orchestrator(ctx.obj.get("config"))

    with console.status(f"[bold green]Starting server: {server_id}..."):
        try:
            success = asyncio.run(orchestrator.start_server(server_id))
            if success:
                console.print(f"[green]✓[/green] Server started: {server_id}")
            else:
                console.print(f"[red]✗[/red] Failed to start server: {server_id}")
                sys.exit(1)
        except Exception as e:
            console.print(f"[red]✗[/red] Error: {e}")
            sys.exit(1)


@server.command()
@click.argument("server_id")
@click.option("--force", "-f", is_flag=True, help="Force kill the server")
@click.pass_context
def stop(ctx: click.Context, server_id: str, force: bool) -> None:
    """Stop an MCP server."""
    orchestrator = get_orchestrator(ctx.obj.get("config"))

    with console.status(f"[bold yellow]Stopping server: {server_id}..."):
        try:
            success = asyncio.run(orchestrator.stop_server(server_id, force=force))
            if success:
                console.print(f"[green]✓[/green] Server stopped: {server_id}")
            else:
                console.print(f"[red]✗[/red] Failed to stop server: {server_id}")
                sys.exit(1)
        except Exception as e:
            console.print(f"[red]✗[/red] Error: {e}")
            sys.exit(1)


@server.command()
@click.argument("server_id")
@click.pass_context
def restart(ctx: click.Context, server_id: str) -> None:
    """Restart an MCP server."""
    orchestrator = get_orchestrator(ctx.obj.get("config"))

    with console.status(f"[bold blue]Restarting server: {server_id}..."):
        try:
            success = asyncio.run(orchestrator.restart_server(server_id))
            if success:
                console.print(f"[green]✓[/green] Server restarted: {server_id}")
            else:
                console.print(f"[red]✗[/red] Failed to restart server: {server_id}")
                sys.exit(1)
        except Exception as e:
            console.print(f"[red]✗[/red] Error: {e}")
            sys.exit(1)


@server.command()
@click.pass_context
def start_all(ctx: click.Context) -> None:
    """Start all enabled servers."""
    orchestrator = get_orchestrator(ctx.obj.get("config"))

    with console.status("[bold green]Starting all servers..."):
        try:
            results = asyncio.run(orchestrator.start_all_local())

            table = Table(title="Server Start Results")
            table.add_column("Server ID", style="cyan")
            table.add_column("Status", justify="center")

            for server_id, success in results.items():
                status = "[green]✓ Started[/green]" if success else "[red]✗ Failed[/red]"
                table.add_row(server_id, status)

            console.print(table)

        except Exception as e:
            console.print(f"[red]✗[/red] Error: {e}")
            sys.exit(1)


@server.command()
@click.pass_context
def stop_all(ctx: click.Context) -> None:
    """Stop all running servers."""
    orchestrator = get_orchestrator(ctx.obj.get("config"))

    with console.status("[bold yellow]Stopping all servers..."):
        try:
            results = asyncio.run(orchestrator.stop_all_local())

            table = Table(title="Server Stop Results")
            table.add_column("Server ID", style="cyan")
            table.add_column("Status", justify="center")

            for server_id, success in results.items():
                status = "[green]✓ Stopped[/green]" if success else "[red]✗ Failed[/red]"
                table.add_row(server_id, status)

            console.print(table)

        except Exception as e:
            console.print(f"[red]✗[/red] Error: {e}")
            sys.exit(1)


# =============================================================================
# Status & Monitoring
# =============================================================================


@cli.command()
@click.argument("server_id", required=False)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def status(ctx: click.Context, server_id: str | None, output_json: bool) -> None:
    """Get server status."""
    orchestrator = get_orchestrator(ctx.obj.get("config"))

    if server_id:
        # Single server status
        status_value = orchestrator.get_status(server_id)

        if output_json:
            print_json({"server_id": server_id, "status": str(status_value)})
        else:
            color = status_color(status_value)
            console.print(f"[{color}]{server_id}: {status_value}[/{color}]")
    else:
        # All servers status
        all_status = orchestrator.get_all_status()

        if output_json:
            print_json({sid: str(s) for sid, s in all_status.items()})
        else:
            table = Table(title="Server Status")
            table.add_column("Server ID", style="cyan")
            table.add_column("Status", justify="center")

            for sid, s in sorted(all_status.items()):
                color = status_color(s)
                table.add_row(sid, f"[{color}]{s}[/{color}]")

            console.print(table)


@cli.command()
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def health(ctx: click.Context, output_json: bool) -> None:
    """Check health of all servers."""
    orchestrator = get_orchestrator(ctx.obj.get("config"))

    with console.status("[bold blue]Checking server health..."):
        try:
            health_results = asyncio.run(orchestrator.health_check_all())

            if output_json:
                print_json(health_results)
            else:
                table = Table(title="Server Health")
                table.add_column("Server ID", style="cyan")
                table.add_column("Health", justify="center")

                for server_id, is_healthy in sorted(health_results.items()):
                    status = "[green]✓ Healthy[/green]" if is_healthy else "[red]✗ Unhealthy[/red]"
                    table.add_row(server_id, status)

                console.print(table)

        except Exception as e:
            console.print(f"[red]✗[/red] Error: {e}")
            sys.exit(1)


# =============================================================================
# Listing Commands
# =============================================================================


@cli.command()
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def list_servers(ctx: click.Context, output_json: bool) -> None:
    """List all registered servers."""
    orchestrator = get_orchestrator(ctx.obj.get("config"))

    servers = orchestrator.process_manager.list_servers()

    if output_json:
        print_json([s.model_dump() for s in servers])
    else:
        table = Table(title="Registered Servers")
        table.add_column("ID", style="cyan")
        table.add_column("Name")
        table.add_column("Port", justify="right")
        table.add_column("Tools", justify="right")
        table.add_column("Enabled", justify="center")

        for server in servers:
            enabled = "[green]✓[/green]" if server.enabled else "[red]✗[/red]"
            table.add_row(
                server.server_id,
                server.name,
                str(server.port) if server.port else "-",
                str(server.tool_count),
                enabled,
            )

        console.print(table)


@cli.command()
@click.option("--category", "-c", help="Filter by category")
@click.option("--search", "-s", help="Search by name or description")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def list_tools(
    ctx: click.Context,
    category: str | None,
    search: str | None,
    output_json: bool,
) -> None:
    """List all available tools."""
    orchestrator = get_orchestrator(ctx.obj.get("config"))

    # Build catalog first
    with console.status("[bold blue]Building tool catalog..."):
        asyncio.run(orchestrator.build_catalog())

    # Get tools
    tools = orchestrator.search_tools(search) if search else orchestrator.get_all_tools()

    # Filter by category if specified
    if category:
        from mcp_servers.catalog_generator import ToolCategory

        cat_enum = ToolCategory(category)
        tools = [t for t in tools if t.category == cat_enum]

    if output_json:
        print_json([t.model_dump() for t in tools])
    else:
        table = Table(title="Available Tools")
        table.add_column("Name", style="cyan")
        table.add_column("Category")
        table.add_column("Server")
        table.add_column("Severity", justify="center")
        table.add_column("Read-Only", justify="center")

        for tool in sorted(tools, key=lambda t: t.name):
            read_only = "[green]✓[/green]" if tool.read_only else ""
            table.add_row(
                tool.name,
                tool.category.value,
                tool.server_id,
                tool.severity.value,
                read_only,
            )

        console.print(table)
        console.print(f"\n[bold]Total tools:[/bold] {len(tools)}")


# =============================================================================
# Catalog Commands
# =============================================================================


@cli.group()
def catalog() -> None:
    """Manage tool catalogs."""
    pass


@catalog.command()
@click.pass_context
def build(ctx: click.Context) -> None:
    """Build unified tool catalog."""
    orchestrator = get_orchestrator(ctx.obj.get("config"))

    with console.status("[bold blue]Building tool catalog..."):
        try:
            asyncio.run(orchestrator.build_catalog())

            stats = orchestrator.tool_registry.get_statistics()

            panel = Panel(
                f"[bold]Total Tools:[/bold] {stats.total_tools}\n"
                f"[bold]Total Servers:[/bold] {stats.total_servers}\n"
                f"[bold]Conflicts:[/bold] {len(stats.conflicts)}\n"
                f"[bold]Deprecated:[/bold] {stats.deprecated_tools}",
                title="[bold green]Catalog Built Successfully[/bold green]",
                expand=False,
            )
            console.print(panel)

            if stats.conflicts:
                console.print("\n[yellow]⚠ Conflicts detected:[/yellow]")
                for conflict in stats.conflicts:
                    console.print(
                        f"  • {conflict.tool_name}: {conflict.conflict_type} "
                        f"(servers: {', '.join(conflict.server_ids)})"
                    )

        except Exception as e:
            console.print(f"[red]✗[/red] Error: {e}")
            sys.exit(1)


@catalog.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["openai", "anthropic", "mcp", "markdown", "json"]),
    required=True,
    help="Export format",
)
@click.option("--output", "-o", type=click.Path(), required=True, help="Output file path")
@click.pass_context
def export(ctx: click.Context, format: str, output: str) -> None:
    """Export catalog to file."""
    orchestrator = get_orchestrator(ctx.obj.get("config"))

    # Build catalog first
    with console.status("[bold blue]Building catalog..."):
        asyncio.run(orchestrator.build_catalog())

    # Export
    with console.status(f"[bold green]Exporting to {format}..."):
        try:
            export_format = ExportFormat(format)
            orchestrator.export_catalog_to_file(export_format, output)
            console.print(f"[green]✓[/green] Catalog exported to: {output}")

        except Exception as e:
            console.print(f"[red]✗[/red] Error: {e}")
            sys.exit(1)


@catalog.command()
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    required=True,
    help="Output directory for all formats",
)
@click.pass_context
def export_all(ctx: click.Context, output_dir: str) -> None:
    """Export catalog to all formats."""
    orchestrator = get_orchestrator(ctx.obj.get("config"))

    # Build catalog first
    with console.status("[bold blue]Building catalog..."):
        asyncio.run(orchestrator.build_catalog())

    # Export all
    with console.status("[bold green]Exporting all formats..."):
        try:
            exports = orchestrator.export_all_formats(output_dir)

            console.print(f"[green]✓[/green] Catalog exported to {len(exports)} formats:")
            for format, path in exports.items():
                console.print(f"  • {format.value}: {path}")

        except Exception as e:
            console.print(f"[red]✗[/red] Error: {e}")
            sys.exit(1)


@catalog.command()
@click.pass_context
def stats(ctx: click.Context) -> None:
    """Show catalog statistics."""
    orchestrator = get_orchestrator(ctx.obj.get("config"))

    # Build catalog first
    with console.status("[bold blue]Building catalog..."):
        asyncio.run(orchestrator.build_catalog())

    stats = orchestrator.tool_registry.get_statistics()

    # Main stats panel
    panel = Panel(
        f"[bold]Total Tools:[/bold] {stats.total_tools}\n"
        f"[bold]Total Servers:[/bold] {stats.total_servers}\n"
        f"[bold]Conflicts:[/bold] {len(stats.conflicts)}\n"
        f"[bold]Deprecated:[/bold] {stats.deprecated_tools}",
        title="[bold]Catalog Statistics[/bold]",
        expand=False,
    )
    console.print(panel)

    # Tools by category
    if stats.tools_by_category:
        console.print("\n[bold]Tools by Category:[/bold]")
        tree = Tree("Categories")
        for category, count in sorted(stats.tools_by_category.items()):
            tree.add(f"{category}: {count}")
        console.print(tree)

    # Tools by severity
    if stats.tools_by_severity:
        console.print("\n[bold]Tools by Severity:[/bold]")
        tree = Tree("Severity Levels")
        for severity, count in sorted(stats.tools_by_severity.items()):
            tree.add(f"{severity}: {count}")
        console.print(tree)


# =============================================================================
# Main Entry Point
# =============================================================================


def main() -> None:
    """CLI entry point."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Fatal error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
