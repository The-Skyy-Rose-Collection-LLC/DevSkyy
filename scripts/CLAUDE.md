# DevSkyy Scripts

> 175 scripts | AI CLI, 3D generation, deployment, training

## Key Scripts

| Script | Purpose |
|--------|---------|
| `ai.py` | AI CLI — spaces, train, dataset, model subcommands |
| `nano-banana-vton.py` | 3D product renders via Gemini |
| `generate-theme-imagery.py` | About page, Instagram, mascot generation |
| `deploy_*.py` | Deployment scripts (WordPress, Vercel, HF) |
| `train_lora_*.py` | LoRA fine-tuning scripts |

## AI CLI (newest)

```bash
python scripts/ai.py spaces list
python scripts/ai.py train start --provider replicate
python scripts/ai.py dataset create --name my-dataset
python scripts/ai.py model info --name my-model
```

Supporting modules: `ai_config.py`, `ai_providers.py`, `ai_templates.py`

## Categories

```
scripts/
├── ai*.py                   # AI CLI + config + providers + templates
├── nano-banana-vton.py      # 3D render pipeline (Gemini)
├── generate-theme-imagery.py # Theme asset generation
├── deploy_*.py              # Deployment (8 scripts)
├── train_*.py               # ML training (6 scripts)
├── generate_*_3d*.py        # 3D asset generation (6 scripts)
├── enhance_*.py             # Image enhancement (4 scripts)
├── upload_*.py              # HF/cloud uploads
└── *.sh                     # Shell utilities (install, setup)
```

## Verification

```bash
# Run AI CLI tests
pytest tests/scripts/ -v

# Check CLI help
python scripts/ai.py --help
```

**"175 scripts with a CLI to rule them all."**
