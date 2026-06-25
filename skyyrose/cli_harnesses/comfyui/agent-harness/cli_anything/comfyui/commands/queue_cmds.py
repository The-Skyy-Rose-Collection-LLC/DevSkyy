"""queue command group — submit, list, interrupt, clear."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from cli_anything.comfyui.core.queue import build_prompt_payload, parse_queue_response
from cli_anything.comfyui.core.secrets import resolve_secrets
from cli_anything.comfyui.core.workflow import load_workflow
from cli_anything.comfyui.utils.comfyui_backend import ComfyUIBackend, ComfyUIBackendError
from cli_anything.comfyui.utils.repl_skin import ReplSkin


@click.group("queue")
def queue() -> None:
    """Submit and manage the ComfyUI execution queue."""


@queue.command("list")
@click.option("--host", envvar="COMFYUI_HOST", default=None, help="ComfyUI base URL")
@click.option("--token", envvar="COMFYUI_AUTH_TOKEN", default=None, help="Bearer token")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def queue_list(host: str | None, token: str | None, json_out: bool) -> None:
    """Show running and pending queue items from /queue."""
    skin = ReplSkin(json_mode=json_out)
    secrets = resolve_secrets(host, token)
    backend = ComfyUIBackend(base_url=secrets.base_url, auth_headers=secrets.auth_headers())
    try:
        raw = backend.queue()
    except ComfyUIBackendError as exc:
        if json_out:
            click.echo(json.dumps({"error": str(exc)}))
        else:
            skin.error(str(exc))
        sys.exit(1)

    parsed = parse_queue_response(raw)
    if json_out:
        click.echo(
            json.dumps(
                {
                    "running": [i.to_dict() for i in parsed["running"]],
                    "pending": [i.to_dict() for i in parsed["pending"]],
                },
                indent=2,
            )
        )
        return

    skin.section("Queue")
    running = parsed["running"]
    pending = parsed["pending"]
    skin.info(f"Running: {len(running)}  Pending: {len(pending)}")

    if running:
        skin.section("Running")
        rows = [[i.prompt_id[:16], str(i.number), i.status.value] for i in running]
        skin.table(["Prompt ID", "#", "Status"], rows)

    if pending:
        skin.section("Pending")
        rows = [[i.prompt_id[:16], str(i.number), i.status.value] for i in pending]
        skin.table(["Prompt ID", "#", "Status"], rows)


@queue.command("submit")
@click.argument("workflow_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--host", envvar="COMFYUI_HOST", default=None, help="ComfyUI base URL")
@click.option("--token", envvar="COMFYUI_AUTH_TOKEN", default=None, help="Bearer token")
@click.option("--client-id", default=None, help="Client ID (UUID4 generated if omitted)")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def queue_submit(
    workflow_file: str,
    host: str | None,
    token: str | None,
    client_id: str | None,
    json_out: bool,
) -> None:
    """Submit WORKFLOW_FILE to the ComfyUI queue via POST /prompt."""
    skin = ReplSkin(json_mode=json_out)
    try:
        wf = load_workflow(Path(workflow_file))
    except (FileNotFoundError, ValueError) as exc:
        if json_out:
            click.echo(json.dumps({"error": str(exc)}))
        else:
            skin.error(str(exc))
        sys.exit(1)

    errors = wf.validate()
    if errors:
        if json_out:
            click.echo(json.dumps({"error": "Workflow validation failed", "details": errors}))
        else:
            skin.error("Workflow validation failed:")
            for e in errors:
                skin.hint(f"  {e}")
        sys.exit(1)

    payload = build_prompt_payload(wf.to_dict(), client_id=client_id)
    secrets = resolve_secrets(host, token)
    backend = ComfyUIBackend(base_url=secrets.base_url, auth_headers=secrets.auth_headers())
    try:
        result = backend.submit_prompt(payload)
    except ComfyUIBackendError as exc:
        if json_out:
            click.echo(json.dumps({"error": str(exc)}))
        else:
            skin.error(str(exc))
        sys.exit(1)

    if json_out:
        click.echo(json.dumps(result, indent=2))
        return

    prompt_id = result.get("prompt_id", "unknown")
    skin.success(f"Submitted. prompt_id: {prompt_id}")
    if result.get("node_errors"):
        skin.warning(f"Node errors: {result['node_errors']}")


@queue.command("interrupt")
@click.option("--host", envvar="COMFYUI_HOST", default=None, help="ComfyUI base URL")
@click.option("--token", envvar="COMFYUI_AUTH_TOKEN", default=None, help="Bearer token")
@click.option("--confirm", is_flag=True, help="Required to interrupt the running prompt")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def queue_interrupt(host: str | None, token: str | None, confirm: bool, json_out: bool) -> None:
    """Interrupt the currently running prompt (POST /interrupt).  Requires --confirm."""
    skin = ReplSkin(json_mode=json_out)
    if not confirm:
        if json_out:
            click.echo(json.dumps({"error": "Pass --confirm to interrupt"}))
        else:
            skin.warning("Destructive operation. Pass --confirm to interrupt.")
        sys.exit(1)

    secrets = resolve_secrets(host, token)
    backend = ComfyUIBackend(base_url=secrets.base_url, auth_headers=secrets.auth_headers())
    try:
        result = backend.interrupt()
    except ComfyUIBackendError as exc:
        if json_out:
            click.echo(json.dumps({"error": str(exc)}))
        else:
            skin.error(str(exc))
        sys.exit(1)

    if json_out:
        click.echo(json.dumps(result, indent=2))
    else:
        skin.success("Interrupt signal sent.")


@queue.command("clear")
@click.option("--host", envvar="COMFYUI_HOST", default=None, help="ComfyUI base URL")
@click.option("--token", envvar="COMFYUI_AUTH_TOKEN", default=None, help="Bearer token")
@click.option("--confirm", is_flag=True, help="Required to clear the pending queue")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def queue_clear(host: str | None, token: str | None, confirm: bool, json_out: bool) -> None:
    """Clear the pending queue (POST /queue + clear=true).  Requires --confirm."""
    skin = ReplSkin(json_mode=json_out)
    if not confirm:
        if json_out:
            click.echo(json.dumps({"error": "Pass --confirm to clear the queue"}))
        else:
            skin.warning("Destructive operation. Pass --confirm to clear.")
        sys.exit(1)

    secrets = resolve_secrets(host, token)
    backend = ComfyUIBackend(base_url=secrets.base_url, auth_headers=secrets.auth_headers())
    try:
        result = backend.queue_clear()
    except ComfyUIBackendError as exc:
        if json_out:
            click.echo(json.dumps({"error": str(exc)}))
        else:
            skin.error(str(exc))
        sys.exit(1)

    if json_out:
        click.echo(json.dumps(result, indent=2))
    else:
        skin.success("Pending queue cleared.")
