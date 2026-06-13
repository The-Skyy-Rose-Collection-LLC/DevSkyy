# models/ — SkyyRose LoRA model registry

Local registry for SkyyRose FLUX LoRA checkpoints. Stores training metadata, trigger maps, and test images for v3/v4. Weights are not stored locally — they live on Replicate and HuggingFace.

## Key files

- `skyyrose-lora-v3-info.json` — v3 training manifest: model ID `devskyy/skyyrose-lora-v3`, trigger word `skyyrose`, 1000 steps, rank 16, dataset `damBruh/skyyrose-lora-dataset-v3` (390 images). Replicate weights URL included.
- `skyyrose-lora-v4-info.json` — v4 training manifest (same structure as v3).
- `skyyrose-lora-v4-trigger-map.json` — Per-collection trigger word map for v4. Use this when constructing FLUX prompts — trigger words differ by collection.
- `skyyrose-lora-v3-tests/` — Evaluation renders for v3 (3 webp files: black-rose, love-hurts, signature). Used for side-by-side comparison with v4.
- `training-runs/` — Training run logs and hyperparameter sweeps.

## Conventions

- Trigger word for v3 is `skyyrose` — always include it in FLUX prompts when using the v3 LoRA.
- Use `skyyrose-lora-v4-trigger-map.json` for v4 prompts — trigger words are collection-specific in v4.
- New LoRA versions go in a new `skyyrose-lora-v{N}-info.json` + `skyyrose-lora-v{N}-tests/` pair.
- Weights URLs in info JSON point to Replicate delivery CDN — they may expire. The canonical weight location is the Replicate model page.
- Base model for both v3 and v4 is `ostris/flux-dev-lora-trainer`.

## Don't

- Don't store actual model weights (`.safetensors`, `.tar`) here — too large for git. Use Replicate/HF.
- Don't hand-edit `*-info.json` — these are generated outputs from Replicate training runs. Update by re-running training and saving the API response.
- Don't use v3 trigger word with v4 weights — they were trained with different trigger strategies.

## Related

- `scripts/tripo_dispatch.py` — 3D pipeline (separate from LoRA FLUX pipeline)
- `skyyrose/elite_studio/agents/` — agents that call FLUX with these LoRA weights
- `datasets/` — source training image datasets
- `renders/` — output from LoRA-generated images
