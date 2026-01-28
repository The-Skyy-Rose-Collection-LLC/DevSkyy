# DevSkyy Notebooks

> Reproducible, documented, versioned | 1 file

## Architecture
```
notebooks/
└── skyyrose_lora_training.ipynb    # LoRA fine-tuning
```

## Pattern
```python
# Cell 1: Configuration
CONFIG = {
    "model_name": "stabilityai/stable-diffusion-xl-base-1.0",
    "lora_rank": 32,
    "learning_rate": 1e-4,
    "epochs": 100,
}

# Cell 2: Dataset
dataset = load_dataset("imagefolder", data_dir="./data/training")

# Cell 3: Training
# ... training loop with checkpoints
```

## Standards
| Standard | Requirement |
|----------|-------------|
| Header | Purpose, prerequisites |
| Config | All params in one cell |
| Checkpoints | Save every N steps |
| Outputs | Clear before commit |

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change

## USE THESE TOOLS
| Task | Tool |
|------|------|
| Model search | **MCP**: HuggingFace `model_search` |
| Dataset ops | **MCP**: HuggingFace `dataset_search` |

**"A notebook should run top-to-bottom without errors."**
