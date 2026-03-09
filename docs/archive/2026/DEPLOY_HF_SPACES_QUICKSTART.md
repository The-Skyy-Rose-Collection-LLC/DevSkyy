# HuggingFace Spaces Deployment - Quick Start

## TL;DR - One Command Deployment

```bash
# 1. Authenticate (get token from https://huggingface.co/settings/tokens)
hf auth login --token YOUR_TOKEN_HERE

# 2. Deploy all 3 spaces
cd /Users/coreyfoster/DevSkyy
./scripts/deploy_hf_spaces.sh
```

That's it! 🎉

---

## What Gets Deployed

| Space | URL | Purpose |
|-------|-----|---------|
| **3D Converter** | [damBruh/skyyrose-3d-converter](https://huggingface.co/spaces/damBruh/skyyrose-3d-converter) | Convert product images to 3D models (GLB) |
| **LoRA Monitor** | [damBruh/skyyrose-lora-training-monitor](https://huggingface.co/spaces/damBruh/skyyrose-lora-training-monitor) | Monitor LoRA training progress |
| **Virtual Try-On** | [damBruh/skyyrose-virtual-tryon](https://huggingface.co/spaces/damBruh/skyyrose-virtual-tryon) | AI-powered virtual try-on (FASHN) |

---

## Pre-Deployment Checklist

- [ ] HuggingFace CLI installed: `pip install -U "huggingface_hub[cli]"`
- [ ] Token obtained from <https://huggingface.co/settings/tokens> (Type: **Write**)
- [ ] Authenticated: `hf auth login --token YOUR_TOKEN`
- [ ] Verified: `hf auth whoami` shows `damBruh`

---

## Post-Deployment

### 1. Verify Builds (2-3 minutes)

Check build status:

- <https://huggingface.co/spaces/damBruh/skyyrose-3d-converter/logs>
- <https://huggingface.co/spaces/damBruh/skyyrose-lora-training-monitor/logs>
- <https://huggingface.co/spaces/damBruh/skyyrose-virtual-tryon/logs>

### 2. Configure Secrets (Virtual Try-On)

If using FASHN API:

1. Visit: <https://huggingface.co/spaces/damBruh/skyyrose-virtual-tryon/settings>
2. Add secret: `FASHN_API_KEY` = your FASHN API key  <!-- pragma: allowlist secret -->

### 3. Test Spaces

- **3D Converter**: Upload product image → Generate 3D → Download GLB
- **LoRA Monitor**: View training dashboard, explore dataset
- **Virtual Try-On**: Upload person + garment photos → See try-on result

---

## Manual Deployment (if automated script fails)

```bash
# Space 1: 3D Converter
cd /Users/coreyfoster/DevSkyy/hf-spaces/3d-converter
git add . && git commit -m "feat: deploy 3D converter space"
git push space main

# Space 2: LoRA Monitor
cd ../lora-training-monitor
git add . && git commit -m "feat: deploy LoRA monitor space"
git push space main

# Space 3: Virtual Try-On
cd ../virtual-tryon
git init && git branch -M main
git remote add space https://huggingface.co/spaces/damBruh/skyyrose-virtual-tryon
git add . && git commit -m "feat: deploy virtual try-on space"
git push space main -f
```

---

## Troubleshooting

### "Not logged in" error

```bash
hf auth login --token YOUR_TOKEN
```

### Push rejected

```bash
git push space main --force
```

### Build failures

Check logs in Space settings → "Logs" tab

---

## Files Created

- `/Users/coreyfoster/DevSkyy/scripts/deploy_hf_spaces.sh` - Automated deployment script
- `/Users/coreyfoster/DevSkyy/HF_SPACES_DEPLOYMENT.md` - Full deployment guide
- `/Users/coreyfoster/DevSkyy/DEPLOY_HF_SPACES_QUICKSTART.md` - This file
- `/Users/coreyfoster/DevSkyy/hf-spaces/virtual-tryon/app.py` - Production FASHN integration

---

**Ready to deploy?** Run the command at the top of this file! 🚀
