# HuggingFace Authentication Guide

**Issue**: Interactive login (`huggingface-cli login`) doesn't work in this environment.

---

## ✅ **Option 1: Token-Based Login (Recommended)**

### Step 1: Get Your HuggingFace Token

1. Visit: <https://huggingface.co/settings/tokens>
2. Click "New token"
3. Name: `skyyrose-lora-upload`
4. Type: **Write** (required for uploading datasets)
5. Copy the token (starts with `hf_...`)

### Step 2: Login with Token

```bash
# Use the new command
hf auth login --token YOUR_TOKEN_HERE

# Or set as environment variable
export HUGGINGFACE_TOKEN=YOUR_TOKEN_HERE
```

### Step 3: Upload Dataset

```bash
cd /Users/coreyfoster/DevSkyy/scripts
python3 upload_lora_dataset_to_hf.py
```

---

## ✅ **Option 2: Web UI Upload (Easiest)**

1. Visit: <https://huggingface.co/new-dataset>
2. Dataset name: `skyyrose-lora-dataset-v1`
3. Public/Private: **Public**
4. Click "Create dataset"
5. Click "Files and versions" tab
6. Click "Upload files"
7. Upload entire folder: `/Users/coreyfoster/DevSkyy/datasets/skyyrose_lora_v1/`
8. Commit message: `Initial upload: 95 images (SIGNATURE, BLACK_ROSE, LOVE_HURTS + logos)`

---

## ✅ **Option 3: Git LFS (Advanced)**

```bash
cd /Users/coreyfoster/DevSkyy/datasets

# Clone the dataset repo
git clone https://huggingface.co/datasets/damBruh/skyyrose-lora-dataset-v1
cd skyyrose-lora-dataset-v1

# Copy dataset files
cp -r ../skyyrose_lora_v1/* .

# Track large files with Git LFS
git lfs track "*.jpg"
git add .gitattributes
git add .
git commit -m "feat: SkyyRose LoRA dataset v1 - 95 images"
git push
```

---

## 📋 **What Needs to be Uploaded**

**Directory**: `/Users/coreyfoster/DevSkyy/datasets/skyyrose_lora_v1/`

**Files** (95 images + 3 metadata files):

- `metadata.jsonl` - Training captions for all images
- `dataset_manifest.json` - Brand DNA and dataset info
- `training_config.json` - SDXL training configuration
- 40 SIGNATURE collection images (`.jpg`)
- 2 BLACK_ROSE collection images (`.jpg`)
- 53 LOVE_HURTS collection images (`.jpg`)

**Total Size**: ~150-200 MB

---

## 🔗 **After Upload**

Once uploaded, the dataset will be available at:

```
https://huggingface.co/datasets/damBruh/skyyrose-lora-dataset-v1
```

Then configure it in the training monitor Space:

```
https://huggingface.co/spaces/damBruh/skyyrose-lora-training-monitor
```

---

## ⚠️ **Security Note**

- **NEVER commit your token to git**
- Use environment variables or `.env` files (gitignored)
- Tokens should have minimal required permissions (Write for uploads)
- Rotate tokens regularly

---

**Need Help?**

- HuggingFace Docs: <https://huggingface.co/docs/huggingface_hub/guides/upload>
- Token Guide: <https://huggingface.co/docs/hub/security-tokens>
