"""system command group — server stats and embeddings."""

from __future__ import annotations

import json
import sys

import click
from cli_anything.comfyui.core.secrets import resolve_secrets
from cli_anything.comfyui.utils.comfyui_backend import ComfyUIBackend, ComfyUIBackendError
from cli_anything.comfyui.utils.repl_skin import ReplSkin


@click.group("system")
def system() -> None:
    """Server system information."""


@system.command("stats")
@click.option("--host", envvar="COMFYUI_HOST", default=None, help="ComfyUI base URL")
@click.option("--token", envvar="COMFYUI_AUTH_TOKEN", default=None, help="Bearer token")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def stats(host: str | None, token: str | None, json_out: bool) -> None:
    """Show CPU, RAM, and VRAM usage from /system_stats."""
    skin = ReplSkin(json_mode=json_out)
    secrets = resolve_secrets(host, token)
    backend = ComfyUIBackend(base_url=secrets.base_url, auth_headers=secrets.auth_headers())
    try:
        data = backend.system_stats()
    except ComfyUIBackendError as exc:
        if json_out:
            click.echo(json.dumps({"error": str(exc)}))
        else:
            skin.error(str(exc))
        sys.exit(1)

    if json_out:
        click.echo(json.dumps(data, indent=2))
        return

    skin.section("System Stats")
    # Flatten nested dicts for display
    rows: list[list[str]] = []
    for section_key, section_val in data.items():
        if isinstance(section_val, dict):
            for k, v in section_val.items():
                rows.append([f"{section_key}.{k}", str(v)])
        else:
            rows.append([section_key, str(section_val)])
    skin.table(["Key", "Value"], rows)


@system.command("embeddings")
@click.option("--host", envvar="COMFYUI_HOST", default=None, help="ComfyUI base URL")
@click.option("--token", envvar="COMFYUI_AUTH_TOKEN", default=None, help="Bearer token")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def embeddings_cmd(host: str | None, token: str | None, json_out: bool) -> None:
    """List available embedding models from /embeddings."""
    skin = ReplSkin(json_mode=json_out)
    secrets = resolve_secrets(host, token)
    backend = ComfyUIBackend(base_url=secrets.base_url, auth_headers=secrets.auth_headers())
    try:
        data = backend.embeddings()
    except ComfyUIBackendError as exc:
        if json_out:
            click.echo(json.dumps({"error": str(exc)}))
        else:
            skin.error(str(exc))
        sys.exit(1)

    if json_out:
        click.echo(json.dumps(data, indent=2))
        return

    skin.section("Embeddings")
    if not data:
        skin.hint("No embeddings found.")
        return
    for name in sorted(data):
        click.echo(f"  {name}")
