# agents/render_pipeline/ — ADK render pipeline for SkyyRose SKUs

**Google ADK agent** that orchestrates a 9-step `SequentialAgent` to generate, QA-tournament, and refine product renders. Validated against `/google/adk-python` via Context7 (cmem #2476, 2026-05-06). Lives in its own runtime (requires `.venv-agents/` per CLAUDE.md — numpy conflicts with main `.venv`).

## 9-step pipeline (validated architecture)

```
SequentialAgent (framework-dispatched — no top-level LLM)
│
├── 1. LoadDossierAgent          gemini-2.5-flash    → load_dossier_fn
├── 2. ResolveSourceAgent        gemini-2.5-flash    → resolve_source_fn
├── 3. VisionConsensusAgent      gemini-2.5-flash    → vision_consensus_fn
│     └── internally: gemini-3-flash-preview + gpt-4o in parallel (dual-judge)
├── 4. RouteEngineAgent          gemini-2.5-flash    → route_engine_fn
│     └── catalog `engine_override` first; vision-driven fallback
├── 5. ArticulateLayer0Agent     claude-sonnet-4-6   (no tool — direct LLM)
│     └── writes Layer 0 (rendering directives ONLY)
│     └── NEVER touches Layers 3 + 2 (canonical dossier — verbatim)
├── 6. BuildPromptAgent          gemini-2.5-flash    → build_prompt_fn
│     └── assembler: L0 (Sonnet) + L3 (verbatim) + L2 (verbatim)
├── 7. GenerateImageAgent        gemini-2.5-flash    → generate_image_fn  ($)
│     └── engine = NB Pro / GPT-image-1.5 / FLUX-pro-v1.1
├── 8. QAAndRefineLoop           LoopAgent(max_iterations=2)
│     ├── QaTournamentAgent      gemini-2.5-flash    → qa_tournament_fn  ($$$)
│     │     └── tournament: gpt-5.5-pro + gemini-3.1-pro-preview + opus-4-7
│     │     └── records to learning loops (Loops 1, 2, 3)
│     ├── ScoreReasonerAgent     gemini-3-pro-preview  (no tool — reasoning)
│     │     └── outputs 'pass' | 'refine' | 'abort' (F5 classifier)
│     ├── StopChecker (custom BaseAgent — escalates on pass/abort)
│     └── RefineImageAgent       gemini-2.5-flash    → refine_image_fn  ($$)
└── 9. SynthesisAgent            claude-opus-4-7     (no tool — Pydantic output_schema)
       └── reads full session state, emits RenderResult
```

**State flow:** each sub-agent reads from `tool_context.state` (auto-injected) and writes via tool side-effects + `output_key`. `SequentialAgent` guarantees order without LLM drift. `LoopAgent` handles iterative refinement up to `max_iterations`.

## Quickstart

```python
from agents.render_pipeline import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

runner = Runner(
    agent=root_agent,
    app_name="render",
    session_service=InMemorySessionService(),
)
# See DESIGN.md "CLI / entry points" for full invocation
```

## CLI

```bash
adk run agents/render_pipeline --input '{"sku": "br-001", "view": "front"}'
```

Or via the included CLI wrapper:

```bash
python agents/render_pipeline/cli.py --sku br-001 --view front
```

## Cost surface (audited cmem #3474, 2026-05-11)

| Step | Tier | Approx cost per render |
|------|------|------------------------|
| Steps 1-6 (load/resolve/vision/route/articulate/build) | Cheap | ~$0.01 (all gemini-2.5-flash + opus-sonnet on Articulate) |
| Step 7 GenerateImageAgent | `$` | $0.04-$0.15 (varies by engine — NB Pro is 4K, FLUX-pro is highest) |
| Step 8 QaTournamentAgent | `$$$` | $0.20-$0.40 (3-judge tournament — gpt-5.5-pro + gemini-3.1 + opus-4-7) |
| Step 8 RefineImageAgent (per loop iteration) | `$$` | $0.04-$0.15 |
| Step 9 SynthesisAgent | Cheap | ~$0.02 (claude-opus-4-7 with `output_schema`) |

**Typical full-cycle render: ~$0.40-$0.80** with 1-2 refinement loop iterations. Multiply by SKU count for batch jobs.

## Layer model (load-bearing — do not violate)

The articulate step writes **Layer 0** (rendering directives — lighting, angle, camera, mood) ONLY. Layers 3 + 2 are the **canonical dossier** (garment facts: silhouette, material, colorway, trims, sizing) — they're injected **verbatim** into the prompt by `BuildPromptAgent`. Sonnet does NOT rewrite Layers 3 + 2 — that's the canonical authoring rule.

Per project memory `feedback_no_silent_fallback.md`: 3D pipeline hard-fails on missing dossier; CSV `branding_spec` is NOT a fallback. Render pipeline inherits this — `LoadDossierAgent` raises on missing dossier rather than substituting.

## Files

```
render_pipeline/
├── __init__.py              re-exports root_agent
├── agent.py                 root_agent = SequentialAgent([...]) — full 9-step wiring
├── cli.py                   CLI wrapper around adk run
├── DESIGN.md                Architectural design doc (F3 routing fix, layer model, cost analysis)
├── README.md                User-facing entry point
├── tools/                   9 FunctionTool wrappers — see tools/CLAUDE.md
├── eval/                    Eval harness for the full pipeline — see eval/CLAUDE.md
├── learning/                Three learning loops + LOOP.md — see learning/CLAUDE.md
└── tests/                   Per-tool unit tests — see tests/CLAUDE.md
```

## Engine routing (F3 fix, cmem #2476)

The load-bearing fix from the May 2026 empirical investigation: **catalog `engine_override` is the authoritative source**. Vision-driven engine selection is the fallback for SKUs that don't have an override set.

`RouteEngineAgent` flow:
1. Check `catalog.engine_override` for this SKU → if set, use it
2. Otherwise, call `vision_consensus` result → routing rules
3. Default → `NANO_BANANA_2_MODEL` (gemini-3.1-flash-image-preview)

Don't bypass this hierarchy. Manual overrides go into the catalog CSV; ad-hoc engine flags in the request payload are discouraged.

## Conventions

- **ADK FunctionTools, not direct LLM calls.** Each step is a `LlmAgent(tools=[FunctionTool(<fn>)])`. The LLM picks tool invocation; the tool does the actual work. Keeps state contract explicit.
- **No imports from main `.venv`.** Use `.venv-agents/` (the ADK-isolated env per `DevSkyy/CLAUDE.md`). `numpy` version conflicts otherwise.
- **Model IDs from `llm/model_ids.py` only.** Don't hardcode `"claude-opus-4-7"` — import the alias.
- **Output paths via `_paths.py`.** Renders land in `renders/output/<sku>/<view>/<engine>/<timestamp>.png`. The `generate_image_fn` call graph was mapped 2026-05-12 (cmem #3824) — paths must match.
- **Learning Loops 1, 2, 3** record outcomes for adaptive improvement — see `learning/` subdir + `learning/LOOP.md`.

## STOP AND SHOW

Steps 7 + 8 are paid. Per project policy, batch runs surface manifest + estimated cost before dispatch. `cli.py --dry-run` shows the manifest without paying.

## Don't

- Don't write to Layers 3 + 2 from `ArticulateLayer0Agent`. Layer 0 only — canonical dossier is verbatim.
- Don't bypass `catalog.engine_override`. F3 fix is intentional architecture.
- Don't add a step without updating `agent.py` SequentialAgent list AND the state contract in DESIGN.md.
- Don't run from the main `.venv` — numpy will conflict. Use `.venv-agents/`.
- Don't substitute CSV `branding_spec` for a missing dossier. Hard-fail.

## Related

- Architecture spec: `agents/render_pipeline/DESIGN.md`
- ADK package: `google-adk` in `.venv-agents/`
- Verified model IDs: `llm/model_ids.py`
- Path config: `agents/render_pipeline/tools/_paths.py`
- Asset pipeline alternative (batch + WC upload): `orchestration/asset_pipeline.py`
- Pre-flight skip list: `renders/ghost-mannequin/SKIPPED.json`
- Canonical dossiers: `knowledge-base/products/<sku>/`

## Recent learnings

- 9-step SequentialAgent architecture confirmed (cmem #3707, 2026-05-12; #3535, 2026-05-11).
- F3 engine routing fix: catalog `engine_override` is authoritative (cmem #2476, 2026-05-06).
- Cost surface audited (cmem #3474, 2026-05-11).
- Merged to main (cmem #3442, 2026-05-11) via PR #501.
- Layer model is load-bearing — Layer 0 from Sonnet ONLY, Layers 3 + 2 verbatim from dossier.
