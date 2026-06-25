# Clothing 3D Pipeline

End-to-end image/text → garment 3D asset pipeline, built on
[Microsoft TRELLIS](https://github.com/microsoft/TRELLIS).

## Why

E-commerce garment photography needs to become 3D for AR try-on, immersive
collection pages, and richer PDP renders. TRELLIS produces the best mesh +
texture quality for clothing among open models, but raw TRELLIS output is
not e-commerce-ready: backgrounds bleed in, polycount is unbounded, USDZ
isn't emitted, and there's no QC gate. This pipeline closes that gap.

## Architecture

```
┌─────────────┐   ┌──────────────┐   ┌───────────────────────────────┐
│  PipelineRequest │   │ ClothingPipeline │   │     services/three_d/trellis/         │
│  (image | text)  ├──▶│  orchestrator    ├──▶│  preprocess → backend → postprocess   │
│  garment meta    │   │  (events, QC)    │   │  ┌─────────┐  ┌──────┐  ┌──────────┐  │
└─────────────┘   └──────┬───────┘   │  │ rembg + │→ │ HF   │→ │ trimesh  │  │
                          │           │  │ resize  │  │Space │  │ + USDZ   │  │
                          │           │  └─────────┘  └──────┘  └──────────┘  │
                          │           └──────────────────────────────────────┘
                          ▼
                ┌──────────────────┐
                │  ArtifactStore   │  Local FS (dev) or S3-compatible (prod)
                │  GLB + USDZ +    │
                │  thumbnail       │
                └─────────┬────────┘
                          ▼
                ┌──────────────────┐     ┌───────────────────┐
                │ PipelineResult   │ ←── │ FastAPI /v1/clothing-3d
                │ + stage reports  │     │   /generate                │
                └──────────────────┘     │   /generate/async + /jobs  │
                                         │   /health + /info          │
                                         └────────────────────────────┘
```

## Layout

```
services/three_d/trellis/
├── __init__.py
├── config.py          # TrellisConfig, quality presets, sampling params
├── garment_aware.py   # category classifier + prompt builder
├── preprocess.py      # background removal, crop, normalize, quality score
├── client.py          # HF Space / Local / Replicate / Stub backends
├── postprocess.py     # mesh cleanup, decimate, USDZ, thumbnail
└── provider.py        # I3DProvider implementation

pipelines/clothing_3d/
├── __init__.py
├── models.py          # PipelineRequest / Result / StageReport
├── events.py          # pub/sub event bus (log + webhook subscribers)
├── stages.py          # ingest / generate / qc / store stage callables
├── storage.py         # LocalArtifactStore + S3ArtifactStore
├── pipeline.py        # ClothingPipeline orchestrator
└── cli.py             # python -m pipelines.clothing_3d.cli

api/v1/clothing_3d/
├── __init__.py
├── schemas.py         # request/response Pydantic models
└── router.py          # FastAPI endpoints (sync + async job)

tests/
├── three_d/trellis/   # unit tests
└── pipelines/clothing_3d/  # integration tests

scripts/
├── setup_trellis.sh   # clone microsoft/TRELLIS into vendor/trellis/
└── trellis_demo.py    # end-to-end smoke test

vendor/
└── trellis/           # vendored microsoft/TRELLIS (git-ignored)
```

## Backends

The TRELLIS provider supports four backends — pick with
`TRELLIS_BACKEND` env var or per-request `backend` field.

| Backend     | GPU? | Cost              | Latency  | Best for                      |
|-------------|------|-------------------|----------|-------------------------------|
| `hf_space`  | no   | free              | 60–180 s | dev, low-volume production    |
| `local`     | yes  | hardware          | 15–30 s  | high-volume self-hosted       |
| `replicate` | no   | ~$0.05 / model    | 30–60 s  | bursty workloads              |
| `modal`     | no   | per GPU sec       | 10–20 s  | strict-SLA production         |
| `stub`      | no   | free              | <0.1 s   | tests, dry runs, CI           |

## Quality presets

`TrellisQualityPreset` (also exposed as `quality` on the request) maps to
sampling steps + mesh detail:

| Preset       | SS / SLAT steps | Mesh simplify | Texture | Polycount target |
|--------------|------------------|----------------|---------|------------------|
| `draft`      | 8 / 8            | 0.85           | 1024²   | 40k              |
| `standard`   | 12 / 12          | 0.95           | 1024²   | 80k              |
| `production` | 20 / 20          | 0.97           | 2048²   | 150k             |

The QC stage tightens or relaxes its acceptance thresholds based on the
selected preset — see `pipelines/clothing_3d/stages.py:default_thresholds_for`.

## Setup

### 1. Install Python deps

```bash
pip install -r requirements-trellis.txt
```

`rembg`, `trimesh`, `usd-core` are optional but recommended — the pipeline
degrades gracefully (emits warnings) when they're missing.

### 2. (Optional) Vendor TRELLIS for local GPU inference

```bash
bash scripts/setup_trellis.sh --with-weights
pip install -e vendor/trellis
```

This is only needed for `TRELLIS_BACKEND=local`. The default `hf_space`
backend works with just `pip install gradio_client`.

### 3. Configure

Add to `.env`:

```bash
TRELLIS_BACKEND=hf_space             # or local | replicate | modal
TRELLIS_QUALITY=standard             # draft | standard | production
TRELLIS_OUTPUT_DIR=./assets/3d-models-generated
TRELLIS_EXPORT_USDZ=true
HUGGINGFACE_TOKEN=hf_xxx              # optional, raises HF Space rate limits
REPLICATE_API_TOKEN=r8_xxx            # only when backend=replicate
```

### 4. Smoke test

```bash
# Stub backend — no network required
python scripts/trellis_demo.py

# HF Space backend — needs network, ~2 min
python scripts/trellis_demo.py --backend hf_space --image path/to/garment.jpg
```

## Programmatic usage

```python
from pipelines.clothing_3d import ClothingPipeline, PipelineRequest
from services.three_d.trellis import TrellisQualityPreset

pipeline = ClothingPipeline()

result = await pipeline.run(
    PipelineRequest(
        image_url="https://skyyrose.co/wp-content/uploads/2024/hoodie.jpg",
        product_name="Black Rose Hoodie",
        product_sku="br-001",
        collection="black_rose",
        garment_type="hoodie",
        quality=TrellisQualityPreset.PRODUCTION,
    )
)

print(result.glb_url)        # /assets/3d-models-generated/br-001_*.glb
print(result.usdz_url)       # /assets/3d-models-generated/br-001_*.usdz
print(result.quality.score)  # 0..1
```

## HTTP API

| Method | Path                               | Purpose                          |
|--------|------------------------------------|----------------------------------|
| POST   | `/v1/clothing-3d/generate`         | synchronous run                  |
| POST   | `/v1/clothing-3d/generate/async`   | enqueue, returns job_id          |
| GET    | `/v1/clothing-3d/jobs/{job_id}`    | poll an async job                |
| GET    | `/v1/clothing-3d/health`           | provider/backend health          |
| GET    | `/v1/clothing-3d/info`             | active config + capabilities     |

To mount on the enterprise app:

```python
# main_enterprise.py
from api.v1.clothing_3d import router as clothing_3d_router
app.include_router(clothing_3d_router, prefix="/v1/clothing-3d")
```

## CLI

```bash
# Single image
python -m pipelines.clothing_3d.cli generate \
  --image ./uploads/hoodie.jpg \
  --product "Black Rose Hoodie" \
  --collection black_rose \
  --garment-type hoodie \
  --quality production

# Batch
echo '{"image_path":"a.jpg","product_name":"A","quality":"draft"}' > batch.jsonl
echo '{"image_path":"b.jpg","product_name":"B","quality":"draft"}' >> batch.jsonl
python -m pipelines.clothing_3d.cli batch batch.jsonl --max-concurrent 2

# Health probe
python -m pipelines.clothing_3d.cli health
```

## Event bus

The pipeline emits structured events at each stage boundary:

| Event              | Stage          | Meaning                       |
|--------------------|----------------|-------------------------------|
| `pipeline.started` | —              | Run accepted                  |
| `stage.started`    | every stage    | Stage beginning execution     |
| `stage.finished`   | every stage    | Stage emitting detail payload |
| `pipeline.rejected`| —              | QC vetoed the artifact        |
| `pipeline.failed`  | —              | Any stage failed              |
| `pipeline.succeeded`| —             | Artifact stored               |

Subscribe with `bus.subscribe(coroutine_fn)`. Built-in subscribers:

- `log_event_subscriber()` — stdlib logging
- `webhook_subscriber(url)` — POSTs each event to ``url`` (httpx)

## QC gate

The QC stage runs after generation/postprocessing and checks:

- Polycount within `[min_polycount, max_polycount]` for the preset
- File size within `[min_file_kb, max_file_kb]`
- Thumbnail present (production only, optional)

Failures trigger a `REJECTED` status — the artifact is still produced
and stored in metadata, but the API marks the run as not shippable. Wire
the `pipeline.rejected` event into your approval queue.

Override thresholds:

```python
from pipelines.clothing_3d.stages import QCThresholds

pipeline = ClothingPipeline(
    thresholds=QCThresholds(min_polycount=20_000, max_file_kb=15_000)
)
```

## Storage backends

| Backend             | Use case                                    |
|---------------------|---------------------------------------------|
| `LocalArtifactStore`| Dev + the existing FastAPI static mount     |
| `S3ArtifactStore`   | Prod: S3, R2, or any S3-compatible store    |

Both implement `ArtifactStore`. Bring your own by implementing the
`store(bundle) -> StoredArtifact` async method.

```python
from pipelines.clothing_3d.storage import S3ArtifactStore

pipeline = ClothingPipeline(
    store=S3ArtifactStore(
        bucket="skyyrose-3d",
        prefix="garments",
        public_base_url="https://cdn.skyyrose.co/3d",
    )
)
```

## Testing

```bash
# All tests
pytest tests/three_d/trellis tests/pipelines/clothing_3d -v

# Just the deterministic stub-backed integration test
pytest tests/pipelines/clothing_3d -v

# Run the CLI in dry-run mode (uses the stub backend)
python -m pipelines.clothing_3d.cli generate --prompt "demo" --dry-run
```

The stub backend writes a tiny placeholder GLB and returns immediately, so
tests run in <1 s and don't require GPU, network, or any optional deps.

## Roadmap

- [ ] Modal backend implementation (placeholder in `client.py`)
- [ ] TRELLIS-text-large weights for true text-to-3D
- [ ] Auto-rigging via `Rigify` for try-on animation
- [ ] Per-garment material library (PBR overrides for known fabrics)
- [ ] WebSocket progress stream on the `/generate/async` endpoint
- [ ] Multi-view input (front + back + side) — TRELLIS supports `multiimages`
