# Replica Foundry — Milestone Roadmap

**Status:** Locked 2026-05-29. Decomposition approved by founder.
**Source:** Grounded codebase map (workflow `wf_c7cbd2bb-eec`, 4 mappers + synthesis), every load-bearing claim re-verified against live code.

## Destination

Elite Studio becomes a fully automated, tenant-aware 3D garment asset factory: a golden
photograph of a product is ingested with its CSV record + authored dossier, dispatched in
parallel to multiple 3D engines (Tripo, Meshy, AniGen, TRELLIS), scored against golden
references via CLIP + DINOv2 + SSIM (Blender renders), **the winner chosen by real mesh
fidelity rather than provider reputation**, passed through a human approval gate, and
delivered to a canonical versioned product tree. At catalog scale it sweeps all 33 SKUs (or
a named collection), emits a per-SKU × per-engine scorecard, surfaces dossier/coverage gaps
as named categories, and re-runs when new SKUs/goldens land. The hosted path (API + queue +
consumer) is re-wired through the same tenant-aware platform layer so every HTTP job inherits
capability pre-flight, fidelity gating, approval, and delivery versioning.

## Reuse vs net-new

**~65% built, 35% net-new** — and the 35% is mostly connective tissue + content, not new
algorithms. Solid & reusable today: multi-engine dispatch (`ThreeDRoundTable`), fidelity
scoring math (`metrics.py`), gate disposition (`gate.py`), Blender render harness
(`render.py`), approval queue (`approval.py`), delivery tree writer (`delivery.py`),
`FidelityReport` audit trail, Redis queue, rate limiter, `CostTracker`,
`platform.service.generate_3d`, CLI batch skeleton, catalog enumerator
(`Catalog.list_skus()`), per-view telemetry.

## Confirmed canon / security breaches (live as of 2026-05-29)

1. **Dossier hard-fail bypassed** — `gate.evaluate` (`platform/fidelity/gate.py:24`) calls
   `source.references(sku)` only, never `source.get(sku)` where `DossierMissingError` lives.
   A SKU with goldens but no dossier sails through. Violates the locked no-silent-fallback canon.
2. **Unguarded API path** — `api/three_d.py` `POST /3d/generate/{text,image,upload}`
   (lines 699/772/851) dispatch via background tasks with no gate, approval, tenant, dossier,
   or delivery versioning. Full bypass of every foundry guarantee.
3. **CLIP alignment is noise** — alignment is fed `image:<16-char-hash>` instead of the dossier
   product description, so the 20% CLIP weight in the composite is meaningless.

### Latent correctness gaps

- `camera_profiles/skyyrose.json` **missing** → `render.py:98` silently falls back to `{}` →
  SSIM/DINO scored against goldens with wrong pose → composite is noise. (Confirmed.)
- `FidelityThresholds.visible_composite_min` defaults `0.0` (`tenancy.py`) → gate never
  auto-rejects on score (report-only forever) until calibrated (P3).
- `discover_all_skus()` (`utils.py:122`) globs `OVERRIDES_DIR/*.json` (near-empty, untracked)
  instead of `Catalog.list_skus()` → batch sweep enumerates from the wrong source.
- Golden coverage: front 33/33, back 10/33, three-quarter/detail-1/detail-2 **0/33** → every
  SKU forced to `HUMAN_QUEUE` (no SKU can reach `PASS_PENDING_HUMAN` today).

## Sub-projects (dependency order: P1 → P2 → P3 → P4 → P5 → P6 → P7 → P8)

| # | Name | Size | One-line scope |
|---|------|------|----------------|
| **P1** | Fidelity-Gated Multi-Engine Bridge (1 SKU) | M | Wire dispatch → `gate.evaluate`; winner by `composite_by_angle` mean; enforce dossier `get()`; fix CLIP text; promote winner to `renders/3d/skyyrose/<sku>/v1/<sku>.glb`; write scorecard JSON. **First slice.** |
| P2 | Dossier hard-fail on all paths | S | `source.get()` in `gate.evaluate` + round-table dispatch + guard/route `api/three_d.py`. |
| P3 | Fidelity threshold calibration + tenant writeback | S | Run `phase0_engine_ab.py --execute` on a sample; write `visible_composite_min` back to tenant config. (← the A/B unblocked this session.) |
| P4 | Catalog sweep + scorecard aggregator | M | Replace `discover_all_skus()` with `Catalog.list_skus(active_only=True)`; `--collection`; `dossier_missing` row category; join UUID-keyed logs into a per-SKU × per-engine table; Tripo/Meshy rate-limit entries. |
| P5 | Golden reference capture (content) | XL | Photograph + commit 23 backs + 99 angle goldens (founder/photographer track). Unlocks `PASS_PENDING_HUMAN`. |
| P6 | Deliverable rig + lookbook render | L | Post-approval: approved GLB → rigged asset (AniGen) + deliverable renders (Blender deliverable mode). |
| P7 | Continuous trigger + auto-engine-pick | M | Watcher/CI fires `aenqueue_batch()` on new SKU/golden; engine-selector reads P4 scorecard for per-garment engine choice. |
| P8 | Productization + tenancy | XL | tenant-from-API-key; route `POST /produce` through `platform.service.generate_3d`; HTTP approval endpoints; namespaced queue keys; per-tenant cost/rate; DB-backed approval store. |

## Open decisions (deferred to their sub-project)

- **api/three_d.py** (P2): deprecate the 3 endpoints / gate inline / route through `platform.service` (correct long-term, required by P8).
- **Sweep budget** (P4): raise `ELITE_STUDIO_BUDGET_USD` 25→50 / per-collection batching / dynamic ceiling from P1 cost data.
- **Rig path** (P6): AniGen-routed / Blender-extended / hybrid (AniGen rig + Blender deliverable renders).
- **Approval store** (P8): Redis hash / Postgres / flat-file + `fcntl.flock`.

## Per-sub-project specs

Each Pn gets its own spec under `docs/superpowers/specs/` when it reaches the front of the
queue. P1 spec: next.
