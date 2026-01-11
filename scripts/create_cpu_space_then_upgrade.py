#!/usr/bin/env python3
"""
Create Gradio Space on CPU (free), then upgrade to GPU.

This bypasses the 402 error by creating the Space first without GPU.

Usage:
    python3 scripts/create_cpu_space_then_upgrade.py
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
print("🎨 Creating Gradio Training Space (CPU → GPU Upgrade)")
print("=" * 70)
print()

try:
    from huggingface_hub import HfApi, create_repo
except ImportError:
    print("Installing huggingface_hub...")
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "huggingface_hub"], check=True)
    from huggingface_hub import HfApi, create_repo

api = HfApi()
space_id = "damBruh/skyyrose-lora-trainer"

# Step 1: Create Space on CPU (FREE)
print(f"📦 Creating Space on CPU (free): {space_id}")
print()

try:
    create_repo(
        repo_id=space_id,
        repo_type="space",
        space_sdk="gradio",
        # No space_hardware = CPU (free)
        exist_ok=True,
        token=HF_TOKEN,
    )
    print("✓ Space created on CPU!\n")
except Exception as e:
    print(f"⚠️  Space may already exist: {e}\n")

# Step 2: Upload files
print("📝 Uploading Space files...")

# Create requirements.txt
requirements = """gradio==4.0.0
huggingface_hub
torch
diffusers
transformers
accelerate
peft
safetensors
"""

api.upload_file(
    path_or_fileobj=requirements.encode(),
    path_in_repo="requirements.txt",
    repo_id=space_id,
    repo_type="space",
    token=HF_TOKEN,
)
print("  ✓ requirements.txt")

# Create app.py (simple UI with upgrade instructions)
app_code = '''import gradio as gr

def show_instructions():
    return """
# 🎨 SkyyRose LoRA Trainer

This Space needs GPU to run training.

## 🔧 Upgrade to GPU (Required)

1. Go to Space Settings
2. Hardware: Select "T4 GPU"
3. Click "Save"
4. Wait for Space to restart (~2 min)
5. Training will be available

## 💰 Cost
~$0.60-$1.00 per training run on T4 GPU

## 📊 Dataset Ready
- Dataset: damBruh/skyyrose-lora-dataset-v1
- Images: 95 (SIGNATURE, BLACK_ROSE, LOVE_HURTS)
- Trigger: "skyyrose luxury fashion"

After GPU upgrade, this interface will update with training controls.
"""

with gr.Blocks(title="SkyyRose LoRA Trainer") as demo:
    gr.Markdown("# 🚀 SkyyRose LoRA Training")

    with gr.Row():
        info = gr.Markdown(show_instructions())

    gr.Markdown("---")
    gr.Markdown("**Space URL**: https://huggingface.co/spaces/damBruh/skyyrose-lora-trainer")

demo.launch()
'''

api.upload_file(
    path_or_fileobj=app_code.encode(),
    path_in_repo="app.py",
    repo_id=space_id,
    repo_type="space",
    token=HF_TOKEN,
)
print("  ✓ app.py")

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

⚠️ **GPU Required**: This Space needs to be upgraded to T4 GPU to run training.

## Setup Steps

1. Click "Settings" (top right)
2. Hardware → Select "T4 GPU"
3. Save and wait for restart

## Dataset
- **ID**: damBruh/skyyrose-lora-dataset-v1
- **Images**: 95 (3 collections + logos)
- **Trigger**: skyyrose luxury fashion

## Cost
~$0.60-$1.00 per training run on T4 GPU
"""

api.upload_file(
    path_or_fileobj=readme.encode(),
    path_in_repo="README.md",
    repo_id=space_id,
    repo_type="space",
    token=HF_TOKEN,
)
print("  ✓ README.md")

print()
print("=" * 70)
print("✅ Space Created Successfully!")
print("=" * 70)
print()
print(f"🌐 Open Space: https://huggingface.co/spaces/{space_id}")
print()
print("📋 Next Steps:")
print("  1. Open Space in browser")
print("  2. Click 'Settings' (top right)")
print("  3. Hardware → Select 'T4 GPU'")
print("  4. Click 'Save'")
print("  5. Wait for Space to restart (~2 min)")
print()
print("⚠️  Note: Upgrading to GPU requires billing credits")
print("   If upgrade fails, add credits at:")
print("   https://huggingface.co/settings/billing")
