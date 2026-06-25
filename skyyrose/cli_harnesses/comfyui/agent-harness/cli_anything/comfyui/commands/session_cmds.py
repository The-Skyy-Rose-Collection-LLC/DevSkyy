"""session command group — save, load, list, delete sessions."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from cli_anything.comfyui.core.secrets import resolve_secrets
from cli_anything.comfyui.core.session import (
    Session,
    delete_session,
    list_sessions,
    load_session,
    save_session,
)
from cli_anything.comfyui.utils.repl_skin import ReplSkin


@click.group("session")
def session() -> None:
    """Manage persistent CLI sessions."""


@session.command("new")
@click.option("--host", envvar="COMFYUI_HOST", default=None, help="ComfyUI base URL")
@click.option("--token", envvar="COMFYUI_AUTH_TOKEN", default=None, help="Bearer token")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def session_new(host: str | None, token: str | None, json_out: bool) -> None:
    """Create and persist a new session."""
    skin = ReplSkin(json_mode=json_out)
    secrets = resolve_secrets(host, token)
    sess = Session(host=secrets.base_url)
    path = save_session(sess)

    if json_out:
        click.echo(json.dumps({"session_id": sess.session_id, "path": str(path)}))
    else:
        skin.success(f"Session created: {sess.session_id}")
        skin.hint(f"Saved to: {path}")


@session.command("list")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def session_list(json_out: bool) -> None:
    """List all saved sessions."""
    skin = ReplSkin(json_mode=json_out)
    sessions = list_sessions()

    if json_out:
        click.echo(json.dumps(sessions, indent=2))
        return

    skin.section(f"Sessions ({len(sessions)})")
    if not sessions:
        skin.hint("No sessions found.")
        return
    rows = [[s["session_id"][:16], s["host"], s["updated_at"][:19]] for s in sessions]
    skin.table(["Session ID", "Host", "Updated"], rows)


@session.command("show")
@click.argument("session_id")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def session_show(session_id: str, json_out: bool) -> None:
    """Show details of a session including history."""
    skin = ReplSkin(json_mode=json_out)
    try:
        sess = load_session(session_id)
    except FileNotFoundError as exc:
        if json_out:
            click.echo(json.dumps({"error": str(exc)}))
        else:
            skin.error(str(exc))
        sys.exit(1)

    if json_out:
        click.echo(json.dumps(sess.to_dict(), indent=2))
        return

    skin.section(f"Session: {sess.session_id}")
    skin.info(f"Host: {sess.host}")
    skin.info(f"Created: {sess.created_at}")
    skin.info(f"Updated: {sess.updated_at}")
    skin.info(f"History entries: {len(sess.history)}")


@session.command("delete")
@click.argument("session_id")
@click.option("--confirm", is_flag=True, help="Required to delete a session")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def session_delete(session_id: str, confirm: bool, json_out: bool) -> None:
    """Delete a saved session.  Requires --confirm."""
    skin = ReplSkin(json_mode=json_out)
    if not confirm:
        if json_out:
            click.echo(json.dumps({"error": "Pass --confirm to delete session"}))
        else:
            skin.warning("Pass --confirm to delete.")
        sys.exit(1)

    deleted = delete_session(session_id)
    if json_out:
        click.echo(json.dumps({"deleted": deleted, "session_id": session_id}))
    elif deleted:
        skin.success(f"Session deleted: {session_id}")
    else:
        skin.warning(f"Session not found: {session_id}")
