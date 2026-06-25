---
title: Elite Team — Strategic Spec (Internal Imagery System for SkyyRose, SaaS-Eligible Architecture)
date: 2026-05-27
revised: 2026-05-27 (scope re-cut from SaaS-first to internal-first)
status: draft
type: strategic (not implementation)
author: corey + claude (brainstorming session)
companions:
  - 2026-05-27-mockup-stage-d-and-cost-ceiling-design.md (commit 563f57f27)
  - 2026-05-27-compositor-production-hardening-design.md (commit ab8a3706f)
verified_sources:
  - Tripo3D pricing tiers (WebFetch on www.tripo3d.ai/pricing) — used as future-reference benchmark only
  - PhotoRoom pricing tiers (WebFetch on www.photoroom.com/pricing) — used as future-reference benchmark only
  - ComfyUI GitHub repo + Comfy Cloud commercial layer (WebFetch on github.com/comfyanonymous/ComfyUI)
  - DevSkyy Elite Studio component inventory (Bash `ls skyyrose/elite_studio/agents/`)
  - DevSkyy billing stack (Bash `find . -path billing/`) — exists, not yet customer-facing
  - DevSkyy 3D pipeline inventory (Bash `ls ai_3d/`, `ls pipelines/clothing_3d/`, `ls hf-spaces/3d-converter/`)
  - SkyyRose catalog (33 SKUs, 4 collections per `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`)
---

# Elite Team — Strategic Spec

This is a **strategic spec**, not an implementation spec. It defines the product surface, internal SkyyRose outcomes, and the build sequence. **SaaS productization is deferred** until internal outcomes prove the architecture in production for the SkyyRose catalog.

## 1. Vision

**Phase A (now):** Elite Team is the internal imagery system that ships the SkyyRose catalog. Mockup-first 100% replica composites, garment-aware QA, lookbooks, and 3D try-on — all running against SkyyRose's 33 SKUs across 4 collections.

**Phase B (deferred until Phase A outcomes ship):** Elite Team productizes the same architecture as a public SaaS — "the Adobe Creative Cloud of fashion imagery" — once the SkyyRose catalog proves the agents work at quality.

**Why this order.** A productized SaaS without a proven internal outcome is a marketing budget burning. SkyyRose's own catalog is the truth test. Every agent, every quality bar, every pricing assumption in Phase B is grounded in measured Phase A behavior.

The architecture is built SaaS-eligible from day one (multi-tenant-ready primitives, credit-metered internally even when the only "tenant" is SkyyRose) so that the Phase B switch is a deployment + marketing step, not a rewrite.

The differentiator is not a better model. It is **specialized agents composed into garment-specific workflows**, where Tripo / Comfy / PhotoRoom ship generic primitives.

## 2. Reference product analysis (verified primary sources)

### Tripo3D — image-to-3D

WebFetch'd `www.tripo3d.ai/pricing` this session.

| Tier | Monthly | Annual | Credits / month | Models / month |
|------|---------|--------|-----------------|----------------|
| Free | $0 | — | 200 | 8 |
| Pro | $11.94 | $143.28 | 3,000 | 120 |
| Max | $44.90 | $539.40 | 25,000 | 1,000 |
| Team | $54.93 / seat | $1,978.20 / seat | 45,000 | 1,800 |

Per-credit cost (Pro): ~$0.004. API pricing not listed on the public page.

**Phase A use:** none of this pricing applies internally — we hit Tripo's API today and pay per call via the `tripo_agent`. This table is the Phase B reference point for the day we replace those calls with our own engine and price ourselves against it.

**What we beat them on (Phase B claim, Phase A proof point):** Tripo treats every image the same. Fashion-specific knowledge — UV unwrap conventions for garments, fabric-aware retopology, multi-view consistency on stitched panels — is value Tripo cannot ship without becoming us. **Phase A must measure this delta on SkyyRose's own garments before we make the Phase B claim publicly.**

### PhotoRoom — background removal + product editing

