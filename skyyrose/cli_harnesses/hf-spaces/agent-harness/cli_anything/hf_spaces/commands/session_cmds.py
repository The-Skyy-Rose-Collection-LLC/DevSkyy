"""session command group — list, show, delete."""

from __future__ import annotations

import json
import sys
import time

import click
from cli_anything.hf_spaces.core import session as session_store

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group("session", context_settings=CONTEXT_SETTINGS)
def session() -> None:
    """Session management — list, show, delete."""


@session.command("list")
@click.pass_context
def session_list(ctx: click.Context) -> None:
    """List all saved sessions."""
    state = ctx.obj
    sessions = session_store.list_sessions()

    if state.json_output:
        click.echo(
            json.dumps(
                {
                    "ok": True,
                    "sessions": [
                        {
                            "session_id": s.session_id,
                            "space_id": s.space_id,
                            "updated_at": s.updated_at,
                            "history_count": len(s.history),
                        }
                        for s in sessions
                    ],
                },
                indent=2,
            )
        )
        return

    if not sessions:
        click.echo("  No sessions found.")
        return

    from cli_anything.hf_spaces.utils.repl_skin import ReplSkin

    skin = ReplSkin("hf_spaces")
    skin.table(
        ["session_id", "space_id", "updated_at", "history"],
        [
            [
                s.session_id[:8] + "...",
                s.space_id or "",
                _fmt_ts(s.updated_at),
                str(len(s.history)),
            ]
            for s in sessions
        ],
    )
    click.echo()


@session.command("show")
@click.argument("session_id")
@click.pass_context
def session_show(ctx: click.Context, session_id: str) -> None:
    """Show details for SESSION_ID."""
    state = ctx.obj
    try:
        s = session_store.load(session_id)
    except FileNotFoundError:
        click.echo(f"  ✗ Session not found: {session_id}", err=True)
        sys.exit(1)
    except ValueError as exc:
        click.echo(f"  ✗ {exc}", err=True)
        sys.exit(1)

    if state.json_output:
        click.echo(json.dumps({"ok": True, "session": s.to_dict()}, indent=2))
    else:
        click.echo(f"\n  session_id  : {s.session_id}")
        click.echo(f"  space_id    : {s.space_id or 'none'}")
        click.echo(f"  created_at  : {_fmt_ts(s.created_at)}")
        click.echo(f"  updated_at  : {_fmt_ts(s.updated_at)}")
        click.echo(f"  history     : {len(s.history)} entries")
        click.echo()


@session.command("delete")
@click.argument("session_id")
@click.pass_context
def session_delete(ctx: click.Context, session_id: str) -> None:
    """Delete SESSION_ID."""
    state = ctx.obj
    deleted = session_store.delete(session_id)
    if not deleted:
        click.echo(f"  ✗ Session not found: {session_id}", err=True)
        sys.exit(1)

    if state.json_output:
        click.echo(json.dumps({"ok": True, "deleted": session_id}, indent=2))
    else:
        click.echo(f"  ✓ Session deleted: {session_id}")


def _fmt_ts(ts: float) -> str:
    """Format a Unix timestamp as a human-readable string."""
    import datetime

    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
