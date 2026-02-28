#!/usr/bin/env python3
"""Unified AI CLI for SkyyRose — training, datasets, Spaces, models."""
from __future__ import annotations

from pathlib import Path

import typer
from huggingface_hub import HfApi
from rich.console import Console
from rich.table import Table

from scripts.ai_config import AIConfig

app = typer.Typer(name="ai", help="SkyyRose AI CLI — train, manage, deploy.")
spaces_app = typer.Typer(help="HuggingFace Spaces management.")
app.add_typer(spaces_app, name="spaces")

console = Console()
config = AIConfig()


# ── Spaces ──────────────────────────────────────────────────────────────


@spaces_app.command("list")
def spaces_list():
    """List all damBruh HuggingFace Spaces."""
    api = HfApi(token=config.get_hf_token())
    spaces = list(api.list_spaces(author=config.hf_user))

    table = Table(title=f"Spaces ({config.hf_user})")
    table.add_column("Name", style="cyan")
    table.add_column("SDK")
    table.add_column("URL")

    for space in spaces:
        name = space.id.split("/")[-1]
        sdk = getattr(space, "sdk", "?")
        url = f"https://huggingface.co/spaces/{space.id}"
        table.add_row(name, str(sdk), url)

    console.print(table)


@spaces_app.command("status")
def spaces_status(name: str):
    """Show Space runtime status."""
    api = HfApi(token=config.get_hf_token())
    repo_id = f"{config.hf_user}/{name}" if "/" not in name else name
    runtime = api.get_space_runtime(repo_id)

    console.print(f"[bold]{repo_id}[/bold]")
    console.print(f"  Stage: {runtime.stage}")
    hardware = getattr(runtime, "hardware", None)
    if hardware:
        console.print(f"  Hardware: {getattr(hardware, 'current', '?')}")
        console.print(f"  Requested: {getattr(hardware, 'requested', '?')}")


@spaces_app.command("restart")
def spaces_restart(name: str):
    """Restart a Space (factory reset if stuck)."""
    api = HfApi(token=config.get_hf_token())
    repo_id = f"{config.hf_user}/{name}" if "/" not in name else name
    api.restart_space(repo_id)
    console.print(f"[green]Restarted {repo_id}[/green]")


@spaces_app.command("hardware")
def spaces_hardware(name: str, gpu: str = "t4-medium"):
    """Change Space GPU hardware."""
    api = HfApi(token=config.get_hf_token())
    repo_id = f"{config.hf_user}/{name}" if "/" not in name else name
    api.request_space_hardware(repo_id, hardware=gpu)
    console.print(f"[green]Requested {gpu} for {repo_id}[/green]")


@spaces_app.command("deploy")
def spaces_deploy(name: str):
    """Deploy trainer app.py to a Space."""
    from scripts.ai_templates import render_requirements, render_trainer_app

    api = HfApi(token=config.get_hf_token())
    repo_id = f"{config.hf_user}/{name}" if "/" not in name else name

    api.create_repo(repo_id, repo_type="space", space_sdk="gradio", exist_ok=True)

    app_content = render_trainer_app(config)
    api.upload_file(
        path_or_fileobj=app_content.encode(),
        path_in_repo="app.py",
        repo_id=repo_id,
        repo_type="space",
        commit_message="Deploy trainer app via AI CLI",
    )

    reqs_content = render_requirements()
    api.upload_file(
        path_or_fileobj=reqs_content.encode(),
        path_in_repo="requirements.txt",
        repo_id=repo_id,
        repo_type="space",
        commit_message="Update requirements via AI CLI",
    )

    console.print(f"[green]Deployed to {repo_id}[/green]")
    console.print(f"  https://huggingface.co/spaces/{repo_id}")


if __name__ == "__main__":
    app()
