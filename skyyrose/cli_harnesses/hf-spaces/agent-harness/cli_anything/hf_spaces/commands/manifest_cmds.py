"""manifest command group — init, plan, apply, show."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click
from cli_anything.hf_spaces.core.manifest import (DEFAULT_MANIFEST_NAME,
                                                  ManifestSpec, build_plan)
from cli_anything.hf_spaces.core.secrets import SecretsBundle
from cli_anything.hf_spaces.core.space import SpaceRef
from cli_anything.hf_spaces.utils.hf_backend import (HfBackendError,
                                                     delete_secret,
                                                     delete_variable,
                                                     get_readme,
                                                     get_space_runtime,
                                                     get_variables,
                                                     set_hardware, set_secret,
                                                     set_sleep_time,
                                                     set_variable,
                                                     upload_readme)

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group("manifest", context_settings=CONTEXT_SETTINGS)
def manifest() -> None:
    """Manifest plan/apply — declare desired state and diff against actual."""


@manifest.command("init")
@click.argument("space_id")
@click.option(
    "--out",
    default=DEFAULT_MANIFEST_NAME,
    show_default=True,
    type=click.Path(dir_okay=False),
    help="Output path for the manifest file.",
)
@click.option("--hardware", default=None, help="Initial hardware tier slug.")
@click.option("--sleep-time", default=None, type=int, help="Sleep time in seconds (-1 = never).")
@click.pass_context
def manifest_init(
    ctx: click.Context,
    space_id: str,
    out: str,
    hardware: Optional[str],
    sleep_time: Optional[int],
) -> None:
    """Create a new manifest file for SPACE_ID."""
    ref = SpaceRef.parse(space_id)
    spec = ManifestSpec(
        space_id=ref.repo_id,
        hardware=hardware,
        sleep_time=sleep_time,
    )
    out_path = Path(out)
    if out_path.exists():
        click.echo(f"  ✗ Manifest already exists: {out_path}. Delete it first.", err=True)
        sys.exit(1)
    spec.save(out_path)
    click.echo(f"  ✓ Manifest created: {out_path}")
    click.echo(f"    Edit it to declare desired state, then run: manifest plan {out_path}")


@manifest.command("show")
@click.argument("manifest_file", type=click.Path(exists=True, dir_okay=False))
@click.pass_context
def manifest_show(ctx: click.Context, manifest_file: str) -> None:
    """Pretty-print the manifest file."""
    state = ctx.obj
    try:
        spec = ManifestSpec.load(Path(manifest_file))
    except Exception as exc:
        click.echo(f"  ✗ {exc}", err=True)
        sys.exit(1)

    if state.json_output:
        click.echo(json.dumps({"ok": True, "manifest": spec.to_dict()}, indent=2))
    else:
        click.echo(json.dumps(spec.to_dict(), indent=2))


@manifest.command("plan")
@click.argument("manifest_file", type=click.Path(exists=True, dir_okay=False))
@click.pass_context
def manifest_plan(ctx: click.Context, manifest_file: str) -> None:
    """Show what 'manifest apply' would change without executing anything."""
    state = ctx.obj
    try:
        spec = ManifestSpec.load(Path(manifest_file))
    except Exception as exc:
        click.echo(f"  ✗ Could not load manifest: {exc}", err=True)
        sys.exit(1)

    ref = SpaceRef.parse(spec.space_id)

    # Fetch current state from HF
    try:
        runtime = get_space_runtime(ref.repo_id, token=state.token)
        hw = getattr(runtime, "hardware", None)
        current_hardware = (
            str(hw.current.value if hasattr(hw.current, "value") else hw.current)
            if hw and getattr(hw, "current", None)
            else None
        )
        current_sleep = getattr(runtime, "sleep_time", None)
    except HfBackendError as exc:
        click.echo(f"  ✗ Could not fetch runtime: {exc}", err=True)
        sys.exit(1)

    try:
        raw_vars = get_variables(ref.repo_id, token=state.token)
        current_vars = {k: v.get("value", "") for k, v in raw_vars.items()}
    except HfBackendError as exc:
        click.echo(f"  ✗ Could not fetch variables: {exc}", err=True)
        sys.exit(1)

    current_readme = get_readme(ref.repo_id, token=state.token)

    changes = build_plan(
        spec=spec,
        current_hardware=current_hardware,
        current_sleep_time=current_sleep,
        current_variables=current_vars,
        current_readme=current_readme,
    )

    if state.json_output:
        click.echo(
            json.dumps(
                {
                    "ok": True,
                    "repo_id": ref.repo_id,
                    "changes": [c.to_dict() for c in changes],
                },
                indent=2,
            )
        )
        return

    if not changes:
        click.echo(f"  ✓ No changes needed — {ref.repo_id} matches manifest.")
        return

    click.echo(f"\n  Planned changes for {ref.repo_id}:")
    for c in changes:
        click.echo(c.summary())
    destructive = [c for c in changes if c.destructive]
    if destructive:
        click.echo(
            f"\n  ⚠  {len(destructive)} destructive change(s) — will require --confirm on apply."
        )
    click.echo(f"\n  Run 'manifest apply {manifest_file} --confirm' to execute.\n")


@manifest.command("apply")
@click.argument("manifest_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--confirm", is_flag=True, default=False, help="Confirm and execute all changes.")
@click.pass_context
def manifest_apply(ctx: click.Context, manifest_file: str, confirm: bool) -> None:
    """Apply manifest to live Space. STOP-AND-SHOW before any change.

    Requires --confirm to execute. Shows the change manifest if omitted.
    """
    state = ctx.obj
    try:
        spec = ManifestSpec.load(Path(manifest_file))
    except Exception as exc:
        click.echo(f"  ✗ Could not load manifest: {exc}", err=True)
        sys.exit(1)

    ref = SpaceRef.parse(spec.space_id)

    # Fetch current state
    try:
        runtime = get_space_runtime(ref.repo_id, token=state.token)
        hw = getattr(runtime, "hardware", None)
        current_hardware = (
            str(hw.current.value if hasattr(hw.current, "value") else hw.current)
            if hw and getattr(hw, "current", None)
            else None
        )
        current_sleep = getattr(runtime, "sleep_time", None)
    except HfBackendError as exc:
        click.echo(f"  ✗ Could not fetch runtime: {exc}", err=True)
        sys.exit(1)

    try:
        raw_vars = get_variables(ref.repo_id, token=state.token)
        current_vars = {k: v.get("value", "") for k, v in raw_vars.items()}
    except HfBackendError as exc:
        click.echo(f"  ✗ Could not fetch variables: {exc}", err=True)
        sys.exit(1)

    current_readme = get_readme(ref.repo_id, token=state.token)

    changes = build_plan(
        spec=spec,
        current_hardware=current_hardware,
        current_sleep_time=current_sleep,
        current_variables=current_vars,
        current_readme=current_readme,
    )

    if not changes:
        click.echo(f"  ✓ No changes needed — {ref.repo_id} already matches manifest.")
        return

    # STOP-AND-SHOW
    click.echo(f"\n  [STOP] Confirm before proceeding:\n")
    click.echo(f"  Target : {ref.repo_id}")
    click.echo(f"  Changes ({len(changes)}):")
    for c in changes:
        click.echo(c.summary())

    destructive = [c for c in changes if c.destructive]
    if destructive:
        click.echo(f"\n  ⚠  {len(destructive)} destructive change(s) included.")

    if not confirm:
        click.echo(f"\n  Pass --confirm to execute.\n")
        return

    # Collect secret values before applying (prompt once per secret)
    secret_values: dict = {}
    from cli_anything.hf_spaces.core.manifest import ChangeKind

    secret_changes = [c for c in changes if c.kind == ChangeKind.SECRET_SET]
    for c in secret_changes:
        secret_values[c.key] = click.prompt(
            f"  Value for secret {c.key}", hide_input=True, confirmation_prompt=False
        )

    # Apply changes
    errors: list = []
    applied: list = []

    for c in changes:
        try:
            if c.kind == ChangeKind.HARDWARE:
                set_hardware(ref.repo_id, c.desired, token=state.token)
            elif c.kind == ChangeKind.SLEEP_TIME:
                set_sleep_time(ref.repo_id, int(c.desired), token=state.token)
            elif c.kind == ChangeKind.VARIABLE_SET:
                set_variable(ref.repo_id, c.key, c.desired, token=state.token)
            elif c.kind == ChangeKind.VARIABLE_DELETE:
                delete_variable(ref.repo_id, c.key, token=state.token)
            elif c.kind == ChangeKind.SECRET_SET:
                val = secret_values.get(c.key, "")
                set_secret(ref.repo_id, c.key, val, token=state.token)
            elif c.kind == ChangeKind.README_SYNC:
                content = Path(c.desired).read_text(encoding="utf-8")
                upload_readme(ref.repo_id, content, token=state.token)
            applied.append(c.summary().strip())
        except HfBackendError as exc:
            errors.append(f"{c.summary().strip()}: {exc}")

    click.echo()
    for a in applied:
        click.echo(f"  ✓ Applied: {a}")
    for e in errors:
        click.echo(f"  ✗ Failed:  {e}", err=True)

    if errors:
        sys.exit(1)
    else:
        click.echo(f"\n  ✓ Manifest applied to {ref.repo_id} ({len(applied)} change(s)).\n")