WebFetch'd `www.photoroom.com/pricing` this session.

| Tier | What's in it |
|------|--------------|
| Free | 250 white-background exports / month |
| Pro | Unlimited white backgrounds + 500 batch exports / month + 5× AI credits |
| Max | Unlimited white backgrounds + 1,500 batch exports + 3× Pro AI credits + better AI models |
| Ultra | 4,000+ batch exports + 2× Max AI credits + fastest processing |
| Enterprise | 200,000+ images / year minimum, custom credits, SOC 2 Type 2 certified API |

API pricing requires a separate subscription. Exact API rates not on the public page.

**Phase A use:** none of this pricing applies internally. PhotoRoom is a reference, not a dependency. We have not integrated PhotoRoom; this table is the Phase B benchmark.

**What we beat them on (Phase B claim, Phase A proof point):** PhotoRoom ships generic e-commerce product editing. Garment-specific operations (fabric drape correction, label placement, color-accurate fabric swatches, runway-photo cleanup) are workflows, not features they have. **Phase A must produce these workflows for SkyyRose's catalog and measure quality before this becomes a public claim.**

### ComfyUI — node-based image pipeline (OSS) + Comfy Cloud (commercial)

WebFetch'd `github.com/comfyanonymous/ComfyUI` this session. **115,000 stars, 13,400 forks. GPL-3.0.** Comfy Cloud is "our official paid cloud version for those who can't afford local hardware."

**Phase A use:** ComfyUI is a structural reference. We have a ComfyUI-shape already in `skyyrose/elite_studio/creative/` (nodes, edges, router, runner, state, checkpointer). We do not use Comfy directly; we use the pattern.

**What we beat them on (Phase B claim):** ComfyUI exposes 500+ primitive nodes and asks the user to assemble workflows. We ship the same primitives ASSEMBLED into named agents (compositor, color_correction, upscaling, vision_audit, …) that each do one fashion job correctly. Lower ceiling for power users, dramatically higher floor for fashion brands who do not want to learn a node graph.

## 3. Current state (verified by `ls` this session)

### Existing agents under `skyyrose/elite_studio/agents/`

Fourteen specialized agents already shipped, by name:

| Agent | What it does today |
|-------|-------------------|
| `compositor_agent` | 7-stage scene compositing (the subject of the two companion specs) |
| `three_d_agent` | 3D model generation orchestrator |
| `tripo_agent` | Routes to Tripo3D API specifically |
| `tryon_agent` | Virtual try-on (FASHN integration) |
| `upscaling_agent` | Image upscaling |
| `vision_agent` | Vision QA |
| `vision_audit_agent` | Vision-based audit logging |
| `color_correction_agent` | Color correction |
| `generator_agent` | Generic image generation |
| `prompt_enrichment_agent` | Prompt engineering |
| `quality_agent` | Quality scoring |
| `safety_agent` | Content safety |
| `variant_agent` | Variant generation |
| `compositor/` (package) | Stage-decomposed compositor pipeline |

### Existing ventures under `skyyrose/elite_studio/ventures/`

Four ventures, each a product surface in waiting:

- `photo/` — image-shaped products (compositor outputs, virtual photoshoots)
- `threed/` — 3D-shaped products (Tripo3D-clone surface)
- `video/` — video-shaped products (Sora/Runway-equivalent for fashion)
- `_base/` — shared abstractions

### Existing creative graph

`skyyrose/elite_studio/creative/` already has `nodes.py`, `edges.py`, `router.py`, `runner.py`, `state.py`, `checkpointer.py`. **This is a ComfyUI-shape already.** It is a LangGraph-backed node + edge runner with a `PostgresSaver` checkpointer for resume-after-failure.

### Existing billing stack

`billing/` contains:

- `stripe_client.py` — Stripe SDK wrapper
- `plans.py` — plan definitions
- `entitlements.py` — feature gating per plan
- `metering.py` — usage metering for credit-based billing
- `webhooks.py` — Stripe webhook handlers
- `middleware.py` — FastAPI middleware enforcing entitlements

