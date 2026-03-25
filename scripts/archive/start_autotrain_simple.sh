#!/bin/bash
# Simple AutoTrain starter script
# Run after adding billing credits: https://huggingface.co/settings/billing

set -e

echo "=================================="
echo "🚀 SkyyRose LoRA AutoTrain Starter"
echo "=================================="
echo ""

# Check if HF token is set
if [ -z "$HUGGINGFACE_API_TOKEN" ]; then
    echo "❌ HUGGINGFACE_API_TOKEN not set"
    echo ""
    echo "Add to .env:"
    echo "  HUGGINGFACE_API_TOKEN=hf_..."
    exit 1
fi

echo "✓ HuggingFace token found"
echo ""

# Login to HuggingFace
echo "🔐 Logging in to HuggingFace..."
huggingface-cli login --token "$HUGGINGFACE_API_TOKEN" --add-to-git-credential

echo ""
echo "📋 Training Configuration:"
echo "  Dataset: damBruh/skyyrose-lora-dataset-v1"
echo "  Base Model: SDXL"
echo "  Trigger: skyyrose"
echo "  Steps: 1000"
echo "  Cost: ~\$0.60-\$1.00"
echo ""

read -p "Start training now? [y/N]: " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Starting AutoTrain..."
    echo "⏱️  This will take 30-60 minutes"
    echo ""

    # Start training (will fail if no billing credits)
    autotrain dreambooth \
      --model stabilityai/stable-diffusion-xl-base-1.0 \
      --project-name skyyrose-lora-v1 \
      --image-path "hf://datasets/damBruh/skyyrose-lora-dataset-v1" \
      --prompt "skyyrose luxury fashion" \
      --learning-rate 1e-4 \
      --num-steps 1000 \
      --batch-size 1 \
      --resolution 512 \
      --rank 16 \
      --push-to-hub \
      --hub-model-id damBruh/skyyrose-lora-v1 \
      || {
        echo ""
        echo "❌ Training failed"
        echo ""
        echo "Common issues:"
        echo "  1. No billing credits: https://huggingface.co/settings/billing"
        echo "  2. AutoTrain not installed: pip install autotrain-advanced"
        echo "  3. Python 3.13+: Use Python 3.12 instead"
        exit 1
      }

    echo ""
    echo "✅ Training started!"
    echo "📊 Monitor at: https://huggingface.co/damBruh/skyyrose-lora-v1"
else
    echo ""
    echo "⏸️  Training cancelled"
fi
