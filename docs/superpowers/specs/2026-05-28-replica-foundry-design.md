# Replica Foundry — Multi-Tenant SaaS Imagery Pipeline (Design Spec)

- **Date:** 2026-05-28
- **Status:** Approved design — ready for implementation planning
- **Owner:** DevSkyy / Elite Studio
- **Working name:** Replica Foundry (Elite Studio productized as a multi-tenant asset platform)
- **Covers:** Phase 0 (empirical engine A/B) + Phase 1 (engine + guarantee vertical slice). Later phases roadmapped, not specified here.

---

## 1. North Star & Hard Mandate

Become the industry standard for producing **2D and 3D product assets** — product-card imagery, A/B test variants, and world-class marketing renders — delivered as a **multi-tenant SaaS** where each brand's assets are verified replicas of its **real garments**.

**Hard mandate (non-negotiable):** every delivered asset is a verified replica. No hallucinated garments, no invented designs, no generation without a ground-truth reference. The guarantee is enforced **structurally** (free capability probes before spend, a fidelity gate before delivery, human sign-off on anything inferred) — not by prompt wording.

Strategic sequencing (Boris-style: de-risk the binding constraint first): the binding risk is **fidelity**, not signup flow. Phase 1 proves the engine + guarantee end-to-end with **SkyyRose as tenant #1** before any public/commercial surface is built.

---

## 2. Scope

### In scope (this spec)
- **Phase 0** — empirical engine A/B on real garments to calibrate the fidelity threshold and close the garment-reconstruction evidence gap.
- **Phase 1** — multi-tenant primitives (logical isolation), the threed TRELLIS venture wrapped as a tenant-scoped service, the dossier-VALIDATE fidelity gate, the human approval queue, the per-tenant CapabilityMatrix, and same-engine fallback. SkyyRose = tenant #1.

### Explicitly OUT of Phase 1 (later roadmap phases)
- Tenant signup / auth / billing / admin UI
- Public REST API + self-serve catalog/reference ingestion
- 2D modality (compositor / nano-banana) — Phase 2
- Alt-engine (Meshy) auto-routing — Phase 4 gated path
- Real infrastructure isolation (Phase 1 is **logical** `tenant_id` isolation: namespaced paths + per-tenant config, single deployment)

### Decomposition note
Multi-tenant SaaS spanning 2D+3D+fidelity+billing+API is too large for one spec. Each roadmap phase (§13) ships standalone and earns its own spec → plan → implementation cycle. This document specifies only Phase 0 + Phase 1.

---

## 3. Architecture

Extends the existing Elite Studio canonical hub; does not fork it. The threed venture and `ventures/_base.py` framework are reused as-is (the venture is wrapped, not rewritten).

```
skyyrose/elite_studio/
├── platform/                  ← NEW: cross-venture multi-tenant layer
│   ├── __init__.py
│   ├── tenancy.py             Tenant, TenantRegistry, per-tenant config
│   ├── catalog_source.py      CatalogSource protocol + SkyyRoseCatalogSource
│   ├── capability.py          CapabilityMatrix — free per-tenant dep probe
│   ├── approval.py            ApprovalQueue, ApprovalRecord, FidelityReport store
│   ├── service.py             generate_3d(tenant_id, sku, ...) orchestrator
│   └── fidelity/
│       ├── __init__.py
│       ├── render.py          Blender-headless multi-view + coverage map
│       ├── metrics.py         CLIP / LPIPS / SSIM / palette scorers (local)
│       ├── validate.py        hidden-face dossier validation + mesh sanity
│       ├── gate.py            FidelityGate.evaluate → FidelityReport + disposition
│       └── report.py          FidelityReport model + persistence
├── ventures/threed/           ← EXISTING: wrapped as a tenant-scoped service
└── ventures/_base.py          ← EXISTING framework, unchanged
```

**Design principles** (each unit has one purpose, a defined interface, and is testable in isolation):
- `tenancy.py` knows nothing about engines or fidelity — only tenant identity + config.
- `capability.py` only probes; it never spends or generates.
- `fidelity/` only scores + disposes; it never generates or delivers.
- `service.py` is the only module that orchestrates across the others.

---

## 4. Tenancy Model

Phase 1 = **logical isolation** (single deployment, `tenant_id` threaded through everything that persists).