**This is a full credit + subscription stack.** The hardest piece of any Creative-Cloud-shaped business is already in the repo. We are not starting from scratch.

### Existing 3D pipeline

- `ai_3d/` — generation_pipeline, model_generator, providers, quality_enhancer, resilience, virtual_photoshoot
- `pipelines/clothing_3d/` — cli, events, job_store, models, observability, pipeline, queue, worker
- `hf-spaces/3d-converter/` — already-deployed HuggingFace Space for self-hosted 3D conversion
- Engines integrated: tripo, trellis, meshy, hunyuan3d

### Existing HuggingFace Spaces (deployed self-hosting layer)

- `hf-spaces/3d-converter/`
- `hf-spaces/flux-upscaler/`
- `hf-spaces/lora-training-monitor/`
- `hf-spaces/product-analyzer/`
- `hf-spaces/product-photography/`
- `hf-spaces/virtual-tryon/`

**Six product surfaces already deployed as HF Spaces.** Each is a candidate Creative-Cloud product.

## 4. Product surface taxonomy

The Creative Cloud organizes by product. Mapping our agents + ventures + Spaces to product names:

| Creative Cloud product (Elite Team) | Competes with | Backed by |
|-------------------------------------|---------------|-----------|
| **Elite Studio 3D** | Tripo3D, Meshy | `agents/three_d_agent` + `agents/tripo_agent` + `pipelines/clothing_3d/` + `ai_3d/` + `hf-spaces/3d-converter` |
| **Elite Studio Compose** | ComfyUI workflows for fashion | `agents/compositor/` (7-stage pipeline) + `skyyrose/elite_studio/creative/` (node graph) + the two companion specs |
| **Elite Studio Edit** | PhotoRoom, Remove.bg | `agents/color_correction_agent` + `agents/upscaling_agent` + `agents/variant_agent` + `hf-spaces/product-photography` |
| **Elite Studio Try-On** | FASHN, Vue.ai | `agents/tryon_agent` + `hf-spaces/virtual-tryon` |
| **Elite Studio Lookbook** | (no direct competitor — wedge product) | `agents/compositor` + `agents/variant_agent` + `skyyrose/elite_studio/ventures/photo` |
| **Elite Studio Reels** | Runway, Sora, Pika (fashion-cut) | `skyyrose/elite_studio/ventures/video` (skeleton) |
| **Elite Studio Audit** | (no direct competitor — fashion QA wedge) | `agents/vision_audit_agent` + `agents/quality_agent` + `agents/safety_agent` |

Seven product surfaces. Five backed by code that already runs.

## 5. Differentiator thesis

The market does not need another image tool. The market needs **the tool that knows what fashion brands need to ship a product**.

Three differentiators, in priority order:

1. **Agents > nodes.** ComfyUI gives you 500 primitives and a graph. Elite Team gives you named agents that each ship a complete fashion-specific workflow. Lower ceiling, higher floor.
2. **Garment-aware composition.** Mockup-first 100% replica (the subject of the companion Stage D spec) means embroidery, prints, and seam stitching survive the composite intact. Tripo + Comfy + PhotoRoom all fight to preserve those details; we preserve them by construction.
3. **One credit wallet across products.** A 3D model + a try-on + a compositor render are all one credit pool. Tripo / PhotoRoom each have their own. Creative-Cloud-shaped pricing requires one wallet.

The first differentiator is the moat. The second is the wedge product. The third is the pricing wedge.

## 6. Gap analysis (what is missing per surface)

