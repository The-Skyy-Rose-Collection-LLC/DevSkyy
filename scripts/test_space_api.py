#!/usr/bin/env python3
"""
Test LoRA training Space API to diagnose issues.

Usage:
    python3 scripts/test_space_api.py
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

print("=" * 70)
print("🔍 Testing Space API")
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

print(f"Connecting to Space: {space_id}")
print()

try:
    client = Client(space_id)

    print("✅ Successfully connected to Space")
    print()

    print("📋 Available API endpoints:")
    print(client.view_api())
    print()

    print("ℹ️  Space is responsive and ready")
    print()
    print("If training isn't starting:")
    print("  1. Check if button is clickable in browser")
    print("  2. Try refreshing the page")
    print("  3. Check browser console for JavaScript errors")
    print()

except Exception as e:
    print(f"❌ Error connecting to Space: {e}")
    print()
    print("Possible issues:")
    print("  1. Space is still building/restarting")
    print("  2. Space has crashed")
    print("  3. Network/authentication issue")
    print()
    print(f"🔗 Check Space status: https://huggingface.co/spaces/{space_id}")
