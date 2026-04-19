# Elite Studio Layer 2 — Pipeline Stages

Layer 2 adds 5 optional pipeline stages to the Elite Studio LangGraph engine.
All stages are opt-in via `GraphConfig` flags. The existing Layer 1 pipeline
runs unchanged when all Layer 2 flags are at their defaults.

## Stages

### 1. Prompt Enrichment (`enable_prompt_enrichment=True`, on by default)

**Agent:** `PromptEnrichmentAgent`
**Node:** `prompt_enrichment_node`
**Position:** Between `vision` and `generator`

Rule-based enrichment — no LLM call, zero cost. Prepends collection DNA
(sourced from `SCENE_LOOKBOOK` + `_COLLECTION_DNA`) and appends style modifiers
(lighting, model type, brand aesthetic) to the vision spec. If enrichment
succeeds, `vision_result.unified_spec` is updated in state so downstream nodes
use the richer spec automatically.

**Collection DNA:**
- `black-rose` — Oakland East Bay luxury streetwear, night, concrete aesthetic
- `love-hurts` — Gothic cathedral, enchanted rose dome, crimson palette
- `signature` — SF Golden Gate golden hour, fog, fashion runway energy
- `kids-capsule` — Vibrant playful luxury, rose gold accent

**Result:** `EnrichedPrompt` stored in `state.enriched_prompt`

---

### 2. Safety Filter (`enable_safety=True`, on by default)

**Agent:** `SafetyAgent`
**Node:** `safety_node`
**Position:** Between `generator` and `quality`

Two-pass content check:
1. OpenAI Moderation API (`client.moderations.create`) — text pass
2. GPT-4o vision — image safety check (base64 encoded)

If either pass flags content, `safety_result.flagged=True` is set,
`status="error"` and `failed_step="safety_filter"` are written to state,
and the routing edge sends the pipeline to `END` (bypassing QC and finalize).

**Result:** `SafetyResult` stored in `state.safety_result`

---

### 3. Upscaling (`enable_upscaling=False`, off by default)

**Agent:** `UpscalingAgent`
**Node:** `upscaling_node`
**Position:** After quality gate passes

Primary: Real-ESRGAN via Replicate API (`nightmareai/real-esrgan`).
Fallback: `PIL.Image.resize` with `LANCZOS` filter.

The provider used is recorded in `UpscaleResult.provider` (`"replicate"` or
`"pil_lanczos"`). A Replicate failure automatically falls back to PIL.

**Result:** `UpscaleResult` stored in `state.upscale_result`

---

### 4. Color Correction (`enable_color_correction=False`, off by default)

**Agent:** `ColorCorrectionAgent`
**Node:** `color_correction_node`
**Position:** After upscaling (or after quality if upscaling is disabled)

PIL-only corrections guided by the SkyyRose brand palette
(`#B76E79` rose gold, `#0A0A0A` dark, `#D4AF37` gold):

| Step | Enhancement | Factor |
|------|------------|--------|
| 1 | Contrast boost | 1.15 |
| 2 | Saturation nudge (rose gold warmth) | 1.08 |
| 3 | Brightness correction (studio lift) | 1.05 |
| 4 | Sharpness pass (garment detail) | 1.10 |

Each adjustment is recorded in `ColorCorrectionResult.adjustments_applied`.

**Result:** `ColorCorrectionResult` stored in `state.color_result`

---

### 5. Variants (`enable_variants=False`, off by default)

**Agent:** `VariantAgent`
**Node:** `variant_node`
**Position:** After quality gate (parallel with post-processing, joins at finalize)

Generates alternate angles or colorways by calling `GeneratorAgent` with
a modified spec per variant. Partial success is allowed — each variant is
attempted independently and a per-variant `VariantResult` is recorded.

**Built-in variant names:**

| Name | Description |
|------|-------------|
| `back_view` | Full back of garment, rear branding |
| `side_view` | 90-degree profile, silhouette |
| `detail_shot` | Macro close-up of branding/stitching |
| `flat_lay` | Overhead flat lay, no model |
| `lifestyle` | Model in collection-context environment |

Custom variant names generate a generic angle modifier.

Configure via `GraphConfig(enable_variants=True, variant_specs=["back_view", "side_view"])`.
The `variant_specs` list is passed into `state` at invocation time.

**Result:** `list[VariantResult]` stored in `state.variant_results`

---

## Graph Topology

```
vision
  └─► [prompt_enrichment?]
        └─► generator
              └─► [safety?] ──flagged──► END
                    └─► quality
                          ├─► [retry]──► generator
                          └─► [proceed]
                                └─► [upscaling?]
                                      └─► [color_correction?]
                                            └─► [variants?]
                                                  └─► [compositor?]
                                                        └─► finalize ──► END
```

---

## GraphConfig Reference

```python
from skyyrose.elite_studio.graph import GraphConfig, build_graph

# Full Layer 2 enabled
cfg = GraphConfig(
    max_retries=2,
    enable_compositor=True,
    enable_prompt_enrichment=True,   # default: True
    enable_safety=True,              # default: True
    enable_upscaling=True,           # default: False — costs Replicate $
    enable_color_correction=True,    # default: False
    enable_variants=True,            # default: False
    variant_specs=["back_view", "side_view"],
)

graph = build_graph(cfg)
```

---

## State Fields Added

```python
enriched_prompt: EnrichedPrompt | None
upscale_result:  UpscaleResult | None
color_result:    ColorCorrectionResult | None
safety_result:   SafetyResult | None
variant_results: list[VariantResult] | None
```

---

## New Models (all `@dataclass(frozen=True)`)

- `EnrichedPrompt` — prompt enrichment result
- `UpscaleResult` — upscaling result with provider field
- `ColorCorrectionResult` — PIL correction result with adjustments tuple
- `SafetyResult` — safety check result with flagged + categories
- `VariantSpec` — spec for a single variant (name + prompt_modifier)
- `VariantResult` — per-variant generation result