| Surface | Have | Missing |
|---------|------|---------|
| Elite Studio 3D | Engine integrations, HF Space, pipeline, billing primitives | Public API surface, SLA on self-hosted Space, quality benchmark vs Tripo |
| Elite Studio Compose | 7-stage compositor, node-graph runner, LangGraph checkpointer | Web UI for non-CLI users, public workflow library |
| Elite Studio Edit | Color/upscaling/variant agents, HF Space | Public API surface, batch API |
| Elite Studio Try-On | FASHN integration, HF Space | Multi-model try-on, fashion-specific pose library |
| Elite Studio Lookbook | Compositor + variant agent | Lookbook template engine, brand-canon constraints |
| Elite Studio Reels | Skeleton venture, no agent yet | Whole product |
| Elite Studio Audit | vision_audit + quality + safety agents | Public API surface, scoring rubric, dashboard |

Cross-cutting gaps (one per product, but built once for all):

- **Public API surface (REST/GraphQL)** — `api/v1/` exists but is internal. Need a publicly-documented API gateway.
- **Web app shell** — `frontend/` is the admin dashboard, not a customer-facing app. New customer-facing shell needed.
- **Pricing page + marketing site** — none.
- **Docs site** — none, or scattered across `docs/`.
- **SDK (Python + TypeScript)** — none.
- **Multi-tenancy on existing billing** — `billing/entitlements.py` likely single-tenant. Audit needed.
- **SOC 2 Type 2** — PhotoRoom Enterprise has it; we will be asked for it within the first year. Implementation is a 6-month process; start early.

## 7. Pricing — deferred to Phase B

**Phase A (now): no external pricing. Internal credit metering only.**

The existing `billing/metering.py` records consumption against the SkyyRose tenant for forensics: every paid API call (FASHN, Replicate, Anthropic, FAL, Gemini, BRIA) is logged with per-call cost and aggregate spend against a notional credit wallet. This produces the cost-per-SKU and cost-per-lookbook telemetry Phase B will price against.

**The unit work in Phase A:** instrument every agent so that running it against a SkyyRose SKU emits one metering event with `{agent_name, sku, paid_api_cost_usd, output_path, latency_ms}`. The `billing/metering.py` schema already supports this; `billing/middleware.py` enforces it on the FastAPI surface.

**Phase B (deferred):** when SkyyRose-internal outcomes prove the agents work, the metering data informs public pricing. The Tripo + PhotoRoom tiers in §2 are the future benchmark. **No public pricing is set until Phase A measurement is in.**

## 8. Sequencing (Phase A — build order driven by SkyyRose catalog outcomes)

Each phase ships an outcome SkyyRose's own catalog needs. No customer-facing API, no public pricing. The order is dictated by what the SkyyRose brand needs to launch and operate.

| Phase A step | Outcome for SkyyRose | Why this order | Estimate |
|--------------|---------------------|----------------|----------|
| A0 | Compositor production hardening | Foundation. Companion specs (Stage D + IC-Light cost gate; preflight + cache + LRU + backoff) land here. Without these, every later phase pays Replicate twice and fails late. | 4–6 weeks |
| A1 | Mockup-first composites for all 33 SkyyRose SKUs | The launch blocker. Each SKU gets a verified mockup, then deterministic Stage D rasterize produces PDP-ready imagery. | 3–4 weeks (parallel with A0 tail) |
| A2 | Elite Studio Audit on the 33 outputs | vision_audit + quality + safety agents score each SKU's imagery. Surfaces brand-canon drift, fabric-color drift, logo-placement errors. Internal QA gate before any image lands on skyyrose.co. | 2–3 weeks |
| A3 | Elite Studio Lookbook for the 4 collections | Compose + variant agent generate brand-canon lookbook spreads. Outputs feed the WP theme's collection pages and pre-order flows. | 3–4 weeks |
| A4 | Elite Studio Try-On for hero SKUs | tryon_agent + FASHN integration. Limited to the 8–10 hero SKUs that drive conversion. | 3–4 weeks |
| A5 | Elite Studio 3D for hero SKUs | three_d_agent on self-hosted TRELLIS/Hunyuan3D Space, Tripo fallback. Same 8–10 hero SKUs. Powers AR / 360° viewer on PDP. | 6–8 weeks |
| A6 | Metering + cost-per-SKU telemetry consolidated | Aggregate `billing/metering.py` data across A1–A5. Produces the dataset Phase B will price against. | 1 week (instrumentation only; data accumulates throughout) |

