---
title: Mockup-First Stage D Landing + IC-Light Cost Gate
date: 2026-05-27
status: approved
author: corey + claude (brainstorming session)
supersedes: tasks/mockup-first-100pct-replica-system-plan.md (never committed; reconstructed inline below)
authority: This document is the binding spec for the two follow-ups it covers. Implementation plan to be authored separately by writing-plans skill.
---

# Mockup-First Stage D Landing + IC-Light Cost Gate

## 1. Goal and non-goals

**Goal.** Close two production follow-ups in one coordinated change:

1. Land the deterministic `stage_d_rasterize.py` (currently isolated in the `elite-studio-mockup` git worktree) onto `main`, behind a feature flag whose default preserves today's FLUX behavior.
2. Close the IC-Light cost-enforcement gap. Today, `stage_c_relight.py` calls Replicate without any `budget` check; the `eval/cost-cap-policy.md` policy does not enumerate Replicate IC-Light v2. Add it to the policy, surface the cost as a constant, and thread the existing `infra._gate_budget()` helper through Stage C so the gate fires per call.

**Non-goals.**

- Retiring `stage_d_flux.py`. The FLUX path stays on `main` as the default until the rasterize path is verified on the SKU set.
- Re-ordering the seven-stage chain.
- Building the SKU mockup-registration system. The deterministic Stage D assumes a per-SKU mockup file exists on disk; if one is missing, the orchestrator falls back to the FLUX path automatically.
- Adding a batch pre-flight cost estimator. Per-call gating is in scope; explicit batch manifests are deferred (the per-call gate + `RunBudget` headroom check naturally surfaces batches over the policy threshold).

---

## 2. Architecture intent (reconstructed from memory)

