# agents/render_pipeline/tools/ — ADK FunctionTool implementations (9 modules)

Pure-Python tool functions wrapped by `google.adk.tools.FunctionTool` and assigned to the 9 LlmAgents in the SequentialAgent pipeline. Each file = one step. No LLM calls inside tools (the wrapping LlmAgent owns LLM dispatch); tools do file I/O, vision API calls, and prompt assembly.

## Inventory (matches 9-step pipeline order)

| File | Function | Step | What it does |
|------|----------|------|--------------|
| `load_dossier.py` | `load_dossier_fn` | 1 | Reads `knowledge-base/products/<sku>/dossier.md` — Layers 3 + 2 canonical garment facts |
| `resolve_source.py` | `resolve_source_fn` | 2 | Resolves the source image path for the SKU + view (front/back/detail) |
| `vision_consensus.py` | `vision_consensus_fn` | 3 | Parallel vision call to gemini-3-flash + gpt-4o; merges + returns dual-judge consensus |
| `route_engine.py` | `route_engine_fn` | 4 | Catalog `engine_override` first; vision-driven fallback (F3 fix) |
| `articulate_layer0.py` | `articulate_layer0_fn` | 5 | Writes Layer 0 (rendering directives only) — Sonnet drives this |
| `build_prompt.py` | `build_prompt_fn` | 6 | Assembles final prompt: L0 (Sonnet) + L3 + L2 (verbatim from dossier) |
| `generate_image.py` | `generate_image_fn` | 7 | Engine dispatch — Nano Banana Pro / gpt-image-1.5 / FLUX-pro-v1.1 |
| `qa_tournament.py` | `qa_tournament_fn` | 8a | 3-judge tournament (gpt-5.5-pro + gemini-3.1-pro-preview + opus-4-7) + records to Loops 1/2/3 |
| `refine_image.py` | `refine_image_fn` | 8c | Re-generate with refinement directives from ScoreReasonerAgent |
| `_paths.py` | path helpers | — | Resolves render output paths under `renders/output/<sku>/<view>/<engine>/` |

## FunctionTool contract

```python
from google.adk.tools import FunctionTool

def load_dossier_fn(sku: str, tool_context) -> dict:
    """Load canonical dossier for SKU. Writes to state.dossier.

    Raises: DossierNotFoundError — never falls back to CSV branding_spec.
    """
    ...

# In agent.py:
load_dossier_agent = LlmAgent(
    name="LoadDossierAgent",
    model="gemini-2.5-flash",
    instruction="Load dossier for the provided SKU using the load_dossier tool.",
    tools=[FunctionTool(load_dossier_fn)],
    output_key="dossier",
)
```

State is auto-injected via `tool_context.state`. Tool writes side-effects + the framework persists `output_key` automatically.

## Output paths (`_paths.py`)

```
renders/output/<sku>/<view>/<engine>/<timestamp>.png
```

Example: `renders/output/br-001/front/nano_banana_pro/2026-05-20T12-39-44Z.png`

The `generate_image_fn` call graph was mapped 2026-05-12 (cmem #3824). All paths must match this shape for downstream pipelines (asset_pipeline, WC upload, QA review) to find renders.

## Vision consensus (Step 3) — dual-judge

`vision_consensus_fn` invokes **two vision models in parallel** and merges:

- `gemini-3-flash-preview` — fast, cheap, broad coverage
- `gpt-4o` — slower, often catches different artifacts

Never Claude — vision is a Claude weakness (per `llm/model_ids.py` comment). Output is a merged `VisionConsensus` Pydantic model with both judges' findings + a `confidence` score.

## Engine dispatch (Step 7)

`generate_image_fn` reads `state.engine` from `route_engine_fn` and dispatches:

| Engine value | Model | Notes |
|--------------|-------|-------|
| `nano_banana_pro` | `gemini-3-pro-image-preview` (4K) | Default for hero shots |
| `nano_banana_2` | `gemini-3.1-flash-image-preview` | Default for non-hero — cheaper |
| `gpt_image_15` | `gpt-image-1.5` | OpenAI side — text-on-image stronger |
| `flux_pro_v1.1` | `flux-pro-v1.1` via fal-client | Highest fidelity, highest cost |

Per `llm/model_ids.py` — never hardcode model strings. Tools import the aliases.

## Conventions

- **Pure functions, no global state.** Tools are stateless — state flows through `tool_context.state`.
- **Pydantic for inputs + outputs.** All function signatures use Pydantic models. `output_schema` on the LlmAgent picks up the type.
- **Side-effects via `tool_context.actions`** (e.g. `state_delta` updates) — not via direct return values that the LLM has to interpret.
- **Hard-fail, no silent fallback.** Missing dossier → raise. Vision API down → raise (don't degrade to single-judge). Invariants matter.
- **Path resolution via `_paths.py`.** Never construct paths inline — call `_paths.render_output_path(sku, view, engine, timestamp)`.
- **Cost markers in docstrings.** `$$$` for tournament, `$$` for refine, `$` for image gen — operator awareness.

## Don't

- Don't make LLM calls from tools. The wrapping `LlmAgent` owns LLM dispatch. Tools do work; they don't reason.
- Don't bypass `_paths.py`. Render paths are the integration contract with `orchestration/asset_pipeline.py`.
- Don't fall back to CSV `branding_spec` when dossier is missing. Hard-fail. The pipeline cannot produce trustworthy output without the dossier.
- Don't add an engine without registering it in `route_engine.py` + `generate_image.py` + updating the docstring engine table in DESIGN.md.
- Don't disable dual-judge vision to save cost. Single-judge consensus is single-point-of-failure — both judges must run.

## Related

- Parent pipeline: `agents/render_pipeline/agent.py` (root_agent = SequentialAgent)
- ADK framework: `google.adk.tools.FunctionTool`
- Output destination: `renders/output/<sku>/<view>/<engine>/`
- Dossier source: `knowledge-base/products/<sku>/dossier.md`
- Catalog source (engine_override): `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`
- Skip list: `renders/ghost-mannequin/SKIPPED.json`
- Model IDs: `llm/model_ids.py`

## Recent learnings

- 9 tools = 9 pipeline steps — 1:1 mapping is intentional, do not collapse.
- Cost surface audited (cmem #3474, 2026-05-11) — tournament is the most expensive step by 5-10×.
- Engine routing F3 fix (cmem #2476): catalog override > vision-driven default. Codified in `route_engine.py`.