**Phase A done = the SkyyRose catalog is shipping imagery, lookbooks, try-ons, and 3D from Elite Team end-to-end, with measured per-SKU costs.**

**Phase B gate (deferred — not in this spec's commitment):** when Phase A is producing measured outcomes for ≥6 months, evaluate whether to productize. The Phase B sub-specs (public API, web shell, marketing site, pricing page, multi-tenancy audit, SOC 2) only run after that gate.

## 9. Decomposition — Phase A only (Phase B sub-specs deferred)

Per the brainstorming skill: "If the project is too large for a single spec, help the user decompose into sub-projects."

**Phase A sub-specs (the only specs we author now):**

| Sub-spec | Drives | Phase A step |
|----------|--------|--------------|
| (already landed) `2026-05-27-mockup-stage-d-and-cost-ceiling-design.md` | Stage D rasterize + IC-Light cost gate | A0 |
| (already landed) `2026-05-27-compositor-production-hardening-design.md` | Preflight + stage cache + LRU + async queue + backoff | A0 |
| `2026-XX-XX-skyyrose-mockup-registration-spec.md` | The per-SKU verified-mockup library that A1 depends on. Defines mockup file format, storage layout, registration process, QA gate. | A1 |
| `2026-XX-XX-skyyrose-catalog-imagery-spec.md` | Running mockup-first composites for all 33 SkyyRose SKUs end-to-end. Defines the run harness, the audit log per SKU, the human-review gate before publish. | A1 |
| `2026-XX-XX-elite-studio-audit-internal-spec.md` | vision_audit + quality + safety on each SKU output. Defines scoring rubric, threshold gates, audit trail. | A2 |
| `2026-XX-XX-elite-studio-lookbook-internal-spec.md` | Lookbook generation for the 4 SkyyRose collections. Defines template + brand-canon constraint set + page layout. | A3 |
| `2026-XX-XX-elite-studio-tryon-internal-spec.md` | Try-on for the 8–10 hero SKUs. FASHN integration hardening, pose library, output gating. | A4 |
| `2026-XX-XX-elite-studio-3d-internal-spec.md` | 3D for hero SKUs. Self-hosted TRELLIS/Hunyuan3D on the existing HF Space + Tripo fallback. AR/360° viewer integration with WP theme. | A5 |
| `2026-XX-XX-elite-team-metering-internal-spec.md` | Consolidated per-SKU cost telemetry across all agents. Defines the schema, retention, dashboard. | A6 |

**Eight Phase A sub-specs.** Each runs its own brainstorm → writing-plans cycle. Together they get the SkyyRose catalog shipping from Elite Team.

**Phase B sub-specs (deferred — listed for traceability, NOT to be authored yet):**

| Future sub-spec | Drives |
|-----------------|--------|
| `elite-team-public-api-spec.md` | Customer-facing REST/GraphQL gateway |
| `elite-team-multi-tenancy-spec.md` | Tenant isolation audit of `billing/entitlements.py` |
| `elite-team-web-shell-spec.md` | Customer-facing web app (separate from admin dashboard) |
| `elite-team-pricing-spec.md` | Public pricing tiers (deferred until Phase A measurement is in) |
| `elite-team-soc2-readiness-spec.md` | SOC 2 Type 2 evidence collection |

These are NOT authored now. They are listed so future-Corey-and-Claude do not forget the path exists.

## 10. Risks — Phase A only

| Risk | Probability | Mitigation |
|------|-------------|------------|
| Mockup-first rasterize misses fidelity on textured fabrics (raised embroidery, sequins, mesh) | Medium | A1's per-SKU human-review gate catches this. SKUs that fail review fall back to the kontext FLUX path per the Stage D spec's flag default. |
| Per-SKU mockup library is laborious to populate (33 SKUs × verified mockups) | High | A1 sub-spec defines the registration process. May require external photoshoot or vendor work — flag in that sub-spec, not here. |
| IC-Light Replicate quality drifts on dark fabric / heavy print SKUs (Black Rose collection especially) | Medium | A2's vision_audit gate scores per-SKU. Drift cases route to libcom local fallback (per Stage C's existing fallback chain). |
| Self-hosted 3D quality lags Tripo at first | High | A5 keeps Tripo as fallback engine via existing `tripo_agent`. Quality benchmark gate before disabling Tripo. |
| Metering data is incomplete — gaps in per-agent cost reporting | Medium | A6 audits every agent for metering coverage. Phase A0's preflight pattern can be extended to assert metering is wired before run. |
| Phase B drift — feature creep toward SaaS productization before Phase A outcome is proven | High | This spec is the gate. Phase B sub-specs do not run until Phase A delivers measured outcomes for ≥6 months. Founder must say "go" to start any Phase B work. |

