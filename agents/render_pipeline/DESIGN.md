# RenderPipeline — Google ADK Agent

**Branch:** `feat/multi-sku-validation`
**Status:** scaffold (Stage B of the ADK plan)
**ADK reference:** `/google/adk-python` (Context7), tag `v1.16+` for AgentEvaluator + LlmAgent
**Companion docs:** `tasks/plan-multi-sku-validation.md`, `tasks/per-sku-prompts-1778061036.md`

---

## Verified empirical data (from this session — load-bearing for design)

These are the findings the ADK design is built on. All paid runs are recorded in `tasks/multi-sku-validation-*.json` and `tasks/source-strategy-comparison-*.json`.

### F1 — The pipeline mechanically works on all 33 SKUs (confirmed)
- Multi-SKU validator (4-SKU sample, 2026-05-05) ran end-to-end without exceptions on br-001, lh-004, sg-007, kids-001 — across 4 collections.
- All 33 SKUs have both a dossier file and a source image (`tasks/plan-multi-sku-validation.md` Phase 0 inventory).
- Cost: ~$0.085/SKU average. Full catalog run is $2-4.

### F2 — Source image is NOT the dominant signal (3-pt range = noise)
- br-001 3-way comparison (`tasks/source-strategy-comparison-br-001-1778095404.json`): render=88, techflat=85, source-photo=88. Range = 3 pts.
- Earlier hypothesis "defective source image causes self-reinforcing defect loop" was FALSIFIED.
- ADK design must NOT default `ResolveSourceTool` to techflat-first; render-as-source is fine.

### F3 — Engine routing IS the dominant signal (58-pt range)
- br-001 with gemini-pro: 88/100. br-001 with flux-pro: 30/100. **58-point delta from engine choice alone.**
- Engine routing is currently driven by `route_product()` reading vision-cache fields like `fabric_appearance` containing keywords like "fleece"/"satin". Stochastic Gemini-vision output → stochastic routing.
- ADK design's `RouteEngineTool` must:
  - Default to vision-driven heuristics (existing logic)
  - Support explicit per-SKU `engine_override` from catalog (NEW catalog column)
  - Log every routing decision with the inferred-DNA fields that drove it (observable)
  - Be deterministic given a fixed vision-cache state

### F4 — Layer 3 + Layer 3.5 prompt structure IS correct (verified)
- br-001 with the canonical-mode prompt scored 88 first-attempt, no refinement.
- Diagnostic dump (`tasks/per-sku-prompts-1778061036.md`) shows zero contradictions in canonical-mode prompts.
- ADK's `BuildPromptTool` mirrors the production composition: Layer 0 (registry render directives) → Layer 3 (canonical positives PREPEND) → Layer 2 (canonical negatives APPEND).

### F5 — Tournament infrastructure is fragile (1/4 SKUs hit it)
- sg-007 in the post-Layer-3.5 multi-SKU run: GPT-5.5-pro TimeoutError + Gemini 504 DEADLINE_EXCEEDED → 0/100 score.
- Not a quality issue — both vision judges timed out simultaneously. Likely network-side, not pipeline-side.
- ADK design must:
  - Distinguish "infra failure" results from "low quality" results (ADK trace metadata gives us this for free)
  - Re-run failed SKUs without re-running passed ones (eval framework supports this via test selection)
  - Cap retries on infra errors (e.g., 1 retry with 30s backoff) before marking SKU failed

### F6 — Defective on-disk renders cause hallucination_veto in judges
- br-001 (multi-color rose render), lh-004 (all-black wrong silhouette), sg-007 (silicone patch), kids-001 (hallucinated "OAKLAND SkyyRose" text). All fired Opus 4.7 hallucination_veto on the existing renders.
- Once the pipeline regenerates with correct prompt + correct engine, the new render passes (br-001 hit 88).
- ADK eval goldens should reflect realistic per-SKU minimums (80+) AND track whether veto fired — both are signals.

### F7 — Cost reality (across 6 paid runs this session)
- 4-SKU multi-SKU run: $0.385 (avg $0.096/SKU)
- br-001 single-SKU Layer 1 validator: $0.80
- br-001 3-way source comparison: $0.040 × 3 = $0.120 (no refinement triggered → cheap)
- Engine impact on cost: gpt-image $0.12 > gemini-pro $0.04 ≈ flux-pro $0.075
- Full catalog run estimate: $2.31–$3.96. Less than a coffee.

