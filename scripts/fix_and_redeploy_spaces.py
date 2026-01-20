#!/usr/bin/env python3
"""Fix and redeploy all HuggingFace Spaces with correct dependencies (ralph-loop retry)."""

import os
import sys
import time
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file
from dotenv import load_dotenv  # noqa: E402

load_dotenv(project_root / ".env")

# Get token
token = os.getenv("HF_TOKEN")
if not token:
    print("❌ HF_TOKEN not found in .env")
    sys.exit(1)

print("✓ Token loaded from .env")

try:
    from huggingface_hub import HfApi
except ImportError:
    print("Installing huggingface_hub...")
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub"], check=True)
    from huggingface_hub import HfApi


# Space configurations
SPACES = [
    {
        "repo_id": "damBruh/skyyrose-virtual-tryon",
        "local_dir": project_root / "hf-spaces" / "virtual-tryon",
    },
    {
        "repo_id": "damBruh/skyyrose-3d-converter",
        "local_dir": project_root / "hf-spaces" / "3d-converter",
    },
    {
        "repo_id": "damBruh/skyyrose-lora-training-monitor",
        "local_dir": project_root / "hf-spaces" / "lora-training-monitor",
    },
]


def upload_space_with_retry(
    api: HfApi, repo_id: str, local_dir: Path, max_retries: int = 3
) -> bool:
    """Upload Space with ralph-loop retry (exponential backoff)."""

    print(f"\n📤 Uploading: {repo_id}")
    print(f"   Local: {local_dir}")

    for attempt in range(max_retries):
        try:
            print(f"   Attempt {attempt + 1}/{max_retries}...")

            api.upload_folder(
                folder_path=str(local_dir),
                repo_id=repo_id,
                repo_type="space",
                commit_message="fix: remove gradio from requirements.txt (SDK version handles it)",
                token=token,
                ignore_patterns=[".git/*", ".git"],
            )

            print("   ✅ Upload successful!")
            print(f"   URL: https://huggingface.co/spaces/{repo_id}")
            return True

        except Exception as e:
            if attempt == max_retries - 1:
                print(f"   ❌ Upload failed after {max_retries} attempts: {e}")
                return False

            # Exponential backoff: 1s, 2s, 4s
            wait_time = 2**attempt
            print(f"   ⚠️  Retry in {wait_time}s: {e}")
            time.sleep(wait_time)

    return False


def main():
    """Fix and redeploy all HuggingFace Spaces."""

    print("=== Fixing and Redeploying SkyyRose HuggingFace Spaces ===\n")
    print("Fix: Remove gradio from requirements.txt (sdk_version handles it)\n")

    # Initialize HuggingFace API
    api = HfApi(token=token)

    success_count = 0

    for space in SPACES:
        if upload_space_with_retry(api, space["repo_id"], space["local_dir"]):
            success_count += 1
            # Rate limiting: wait between uploads
            if space != SPACES[-1]:
                time.sleep(2)

    print(f"\n{'=' * 60}")
    print(f"✅ Successfully redeployed {success_count}/{len(SPACES)} Spaces")
    print(f"{'=' * 60}")

    if success_count == len(SPACES):
        print("\n📋 Next Steps:")
        print("  1. Wait ~2-3 minutes for Spaces to rebuild")
        print("  2. Visit https://huggingface.co/spaces/damBruh/skyyrose-virtual-tryon")
        print("  3. Visit https://huggingface.co/spaces/damBruh/skyyrose-3d-converter")
        print("  4. Visit https://huggingface.co/spaces/damBruh/skyyrose-lora-training-monitor")
        print("  5. Verify all Spaces are running without errors")
        return 0
    else:
        print(f"\n⚠️  {len(SPACES) - success_count} Spaces failed to redeploy")
        return 1


if __name__ == "__main__":
    sys.exit(main())
