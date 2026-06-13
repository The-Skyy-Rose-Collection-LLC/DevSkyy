# ai_3d/ — 3D generation pipeline (10 Python files)

Generates 3D models, virtual photoshoots, and quality-enhanced renders for the SkyyRose collections.

## Files

- `generation_pipeline.py` — top-level pipeline coordinating providers
- `model_generator.py` — model creation logic (GLB, USDZ formats)
- `virtual_photoshoot.py` — composes scenes for product photography
- `quality_enhancer.py` — post-generation quality pass
- `resilience.py` — retry, fallback, timeout handling
- `providers/` — provider-specific adapters (Tripo3D, Meshy, Hunyuan3D)

## Conventions

- All provider calls go through `providers/<name>.py`. Provider-agnostic logic lives in the top-level files.
- Outputs land in `renders/output/<sku>/` (gitignored). Manifests track which provider produced each artifact.
- All generation calls are gated by `/preflight` — they cost money and are slow. Confirm gate passed before invoking.

## Don't

- Don't call providers directly from outside this directory. Use the pipeline.
- Don't write generated 3D files into the source tree. Always to `renders/output/`.
- Don't add a new provider without updating `resilience.py` with the appropriate retry/fallback rules.

## Related

- Triggered from: `agents/tripo_agent.py`, `agents/meshy_agent.py`, `orchestration/asset_pipeline.py`
- Endpoints: `api/ai_3d_endpoints.py`
- Storage: `services/storage/three_d_storage.py`


