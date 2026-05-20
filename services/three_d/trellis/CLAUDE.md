# services/three_d/trellis/ — TRELLIS Clothing 3D Pipeline

**Microsoft Structured 3D Latents pipeline tuned for garment imagery.** Backed by vendored `vendor/trellis` (https://github.com/microsoft/TRELLIS) with HF Space fallback (`JeffreyXiang/TRELLIS`).

Merged into monorepo 2026-05-19 (PR #508).

## Public Surface (`services/three_d/trellis/__init__.py`)

| Group | Symbols | Source |
|-------|---------|--------|
| Provider | `TrellisProvider` (implements `I3DProvider`) | `provider.py` |
| Config | `TrellisConfig`, `TrellisBackend`, `TrellisQualityPreset` | `config.py` |
| Preprocessing | `TrellisPreprocessor`, `PreprocessedImage`, `PreprocessResult` | `preprocess.py` |
| Postprocessing | `MeshPostprocessor`, `PostprocessResult` | `postprocess.py` |
| Garment knowledge | `GarmentCategory`, `GarmentKnowledge`, `classify_garment()`, `build_clothing_prompt()` | `garment_aware.py` |

## Backends (`TrellisBackend`)

| Backend | When | Cost |
|---------|------|------|
| Local Python (vendored) | GPU available, fastest | Compute only |
| HF Space (`JeffreyXiang/TRELLIS`) | Fallback when local unavailable | Free (rate limited) |
| Replicate | High-volume production | Per-invocation |

## Hard Rules

- **Configuration via `TrellisConfig.from_env()`** — never construct config inline. Env vars: `TRELLIS_BACKEND`, `TRELLIS_QUALITY_PRESET`, `HF_TOKEN`, `REPLICATE_API_TOKEN`
- Preprocessing order: **bg removal → crop → normalize → resize**. Skipping bg removal degrades mesh quality significantly
- `classify_garment()` is mandatory before `build_clothing_prompt()` — prompt construction depends on `GarmentCategory` (top/bottom/full-body/accessory)
- Postprocessing pipeline: **cleanup → decimation → AR export**. Decimation BEFORE AR export keeps file sizes < 5MB for web delivery
- `TrellisProvider` is registered with `ThreeDProviderFactory` — never invoke directly outside the factory
- Vendored TRELLIS at `vendor/trellis` is read-only — patches go through the TRELLIS upstream, not local edits
- Output meshes ship to R2 via `services/storage/AssetVersionManager` — never write to local disk in production

## Entry Point

```python
from services.three_d.trellis import TrellisProvider, TrellisConfig

provider = TrellisProvider(TrellisConfig.from_env())
response = await provider.generate_from_image(request)
```

## Consumers

- `services/three_d/provider_factory.py` — registers TRELLIS as a provider
- `api/v1/clothing_3d/*` — async pipeline routes garment requests preferentially to TRELLIS
- `pipelines/clothing_3d/*` — worker queue consumes TRELLIS provider
