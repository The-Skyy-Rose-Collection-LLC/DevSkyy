# AI CLI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build `scripts/ai.py` — a unified multi-provider CLI that consolidates 30+ scattered AI/ML scripts into 4 subcommand groups (spaces, dataset, train, model) with HF + Replicate providers.

**Architecture:** 4 Python files under `scripts/` using Typer for CLI, `huggingface_hub` for HF API, `replicate` for Replicate API, and `gradio_client` for Space interaction. All compute is remote — no heavy ML deps in the CLI.

**Tech Stack:** Python 3.11+, Typer, huggingface_hub, replicate, gradio_client, Rich (via Typer)

**Design doc:** `docs/plans/2026-02-28-ai-cli-design.md`

---

## Task 1: Config module (`ai_config.py`)

**Files:**
- Create: `scripts/ai_config.py`
- Test: `tests/scripts/test_ai_config.py`

**Step 1: Create test directory and write failing tests**

Create `tests/scripts/__init__.py` (empty) and `tests/scripts/test_ai_config.py`:

```python
"""Tests for AI CLI configuration."""
import os
from unittest.mock import patch

import pytest


def test_ai_config_defaults():
    """AIConfig has correct default values."""
    from scripts.ai_config import AIConfig

    config = AIConfig()
    assert config.hf_user == "damBruh"
    assert config.base_model == "stabilityai/stable-diffusion-xl-base-1.0"
    assert config.steps == 1000
    assert config.resolution == 1024
    assert config.learning_rate == 1e-4
    assert config.trainer_space == "damBruh/skyyrose-lora-trainer"


def test_ai_config_get_hf_token_from_env():
    """get_hf_token() reads HF_TOKEN from environment."""
    from scripts.ai_config import AIConfig

    config = AIConfig()
    with patch.dict(os.environ, {"HF_TOKEN": "hf_test123"}):
        assert config.get_hf_token() == "hf_test123"


def test_ai_config_get_hf_token_missing_raises():
    """get_hf_token() raises when token not set."""
    from scripts.ai_config import AIConfig

    config = AIConfig()
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("HF_TOKEN", None)
        with pytest.raises(ValueError, match="HF_TOKEN"):
            config.get_hf_token()


def test_ai_config_get_replicate_token():
    """get_replicate_token() reads REPLICATE_API_TOKEN from environment."""
    from scripts.ai_config import AIConfig

    config = AIConfig()
    with patch.dict(os.environ, {"REPLICATE_API_TOKEN": "r8_test456"}):
        assert config.get_replicate_token() == "r8_test456"


def test_ai_config_override():
    """AIConfig fields can be overridden."""
    from scripts.ai_config import AIConfig

    config = AIConfig(steps=500, resolution=512)
    assert config.steps == 500
    assert config.resolution == 512
    # Other defaults remain
    assert config.hf_user == "damBruh"
```

**Step 2: Run tests — verify they fail**

Run: `pytest tests/scripts/test_ai_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.ai_config'`

**Step 3: Write `scripts/ai_config.py`**

```python
"""AI CLI configuration and constants."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class AIConfig:
    """Central configuration for the AI CLI."""

    # HuggingFace
    hf_user: str = "damBruh"
    hf_token_env: str = "HF_TOKEN"

    # Replicate
    replicate_token_env: str = "REPLICATE_API_TOKEN"

    # Training defaults
    base_model: str = "stabilityai/stable-diffusion-xl-base-1.0"
    vae_model: str = "madebyollin/sdxl-vae-fp16-fix"
    dataset: str = "damBruh/skyyrose-lora-dataset-v5"
    output_repo: str = "damBruh/skyyrose-lora-v1"
    trigger_word: str = "skyyrose luxury fashion"

    # Training hyperparams
    steps: int = 1000
    resolution: int = 1024
    learning_rate: float = 1e-4
    batch_size: int = 1
    gradient_accumulation: int = 3
    seed: int = 0

    # Spaces
    trainer_space: str = "damBruh/skyyrose-lora-trainer"
    default_gpu: str = "t4-medium"

    def get_hf_token(self) -> str:
        """Get HF token from environment, raise if missing."""
        token = os.environ.get(self.hf_token_env)
        if not token:
            raise ValueError(
                f"{self.hf_token_env} not set. "
                "Run: export HF_TOKEN=hf_..."
            )
        return token

    def get_replicate_token(self) -> str:
        """Get Replicate token from environment, raise if missing."""
        token = os.environ.get(self.replicate_token_env)
        if not token:
            raise ValueError(
                f"{self.replicate_token_env} not set. "
                "Run: export REPLICATE_API_TOKEN=r8_..."
            )
        return token
```

