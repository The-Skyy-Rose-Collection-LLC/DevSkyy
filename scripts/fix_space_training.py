#!/usr/bin/env python3
"""
Fix LoRA training Space - OMP_NUM_THREADS environment variable issue.

Error: ValueError: invalid literal for int() with base 10: '7500m'
Fix: Clear OMP_NUM_THREADS before running accelerate

Usage:
    python3 scripts/fix_space_training.py
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
print("🔧 Fixing LoRA Training Space")
print("=" * 70)
print()
print("Issue: OMP_NUM_THREADS='7500m' (Kubernetes format)")
print("Fix: Clear env var before running accelerate")
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

# Fixed training app
app_code = '''import gradio as gr
import subprocess
import sys
import os
from pathlib import Path

def install_dependencies():
    """Install training dependencies."""
    deps = [
        "diffusers[torch]",
        "transformers",
        "accelerate",
        "peft",
        "bitsandbytes",
        "datasets",
        "torchvision"
    ]

    for dep in deps:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", dep],
            check=True
        )

def train_lora(progress=gr.Progress()):
    """Run LoRA training."""

    logs = []

    try:
        # FIX: Clear problematic environment variables
        # HuggingFace Spaces sets OMP_NUM_THREADS to '7500m' (Kubernetes format)
        # but accelerate expects an integer
        if 'OMP_NUM_THREADS' in os.environ:
            logs.append(f"🔧 Clearing OMP_NUM_THREADS (was: {os.environ['OMP_NUM_THREADS']})")
            yield "\\n".join(logs)
            del os.environ['OMP_NUM_THREADS']

        # Set to a reasonable value for T4 GPU
        os.environ['OMP_NUM_THREADS'] = '4'
        logs.append("✓ Environment configured\\n")
        yield "\\n".join(logs)

        # Install dependencies
        progress(0.05, desc="Installing dependencies...")
        logs.append("📦 Installing training dependencies...")
        yield "\\n".join(logs)

        install_dependencies()
        logs.append("✓ Dependencies installed\\n")
        yield "\\n".join(logs)

        # Download dataset
        progress(0.1, desc="Downloading dataset...")
        logs.append("📥 Downloading dataset: damBruh/skyyrose-lora-dataset-v1")
        yield "\\n".join(logs)

        from huggingface_hub import snapshot_download
        dataset_path = snapshot_download(
            repo_id="damBruh/skyyrose-lora-dataset-v1",
            repo_type="dataset",
            local_dir="./skyyrose_dataset"
        )
        logs.append(f"✓ Dataset downloaded: {dataset_path}\\n")
        yield "\\n".join(logs)

        # Download training script
        progress(0.15, desc="Preparing training script...")
        logs.append("📝 Downloading training script...")
        yield "\\n".join(logs)

        import requests
        script_url = "https://raw.githubusercontent.com/huggingface/diffusers/main/examples/dreambooth/train_dreambooth_lora_sdxl.py"
        response = requests.get(script_url)

        with open("train_dreambooth_lora_sdxl.py", "w") as f:
            f.write(response.text)

        logs.append("✓ Training script ready\\n")
        yield "\\n".join(logs)

        # Configure accelerate
        progress(0.2, desc="Configuring accelerate...")
        logs.append("⚙️  Configuring accelerate...")
        yield "\\n".join(logs)

        subprocess.run(["accelerate", "config", "default"], check=True)
        logs.append("✓ Accelerate configured\\n")
        yield "\\n".join(logs)

        # Start training
        progress(0.25, desc="Starting LoRA training...")
        logs.append("🚀 Starting LoRA training...")
        logs.append("   Base: SDXL")
        logs.append("   Steps: 1000")
        logs.append("   Learning Rate: 1e-4")
        logs.append("   LoRA Rank: 16")
        logs.append("")
        yield "\\n".join(logs)

        # Training command
        train_cmd = [
            "accelerate", "launch", "train_dreambooth_lora_sdxl.py",
            "--pretrained_model_name_or_path=stabilityai/stable-diffusion-xl-base-1.0",
            "--pretrained_vae_model_name_or_path=madebyollin/sdxl-vae-fp16-fix",
            "--dataset_name=skyyrose_dataset",
            "--output_dir=skyyrose-lora-v1",
            "--caption_column=prompt",
            "--mixed_precision=fp16",
            "--instance_prompt=skyyrose luxury fashion",
            "--resolution=1024",
            "--train_batch_size=1",
            "--gradient_accumulation_steps=3",
            "--gradient_checkpointing",
            "--learning_rate=1e-4",
            "--snr_gamma=5.0",
            "--lr_scheduler=constant",
            "--lr_warmup_steps=0",
            "--use_8bit_adam",
            "--max_train_steps=1000",
            "--checkpointing_steps=500",
            "--seed=0",
            "--push_to_hub",
            f"--hub_token={os.environ.get('HF_TOKEN', '')}"
        ]

        # Run training with live output
        process = subprocess.Popen(
            train_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        step = 0
        for line in process.stdout:
            line = line.strip()
            if line:
                logs.append(line)

                # Update progress based on steps
                if "Steps:" in line and "/" in line:
                    try:
                        parts = line.split()
                        for part in parts:
                            if "/" in part:
                                current, total = part.split("/")
                                step = int(current)
                                total_steps = int(total)
                                progress_pct = 0.25 + (0.7 * step / total_steps)
                                progress(progress_pct, desc=f"Training step {step}/{total_steps}")
                                break
                    except:
                        pass

                # Only show last 100 lines
                if len(logs) > 100:
                    logs = logs[-100:]

                yield "\\n".join(logs)

        process.wait()

        if process.returncode == 0:
            progress(1.0, desc="Training complete!")
            logs.append("")
            logs.append("=" * 70)
            logs.append("✅ Training Complete!")
            logs.append("=" * 70)
            logs.append("")
            logs.append("📦 Model saved and uploaded to HuggingFace Hub")
            logs.append("   Repository: damBruh/skyyrose-lora-v1")
            logs.append("")
            logs.append("🔗 View model: https://huggingface.co/damBruh/skyyrose-lora-v1")
        else:
            logs.append("")
            logs.append(f"❌ Training failed with exit code {process.returncode}")

    except Exception as e:
        logs.append("")
        logs.append(f"❌ Error: {e}")
        import traceback
        logs.append(traceback.format_exc())

    yield "\\n".join(logs)

# Gradio UI
with gr.Blocks(title="SkyyRose LoRA Trainer", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎨 SkyyRose LoRA Training

    Train a custom LoRA model for SkyyRose luxury fashion brand.

    **Dataset**: damBruh/skyyrose-lora-dataset-v1 (95 images)
    **Base Model**: Stable Diffusion XL
    **Trigger Word**: skyyrose luxury fashion
    """)

    with gr.Row():
        train_btn = gr.Button("🚀 Start Training", variant="primary", size="lg", scale=2)

    output = gr.Textbox(
        label="Training Progress",
        lines=30,
        max_lines=50,
        show_copy_button=True,
        autoscroll=True
    )

    train_btn.click(
        train_lora,
        outputs=output,
        show_progress="full"
    )

    gr.Markdown("""
    ---

    **Training Details:**
    - Duration: ~30-60 minutes on T4 GPU
    - Cost: ~$0.60-$1.00
    - Output: damBruh/skyyrose-lora-v1 on HuggingFace Hub

    **After Training:**
    - Download model from HuggingFace
    - Use with Stable Diffusion XL + prompt: "skyyrose luxury fashion [your description]"

    **Technical Info:**
    - Fixed OMP_NUM_THREADS environment variable issue
    - Configured for T4 GPU (4 CPU threads)
    """)

demo.queue().launch()
'''

print("📝 Uploading fixed app.py...")
api.upload_file(
    path_or_fileobj=app_code.encode(),
    path_in_repo="app.py",
    repo_id=space_id,
    repo_type="space",
    token=HF_TOKEN,
)
print("  ✓ app.py updated with fix")

print()
print("=" * 70)
print("✅ Fix Deployed!")
print("=" * 70)
print()
print(f"🌐 Space: https://huggingface.co/spaces/{space_id}")
print()
print("📋 Next Steps:")
print("  1. Space will restart automatically (~1-2 min)")
print("  2. Refresh browser page")
print("  3. Click '🚀 Start Training' button")
print("  4. Training should start successfully")
print()
print("🔧 What was fixed:")
print("  - Cleared OMP_NUM_THREADS='7500m' (Kubernetes format)")
print("  - Set to OMP_NUM_THREADS='4' (valid integer for T4 GPU)")
print()