## 11. Verification trail

Every factual claim about competitors or current-state inventory traces to a tool call from this session:

| Claim | Source |
|-------|--------|
| Tripo3D Free / Pro / Max / Team tier prices and credit allotments | WebFetch on www.tripo3d.ai/pricing |
| PhotoRoom Free / Pro / Max / Ultra / Enterprise tier structure | WebFetch on www.photoroom.com/pricing |
| ComfyUI: 115K stars, 13.4K forks, GPL-3.0, Comfy Cloud as official paid product | WebFetch on github.com/comfyanonymous/ComfyUI |
| 14 named agents under `skyyrose/elite_studio/agents/` | Bash `ls` this session |
| Four ventures (`photo`, `threed`, `video`, `_base`) under `skyyrose/elite_studio/ventures/` | Bash `ls` this session |
| Creative-graph layer (nodes, edges, router, runner, state, checkpointer) under `skyyrose/elite_studio/creative/` | Bash `ls` this session |
| Full billing stack at `billing/` (stripe_client, metering, entitlements, plans, webhooks, middleware) | Bash `find . -path billing/` this session |
| `ai_3d/`, `pipelines/clothing_3d/`, `hf-spaces/3d-converter/` already in repo | Bash `ls` this session |
| Six deployed HF Spaces (3d-converter, flux-upscaler, lora-training-monitor, product-analyzer, product-photography, virtual-tryon) | Bash `ls hf-spaces/` this session |

Any claim not in the table above is a strategic recommendation derived from the verified facts plus the goal — not an unverified factual claim about the codebase or external products.

---

## 12. What this spec does NOT do

It does not:

- Specify implementation. That happens in the eight Phase A sub-specs in §9.
- Commit to any public pricing. Public pricing is a Phase B decision gated on Phase A measurement.
- Commit to SaaS launch. Phase B is deferred and conditional on Phase A outcomes.
- Promise SOC 2, multi-tenancy, marketing, sales motion, or web shell. All Phase B.
- Decide vendor selection for self-hosted 3D compute. That is the A5 sub-spec.

It does:

- Lock the dual-phase framing: Phase A (internal SkyyRose outcomes) before Phase B (SaaS productization).
- Lock the seven-product taxonomy as the target architecture (even though Phase A only operates four of them internally: Compose, Audit, Lookbook, Try-On + the start of 3D).
- Lock the differentiator thesis (agents > nodes; garment-aware composition; one credit wallet).
- Lock the Phase A build sequence (A0 → A6) driven by SkyyRose catalog needs.
- Identify the eight Phase A sub-specs that each run their own brainstorm cycle.
- Make the Phase B option visible without committing to it.

---

*End of strategic spec. Next sub-spec to author: `skyyrose-mockup-registration-spec.md` (the per-SKU verified-mockup library that A1 depends on) — without it, the deterministic Stage D path has nothing to rasterize. Compositor companion specs (A0) continue in parallel via the paused writing-plans flow.*
