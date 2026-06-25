"""secrets command group — set, delete, list (manifest-only).

IMPORTANT: HfApi has no get_space_secrets method. Secrets are write-only
by design (HF security model). The 'list' subcommand reads from a local
manifest file only and explicitly documents this limitation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click
from cli_anything.hf_spaces.core.space import SpaceRef
from cli_anything.hf_spaces.utils.hf_backend import (HfBackendError,
                                                     delete_secret, set_secret)

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group("secrets", context_settings=CONTEXT_SETTINGS)
def secrets() -> None:
    """Secret management — set, delete, list (manifest-only).

    NOTE: HuggingFace does not allow reading secret values or names via API.
    The 'list' command reads from a local manifest file only.
    """


@secrets.command("set")
@click.argument("space_id")
@click.argument("key")
@click.option(
    "--value",
    default=None,
    help="Secret value. If omitted, prompted interactively (recommended).",
)
@click.pass_context
def secrets_set(ctx: click.Context, space_id: str, key: str, value: Optional[str]) -> None:
    """Set secret KEY on SPACE_ID.

    Value is prompted interactively if --value is not supplied.
    The value is used in-memory only and never written to disk.
    """
    state = ctx.obj
    ref = SpaceRef.parse(space_id)

    if value is None:
        value = click.prompt(f"  Value for {key}", hide_input=True, confirmation_prompt=True)

    try:
        set_secret(ref.repo_id, key=key, value=value, token=state.token)
    except HfBackendError as exc:
        click.echo(f"  ✗ {exc}", err=True)
        sys.exit(1)

    if state.json_output:
        click.echo(
            json.dumps(
                {"ok": True, "action": "secret_set", "repo_id": ref.repo_id, "key": key},
                indent=2,
            )
        )
    else:
        click.echo(f"  ✓ Secret set: {key} on {ref.repo_id}")


@secrets.command("delete")
@click.argument("space_id")
@click.argument("key")
@click.option("--confirm", is_flag=True, default=False, help="Confirm the deletion.")
@click.pass_context
def secrets_delete(ctx: click.Context, space_id: str, key: str, confirm: bool) -> None:
    """Delete secret KEY from SPACE_ID. Requires --confirm."""
    state = ctx.obj
    ref = SpaceRef.parse(space_id)

    if not confirm:
        click.echo(
            f"\n  [STOP] Confirm before proceeding:\n"
            f"\n  Action : delete secret\n"
            f"  Target : {ref.repo_id}\n"
            f"  Key    : {key}\n"
            f"\n  This is irreversible. Pass --confirm to execute.\n"
        )
        return

    try:
        delete_secret(ref.repo_id, key=key, token=state.token)
    except HfBackendError as exc:
        click.echo(f"  ✗ {exc}", err=True)
        sys.exit(1)

    if state.json_output:
        click.echo(
            json.dumps(
                {
                    "ok": True,
                    "action": "secret_delete",
                    "repo_id": ref.repo_id,
                    "key": key,
                },
                indent=2,
            )
        )
    else:
        click.echo(f"  ✓ Secret deleted: {key} from {ref.repo_id}")


@secrets.command("list")
@click.option(
    "--manifest",
    "manifest_path",
    default=None,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to manifest JSON. Reads secret key names from manifest only.",
)
@click.pass_context
def secrets_list(ctx: click.Context, manifest_path: Optional[str]) -> None:
    """List secret key names from a local manifest file.

    LIMITATION: The HuggingFace API does not allow reading secret names or
    values after they are written. This command reads from a local manifest
    file only. If no manifest is provided, an empty list is returned.

    Use 'manifest init' to create a manifest that tracks secret key names.
    """
    state = ctx.obj

    key_names: list = []
    source = "none"

    if manifest_path:
        try:
            from cli_anything.hf_spaces.core.manifest import ManifestSpec

            spec = ManifestSpec.load(Path(manifest_path))
            key_names = list(spec.secrets)
            source = manifest_path
        except Exception as exc:
            click.echo(f"  ✗ Could not read manifest: {exc}", err=True)
            sys.exit(1)

    warning = (
        "HuggingFace API does not support reading secret names. "
        "Results are from local manifest only."
    )

    if state.json_output:
        click.echo(
            json.dumps(
                {
                    "ok": True,
                    "source": source,
                    "warning": warning,
                    "secrets": key_names,
                },
                indent=2,
            )
        )
    else:
        click.echo(f"\n  ⚠  {warning}\n")
        if key_names:
            click.echo(f"  Secrets in manifest ({source}):")
            for k in key_names:
                click.echo(f"    • {k}")
        else:
            click.echo("  No secrets found in manifest (or no manifest provided).")
        click.echo()
