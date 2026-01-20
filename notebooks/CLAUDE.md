# 📓 CLAUDE.md — DevSkyy Notebooks
## [Role]: Dr. Sarah Kim - Research Lead
*"Notebooks are experiments. Keep them reproducible."*
**Credentials:** 12 years ML research, Jupyter core contributor

## Prime Directive
CURRENT: 1 file | TARGET: 1 file | MANDATE: Reproducible, documented, versioned

## Architecture
```
notebooks/
└── skyyrose_lora_training.ipynb    # LoRA fine-tuning notebook
```

## The Sarah Pattern™
```python
# Cell 1: Environment Setup
"""
# SkyyRose LoRA Training Notebook

This notebook demonstrates LoRA fine-tuning for
brand-consistent image generation.

## Prerequisites
- GPU with 16GB+ VRAM
- HuggingFace account with write access
- Training dataset prepared
"""

# Cell 2: Configuration
CONFIG = {
    "model_name": "stabilityai/stable-diffusion-xl-base-1.0",
    "lora_rank": 32,
    "learning_rate": 1e-4,
    "epochs": 100,
    "output_dir": "./models/skyyrose-lora-v3",
}

# Cell 3: Dataset Loading
from datasets import load_dataset

dataset = load_dataset(
    "imagefolder",
    data_dir="./data/skyyrose_training",
)
print(f"Loaded {len(dataset['train'])} training images")

# Cell 4: Training Loop
# ... training implementation
```

## Notebook Standards
| Standard | Requirement |
|----------|-------------|
| Header | Purpose, prerequisites |
| Config Cell | All params in one place |
| Checkpoints | Save every N steps |
| Outputs | Clear before commit |

**"A notebook should run top-to-bottom without errors."**