**Step 4: Ensure `scripts/__init__.py` exists**

Create `scripts/__init__.py` (empty) if it doesn't exist, so `scripts` is importable.

**Step 5: Run tests — verify they pass**

Run: `pytest tests/scripts/test_ai_config.py -v`
Expected: 5 passed

**Step 6: Commit**

```bash
git add scripts/__init__.py scripts/ai_config.py tests/scripts/__init__.py tests/scripts/test_ai_config.py
git commit -m "feat(scripts): add AI CLI config module (ai_config.py)"
```

---

## Task 2: Provider abstraction (`ai_providers.py`)

**Files:**
- Create: `scripts/ai_providers.py`
- Test: `tests/scripts/test_ai_providers.py`

**Step 1: Write failing tests**

```python
"""Tests for AI training providers."""
from unittest.mock import MagicMock, patch

import pytest

from scripts.ai_config import AIConfig


def test_provider_registry_has_both_providers():
    """PROVIDERS dict contains 'replicate' and 'hf'."""
    from scripts.ai_providers import PROVIDERS

    assert "replicate" in PROVIDERS
    assert "hf" in PROVIDERS


def test_replicate_provider_start_training():
    """ReplicateProvider.start_training calls replicate.trainings.create."""
    from scripts.ai_providers import ReplicateProvider

    provider = ReplicateProvider()
    config = AIConfig()

    mock_training = MagicMock()
    mock_training.id = "train_abc123"

    with patch.dict("os.environ", {"REPLICATE_API_TOKEN": "r8_test"}):
        with patch("scripts.ai_providers.replicate") as mock_rep:
            mock_rep.trainings.create.return_value = mock_training
            job_id = provider.start_training(config)

    assert job_id == "train_abc123"
    mock_rep.trainings.create.assert_called_once()


def test_replicate_provider_get_status():
    """ReplicateProvider.get_status returns dict with status/progress."""
    from scripts.ai_providers import ReplicateProvider

    provider = ReplicateProvider()

    mock_training = MagicMock()
    mock_training.status = "processing"
    mock_training.logs = "Step 100/1000"

    with patch.dict("os.environ", {"REPLICATE_API_TOKEN": "r8_test"}):
        with patch("scripts.ai_providers.replicate") as mock_rep:
            mock_rep.trainings.get.return_value = mock_training
            status = provider.get_status("train_abc123")

    assert status["status"] == "processing"
    assert "logs" in status


def test_hf_provider_start_training():
    """HuggingFaceProvider.start_training deploys Space and triggers training."""
    from scripts.ai_providers import HuggingFaceProvider

    provider = HuggingFaceProvider()
    config = AIConfig()

    with patch.dict("os.environ", {"HF_TOKEN": "hf_test"}):
        with patch("scripts.ai_providers.HfApi") as mock_api_cls:
            mock_api = mock_api_cls.return_value
            mock_api.get_space_runtime.return_value = MagicMock(stage="RUNNING")

            with patch("scripts.ai_providers.Client") as mock_client_cls:
                mock_client = mock_client_cls.return_value
                mock_client.predict.return_value = "Training complete"

                job_id = provider.start_training(config)

    assert job_id == config.trainer_space


def test_hf_provider_get_status():
    """HuggingFaceProvider.get_status checks Space runtime."""
    from scripts.ai_providers import HuggingFaceProvider

    provider = HuggingFaceProvider()
    mock_runtime = MagicMock()
    mock_runtime.stage = "RUNNING"
    mock_runtime.hardware = "t4-medium"

    with patch.dict("os.environ", {"HF_TOKEN": "hf_test"}):
        with patch("scripts.ai_providers.HfApi") as mock_api_cls:
            mock_api = mock_api_cls.return_value
            mock_api.get_space_runtime.return_value = mock_runtime

            status = provider.get_status("damBruh/skyyrose-lora-trainer")

    assert status["status"] == "RUNNING"
    assert status["hardware"] == "t4-medium"
```