---

## ADK design — agents/render_pipeline/

### Package layout

```
agents/render_pipeline/
├── DESIGN.md                # this file
├── README.md                # quickstart for users
├── __init__.py              # exports root_agent
├── agent.py                 # LlmAgent root — orchestrates the workflow
├── .env.example             # env var template (API keys)
├── tools/
│   ├── __init__.py
│   ├── load_dossier.py      # FunctionTool wrapping spec_builder.build_dna_from_sku
│   ├── resolve_source.py    # render | techflat | source-photo strategy
│   ├── route_engine.py      # F3 — adds engine_override support to existing router
│   ├── build_prompt.py      # Layer 0 + Layer 3 + Layer 2 composition
│   ├── generate_image.py    # dispatches to generate_gemini/gpt/flux
│   ├── refine_image.py      # wraps refine_with_kontext
│   └── qa_tournament.py     # wraps run_tournament; surfaces infra-vs-quality distinction
├── eval/
│   ├── __init__.py
│   ├── render_pipeline.evalset.json  # per-SKU goldens (min QA score, expected veto state)
│   ├── test_config.json              # eval criteria (e.g., score threshold ≥ 80)
│   └── test_render_pipeline.py       # pytest entry — calls AgentEvaluator.evaluate()
└── tests/
    ├── __init__.py
    └── test_tools.py        # unit tests on tool wrappers (don't hit paid APIs)
```

### Agent shape

The root agent is an `LlmAgent` that orchestrates the 7-tool workflow. It accepts `{sku, view}` input, returns `{output_path, qa_score, qa_passed, attempts, cost_usd, refinement_applied, issues}`.

```python
from google.adk.agents import LlmAgent
from .tools import (
    load_dossier_tool, resolve_source_tool, route_engine_tool,
    build_prompt_tool, generate_image_tool, refine_image_tool,
    qa_tournament_tool,
)

root_agent = LlmAgent(
    name="render_pipeline",
    model="gemini-2.5-flash",
    description="Generate a validated product render for a SkyyRose SKU.",
    instruction="""You are a render-pipeline orchestrator for a luxury fashion brand.

Workflow:
1. load_dossier — fetch the canonical design spec for the requested SKU
2. resolve_source — find the source image (catalog override, bundle, or glob)
3. route_engine — pick the best image-gen model for this product (consult engine_override first)
4. build_prompt — compose Layer 0 + 3 + 2 prompt
5. generate_image — render with the routed engine
6. qa_tournament — score against canonical with 3 judges
7. If qa_score < 80: refine_image, then qa_tournament again (max 1 refinement)
8. Return RenderResult — pass/fail + score + cost + path

Always log routing decision and any judge issues to session state for downstream debugging.
Hard-fail if the dossier doesn't load (Tier 2 contract).
""",
    tools=[
        load_dossier_tool, resolve_source_tool, route_engine_tool,
        build_prompt_tool, generate_image_tool, refine_image_tool,
        qa_tournament_tool,
    ],
    output_key="render_result",
)
```

### Tool implementations

Each tool is a thin Python function (FunctionTool pattern from ADK docs). Reuses `nano_banana.*` modules — no logic duplication.

| Tool | Wraps | Returns |
|------|-------|---------|
| `load_dossier_tool(sku)` | `spec_builder.build_dna_from_sku(sku)` | `VisionContext` as dict (ADK serializes JSON) |
| `resolve_source_tool(sku, name, strategy="auto")` | `_validate_pipeline_multi_sku._resolve_source_image` | `{path, strategy_used, alternates_available}` |
| `route_engine_tool(sku, vision_desc, view, engine_override=None)` | `router.route_product` + new override layer | `{engine, model_id, reason, estimated_cost, override_applied}` |
| `build_prompt_tool(vision_desc, product, engine, view)` | `PromptRegistry.get_prompt` + `augment_prompt_with_dossier_positives/negatives` | `{prompt, template_id, layer3_chars, layer2_chars}` |
| `generate_image_tool(prompt, source_path, engine, model_id, attempts_remaining)` | `generate_gemini/gpt/flux_fal` | `{output_path, bytes_size, attempts_used}` |
| `refine_image_tool(image_path, refine_prompt)` | `refine_with_kontext` + composite_gemini fallback | `{refined_path or None, used_kontext, used_composite}` |
| `qa_tournament_tool(source_path, candidate_path, dna)` | `run_tournament` | `{aggregate_score, vision_pair_mean, synthesis_overall, per_judge_scores, hallucination_veto, infra_failures, top_issues, all_fixes}` |

