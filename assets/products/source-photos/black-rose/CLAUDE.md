# skyyrose/elite_studio/

## pipeline3d — Unified 3D Pipeline Orchestrator

- `skyyrose/elite_studio/pipeline3d/` is the provider-agnostic staged 3D pipeline (Tripo/Meshy workflow clone). Stages: image-to-3D → texture → remesh → export-GLB. Phase 1 = Tripo vertical slice driven by the CLI; Phases 2 (Meshy/TRELLIS adapters + router fallback + batch) and 3 (REST + webhook + Redis worker) are roadmapped in the spec.
- **Execution spine is synchronous-within-stage** — the adapter blocks via the `tripo3d` SDK `wait_for_task`. No event-driven DAG advancement. Job concurrency is a worker-layer concern (Phase 3).
- **Chaining rule:** `Artifact` carries both a provider `task_id` (same-provider chaining) and a local `path`/`model_url` (cross-provider handoff). `router.pick(stage, exclude=...)` enables fallback.
- **Remesh-to-GLB uses `smart_lowpoly`, NOT `convert_model`** — the tripo3d SDK's `convert_model` format Literal excludes GLB (GLB is the native output). `convert_model` is reserved for deferred USDZ/FBX export.
- **Estimate prices CAPABILITY, dispatch checks AVAILABILITY.** `router.supporting(stage)` (ignores availability) drives the cost estimate so a dry-run shows real cost with no API key loaded; `router.candidates(stage)` (availability-gated) drives actual dispatch + fallback. Cost gate stays correct: `--go` with no key raises `NoAdapterError` at `pick()`, never silently pays.
- **Cost gate:** whole-job estimate computed once (`estimator.estimate`), shown via STOP-AND-SHOW before dispatch. Reuses `RunBudget.ensure_within_budget`/`spend`. Paid dispatch requires `--go`; never auto-dispatches.
- **Money gate is FAIL-CLOSED (do not regress).** `cli._confirm()` ALWAYS prints the banner first, then: `SKYYROSE_AUTO_CONFIRM=1` is the only non-interactive opt-in; a missing TTY (CI/cron/subprocess/pytest) ABORTS (returns False); an interactive TTY prompts for `y`. Auto-approving paid dispatch on a missing TTY was a CRITICAL review finding (fixed 2026-06-02) — paid APIs require explicit `y` or the explicit env opt-in, NEVER a silent no-TTY pass. The CLI also aborts up front if `estimate.total_usd > --budget` (strict `>`, matching `RunBudget.ensure_within_budget`) so earlier stages can't bill before a later stage trips the ceiling.
- **Tripo mesh selection never trusts dict order.** `adapters.tripo._pick_mesh()` returns the `model` key, else the first value with a mesh extension (`.glb/.gltf/.obj/.fbx/.usdz/.stl`), else None → `run_stage` raises. Prevents copying a texture PNG to `<sku>.glb`. Don't revert to `next(iter(downloaded.values()))`.
- **Idempotency hash folds `job.params`** (`executor.run_job` → `telemetry.hash_inputs(source, sku, json.dumps(params, sort_keys=True))`). A re-run with a new `target_polycount` invalidates the cache (correctness over re-bill avoidance). SKU is format-validated (`^[a-z]{2,4}-\d{3}$`) in `preflight.resolve_source` before any glob/output use.
- **Idempotency:** `StageStore` (file-based) persists each stage result keyed by `(input_hash, stage)`; a resumed job skips completed stages so a crash at remesh does not re-bill image-to-3D + texture.
- Entry: `python -m skyyrose.elite_studio.pipeline3d --sku <sku> --stages ... [--go]`. Dry-run by default.
- Reuses (does not duplicate): `budget.py` (RunBudget), `telemetry.py` (stage span + hash_inputs), and the `tripo3d` SDK via a thin adapter. Does NOT use `ai_3d/generation_pipeline.py` (superseded — monolithic, no budget/telemetry).

<claude-mem-context>

</claude-mem-context>