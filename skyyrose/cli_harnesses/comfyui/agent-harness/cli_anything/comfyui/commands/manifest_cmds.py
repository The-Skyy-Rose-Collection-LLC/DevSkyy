"""manifest command group — plan/apply action manifests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from cli_anything.comfyui.core.manifest import (
    ActionManifest,
    ChangeItem,
    ChangeKind,
    build_plan,
    load_manifest,
    plan_history_clear,
    plan_queue_clear,
    plan_queue_interrupt,
    plan_queue_submit,
    save_manifest,
)
from cli_anything.comfyui.core.secrets import resolve_secrets
from cli_anything.comfyui.core.workflow import load_workflow
from cli_anything.comfyui.utils.comfyui_backend import ComfyUIBackend, ComfyUIBackendError
from cli_anything.comfyui.utils.repl_skin import ReplSkin


@click.group("manifest")
def manifest() -> None:
    """Plan and apply batched ComfyUI operations."""


@manifest.command("plan")
@click.option(
    "--submit", "submit_file", default=None, type=click.Path(), help="Workflow file to submit"
)
@click.option("--clear-queue", is_flag=True, help="Add queue clear to plan")
@click.option("--interrupt", is_flag=True, help="Add interrupt to plan")
@click.option("--clear-history", is_flag=True, help="Add history clear to plan")
@click.option("--output", default=None, type=click.Path(), help="Path to save manifest JSON")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def manifest_plan(
    submit_file: str | None,
    clear_queue: bool,
    interrupt: bool,
    clear_history: bool,
    output: str | None,
    json_out: bool,
) -> None:
    """Build a manifest of planned actions (does NOT execute them)."""
    skin = ReplSkin(json_mode=json_out)
    changes: list[ChangeItem] = []

    if submit_file:
        changes.append(plan_queue_submit(submit_file))
    if clear_queue:
        changes.append(plan_queue_clear())
    if interrupt:
        changes.append(plan_queue_interrupt())
    if clear_history:
        changes.append(plan_history_clear())

    if not changes:
        if json_out:
            click.echo(json.dumps({"error": "No actions specified for plan"}))
        else:
            skin.warning(
                "Specify at least one action (--submit, --clear-queue, --interrupt, --clear-history)."
            )
        sys.exit(1)

    m = build_plan(changes)
    path = save_manifest(m, output)

    if json_out:
        click.echo(json.dumps({"manifest": m.to_dict(), "path": str(path)}))
        return

    skin.section("Manifest Plan")
    for c in m.changes:
        marker = "[DESTRUCTIVE] " if c.is_destructive() else ""
        skin.info(f"  {marker}{c.kind.value}: {c.description}")
    skin.hint(f"Saved to: {path}")
    skin.hint("Run `manifest apply` to execute.")


@manifest.command("show")
@click.option("--path", "manifest_path", default=None, type=click.Path(), help="Manifest file path")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def manifest_show(manifest_path: str | None, json_out: bool) -> None:
    """Show the current manifest."""
    skin = ReplSkin(json_mode=json_out)
    m = load_manifest(manifest_path)

    if json_out:
        click.echo(json.dumps(m.to_dict(), indent=2))
        return

    skin.section("Current Manifest")
    if not m.changes:
        skin.hint("No changes in manifest.")
        return
    for c in m.changes:
        skin.info(c.summary())
    skin.info(f"Applied: {m.applied}")


@manifest.command("apply")
@click.option("--host", envvar="COMFYUI_HOST", default=None, help="ComfyUI base URL")
@click.option("--token", envvar="COMFYUI_AUTH_TOKEN", default=None, help="Bearer token")
@click.option("--path", "manifest_path", default=None, type=click.Path(), help="Manifest file path")
@click.option("--confirm", is_flag=True, help="Required when manifest contains destructive changes")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def manifest_apply(
    host: str | None,
    token: str | None,
    manifest_path: str | None,
    confirm: bool,
    json_out: bool,
) -> None:
    """Apply the current manifest, executing all planned actions."""
    skin = ReplSkin(json_mode=json_out)
    m = load_manifest(manifest_path)

    if not m.changes:
        if json_out:
            click.echo(json.dumps({"error": "No changes in manifest"}))
        else:
            skin.warning("Manifest is empty.")
        sys.exit(1)

    if m.has_destructive() and not confirm:
        if json_out:
            click.echo(
                json.dumps({"error": "Manifest contains destructive changes; pass --confirm"})
            )
        else:
            skin.warning("Manifest contains destructive changes. Pass --confirm to proceed.")
        sys.exit(1)

    secrets = resolve_secrets(host, token)
    backend = ComfyUIBackend(base_url=secrets.base_url, auth_headers=secrets.auth_headers())
    results: list[dict] = []

    for change in m.changes:
        try:
            if change.kind == ChangeKind.QUEUE_SUBMIT:
                wf_path = change.params.get("workflow_path", "")
                wf = load_workflow(Path(wf_path))
                from cli_anything.comfyui.core.queue import build_prompt_payload

                payload = build_prompt_payload(wf.to_dict())
                result = backend.submit_prompt(payload)
                results.append({"kind": change.kind.value, "result": result})
            elif change.kind == ChangeKind.QUEUE_CLEAR:
                result = backend.queue_clear()
                results.append({"kind": change.kind.value, "result": result})
            elif change.kind == ChangeKind.QUEUE_INTERRUPT:
                result = backend.interrupt()
                results.append({"kind": change.kind.value, "result": result})
            elif change.kind == ChangeKind.HISTORY_CLEAR:
                pid = change.params.get("prompt_id")
                result = backend.clear_history(prompt_id=pid)
                results.append({"kind": change.kind.value, "result": result})
            else:
                results.append({"kind": change.kind.value, "skipped": True})
        except ComfyUIBackendError as exc:
            results.append({"kind": change.kind.value, "error": str(exc)})

    m.applied = True
    save_manifest(m, manifest_path)

    if json_out:
        click.echo(json.dumps({"applied": results}, indent=2))
        return

    skin.section("Apply Results")
    for r in results:
        if "error" in r:
            skin.error(f"{r['kind']}: {r['error']}")
        elif r.get("skipped"):
            skin.warning(f"{r['kind']}: skipped")
        else:
            skin.success(f"{r['kind']}: ok")
