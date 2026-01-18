# HuggingFace Spaces Deployment Guide

## Overview

Deploy three production-ready SkyyRose HuggingFace Spaces:

1. **3d-converter** - Convert product images to 3D models (TripoSR)
2. **lora-training-monitor** - Monitor LoRA training progress in real-time
3. **virtual-tryon** - Virtual try-on using FASHN AI

---

## Prerequisites

### 1. Install HuggingFace CLI

```bash
pip install -U "huggingface_hub[cli]"
```

### 2. Authenticate with HuggingFace

**Option A: Interactive Login**

```bash
hf auth login
```

**Option B: Token-Based Login (Recommended)**

```bash
# Get token from: https://huggingface.co/settings/tokens
# Click "New token" → Name: "skyyrose-spaces-deploy" → Type: "Write"
hf auth login --token YOUR_TOKEN_HERE
```

### 3. Verify Authentication

```bash
hf auth whoami
# Should display: damBruh
```

---

## Automated Deployment (Recommended)

### Single Command Deployment

```bash
cd /Users/coreyfoster/DevSkyy
./scripts/deploy_hf_spaces.sh
```

This script will:

- ✓ Check HuggingFace authentication
- ✓ Deploy all three spaces in sequence
- ✓ Handle git commits and pushes
- ✓ Display deployment URLs

---

## Manual Deployment

### Space 1: 3D Converter

```bash
cd /Users/coreyfoster/DevSkyy/hf-spaces/3d-converter

# Stage and commit changes
git add .
git commit -m "feat: deploy 3D converter space (GLB/FBX/OBJ conversion)"

# Push to HuggingFace
git push space main
```

**URL**: <https://huggingface.co/spaces/damBruh/skyyrose-3d-converter>

---

### Space 2: LoRA Training Monitor

```bash
cd /Users/coreyfoster/DevSkyy/hf-spaces/lora-training-monitor

# Stage and commit changes
git add .
git commit -m "feat: deploy LoRA training monitor space"

# Push to HuggingFace
git push space main
```

**URL**: <https://huggingface.co/spaces/damBruh/skyyrose-lora-training-monitor>

---

### Space 3: Virtual Try-On

```bash
cd /Users/coreyfoster/DevSkyy/hf-spaces/virtual-tryon

# Initialize git if needed
git init
git branch -M main

# Add HuggingFace remote
git remote add space https://huggingface.co/spaces/damBruh/skyyrose-virtual-tryon

# Stage and commit
git add .
git commit -m "feat: deploy virtual try-on space (FASHN integration)"

# Push to HuggingFace
git push space main -f
```

**URL**: <https://huggingface.co/spaces/damBruh/skyyrose-virtual-tryon>

---

## Post-Deployment

### 1. Verify Builds

Visit each Space and check the **Logs** tab:

- 3D Converter: <https://huggingface.co/spaces/damBruh/skyyrose-3d-converter/logs>
- LoRA Monitor: <https://huggingface.co/spaces/damBruh/skyyrose-lora-training-monitor/logs>
- Virtual Try-On: <https://huggingface.co/spaces/damBruh/skyyrose-virtual-tryon/logs>

**Build time**: ~2-3 minutes per Space

### 2. Configure Secrets (Virtual Try-On)

The Virtual Try-On space requires a FASHN API key:

1. Visit: <https://huggingface.co/spaces/damBruh/skyyrose-virtual-tryon/settings>
2. Click "Variables and secrets"
3. Add secret:
   - Name: `FASHN_API_KEY`
   - Value: Your FASHN API key from <https://fashn.ai/dashboard>

### 3. Test Each Space

- **3D Converter**: Upload a product image → Generate 3D model → Download GLB
- **LoRA Monitor**: View version history, dataset explorer, product mapping
- **Virtual Try-On**: Upload person photo + garment image → Generate try-on result

---

## Troubleshooting

### Authentication Issues

**Problem**: `Not logged in` error

**Solution**:

```bash
# Check current authentication
hf auth whoami

# Re-authenticate
hf auth login --token YOUR_TOKEN_HERE
```

### Git Push Failures

**Problem**: `! [rejected] main -> main (fetch first)`

**Solution**:

```bash
# Force push (safe for Spaces deployment)
git push space main --force
```

### Build Failures

**Problem**: Space fails to build

**Solutions**:

1. Check requirements.txt dependencies
2. Verify README.md frontmatter (sdk, sdk_version)
3. Check app.py for syntax errors
4. Review build logs for specific errors

---

## Space URLs (Quick Reference)

| Space | URL | Status |
|-------|-----|--------|
| 3D Converter | <https://huggingface.co/spaces/damBruh/skyyrose-3d-converter> | ✓ Ready |
| LoRA Monitor | <https://huggingface.co/spaces/damBruh/skyyrose-lora-training-monitor> | ✓ Ready |
| Virtual Try-On | <https://huggingface.co/spaces/damBruh/skyyrose-virtual-tryon> | ✓ Ready |

---

## Architecture Notes

### 3D Converter

- **Backend**: TripoSR (Stability AI)
- **GPU**: T4 (free tier)
- **Input**: Product images (PNG/JPG)
- **Output**: 3D models (GLB format)

### LoRA Training Monitor

- **Backend**: Gradio dashboard
- **Data Source**: SQLite database + progress JSON
- **Features**: Live metrics, dataset explorer, version comparison

### Virtual Try-On

- **Backend**: FASHN API (external)
- **API Key**: Required (set via Secrets)
- **Input**: Person photo + garment image
- **Output**: Virtual try-on result image

---

## Next Steps

After successful deployment:

1. **Embed in WordPress**:
   - Use iframe embed codes
   - Create WooCommerce product pages with AR viewers
   - Integrate virtual try-on in product galleries

2. **Link Spaces**:
   - Add cross-links between Spaces
   - Create unified SkyyRose Spaces collection

3. **Monitor Usage**:
   - Check HuggingFace analytics
   - Review user feedback
   - Optimize based on usage patterns

4. **Upgrade to Pro** (if needed):
   - Better GPU (A100)
   - More concurrent users
   - Persistent storage
   - Custom domains

---

**Last Updated**: 2026-01-08
**Status**: Production-ready, pending authentication
**Author**: DevSkyy Platform Team
