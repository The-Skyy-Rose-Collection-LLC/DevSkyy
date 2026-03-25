# SkyyRose Fine-Tuning Guide

## Overview

Fine-tune custom models for SkyyRose brand consistency:
- **Image LoRA** (Replicate) - Flux/SDXL for product generation
- **LLM Fine-tuning** (HuggingFace) - Brand voice for descriptions

## Training Status

| Model | Provider | Status | Location |
|-------|----------|--------|----------|
| Image LoRA v4 | Replicate | ✅ **COMPLETE** | `devskyy/skyyrose-lora-v4` |
| Brand Voice LLM | HuggingFace | ⏳ Pending | Use Colab notebook |

### Image LoRA (Completed)
- **Model**: `devskyy/skyyrose-lora-v4:5c5b843363b5f8ffb8fa10288d9dfd2496b963c37934faea004341bcd7a28f14`
- **Trigger word**: `skyyrose`
- **Training**: 105 images, 1000 steps
- **Test**: https://replicate.delivery/xezq/qgTaemvqeEl4FkLloGYVrWeCChI1tcGz7jfVwkFmrJkbyoEYB/out-0.webp

### LLM Training Options
1. **Google Colab** (FREE GPU): `scripts/training/skyyrose_brand_voice_colab.ipynb`
2. **HF Jobs** (requires credits): Add at https://huggingface.co/settings/billing
3. **Local GPU**: Run `scripts/training/train_brand_voice.py`

## API Key Status

| Service | Status | Action Required |
|---------|--------|-----------------|
| Replicate | ✅ Working | None |
| HuggingFace | ✅ Working | Add credits for Jobs |
| Claude | ✅ Working | None |
| GPT-4 | ✅ Working | None |
| Mistral | ❌ Invalid | Get new key |
| Gemini | ✅ Working | None |
| Groq | ✅ Working | None |
| Cohere | ✅ Working | model: command-a-03-2025 |

## Quick Start

### 1. Update API Keys

Edit `.env` and update these keys:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-proj-...
MISTRAL_API_KEY=...
HF_TOKEN=hf_...  # Write access required
```

### 2. Train Image LoRA (Replicate)

```bash
python scripts/training/finetune_pipeline.py image
```

This will:
- Prepare images from `datasets/skyyrose_lora_v1/`
- Upload to HuggingFace as training zip
- Start Flux LoRA training on Replicate
- Output model at: `replicate.com/dambruh/skyyrose-lora-v4`

**Trigger word:** `skyyrose`

### 3. Train LLM (HuggingFace)

```bash
python scripts/training/finetune_pipeline.py llm
```

This will:
- Prepare chat dataset from brand examples
- Generate AutoTrain config
- Output config for HuggingFace training

**Base model:** `meta-llama/Llama-3.2-3B-Instruct`

### 4. Train Both

```bash
python scripts/training/finetune_pipeline.py all
```

## Training Data

### Image Dataset
- Location: `datasets/skyyrose_lora_v1/`
- Images: 100+ product photos
- Captions: `metadata.jsonl`

### LLM Dataset
- Location: `datasets/skyyrose_brand_voice/train.jsonl`
- Format: Chat conversations (system + user + assistant)
- Examples: 5 high-quality brand voice samples

## Adding More LLM Training Examples

Edit `scripts/training/finetune_pipeline.py` and add to `SKYYROSE_BRAND_EXAMPLES`:

```python
{
    "input": "Your prompt here",
    "output": "Ideal brand-voice response here"
}
```

Guidelines for examples:
- Use SkyyRose brand voice (sophisticated, Oakland authentic)
- Include product descriptions, marketing copy, social captions
- Emphasize: luxury, premium quality, limited edition
- Avoid: cheap, discount, basic, generic

## Fine-Tuned Model Usage

### Image Generation

```python
import replicate

output = replicate.run(
    "dambruh/skyyrose-lora-v4:latest",
    input={
        "prompt": "skyyrose luxury hoodie, rose gold accents, premium fabric",
        "num_outputs": 1,
    }
)
```

### LLM Brand Voice

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("damBruh/skyyrose-brand-voice-llm")
tokenizer = AutoTokenizer.from_pretrained("damBruh/skyyrose-brand-voice-llm")

# Generate product description
prompt = "Write a product description for the Black Rose Sherpa jacket."
# ...
```

## Integration with Round Table

After fine-tuning, register the custom model as a Round Table provider:

```python
# In llm/round_table.py
async def skyyrose_generator(prompt: str, context: dict | None = None):
    # Call fine-tuned model
    ...

rt.register_provider(LLMProvider.SKYYROSE, skyyrose_generator)
```

## Monitoring Training

### Replicate
- Dashboard: https://replicate.com/trainings
- Logs: Real-time in terminal or web UI

### HuggingFace
- AutoTrain: https://huggingface.co/spaces/autotrain-projects/autotrain-advanced
- TensorBoard: Enabled in training config

## Costs

| Training Type | Provider | Estimated Cost |
|---------------|----------|----------------|
| Image LoRA (1000 steps) | Replicate | ~$5-10 |
| LLM Fine-tune (3 epochs) | HuggingFace | ~$2-5 (A10G Small) |

## Troubleshooting

### "Unauthorized" errors
- Check API key validity
- Ensure HF token has write access
- Verify Replicate billing is active

### Training fails to start
- Check dataset format matches expected schema
- Verify images are valid (not corrupted)
- Check HuggingFace dataset is accessible

### Low quality results
- Increase training steps/epochs
- Add more diverse training examples
- Adjust learning rate (lower = more stable)