```python
@dataclass(frozen=True)
class Tenant:
    id: str                         # stable slug, e.g. "skyyrose"
    display_name: str
    catalog_source: str             # dotted path to a CatalogSource impl
    reference_root: Path            # per-tenant ground-truth reference assets
    fidelity_thresholds: FidelityThresholds  # per-tenant gate tuning
    enabled_engines: frozenset[str] # {"trellis"} for tenant #1
```

- `tenant_id` namespaces every artifact: delivered assets land in the **user-approved canonical product tree** `skyyrose/elite_studio/products/<tenant>/<sku>/v{n}/` (versioned; `<tenant>` generalizes the approved `products/skyyrose/<sku>/v1/` layout). Fidelity reports, approval records, capability probes, and thresholds are likewise `tenant_id`-keyed. (Raw pre-gate generation stays at the engine's working path, e.g. `renders/3d/<sku>_<task-id>.glb`; only *approved* assets are promoted into the canonical tree.)
- **`CatalogSource` protocol** generalizes the existing `dossier_loader`:
  ```python
  @runtime_checkable
  class CatalogSource(Protocol):
      def get(self, sku: str) -> ProductRecord: ...      # row + dossier + reference paths
      def references(self, sku: str) -> tuple[Path, ...] # ground-truth images for the gate
  ```
- **`SkyyRoseCatalogSource`** = implementation #1: reads the LOCKED canonical sources — the catalog CSV + per-SKU dossiers + `assets/golden/<sku>/` references (`front.jpg` always; `back.jpg` only where the SKU has one — e.g. lh-004 has front+back, br-001 has front only). `references()` returns whatever reference views exist; the gate's coverage map handles missing views by marking those faces inferred. The locked "canonical sources only" + "no silent fallback on missing dossier" rules carry through unchanged: `DossierMissingError` → hard fail.
- `TenantRegistry` resolves `tenant_id → Tenant`; SkyyRose is seeded as the only tenant in Phase 1.

---

## 5. Generation Service & Verifiable Endpoints

The threed venture is wrapped behind a tenant-scoped entry point:

```python
def generate_3d(tenant_id: str, sku: str, *, source_image: str | None = None,
                generate: bool = False) -> GenerationResult: ...
```

### CapabilityMatrix (the "verifiable endpoints" abstraction)
Generalizes the threed `verify_capability` node into a per-tenant, **FREE** probe of every dependency — runs without spend, queryable on demand:

| Capability | Probe (free) |
|---|---|
| engine: local TRELLIS | conda env python resolvable + TRELLIS.2 repo present + output dir writable |
| engine: same-engine fallback (Modal/fal.ai) | endpoint reachable + auth present (HEAD/health, no generation) |
| catalog source | `CatalogSource.get(sku)` resolves (dossier present) |
| reference store | reference images exist + readable for the SKU |
| fidelity scorer | scorer deps importable (torch/CLIP/LPIPS) + Blender resolvable |
| approval queue | queue backend reachable + writable |

`CapabilityMatrix(tenant).probe()` returns a typed matrix of `CapabilityStatus` (green/red + detail). **Generation refuses to start if any *required* capability is red.** You structurally cannot spend on an unproven endpoint — this is the no-hallucination guarantee at the infrastructure layer.

### Fallback policy (honors the locked "no silent fallback" rule)
- **Same-engine fallback** (Modal-hosted or fal.ai-hosted TRELLIS.2): same model → *expected* identical fidelity profile → **transparent overflow** when the local env is down or at capacity. **This "identical" claim is unverified until proven** — `CapabilityMatrix` probes liveness/auth, not output consistency. Transparent overflow is therefore **gated on the Phase 0 same-engine consistency check** (§11): local vs hosted TRELLIS on the identical br-001 input must score ≥ a very-high similarity bar. Until that passes, a hosted-engine asset takes the same human sign-off as any other — never silently treated as local-equivalent.
- **Alt-engine** (Meshy): a *different* engine with a different output distribution and fidelity profile. It is **NOT a fallback** — it is a separate, explicitly-gated path, `ready=False`, never auto-invoked. (Deferred to Phase 4.)
- **No engine available** → honest `engine_unavailable` hard-state. Never a silent substitution.

---

## 6. Fidelity Gate — Crown Jewel (`platform/fidelity/`)

**Policy: dossier-VALIDATE.** TRELLIS is single-shot image→mesh and cannot be *constrained* by a dossier at generation time. The gate therefore **validates after generation**: render, compare visible faces to references, validate inferred faces against dossier ranges, dispose. All gate compute is **free + local** (Blender + local CLIP/LPIPS + trimesh) — never a paid scoring API (a paid scorer would defeat "probe before spend").

**Inputs:** generated GLB · SKU reference image(s) · SKU dossier (palette, material family, construction).

```
GLB ─┐
     ├─▶ 1. RENDER (render.py)     Blender headless → canonical views:
ref ─┘                              source-cam (matches techflat front pose),
                                    back, L/R side, detail. + per-face COVERAGE MAP
                                    (which faces ≥1 reference camera physically sees).

     ├─▶ 2. VERIFY VISIBLE (metrics.py)   source-cam render  vs  reference image:
     │                                      · perceptual  (local CLIP cosine + LPIPS)
     │                                      · structural  (SSIM)
     │                                      · color       (palette distance, brand-hex aware)
     │                                    → composite score. < tenant threshold ⇒ HARD REJECT.

     ├─▶ 3. VALIDATE HIDDEN (validate.py)  faces with ZERO reference coverage:
     │                                      · sampled color ∈ dossier palette (±tol)?
     │                                      · material family plausible vs dossier?
     │                                      · mesh sanity (no holes / non-manifold spikes)?
     │                                    → out-of-range ⇒ FLAG inferred-region violation.

     └─▶ 4. DISPOSE (gate.py)
            visible FAIL                   → REJECT  (regen ≤N, else escalate)
            visible PASS + hidden in-range → PASS-pending-human
            visible PASS + hidden FLAGGED  → HUMAN QUEUE (inferred regions overlaid)
```

### The coverage map is the technical heart of honesty
A face is **"verified"** only if a reference camera physically saw it; everything else is explicitly **"inferred"** and routed to a human. The system can never *silently* pass a hallucinated back panel as fact.

### Regeneration policy (no fidelity-laundering)
"visible-fail ⇒ regen ≤N" must not become "roll the dice until one passes." TRELLIS image→mesh is non-deterministic (sampling), so a retry produces a *different* mesh — legitimate, because the **front has ground truth**: retrying to get a front that matches the real reference is honest, not laundering. Guardrails that keep it honest:
- The visible-face threshold is **fixed across attempts** — never loosened to force a pass.
- Every attempt (seed/params + per-attempt scores) is **recorded in the FidelityReport** — the audit trail shows how many tries it took.
- `N` is small and bounded (default 2; configurable per tenant); exhausting `N` → **escalate to human**, never auto-ship the best-of-failed.
- Retry only addresses **visible** failure. Hidden/inferred faces never auto-pass regardless of attempt count — they always route to human sign-off. So retry cannot launder a hallucinated back panel.

### Report-only calibration mode
Until Phase 0 calibrates the threshold from real garments, the gate runs **report-only**: it scores everything and auto-rejects nothing. This surfaces real score distributions before committing a number that could ship a bad asset or wrongly block a good one. Phase 0 flips it to enforcing.

### FidelityReport (`report.py`)
Persisted per asset, `tenant_id`-namespaced: composite + per-view scores, per-face disposition map, inferred-region overlay image, dossier-validation results, verdict, timestamp. **Nothing delivers without a report + a human approval.** This is the audit trail behind "100% replica."

### Approval queue (`approval.py`)
A human reviews the renders, the verified-vs-inferred overlay, and the scores → approve / reject. Approve → deliver to namespaced output. Reject → regenerate or kill. This is the chosen human-in-loop policy made concrete.

### Renderer choice
**Blender headless** (already in the stack at `three_d_agent.py` for GLB cleanup) — reuse over adding a new dep (`pyrender`). Renders the canonical camera set and produces the per-face coverage map.

---

## 7. Data Flow (end-to-end, `service.py`)

```
request(tenant_id, sku, [source_image override])
 │
 ├─ resolve   CatalogSource(tenant).get(sku) → row + dossier + references
 │              DossierMissingError ⇒ HARD FAIL (locked rule, no fallback)
 ├─ probe     CapabilityMatrix(tenant).probe()  [FREE] — required cap red ⇒ refuse, zero spend
 ├─ route     local TRELLIS ready? → use it
 │            else same-engine (Modal/fal.ai TRELLIS) → transparent overflow
 │            else engine_unavailable HARD-STATE        [PAID hop ⇒ STOP-AND-SHOW]
 ├─ generate  GLB (compute-gated behind generate=True)
 ├─ gate      FidelityGate.evaluate(glb, refs, dossier) [FREE local] → FidelityReport
 │              visible-fail ⇒ regen ≤N ⇒ escalate
 ├─ approve   ApprovalQueue.enqueue(report) → human approve / reject
 └─ deliver   on approve → promote to products/<tenant>/<sku>/v{n}/ + register with consumer
                (WP gallery · experience page · A-B asset store)
```

---

## 8. Error Handling, Cost Gates, Honesty

- **Free probe before every paid or external hop** — no spend on an unproven endpoint.
- **No silent fallback:** missing dossier → hard-fail; no engine → honest `engine_unavailable`; below-threshold → reject, never "best-effort ship."
- **STOP-AND-SHOW** wired on every paid call (Modal/fal.ai generation, Phase 0 Tripo/Meshy): print manifest (action · SKU · source file · cost) → wait for explicit `y`. Reuses the project's existing STOP-AND-SHOW protocol.
- **Budget ceiling — reuse, don't reinvent:** paid spend accounts against the existing `RunBudget` accumulator + `ELITE_STUDIO_BUDGET_USD` hard ceiling (default `25.0`); `BudgetExceededError` halts cleanly with partial outputs + a per-run summary. Phase 0/1 hook into this, not a new cost tracker.
- Every hard-state is an explicit, persisted status enum — honest reporting, full audit trail.
- Generic errors to any future API client; detailed context logged server-side only.

---

## 9. Dependencies

| Dep | Where | Notes |
|---|---|---|
| Blender (headless) | system / existing | already used by `three_d_agent.py`; renderer + coverage map |
| `torch` + `open_clip` / `lpips` | main `.venv` | fidelity scorers — run CPU-fine, must stay importable for CI's free path |
| `trimesh` | main `.venv` | mesh sanity (manifold, holes, spikes) |
| `langgraph`, `dossier_loader` | existing | reused |

**Decision:** fidelity scorers live in the **main `.venv`** (not the `trellis2` conda env) and run on CPU, so CI's free path can import + smoke them without a GPU. Scoring is never a paid API — that would break "probe before spend."

---

## 10. Testing Strategy (85% on the pure-logic platform layer)

- **CI-safe free path:** `CapabilityMatrix` returns honest red without GPU/Blender → the entire free path runs in CI with no infra (reuses the threed verify-path pattern; generation stays gated off).
- **Fidelity gate units:** golden reference + synthetic known-good / known-bad meshes → assert PASS / REJECT / FLAG. Mesh-sanity + brand-palette validation tests with real brand hex values.
- **Tenancy units:** `tenant_id` isolation (no cross-tenant path/threshold leak), `CatalogSource` protocol conformance, `SkyyRoseCatalogSource` reads CSV + dossier + golden.
- **Service units:** routing logic (local → same-engine → hard-state), refuse-on-red-capability, regen-≤N then escalate — all with the engine boundary mocked.
- **Gated integration** (pytest marker, needs GPU): real TRELLIS on br-001 → full gate → report. Never in CI.
- **Golden assets do double duty:** ground-truth references for tenant #1 *and* gate test fixtures.

---

## 11. Phase 0 — Empirical Engine A/B (precedes routing/threshold lock)

**Goal:** close the garment-reconstruction evidence gap and calibrate the fidelity threshold from real garments — no engine routing or threshold number is locked on assumption.

- **Harness:** `scripts/phase0_engine_ab.py`
- **Inputs (verified present):** br-001 (crewneck) — `front.jpg` + `reference.jpg`, **no back ref** (its back faces are inferred → human). lh-004 (bomber) — `front.jpg` + `back.jpg` + `reference.jpg` (full front+back comparison). Distinct garment geometries.
- **Engines:** TRELLIS (owned) · Tripo · Meshy.

**Ordered deliverables (each gates the next):**
1. **Camera-pose calibration (FIRST — without it the score table is garbage).** Establish that the gate's source-cam render reproduces the SkyyRose techflat capture pose. Produce a concrete camera definition (not "canonical orthographic-front" hand-waving) validated against br-001/lh-004 — visible-face render-compare is only meaningful once render pose ≈ reference pose.
2. **Same-engine consistency check** (closes the §5 unverified "identical" claim): local TRELLIS vs Modal/fal.ai-hosted TRELLIS on the identical br-001 input → similarity score. Result sets the bar that must be cleared before transparent overflow is allowed; below it, hosted fallback keeps full human sign-off.
3. **Cross-engine fidelity-score table:** run each engine's mesh through the report-only gate against the golden references → sets the per-tenant similarity threshold and confirms/refutes TRELLIS's garment-fidelity lead.

- **⚠ PAID + GPU compute** → every engine call is **STOP-AND-SHOW gated** and accounted against the existing `RunBudget` ceiling (§8). Real per-SKU 3D costs (from `tasks/phase-e-manifest.md`): Meshy $0.20, Tripo $0.25, TRELLIS-local $0.00. This whole phase is a gate before onboarding any tenant beyond #1.

---

## 12. Phase 1 — Implementation Surface (this build)

1. Commit the built-but-uncommitted threed venture (clean, 10/10 tests green, code-reviewed), then wrap it tenant-scoped.
2. `platform/tenancy.py` + `TenantRegistry` + seed SkyyRose as tenant #1.
3. `platform/catalog_source.py` — `CatalogSource` protocol + `SkyyRoseCatalogSource` (generalizes `dossier_loader`).
4. `platform/capability.py` — `CapabilityMatrix` (generalizes the verify node; lifts `_probe_output_writable` / `_probe_dossier`).
5. `platform/fidelity/` — render, metrics, validate, gate, report (report-only mode initially).
6. `platform/approval.py` — approval queue + FidelityReport store.
7. `platform/service.py` — `generate_3d` orchestrator (resolve → probe → route → generate → gate → approve → deliver).
8. Same-engine fallback (Modal/fal.ai TRELLIS) wired; alt-engine (Meshy) scaffolded `ready=False`.
9. Tests per §10 (85% on platform layer).

---

## 13. Roadmap (later phases — each its own spec)

| Phase | Scope |
|---|---|
| **0** | Empirical A/B (br-001 + lh-004) → threshold calibration. *(this spec)* |
| **1** | Engine + guarantee vertical slice, SkyyRose tenant #1. *(this spec)* |
| **2** | 2D modality (compositor / nano-banana) under the same tenancy + fidelity frame. |
| **3** | Public REST API + self-serve tenant onboarding (catalog/reference ingestion). |
| **4** | Billing + admin + alt-engine (Meshy) explicitly-gated path. |

> **Naming:** these numbered Replica Foundry phases are distinct from the existing lettered render-run scheme (`tasks/phase-e-manifest.md`'s Phases A–E + hardening P1–P7), which governs the ADK render dispatch, not this platform build. No scope overlap.

---

## 14. Risks & Open Items

- **Camera-pose alignment:** the source-cam render must reproduce the reference techflat pose for an apples-to-apples visible-face comparison. **Promoted from risk to a hard Phase 0 deliverable (§11.1)** — pose calibration runs and is validated *before* the cross-engine score table, so no threshold is calibrated on a mismatched pose.
- **Threshold is data-driven, not guessed:** enforcing mode stays off until Phase 0 produces real distributions. Shipping a guessed threshold is explicitly forbidden.
- **Tenant generalization beyond #1** is deferred: a generic tenant must supply its own catalog + references; the `CatalogSource` protocol makes this a Phase 3 implementation, not a Phase 1 rewrite.
- **Blender headless availability** on the generation host is a `CapabilityMatrix` probe — a missing Blender is an honest red, not a crash.

---

## 15. Success Criteria

- A SkyyRose SKU (e.g. br-001) flows end-to-end: resolve → free capability proof → (gated) generate → fidelity gate → FidelityReport → human approval → namespaced delivery.
- The free path (everything except generation) runs green in CI with no GPU/Blender.
- No asset can reach delivery without a FidelityReport and a human approval.
- No paid hop fires without STOP-AND-SHOW.
- Phase 0 produces a real fidelity-score table across the three engines on two real garments.
- Adding tenant #2 later requires implementing `CatalogSource` + seeding a `Tenant` — no core rewrite.
