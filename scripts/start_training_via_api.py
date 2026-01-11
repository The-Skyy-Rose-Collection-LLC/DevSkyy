#!/usr/bin/env python3
"""
Start LoRA training via Gradio API (bypass browser).

Usage:
    python3 scripts/start_training_via_api.py
"""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("🚀 Starting LoRA Training via API")
print("=" * 70)
print()

try:
    from gradio_client import Client
except ImportError:
    print("Installing gradio_client...")
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "gradio_client"], check=True)
    from gradio_client import Client

space_id = "damBruh/skyyrose-lora-trainer"

print(f"Connecting to: {space_id}")
print()

try:
    client = Client(space_id)

    print("✅ Connected successfully")
    print()
    print("🎯 Starting training job...")
    print("   (This will take 30-60 minutes)")
    print()
    print("📊 Live training output:")
    print("-" * 70)

    # Start training and stream output
    for output in client.submit(api_name="/train_lora"):
        if output:
            # Print only the last few lines to avoid spam
            lines = output.split("\n")
            recent_lines = lines[-5:] if len(lines) > 5 else lines
            print("\n".join(recent_lines))
            print("-" * 70)

except KeyboardInterrupt:
    print()
    print("⚠️  Training interrupted by user")
    print()
    print("Note: Training may still be running on the Space")
    print(f"Check: https://huggingface.co/spaces/{space_id}")

except Exception as e:
    print(f"❌ Error: {e}")
    print()
    import traceback

    traceback.print_exc()
