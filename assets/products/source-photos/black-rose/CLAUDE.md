# skyyrose/elite_studio/

## pipeline3d — Unified 3D Pipeline Orchestrator

- `skyyrose/elite_studio/pipeline3d/` is the provider-agnostic staged 3D pipeline (Tripo/Meshy workflow clone). Stages: image-to-3D → texture → remesh → export-GLB. Phase 1 = Tripo vertical slice driven by the CLI; Phases 2 (Meshy/TRELLIS adapters + router fallback + batch) and 3 (REST + webhook + Redis worker) are roadmapped in the spec.
- **Execution spine is synchronous-within-stage** — the adapter blocks via the `tripo3d` SDK `wait_for_task`. No event-driven DAG advancement. Job concurrency is a worker-layer concern (Phase 3).
- **Chaining rule:** `Artifact` carries both a provider `task_id` (same-provider chaining) and a local `path`/`model_url` (cross-provider handoff). `router.pick(stage, exclude=...)` enables fallback.
- **Remesh-to-GLB uses `smart_lowpoly`, NOT `convert_model`** — the tripo3d SDK's `convert_model` format Literal excludes GLB (GLB is the native output). `convert_model` is reserved for deferred USDZ/FBX export.
- **Estimate prices CAPABILITY, dispatch checks AVAILABILITY.** `router.supporting(stage)` (ignores availability) drives the cost estimate so a dry-run shows real cost with no API key loaded; `router.candidates(stage)` (availability-gated) drives actual dispatch + fallback. Cost gate stays correct: `--go` with no key raises `NoAdapterError` at `pick()`, never silently pays.
- **Cost gate:** whole-job estimate computed once (`estimator.estimate`), shown via STOP-AND-SHOW before dispatch. Reuses `RunBudget.ensure_within_budget`/`spend`. Paid dispatch requires `--go`; never auto-dispatches.
- **Idempotency:** `StageStore` (file-based) persists each stage result keyed by `(input_hash, stage)`; a resumed job skips completed stages so a crash at remesh does not re-bill image-to-3D + texture.
- Entry: `python -m skyyrose.elite_studio.pipeline3d --sku <sku> --stages ... [--go]`. Dry-run by default.
- Reuses (does not duplicate): `budget.py` (RunBudget), `telemetry.py` (stage span + hash_inputs), and the `tripo3d` SDK via a thin adapter. Does NOT use `ai_3d/generation_pipeline.py` (superseded — monolithic, no budget/telemetry).

<claude-mem-context>

</claude-mem-context>