**Step 2: Run tests — verify they fail**

Run: `pytest tests/scripts/test_ai_providers.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write `scripts/ai_providers.py`**

```python
"""Training providers for AI CLI — HuggingFace and Replicate."""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Iterator

from scripts.ai_config import AIConfig


class TrainingProvider(ABC):
    """Abstract base for training compute providers."""

    @abstractmethod
    def start_training(self, config: AIConfig) -> str:
        """Start training, return job ID."""

    @abstractmethod
    def get_status(self, job_id: str) -> dict:
        """Return {status, progress, logs, hardware}."""

    @abstractmethod
    def get_logs(self, job_id: str) -> Iterator[str]:
        """Stream training log lines."""


class ReplicateProvider(TrainingProvider):
    """Fast A100 training via Replicate API."""

    def start_training(self, config: AIConfig) -> str:
        import replicate

        os.environ["REPLICATE_API_TOKEN"] = config.get_replicate_token()

        training = replicate.trainings.create(
            model="stability-ai/sdxl",
            version="39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            input={
                "input_images": f"https://huggingface.co/datasets/{config.dataset}/resolve/main/data.zip",
                "token_string": "TOK",
                "caption_prefix": f"{config.trigger_word} ",
                "max_train_steps": config.steps,
                "use_face_detection_instead": False,
                "resolution": config.resolution,
                "seed": config.seed,
            },
            destination=f"{config.hf_user}/skyyrose-lora-replicate",
        )
        return training.id

    def get_status(self, job_id: str) -> dict:
        import replicate

        training = replicate.trainings.get(job_id)
        return {
            "status": training.status,
            "logs": training.logs or "",
        }

    def get_logs(self, job_id: str) -> Iterator[str]:
        import replicate

        training = replicate.trainings.get(job_id)
        if training.logs:
            yield from training.logs.splitlines()


class HuggingFaceProvider(TrainingProvider):
    """Managed training via HF Spaces + gradio_client."""

    def start_training(self, config: AIConfig) -> str:
        from gradio_client import Client
        from huggingface_hub import HfApi

        token = config.get_hf_token()
        api = HfApi(token=token)

        # Check Space is running
        runtime = api.get_space_runtime(config.trainer_space)
        if runtime.stage != "RUNNING":
            api.restart_space(config.trainer_space)

        # Trigger training via Gradio API
        client = Client(config.trainer_space, hf_token=token)
        client.predict(api_name="/predict")

        return config.trainer_space

    def get_status(self, job_id: str) -> dict:
        from huggingface_hub import HfApi

        token = os.environ.get("HF_TOKEN", "")
        api = HfApi(token=token)
        runtime = api.get_space_runtime(job_id)

        return {
            "status": runtime.stage,
            "hardware": getattr(runtime, "hardware", "unknown"),
        }

    def get_logs(self, job_id: str) -> Iterator[str]:
        from huggingface_hub import HfApi

        token = os.environ.get("HF_TOKEN", "")
        api = HfApi(token=token)

        for log_entry in api.get_space_runtime(job_id).raw.get("logs", []):
            yield log_entry


PROVIDERS: dict[str, TrainingProvider] = {
    "replicate": ReplicateProvider(),
    "hf": HuggingFaceProvider(),
}
```

**Step 4: Run tests — verify they pass**

Run: `pytest tests/scripts/test_ai_providers.py -v`
Expected: 5 passed

**Step 5: Commit**

```bash
git add scripts/ai_providers.py tests/scripts/test_ai_providers.py
git commit -m "feat(scripts): add training providers (Replicate + HF)"
```

---

## Task 3: Space template (`ai_templates.py`)

**Files:**
- Create: `scripts/ai_templates.py`
- Test: `tests/scripts/test_ai_templates.py`

**Step 1: Write failing tests**

```python
"""Tests for AI Space templates."""
from scripts.ai_config import AIConfig


