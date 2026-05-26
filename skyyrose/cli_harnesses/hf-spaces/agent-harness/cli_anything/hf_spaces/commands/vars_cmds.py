"""vars command group — list, get, set, delete."""

from __future__ import annotations

import json
import sys
from typing import Optional

import click
from cli_anything.hf_spaces.core.secrets import SecretsBundle
from cli_anything.hf_spaces.core.space import SpaceRef
from cli_anything.hf_spaces.utils.hf_backend import (HfBackendError,
                                                     delete_variable,
                                                     get_variables,
                                                     set_variable)

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group("vars", context_settings=CONTEXT_SETTINGS)
def vars() -> None:
    """Environment variable management — list, get, set, delete."""


@vars.command("list")
@click.argument("space_id")
@click.pass_context
def vars_list(ctx: click.Context, space_id: str) -> None:
    """List all environment variables for SPACE_ID."""
    state = ctx.obj
    ref = SpaceRef.parse(space_id)
    try:
        raw = get_variables(ref.repo_id, token=state.token)
    except HfBackendError as exc:
        click.echo(f"  ✗ {exc}", err=True)
        sys.exit(1)

    entries = SecretsBundle.variables_from_api(raw)

    if state.json_output:
        click.echo(
            json.dumps(
                {
                    "ok": True,
                    "repo_id": ref.repo_id,
                    "variables": [e.to_dict() for e in entries],
                },
                indent=2,
            )
        )
    else:
        if not entries:
            click.echo(f"  No variables set on {ref.repo_id}.")
            return
        from cli_anything.hf_spaces.utils.repl_skin import ReplSkin

        skin = ReplSkin("hf_spaces")
        skin.table(
            ["key", "value", "description"],
            [[e.key, e.value, e.description or ""] for e in entries],
        )
        click.echo()


@vars.command("get")
@click.argument("space_id")
@click.argument("key")
@click.pass_context
def vars_get(ctx: click.Context, space_id: str, key: str) -> None:
    """Get the value of variable KEY on SPACE_ID."""
    state = ctx.obj
    ref = SpaceRef.parse(space_id)
    try:
        raw = get_variables(ref.repo_id, token=state.token)
    except HfBackendError as exc:
        click.echo(f"  ✗ {exc}", err=True)
        sys.exit(1)

    if key not in raw:
        click.echo(f"  ✗ Variable '{key}' not found on {ref.repo_id}.", err=True)
        sys.exit(1)

    value = raw[key].get("value", "")
    if state.json_output:
        click.echo(
            json.dumps(
                {"ok": True, "repo_id": ref.repo_id, "key": key, "value": value},
                indent=2,
            )
        )
    else:
        click.echo(f"  {key} = {value}")


@vars.command("set")
@click.argument("space_id")
@click.argument("key")
@click.argument("value")
@click.pass_context
def vars_set(ctx: click.Context, space_id: str, key: str, value: str) -> None:
    """Set variable KEY=VALUE on SPACE_ID."""
    state = ctx.obj
    ref = SpaceRef.parse(space_id)
    try:
        set_variable(ref.repo_id, key=key, value=value, token=state.token)
    except HfBackendError as exc:
        click.echo(f"  ✗ {exc}", err=True)
        sys.exit(1)

    if state.json_output:
        click.echo(
            json.dumps(
                {"ok": True, "repo_id": ref.repo_id, "key": key, "value": value},
                indent=2,
            )
        )
    else:
        click.echo(f"  ✓ Variable set: {key}={value} on {ref.repo_id}")


@vars.command("delete")
@click.argument("space_id")
@click.argument("key")
@click.option("--confirm", is_flag=True, default=False, help="Confirm deletion.")
@click.pass_context
def vars_delete(ctx: click.Context, space_id: str, key: str, confirm: bool) -> None:
    """Delete variable KEY from SPACE_ID. Requires --confirm."""
    state = ctx.obj
    ref = SpaceRef.parse(space_id)

    if not confirm:
        click.echo(
            f"\n  [STOP] Confirm before proceeding:\n"
            f"\n  Action : delete variable\n"
            f"  Target : {ref.repo_id}\n"
            f"  Key    : {key}\n"
            f"\n  Pass --confirm to execute.\n"
        )
        return

    try:
        delete_variable(ref.repo_id, key=key, token=state.token)
    except HfBackendError as exc:
        click.echo(f"  ✗ {exc}", err=True)
        sys.exit(1)

    if state.json_output:
        click.echo(
            json.dumps(
                {"ok": True, "action": "var_delete", "repo_id": ref.repo_id, "key": key},
                indent=2,
            )
        )
    else:
        click.echo(f"  ✓ Variable deleted: {key} from {ref.repo_id}")