The original `tasks/mockup-first-100pct-replica-system-plan.md` was never committed to git and is no longer on disk (memory observations #8800, #8801). The relevant architectural claims it carried are reconstructed here from memory observations #8796 and #8797 and from the worktree code itself.

**The mockup-first principle.** A hand-crafted, pixel-exact mockup is registered per SKU. The mockup carries the product's embroidery, prints, seam stitching, and color fidelity intact. The compositor pipeline never generates the product surface; instead, it places the verified mockup onto a scene via deterministic PIL operations, then relights, cleans up, and adds shadows around the placed mockup. This guarantees 100% replica fidelity for any SKU with a registered mockup.

**Stage chain (mockup-first mode).** The chain itself does not change. Only Stage D's behavior changes.

| Stage | Module | Purpose |
|-------|--------|---------|
| A | `stage_a_matte.py` | BRIA RMBG — extract subject silhouette from source photo for downstream mask alignment. |
| B | `stage_b_prompt.py` | Claude Opus — synthesize the scene + lighting prompt that conditions Stage C and (in `kontext` mode) Stage D. |
| C | `stage_c_relight.py` | IC-Light v2 — Replicate primary, libcom local fallback, alpha pass-through final fallback. |
| D | `stage_d_flux.py` (existing) **or** `stage_d_rasterize.py` (new) | FLUX inpainting **or** deterministic PIL alpha-composite. Selected by `ELITE_STUDIO_STAGE_D_MODE`. |
| E | `stage_e_cleanup.py` | GIMP pixel cleanup via `cli-anything-gimp`. |
| F | `stage_f_shadows.py` | PIL contact shadow. |
| G | `stage_g_visual_qa.py` | Embedding pre-gate + Gemini visual QA. |

**Why deterministic at D.** A generative model at the product-surface stage is the dominant source of fidelity drift — wrong embroidery placement, mangled prints, fabricated seam lines. The mockup is already correct; rasterizing it is a one-way street that cannot regress those details.

---

## 3. Stage D landing plan

### 3.1 File moves

Source: `.claude/worktrees/elite-studio-mockup/skyyrose/elite_studio/agents/compositor/stage_d_rasterize.py`
Source: `.claude/worktrees/elite-studio-mockup/skyyrose/elite_studio/tests/test_stage_d_rasterize.py`

Cherry-pick both into `main` at the same paths.

### 3.2 Docstring cleanup

Strip the dead link from `stage_d_rasterize.py:16` (`tasks/mockup-first-100pct-replica-system-plan.md`). Replace with a reference to this design doc.

### 3.3 Feature flag

Add to `skyyrose/elite_studio/config.py`:

```python
# Stage D selector — `kontext` (default, FLUX inpainting) or `rasterize` (deterministic PIL).
ELITE_STUDIO_STAGE_D_MODE = os.getenv("ELITE_STUDIO_STAGE_D_MODE", "kontext")
```

### 3.4 Orchestrator branch

In `skyyrose/elite_studio/agents/compositor/orchestrator.py` at the Stage D call site (currently near line 221, calling `stage_d_flux` with `budget=budget`):

```python
mode = ELITE_STUDIO_STAGE_D_MODE
mockup_path = self._lookup_mockup_path(sku)
aligned_mask_path = stages["matte"].get("aligned_mask_path")

if mode == "rasterize" and mockup_path and aligned_mask_path:
    composite_path = stage_d_rasterize.rasterize_composite(
        mockup_path=mockup_path,
        scene_image_path=scene_path,
        aligned_mask_path=aligned_mask_path,
        sku=sku,
        output_dir=output_dir,
    )
    stages["composite"] = {"path": composite_path, "mode": "rasterize"}
else:
    composite_path = stage_d_flux.inpaint_subject(
        ...,
        budget=budget,
    )
    stages["composite"] = {"path": composite_path, "mode": "kontext"}
    if mode == "rasterize":
        stages["composite"]["fallback_reason"] = (
            "missing_mockup" if not mockup_path else "missing_aligned_mask"
        )
```

The `_lookup_mockup_path(sku)` helper is new — it resolves `mockup_path` from a per-SKU lookup (existing mockup-registration source) or returns `None`. Initial implementation: read `data/mockups/{sku}.png` if present, else `None`. Future enhancement is out of scope.

### 3.5 Audit entry

The new `stages["composite"]["mode"]` field is written to the audit JSON. The audit writer in `agents/compositor/audit.py` is unchanged — it serializes the `stages` dict verbatim.

### 3.6 Module docstring

Update `orchestrator.py` lines 8–17 to document both Stage D paths:

```
  stage_d_flux.py      — FLUX inpainting (fal-fill → kontext → replicate) + budget gates
  stage_d_rasterize.py — Deterministic PIL alpha-composite (mockup-first mode)
```

### 3.7 Exports

No change required. `skyyrose/elite_studio/agents/compositor/__init__.py` exports only `CompositorAgent`, `SCENE_LOOKBOOK`, and `upload_to_fal`; stage modules are not in the public surface and Stage D rasterize follows the same convention (imported by the orchestrator, not re-exported).

---

## 4. IC-Light cost ceiling plan

### 4.1 Policy doc update

Add to `eval/cost-cap-policy.md` under the "Autonomous singles, batch-gated" section:

| API / endpoint | Per-call cost | Policy | Notes |
|----------------|---------------|--------|-------|
| **Replicate IC-Light v2** (`stage_c_relight`) | $0.05–$0.10 per image | Autonomous singles, batches gated by `RunBudget` headroom | One paid spike required to confirm exact per-call cost; the per-call constant in `infra.py` is the authoritative value once measured. |

### 4.2 Cost constant

Add to `skyyrose/elite_studio/agents/compositor/infra.py` near line 210 (next to the existing FLUX cost constants):

```python
# IC-Light cost constants (used by stage_c_relight)
IC_LIGHT_REPLICATE_COST_USD = 0.075  # midpoint of $0.05–$0.10 observed range; update after first paid spike.
```

### 4.3 Thread `budget` through Stage C

`CompositorAgent.composite()` already receives `budget: Any = None` (orchestrator.py:133). Its `_relight_subject()` wrapper does not forward `budget` to `stage_c_relight.relight_subject()`. Fix the signature:

```python
# stage_c_relight.py
def relight_subject(
    alpha_path: str,
    scene_path: str,
    prompt: str,
    sku: str,
    output_dir: str,
    budget: Any = None,
) -> str:
    ...
```

And in `orchestrator.py:_relight_subject()`, pass `budget=budget` through.

### 4.4 Gate the Replicate call

In `stage_c_relight._run_iclight_replicate()`, before the `httpx.post` to Replicate:

```python
from .infra import IC_LIGHT_REPLICATE_COST_USD, _gate_budget

_gate_budget(budget, IC_LIGHT_REPLICATE_COST_USD, "stage_c_iclight_replicate")
# ... existing httpx call ...
```

If `_gate_budget` raises `BudgetExceededError`, the existing `except` clause already falls through to the libcom local path. No new error-handling code needed — the fallback chain absorbs the budget failure exactly the same way it absorbs an HTTP failure.

### 4.5 Spend recording

On the successful return path of `_run_iclight_replicate()` (after `relit_bytes` has been written to disk), call:

```python
if budget is not None:
    budget.spend(IC_LIGHT_REPLICATE_COST_USD)
```

This mirrors the existing Stage D FLUX spend pattern.

### 4.6 Free fallbacks stay free

`_run_iclight()` (libcom local) and the alpha pass-through final fallback do not call paid APIs. They remain ungated.

---

## 5. Testing

| Component | Test name | Assertion |
|-----------|-----------|-----------|
| `stage_d_rasterize` smoke | `test_stage_d_rasterize.py` (cherry-picked from worktree) | 5 existing tests pass on `main`: pixel-exact, error on missing mockup, error on missing mask, determinism (same inputs → identical bytes), output dimensions match scene. |
| Orchestrator flag branch — `kontext` | `test_orchestrator_stage_d_flag_kontext` | Set env `ELITE_STUDIO_STAGE_D_MODE=kontext`, run `composite()`, assert `stages["composite"]["mode"] == "kontext"` and `stage_d_flux.inpaint_subject` called once. |
| Orchestrator flag branch — `rasterize` happy path | `test_orchestrator_stage_d_flag_rasterize` | Set env `ELITE_STUDIO_STAGE_D_MODE=rasterize`, supply a mockup file, assert `stages["composite"]["mode"] == "rasterize"` and `stage_d_rasterize.rasterize_composite` called once. |
| Orchestrator flag branch — `rasterize` fallback | `test_orchestrator_stage_d_flag_rasterize_fallback` | Set env `ELITE_STUDIO_STAGE_D_MODE=rasterize`, do NOT supply a mockup, assert `stages["composite"]["mode"] == "kontext"`, `stages["composite"]["fallback_reason"] == "missing_mockup"`, FLUX path ran. |
| IC-Light budget gate fires | `test_stage_c_budget_gate_blocks_replicate` | Mock a `RunBudget` that raises `BudgetExceededError` on `ensure_within_budget`. Assert `_run_iclight_replicate` never calls `httpx.post`, and the libcom fallback path runs instead. |
| IC-Light budget spend | `test_stage_c_budget_spend_on_success` | Mock a successful Replicate response. Assert `budget.spend(0.075)` called exactly once. |
| IC-Light no-budget back-compat | `test_stage_c_no_budget_warns_not_raises` | Call `relight_subject(..., budget=None)`. Assert a WARNING log line is emitted and the Replicate call still proceeds (when strict-budget env is off, which is the default). |

**Run command:** `pytest skyyrose/elite_studio/tests/ -k "stage_c or stage_d or compositor or rasterize" -v`

**Coverage gate:** the two changed modules (`stage_c_relight.py`, `orchestrator.py`) must retain ≥85% line coverage per repo testing standard.

---

## 6. Rollback

### Stage D rasterize

- Set environment variable `ELITE_STUDIO_STAGE_D_MODE=kontext` (the default). All compositor runs revert to the FLUX path. No code rollback required.
- For a full code revert: drop the commits that added `stage_d_rasterize.py`, `test_stage_d_rasterize.py`, the orchestrator branch, and the config flag. The FLUX path is unchanged by this design, so reverting is a clean delete.

### IC-Light budget gate

- Set environment variable `ELITE_STUDIO_STRICT_BUDGET=0` (already wired in `infra._strict_budget_enabled()`). The gate downgrades to a warning log. Replicate calls proceed unchecked.
- For a full code revert: revert the commit that threaded `budget=` through `relight_subject()`. The policy-doc row in `cost-cap-policy.md` is documentation and can stay; reverting it costs nothing operationally.

### Why these are safe rollbacks

Each change is additive (new code path, new constant, new threaded kwarg with default `None`). No existing callers break when the new behavior is disabled. The flag default is `kontext`, so production behavior on first deploy is bit-for-bit identical to today.

---

## 7. Open questions and deferred items

| Item | Disposition |
|------|-------------|
| SKU mockup registration system | Out of scope. Stage D rasterize assumes `data/mockups/{sku}.png` is the lookup path. Establishing what registers a mockup, who QAs it, and how it versions is a separate workstream. |
| Per-SKU verification of rasterize output | Out of scope. Stage G visual QA already runs on every composite output; rasterize-mode outputs are QA'd the same way. |
| Batch pre-flight cost estimator | Deferred per Q3 of the brainstorm. The per-call gate plus `RunBudget` headroom check surfaces batches over the policy threshold naturally — when total spend approaches the budget ceiling, the next gate call raises. An explicit pre-flight manifest can layer on later if usage shows the implicit gating is too late in the run. |
| Real measured IC-Light v2 per-call cost | One paid spike against Replicate IC-Light v2 to confirm $0.075 is correct. The constant in `infra.py` is configurable; if the measurement comes in at $0.10, bump the constant in a follow-up commit. |
| Audit-log schema documentation | The new `stages["composite"]["mode"]` and `stages["composite"]["fallback_reason"]` fields should be documented in whatever audit-schema doc exists (or one created). Out of scope for this spec; flagged for the implementation plan. |

---

## 8. Sequencing

Implementation phases (to be expanded by `writing-plans`):

1. **Phase 1 — Stage D landing (additive only, no behavior change).** Cherry-pick the rasterize file + tests, add config flag with `kontext` default, add orchestrator branch with mockup-lookup helper, add audit fields. Deploy. Verify tests green on `main`. No production behavior change because the flag defaults to `kontext`.
2. **Phase 2 — IC-Light cost gate.** Add cost constant + policy row, thread `budget` through Stage C, gate the Replicate call, add tests. Deploy. Verify no regression on existing compositor runs.
3. **Phase 3 — Opt-in rasterize trial.** Pick one SKU with a known-good mockup. Run with `ELITE_STUDIO_STAGE_D_MODE=rasterize`. Compare output to FLUX baseline. Document drift.
4. **Phase 4 — Per-SKU rollout decision.** Out of scope for this spec; covered by a separate go-to-production plan once Phase 3 data exists.

---

*End of spec. Implementation plan to be authored by `writing-plans` after user review.*