def test_render_trainer_template_contains_dataset():
    """Rendered template includes the configured dataset name."""
    from scripts.ai_templates import render_trainer_app

    config = AIConfig(dataset="damBruh/skyyrose-lora-dataset-v5")
    rendered = render_trainer_app(config)

    assert "damBruh/skyyrose-lora-dataset-v5" in rendered
    assert "gradio" in rendered.lower()


def test_render_trainer_template_respects_steps():
    """Rendered template uses configured step count."""
    from scripts.ai_templates import render_trainer_app

    config = AIConfig(steps=500)
    rendered = render_trainer_app(config)

    assert "--max_train_steps=500" in rendered


def test_render_trainer_template_respects_resolution():
    """Rendered template uses configured resolution."""
    from scripts.ai_templates import render_trainer_app

    config = AIConfig(resolution=512)
    rendered = render_trainer_app(config)

    assert "--resolution=512" in rendered


def test_render_requirements():
    """render_requirements() returns valid requirements.txt content."""
    from scripts.ai_templates import render_requirements

    reqs = render_requirements()

    assert "gradio" in reqs
    assert "huggingface_hub" in reqs
    assert "torch" in reqs
```

**Step 2: Run tests — verify they fail**

Run: `pytest tests/scripts/test_ai_templates.py -v`
Expected: FAIL

**Step 3: Write `scripts/ai_templates.py`**

This file embeds the proven working `app.py` template from `/tmp/hf-spaces/skyyrose-lora-trainer/app.py` as a Python string with `.format()` placeholders for configurable values (dataset, steps, resolution, output_repo, base_model, vae_model, learning_rate, gradient_accumulation, seed).

The `render_trainer_app(config: AIConfig) -> str` function substitutes config values into the template.

The `render_requirements() -> str` function returns the requirements.txt content.

```python
"""Embedded HF Space templates for AI CLI."""
from __future__ import annotations

from scripts.ai_config import AIConfig

TRAINER_APP_TEMPLATE = '''import gradio as gr
import subprocess
import sys
import os


def install_dependencies():
    """Install training dependencies."""
    deps = [
        "diffusers[torch]", "transformers", "accelerate",
        "peft", "bitsandbytes", "datasets", "torchvision"
    ]
    for dep in deps:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", dep],
            check=True
        )


def train_lora(progress=gr.Progress()):
    """Run LoRA training on persistent GPU."""
    logs = []
    try:
        if 'OMP_NUM_THREADS' in os.environ:
            del os.environ['OMP_NUM_THREADS']
        os.environ['OMP_NUM_THREADS'] = '4'
        logs.append("Environment configured")
        yield "\\n".join(logs)

        progress(0.05, desc="Installing dependencies...")
        install_dependencies()
        logs.append("Dependencies installed")
        yield "\\n".join(logs)

        progress(0.1, desc="Downloading training script...")
        import requests
        script_url = "https://raw.githubusercontent.com/huggingface/diffusers/v0.36.0/examples/text_to_image/train_text_to_image_lora_sdxl.py"
        response = requests.get(script_url)
        with open("train_text_to_image_lora_sdxl.py", "w") as f:
            f.write(response.text)
        logs.append("Training script ready")
        yield "\\n".join(logs)

        progress(0.15, desc="Configuring accelerate...")
        subprocess.run(["accelerate", "config", "default"], check=True)
        logs.append("Accelerate configured")
        yield "\\n".join(logs)

        progress(0.2, desc="Starting LoRA training...")
        output_dir = "lora-output"
        train_cmd = [
            "accelerate", "launch", "train_text_to_image_lora_sdxl.py",
            "--pretrained_model_name_or_path={base_model}",
            "--pretrained_vae_model_name_or_path={vae_model}",
            "--dataset_name={dataset}",
            "--image_column=image",
            "--caption_column=text",
            f"--output_dir={{output_dir}}",
            "--mixed_precision=fp16",
            "--resolution={resolution}",
            "--train_batch_size=1",
            "--gradient_accumulation_steps={gradient_accumulation}",
            "--gradient_checkpointing",
            "--learning_rate={learning_rate}",
            "--snr_gamma=5.0",
            "--lr_scheduler=constant",
            "--lr_warmup_steps=0",
            "--use_8bit_adam",
            "--max_train_steps={steps}",
            "--checkpointing_steps=500",
            "--seed={seed}",
        ]

        process = subprocess.Popen(
            train_cmd, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, bufsize=1
        )
        for line in process.stdout:
            line = line.strip()
            if line:
                logs.append(line)
                if len(logs) > 100:
                    logs = logs[-100:]
                yield "\\n".join(logs)
        process.wait()

        if process.returncode != 0:
            logs.append(f"Training failed (exit {{process.returncode}})")
            yield "\\n".join(logs)
            return

        progress(0.92, desc="Uploading to Hub...")
        from huggingface_hub import HfApi
        hub_api = HfApi(token=os.environ.get("HF_TOKEN", ""))
        hub_api.create_repo("{output_repo}", exist_ok=True)
        hub_api.upload_folder(
            folder_path=output_dir,
            repo_id="{output_repo}",
            commit_message="LoRA trained on {dataset} ({steps} steps, SDXL, {resolution}px)"
        )

        progress(1.0, desc="Done!")
        logs.append("TRAINING COMPLETE")
        logs.append("Model: https://huggingface.co/{output_repo}")
    except Exception as e:
        logs.append(f"Error: {{e}}")
    yield "\\n".join(logs)


demo = gr.Interface(
    fn=train_lora, inputs=[],
    outputs=gr.Textbox(label="Training Progress", lines=30, max_lines=50, show_copy_button=True),
    title="SkyyRose LoRA Training",
    description="LoRA training for SkyyRose. Dataset: {dataset}. Trigger: {trigger_word}",
    api_name="predict"
)
demo.queue().launch()
'''

