# FLUX Synthesis Pipeline — Architecture Document

**Status:** Draft for review
**Author:** Engineering
**Date:** 2026-04-26
**Supersedes:** `skyyrose/elite_studio/agents/three_d_agent.py` Stage 3 (Gemini Pro Image Preview RAS)
**Related:** `.claude/plans/tidy-sparking-goose.md` (dossier system H1–H8 hardening)

---

## 1. Goal

Replace the single-pass Gemini Pro Image Preview generation stage with a hardened, multi-stage diffusion pipeline that reliably produces commercial-grade luxury fashion product renders from a per-SKU dossier + techflat. The replacement must:

1. **Eliminate decoration drift** — Gemini hallucinates SR monograms on cuffs, sleeves, or other regions the dossier doesn't authorize. The new pipeline must make this physically impossible at the architecture layer, not the prompting layer.

2. **Eliminate technique hallucination** — Gemini renders embroidery (visible thread, satin stitches) when the dossier specifies embossed (3D pressed-into-fabric tonal effect). Negative prompts alone don't fix this — academic research (ArXiv 2406.02965) shows negative prompts only act between diffusion steps 5–11 and can fight statistical priors.

3. **Preserve every existing dossier guardrail** — H1 hard-fail on missing dossier, H4 vision audit gate, H4 retry loop, H5 forensic manifests, H7 CI checks. The new pipeline plugs into the existing scaffolding without replacing it.

4. **Be production-grade from day one** — full error handling, retries, structured observability, idempotency, batch resumability, crash recovery.

## 2. Non-goals

