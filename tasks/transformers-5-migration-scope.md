# transformers 4 → 5 — migration scope

**Status:** SCOPE ONLY (not executed). Current pin `transformers>=4.53.0`, locked **4.57.6**.
**Date:** 2026-07-18

## Why this is on the table

Two Dependabot **HIGH** alerts, both patched only in the 5.x major:

| Alert | GHSA | Patched | What it is | Reachable here? |
|---|---|---|---|---|
| #939 | GHSA-29pf-2h5f-8g72 | 5.3.0 | RCE (arbitrary code exec on model load) | **Only with an untrusted model.** Our sites load trusted, named models (CLIP/DINO/brand-voice) — not attacker-controlled repos. Low practical reachability. |
| #948 | GHSA-fgcw-684q-jj6r | 5.5.0 | Arbitrary code exec in the **LightGlue** model-loading path | **Not reachable** — grep confirms no LightGlue usage anywhere. |

**Neither is reachable with attacker-controlled input in the current codebase** (no untrusted-model loading, no LightGlue). This mirrors the litellm situation: real CVE severity, but the vulnerable path isn't exercised.

## Decision: two paths

### Path A — Dismiss (proportionate, recommended unless untrusted models are ever loaded)
- #948 (LightGlue): dismiss `not_used` — LightGlue not used. Unambiguous.
- #939 (RCE-on-load): dismiss `not_used` **iff** the codebase never loads a model from an untrusted/user-supplied source. Verify: audit every `from_pretrained` / `pipeline(model=...)` — are the model IDs all hardcoded/config-pinned (trusted), or can any come from user input? If all trusted → dismiss. If any user-supplied → do Path B or gate the input.
- Cost: minutes. No code churn, no ML-stack risk.

### Path B — Migrate to transformers ≥5.5.0 (defense-in-depth / zero open highs)
Bump `transformers>=5.5.0`, re-lock, fix breakage.

## Migration surface — 15 files (verified via git grep)

| Area | Files | transformers API |
|---|---|---|
| CLIP embeddings | `skyyrose/core/embeddings/clip.py`, `dino.py`, `device.py` | CLIPModel, CLIPProcessor, CLIPVisionModelWithProjection, CLIPTextModel(WithProjection), AutoImageProcessor, AutoModel |
| Imagery / SDXL / LoRA | `imagery/sdxl_pipeline.py`, `lora_trainer.py`, `visual_comparison.py` | CLIPTextModel, CLIPTextModelWithProjection, get_scheduler, BitsAndBytesConfig, PretrainedConfig |
| Brand-voice training | `scripts/training/train_brand_voice.py`, `modal_train_brand_voice.py`, `scripts/train_dreambooth_lora_sdxl.py`, `scripts/generate_ai_models_with_products.py` | AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, get_scheduler |
| Agents / workflows / QA | `agents/base_super_agent/ml_module.py`, `devskyy_workflows/ml_workflow.py`, `imagery/quality/ml_classifier.py`, `skyyrose/elite_studio/quality/ml_classifier.py` | pipeline, AutoModel, AutoTokenizer, transformers.utils, transformers.__version__ |

Surface is **mainstream, stable APIs** (CLIP, Auto*, pipeline, training utils) — not deprecated/niche classes. That lowers migration risk considerably.

## 5.x breaking-change categories to verify BEFORE executing (Context7 / release notes)

> **MANDATORY at execution time:** `Context7 resolve-library-id transformers` → `query-docs "v5 migration breaking changes"`. Do NOT bump blind. Known 5.0 change areas to check against our surface:

1. **`from_pretrained` defaults** — `use_safetensors`, `torch_dtype`/`dtype` arg rename, `trust_remote_code` default tightening (relevant to CLIP/Auto loads).
2. **Tokenizer defaults** — fast tokenizers default; check AutoTokenizer callers for `use_fast`/return-type changes.
3. **`pipeline`** — signature/return-shape changes; 2 call sites.
4. **Removed deprecated classes/args** — audit for anything removed (our surface looks clean but verify).
5. **Quantization** — `BitsAndBytesConfig` API stability across 5.x (LoRA/brand-voice training).
6. **Python / torch floor** — 5.x may raise min Python or torch; confirm compatible with our torch 2.9.1 pin (just reconciled in #761).
7. **diffusers/accelerate/peft compat** — SDXL+LoRA stack: transformers 5.x must be compatible with the pinned diffusers/accelerate/peft versions; re-resolve may cascade.

## Plan (Path B)

1. Context7 the 5.x migration guide; diff against the surface table above.
2. Bump `transformers>=5.5.0` in `pyproject.toml`; `uv lock` (watch for diffusers/accelerate/peft cascade — the ML stack is tightly coupled).
3. Fix call sites per the breaking-change diff (expect: `dtype` arg, tokenizer `use_fast`, pipeline returns).
4. **Test surface (the real gate):** run the imagery/embeddings/training tests — CLIP embedding output parity, SDXL pipeline load, a LoRA/brand-voice training smoke. These are heavy (GPU/model download); budget for it.
5. Verify Dependabot rescan closes #939 + #948.

## Effort / risk

- **Path A (dismiss):** ~15 min (audit model-load trust boundary + dismiss). **Low risk.**
- **Path B (migrate):** ~0.5–1.5 day. Risk concentrated in the **ML-stack re-resolve** (transformers 5.x ↔ diffusers/accelerate/peft/torch 2.9.1) and **runtime parity** of CLIP embeddings / SDXL / training — not the API edits themselves.

## Recommendation

**Path A** unless you load untrusted models anywhere. First action either way: audit the model-load trust boundary (all `from_pretrained`/`pipeline(model=...)` IDs). If all trusted → dismiss both, done. If any user-supplied → gate that input AND do Path B.