REQUIREMENTS_TEMPLATE = """gradio==5.50.0
huggingface_hub>=0.28.0
requests>=2.32.0
torch>=2.1.0
accelerate>=1.0.0
diffusers[torch]>=0.31.0
transformers>=4.47.0
peft>=0.14.0
bitsandbytes>=0.45.0
datasets>=3.2.0
torchvision>=0.20.0
"""


def render_trainer_app(config: AIConfig) -> str:
    """Render the trainer Space app.py with config values."""
    return TRAINER_APP_TEMPLATE.format(
        base_model=config.base_model,
        vae_model=config.vae_model,
        dataset=config.dataset,
        resolution=config.resolution,
        gradient_accumulation=config.gradient_accumulation,
        learning_rate=config.learning_rate,
        steps=config.steps,
        seed=config.seed,
        output_repo=config.output_repo,
        trigger_word=config.trigger_word,
    )


def render_requirements() -> str:
    """Render requirements.txt for trainer Space."""
    return REQUIREMENTS_TEMPLATE
```

**Step 4: Run tests — verify they pass**

Run: `pytest tests/scripts/test_ai_templates.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add scripts/ai_templates.py tests/scripts/test_ai_templates.py
git commit -m "feat(scripts): add embedded Space templates (ai_templates.py)"
```

---

## Task 4: CLI entrypoint — `spaces` subcommand

**Files:**
- Create: `scripts/ai.py`
- Test: `tests/scripts/test_ai_cli_spaces.py`

**Step 1: Write failing tests**

```python
"""Tests for AI CLI spaces subcommand."""
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

runner = CliRunner()


def test_spaces_list():
    """spaces list shows damBruh Spaces."""
    from scripts.ai import app

    mock_space_1 = MagicMock()
    mock_space_1.id = "damBruh/skyyrose-lora-trainer"
    mock_space_2 = MagicMock()
    mock_space_2.id = "damBruh/skyyrose-3d-converter"

    with patch.dict("os.environ", {"HF_TOKEN": "hf_test"}):
        with patch("scripts.ai.HfApi") as mock_api_cls:
            mock_api = mock_api_cls.return_value
            mock_api.list_spaces.return_value = [mock_space_1, mock_space_2]

            result = runner.invoke(app, ["spaces", "list"])

    assert result.exit_code == 0
    assert "skyyrose-lora-trainer" in result.stdout


