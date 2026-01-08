#!/usr/bin/env python3
"""Create virtual-tryon HuggingFace Space and push code with ralph-loop retry."""

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

# Get token
token = os.getenv("HF_TOKEN")
if not token:
    print("❌ HF_TOKEN not found in .env")
    sys.exit(1)

print("✓ Token loaded from .env")

try:
    from huggingface_hub import HfApi, create_repo
except ImportError:
    print("Installing huggingface_hub...")
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub"], check=True)
    from huggingface_hub import HfApi, create_repo


def main():
    """Create Space and upload files with ralph-loop retry."""

    print("=== Creating SkyyRose Virtual Try-On Space ===\n")

    # Space directory
    space_dir = project_root / "hf-spaces" / "virtual-tryon"

    if not space_dir.exists():
        print(f"❌ Space directory not found at: {space_dir}")
        return 1

    # Initialize HuggingFace API with token
    api = HfApi(token=token)

    # Space repository
    repo_id = "damBruh/skyyrose-virtual-tryon"

    # Ralph-loop: Create repo with retry (exponential backoff)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"Creating Space repository: {repo_id} (attempt {attempt + 1}/{max_retries})")
            create_repo(
                repo_id=repo_id,
                repo_type="space",
                space_sdk="gradio",
                exist_ok=True,
                private=False,
                token=token,
            )
            print("✓ Space repository created/verified\n")
            break
        except Exception as e:
            if "already exists" in str(e).lower() or attempt == max_retries - 1:
                print(f"⚠ Repository exists or max retries reached: {e}\n")
                break
            # Exponential backoff: 1s, 2s, 4s
            wait_time = 2**attempt
            print(f"⚠ Retry in {wait_time}s: {e}")
            time.sleep(wait_time)

    # Ralph-loop: Upload folder with retry (exponential backoff)
    print(f"Uploading Space files from: {space_dir}")

    for attempt in range(max_retries):
        try:
            print(f"  Upload attempt {attempt + 1}/{max_retries}...")
            api.upload_folder(
                folder_path=str(space_dir),
                repo_id=repo_id,
                repo_type="space",
                commit_message="feat: deploy SkyyRose virtual try-on Space with Gradio interface",
                token=token,
                ignore_patterns=[".git/*", ".git"],
            )

            print(f"\n{'='*60}")
            print("✅ Virtual Try-On Space Deployed Successfully!")
            print(f"{'='*60}")
            print(f"\nSpace URL: https://huggingface.co/spaces/{repo_id}")
            print("\n📋 Next Steps:")
            print("  1. Space will build automatically")
            print("  2. Integrate FASHN API for try-on functionality")
            print("  3. Embed in WordPress /experiences/ pages")

            return 0

        except Exception as e:
            if attempt == max_retries - 1:
                print(f"\n❌ Upload failed after {max_retries} attempts: {e}")
                return 1
            # Exponential backoff: 1s, 2s, 4s
            wait_time = 2**attempt
            print(f"  ⚠ Retry in {wait_time}s: {e}")
            time.sleep(wait_time)

    return 1


if __name__ == "__main__":
    sys.exit(main())
