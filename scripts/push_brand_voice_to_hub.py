"""Push trained SkyyRose brand voice model to HuggingFace Hub."""

import os

from dotenv import load_dotenv
from huggingface_hub import HfApi, create_repo

load_dotenv()

HF_TOKEN = (
    os.getenv("HUGGINGFACE_TOKEN") or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_ACCESS_TOKEN")
)
HF_USERNAME = "damBruh"
REPO_NAME = "skyyrose-brand-voice-llm"
LOCAL_MODEL_PATH = "skyyrose-brand-voice-lora"


def main():
    print("=" * 70)
    print("  PUSH SKYYROSE BRAND VOICE MODEL TO HUGGINGFACE HUB")
    print("=" * 70)
    print()

    if not HF_TOKEN:
        print("✗ HUGGINGFACE_TOKEN not found in environment")
        print("  Set it in .env: HUGGINGFACE_TOKEN=hf_...")
        return

    # Initialize API
    api = HfApi(token=HF_TOKEN)
    repo_id = f"{HF_USERNAME}/{REPO_NAME}"

    # Create repo if it doesn't exist
    print(f"[1/3] Creating repository: {repo_id}")
    try:
        create_repo(repo_id=repo_id, repo_type="model", exist_ok=True, token=HF_TOKEN)
        print(f"✓ Repository ready: https://huggingface.co/{repo_id}")
    except Exception as e:
        print(f"✗ Failed to create repo: {e}")
        return

    # Upload model
    print(f"\n[2/3] Uploading model from {LOCAL_MODEL_PATH}...")
    try:
        api.upload_folder(
            folder_path=LOCAL_MODEL_PATH,
            repo_id=repo_id,
            repo_type="model",
            token=HF_TOKEN,
        )
        print("✓ Model uploaded")
    except Exception as e:
        print(f"✗ Upload failed: {e}")
        return

    # Create model card
    print("\n[3/3] Creating model card...")
    model_card = f"""---
license: apache-2.0
base_model: Qwen/Qwen2.5-0.5B-Instruct
tags:
  - peft
  - lora
  - brand-voice
  - fashion
  - skyyrose
  - luxury-streetwear
---

# SkyyRose Brand Voice LLM

Fine-tuned brand voice model for SkyyRose luxury streetwear. Uses LoRA adapters on Qwen/Qwen2.5-0.5B-Instruct.

## Model Details

- **Base Model**: Qwen/Qwen2.5-0.5B-Instruct (494M parameters)
- **Method**: LoRA (r=16, alpha=32)
- **Trainable Params**: 2.2M (0.44%)
- **Training Data**: 20 brand voice examples
- **Final Loss**: 1.15

## Brand Guidelines

- **Tone**: Sophisticated yet accessible, bold yet elegant
- **Style**: Poetic, evocative, with street culture authenticity
- **Colors**: Rose gold (#B76E79), black (#1A1A1A), pastels
- **Tagline**: "Where Love Meets Luxury"
- **Collections**: Signature (classic), Black Rose (dark romantic), Love Hurts (edgy)

## Usage

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

# Load base model and LoRA adapter
base_model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")
model = PeftModel.from_pretrained(base_model, "{repo_id}")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")

# Generate SkyyRose brand voice content
prompt = \"\"\"<|im_start|>system
You are SkyyRose's brand voice - a luxury streetwear brand from Oakland, California.
<|im_end|>
<|im_start|>user
Write a product description for a rose gold hoodie.
<|im_end|>
<|im_start|>assistant
\"\"\"

inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_length=300, temperature=0.7)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## Training Details

- **Device**: CPU (Apple Silicon M1)
- **Batch Size**: 1
- **Gradient Accumulation**: 4
- **Epochs**: 5
- **Learning Rate**: 3e-4
- **Max Sequence Length**: 256
- **Training Time**: ~11 minutes

## Examples

### Product Description
**Prompt**: "Write a product description for rose gold joggers."

**Output**: "Introducing the SkyyRose Signature Joggers - where Oakland street culture meets luxury comfort. Crafted in our iconic rose gold hue, these premium joggers embody effortless sophistication..."

### Social Media
**Prompt**: "Write an Instagram caption for a new collection drop."

**Output**: "New pieces. Same soul. The latest from SkyyRose - where Oakland authenticity meets global luxury. Limited quantities. Timeless style. 🌹 #WhereloveMeetsLuxury"

## License

Apache 2.0

## Contact

- **Brand**: SkyyRose
- **Website**: https://skyyrose.co
- **HuggingFace**: https://huggingface.co/{HF_USERNAME}
"""

    try:
        api.upload_file(
            path_or_fileobj=model_card.encode(),
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type="model",
            token=HF_TOKEN,
        )
        print("✓ Model card created")
    except Exception as e:
        print(f"⚠ Model card upload failed: {e}")

    print()
    print("=" * 70)
    print("  UPLOAD COMPLETE")
    print("=" * 70)
    print(f"\n✓ Model available at: https://huggingface.co/{repo_id}")
    print("\nUse in your code:")
    print(f'  model = PeftModel.from_pretrained(base_model, "{repo_id}")')


if __name__ == "__main__":
    main()
