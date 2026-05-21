<claude-mem-context>

</claude-mem-context>

# hf-spaces/ — HuggingFace Spaces deployment configs

Six HuggingFace Spaces that expose DevSkyy capabilities as public Gradio/web apps. Each subdirectory is a self-contained Space — deployed independently to `huggingface.co/spaces/damBruh/{space-name}`.

## Key files

- `3d-converter/` — Space for converting 2D product images to 3D models (Tripo/Meshy pipeline).
- `flux-upscaler/` — FLUX-based image upscaling for product photography.
- `lora-training-monitor/` — Dashboard Space showing active LoRA training run status (reads from Replicate API).
- `product-analyzer/` — Product image quality analyzer: blur detection, background check, aspect ratio validation.
- `product-photography/` — End-to-end product photography pipeline Space (background removal → enhance → compose).
- `virtual-tryon/` — Virtual try-on Space wrapping the FASHN API.

## Conventions

- Each Space subdirectory must contain its own `requirements.txt` and `app.py` (or `README.md` with YAML frontmatter for HF metadata) — HF Spaces are self-contained.
- Secrets (API keys) are set as HF Space environment variables — never hard-coded in `app.py`.
- Deploy via `git push` to the HF Space repo (not `scripts/deploy-theme.sh`) — separate git remote per Space.
- `virtual-tryon` Space calls FASHN API — **STOP AND SHOW required** before any code change that alters cost-per-call behavior.

## Don't

- Don't add a Space subdirectory without a corresponding `app.py` and `requirements.txt` — incomplete Spaces fail to build on HF.
- Don't store model weights in Space subdirectories — use `models/` for metadata and HF Hub for weights.
- Don't cross-reference across Spaces at runtime — each Space must be independently deployable.

## Related

- `models/` — LoRA model metadata consumed by `flux-upscaler` and `lora-training-monitor`
- `skyyrose/elite_studio/` — local pipeline that Spaces wrap for public access
- `scripts/deploy_hf_spaces.sh` — batch deploy script for all Spaces
