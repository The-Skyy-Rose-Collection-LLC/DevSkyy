"""workflow command group — load, save, validate, render."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from cli_anything.comfyui.core.workflow import Workflow, dump_workflow, load_workflow
from cli_anything.comfyui.utils.repl_skin import ReplSkin


@click.group("workflow")
def workflow() -> None:
    """Load, validate, and inspect ComfyUI workflow JSON files."""


@workflow.command("validate")
@click.argument("workflow_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def workflow_validate(workflow_file: str, json_out: bool) -> None:
    """Validate a workflow JSON file for structural correctness."""
    skin = ReplSkin(json_mode=json_out)
    try:
        wf = load_workflow(Path(workflow_file))
    except (FileNotFoundError, ValueError) as exc:
        if json_out:
            click.echo(json.dumps({"valid": False, "errors": [str(exc)]}))
        else:
            skin.error(str(exc))
        sys.exit(1)

    errors = wf.validate()
    if json_out:
        click.echo(json.dumps({"valid": not errors, "errors": errors}))
        return

    if errors:
        skin.error(f"Validation failed ({len(errors)} error(s)):")
        for e in errors:
            skin.hint(f"  {e}")
        sys.exit(1)
    else:
        skin.success(f"Valid. {len(wf.nodes)} nodes, {len(wf.class_types())} class types.")


@workflow.command("show")
@click.argument("workflow_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def workflow_show(workflow_file: str, json_out: bool) -> None:
    """Show a summary of a workflow file."""
    skin = ReplSkin(json_mode=json_out)
    try:
        wf = load_workflow(Path(workflow_file))
    except (FileNotFoundError, ValueError) as exc:
        if json_out:
            click.echo(json.dumps({"error": str(exc)}))
        else:
            skin.error(str(exc))
        sys.exit(1)

    summary = wf.summary()
    if json_out:
        click.echo(json.dumps(summary, indent=2))
        return

    skin.section(f"Workflow: {Path(workflow_file).name}")
    skin.info(f"Nodes: {summary['node_count']}")
    skin.info(f"Class types ({len(summary['class_types'])}):")
    for ct in summary["class_types"]:
        click.echo(f"  {ct}")


@workflow.command("save")
@click.argument("workflow_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("output_file")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def workflow_save(workflow_file: str, output_file: str, json_out: bool) -> None:
    """Parse and re-save a workflow, normalising formatting."""
    skin = ReplSkin(json_mode=json_out)
    try:
        wf = load_workflow(Path(workflow_file))
        dump_workflow(wf, Path(output_file))
    except (FileNotFoundError, ValueError, OSError) as exc:
        if json_out:
            click.echo(json.dumps({"error": str(exc)}))
        else:
            skin.error(str(exc))
        sys.exit(1)

    if json_out:
        click.echo(json.dumps({"saved": output_file, "nodes": len(wf.nodes)}))
    else:
        skin.success(f"Saved {len(wf.nodes)} nodes → {output_file}")


@workflow.command("nodes")
@click.argument("workflow_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--class-type", default=None, help="Filter by class type substring")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def workflow_nodes(workflow_file: str, class_type: str | None, json_out: bool) -> None:
    """List nodes inside a workflow file."""
    skin = ReplSkin(json_mode=json_out)
    try:
        wf = load_workflow(Path(workflow_file))
    except (FileNotFoundError, ValueError) as exc:
        if json_out:
            click.echo(json.dumps({"error": str(exc)}))
        else:
            skin.error(str(exc))
        sys.exit(1)

    node_list = list(wf.nodes.values())
    if class_type:
        node_list = [n for n in node_list if class_type.lower() in n.class_type.lower()]

    if json_out:
        click.echo(
            json.dumps(
                [{"node_id": n.node_id, "class_type": n.class_type} for n in node_list], indent=2
            )
        )
        return

    skin.section(f"Nodes in {Path(workflow_file).name} ({len(node_list)})")
    rows = [[n.node_id, n.class_type] for n in node_list]
    skin.table(["ID", "Class Type"], rows)
