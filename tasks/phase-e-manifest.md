# Phase E — I2I Re-Render Manifest (33 SKUs)

> **Status:** STOP-AND-SHOW. Do NOT dispatch until user confirms.
> **Generated:** 2026-05-11 from current main (post-Phases A-D, hardening P1–P6 at `19a8952d7`)
> **Revised:** 2026-05-11 12:55 PDT — accurate cost ceiling, budget interaction, elite-studio-rooted phrasing.
> **Scope:** Full 33-SKU Elite Studio render run. Engine = ADK render_pipeline (Sequential 9-step + LoopAgent QA-refine + 3-judge tournament + 3D round-table dispatch).

---

## Pre-flight readiness

<!-- PREFLIGHT-AUTO-START -->
| Check | Result |
|-------|--------|
| Catalog rows | 33 / 33 parse cleanly (24 cols, `csv.reader` handles quoted descriptions) |
| Source images present | 33 / 33 (every `image` column path resolves under `wordpress-theme/skyyrose-flagship/`) |
| Output collision guard (ADK pipeline) | **DOC (accepted)** — `renders/gated/<sku>/<sku>-<view>-render.webp` deterministic path at `agents/render_pipeline/tools/generate_image.py:264-268`. LoopAgent refine and re-dispatch both overwrite by design (decision 2026-05-12, path-b). Archive `renders/gated/<sku>/` before re-dispatch if history needed. |
| Round-table import | clean (`python -c "from orchestration.threed_round_table import ThreeDRoundTable"`) |
| Round-table tests | 36 / 36 passing |
| Render-pipeline tests | 28 / 28 passing |
| TRELLIS hardening tests | 8 / 8 passing |
| Elite Studio hardening tests | 18 / 18 passing |
| Aggregate test baseline | **90 / 90 green** |
| TRELLIS.2 available locally | NO — conda not on PATH; TRELLIS.2 provider unavailable on this host |
| `RunBudget` enforcement (P1) | LIVE — `ELITE_STUDIO_BUDGET_USD=25.0` default. `ensure_within_budget` gate raises `BudgetExceededError` on projected breach. |
| Run summary persistence (P2) | LIVE — `logs/runs/<workflow_id>.json` written on success and failure |
| Cross-SKU image-leak guard (P4) | LIVE — `_sku_tokens_consistent()` blocks round-table dispatch on SKU token mismatch |
| 3-judge QA tournament | LIVE — judge tournament wired; specific model IDs not declared in nodes.py (verify in prompts/clients) |
| QA refine loop | LIVE — `LoopAgent(max_iterations=2)` in `agents/render_pipeline/agent.py`; F5 score classifier emits `pass | refine | abort` |
<!-- PREFLIGHT-AUTO-END -->

## Per-SKU readiness (dossier gap audit)

Source = catalog `image` column. `LOGO` / `EXTRAS` = dossier frontmatter field presence. Empty `logo_reference` is a silent quality regression (no logo overlay refs sent to Gemini), not a crash — verified at `agents/render_pipeline/tools/generate_image.py:108-120`.

<!-- PERSKU-AUTO-START -->
| SKU | Collection | SRC | logo_reference | extra_logos | Dossier slug |
|-----|------------|-----|----------------|-------------|--------------|
| br-001 | black-rose | OK | OK | OK | black-rose-crewneck |
| br-002 | black-rose | OK | OK | OK | black-rose-joggers |
| br-003 | black-rose | OK | OK | OK | black-is-beautiful-jersey-series-0-baseball-classic |
| br-004 | black-rose | OK | OK | **GAP** | black-rose-hoodie |
| br-005 | black-rose | OK | OK | **GAP** | black-rose-hoodie-signature-edition |
| br-006 | black-rose | OK | OK | **GAP** | black-rose-sherpa-jacket |
| br-007 | black-rose | OK | OK | OK | black-rose-x-love-hurts-basketball-shorts |
| br-008 | black-rose | OK | OK | OK | black-is-beautiful-jersey-series-1-sf-inspired-football |
| br-009 | black-rose | OK | OK | OK | black-is-beautiful-jersey-series-2-last-oakland-football |
| br-010 | black-rose | OK | OK | OK | black-is-beautiful-jersey-series-3-the-bay-basketball |
| br-011 | black-rose | OK | OK | OK | black-is-beautiful-jersey-series-4-the-rose-hockey |
| br-012 | black-rose | OK | OK | OK | black-is-beautiful-jersey-series-5-last-oakland-baseball |
| lh-002 | love-hurts | OK | OK | OK | love-hurts-joggers |
| lh-003 | love-hurts | OK | OK | OK | love-hurts-basketball-shorts |
| lh-004 | love-hurts | OK | OK | OK | love-hurts-bomber-jacket |
| lh-005 | love-hurts | OK | OK | **GAP** | the-fannie |
| sg-001 | signature | OK | **GAP** | **GAP** | the-bridge-series-the-bay-bridge-shorts |
| sg-002 | signature | OK | OK | OK | the-bridge-series-stay-golden-shirt |
| sg-003 | signature | OK | **GAP** | **GAP** | the-bridge-series-stay-golden-shorts |
| sg-005 | signature | OK | OK | OK | the-bridge-series-the-bay-bridge-shirt |
| sg-006 | signature | OK | OK | **GAP** | mint-lavender-hoodie |
| sg-007 | signature | OK | OK | OK | the-signature-beanie |
| sg-009 | signature | OK | OK | OK | the-sherpa-jacket |
| sg-011 | signature | OK | OK | **GAP** | original-label-tee-white |
| sg-012 | signature | OK | OK | **GAP** | original-label-tee-orchid |
| sg-013 | signature | OK | OK | **GAP** | mint-lavender-crewneck |
| sg-014 | signature | OK | **GAP** | **GAP** | mint-lavender-sweatpants |
| sg-015 | signature | OK | OK | OK | the-windbreaker-set |
| kids-001 | kids-capsule | OK | OK | OK | kids-colorblock-hoodie-set-red-black |
| kids-002 | kids-capsule | OK | OK | OK | kids-colorblock-hoodie-set-purple-black |
| br-003-oakland | black-rose | OK | OK | OK | black-is-beautiful-jersey-series-0-baseball-classic-oakland |
| br-003-giants | black-rose | OK | OK | OK | black-is-beautiful-jersey-series-0-baseball-classic-giants |
| br-003-white | black-rose | OK | OK | OK | black-is-beautiful-jersey-series-0-baseball-classic-white |