def test_spaces_status():
    """spaces status shows runtime info."""
    from scripts.ai import app

    mock_runtime = MagicMock()
    mock_runtime.stage = "RUNNING"
    mock_runtime.hardware = MagicMock()
    mock_runtime.hardware.current = "t4-medium"
    mock_runtime.hardware.requested = "t4-medium"

    with patch.dict("os.environ", {"HF_TOKEN": "hf_test"}):
        with patch("scripts.ai.HfApi") as mock_api_cls:
            mock_api = mock_api_cls.return_value
            mock_api.get_space_runtime.return_value = mock_runtime

            result = runner.invoke(app, ["spaces", "status", "skyyrose-lora-trainer"])

    assert result.exit_code == 0
    assert "RUNNING" in result.stdout


def test_spaces_restart():
    """spaces restart calls restart_space API."""
    from scripts.ai import app

    with patch.dict("os.environ", {"HF_TOKEN": "hf_test"}):
        with patch("scripts.ai.HfApi") as mock_api_cls:
            mock_api = mock_api_cls.return_value
            result = runner.invoke(app, ["spaces", "restart", "skyyrose-lora-trainer"])

    assert result.exit_code == 0
    mock_api.restart_space.assert_called_once()
```

**Step 2: Run tests — verify they fail**

Run: `pytest tests/scripts/test_ai_cli_spaces.py -v`
Expected: FAIL

**Step 3: Write `scripts/ai.py` with spaces subcommand**

```python
#!/usr/bin/env python3
"""Unified AI CLI for SkyyRose — training, datasets, Spaces, models."""
from __future__ import annotations

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

    # Create Space if needed
    api.create_repo(repo_id, repo_type="space", space_sdk="gradio", exist_ok=True)

    # Upload app.py
    app_content = render_trainer_app(config)
    api.upload_file(
        path_or_fileobj=app_content.encode(),
        path_in_repo="app.py",
        repo_id=repo_id,
        repo_type="space",
        commit_message="Deploy trainer app via AI CLI",
    )

    # Upload requirements.txt
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
```

**Step 4: Run tests — verify they pass**

Run: `pytest tests/scripts/test_ai_cli_spaces.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add scripts/ai.py tests/scripts/test_ai_cli_spaces.py
git commit -m "feat(scripts): add AI CLI with spaces subcommand"
```

---

## Task 5: CLI — `train` subcommand

**Files:**
- Modify: `scripts/ai.py`
- Test: `tests/scripts/test_ai_cli_train.py`

**Step 1: Write failing tests**

```python
"""Tests for AI CLI train subcommand."""
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

runner = CliRunner()


def test_train_run_replicate():
    """train run --provider replicate starts Replicate training."""
    from scripts.ai import app

    with patch.dict("os.environ", {"REPLICATE_API_TOKEN": "r8_test"}):
        with patch("scripts.ai_providers.replicate") as mock_rep:
            mock_training = MagicMock()
            mock_training.id = "train_abc123"
            mock_rep.trainings.create.return_value = mock_training

            result = runner.invoke(app, ["train", "run", "--provider", "replicate"])

    assert result.exit_code == 0
    assert "train_abc123" in result.stdout


def test_train_run_hf():
    """train run --provider hf triggers HF Space training."""
    from scripts.ai import app

    with patch.dict("os.environ", {"HF_TOKEN": "hf_test"}):
        with patch("scripts.ai.HfApi") as mock_api_cls:
            mock_api = mock_api_cls.return_value
            mock_runtime = MagicMock()
            mock_runtime.stage = "RUNNING"
            mock_api.get_space_runtime.return_value = mock_runtime

            with patch("scripts.ai_providers.HfApi", return_value=mock_api):
                with patch("scripts.ai_providers.Client") as mock_client_cls:
                    mock_client = mock_client_cls.return_value
                    mock_client.predict.return_value = "done"

                    result = runner.invoke(app, ["train", "run", "--provider", "hf"])

    assert result.exit_code == 0


def test_train_status_replicate():
    """train status shows Replicate training status."""
    from scripts.ai import app

    with patch.dict("os.environ", {"REPLICATE_API_TOKEN": "r8_test"}):
        with patch("scripts.ai_providers.replicate") as mock_rep:
            mock_training = MagicMock()
            mock_training.status = "succeeded"
            mock_training.logs = "Step 1000/1000"
            mock_rep.trainings.get.return_value = mock_training

            result = runner.invoke(
                app, ["train", "status", "--provider", "replicate", "--job-id", "train_abc123"]
            )

    assert result.exit_code == 0
    assert "succeeded" in result.stdout


