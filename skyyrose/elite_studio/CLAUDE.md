# skyyrose/elite_studio/

Canonical imagery hub. Meshy / TRELLIS / Tripo / FASHN are engines behind this. The `pipeline3d/`
subpackage is the provider-agnostic staged 3D pipeline (image-to-3D → texture → remesh → export-GLB).

## Hard rules (do not regress — these were review findings)

- **Money gate is FAIL-CLOSED.** `cli._confirm()` ALWAYS prints the cost banner first, then: `SKYYROSE_AUTO_CONFIRM=1` is the ONLY non-interactive opt-in; a missing TTY (CI/cron/subprocess/pytest) **ABORTS** (returns False); an interactive TTY prompts for `y`. Auto-approving paid dispatch on a missing TTY was a CRITICAL finding (fixed 2026-06-02). Paid APIs require explicit `y` or the explicit env opt-in — NEVER a silent no-TTY pass. The CLI also aborts up front if `estimate.total_usd > --budget` (strict `>`).
- **Estimate prices CAPABILITY, dispatch checks AVAILABILITY.** `router.supporting(stage)` (ignores availability) drives the cost estimate, so a dry-run shows real cost with no API key loaded. `router.candidates(stage)` (availability-gated) drives actual dispatch + fallback. `--go` with no key raises `NoAdapterError` at `pick()`, never silently pays.
- **Tripo mesh selection never trusts dict order.** `adapters.tripo._pick_mesh()` returns the `model` key, else the first value with a mesh extension (`.glb/.gltf/.obj/.fbx/.usdz/.stl`), else None → `run_stage` raises. Prevents copying a texture PNG to `<sku>.glb`. Do NOT revert to `next(iter(downloaded.values()))`.

## Conventions

- **Remesh-to-GLB uses `smart_lowpoly`, NOT `convert_model`** — the tripo3d SDK's `convert_model` format Literal excludes GLB (GLB is the native output). `convert_model` is reserved for deferred USDZ/FBX export.
- **Chaining:** `Artifact` carries both a provider `task_id` (same-provider chaining) and a local `path`/`model_url` (cross-provider handoff). `router.pick(stage, exclude=...)` enables fallback.
- **Idempotency:** `StageStore` (file-based) persists each stage result keyed by `(input_hash, stage)`; a resumed job skips completed stages (a crash at remesh does not re-bill image-to-3D + texture). The hash folds `job.params` (`telemetry.hash_inputs`), so changing `target_polycount` invalidates the cache (correctness over re-bill avoidance). SKU is format-validated `^[a-z]{2,4}-\d{3}$` in `preflight.resolve_source` before any glob/output use.
- **Execution spine is synchronous-within-stage** — adapters block via the SDK `wait_for_task`. No event-driven DAG; job concurrency is a Phase-3 worker concern.
- Reuses (does NOT duplicate): `budget.py` (RunBudget), `telemetry.py` (stage span + hash_inputs), the `tripo3d` SDK via a thin adapter. Does NOT use `ai_3d/generation_pipeline.py` (superseded — monolithic, no budget/telemetry).

## Entry

`python -m skyyrose.elite_studio.pipeline3d --sku <sku> --stages ... [--go]` — dry-run by default; `--go` dispatches paid work (subject to the money gate above).
