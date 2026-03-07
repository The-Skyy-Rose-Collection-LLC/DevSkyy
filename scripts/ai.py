#!/usr/bin/env python3
"""Unified AI CLI for SkyyRose — training, datasets, Spaces, models."""

from __future__ import annotations

from pathlib import Path

import typer
from huggingface_hub import HfApi, snapshot_download
from rich.console import Console
from rich.table import Table

from scripts.ai_config import AIConfig
from scripts.ai_providers import PROVIDERS

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


# ── Train ───────────────────────────────────────────────────────────────

train_app = typer.Typer(help="Training orchestration.")
app.add_typer(train_app, name="train")


@train_app.command("run")
def train_run(
    provider: str = typer.Option("replicate", help="Provider: replicate or hf"),
    steps: int = typer.Option(None, help="Training steps (default: from config)"),
    gpu: str = typer.Option(None, help="GPU type for HF (default: t4-medium)"),
):
    """Start LoRA training run."""
    if provider not in PROVIDERS:
        console.print(f"[red]Unknown provider: {provider}. Use 'replicate' or 'hf'.[/red]")
        raise typer.Exit(code=1)

    run_config = AIConfig(
        steps=steps or config.steps,
        default_gpu=gpu or config.default_gpu,
    )

    console.print(f"[bold]Starting training via {provider}...[/bold]")
    console.print(f"  Steps: {run_config.steps}")
    console.print(f"  Dataset: {run_config.dataset}")

    job_id = PROVIDERS[provider].start_training(run_config)
    console.print(f"[green]Training started! Job: {job_id}[/green]")


@train_app.command("status")
def train_status(
    provider: str = typer.Option("replicate", help="Provider: replicate or hf"),
    job_id: str = typer.Option(None, help="Job ID (required for Replicate)"),
):
    """Check training status."""
    if provider not in PROVIDERS:
        console.print(f"[red]Unknown provider: {provider}[/red]")
        raise typer.Exit(code=1)

    check_id = job_id or config.trainer_space
    status = PROVIDERS[provider].get_status(check_id)

    console.print(f"[bold]Training Status ({provider})[/bold]")
    for key, value in status.items():
        if key != "logs":
            console.print(f"  {key}: {value}")

    if "logs" in status and status["logs"]:
        console.print(f"\n[dim]Last log:[/dim] {status['logs'][-200:]}")


@train_app.command("logs")
def train_logs(
    provider: str = typer.Option("replicate", help="Provider: replicate or hf"),
    job_id: str = typer.Option(None, help="Job ID"),
):
    """Stream training logs."""
    if provider not in PROVIDERS:
        console.print(f"[red]Unknown provider: {provider}[/red]")
        raise typer.Exit(code=1)

    check_id = job_id or config.trainer_space
    for line in PROVIDERS[provider].get_logs(check_id):
        console.print(line)


# ── Dataset ─────────────────────────────────────────────────────────────

dataset_app = typer.Typer(help="Dataset management.")
app.add_typer(dataset_app, name="dataset")


@dataset_app.command("info")
def dataset_info(name: str):
    """Show dataset info from HuggingFace Hub."""
    api = HfApi(token=config.get_hf_token())
    repo_id = f"{config.hf_user}/{name}" if "/" not in name else name
    info = api.dataset_info(repo_id)

    console.print(f"[bold]{info.id}[/bold]")
    console.print(f"  Downloads: {info.downloads}")
    console.print(f"  Files: {len(info.siblings)}")


@dataset_app.command("push")
def dataset_push(
    source: str = typer.Option(..., help="Local directory with images"),
    name: str = typer.Option(..., help="Dataset name on Hub"),
):
    """Upload a local directory as a HuggingFace dataset."""
    api = HfApi(token=config.get_hf_token())
    repo_id = f"{config.hf_user}/{name}" if "/" not in name else name
    source_path = Path(source)

    if not source_path.exists():
        console.print(f"[red]Source not found: {source}[/red]")
        raise typer.Exit(code=1)

    api.create_repo(repo_id, repo_type="dataset", exist_ok=True)
    api.upload_folder(
        folder_path=str(source_path),
        repo_id=repo_id,
        repo_type="dataset",
        commit_message="Upload dataset via AI CLI",
    )
    console.print(f"[green]Pushed to {repo_id}[/green]")
    console.print(f"  https://huggingface.co/datasets/{repo_id}")


# ── Model ───────────────────────────────────────────────────────────────

model_app = typer.Typer(help="Model operations.")
app.add_typer(model_app, name="model")


@model_app.command("list")
def model_list():
    """List damBruh models on HuggingFace Hub."""
    api = HfApi(token=config.get_hf_token())
    models = list(api.list_models(author=config.hf_user))

    table = Table(title=f"Models ({config.hf_user})")
    table.add_column("Name", style="cyan")
    table.add_column("Downloads")
    table.add_column("Tags")

    for model in models:
        name = model.id.split("/")[-1]
        downloads = str(getattr(model, "downloads", 0))
        tags = ", ".join(getattr(model, "tags", [])[:3])
        table.add_row(name, downloads, tags)

    console.print(table)


@model_app.command("info")
def model_info(name: str):
    """Show model details."""
    api = HfApi(token=config.get_hf_token())
    repo_id = f"{config.hf_user}/{name}" if "/" not in name else name
    info = api.model_info(repo_id)

    console.print(f"[bold]{info.id}[/bold]")
    console.print(f"  Downloads: {info.downloads}")
    console.print(f"  Files: {len(info.siblings)}")
    for f in info.siblings:
        size_mb = getattr(f, "size", 0) / 1_000_000
        console.print(f"    {f.rfilename} ({size_mb:.1f} MB)")


@model_app.command("download")
def model_download(
    name: str, output: str = typer.Option("./models", help="Local output directory")
):
    """Download model from Hub to local directory."""
    repo_id = f"{config.hf_user}/{name}" if "/" not in name else name
    local_dir = snapshot_download(
        repo_id=repo_id,
        local_dir=f"{output}/{name}",
        token=config.get_hf_token(),
    )
    console.print(f"[green]Downloaded to {local_dir}[/green]")


if __name__ == "__main__":
    app()