def test_train_run_invalid_provider():
    """train run with invalid provider shows error."""
    from scripts.ai import app

    result = runner.invoke(app, ["train", "run", "--provider", "invalid"])
    assert result.exit_code != 0
```

**Step 2: Run tests — verify they fail**

Run: `pytest tests/scripts/test_ai_cli_train.py -v`
Expected: FAIL

**Step 3: Add train subcommand to `scripts/ai.py`**

Add after the spaces section:

```python
from scripts.ai_providers import PROVIDERS

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
```

**Step 4: Run tests — verify they pass**

Run: `pytest tests/scripts/test_ai_cli_train.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add scripts/ai.py scripts/ai_providers.py tests/scripts/test_ai_cli_train.py
git commit -m "feat(scripts): add train subcommand to AI CLI"
```

---

## Task 6: CLI — `dataset` subcommand

**Files:**
- Modify: `scripts/ai.py`
- Test: `tests/scripts/test_ai_cli_dataset.py`

**Step 1: Write failing tests**

```python
"""Tests for AI CLI dataset subcommand."""
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

runner = CliRunner()


def test_dataset_info():
    """dataset info shows dataset metadata."""
    from scripts.ai import app

    mock_info = MagicMock()
    mock_info.id = "damBruh/skyyrose-lora-dataset-v5"
    mock_info.downloads = 42
    mock_info.card_data = MagicMock()
    mock_info.card_data.size_categories = ["n<1K"]
    mock_info.siblings = [MagicMock(rfilename=f"img_{i}.png") for i in range(78)]

    with patch.dict("os.environ", {"HF_TOKEN": "hf_test"}):
        with patch("scripts.ai.HfApi") as mock_api_cls:
            mock_api = mock_api_cls.return_value
            mock_api.dataset_info.return_value = mock_info

            result = runner.invoke(app, ["dataset", "info", "skyyrose-lora-dataset-v5"])

    assert result.exit_code == 0
    assert "skyyrose-lora-dataset-v5" in result.stdout


def test_dataset_push():
    """dataset push uploads folder to Hub."""
    from scripts.ai import app

    with patch.dict("os.environ", {"HF_TOKEN": "hf_test"}):
        with patch("scripts.ai.HfApi") as mock_api_cls:
            mock_api = mock_api_cls.return_value
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.iterdir", return_value=[]):
                    result = runner.invoke(
                        app,
                        ["dataset", "push", "--source", "/tmp/test-data", "--name", "test-dataset-v1"],
                    )

    assert result.exit_code == 0
    mock_api.create_repo.assert_called_once()
```

**Step 2: Run tests — verify they fail**

Run: `pytest tests/scripts/test_ai_cli_dataset.py -v`

**Step 3: Add dataset subcommand to `scripts/ai.py`**

```python
from pathlib import Path

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
        commit_message=f"Upload dataset via AI CLI",
    )
    console.print(f"[green]Pushed to {repo_id}[/green]")
    console.print(f"  https://huggingface.co/datasets/{repo_id}")
```

**Step 4: Run tests — verify they pass**

Run: `pytest tests/scripts/test_ai_cli_dataset.py -v`
Expected: 2 passed

**Step 5: Commit**

```bash
git add scripts/ai.py tests/scripts/test_ai_cli_dataset.py
git commit -m "feat(scripts): add dataset subcommand to AI CLI"
```

---

## Task 7: CLI — `model` subcommand

**Files:**
- Modify: `scripts/ai.py`
- Test: `tests/scripts/test_ai_cli_model.py`

**Step 1: Write failing tests**

```python
"""Tests for AI CLI model subcommand."""
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

runner = CliRunner()


def test_model_list():
    """model list shows damBruh models."""
    from scripts.ai import app

    mock_model = MagicMock()
    mock_model.id = "damBruh/skyyrose-lora-v1"
    mock_model.downloads = 5
    mock_model.tags = ["lora"]

    with patch.dict("os.environ", {"HF_TOKEN": "hf_test"}):
        with patch("scripts.ai.HfApi") as mock_api_cls:
            mock_api = mock_api_cls.return_value
            mock_api.list_models.return_value = [mock_model]

            result = runner.invoke(app, ["model", "list"])

    assert result.exit_code == 0
    assert "skyyrose-lora-v1" in result.stdout


