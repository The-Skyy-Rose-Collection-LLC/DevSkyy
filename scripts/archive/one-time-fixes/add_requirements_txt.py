#!/usr/bin/env python3
"""
Add requirements.txt to force Space rebuild with torchvision.

Usage:
    python3 scripts/add_requirements_txt.py
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
print("🔧 Adding requirements.txt to Force Rebuild")
print("=" * 70)
print()

try:
    from huggingface_hub import HfApi
except ImportError:
    print("Installing huggingface_hub...")
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "huggingface_hub"], check=True)
    from huggingface_hub import HfApi

api = HfApi()
space_id = "damBruh/skyyrose-lora-trainer"

# Create requirements.txt
requirements = """gradio==4.0.0
huggingface_hub
torch
torchvision
diffusers
transformers
accelerate
peft
safetensors
bitsandbytes
datasets
"""

print("📝 Uploading requirements.txt...")
api.upload_file(
    path_or_fileobj=requirements.encode(),
    path_in_repo="requirements.txt",
    repo_id=space_id,
    repo_type="space",
    token=HF_TOKEN,
)
print("  ✓ requirements.txt uploaded")

print()
print("=" * 70)
print("✅ Requirements.txt Added!")
print("=" * 70)
print()
print(f"🌐 Space: https://huggingface.co/spaces/{space_id}")
print()
print("🔄 Space will rebuild from scratch (~3-5 min)")
print("   - Installing all dependencies including torchvision")
print("   - Previous attempts installed deps at runtime")
print("   - This forces install during build phase")
print()
print("📋 After rebuild:")
print("  1. Open Space URL above")
print("  2. Click 'Start Training'")
print("  3. Training should work this time")
print()
