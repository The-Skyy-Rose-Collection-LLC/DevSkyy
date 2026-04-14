# Elite Studio Layer 2 — New Pipeline Stages

## Context

You are working in `/Users/theceo/DevSkyy` (or `../elite-layer-2` worktree), branch `elite/layer-2-pipeline-stages`.

Layer 1 is already merged to `wp-theme-work` and provides the LangGraph graph engine at `skyyrose/elite_studio/graph/`. Your job is Layer 2: add 5 new processing agents as graph nodes.

**Pre-reads (do these first):**
- `skyyrose/elite_studio/graph/nodes.py` — existing node pattern to follow
- `skyyrose/elite_studio/graph/state.py` — state fields to extend
- `skyyrose/elite_studio/graph/builder.py` — topology to extend
- `skyyrose/elite_studio/models.py` — existing frozen dataclasses
- `skyyrose/elite_studio/agents/quality_agent.py` — example agent structure
- `pyproject.toml` — existing dependencies (add replicate, Pillow if not present)

---

## Goal

Add 5 new agents + their graph nodes. Each node is optional (disabled by default via GraphConfig flag). Existing pipeline must be unaffected when all new nodes are disabled.

---

## New Agents (one file each in `skyyrose/elite_studio/agents/`)

### 1. `prompt_enrichment_agent.py`
- Class: `PromptEnrichmentAgent`
- No LLM call needed — rule-based enrichment
- Input: `(sku: str, vision_spec: str)` → Output: `EnrichedPrompt`
- Logic: prepend brand/collection DNA from `agents/compositor_agent.py`'s SCENE_LOOKBOOK and collection names to the vision spec; append style modifiers (lighting, model type, brand aesthetic)
- Node: `prompt_enrichment_node` — runs between `vision_node` and `generator_node`

### 2. `upscaling_agent.py`
- Class: `UpscalingAgent`
- Primary: Real-ESRGAN via Replicate API (`nightmareai/real-esrgan`)
- Fallback: `PIL.Image.resize` with LANCZOS
- Input: `(image_path: str, target_resolution: tuple[int, int] = (2048, 2048))` → Output: `UpscaleResult`
- Node: `upscaling_node` — runs after `quality_node` passes, before compositor

### 3. `color_correction_agent.py`
- Class: `ColorCorrectionAgent`
- Uses PIL for corrections (contrast, saturation, white balance) guided by brand palette
- Brand palette from `config.py` or hardcoded: `{"rose_gold": "#B76E79", "dark": "#0A0A0A"}`
- Input: `(image_path: str)` → Output: `ColorCorrectionResult`
- Node: `color_correction_node` — runs after `upscaling_node` (or after quality if upscaling disabled)

### 4. `safety_agent.py`
- Class: `SafetyAgent`
- Uses OpenAI moderation API: `client.moderations.create(input=...)`
- For images: encode to base64, use `gpt-4o` with system prompt checking for inappropriate content
- Input: `(image_path: str)` → Output: `SafetyResult`
- Node: `safety_node` — runs between `generator_node` and `quality_node`
- If safety fails: set `status="error"`, `failed_step="safety_filter"`

### 5. `variant_agent.py`
- Class: `VariantAgent`
- Uses existing `GeneratorAgent` with modified prompts for alternate angles/colorways
- Input: `(sku: str, base_image_path: str, spec: str, variants: list[str])` where variants are e.g. `["back_view", "side_view"]`
- Output: `list[VariantResult]`
- Node: `variant_node` — runs in parallel branch after quality gate (see topology below)

---

## New Models (add to `skyyrose/elite_studio/models.py`)

```python
@dataclass(frozen=True)
class EnrichedPrompt:
    success: bool
    original_spec: str = ""
    enriched_spec: str = ""
    additions: tuple[str, ...] = ()
    error: str = ""

@dataclass(frozen=True)
class UpscaleResult:
    success: bool
    output_path: str = ""
    original_resolution: tuple[int, int] = (0, 0)
    final_resolution: tuple[int, int] = (0, 0)
    provider: str = ""  # "replicate" or "pil_lanczos"
    error: str = ""

@dataclass(frozen=True)
class ColorCorrectionResult:
    success: bool
    output_path: str = ""
    adjustments_applied: tuple[str, ...] = ()
    error: str = ""

@dataclass(frozen=True)
class SafetyResult:
    success: bool
    flagged: bool = False
    categories: tuple[str, ...] = ()
    error: str = ""

@dataclass(frozen=True)
class VariantSpec:
    name: str  # e.g. "back_view"
    prompt_modifier: str

@dataclass(frozen=True)
class VariantResult:
    success: bool
    variant_name: str = ""
    output_path: str = ""
    error: str = ""
```

