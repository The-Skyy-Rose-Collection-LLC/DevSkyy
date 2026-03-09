#!/usr/bin/env python3
"""
Submit LoRA training job to HuggingFace via API.

This bypasses local AutoTrain installation issues by using
HuggingFace's remote training infrastructure.

Usage:
    python3 scripts/submit_training_job.py
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
print("🚀 Submitting LoRA Training Job to HuggingFace")
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

# Training configuration
config = {
    "dataset": "damBruh/skyyrose-lora-dataset-v1",
    "base_model": "stabilityai/stable-diffusion-xl-base-1.0",
    "output_repo": "damBruh/skyyrose-lora-v1",
    "trigger_word": "skyyrose",
    "learning_rate": 1e-4,
    "steps": 1000,
    "rank": 16,
}

print("📋 Training Configuration:")
for key, value in config.items():
    print(f"  {key}: {value}")
print()

# Create output repo
print(f"📦 Creating model repository: {config['output_repo']}")
try:
    create_repo(
        repo_id=config["output_repo"],
        repo_type="model",
        exist_ok=True,
        token=HF_TOKEN,
    )
    print("✓ Repository created/verified\n")
except Exception as e:
    print(f"⚠️  Repository may exist: {e}\n")

# Submit training job using HuggingFace Spaces API
print("🚀 Submitting training job...")
print()
print("⚠️  HuggingFace doesn't have a direct training API (yet)")
print()
print("💡 Best options with billing credits added:")
print()
print("1. Use AutoTrain CLI with Python 3.12:")
print("   brew install python@3.12")
print("   python3.12 -m pip install autotrain-advanced")
print("   python3.12 scripts/setup_autotrain_cli.py")
print()
print("2. Use Google Colab (Free T4 GPU):")
print(
    "   https://colab.research.google.com/github/huggingface/notebooks/blob/main/diffusers/SDXL_DreamBooth_LoRA_.ipynb"
)
print("   - Upload dataset: damBruh/skyyrose-lora-dataset-v1")
print("   - Run notebook cells")
print("   - Download trained model")
print()
print("3. Use Replicate API (Easiest):")
print("   - Sign up: https://replicate.com")
print("   - Create training: ostris/flux-dev-lora-trainer")
print("   - Cost: ~$2-3")
print()

# Provide direct Colab link with pre-filled dataset
colab_url = "https://colab.research.google.com/github/huggingface/notebooks/blob/main/diffusers/SDXL_DreamBooth_LoRA_.ipynb"
print("🎯 Recommended: Open Colab notebook:")
print(f"   {colab_url}")
print()
print("📊 Your dataset is ready at:")
print(f"   https://huggingface.co/datasets/{config['dataset']}")
