"""nodes command group — node registry (object_info)."""

from __future__ import annotations

import json
import sys

import click
from cli_anything.comfyui.core.secrets import resolve_secrets
from cli_anything.comfyui.utils.comfyui_backend import ComfyUIBackend, ComfyUIBackendError
from cli_anything.comfyui.utils.repl_skin import ReplSkin


@click.group("nodes")
def nodes() -> None:
    """Browse the ComfyUI node registry."""


@nodes.command("list")
@click.option("--host", envvar="COMFYUI_HOST", default=None, help="ComfyUI base URL")
@click.option("--token", envvar="COMFYUI_AUTH_TOKEN", default=None, help="Bearer token")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
@click.option("--filter", "filter_str", default="", help="Case-insensitive substring filter")
def nodes_list(host: str | None, token: str | None, json_out: bool, filter_str: str) -> None:
    """List all available node class types from /object_info."""
    skin = ReplSkin(json_mode=json_out)
    secrets = resolve_secrets(host, token)
    backend = ComfyUIBackend(base_url=secrets.base_url, auth_headers=secrets.auth_headers())
    try:
        data = backend.object_info()
    except ComfyUIBackendError as exc:
        if json_out:
            click.echo(json.dumps({"error": str(exc)}))
        else:
            skin.error(str(exc))
        sys.exit(1)

    names = sorted(data.keys())
    if filter_str:
        names = [n for n in names if filter_str.lower() in n.lower()]

    if json_out:
        click.echo(json.dumps(names, indent=2))
        return

    skin.section(f"Nodes ({len(names)})")
    if not names:
        skin.hint("No nodes match the filter.")
        return
    for name in names:
        click.echo(f"  {name}")


@nodes.command("info")
@click.argument("node_class")
@click.option("--host", envvar="COMFYUI_HOST", default=None, help="ComfyUI base URL")
@click.option("--token", envvar="COMFYUI_AUTH_TOKEN", default=None, help="Bearer token")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def node_info(node_class: str, host: str | None, token: str | None, json_out: bool) -> None:
    """Show full spec for a single node class from /object_info/{node_class}."""
    skin = ReplSkin(json_mode=json_out)
    secrets = resolve_secrets(host, token)
    backend = ComfyUIBackend(base_url=secrets.base_url, auth_headers=secrets.auth_headers())
    try:
        data = backend.object_info_node(node_class)
    except ComfyUIBackendError as exc:
        if json_out:
            click.echo(json.dumps({"error": str(exc)}))
        else:
            skin.error(str(exc))
        sys.exit(1)

    if json_out:
        click.echo(json.dumps(data, indent=2))
        return

    skin.section(f"Node: {node_class}")
    node_spec = data.get(node_class, data)
    if isinstance(node_spec, dict):
        click.echo(json.dumps(node_spec, indent=2))
    else:
        click.echo(str(node_spec))
