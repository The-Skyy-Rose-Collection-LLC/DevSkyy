#!/usr/bin/env python3
"""
Download and Test Trained SkyyRose LoRA Model.

After AutoTrain completes, this downloads the model and runs test inference.

Usage:
    python3 scripts/download_and_test_lora.py
"""

import os
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(project_root / ".env")

# HuggingFace credentials
HF_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")

if not HF_TOKEN:
    print("❌ HUGGINGFACE_API_TOKEN not set in .env")
    sys.exit(1)


def check_training_complete() -> bool:
    """Check if AutoTrain has completed."""
    try:
        from huggingface_hub import HfApi

        api = HfApi()

        # Check if model repo exists
        try:
            api.model_info("damBruh/skyyrose-lora-v1", token=HF_TOKEN)
            return True
        except Exception:
            return False

    except Exception as e:
        print(f"⚠️  Could not check training status: {e}")
        return False


def download_lora_model():
    """Download trained LoRA model from HuggingFace Hub."""
    print("=" * 70)
    print("📥 Downloading SkyyRose LoRA Model")
    print("=" * 70)
    print()

    try:
        from huggingface_hub import snapshot_download

        model_id = "damBruh/skyyrose-lora-v1"
        local_dir = project_root / "models" / "skyyrose_lora_v1"

        print(f"Model: {model_id}")
        print(f"Destination: {local_dir}")
        print()

        # Download entire model repository
        snapshot_download(
            repo_id=model_id,
            local_dir=str(local_dir),
            token=HF_TOKEN,
            allow_patterns=["*.safetensors", "*.json", "*.txt", "README.md"],
        )

        print(f"\n✅ Model downloaded to: {local_dir}")
        return local_dir

    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        print("\n💡 Troubleshooting:")
        print("  - Verify training completed: https://huggingface.co/damBruh")
        print("  - Check model exists: https://huggingface.co/damBruh/skyyrose-lora-v1")
        print("  - Ensure HF_TOKEN has read access")
        return None


def test_lora_inference(model_dir: Path):
    """Run test inference with LoRA model."""
    print("\n" + "=" * 70)
    print("🎨 Testing LoRA Inference")
    print("=" * 70)
    print()

    # Install dependencies
    print("📦 Installing diffusers and dependencies...")
    try:
        import subprocess

        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-q",
                "diffusers",
                "transformers",
                "accelerate",
                "safetensors",
                "torch",
            ],
            check=True,
        )
        print("✓ Dependencies installed\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        return False

    try:
        import torch
        from diffusers import DiffusionPipeline

        print("🔧 Loading Stable Diffusion XL + LoRA...")

        # Load base SDXL model
        pipe = DiffusionPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0",
            torch_dtype=torch.float16,
            use_safetensors=True,
        )

        # Load LoRA weights
        pipe.load_lora_weights(str(model_dir))

        # Move to GPU if available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        pipe = pipe.to(device)

        print(f"✓ Model loaded on {device.upper()}\n")

        # Test prompts with trigger word
        test_prompts = [
            "skyyrose luxury black rose hoodie on model",
            "skyyrose signature collection t-shirt professional photo",
            "skyyrose love hurts design on premium apparel",
        ]

        output_dir = project_root / "generated_assets" / "lora_test"
        output_dir.mkdir(parents=True, exist_ok=True)

        print("🎨 Generating test images...\n")

        for i, prompt in enumerate(test_prompts, 1):
            print(f"[{i}/{len(test_prompts)}] {prompt}")

            # Generate image
            image = pipe(
                prompt=prompt,
                num_inference_steps=30,
                guidance_scale=7.5,
            ).images[0]

            # Save
            output_path = output_dir / f"test_{i}.png"
            image.save(output_path)
            print(f"    ✓ Saved: {output_path}\n")

        print("=" * 70)
        print("✅ Test Inference Complete!")
        print("=" * 70)
        print(f"\n📁 Test images saved to: {output_dir}")
        print("\n📋 Next Steps:")
        print("  1. Review generated images for quality")
        print("  2. Adjust prompts/parameters if needed")
        print("  3. Integrate into product generation pipeline")
        print("  4. Deploy to production API")

        return True

    except Exception as e:
        print(f"\n❌ Inference failed: {e}")
        print("\n💡 This might be due to:")
        print("  - Insufficient GPU memory (SDXL needs ~8GB VRAM)")
        print("  - LoRA weights incompatible with base model")
        print("  - Missing dependencies")
        return False


def main():
    """Main execution flow."""
    print("=" * 70)
    print("🚀 SkyyRose LoRA Download  Test")
    print("=" * 70)
    print()

    # Check if training is complete
    print("🔍 Checking training status...")
    if not check_training_complete():
        print("⚠️  Training not complete yet")
        print("\n💡 Options:")
        print("  1. Wait for training to finish (check terminal)")
        print("  2. Monitor: python3 scripts/monitor_autotrain.py")
        print("  3. Check manually: https://huggingface.co/damBruh")
        return 1

    print("✓ Training complete!\n")

    # Download model
    model_dir = download_lora_model()
    if not model_dir:
        return 1

    # Run test inference
    print("\n⚠️  Test inference requires GPU (8GB+ VRAM recommended)")
    response = input("Run test inference now? [y/N]: ").strip().lower()

    if response == "y":
        success = test_lora_inference(model_dir)
        return 0 if success else 1
    else:
        print("\n⏸️  Skipping inference test")
        print("\nTo test later, run:")
        print("  python3 scripts/download_and_test_lora.py")
        return 0


if __name__ == "__main__":
    sys.exit(main())
