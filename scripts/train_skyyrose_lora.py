#!/usr/bin/env python3
"""
SkyyRose LoRA Training Script

Run on any GPU environment (Colab, local, cloud):
    python3 scripts/train_skyyrose_lora.py

Requires: GPU with 16GB+ VRAM, CUDA
"""

import os
import subprocess
import sys
from pathlib import Path

# Configuration
CONFIG = {
    "model_name": "stabilityai/stable-diffusion-xl-base-1.0",
    "dataset_name": "damBruh/skyyrose-lora-dataset-v2",
    "output_dir": "./skyyrose-lora-output",
    "hub_model_id": "damBruh/skyyrose-lora-model-v2",
    "instance_prompt": "skyyrose luxury streetwear",
    "resolution": 1024,
    "train_batch_size": 1,
    "gradient_accumulation_steps": 4,
    "learning_rate": 1e-4,
    "lr_scheduler": "constant",
    "max_train_steps": 1000,
    "checkpointing_steps": 250,
    "seed": 42,
    "rank": 16,
}


def install_dependencies():
    """Install required packages."""
    packages = [
        "accelerate",
        "transformers",
        "diffusers[torch]",
        "datasets",
        "peft",
        "bitsandbytes",
        "wandb",
    ]
    print("📦 Installing dependencies...")
    for pkg in packages:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg])
    print("✓ Dependencies installed\n")


def download_training_script():
    """Download the official training script."""
    script_url = "https://raw.githubusercontent.com/huggingface/diffusers/main/examples/dreambooth/train_dreambooth_lora_sdxl.py"
    script_path = Path("train_dreambooth_lora_sdxl.py")

    if not script_path.exists():
        print("📥 Downloading training script...")
        import urllib.request

        urllib.request.urlretrieve(script_url, script_path)
        print("✓ Training script downloaded\n")
    return script_path


def run_training():
    """Run LoRA training."""
    print("=" * 60)
    print("🚀 Starting SkyyRose LoRA Training")
    print("=" * 60)
    print("\n📊 Configuration:")
    for key, value in CONFIG.items():
        print(f"   {key}: {value}")

    # Build training command
    cmd = [
        sys.executable,
        "train_dreambooth_lora_sdxl.py",
        f"--pretrained_model_name_or_path={CONFIG['model_name']}",
        f"--dataset_name={CONFIG['dataset_name']}",
        f"--output_dir={CONFIG['output_dir']}",
        f"--instance_prompt={CONFIG['instance_prompt']}",
        f"--resolution={CONFIG['resolution']}",
        f"--train_batch_size={CONFIG['train_batch_size']}",
        f"--gradient_accumulation_steps={CONFIG['gradient_accumulation_steps']}",
        f"--learning_rate={CONFIG['learning_rate']}",
        f"--lr_scheduler={CONFIG['lr_scheduler']}",
        f"--max_train_steps={CONFIG['max_train_steps']}",
        f"--checkpointing_steps={CONFIG['checkpointing_steps']}",
        f"--seed={CONFIG['seed']}",
        f"--rank={CONFIG['rank']}",
        "--mixed_precision=fp16",
        "--use_8bit_adam",
        "--enable_xformers_memory_efficient_attention",
        "--push_to_hub",
        f"--hub_model_id={CONFIG['hub_model_id']}",
    ]

    print("\n🏃 Running training...")
    print(f"   Command: {' '.join(cmd[:5])}...")

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✅ Training Complete!")
        print("=" * 60)
        print(f"\n📦 Model saved to: {CONFIG['output_dir']}")
        print(f"🌐 HuggingFace: https://huggingface.co/{CONFIG['hub_model_id']}")
    else:
        print(f"\n❌ Training failed with code {result.returncode}")

    return result.returncode


def main():
    """Main entry point."""
    # Check for GPU
    try:
        import torch

        if not torch.cuda.is_available():
            print("⚠ WARNING: No GPU detected. Training will be very slow.")
            print("   Recommend using Google Colab or cloud GPU.\n")
        else:
            print(f"✓ GPU detected: {torch.cuda.get_device_name(0)}\n")
    except ImportError:
        print("⚠ PyTorch not installed. Will install during setup.\n")

    # Setup
    install_dependencies()
    download_training_script()

    # Login to HuggingFace
    token = os.environ.get("HF_TOKEN")
    if token:
        from huggingface_hub import login

        login(token=token)
        print("✓ Logged in to HuggingFace\n")
    else:
        print("⚠ HF_TOKEN not set. Run: huggingface-cli login\n")

    # Run training
    return run_training()


if __name__ == "__main__":
    exit(main())
