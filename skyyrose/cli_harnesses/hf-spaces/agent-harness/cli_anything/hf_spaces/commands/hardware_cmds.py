"""hardware command group — get, set, list-tiers."""

from __future__ import annotations

import json
import sys

import click
from cli_anything.hf_spaces.core.hardware import (HARDWARE_SLUGS,
                                                  hardware_table_rows,
                                                  validate_hardware_slug)
from cli_anything.hf_spaces.core.space import SpaceRef
from cli_anything.hf_spaces.utils.hf_backend import (HfBackendError,
                                                     get_hardware,
                                                     set_hardware)

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group("hardware", context_settings=CONTEXT_SETTINGS)
def hardware() -> None:
    """Hardware tier management — get, set, list-tiers."""


@hardware.command("get")
@click.argument("space_id")
@click.pass_context
def hardware_get(ctx: click.Context, space_id: str) -> None:
    """Get the current hardware tier for SPACE_ID."""
    state = ctx.obj
    ref = SpaceRef.parse(space_id)
    try:
        slug = get_hardware(ref.repo_id, token=state.token)
    except HfBackendError as exc:
        click.echo(f"  ✗ {exc}", err=True)
        sys.exit(1)

    if state.json_output:
        click.echo(json.dumps({"ok": True, "repo_id": ref.repo_id, "hardware": slug}, indent=2))
    else:
        click.echo(f"  Hardware: {slug or 'unknown'}")


@hardware.command("set")
@click.argument("space_id")
@click.argument("tier", type=click.Choice(list(HARDWARE_SLUGS), case_sensitive=True))
@click.option(
    "--confirm", is_flag=True, default=False, help="Confirm the hardware change (billing impact)."
)
@click.pass_context
def hardware_set(ctx: click.Context, space_id: str, tier: str, confirm: bool) -> None:
    """Request hardware tier TIER for SPACE_ID.

    This is a destructive/billing operation. Requires --confirm.
    """
    state = ctx.obj
    ref = SpaceRef.parse(space_id)

    if not confirm:
        click.echo(
            f"\n  [STOP] Confirm before proceeding:\n"
            f"\n  Action : hardware change\n"
            f"  Target : {ref.repo_id}\n"
            f"  Tier   : {tier}\n"
            f"\n  This may incur billing charges.\n"
            f"  Pass --confirm to execute.\n"
        )
        return

    try:
        set_hardware(ref.repo_id, tier, token=state.token)
    except HfBackendError as exc:
        click.echo(f"  ✗ {exc}", err=True)
        sys.exit(1)

    if state.json_output:
        click.echo(json.dumps({"ok": True, "repo_id": ref.repo_id, "hardware": tier}, indent=2))
    else:
        click.echo(f"  ✓ Hardware change requested: {ref.repo_id} → {tier}")


@hardware.command("list-tiers")
@click.pass_context
def hardware_list_tiers(ctx: click.Context) -> None:
    """List all available hardware tiers with reference pricing."""
    state = ctx.obj
    rows = hardware_table_rows()

    if state.json_output:
        click.echo(json.dumps({"ok": True, "tiers": rows}, indent=2))
    else:
        from cli_anything.hf_spaces.utils.repl_skin import ReplSkin

        skin = ReplSkin("hf_spaces")
        skin.hint("  Reference pricing (verify at https://huggingface.co/pricing):")
        skin.table(
            ["slug", "cost_usd_hr", "description"],
            [[r["slug"], r["cost_usd_hr"], r["description"]] for r in rows],
            max_col_width=50,
        )
        click.echo()