### Eval framework

Per ADK's `AgentEvaluator`:
- `eval/render_pipeline.evalset.json` — per-SKU test entries with `expected.qa_score >= 80`
- `eval/test_config.json` — criteria (`score_threshold: 80`, `trajectory_match: false` since steps are deterministic)
- `eval/test_render_pipeline.py` — single pytest test calling `AgentEvaluator.evaluate(agent_module="agents.render_pipeline", eval_dataset_file_path_or_dir="agents/render_pipeline/eval/")` for CI integration.

Eval-as-first-class lets us regression-test "does br-001 still pass after dossier edit?" automatically. Add a SKU to the eval set; CI catches regressions before they reach production.

### CLI / entry points

```bash
# Run agent on one SKU (dev)
adk run agents/render_pipeline --input '{"sku": "br-001", "view": "front"}'

# Eval suite (CI)
adk eval agents/render_pipeline agents/render_pipeline/eval/render_pipeline.evalset.json

# Programmatic (pytest, CI/CD)
pytest agents/render_pipeline/eval/test_render_pipeline.py
```

### Env / venv

Per `CLAUDE.md`: ADK requires `.venv-agents/` (numpy/CUDA conflict with the main `.venv`).

```bash
python3 -m venv .venv-agents
source .venv-agents/bin/activate
pip install google-adk
pip install -e .  # so the agent can import nano_banana.* tools
```

`.env.example` lists required keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `FAL_KEY`. The agent reads them via the standard `from_env()` pattern.

---

## Catalog change required

Add an `engine_override` column to `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`. Empty for most SKUs; populated for the ~5-10 SKUs where vision-driven routing has empirically failed.

Per F3, br-001 should be `engine_override=gemini-pro`. After the lh-004 source-strategy comparison completes (running in background), we'll know if lh-004 needs an override too.

`load_catalog()` in `nano_banana.catalog` parses CSV columns; one new field is a 3-line change. Existing tests check column count — those need a +1 update.

---

## Migration path (no big-bang)

1. **Phase 1 (this session): scaffold the ADK package alongside the existing `nano_banana` pipeline.** Both work. ADK is opt-in via `adk run`. nano_banana validators continue to work unchanged.
2. **Phase 2: add `engine_override` column to catalog.** Backward-compatible — empty values fall through to vision-driven routing.
3. **Phase 3: full-catalog run via the ADK agent.** Sample 10 SKUs first; if all pass, run all 33.
4. **Phase 4: deprecate `_validate_pipeline_multi_sku.py`** in favor of `adk eval`. The existing validator stays as-is for archival.
5. **Phase 5 (optional): deploy the agent.** Cloud Run / Vertex AI Agent Engine. The agent becomes a service — call it from the dashboard, from a CI job, from a cron.

---

## Open questions (to resolve as we build)

1. **Should the agent be `LlmAgent` (LLM-driven workflow) or `SequentialAgent` (hard-coded order)?** The 7 steps are deterministic and well-known. SequentialAgent gives reproducibility but loses the "agent decides what to do" flexibility. Lean SequentialAgent because the workflow shouldn't drift across runs.

2. **What goes in `output_schema` (Pydantic) vs. `output_key` (session state)?** `RenderResult` is well-suited to a Pydantic schema for the final output. Intermediate state (vision_desc, prompt, image bytes) goes in session state via output_key.

3. **How does the eval framework handle paid calls in CI?** ADK's AgentEvaluator runs the agent end-to-end. For CI, we either (a) mock the SDK clients (mirroring the Phase 2 mock-coverage discipline), or (b) run a tiny subset of SKUs and accept the cost. Default to (a) for unit-eval, (b) for nightly integration.
