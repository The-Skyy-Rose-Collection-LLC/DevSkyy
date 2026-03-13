# HuggingFace AutoTrain Setup Guide

## ⚡ Quick Start (5 minutes)

### Step 1: Add Billing (Required for GPU)
1. Go to: https://huggingface.co/settings/billing
2. Add payment method
3. Add $5-10 credits (training costs ~$0.60-$1.00)

### Step 2: Start Training
1. Open: https://huggingface.co/new?cardData=eyJsaWNlbnNlIjogIm1pdCIsICJ0YXNrX2NhdGVnb3JpZXMiOiBbInRleHQtdG8taW1hZ2UiXSwgInRhZ3MiOiBbImRpZmZ1c2VycyJdfQ%3D%3D
2. Click "Create model"
3. Fill in:
   - **Model name**: `skyyrose-lora-v1`
   - **Visibility**: Public
4. Click "Create model repository"

### Step 3: Upload Training Config
Create a file `autotrain_config.yaml`:

```yaml
task: dreambooth
base_model: stabilityai/stable-diffusion-xl-base-1.0

data:
  dataset_id: damBruh/skyyrose-lora-dataset-v1
  prompt: skyyrose luxury fashion

training:
  learning_rate: 1e-4
  num_steps: 1000
  batch_size: 1
  gradient_accumulation_steps: 4
  resolution: 512

lora:
  rank: 16

output:
  push_to_hub: true
  repo_id: damBruh/skyyrose-lora-v1
```

### Step 4: Start Training via CLI

```bash
# Install AutoTrain (use Python 3.12 if you have it)
pip install autotrain-advanced

# Login to HuggingFace
huggingface-cli login

# Start training
autotrain dreambooth \
  --model stabilityai/stable-diffusion-xl-base-1.0 \
  --project-name skyyrose-lora-v1 \
  --image-path hf://datasets/damBruh/skyyrose-lora-dataset-v1 \
  --prompt "skyyrose luxury fashion" \
  --learning-rate 1e-4 \
  --num-steps 1000 \
  --batch-size 1 \
  --resolution 512 \
  --rank 16 \
  --push-to-hub \
  --hub-model-id damBruh/skyyrose-lora-v1
```

---

## 🔄 Alternative: Use Colab (Free T4 GPU)

If you don't want to pay HuggingFace:

1. Open: https://colab.research.google.com/
2. New notebook
3. Runtime → Change runtime type → T4 GPU
4. Paste this code:

```python
# Install dependencies
!pip install -q diffusers transformers accelerate peft

# Login to HuggingFace
from huggingface_hub import notebook_login
notebook_login()

# Download dataset
from huggingface_hub import snapshot_download
dataset_path = snapshot_download(
    repo_id="damBruh/skyyrose-lora-dataset-v1",
    repo_type="dataset"
)

# Configure training
from diffusers import DiffusionPipeline
import torch

model_id = "stabilityai/stable-diffusion-xl-base-1.0"

# Load model
pipe = DiffusionPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    use_safetensors=True
)

# TODO: Add LoRA training code here
# (Full Colab notebook available at: https://colab.research.google.com/github/huggingface/notebooks/blob/main/diffusers/SDXL_DreamBooth_LoRA_.ipynb)
```

---

## 📊 Cost Comparison

| Method | Cost | Time | Complexity |
|--------|------|------|------------|
| HuggingFace AutoTrain | $0.60-$1 | 30-60 min | Low |
| Google Colab (Free T4) | Free | 40-80 min | Medium |
| Local GPU (RTX 3090+) | Free | 30-60 min | High |

---

## 🎯 Recommended: Add $5 to HuggingFace Billing

**Fastest path:**
1. https://huggingface.co/settings/billing → Add $5
2. Run training command (see Step 4 above)
3. Done in ~1 hour

**Dataset is ready**: https://huggingface.co/datasets/damBruh/skyyrose-lora-dataset-v1
