# ✅ Google Colab LoRA Training Guide (FREE)

**Dataset Ready**: https://huggingface.co/datasets/damBruh/skyyrose-lora-dataset-v1

## 🚀 Quick Start (5 Steps)

### 1. Open Colab Notebook
- Link: https://colab.research.google.com/github/huggingface/notebooks/blob/main/diffusers/SDXL_DreamBooth_LoRA_.ipynb
- **Screenshot saved**: `.playwright-mcp/colab_training_notebook.png`

### 2. Enable T4 GPU (REQUIRED)
- Top menu: **Runtime** → **Change runtime type**
- Hardware accelerator: **T4 GPU**
- Click **Save**

### 3. Skip to Cell 13 (Download Dataset)
**Scroll down to the section "Dataset 🐶"**

Find **Cell 13** (has this code):
```python
from huggingface_hub import snapshot_download

local_dir = "./dog/"
snapshot_download(
    "diffusers/dog-example",
    local_dir=local_dir, repo_type="dataset",
    ignore_patterns=".gitattributes",
)
```

**CHANGE IT TO**:
```python
from huggingface_hub import snapshot_download

local_dir = "./skyyrose/"
snapshot_download(
    "damBruh/skyyrose-lora-dataset-v1",  # ← YOUR DATASET
    local_dir=local_dir,
    repo_type="dataset",
    ignore_patterns=".gitattributes",
)
```

### 4. Update Training Parameters (Cell 35)

Find **Cell 35** (training command) and change:
- `--dataset_name="dog"` → `--dataset_name="skyyrose"`
- `--output_dir="corgy_dog_LoRA"` → `--output_dir="skyyrose-lora-v1"`
- `--instance_prompt="a photo of TOK dog"` → `--instance_prompt="skyyrose luxury fashion"`

**Full command** (Cell 35):
```bash
!accelerate launch train_dreambooth_lora_sdxl.py \
  --pretrained_model_name_or_path="stabilityai/stable-diffusion-xl-base-1.0" \
  --pretrained_vae_model_name_or_path="madebyollin/sdxl-vae-fp16-fix" \
  --dataset_name="skyyrose" \
  --output_dir="skyyrose-lora-v1" \
  --caption_column="prompt" \
  --mixed_precision="fp16" \
  --instance_prompt="skyyrose luxury fashion" \
  --resolution=1024 \
  --train_batch_size=1 \
  --gradient_accumulation_steps=3 \
  --gradient_checkpointing \
  --learning_rate=1e-4 \
  --snr_gamma=5.0 \
  --lr_scheduler="constant" \
  --lr_warmup_steps=0 \
  --use_8bit_adam \
  --max_train_steps=1000 \
  --checkpointing_steps=717 \
  --seed="0"
```

### 5. Run Training

**Execute cells in order**:
1. **Cell 1-7**: Setup dependencies (5 min)
2. **Cell 13**: Download YOUR dataset (2 min)
3. **Cell 26**: Configure accelerate (30 sec)
4. **Cell 28**: Login to HuggingFace (enter your token)
5. **Cell 35**: START TRAINING (40-80 min)

---

## 📊 What to Expect

**Training Progress**:
```
Steps: 100% 1000/1000 [40:00<00:00, loss=0.005, lr=0.0001]
```

**On Completion**:
- Model saved to: `skyyrose-lora-v1/`
- Automatically uploads to HuggingFace Hub
- Available at: `https://huggingface.co/YOUR_USERNAME/skyyrose-lora-v1`

---

## 💾 Download Model After Training

**Option A: From Colab** (Cell 37-39)
- Uploads automatically to your HuggingFace account
- Download from: https://huggingface.co/YOUR_USERNAME/skyyrose-lora-v1

**Option B: Local Download**
```python
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="YOUR_USERNAME/skyyrose-lora-v1",
    local_dir="./models/skyyrose_lora"
)
```

---

## 🎨 Test the Model (Cell 42-43)

After training, run inference in Colab:
```python
prompt = "skyyrose luxury black rose hoodie on model"
image = pipe(prompt=prompt, num_inference_steps=25).images[0]
image
```

---

## ⚠️ Troubleshooting

**"SIGKILL: 9" Error** (Out of Memory):
- Reduce `--max_train_steps` from 1000 → 500
- Reduce `--resolution` from 1024 → 512

**"Token Required" Error**:
- Get token: https://huggingface.co/settings/tokens
- Paste in Cell 28 when prompted

**Dataset Not Found**:
- Verify: https://huggingface.co/datasets/damBruh/skyyrose-lora-dataset-v1
- Check dataset is public (not private)

---

## 📋 Summary

✅ **Free** - No billing required
✅ **Fast** - 40-80 minutes on T4 GPU
✅ **Simple** - Change 3 lines of code
✅ **Dataset Ready** - 95 images already uploaded

**Start here**: https://colab.research.google.com/github/huggingface/notebooks/blob/main/diffusers/SDXL_DreamBooth_LoRA_.ipynb
