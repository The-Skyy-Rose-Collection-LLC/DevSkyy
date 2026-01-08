#!/usr/bin/env python3
"""Redeploy lora-training-monitor HuggingFace Space with ralph-loop retry."""

import os
import sys
import time
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file
from dotenv import load_dotenv

load_dotenv(project_root / ".env")

HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    print("❌ HF_TOKEN not found in .env")
    sys.exit(1)

try:
    from huggingface_hub import HfApi
except ImportError:
    print("Installing huggingface_hub...")
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub<1.0"], check=True)
    from huggingface_hub import HfApi


def push_space_with_retry(max_retries: int = 3) -> bool:
    """Push lora-training-monitor Space with ralph-loop retry."""

    api = HfApi(token=HF_TOKEN)
    repo_id = "damBruh/skyyrose-lora-training-monitor"
    local_dir = project_root / "hf-spaces" / "lora-training-monitor"

    print(f"=== Deploying {repo_id} ===")
    print(f"Local directory: {local_dir}\n")

    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries}: Uploading...")

            api.upload_folder(
                folder_path=str(local_dir),
                repo_id=repo_id,
                repo_type="space",
                commit_message="fix: remove manual component.render() calls to fix DuplicateBlockError",
                token=HF_TOKEN,
                ignore_patterns=[".git/*", ".git", "__pycache__/*"],
            )

            print(f"✅ Successfully deployed to https://huggingface.co/spaces/{repo_id}")
            print("   Space URL: https://dambruh-skyyrose-lora-training-monitor.hf.space")
            return True

        except Exception as e:
            if attempt == max_retries - 1:
                print(f"❌ Failed after {max_retries} attempts: {e}")
                return False

            wait_time = 2**attempt
            print(f"⚠️  Retry in {wait_time}s: {e}")
            time.sleep(wait_time)

    return False


def main():
    """Redeploy lora-training-monitor Space."""

    print("=== SkyyRose LoRA Training Monitor Redeployment ===\n")

    if push_space_with_retry():
        print("\n" + "=" * 60)
        print("✅ Deployment successful")
        print("=" * 60)
        print("\n📋 Next Steps:")
        print("  1. Wait 2-3 minutes for Space to rebuild")
        print("  2. Visit https://dambruh-skyyrose-lora-training-monitor.hf.space")
        print("  3. Verify no DuplicateBlockError")
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ Deployment failed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
