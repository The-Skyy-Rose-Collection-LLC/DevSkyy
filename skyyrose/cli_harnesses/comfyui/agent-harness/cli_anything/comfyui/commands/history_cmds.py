"""history command group — completed prompt history."""

from __future__ import annotations

import json
import sys

import click
from cli_anything.comfyui.core.history import parse_history_response
from cli_anything.comfyui.core.secrets import resolve_secrets
from cli_anything.comfyui.utils.comfyui_backend import ComfyUIBackend, ComfyUIBackendError
from cli_anything.comfyui.utils.repl_skin import ReplSkin


@click.group("history")
def history() -> None:
    """Inspect and manage completed prompt history."""


@history.command("list")
@click.option("--host", envvar="COMFYUI_HOST", default=None, help="ComfyUI base URL")
@click.option("--token", envvar="COMFYUI_AUTH_TOKEN", default=None, help="Bearer token")
@click.option("--max-items", default=None, type=int, help="Limit number of history items")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def history_list(
    host: str | None, token: str | None, max_items: int | None, json_out: bool
) -> None:
    """List completed prompts from /history."""
    skin = ReplSkin(json_mode=json_out)
    secrets = resolve_secrets(host, token)
    backend = ComfyUIBackend(base_url=secrets.base_url, auth_headers=secrets.auth_headers())
    try:
        raw = backend.history(max_items=max_items)
    except ComfyUIBackendError as exc:
        if json_out:
            click.echo(json.dumps({"error": str(exc)}))
        else:
            skin.error(str(exc))
        sys.exit(1)

    items = parse_history_response(raw)
    if json_out:
        click.echo(json.dumps([i.to_dict() for i in items], indent=2))
        return

    skin.section(f"History ({len(items)} prompts)")
    if not items:
        skin.hint("No completed prompts.")
        return
    rows = [[i.prompt_id[:16], i.status, str(len(i.all_output_files()))] for i in items]
    skin.table(["Prompt ID", "Status", "Outputs"], rows)


@history.command("show")
@click.argument("prompt_id")
@click.option("--host", envvar="COMFYUI_HOST", default=None, help="ComfyUI base URL")
@click.option("--token", envvar="COMFYUI_AUTH_TOKEN", default=None, help="Bearer token")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def history_show(prompt_id: str, host: str | None, token: str | None, json_out: bool) -> None:
    """Show details for a single completed prompt from /history/{prompt_id}."""
    skin = ReplSkin(json_mode=json_out)
    secrets = resolve_secrets(host, token)
    backend = ComfyUIBackend(base_url=secrets.base_url, auth_headers=secrets.auth_headers())
    try:
        raw = backend.history_prompt(prompt_id)
    except ComfyUIBackendError as exc:
        if json_out:
            click.echo(json.dumps({"error": str(exc)}))
        else:
            skin.error(str(exc))
        sys.exit(1)

    if json_out:
        click.echo(json.dumps(raw, indent=2))
        return

    items = parse_history_response(raw)
    if not items:
        skin.hint(f"No history found for prompt_id: {prompt_id}")
        return

    item = items[0]
    skin.section(f"Prompt: {item.prompt_id}")
    skin.info(f"Status: {item.status}")
    files = item.all_output_files()
    if files:
        skin.section("Output Files")
        rows = [[f.filename, f.subfolder, f.file_type] for f in files]
        skin.table(["Filename", "Subfolder", "Type"], rows)
    if item.node_errors:
        skin.warning(f"Node errors: {json.dumps(item.node_errors, indent=2)}")


@history.command("extract-outputs")
@click.argument("prompt_id")
@click.option("--host", envvar="COMFYUI_HOST", default=None, help="ComfyUI base URL")
@click.option("--token", envvar="COMFYUI_AUTH_TOKEN", default=None, help="Bearer token")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def extract_outputs(prompt_id: str, host: str | None, token: str | None, json_out: bool) -> None:
    """Extract all output file paths for a completed prompt."""
    skin = ReplSkin(json_mode=json_out)
    secrets = resolve_secrets(host, token)
    backend = ComfyUIBackend(base_url=secrets.base_url, auth_headers=secrets.auth_headers())
    try:
        raw = backend.history_prompt(prompt_id)
    except ComfyUIBackendError as exc:
        if json_out:
            click.echo(json.dumps({"error": str(exc)}))
        else:
            skin.error(str(exc))
        sys.exit(1)

    items = parse_history_response(raw)
    if not items:
        if json_out:
            click.echo(json.dumps([]))
        else:
            skin.hint("No outputs found.")
        return

    files = items[0].all_output_files()
    if json_out:
        click.echo(json.dumps([f.to_dict() for f in files], indent=2))
        return

    for f in files:
        click.echo(f.filename)


@history.command("clear")
@click.option("--host", envvar="COMFYUI_HOST", default=None, help="ComfyUI base URL")
@click.option("--token", envvar="COMFYUI_AUTH_TOKEN", default=None, help="Bearer token")
@click.option("--prompt-id", default=None, help="Clear a single prompt (omit to clear all)")
@click.option("--confirm", is_flag=True, help="Required to execute destructive clear")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def history_clear(
    host: str | None,
    token: str | None,
    prompt_id: str | None,
    confirm: bool,
    json_out: bool,
) -> None:
    """Clear history (all or a single prompt).  Requires --confirm."""
    skin = ReplSkin(json_mode=json_out)
    if not confirm:
        if json_out:
            click.echo(json.dumps({"error": "Pass --confirm to execute history clear"}))
        else:
            skin.warning("Destructive operation. Pass --confirm to proceed.")
        sys.exit(1)

    secrets = resolve_secrets(host, token)
    backend = ComfyUIBackend(base_url=secrets.base_url, auth_headers=secrets.auth_headers())
    try:
        result = backend.clear_history(prompt_id=prompt_id)
    except ComfyUIBackendError as exc:
        if json_out:
            click.echo(json.dumps({"error": str(exc)}))
        else:
            skin.error(str(exc))
        sys.exit(1)

    if json_out:
        click.echo(json.dumps(result, indent=2))
    else:
        skin.success("History cleared.")
