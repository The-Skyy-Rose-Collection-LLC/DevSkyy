#!/usr/bin/env python3
"""
Setup and launch AutoTrain for SkyyRose LoRA training via CLI.

This uses AutoTrain Advanced CLI to bypass the broken web template.

Usage:
    python3 scripts/setup_autotrain_cli.py
"""

import os
import subprocess
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("🚀 AutoTrain CLI Setup for SkyyRose LoRA")
print("=" * 70)
print()

# Check Python version (AutoTrain requires 3.11 or 3.12 for pre-built wheels)
python_version = sys.version_info
print(f"🐍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")

if python_version.major == 3 and python_version.minor >= 13:
    print("⚠️  WARNING: Python 3.13+ detected")
    print("   AutoTrain packages (pydantic-core, tiktoken, sentencepiece)")
    print("   don't have pre-built wheels for Python 3.13+")
    print()
    print("💡 Solutions:")
    print("   1. Use Python 3.11 or 3.12:")
    print("      python3.12 scripts/setup_autotrain_cli.py")
    print()
    print("   2. Install Rust + build tools (slower):")
    print("      brew install rust")
    print("      xcode-select --install")
    print()
    print("   3. Use HuggingFace Spaces instead (recommended)")
    print()
    response = input("Continue anyway and try to build from source? [y/N]: ").strip().lower()
    if response != "y":
        print("\n⏸️  Setup cancelled")
        print("\nRecommended: Use Python 3.12:")
        print("  python3.12 -m pip install autotrain-advanced")
        sys.exit(0)
    print()

print()

# Step 1: Install AutoTrain
print("📦 Step 1: Installing AutoTrain Advanced...")
try:
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-U", "autotrain-advanced"],
        check=True,
    )
    print("✓ AutoTrain installed\n")
except subprocess.CalledProcessError as e:
    print(f"❌ Installation failed: {e}")
    sys.exit(1)

# Step 2: Verify HuggingFace token
print("🔑 Step 2: Verifying HuggingFace authentication...")
hf_token = os.getenv("HUGGINGFACE_API_TOKEN")
if not hf_token:
    print("❌ HUGGINGFACE_API_TOKEN not set in .env")
    print("\n💡 Get your token at: https://huggingface.co/settings/tokens")
    print("   Then add to .env: HUGGINGFACE_API_TOKEN=hf_...")
    sys.exit(1)

print(f"✓ Token found: {hf_token[:10]}...\n")

# Step 3: Login to HuggingFace Hub
print("🔐 Step 3: Authenticating with HuggingFace Hub...")
try:
    subprocess.run(
        ["huggingface-cli", "login", "--token", hf_token],
        check=True,
        capture_output=True,
    )
    print("✓ Authentication successful\n")
except subprocess.CalledProcessError:
    print("⚠️  Using existing authentication\n")

# Step 4: Prepare training command
print("=" * 70)
print("📋 Training Configuration")
print("=" * 70)

config = {
    "project_name": "skyyrose-lora-v1",
    "dataset": "damBruh/skyyrose-lora-dataset-v1",
    "model": "stabilityai/stable-diffusion-xl-base-1.0",
    "prompt": "skyyrose luxury fashion",
    "lr": "1e-4",
    "epochs": "100",
    "batch_size": "1",
    "resolution": "512",
    "lora_rank": "16",
    "push_to_hub": "True",
}

for key, value in config.items():
    print(f"  {key}: {value}")

print("\n" + "=" * 70)
print("🚀 Ready to Launch Training")
print("=" * 70)

# AutoTrain CLI command
autotrain_cmd = [
    "autotrain",
    "dreambooth",
    "--model",
    config["model"],
    "--project-name",
    config["project_name"],
    "--image-path",
    f"hf://datasets/{config['dataset']}",
    "--prompt",
    config["prompt"],
    "--learning-rate",
    config["lr"],
    "--num-steps",
    "1000",
    "--batch-size",
    config["batch_size"],
    "--gradient-accumulation",
    "4",
    "--resolution",
    config["resolution"],
    "--use-8bit-adam",
    "--xformers",
    "--mixed-precision",
    "fp16",
    "--train-text-encoder",
    "--lr-scheduler",
    "constant",
    "--lr-warmup-steps",
    "0",
    "--rank",
    config["lora_rank"],
    "--push-to-hub",
    "--token",
    hf_token,
]

print("\n💡 Command to run:")
print(" ".join(autotrain_cmd))
print()

# Ask user confirmation
response = input("Start training now? [y/N]: ").strip().lower()

if response == "y":
    print("\n🚀 Starting AutoTrain...\n")
    print("⏳ This will take 30-60 minutes on cloud GPU")
    print("📊 Monitor progress at: https://huggingface.co/damBruh\n")

    try:
        subprocess.run(autotrain_cmd, check=True)
        print("\n✅ Training started successfully!")
        print("\n📋 Next Steps:")
        print("  1. Monitor at: https://huggingface.co/damBruh/skyyrose-lora-v1")
        print("  2. Or run: python3 scripts/monitor_autotrain.py")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Training failed: {e}")
        print("\n💡 Troubleshooting:")
        print("  - Check HuggingFace token has write access")
        print(
            "  - Verify dataset exists: https://huggingface.co/datasets/damBruh/skyyrose-lora-dataset-v1"
        )
        print("  - Check HuggingFace billing/credits")
        sys.exit(1)
else:
    print("\n⏸️  Training not started")
    print("\nTo start manually, run:")
    print(f"  {' '.join(autotrain_cmd)}")
