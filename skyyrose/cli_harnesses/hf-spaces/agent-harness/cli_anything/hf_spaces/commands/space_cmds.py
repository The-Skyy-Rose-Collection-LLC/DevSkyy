"""space command group — info, list, pause, restart, duplicate."""

from __future__ import annotations

import json
from typing import Optional

import click
from cli_anything.hf_spaces.core.space import SpaceRef
from cli_anything.hf_spaces.utils.hf_backend import (HfBackendError,
                                                     duplicate_space,
                                                     get_space_info,
                                                     list_spaces, pause_space,
                                                     restart_space)

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


def _state(ctx: click.Context):
    return ctx.find_object(object)  # returns CliState


@click.group("space", context_settings=CONTEXT_SETTINGS)
def space() -> None:
    """Space lifecycle — info, list, pause, restart, duplicate."""


# ---------------------------------------------------------------------------
# space info
# ---------------------------------------------------------------------------


@space.command("info")
@click.argument("space_id")
@click.pass_context
def space_info(ctx: click.Context, space_id: str) -> None:
    """Show runtime info for SPACE_ID (owner/name or full URL)."""
    state = ctx.obj
    try:
        ref = SpaceRef.parse(space_id)
        info = get_space_info(ref.repo_id, token=state.token)
    except HfBackendError as exc:
        import sys

        if state.json_output:
            click.echo(json.dumps({"ok": False, "error": str(exc)}, indent=2), err=True)
        else:
            click.echo(f"  ✗ {exc}", err=True)
        sys.exit(1)

    runtime = getattr(info, "runtime", None)
    stage = str(getattr(runtime, "stage", "unknown")) if runtime else "unknown"
    hw = getattr(runtime, "hardware", None)
    hw_current = (
        str(hw.current.value if hasattr(hw.current, "value") else hw.current)
        if hw and getattr(hw, "current", None)
        else "unknown"
    )
    hw_requested = (
        str(hw.requested.value if hasattr(hw.requested, "value") else hw.requested)
        if hw and getattr(hw, "requested", None)
        else None
    )

    payload = {
        "ok": True,
        "repo_id": ref.repo_id,
        "url": ref.url,
        "stage": stage,
        "hardware_current": hw_current,
        "hardware_requested": hw_requested,
        "private": getattr(info, "private", None),
        "sdk": getattr(info, "sdk", None),
    }

    if state.json_output:
        click.echo(json.dumps(payload, indent=2))
    else:
        click.echo(f"\n  Space: {ref.url}")
        click.echo(f"  Stage        : {stage}")
        click.echo(f"  Hardware     : {hw_current}")
        if hw_requested:
            click.echo(f"  HW requested : {hw_requested}")
        click.echo(f"  Private      : {payload['private']}")
        click.echo(f"  SDK          : {payload['sdk'] or 'unknown'}")
        click.echo()


# ---------------------------------------------------------------------------
# space list
# ---------------------------------------------------------------------------


@space.command("list")
@click.option("--author", default=None, help="Filter by author/org.")
@click.option("--search", default=None, help="Search query.")
@click.option("--limit", default=20, show_default=True, help="Max results.")
@click.pass_context
def space_list(
    ctx: click.Context,
    author: Optional[str],
    search: Optional[str],
    limit: int,
) -> None:
    """List HuggingFace Spaces."""
    state = ctx.obj
    try:
        spaces = list_spaces(author=author, search=search, token=state.token, limit=limit)
    except HfBackendError as exc:
        import sys

        click.echo(f"  ✗ {exc}", err=True)
        sys.exit(1)

    rows = []
    for s in spaces:
        rid = getattr(s, "id", "")
        runtime = getattr(s, "runtime", None)
        stage = str(getattr(runtime, "stage", "")) if runtime else ""
        rows.append({"repo_id": rid, "stage": stage})

    if state.json_output:
        click.echo(json.dumps({"ok": True, "spaces": rows}, indent=2))
    else:
        if not rows:
            click.echo("  No spaces found.")
            return
        from cli_anything.hf_spaces.utils.repl_skin import ReplSkin

        skin = ReplSkin("hf_spaces")
        skin.table(
            ["repo_id", "stage"],
            [[r["repo_id"], r["stage"]] for r in rows],
        )
        click.echo()


# ---------------------------------------------------------------------------
# space pause
# ---------------------------------------------------------------------------


@space.command("pause")
@click.argument("space_id")
@click.option("--confirm", is_flag=True, default=False, help="Confirm the pause.")
@click.pass_context
def space_pause(ctx: click.Context, space_id: str, confirm: bool) -> None:
    """Pause SPACE_ID. Requires --confirm."""
    state = ctx.obj
    ref = SpaceRef.parse(space_id)

    if not confirm:
        click.echo(
            f"\n  [STOP] Confirm before proceeding:\n"
            f"\n  Action : pause Space\n"
            f"  Target : {ref.repo_id}\n"
            f"\n  Pass --confirm to execute.\n"
        )
        return

    try:
        pause_space(ref.repo_id, token=state.token)
    except HfBackendError as exc:
        import sys

        click.echo(f"  ✗ {exc}", err=True)
        sys.exit(1)

    if state.json_output:
        click.echo(json.dumps({"ok": True, "action": "pause", "repo_id": ref.repo_id}))
    else:
        click.echo(f"  ✓ Space paused: {ref.repo_id}")


# ---------------------------------------------------------------------------
# space restart
# ---------------------------------------------------------------------------


@space.command("restart")
@click.argument("space_id")
@click.pass_context
def space_restart(ctx: click.Context, space_id: str) -> None:
    """Warm-restart SPACE_ID."""
    state = ctx.obj
    ref = SpaceRef.parse(space_id)
    try:
        restart_space(ref.repo_id, token=state.token)
    except HfBackendError as exc:
        import sys

        click.echo(f"  ✗ {exc}", err=True)
        sys.exit(1)

    if state.json_output:
        click.echo(json.dumps({"ok": True, "action": "restart", "repo_id": ref.repo_id}))
    else:
        click.echo(f"  ✓ Space restarted: {ref.repo_id}")


# ---------------------------------------------------------------------------
# space duplicate
# ---------------------------------------------------------------------------


@space.command("duplicate")
@click.argument("from_id")
@click.argument("to_id")
@click.option(
    "--private/--public",
    default=True,
    show_default=True,
    help="Make the new Space private (default) or public.",
)
@click.option(
    "--exist-ok",
    is_flag=True,
    default=False,
    help="Don't error if destination already exists.",
)
@click.pass_context
def space_duplicate(
    ctx: click.Context,
    from_id: str,
    to_id: str,
    private: bool,
    exist_ok: bool,
) -> None:
    """Duplicate FROM_ID to TO_ID."""
    state = ctx.obj
    from_ref = SpaceRef.parse(from_id)
    to_ref = SpaceRef.parse(to_id)
    try:
        info = duplicate_space(
            from_id=from_ref.repo_id,
            to_id=to_ref.repo_id,
            private=private,
            exist_ok=exist_ok,
            token=state.token,
        )
    except HfBackendError as exc:
        import sys

        click.echo(f"  ✗ {exc}", err=True)
        sys.exit(1)

    new_id = getattr(info, "id", to_ref.repo_id)
    if state.json_output:
        click.echo(
            json.dumps(
                {
                    "ok": True,
                    "action": "duplicate",
                    "from": from_ref.repo_id,
                    "to": new_id,
                    "private": private,
                },
                indent=2,
            )
        )
    else:
        click.echo(f"  ✓ Duplicated {from_ref.repo_id} → {new_id} (private={private})")