---

## State Fields to Add (`graph/state.py`)

```python
# Layer 2 stage results
enriched_prompt: EnrichedPrompt | None
upscale_result: UpscaleResult | None
color_result: ColorCorrectionResult | None
safety_result: SafetyResult | None
variant_results: list[VariantResult] | None
```

---

## GraphConfig Fields to Add (`graph/builder.py`)

```python
enable_prompt_enrichment: bool = True   # on by default (pure enrichment, no cost)
enable_safety: bool = True              # on by default
enable_upscaling: bool = False          # off by default (costs $)
enable_color_correction: bool = False   # off by default
enable_variants: bool = False           # off by default
variant_specs: list[str] = []           # e.g. ["back_view"]
```

---

## Updated Graph Topology (`graph/builder.py`)

```
vision → [prompt_enrichment?] → generator → [safety?] → quality
quality → [retry?] → generator
quality → [proceed] → [upscaling?] → [color_correction?] → compositor → finalize
                   → [variants?] → variant_generation (joins at finalize)
```

Key rules:
- prompt_enrichment: if enabled, replace vision node's `unified_spec` with `enriched_spec` in state before generator runs
- safety: if enabled and flags content, route to END with error (not finalize)
- upscaling + color_correction: optional sequential post-processing chain
- variants: parallel branch — collect into `variant_results`, join before finalize

---

## Files to Create

| File | Purpose |
|------|---------|
| `skyyrose/elite_studio/agents/prompt_enrichment_agent.py` | PromptEnrichmentAgent |
| `skyyrose/elite_studio/agents/upscaling_agent.py` | UpscalingAgent (Replicate + PIL fallback) |
| `skyyrose/elite_studio/agents/color_correction_agent.py` | ColorCorrectionAgent (PIL) |
| `skyyrose/elite_studio/agents/safety_agent.py` | SafetyAgent (OpenAI moderation) |
| `skyyrose/elite_studio/agents/variant_agent.py` | VariantAgent |
| `skyyrose/elite_studio/tests/test_prompt_enrichment_agent.py` | Tests |
| `skyyrose/elite_studio/tests/test_upscaling_agent.py` | Tests |
| `skyyrose/elite_studio/tests/test_color_correction_agent.py` | Tests |
| `skyyrose/elite_studio/tests/test_safety_agent.py` | Tests |
| `skyyrose/elite_studio/tests/test_variant_agent.py` | Tests |
| `docs/elite-studio/LAYER_2_PIPELINE_STAGES.md` | Architecture doc |

## Files to Modify

| File | Change |
|------|--------|
| `skyyrose/elite_studio/models.py` | Add 6 new frozen dataclasses |
| `skyyrose/elite_studio/graph/state.py` | Add 5 new optional state fields |
| `skyyrose/elite_studio/graph/nodes.py` | Add 5 new node functions |
| `skyyrose/elite_studio/graph/edges.py` | Add safety routing edge |
| `skyyrose/elite_studio/graph/builder.py` | Extend GraphConfig + topology |
| `skyyrose/elite_studio/graph/__init__.py` | Export new symbols |

---

## Standards

- All result types: `@dataclass(frozen=True)` with `success: bool` as first field
- All agents: synchronous, wrap exceptions internally, return result with `success=False` + error message
- All new nodes: pattern from existing `vision_node` — time the call, accumulate `stage_timings`
- Tests: mock all external APIs (OpenAI, Replicate), 85%+ coverage on new code
- Files: <800 lines, functions <50 lines
- Run: `python -m pytest skyyrose/elite_studio/tests/ -v` — all tests pass including Layer 1

---

## Verification

1. `pytest skyyrose/elite_studio/tests/ -v` — 69 Layer 1 tests + all new tests pass
2. `python -m skyyrose.elite_studio produce br-001 --graph` — unchanged (all new nodes disabled)
3. GraphConfig with all nodes enabled produces correct topology (test in test_graph_builder.py)
4. Safety failure routes to error, not finalize
