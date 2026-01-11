#!/usr/bin/env python3
"""
Create AutoTrain Space on HuggingFace (No Local Dependencies).

This creates a Space that will run the training on HuggingFace infrastructure,
avoiding local Python dependency issues.

Usage:
    python3 scripts/setup_autotrain_space.py
"""

import os
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(project_root / ".env")

HF_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")

if not HF_TOKEN:
    print("❌ HUGGINGFACE_API_TOKEN not set in .env")
    sys.exit(1)

print("=" * 70)
print("🚀 Creating AutoTrain Space on HuggingFace")
print("=" * 70)
print()

try:
    from huggingface_hub import HfApi, create_repo
except ImportError:
    print("Installing minimal dependencies...")
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub"], check=True)
    from huggingface_hub import HfApi, create_repo

api = HfApi()

# Create Space for training
space_name = "skyyrose-lora-trainer"
space_id = f"damBruh/{space_name}"

print(f"📦 Creating Space: {space_id}")

try:
    create_repo(
        repo_id=space_id,
        repo_type="space",
        space_sdk="gradio",
        space_hardware="t4-small",  # T4 GPU
        exist_ok=True,
        token=HF_TOKEN,
    )
    print(f"✓ Space created: https://huggingface.co/spaces/{space_id}\n")
except Exception as e:
    print(f"⚠️  Space may already exist: {e}\n")

# Create app.py for the Space
app_code = '''import gradio as gr
import os
from huggingface_hub import  # noqa: E402
from huggingface_hub import snapshot_download
import subprocess
import sys

def start_training(
    dataset_id="damBruh/skyyrose-lora-dataset-v1",
    trigger_word="skyyrose",
    learning_rate=1e-4,
    epochs=100,
):
    """Start LoRA training."""

    status_log = []

    try:
        # Install AutoTrain
        status_log.append("📦 Installing AutoTrain Advanced...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "autotrain-advanced"],
            check=True,
            capture_output=True
        )
        status_log.append("✓ AutoTrain installed")

        # Download dataset
        status_log.append(f"📥 Downloading dataset: {dataset_id}")
        dataset_path = snapshot_download(
            repo_id=dataset_id,
            repo_type="dataset",
            token=os.environ.get("HF_TOKEN")
        )
        status_log.append(f"✓ Dataset downloaded to: {dataset_path}")

        # Start training
        status_log.append("🚀 Starting LoRA training...")

        cmd = [
            "autotrain", "dreambooth",
            "--model", "stabilityai/stable-diffusion-xl-base-1.0",
            "--project-name", "skyyrose-lora-v1",
            "--image-path", dataset_path,
            "--prompt", f"{trigger_word} luxury fashion",
            "--learning-rate", str(learning_rate),
            "--num-steps", "1000",
            "--batch-size", "1",
            "--resolution", "512",
            "--rank", "16",
            "--push-to-hub",
        ]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        # Stream output
        for line in process.stdout:
            status_log.append(line.strip())
            yield "\\n".join(status_log)

        process.wait()

        if process.returncode == 0:
            status_log.append("\\n✅ Training Complete!")
            status_log.append("Model: damBruh/skyyrose-lora-v1")
        else:
            status_log.append(f"\\n❌ Training failed with code {process.returncode}")

    except Exception as e:
        status_log.append(f"\\n❌ Error: {e}")

    return "\\n".join(status_log)


# Gradio Interface
with gr.Blocks(title="SkyyRose LoRA Trainer") as demo:
    gr.Markdown("# 🚀 SkyyRose LoRA Training")
    gr.Markdown("Train a custom LoRA model for SkyyRose luxury fashion brand")

    with gr.Row():
        dataset_input = gr.Textbox(
            value="damBruh/skyyrose-lora-dataset-v1",
            label="Dataset ID"
        )
        trigger_input = gr.Textbox(
            value="skyyrose",
            label="Trigger Word"
        )

    with gr.Row():
        lr_input = gr.Number(value=1e-4, label="Learning Rate")
        epochs_input = gr.Number(value=100, label="Epochs")

    start_btn = gr.Button("🚀 Start Training", variant="primary")

    output = gr.Textbox(
        label="Training Progress",
        lines=20,
        max_lines=30
    )

    start_btn.click(
        start_training,
        inputs=[dataset_input, trigger_input, lr_input, epochs_input],
        outputs=output
    )

    gr.Markdown("⏱️ Training takes ~30-60 minutes on T4 GPU")

demo.launch()
'''

# Upload app.py to Space
print("📝 Creating app.py for training...")
api.upload_file(
    path_or_fileobj=app_code.encode(),
    path_in_repo="app.py",
    repo_id=space_id,
    repo_type="space",
    token=HF_TOKEN,
)

# Create requirements.txt
requirements = """gradio
huggingface_hub
autotrain-advanced
torch
diffusers
transformers
"""

api.upload_file(
    path_or_fileobj=requirements.encode(),
    path_in_repo="requirements.txt",
    repo_id=space_id,
    repo_type="space",
    token=HF_TOKEN,
)

# Create README
readme = """---
title: SkyyRose LoRA Trainer
emoji: 🎨
colorFrom: pink
colorTo: purple
sdk: gradio
sdk_version: 4.0.0
app_file: app.py
pinned: false
license: mit
---

# SkyyRose LoRA Training Space

Automated LoRA training for SkyyRose luxury fashion brand.

**Dataset**: damBruh/skyyrose-lora-dataset-v1 (95 images)
**Trigger Word**: skyyrose
**Base Model**: Stable Diffusion XL

Training will produce a LoRA model at: `damBruh/skyyrose-lora-v1`
"""

api.upload_file(
    path_or_fileobj=readme.encode(),
    path_in_repo="README.md",
    repo_id=space_id,
    repo_type="space",
    token=HF_TOKEN,
)

print("✅ Space Created Successfully!")
print("=" * 70)
print()
print(f"🌐 Space URL: https://huggingface.co/spaces/{space_id}")
print()
print("📋 Next Steps:")
print(f"  1. Open: https://huggingface.co/spaces/{space_id}")
print("  2. Wait for Space to build (~2-3 minutes)")
print("  3. Click '🚀 Start Training' button")
print("  4. Monitor progress in the Space interface")
print()
print("⏱️ Training will take 30-60 minutes on T4 GPU")
print("💰 Cost: ~$0.60-$1.00")