**Summary:** 30 / 33 ready for primary-logo render. 22 / 33 fully ready (logo + extras). 3 SKU(s) missing primary `logo_reference`. 11 SKU(s) missing `extra_logos`. 0 dossier file(s) absent.
<!-- PERSKU-AUTO-END -->

## Dossier gap remediation options

Signature collection has no canonical logo — populated dossiers split across `sr-monogram.md`, `red-roses-cloud-cluster.md`, and `black-rose-logo.md` depending on product. Per `feedback_dossier_authoring.md`: "Corey-authored from the actual product, never ML-drafted." Suggested deterministic pairings (subject to your review):

| Dossier | Suggested `logo_reference` | Reasoning |
|---------|-----------------------------|-----------|
| `the-bridge-series-stay-golden-shorts` | `data/brand-logos/black-rose-logo.md` | Pairs with `the-bridge-series-stay-golden-shirt` which uses this |
| `the-bridge-series-the-bay-bridge-shorts` | `data/brand-logos/black-rose-logo.md` | Pairs with `the-bridge-series-the-bay-bridge-shirt` which uses this |
| `mint-lavender-sweatpants` | **NEEDS COREY** | Mint-lavender peers split: crewneck uses `red-roses-cloud-cluster`, hoodie uses `sr-monogram`. No deterministic pairing. |

For `extra_logos` gaps (11 dossiers), the populated convention is one or two `data/brand-logos/<name>.md` entries reflecting product-specific authentic-collection patches or monograms. Without per-product inspection these should be hand-authored, not defaulted to `[]`.

---

## Cost surface (revised — accurate)

The ADK render_pipeline runs **per (SKU, view)** invocation. A "full re-render" for one SKU = 4 view invocations (front / back / detail / hero). 3D round-table is dispatched separately, once per SKU.

### Per-view (single ADK pipeline invocation) — verified from code

Source: `agents/render_pipeline/cli.py:144-147`, `agents/render_pipeline/tools/route_engine.py:28-34`, `skyyrose/elite_studio/graph/nodes.py:128`.

| Stage | Model | Per-view cost (USD) |
|-------|-------|---------------------|
| Engine generation (NB Pro default) | `gemini-3-pro-image-preview` | $0.040 |
| L0 articulation | `claude-sonnet-4-6` | $0.005 |
| Dual-vision consensus | `gemini-3-flash-preview` + `gpt-4o` | $0.010 |
| QA tournament (3 judges, one round) | `gpt-5.5-pro` + `gemini-3.1-pro-preview` + `claude-opus-4-7` | $0.100 |
| Refine retry (1 cycle of LoopAgent) | `flux-pro/kontext` | $0.040 |
| Synthesis output | `claude-opus-4-7` (structured) | $0.005 |
| **Per-view subtotal (no refine)** | | **$0.160** |
| **Per-view subtotal (1 refine retry — typical)** | | **$0.200** |
| **Per-view subtotal (2 refine retries — worst case, LoopAgent ceiling)** | | **$0.240** |

### Per-SKU 3D round-table (one dispatch per SKU)

Default enables (`enable_meshy=True`, `enable_tripo3d=True`, `enable_anigen=True`, `enable_trellis=False`):

| Provider | Per-SKU cost (USD) |
|----------|---------------------|
| Meshy (image-to-3D) | $0.200 |
| Tripo3D (image-to-3D, `.ai` region) | $0.250 |
| AniGen (HF Space free tier) | $0.000 |
| TRELLIS.2 local GPU (unavailable this machine) | $0.000 |
| **3D round-table subtotal** | **$0.450** |

### Per-SKU totals (4 views + 3D)

