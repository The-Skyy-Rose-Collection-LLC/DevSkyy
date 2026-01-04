#!/bin/bash
# Download SDXL and related models for local image generation
# Total size: ~20GB - ensure sufficient disk space

set -e

MODEL_DIR="${1:-./models}"
echo "Downloading models to: $MODEL_DIR"
echo "This will download approximately 20GB of model files."
echo ""

# Check disk space
AVAILABLE_GB=$(df -g . | tail -1 | awk '{print $4}')
echo "Available disk space: ${AVAILABLE_GB}GB"
if [ "$AVAILABLE_GB" -lt 25 ]; then
    echo "WARNING: Less than 25GB available. Consider freeing space."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "1/5: SDXL Base Model (~6.5GB)"
echo "=========================================="
huggingface-cli download stabilityai/stable-diffusion-xl-base-1.0 \
    --local-dir "$MODEL_DIR/sdxl-base" \
    --include "*.safetensors" "*.json" "*.txt" \
    --exclude "*.ckpt" "*.bin"

echo ""
echo "=========================================="
echo "2/5: SDXL Refiner (~6GB)"
echo "=========================================="
huggingface-cli download stabilityai/stable-diffusion-xl-refiner-1.0 \
    --local-dir "$MODEL_DIR/sdxl-refiner" \
    --include "*.safetensors" "*.json" "*.txt" \
    --exclude "*.ckpt" "*.bin"

echo ""
echo "=========================================="
echo "3/5: ControlNet Canny (~2.5GB)"
echo "=========================================="
huggingface-cli download diffusers/controlnet-canny-sdxl-1.0 \
    --local-dir "$MODEL_DIR/controlnet-canny"

echo ""
echo "=========================================="
echo "4/5: ControlNet Depth (~2.5GB)"
echo "=========================================="
huggingface-cli download diffusers/controlnet-depth-sdxl-1.0 \
    --local-dir "$MODEL_DIR/controlnet-depth"

echo ""
echo "=========================================="
echo "5/5: IP-Adapter (~2GB)"
echo "=========================================="
huggingface-cli download h94/IP-Adapter \
    --local-dir "$MODEL_DIR/ip-adapter" \
    --include "sdxl_models/*"

echo ""
echo "=========================================="
echo "Download complete!"
echo "=========================================="
echo "Models saved to: $MODEL_DIR"
du -sh "$MODEL_DIR"/*