def test_model_info():
    """model info shows model details."""
    from scripts.ai import app

    mock_info = MagicMock()
    mock_info.id = "damBruh/skyyrose-lora-v1"
    mock_info.downloads = 5
    mock_info.siblings = [MagicMock(rfilename="pytorch_lora_weights.safetensors", size=50_000_000)]

    with patch.dict("os.environ", {"HF_TOKEN": "hf_test"}):
        with patch("scripts.ai.HfApi") as mock_api_cls:
            mock_api = mock_api_cls.return_value
            mock_api.model_info.return_value = mock_info

            result = runner.invoke(app, ["model", "info", "skyyrose-lora-v1"])

    assert result.exit_code == 0
    assert "skyyrose-lora-v1" in result.stdout


def test_model_download():
    """model download calls snapshot_download."""
    from scripts.ai import app

    with patch.dict("os.environ", {"HF_TOKEN": "hf_test"}):
        with patch("scripts.ai.snapshot_download") as mock_download:
            mock_download.return_value = "/tmp/models/skyyrose-lora-v1"

            result = runner.invoke(app, ["model", "download", "skyyrose-lora-v1"])

    assert result.exit_code == 0
    mock_download.assert_called_once()
```

**Step 2: Run tests — verify they fail**

Run: `pytest tests/scripts/test_ai_cli_model.py -v`

**Step 3: Add model subcommand to `scripts/ai.py`**

```python
from huggingface_hub import snapshot_download

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
def model_download(name: str, output: str = typer.Option("./models", help="Local output directory")):
    """Download model from Hub to local directory."""
    repo_id = f"{config.hf_user}/{name}" if "/" not in name else name
    local_dir = snapshot_download(
        repo_id=repo_id,
        local_dir=f"{output}/{name}",
        token=config.get_hf_token(),
    )
    console.print(f"[green]Downloaded to {local_dir}[/green]")
```

**Step 4: Run tests — verify they pass**

Run: `pytest tests/scripts/test_ai_cli_model.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add scripts/ai.py tests/scripts/test_ai_cli_model.py
git commit -m "feat(scripts): add model subcommand to AI CLI"
```

---

## Task 8: Install dependencies and smoke test

**Files:**
- Modify: `requirements.txt` or `pyproject.toml` (add typer, replicate, gradio_client if missing)

**Step 1: Install CLI dependencies**

```bash
pip install "typer[all]>=0.15.0" "replicate>=1.0.0" "gradio_client>=1.0.0"
```

**Step 2: Run full test suite**

```bash
pytest tests/scripts/ -v --tb=short
```

Expected: All tests pass (17+ tests across 5 files)

**Step 3: Manual smoke test**

```bash
# Should show help
python scripts/ai.py --help

# Should show subcommands
python scripts/ai.py spaces --help
python scripts/ai.py train --help
python scripts/ai.py dataset --help
python scripts/ai.py model --help
```

**Step 4: Live smoke test (requires tokens)**

```bash
# List Spaces (needs HF_TOKEN)
python scripts/ai.py spaces list

# Check model repo
python scripts/ai.py model info skyyrose-lora-v1
```

**Step 5: Commit**

```bash
git add -A
git commit -m "feat(scripts): complete AI CLI v1 with all subcommands"
```

---

## Summary

| Task | What | Tests | Files |
|------|------|-------|-------|
| 1 | Config module | 5 | `ai_config.py` |
| 2 | Provider abstraction | 5 | `ai_providers.py` |
| 3 | Space templates | 4 | `ai_templates.py` |
| 4 | CLI + spaces | 3 | `ai.py` |
| 5 | Train subcommand | 4 | `ai.py` (modify) |
| 6 | Dataset subcommand | 2 | `ai.py` (modify) |
| 7 | Model subcommand | 3 | `ai.py` (modify) |
| 8 | Install + smoke test | — | deps |
| **Total** | | **26 tests** | **4 files** |

**Total estimated commits:** 8
**Key dependency chain:** Task 1 → Task 2 → Task 3 → Task 4 → Tasks 5-7 (parallel) → Task 8
