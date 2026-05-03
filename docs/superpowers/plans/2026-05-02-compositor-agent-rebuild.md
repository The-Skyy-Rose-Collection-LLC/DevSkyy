# CompositorAgent Rebuild Implementation Plan

> **Status:** STUB — needs full grilling before execution. Reserved as the prerequisite for `2026-05-01-embedding-quality-gates.md` Task 4 (deferred) and for un-blocking the LangGraph creative pipeline.
>
> **For agentic workers:** DO NOT execute this plan as written. Tasks are TBD pending design. Coordinate with the human owner before drafting tasks.

**Goal:** Rebuild `skyyrose/elite_studio/agents/compositor_agent.py` from its current 68-line `pass_through` shell back into a working six-stage compositor that fulfils the contract LangGraph's `compositor_node` already expects (`agent.composite(sku, image_path, scene_name, collection)`). Retire the parallel procedural script `scripts/run_compositor_pipeline.py` once the rebuild reaches parity.

**Architecture:** Per ADR-0001, the compositor is an agent inside a LangGraph node. Stages are private methods on the agent class, not module-level functions in a script. ADK observability ("Back Data") flows through `BaseSuperAgent`. `compositor_node` (the LangGraph wrapper) stays as-is — it's already correctly designed.

**Why this exists:** Commit `f25fd25d3` ("Phase B1 scorched earth — rebuild pending") gutted the agent on 2026-04-21. Today the LangGraph `compositor_node` calls `agent.composite()` and gets a `pass_through` no-op back. Compositing functionality lives in `scripts/run_compositor_pipeline.py` (697L) outside the graph. Two pipelines, only one wired into the rest of the creative flow.

---

## Inputs to bring forward

- `scripts/run_compositor_pipeline.py` (697L) — already-working stage logic to extract into agent methods
  - `remove_background()` → `_extract_alpha()`
  - `opus_prompt_for_product()` → `_opus_prompt()`
  - `composite_product_into_scene()` → `_relight()`, `_composite()`, `_shadows()`
  - Currently no Gemini QA stage in the script — was retained in the original agent design (`_visual_qa()`)
- `skyyrose/elite_studio/tests/test_compositor_agent.py` (544L, currently stale) — the de-facto spec for the rebuild's API surface; class structure (`TestAlphaExtraction`, `TestOpusPromptEngineering`, `TestICLightRelighting`, `TestFLUXCompositing`, `TestShadowGeneration`, `TestVisualQA`, `TestFullPipeline`, `TestCheckpointResume`, `TestAuditLog`) maps 1:1 to the methods we need to restore
- `skyyrose/elite_studio/synthesis/flux_pipeline.py` (374L), `synthesis/stages/{audit_filter,mask_deriver,decoration_inpaint}.py` — supporting helpers already structured per-stage
- `skyyrose/elite_studio/graph/nodes.py:318` — the canonical contract (`agent.composite(sku, image_path, scene_name, collection) -> CompositorResult`); rebuild MUST satisfy this signature unchanged
- `skyyrose/elite_studio/coordinator.py` (325L) and `master_registry.py` (288L) — observability and registration surfaces the rebuilt agent should plug into
- Embedding gate library from `2026-05-01-embedding-quality-gates.md` Tasks 1-3 (once landed) — drop-in `_embedding_gate()` call between Stages 5 and 6

## Open questions for grilling

1. **Stage 6 (Gemini visual QA) — keep or replace?** The original design calls Gemini for every render. The embedding gate (Task 4 of the deferred work) was meant to *precede* Gemini and skip it on rejected renders. Given CLIP alignment scoring (Task 7 of the embedding plan) gives a similar signal cheaper, do we still need Gemini QA? Decision affects whether Stage 6 = Gemini, Stage 6 = embedding gate (replacing Gemini entirely), or Stage 6 = embedding gate → Gemini (current design).
2. **Async vs sync `composite()`?** `nodes.py:346` has the comment `# composite() is sync since the Phase B2 rewrite — no [...]`. Sync simplifies the LangGraph integration. Async would let stages run concurrently for batches. Default: keep sync.
3. **Procedural script retirement timing.** Hard cutover (delete in the same PR as rebuild) vs deprecation window (mark deprecated, schedule removal in N weeks). Default: deprecation window, because external runbooks may reference the script.
4. **Test file salvage strategy.** The 544-line test file mocks every external dep (rembg, Anthropic, fal_client, httpx, Gemini REST, PIL, libcom). Re-pointing it at the rebuilt agent should be possible with minimal fixture changes — but the rebuild may diverge in stage signatures. Default: rebuild the agent first, *then* fix the test file to match, accepting that some test method renames are inevitable.
5. **Where do retries live?** `BaseSuperAgent` has retry primitives. The script has its own `retry_call()` helper at line 75. Default: use `BaseSuperAgent`'s retry surface, drop the script's helper.
6. **Audit log format.** The script writes `STAGE_DELAY = 2` and presumably an audit JSON. The agent should produce structured per-stage telemetry that flows through ADK Back Data. Need to align format so existing dashboards keep working.

## Tasks

TBD — grill before drafting.