- Replacing the dossier system or the dossier loader (`skyyrose.core.dossier_loader`).
- Replacing the Vision Audit gate (`skyyrose/elite_studio/agents/vision_audit_agent.py`).
- Replacing the Meshy + Blender 3D scaffolding (Stages 1–2 of `three_d_agent.py`).
- Building a UI — this is a pipeline + CLI module.
- Generating editorial / lookbook scenes (that's `scripts/run_compositor_pipeline.py` — out of scope).

---

## 3. Architecture

### 3.1 High-level flow

```
┌─────────────────┐
│ Stage 0: Inputs │   dossier (md) + techflat (png/jpeg) + scaffold (png from Blender)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Stage 1: BASE GARMENT RENDER            │
│ Model: FLUX.1 Kontext Pro (via fal.ai)  │
│ Input: techflat as input_image          │
│ Prompt: garment_type_lock + fabric +    │
│         silhouette + colorway           │
│ Decoration prompt: NONE (silent)        │
│ Conditioning: techflat shape            │
│ Output: clean_garment.png               │
│ Goal: garment with NO decoration        │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Stage 2: DECORATION-MASK DERIVATION     │
│ Tool: Gemini Flash vision (primary) +   │
│       static-template fallback          │
│ Input: clean_garment.png + dossier      │
│        branding regions list            │
│ Output: decoration_mask.png             │
│         (B&W, white = inpaint zones)    │
│ Goal: precise mask of authorized        │
│       decoration regions only           │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Stage 3: DECORATION INPAINT             │
│ Model: FLUX.1 Fill Pro (via fal.ai)     │
│ Input: clean_garment.png + mask         │
│ Reference: techflat decoration crop     │
│ Prompt: physics-described decoration    │
│         ("tonal embossed relief, no     │
│         thread, no stitching")          │
│ Optional: SkyyRose decoration LoRA      │
│ Output: branded_garment.png             │
│ Goal: decoration only inside mask zones │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Stage 4: RELIGHTING (optional)          │
│ Model: IC-Light V2 (via fal.ai)         │
│ Input: branded_garment.png              │
│ Output: final_render.png                │
│ Goal: studio lighting refinement        │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Stage 5: VISION AUDIT GATE              │
│ (existing — VisionAuditAgent)           │
│ Verdict: ok / has_blocking_violations   │
└────────┬────────────────────────────────┘
         │
   ┌─────┴─────┐
   ▼           ▼
 PASS        FAIL → retry Stage 3 with violation feedback (max 2 retries)
   │           │
   │           └─ if all retries fail: quarantine
   ▼
 H5 forensic manifest + return success
```

### 3.2 Why this fixes both failure modes

**Decoration drift** is impossible because Stage 3 uses a binary mask. FLUX Fill Pro can only paint inside the white regions of the mask. If `front-left-cuff` isn't in the dossier's authorized regions, it isn't in the mask, so no decoration can appear there regardless of how strongly the model wants to.

**Technique hallucination** is mitigated by three compounding factors:
1. **Narrower scope**: Stage 3 inpaints only ~10% of the image (the decoration zones). The model has less freedom to invent.
2. **Physics-described prompt**: instead of fighting the embroidery prior with `NOT embroidery, NOT thread`, we describe the physical mechanism — *"pressed-into-fabric impression, single-color tonal relief, raking light shadow at edges, no surface attachment, no thread, no stitching."* The prior is partially neutralized by giving the model an alternative low-energy state to settle into.
3. **Reference-image conditioning** via the techflat decoration crop. FLUX Kontext Pro and Fill Pro both accept reference images. Showing the model what an embossed logo looks like (a real photo from `data/product-references/`) is far stronger than describing it in text.
4. **Optional LoRA layer** trained on 30-50 photos of real embossed garments. The LoRA teaches the model a new low-energy state for "tonal decoration on dark fabric" so it doesn't have to fight the data prior at all.

---

## 4. API contracts (from Context7 docs, 2026-04-26)

### 4.1 FLUX.1 Kontext Pro (Stage 1)

**fal.ai endpoint:** `fal-ai/flux-pro/v1/kontext`
**BFL direct equivalent:** `POST https://api.bfl.ai/v1/flux-kontext-pro`

**Required:**
- `prompt` (string): Text instruction for the edit.
- `input_image` (string): Base64 or URL, ≤20MB / ≤20MP.

**Optional:**
- `aspect_ratio` (e.g., `"1:1"`, `"16:9"`)
- `seed` (int, for reproducibility)
- `prompt_upsampling` (bool, default false)
- `safety_tolerance` (0–6, default 2)
- `output_format` (`"jpeg"` | `"png"`)

**Response (sync via fal.ai):**
```json
{ "images": [{ "url": "https://fal.media/...", "width": 1024, "height": 1024 }], "seed": 12345 }
```

**Response (async via BFL direct):** `{ "id", "polling_url" }` — must poll `polling_url` until `status: "Ready"`.

**Used for:** generating the clean garment shape from the techflat without decoration.

### 4.2 FLUX.1 Fill Pro (Stage 3)

**fal.ai endpoint:** `fal-ai/flux-pro/v1/fill`
**BFL direct:** `POST https://api.bfl.ai/v1/flux-pro-1.0-fill`

**Required:**
- `image` (string): Base64-encoded image to inpaint.
- `safety_tolerance` (int, 0–6, default 2)

**Optional:**
- `mask` (string): Base64-encoded B&W mask, **same dimensions** as image. **White = inpaint, Black = preserve.** If omitted, alpha channel of `image` is used.
- `prompt` (string): Inpaint prompt. Defaults to empty.
- `steps` (int, 15–50, default 50)
- `guidance` (float, 1.5–100, default 60)
- `prompt_upsampling` (bool)
- `seed` (int)
- `output_format` (`"jpeg"` | `"png"` | `"webp"`)

**LoRA support:** fal.ai's `fal-ai/flux-pro/v1/fill` does NOT accept a `lora` parameter directly. For LoRA inference, use `fal-ai/flux-kontext-lora/inpaint` (already used in the compositor) which DOES accept `loras: [{path: <url>, scale: 1.0}]`. Decision: route LoRA-active SKUs through `flux-kontext-lora/inpaint`, non-LoRA SKUs through `flux-pro/v1/fill`. Both endpoints share the same `image` + `mask` + `prompt` schema.

### 4.3 IC-Light V2 (Stage 4, optional)

**fal.ai endpoint:** `fal-ai/iclight-v2`

**Schema** (best-effort from fal docs — verify on first integration):
- `image_url`: foreground subject
- `prompt`: target lighting environment description
- `num_inference_steps`, `guidance_scale`, `seed` (standard diffusion params)

Skipped on first batch — Stage 1 prompt already specifies "studio lighting, hyper-realistic." Add Stage 4 in a v2 if relighting issues surface.

### 4.4 fal.ai client patterns

**Async + queued (recommended for batch):**

```python
import fal_client
client = fal_client.AsyncClient()

# Upload reference images to fal CDN once, reuse URLs
techflat_url = await client.upload_file(techflat_path)  # cached

# Subscribe pattern with progress events
result = await client.subscribe(
    "fal-ai/flux-pro/v1/kontext",
    arguments={
        "input_image": techflat_url,
        "prompt": stage_1_prompt,
        "aspect_ratio": "1:1",
        "output_format": "png",
    },
    with_logs=True,
    on_queue_update=lambda status: log.info("flux-kontext queue: %s", status),
)
output_url = result["images"][0]["url"]
```

**Concurrency:**

```python
results = await asyncio.gather(*[
    client.subscribe("fal-ai/flux-pro/v1/kontext", arguments=args)
    for args in batch_args
])
```

**Error semantics:**
- `fal_client.ApplicationError` — model returned error (validation, content policy, etc.). Do NOT retry blindly; inspect message.
- `fal_client.HTTPError` (5xx) — transient; retry with exponential backoff.
- Timeout — wrap `subscribe` with `asyncio.wait_for(timeout=300)`.

### 4.5 Replicate (LoRA training, Phase 3)

**Trainer model:** `ostris/flux-dev-lora-trainer` (current best per community 2026; alt: `replicate/fast-flux-trainer` if available).

**Training input schema** (verify via `replicate.models.get(...)` before launch):
- `input_images` (URL to zip file, OR uploaded `replicate.files.create()` URL)
- `trigger_word` (e.g., `"SKYR_EMBOSS"`) — used in inference prompts
- `caption_prefix` (e.g., `"a photo of SKYR_EMBOSS, "`)
- `max_train_steps` (1500–3000 typical)
- `lora_rank` (16 or 32 — 16 matches Finegrain experiment)
- `learning_rate` (1e-4 typical)

**Training pattern:**

```python
import replicate

# Pre-upload dataset
dataset_file = replicate.files.create(open("emboss_dataset.zip", "rb"))

training = replicate.trainings.create(
    model="ostris/flux-dev-lora-trainer",
    version="<version-hash>",
    input={
        "input_images": dataset_file.urls["get"],
        "trigger_word": "SKYR_EMBOSS",
        "caption_prefix": "a photo of SKYR_EMBOSS embossed garment, ",
        "max_train_steps": 2000,
        "lora_rank": 16,
    },
    destination="skyyroseco/skyyrose-emboss-lora-v1",
)

# Poll until done
while training.status not in ["succeeded", "failed", "canceled"]:
    time.sleep(15)
    training.reload()

lora_url = training.output["weights"]  # URL to LoRA safetensors file
```

**Then use that URL** as the `loras[].path` argument in `fal-ai/flux-kontext-lora/inpaint`.

---

## 5. Module structure

```
skyyrose/elite_studio/synthesis/
├── __init__.py
├── flux_pipeline.py        # main orchestrator: render(sku, view) -> RenderResult
├── stages/
│   ├── __init__.py
│   ├── base_render.py      # Stage 1: FLUX Kontext base render
│   ├── mask_deriver.py     # Stage 2: decoration-mask derivation
│   ├── decoration_inpaint.py  # Stage 3: FLUX Fill / Kontext-LoRA inpaint
│   └── relight.py          # Stage 4: IC-Light V2 (optional)
├── prompts/
│   ├── __init__.py
│   ├── base_prompts.py     # Stage 1 prompt templates per garment_type
│   ├── decoration_prompts.py  # Stage 3 physics-described prompts per technique
│   └── lora_triggers.py    # trigger words for trained LoRAs
├── clients/
│   ├── __init__.py
│   ├── fal.py              # thin async wrapper around fal_client with retry/timeout
│   └── replicate.py        # async wrapper for LoRA training (used in Phase 3)
├── state/
│   ├── __init__.py
│   ├── batch_state.py      # idempotent batch resumability
│   └── telemetry.py        # cost tracker + structured logging
├── tests/
│   ├── __init__.py
│   ├── test_mask_deriver.py
│   ├── test_prompts.py
│   ├── test_flux_pipeline.py  # mocked fal_client
│   └── fixtures/
│       └── (test dossiers, test images, golden mask outputs)
└── README.md               # pipeline overview, env setup, runbook
```

**Why separate `synthesis/` module:** keeps the dossier-aware FLUX pipeline distinct from the legacy compositor (`scripts/run_compositor_pipeline.py`) and the lookbook scene work. Single import path: `from skyyrose.elite_studio.synthesis import render`.

---

## 6. Mask derivation strategy

The decoration mask is the structural innovation. It must:
- Be a binary B&W image, same dimensions as the Stage 1 output.
- Have white pixels ONLY in regions the dossier authorizes for decoration.
- Be conservative — slightly larger than the actual decoration is fine, but must not extend into unauthorized regions.

### 6.1 Approach: Gemini Flash vision-guided masking

The dossier already names regions (`front-center-chest`, `back-yoke`, `left-cuff`, `front-thigh-chevron-pants`). Gemini Flash can take the Stage 1 render + the list of authorized regions and output bounding boxes.

**Prompt to Gemini Flash:**

```
You are a fashion product imagery preprocessor. The attached image shows a
{dossier.name} ({garment_type}) with no decoration applied yet.

The following decoration regions are AUTHORIZED for branding:
- front-center-chest: large emblem (~5-6in tall) on the upper chest area
- back-yoke: small emblem (~2in tall) at the back-neck below the collar
- left-cuff: small emblem (~1.5in tall) on the wearer's left wrist cuff

Output a JSON array of bounding boxes for EACH authorized region, in the format:
[
  { "region": "front-center-chest", "bbox": [x1, y1, x2, y2] },
  { "region": "back-yoke", "bbox": [x1, y1, x2, y2] },
  ...
]

Coordinates are in pixels relative to the top-left of the image. Be slightly
generous (10% padding). Output ONLY the JSON, no prose, no code fences.
```

We then build a binary mask by drawing white-filled rectangles at the bounding boxes onto a black canvas of the image's dimensions.

**Why Gemini Flash:**
- Already in the pipeline (vision_audit_agent uses it).
- Cheap ($0.005/call).
- Fast (~2 sec).
- Good at spatial reasoning on garment images.

### 6.2 Fallback: static-template masks

If Gemini Flash fails (validation error, JSON parse error, or returns regions it can't locate), fall back to a static-template mask registry per garment_type. Templates are in `synthesis/stages/mask_templates/` as PNG files, normalized to 1024x1024:

- `crewneck.front.center-chest.png` — white blob on a black canvas at the standard center-chest location
- `crewneck.back.yoke.png`
- `jersey.front.left-chest.png`
- ... etc.

For each authorized region in the dossier, OR-composite the matching template into the mask. Templates are conservative (slightly larger than typical decoration size).

This fallback is also used during testing (no API calls) and as a sanity check (Gemini's output should overlap the static template > 70% — if it doesn't, log a warning and use the static template).

### 6.3 Mask sanity checks

Before passing to Stage 3, validate:
- Mask dimensions match Stage 1 output dimensions.
- Mask is binary (only 0 and 255 values).
- Total white pixel area is between 1% and 30% of the image (sanity bounds — too small = no decoration possible, too large = no benefit over no-mask).
- Mask is non-empty.

If any check fails: log + fall back to static template + log telemetry event.

---

## 7. Error handling + retries

### 7.1 Retry matrix

| Failure | Retry strategy |
|---|---|
| fal.ai 5xx (rate limit, transient) | Exponential backoff, 3 retries, 2s/4s/8s |
| fal.ai 4xx (validation) | No retry — log + fail |
| fal.ai timeout (>300s) | 1 retry with same args |
| Gemini Flash mask derivation: JSON parse error | 1 retry with stricter prompt; then fallback to static template |
| Gemini Flash mask derivation: bounding box outside image | Clip to image bounds, log warning, continue |
| Vision audit blocking violation | Existing H4 retry loop (already implemented) — feeds violation back into Stage 3 prompt |
| Stage 1 (Kontext) returns image | Validate dimensions match expected (~1MP); if wildly off, retry with explicit `aspect_ratio` |
| Stage 3 (Fill) returns image | Validate dimensions match Stage 1 output exactly; abort if not |
| All retries exhausted | Forensic manifest + quarantine + return failure |

### 7.2 Tenacity wrapper

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=10),
    retry=retry_if_exception_type((fal_client.HTTPError, asyncio.TimeoutError)),
    reraise=True,
)
async def _call_fal(endpoint: str, arguments: dict) -> dict:
    ...
