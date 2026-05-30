# 3D Ghost-Mannequin Pipeline — Handoff (2026-05-29)

**Goal:** render all 33 products in 3D ghost-mannequin format, integrated into their collections.
**Decision (locked):** Path A — Full Elite ghost-mannequin (FLUX base render + Meshy 3D + composite). User accepts FLUX is generative (not pixel-identical).

## What WORKS (verified this session)
- **SKU discovery** → canonical catalog (was empty overrides dir). `discover_all_skus()`.
- **3D mesh generation SUCCEEDS** — br-006 produced `renders/3d/br-006-sherpa-jacket_meshy.glb` (8.3M) + `renders/3d/br-006_clean.glb` (7.4M, Blender-cleaned). Meshy + Blender-clean path is functional on this Mac (`/opt/homebrew/bin/blender`).
- **Preflight** clears (now verifies vs `garment_type_lock`, not `product.name`).
- **Dossier reference integrity: 33/33 green.** All logo/patch/techflat refs resolve.

## What BLOCKS the goal (gap #6 — OPEN, ROOT CAUSE FOUND)
- **FLUX ghost-mannequin synthesis fails the VisionAudit fidelity gate** → quarantined
  after 3 retry-with-feedback attempts.
- **The QC gate is correct, NOT over-strict.** `renders/quarantine/br-006/20260530T051449/manifest.json`
  records `"matches_dossier": false` with real violations:
  - HIGH: "Missing buttoned storm-flap; zipper is exposed and not covered by a satin
    overlap" (region `front-placket-storm-flap`). br-006's dossier explicitly specifies
    a button storm-flap covering the zipper — FLUX won't render it.
  - MEDIUM: "Zipper hardware silver/metallic instead of black".
- **This is the generative-vs-faithful tension, concrete.** FLUX (`fal-ai/flux-pro/kontext`
  stage1 + `fal-ai/flux-pro/v1/fill` stage3, audit `gemini-3-flash-preview`) keeps
  reinterpreting the placket; the gate refuses unfaithful renders. Not a 5-line fix.
- **Options next session (decide with founder):**
  1. Prompt-tune the FLUX synthesis to emphasize the storm-flap placket / black hardware
     (may or may not be within FLUX's capability for this detail).
  2. Loosen the audit severity policy (accept MEDIUM violations) — lowers fidelity bar.
  3. Reconsider path: the **Meshy 3D mesh PASSED** (it textures from the real photo) and is
     more faithful than FLUX synthesis for detailed garments. The "Meshy 3D, real-photo
     texture" path (offered + declined) may actually clear QC where FLUX can't.

## Budget ceiling — CORRECTED 2026-05-29 (earlier "budget OFF" was WRONG)
- **A coarse ceiling IS active.** `create_initial_state` (`graph/state.py:154`) sets
  `budget=_default_budget()` → `RunBudget(ceiling_usd=25.0)` (env `ELITE_STUDIO_BUDGET_USD`).
  Each `run_single` (per SKU) gets a FRESH $25-capped budget; `generator_node`
  (`layer1.py:127-159`) + `three_d_node` pre-check (`ensure_within_budget`) and `spend`
  against it. So a per-SKU stage cannot blow past $25 — **the batch is NOT uncapped.**
- **What's actually missing (polish, NOT a blocker):**
  (a) Fine-grained: `generator_node` calls `agent.generate(...)` (`layer1.py:142`) WITHOUT
      passing `budget`, so FLUX's 3 internal retries aren't individually capped (the
      `render_base called without a RunBudget` warning). Thread `budget` →
      `GeneratorAgent.generate(budget=)` → `flux_pipeline.render(budget=)` (already supports it).
  (b) No shared BATCH-TOTAL ceiling — each SKU resets to $25, so 28 SKUs ≈ up to 28×$25
      worst case (real ≈ $1-2/SKU). For a hard batch cap, build one RunBudget in
      `cli.py cmd_batch`/`run_batch` and reuse it across SKUs instead of per-SKU defaults.
- **Exact fix — fully scoped 2026-05-29 (~15 min, but touches core state type → do with full context + mypy):**
  1. `graph/state.py`: `EliteStudioState` TypedDict — add field `budget: RunBudget | None`
     (import `from ..budget import RunBudget`). `create_initial_state` (`state.py:103`) — add
     param `budget: RunBudget | None = None` and set `"budget": budget` in the returned dict.
  2. `graph/runner.py:28 run_single` — construct `RunBudget(ceiling_usd=<per-SKU, e.g. 2.50>)`
     and pass `budget=` into the `create_initial_state(...)` call at line 52. Same in `run_batch`
     (runner.py:66) per-SKU.
  3. That's it for coarse enforcement: `generator_node` (`layer1.py:127-159`) and `three_d_node`
     already read `state.get("budget")` and call `ensure_within_budget`/`spend` when non-None.
  4. (Optional, finer) pass `budget` through `GeneratorAgent.generate(..., budget=)` →
     `flux_pipeline.render(budget=)` so the 3 internal FLUX retries are individually capped.
  - Costs for ceiling math: `_FLUX_KONTEXT_EST_COST_USD` (flux_pipeline), `_THREE_D_EST_COST_USD=0.50`.
  - `RunBudget(ceiling_usd: float)` dataclass: `.ensure_within_budget(cost, stage)`, `.spend(cost, stage)`, `.remaining`.
  - VERIFY after: `.venv/bin/python -c "from skyyrose.elite_studio.graph.runner import run_single"` + mypy.

## Spend so far
- br-006: ~1 Meshy gen (~$0.50) + 3 fal FLUX attempts (~$0.10–0.40) = **~$0.60–0.90**. First and only spend of the session. All earlier attempts (gaps 1–5) failed safe at $0.

## Fixes committed
- `c07045b0e` — discover_all_skus→catalog; Tripo key scrub (ROTATE IT); 5 dossier pointer fixes; heart-rose-composite.md (founder-confirmed: rose above broken heart); love-hurts-logo.md note.
- `6da72d2ce` — preflight verifies vs garment_type_lock.
- **Uncommitted env changes:** `pip install trimesh fal-client` into `.venv` (both UNDECLARED in requirements — add to requirements-full.txt / pyproject extras).

## Non-fatal warnings (ignore / optional)
- `pyrender not available` — Blender subprocess path used instead (works). 
- `google-adk not installed` — ADK telemetry only, wrapped in try/except.
- `Langfuse no public_key` — observability disabled, non-fatal.

## Next session, in order
1. Diagnose gap #6: why does br-006 FLUX ghost-mannequin render fail QC? (compare vs golden, check fidelity thresholds). Tune synthesis prompt or QC gate.
2. Wire RunBudget ceiling into the FAL render path (cost safety).
3. Re-run br-006 → confirm a ghost-mannequin render PASSES QC end-to-end.
4. THEN batch the 28 with budget ceiling + `--remaining` (skip-existing).
5. Display half (UNSTARTED): host GLBs + set `_product_3d_model` post-meta per product (WooCommerce production writes — separate STOP-AND-SHOW). "Rendered" ≠ "in collection" until this.

## Two open dossier items (flagged, non-blocking)
- br-004 left-sleeve patch: PARKED pending Corey read-back (dossier correctly omits, won't guess).
- heart-rose-composite roses: resolved 2026-05-29 — founder confirmed rose IS present; `heart-rose-composite.md` updated.