| Mode | Math | Per-SKU |
|------|------|---------|
| **Floor** (1 view, no refine, no 3D) | $0.160 × 1 | **$0.16** |
| **Conservative** (4 views, no refine, no 3D) | $0.160 × 4 | **$0.64** |
| **Typical** (4 views, 1 refine each, 3D enabled) | $0.200 × 4 + $0.450 | **$1.25** |
| **Worst-case** (4 views, 2 refines, 3D enabled) | $0.240 × 4 + $0.450 | **$1.41** |

### Full 33-SKU run

| Mode | Math | Total (USD) |
|------|------|-------------|
| Floor | $0.16 × 33 | **$5.28** |
| Conservative | $0.64 × 33 | **$21.12** |
| **Typical** | $1.25 × 33 | **$41.25** |
| Worst-case | $1.41 × 33 | **$46.53** |

### Budget interaction (P1 safety)

`ELITE_STUDIO_BUDGET_USD=25.0` (default) is the **hard ceiling**. The `RunBudget` lock-protected accumulator increments on every paid `spend()` call. If the cumulative cost would cross $25, `BudgetExceededError` halts the run cleanly — partial outputs are written, `logs/runs/<workflow_id>.json` records the breach point and per-stage breakdown.

**Implication for the typical-case $41 estimate:** with `ELITE_STUDIO_BUDGET_USD=25.0`, the run is **guaranteed to halt mid-batch** around SKU 20/33. To complete all 33 SKUs without budget breach, raise the ceiling:

```bash
ELITE_STUDIO_BUDGET_USD=50 python -m skyyrose.elite_studio …
```

Recommended ceilings for this dispatch:

| Dispatch option | Recommended `ELITE_STUDIO_BUDGET_USD` |
|-----------------|---------------------------------------|
| Floor / single-view validation | `10` |
| Conservative (4 views, no 3D) | `25` (default) |
| Typical (4 views, refine, 3D) | `50` |
| Worst-case insurance | `60` |

---

## Outputs & destinations

- **2D renders (ADK pipeline):** `renders/gated/<sku>/<sku>-<view>-render.webp` — per-SKU subdir, **deterministic path, overwrite-on-rerun** (LoopAgent refine + Phase E re-dispatch both rewrite). Archive `renders/gated/<sku>/` before re-dispatch if history needed. Env override: `RENDER_PIPELINE_OUTPUT_DIR`. Decision: 2026-05-12 path-b (no guard, no flag, documented).
- **2D renders (legacy compositor path):** `renders/output/<sku>/` — versioned, additive
- **3D models (round-table):** `renders/3d/<sku>_<task-id>.glb` — task-id-suffixed, no collision risk
- **3D models (legacy MeshyClient direct):** `output/` (flat, mixed `.glb`s — being retired)
- **Provider metadata + costs:** logged to round-table internal health dict + per-run summary at `skyyrose/elite_studio/logs/runs/<workflow_id>.json` (P2)
- **Run summary content:** engine, qa, fidelity, budget snapshot (spent + remaining + by-stage), timings, error state

> **Filesystem restructure pending:** user has approved a canonical product home at `skyyrose/elite_studio/products/skyyrose/<sku>/` with `v1/v2/...` versioning. This dispatch still writes to the legacy roots above; new tree migration is a separate task (no money, doc + code work).

## What this manifest does NOT cover

- **WordPress production upload** of any rendered asset — that is a separate STOP-AND-SHOW gate per `CLAUDE.md`. Dispatch produces local files only.
- **Hand-authored fixes** to the 3 missing `logo_reference` and 11 missing `extra_logos` — those require Corey input or explicit acceptance of the auto-suggested pairings above.
- **Filesystem migration** of prior renders into the new canonical tree — user said "migrate what was good, leave behind the terrible." This requires a Corey-curated list and is sequenced after the new tree exists.
- **Legacy compositor path** (`engine="legacy"`) — P7 wires `engine="adk-render"` as the dispatch choice; the legacy compositor remains the default until explicitly switched.

---

## Decision required

Pick one before I touch anything that costs money:

1. **Dispatch as-is** (30/33 full quality, 3/33 with logo regression) — accept the silent gap. Budget = `50` recommended for typical case.
2. **Patch first** with the 2 deterministic pairings (sg-001 + sg-003 → `black-rose-logo`), still leave sg-014 for Corey, then dispatch 32/33 full quality. Budget = `50`.
3. **Halt for full hand-authoring** of all 14 gaps (3 logo + 11 extras) before any dispatch. No money fires until Corey supplies the missing dossier entries.
4. **Smaller test batch** — pick 3-5 SKUs that are 100% ready (e.g. br-001, br-003, lh-003, sg-002, kids-001) and dispatch only those to validate the pipeline end-to-end at ~$5-7 cost before the full 33. Budget = `15`.

> Until you pick one and reply with explicit `y` / `yes` / `dispatch`, no paid API call fires. The Phase E todo in `tasks/todo.md` stays open. The Elite Studio render run uses the ADK engine wired via P7's `engine="adk-render"` selector; if you want the legacy compositor for a specific batch, say so explicitly.
