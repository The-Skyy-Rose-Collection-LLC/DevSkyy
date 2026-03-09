#!/bin/bash
#
# HuggingFace Spaces Deployment Script
# =====================================
#
# Deploys all three SkyyRose HuggingFace Spaces:
#   1. 3d-converter
#   2. lora-training-monitor
#   3. virtual-tryon
#
# Prerequisites:
#   - HuggingFace CLI installed: pip install -U huggingface_hub[cli]
#   - Authenticated: hf auth login
#
# Usage:
#   chmod +x scripts/deploy_hf_spaces.sh
#   ./scripts/deploy_hf_spaces.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/Users/coreyfoster/DevSkyy"
SPACES_DIR="$PROJECT_ROOT/hf-spaces"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         SkyyRose HuggingFace Spaces Deployment                        ║${NC}"
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
echo ""

# Check authentication
echo -e "${YELLOW}[1/4] Checking HuggingFace authentication...${NC}"
if ! hf auth whoami &>/dev/null; then
    echo -e "${RED}❌ Not authenticated with HuggingFace!${NC}"
    echo ""
    echo "Please run one of:"
    echo "  hf auth login                          # Interactive login"
    echo "  hf auth login --token YOUR_TOKEN_HERE  # Token-based login"
    echo ""
    echo "Get your token from: https://huggingface.co/settings/tokens"
    exit 1
fi

USERNAME=$(hf auth whoami | head -n 1)
echo -e "${GREEN}✓ Authenticated as: $USERNAME${NC}"
echo ""

# Deploy 3D Converter
echo -e "${YELLOW}[2/4] Deploying 3d-converter...${NC}"
cd "$SPACES_DIR/3d-converter"

if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Not a git repository. Please initialize first.${NC}"
    exit 1
fi

# Check for changes
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "   Staging changes..."
    git add .
    git commit -m "feat: deploy 3D converter space (GLB/FBX/OBJ conversion)" || true
fi

echo "   Pushing to HuggingFace..."
git push space main || git push space main --force
echo -e "${GREEN}✓ 3d-converter deployed!${NC}"
echo "   URL: https://huggingface.co/spaces/damBruh/skyyrose-3d-converter"
echo ""

# Deploy LoRA Training Monitor
echo -e "${YELLOW}[3/4] Deploying lora-training-monitor...${NC}"
cd "$SPACES_DIR/lora-training-monitor"

if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Not a git repository. Please initialize first.${NC}"
    exit 1
fi

# Check for changes
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "   Staging changes..."
    git add .
    git commit -m "feat: deploy LoRA training monitor space" || true
fi

echo "   Pushing to HuggingFace..."
git push space main || git push space main --force
echo -e "${GREEN}✓ lora-training-monitor deployed!${NC}"
echo "   URL: https://huggingface.co/spaces/damBruh/skyyrose-lora-training-monitor"
echo ""

# Deploy Virtual Try-On
echo -e "${YELLOW}[4/4] Deploying virtual-tryon...${NC}"
cd "$SPACES_DIR/virtual-tryon"

if [ ! -d ".git" ]; then
    echo "   Initializing git repository..."
    git init
    git branch -M main
fi

# Check for remote
if ! git remote | grep -q "space"; then
    echo "   Adding HuggingFace remote..."
    git remote add space https://huggingface.co/spaces/damBruh/skyyrose-virtual-tryon
fi

# Stage and commit
if ! git diff --quiet || ! git diff --cached --quiet || [ -z "$(git log 2>/dev/null)" ]; then
    echo "   Staging changes..."
    git add .
    git commit -m "feat: deploy virtual try-on space (FASHN integration)" || true
fi

echo "   Pushing to HuggingFace..."
git push space main || git push space main --force
echo -e "${GREEN}✓ virtual-tryon deployed!${NC}"
echo "   URL: https://huggingface.co/spaces/damBruh/skyyrose-virtual-tryon"
echo ""

# Summary
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                     Deployment Complete!                              ║${NC}"
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════════╗${NC}"
echo ""
echo -e "${GREEN}All three HuggingFace Spaces have been deployed successfully!${NC}"
echo ""
echo "Space URLs:"
echo "  1. 3D Converter:          https://huggingface.co/spaces/damBruh/skyyrose-3d-converter"
echo "  2. LoRA Training Monitor: https://huggingface.co/spaces/damBruh/skyyrose-lora-training-monitor"
echo "  3. Virtual Try-On:        https://huggingface.co/spaces/damBruh/skyyrose-virtual-tryon"
echo ""
echo -e "${YELLOW}Note: Spaces may take 2-3 minutes to build and deploy.${NC}"
echo "Check build status in the 'Logs' tab of each Space."
echo ""
