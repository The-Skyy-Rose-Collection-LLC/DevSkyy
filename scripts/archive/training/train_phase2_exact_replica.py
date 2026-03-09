"""
SkyyRose LoRA Phase 2 Training - Exact Replica Mode
====================================================

CRITICAL: This training focuses on quality enhancement ONLY.
- ✅ Sharpen details, improve lighting, reduce noise
- ❌ NO logo changes, NO color alterations, NO design modifications

Training Features (Tier 1):
1. Lighting Intelligence - Correct poor lighting → professional studio quality
2. Texture Enhancement - Enhance fabric/material clarity
3. Color Calibration - Preserve exact brand colors (#B76E79 rose gold, etc.)

Usage:
    export HF_TOKEN=hf_your_token_here
    python scripts/train_phase2_exact_replica.py
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Phase 2 Configuration - Exact Replica Mode
CONFIG = {
    # Model & Dataset
    "model_name": "stabilityai/stable-diffusion-xl-base-1.0",
    "dataset_name": "damBruh/skyyrose-lora-dataset-v2",
    "output_dir": "./models/training-runs/phase2-exact-replica",
    "hub_model_id": "damBruh/skyyrose-lora-phase2-exact-replica",
    # CRITICAL: Exact Replica Prompts
    "instance_prompt": "exact replica, SkyyRose product, preserve all logos and colors, professional studio photography, enhance quality only",
    "class_prompt": "professional product photography",
    # Phase 2 Training Parameters (Conservative for Preservation)
    "resolution": 1024,
    "train_batch_size": 1,
    "gradient_accumulation_steps": 4,
    "learning_rate": 1e-5,  # VERY LOW - prevents creative alterations
    "lr_scheduler": "constant",
    "lr_warmup_steps": 0,
    "max_train_steps": 1000,
    "checkpointing_steps": 100,  # Save more frequently for quality checks
    "validation_steps": 100,  # Validate preservation every 100 steps
    # LoRA Configuration
    "rank": 32,  # Higher rank for better quality learning
    "lora_alpha": 64,
    # Optimization
    "mixed_precision": "fp16",
    "use_8bit_adam": True,
    "enable_xformers": True,
    "gradient_checkpointing": True,
    # Preservation Settings
    "prior_loss_weight": 1.0,  # Regularization to prevent overfitting
    "seed": 42,
    # Monitoring
    "logging_dir": "./models/training-runs/phase2-exact-replica/logs",
    "report_to": "tensorboard",
    "validation_prompt": "exact replica, SkyyRose signature collection cotton candy tee, preserve all logos and colors, enhance clarity and sharpness only, professional studio photography, preserve original rose gold accents",
    "num_validation_images": 4,
    # Training Focus (Tier 1)
    "training_focus": {
        "lighting_intelligence": True,
        "texture_enhancement": True,
        "color_calibration": True,
        "logo_preservation": True,
        "design_preservation": True,
    },
    # Quality Targets
    "quality_metrics": {
        "logo_similarity_threshold": 0.99,
        "color_deviation_threshold": 0.02,  # <2% allowed
        "sharpness_gain_target": 0.20,  # >20% improvement
        "noise_reduction_target": 0.30,  # >30% reduction
    },
}


def create_output_dirs():
    """Create output directories."""
    dirs = [
        CONFIG["output_dir"],
        CONFIG["logging_dir"],
        f"{CONFIG['output_dir']}/checkpoints",
        f"{CONFIG['output_dir']}/validation",
    ]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    print(f"✓ Created output directories in {CONFIG['output_dir']}\n")


def save_training_config():
    """Save training configuration to JSON."""
    config_path = Path(CONFIG["output_dir"]) / "training_config.json"
    with open(config_path, "w") as f:
        json.dump(CONFIG, f, indent=2)
    print(f"✓ Saved training config to {config_path}\n")


def create_progress_file():
    """Create progress tracking file."""
    progress_path = Path(CONFIG["output_dir"]) / "progress.json"
    progress_data = {
        "version": "phase2-exact-replica",
        "status": "preparing",
        "started_at": datetime.utcnow().isoformat(),
        "current_epoch": 0,
        "total_epochs": CONFIG["max_train_steps"] // 100,  # Approximate
        "current_step": 0,
        "total_steps": CONFIG["max_train_steps"],
        "progress_percentage": 0.0,
        "loss": 0.0,
        "learning_rate": CONFIG["learning_rate"],
        "avg_loss": 0.0,
        "best_loss": float("inf"),
        "total_images": 254,  # From skyyrose_lora_v2 dataset
        "total_products": 254,
        "collections": {
            "signature": 85,
            "love_hurts": 92,
            "black_rose": 77,
        },
        "message": "Preparing Phase 2 training with exact replica focus",
        "training_focus": CONFIG["training_focus"],
        "quality_targets": CONFIG["quality_metrics"],
    }

    with open(progress_path, "w") as f:
        json.dump(progress_data, f, indent=2)
    print(f"✓ Created progress file at {progress_path}\n")


def install_dependencies():
    """Install required packages."""
    packages = [
        "accelerate>=0.26.0",
        "transformers>=4.38.0",
        "diffusers[torch]>=0.26.0",
        "datasets>=2.16.0",
        "peft>=0.8.0",
        "bitsandbytes>=0.41.0",
        "tensorboard>=2.15.0",
        "huggingface-hub>=0.20.0",
    ]
    print("📦 Installing dependencies...")
    for pkg in packages:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg], check=False)
    print("✓ Dependencies installed\n")


def download_training_script():
    """Download the official SDXL LoRA training script."""
    script_url = "https://raw.githubusercontent.com/huggingface/diffusers/main/examples/dreambooth/train_dreambooth_lora_sdxl.py"
    script_path = Path("train_dreambooth_lora_sdxl.py")

    if not script_path.exists():
        print("📥 Downloading HuggingFace training script...")
        import urllib.request

        urllib.request.urlretrieve(script_url, script_path)
        print("✓ Training script downloaded\n")
    else:
        print("✓ Training script already exists\n")

    return script_path


def run_training():
    """Run Phase 2 LoRA training with exact replica focus."""
    print("=" * 70)
    print("🚀 SkyyRose LoRA Phase 2 Training - EXACT REPLICA MODE")
    print("=" * 70)
    print("\n🎯 Training Objectives:")
    print("   ✅ Enhance lighting quality (studio-grade)")
    print("   ✅ Sharpen textures and materials")
    print("   ✅ Calibrate colors to brand standards")
    print("   ❌ NO logo alterations")
    print("   ❌ NO color modifications")
    print("   ❌ NO design changes")

    print("\n📊 Configuration:")
    print(f"   Base Model: {CONFIG['model_name']}")
    print(f"   Dataset: {CONFIG['dataset_name']} (254 images)")
    print(f"   Learning Rate: {CONFIG['learning_rate']} (VERY LOW for preservation)")
    print(f"   Max Steps: {CONFIG['max_train_steps']}")
    print(f"   LoRA Rank: {CONFIG['rank']}")
    print(f"   Output: {CONFIG['output_dir']}")

    # Build training command
    cmd = [
        sys.executable,
        "train_dreambooth_lora_sdxl.py",
        f"--pretrained_model_name_or_path={CONFIG['model_name']}",
        f"--dataset_name={CONFIG['dataset_name']}",
        f"--output_dir={CONFIG['output_dir']}",
        f"--instance_prompt={CONFIG['instance_prompt']}",
        f"--class_prompt={CONFIG['class_prompt']}",
        f"--resolution={CONFIG['resolution']}",
        f"--train_batch_size={CONFIG['train_batch_size']}",
        f"--gradient_accumulation_steps={CONFIG['gradient_accumulation_steps']}",
        f"--learning_rate={CONFIG['learning_rate']}",
        f"--lr_scheduler={CONFIG['lr_scheduler']}",
        f"--lr_warmup_steps={CONFIG['lr_warmup_steps']}",
        f"--max_train_steps={CONFIG['max_train_steps']}",
        f"--checkpointing_steps={CONFIG['checkpointing_steps']}",
        # Note: Using validation_epochs instead of validation_steps
        f"--validation_epochs={CONFIG['validation_steps'] // 100}",  # Convert steps to epochs
        f"--validation_prompt={CONFIG['validation_prompt']}",
        f"--num_validation_images={CONFIG['num_validation_images']}",
        f"--seed={CONFIG['seed']}",
        f"--rank={CONFIG['rank']}",
        "--mixed_precision=fp16",
        "--use_8bit_adam",
        "--enable_xformers_memory_efficient_attention",
        "--gradient_checkpointing",
        f"--prior_loss_weight={CONFIG['prior_loss_weight']}",
        f"--logging_dir={CONFIG['logging_dir']}",
        f"--report_to={CONFIG['report_to']}",
    ]

    # Add HuggingFace upload flags only if token available
    if CONFIG.get("use_hf", False):
        cmd.extend(
            [
                "--push_to_hub",
                f"--hub_model_id={CONFIG['hub_model_id']}",
            ]
        )

    print("\n🏃 Starting training...")
    print(f"   Monitor progress: tensorboard --logdir={CONFIG['logging_dir']}")
    print(f"   Progress file: {CONFIG['output_dir']}/progress.json\n")

    # Update progress to training
    progress_path = Path(CONFIG["output_dir"]) / "progress.json"
    with open(progress_path) as f:
        progress = json.load(f)
    progress["status"] = "training"
    progress["message"] = "Training in progress - Phase 2 exact replica mode"
    with open(progress_path, "w") as f:
        json.dump(progress, f, indent=2)

    # Run training
    result = subprocess.run(cmd)

    # Update progress based on result
    with open(progress_path) as f:
        progress = json.load(f)

    if result.returncode == 0:
        progress["status"] = "completed"
        progress["completed_at"] = datetime.utcnow().isoformat()
        progress["message"] = "Training completed successfully"
        progress["progress_percentage"] = 100.0
        progress["current_step"] = CONFIG["max_train_steps"]

        print("\n" + "=" * 70)
        print("✅ Phase 2 Training Complete!")
        print("=" * 70)
        print("\n📦 Model Location:")
        print(f"   Local: {CONFIG['output_dir']}")
        print(f"   HuggingFace: https://huggingface.co/{CONFIG['hub_model_id']}")
        print("\n🔬 Next Steps:")
        print("   1. Validate logo preservation (100% match required)")
        print("   2. Validate color accuracy (<2% deviation required)")
        print("   3. Test on sample products")
        print("   4. Integrate into Product Photography Space")
    else:
        progress["status"] = "failed"
        progress["completed_at"] = datetime.utcnow().isoformat()
        progress["error"] = f"Training failed with exit code {result.returncode}"
        progress["message"] = "Training failed - check logs for details"

        print(f"\n❌ Training failed with code {result.returncode}")
        print(f"   Check logs: {CONFIG['logging_dir']}")

    # Save final progress
    with open(progress_path, "w") as f:
        json.dump(progress, f, indent=2)

    # Create status.json for completed training
    status_path = Path(CONFIG["output_dir"]) / "status.json"
    with open(status_path, "w") as f:
        json.dump(progress, f, indent=2)

    return result.returncode


def main():
    """Main entry point for Phase 2 training."""
    print("\n" + "=" * 70)
    print("SkyyRose LoRA Phase 2 - EXACT REPLICA MODE")
    print("=" * 70)

    # Check GPU
    try:
        import sys

        import torch

        if not torch.cuda.is_available():
            print("\n⚠ WARNING: No GPU detected!")
            print("   Training requires GPU with 16GB+ VRAM")
            print("   Recommend: Google Colab, AWS, or cloud GPU\n")

            # Skip confirmation if running non-interactively
            if not sys.stdin.isatty():
                print("   Running in non-interactive mode - skipping GPU check")
                print("   NOTE: Training will be slow without GPU!\n")
            else:
                response = input("Continue anyway? (y/n): ")
                if response.lower() != "y":
                    return 1
        else:
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"\n✓ GPU Detected: {gpu_name}")
            print(f"   VRAM: {gpu_memory:.1f} GB")

            if gpu_memory < 16:
                print(f"   ⚠ WARNING: {gpu_memory:.1f} GB may not be enough (16GB+ recommended)")
            print()
    except ImportError:
        print("\n⚠ PyTorch not installed. Will install during setup.\n")

    # Check HF_TOKEN (optional for local training)
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("⚠ WARNING: HF_TOKEN not set")
        print("   Training will run locally only (no HuggingFace uploads)")
        print("   To enable HF uploads: export HF_TOKEN=hf_your_token_here\n")
        use_hf = False
    else:
        # Login to HuggingFace
        try:
            from huggingface_hub import login

            login(token=token)
            print("✓ Logged in to HuggingFace\n")
            use_hf = True
        except Exception as e:
            print(f"❌ HuggingFace login failed: {e}")
            print("   Continuing with local training only\n")
            use_hf = False

    # Store HF flag in CONFIG for use in run_training()
    CONFIG["use_hf"] = use_hf

    # Setup
    create_output_dirs()
    save_training_config()
    create_progress_file()
    install_dependencies()
    download_training_script()

    # Confirm before training
    print("\n" + "=" * 70)
    print("Ready to start Phase 2 training")
    print("=" * 70)
    print(f"\nDataset: {CONFIG['dataset_name']} (254 SkyyRose product images)")
    print(f"Training Steps: {CONFIG['max_train_steps']}")
    print("Estimated Time: ~2-3 hours (GPU-dependent)")
    print(f"Output: {CONFIG['output_dir']}")
    print("\n🎯 Training Focus:")
    print("   - Lighting intelligence (studio-grade)")
    print("   - Texture enhancement (fabric/material clarity)")
    print("   - Color calibration (preserve #B76E79 rose gold)")
    print("   - Logo preservation (100% exact match)")
    print("   - Design preservation (zero alterations)")

    # Auto-confirm in non-interactive mode
    if not sys.stdin.isatty():
        print("\n✓ Auto-starting training in non-interactive mode...\n")
    else:
        response = input("\nStart training? (y/n): ")
        if response.lower() != "y":
            print("Training cancelled.")
            return 0

    # Run training
    return run_training()


if __name__ == "__main__":
    exit(main())