```

### 7.3 Crash recovery

- SIGINT / SIGTERM handling: finish current SKU's stage if mid-API-call; write batch state; exit clean.
- On restart with `--resume`, read state file, skip completed SKUs.

---

## 8. Observability + cost tracking

### 8.1 Structured log per SKU per attempt

```json
{
  "ts": "2026-04-26T15:30:00Z",
  "sku": "br-001",
  "view": "front",
  "attempt": 1,
  "stage": "stage_3_inpaint",
  "model": "fal-ai/flux-pro/v1/fill",
  "request_id": "req_abc123",
  "duration_ms": 4231,
  "input_image_url": "https://fal.media/.../clean_garment.png",
  "mask_image_url": "https://fal.media/.../decoration_mask.png",
  "output_image_url": "https://fal.media/.../branded_garment.png",
  "estimated_cost_usd": 0.05,
  "audit_verdict": "ok",
  "audit_violations": []
}
```

### 8.2 Cost tracker

In-process counter incremented by each API call's estimated cost. Written to `renders/output/{name-slug}/{ts}/cost.json` per SKU and aggregated per batch. Logs warnings at $5 / $10 / $20 / $50 thresholds. **No hard cap** per user directive — log only. `cost.json` includes per-stage breakdown so we can later analyze where spend goes.

### 8.3 Forensic manifest (extends existing H5)

Existing manifest at `renders/output/{name-slug}/{ts}/manifest.json` adds:

```json
{
  "pipeline_version": "flux-synthesis-v1",
  "stages": [
    { "stage": "stage_1_base", "model": "fal-ai/flux-pro/v1/kontext", ... },
    { "stage": "stage_2_mask", "model": "gemini-3-flash-preview", ... },
    { "stage": "stage_3_inpaint", "model": "fal-ai/flux-pro/v1/fill", ... },
    { "stage": "stage_5_audit", "model": "gemini-3-flash-preview", ... }
  ],
  "total_cost_usd": 0.135,
  "total_duration_ms": 12500
}
```

Replay test: feed manifest + saved seeds → reproduce output bit-for-bit-similar (subject to fal.ai server determinism).

---

## 9. State + idempotency

### 9.1 Batch state file

`renders/state/{batch_id}.json`:

```json
{
  "batch_id": "20260426T153000",
  "started_at": "...",
  "skus_planned": ["br-001", "br-002", ...],
  "skus_completed": ["br-001:front", "br-001:back"],
  "skus_failed": [],
  "total_cost_usd": 1.23
}
```

CLI flag `--resume <batch_id>` reads this and skips completed SKUs.

### 9.2 Idempotency key

Forensic manifests are written to `renders/output/{name-slug}/{ts}/manifest.json` with `ts` derived from `(sku, view, dossier_sha256, prompt_sha256)` so identical inputs produce identical output paths. Re-running on the same dossier overwrites cleanly.

---

## 10. Test strategy

### 10.1 Unit tests (no API calls)

- `test_mask_deriver.py`: feed mock Gemini Flash response → verify mask dimensions, binary, white-area sanity bounds. Verify static template fallback path.
- `test_prompts.py`: verify prompt construction includes garment_type_lock, fabric description, NO decoration mention in Stage 1 prompt; verify Stage 3 prompt includes physics description.
- `test_flux_pipeline.py`: mock `fal_client` calls, verify orchestration flow, retry behavior, error handling.

### 10.2 Integration test (single SKU smoke)

`tests/integration/test_flux_synthesis_smoke.py` — gated behind `--run-integration` flag. Runs br-001 end-to-end against real fal.ai. Asserts:
- Output file written
- Audit verdict is `ok` OR violations are LOW-severity only
- Manifest written with all 5 stages

### 10.3 Property tests on mask derivation

Use Hypothesis for region-list inputs → verify mask is always valid (dimensions, binary, area bounds) regardless of region count.

### 10.4 Replay test

Given a forensic manifest from a prior run, replay produces output within a perceptual-hash threshold (allowing for fal.ai non-determinism on no-seed paths).

---

## 11. LoRA training pipeline (Phase 3)

### 11.1 Dataset

- Source 1: `data/product-references/` — existing techflats and product photos. Filter for ones showing embossed/debossed/tonal decoration.
- Source 2: existing `assets/images/products/*.webp` — real product photography for SKUs that ship as photo (br-007, lh-003, kids-001, kids-002).
- Source 3: web-sourced reference photos of embossed garments (10-20 high-quality stock images, fair use for fine-tuning).
- Target: 30-50 images, 1024x1024 minimum, raking-light or directional-light shots showing emboss visibility.

### 11.2 Caption file

`{trigger_word} {decoration_description}` per image. Example:

```
SKYR_EMBOSS embossed black rose-cluster on black fleece crewneck, raking light
SKYR_EMBOSS debossed wordmark on dark navy nylon, side directional light
SKYR_EMBOSS tonal embossed logo on charcoal cotton, soft shadow
```

### 11.3 Training run

Replicate `ostris/flux-dev-lora-trainer` with rank-16, 2000 steps, learning rate 1e-4. Training time ~20-30 min on H100. Output: LoRA `.safetensors` URL.

### 11.4 LoRA inference integration

Stage 3 routes through `fal-ai/flux-kontext-lora/inpaint` with:

```python
arguments = {
    "image_url": clean_garment_url,
    "mask_url": mask_url,
    "prompt": f"SKYR_EMBOSS {decoration_description}",
    "loras": [{"path": LORA_WEIGHTS_URL, "scale": 0.85}],
    ...
}
```

LoRA scale 0.85 (slightly under 1.0) balances LoRA influence against base model fidelity.

### 11.5 LoRA evaluation

After training, smoke-test on:
- br-001 Black Rose Crewneck (embossed-on-black, hardest case)
- lh-005 The Fannie (embossed wordmark on faux-leather)
- sg-002 Stay Golden Shirt (small chest cluster)

Compare with-LoRA vs without-LoRA via vision audit pass rate.

---

## 12. Migration plan

### 12.1 What stays

- `skyyrose/core/dossier_loader.py` — unchanged
- `skyyrose/elite_studio/agents/vision_audit_agent.py` — unchanged (already patched for LOW-severity)
- `skyyrose/elite_studio/forensics.py` — extended with new stage fields
- `wordpress-theme/skyyrose-flagship/data/dossiers/*.md` — unchanged
- `scripts/validate_dossier.py` — unchanged
- `scripts/check_dossier_coverage.py` — unchanged

### 12.2 What changes

- `skyyrose/elite_studio/agents/three_d_agent.py` Stage 3 — replaces `gen_2d.generate(...)` call with `synthesis.flux_pipeline.render(sku, view, dossier, scaffold_path, techflat_path)`. The retry loop (H4) stays in `three_d_agent.py`; the synthesis module is the inner call.

### 12.3 What's new

- `skyyrose/elite_studio/synthesis/` (full module per Section 5)
- Static mask templates per garment_type
- LoRA training script + dataset (`scripts/train_decoration_lora.py`)

### 12.4 Rollout

1. Land synthesis module + tests (no production calls)
2. Smoke br-001 (1 SKU, ~$0.20)
3. Smoke 3 hard cases (br-001 emboss, lh-005 emboss, sg-002 small cluster)
4. Train LoRA, smoke same 3 cases with LoRA active
5. Run full 30-SKU × 2-view batch
6. Manual QC pass on output
7. Move passing renders to assets/, update CSV, deploy

---

## 13. Open questions / risks

1. **fal.ai concurrency limits.** Need to verify per-account concurrent request limits. If low (e.g., 5), batch parallelism is bounded. Mitigation: sequential or small-pool execution; not blocking.

2. **FLUX Kontext on techflat fidelity.** Kontext is designed for editing photographs, not transforming vector techflats. There's risk that Kontext "interprets" the techflat into a stylized render rather than a clean garment shape. Mitigation: test on br-001; if poor, switch Stage 1 to FLUX.1.1 Pro Ultra (text-to-image with techflat as ControlNet) or use the existing Blender scaffold as Stage 1 input directly.

3. **Mask dimension matching.** FLUX Kontext output dimensions depend on `aspect_ratio`. Mask must match exactly. Mitigation: lock aspect ratio, resize Stage 1 output to canonical 1024x1024 before mask derivation.

4. **LoRA generalization.** A LoRA trained on embossed cotton may not transfer to embossed nylon. Mitigation: include 5-10 different fabric types in training set; if generalization is poor, train per-fabric LoRAs (small dataset each).

5. **Replicate model availability.** `ostris/flux-dev-lora-trainer` may or may not be the current best. Mitigation: confirm via Replicate model search before training.

6. **IC-Light V2 schema.** Context7 didn't surface fal docs for `iclight-v2`. Verify schema before integration. Mitigation: Stage 4 is optional — skip on first batch.

7. **Cost modeling.** Stages have variable cost per render (Kontext fixed $0.04, Fill $0.05, Flash audit $0.005, optional IC-Light ~$0.02). Per-SKU cost ~$0.10 × 60 renders = ~$6 baseline + retries. No hard cap, but observability flags spending tiers.

---

## 14. Definition of done

The pipeline is "done" when:

- All unit tests pass (mocked fal_client paths).
- Integration smoke (br-001) produces output that passes the existing vision audit gate.
- Three hard-case smokes (br-001, lh-005, sg-002) produce outputs Corey approves visually.
- LoRA trained, weights URL persisted.
- Full batch (30 SKUs × 2 views) completes with ≤10% quarantine rate.
- All forensic manifests written.
- README in `synthesis/` module covers env setup, CLI commands, troubleshooting.

---

## 15. Decisions to ratify

These are the decisions baked into this design that the user should ack before I start coding:

1. **fal.ai over direct BFL API.** Reason: existing wiring, single API key, IC-Light V2 hosted there, LoRA inference via `flux-kontext-lora/inpaint`.
2. **Gemini Flash vision-guided masking with static-template fallback.** Reason: aligns with dossier region names without maintaining a separate mask registry; cheap; falls back gracefully.
3. **Async + queued (`AsyncClient.subscribe`) over sync.** Reason: progress events, better timeout handling, supports `asyncio.gather` for concurrency once limits allow.
4. **Replicate `ostris/flux-dev-lora-trainer` for LoRA training** (current top community trainer). Confirm at training time.
5. **LoRA scale 0.85 default** (slightly under 1.0 for stability). Tunable per smoke test.
6. **No hard cost cap; log tier warnings only.** Per user directive.
7. **Stage 4 (IC-Light V2) deferred to v2.** Stage 1 prompt already specifies studio lighting.
8. **Test strategy: TDD with mocked fal_client + gated integration smoke.** No API calls in CI.
