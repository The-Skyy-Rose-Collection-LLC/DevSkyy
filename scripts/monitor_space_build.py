#!/usr/bin/env python3
"""
Monitor HuggingFace Space build status.

Polls the Space every 30 seconds and notifies when build completes.

Usage:
    python3 scripts/monitor_space_build.py
"""

import os
import sys
import time
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv  # noqa: E402
from huggingface_hub import HfApi  # noqa: E402

load_dotenv(project_root / ".env")

HF_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")

if not HF_TOKEN:
    print("❌ HUGGINGFACE_API_TOKEN not set in .env")
    sys.exit(1)

api = HfApi()
space_id = "damBruh/skyyrose-lora-trainer"

print("=" * 70)
print("🔍 Monitoring Space Build Status")
print("=" * 70)
print(f"Space: {space_id}")
print("Checking every 30 seconds...")
print()

previous_status = None

try:
    while True:
        try:
            # Get Space runtime info
            space_info = api.space_info(repo_id=space_id, token=HF_TOKEN)

            runtime = getattr(space_info, "runtime", None)
            if runtime:
                stage = getattr(runtime, "stage", "unknown")
                hardware = getattr(runtime, "hardware", "unknown")

                current_status = f"{stage} on {hardware}"

                if current_status != previous_status:
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] Status: {current_status}")
                    previous_status = current_status

                # Check if running
                if stage.lower() == "running":
                    print()
                    print("=" * 70)
                    print("✅ BUILD COMPLETE - Space is Running!")
                    print("=" * 70)
                    print()
                    print(f"🎯 Open Space: https://huggingface.co/spaces/{space_id}")
                    print()
                    print("Next Steps:")
                    print("1. Click the '🚀 Start Training' button")
                    print("2. Training will take 30-60 minutes")
                    print("3. Model will auto-upload to damBruh/skyyrose-lora-v1")
                    print()
                    break

                # Check if failed
                elif "error" in stage.lower() or "failed" in stage.lower():
                    print()
                    print("=" * 70)
                    print("❌ BUILD FAILED")
                    print("=" * 70)
                    print()
                    print(f"🔍 Check logs: https://huggingface.co/spaces/{space_id}?logs=build")
                    print()
                    break

            else:
                print(f"[{time.strftime('%H:%M:%S')}] No runtime info available yet...")

        except Exception as e:
            print(f"⚠️  Error checking status: {e}")

        # Wait 30 seconds before next check
        time.sleep(30)

except KeyboardInterrupt:
    print()
    print("🛑 Monitoring stopped by user")
    print(f"Check status manually: https://huggingface.co/spaces/{space_id}")
