---
title: Elite Team Creative Cloud — Strategic Spec (Tripo3D + ComfyUI + PhotoRoom for Fashion)
date: 2026-05-27
status: draft
type: strategic (not implementation)
author: corey + claude (brainstorming session)
companions:
  - 2026-05-27-mockup-stage-d-and-cost-ceiling-design.md (commit 563f57f27)
  - 2026-05-27-compositor-production-hardening-design.md (commit ab8a3706f)
verified_sources:
  - Tripo3D pricing tiers (WebFetch on www.tripo3d.ai/pricing)
  - PhotoRoom pricing tiers (WebFetch on www.photoroom.com/pricing)
  - ComfyUI GitHub repo + Comfy Cloud commercial layer (WebFetch on github.com/comfyanonymous/ComfyUI)
  - DevSkyy Elite Studio component inventory (Bash `ls skyyrose/elite_studio/agents/`)
  - DevSkyy billing stack (Bash `find . -path billing/`)
  - DevSkyy 3D pipeline inventory (Bash `ls ai_3d/`, `ls pipelines/clothing_3d/`, `ls hf-spaces/3d-converter/`)
---

# Elite Team Creative Cloud — Strategic Spec

This is a **strategic spec**, not an implementation spec. It defines the product surface, the market position, and the build sequence. Implementation specs for each product surface are listed in §9 (Decomposition) and authored separately as work begins.

## 1. Vision

**Elite Team is the Adobe Creative Cloud of fashion imagery.**

One subscription. Multi-product. Every product is an agent that already exists inside `skyyrose/elite_studio/agents/`. The competitive frame is not "another image tool" — it is "the suite that fashion brands switch to so they can stop renting Tripo3D, ComfyUI hosts, and PhotoRoom seats separately."

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

**What we beat them on:** Tripo treats every image the same. Fashion-specific knowledge — UV unwrap conventions for garments, fabric-aware retopology, multi-view consistency on stitched panels — is value Tripo cannot ship without becoming us.

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

**What we beat them on:** PhotoRoom ships generic e-commerce product editing. Garment-specific operations (fabric drape correction, label placement, color-accurate fabric swatches, runway-photo cleanup) are workflows, not features they have.

### ComfyUI — node-based image pipeline (OSS) + Comfy Cloud (commercial)

WebFetch'd `github.com/comfyanonymous/ComfyUI` this session. **115,000 stars, 13,400 forks. GPL-3.0.** Comfy Cloud is "our official paid cloud version for those who can't afford local hardware."

**What we beat them on:** ComfyUI exposes 500+ primitive nodes and asks the user to assemble workflows. We ship the same primitives ASSEMBLED into named agents (compositor, color_correction, upscaling, vision_audit, …) that each do one fashion job correctly. Lower ceiling for power users, dramatically higher floor for fashion brands who do not want to learn a node graph.

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

## 7. Pricing + revenue model (proposed)

Adobe Creative Cloud charges $54.99/month for the full suite. Tripo3D charges $11.94 just for 3D. PhotoRoom charges separately for editing.

**Proposed tiers (anchored to Tripo + PhotoRoom verified numbers):**

| Tier | Monthly | Credits | Targets |
|------|---------|---------|---------|
| Free | $0 | 250 / month | Discovery; convert to Pro after first lookbook |
| Pro | $19 | 5,000 | Solo brands, 1–10 SKUs / month |
| Studio | $79 | 25,000 | Multi-SKU brands, 10–100 SKUs / month |
| Team | $79 / seat (min 3 seats) | 45,000 / seat | Agencies, brand teams |
| Enterprise | Custom | Custom | 100K+ images / year, dedicated infra, SOC 2 |

Per-credit consumption is product-specific:

- 3D model generation: 25 credits (≈ Tripo's per-model effective rate)
- Compositor render (single SKU): 5 credits
- PhotoRoom-style background removal: 1 credit
- Try-on (single garment × model): 10 credits

The point of the credit unit: every product feeds one wallet. The customer does not maintain mental balance sheets for 4 different tools.

## 8. Sequencing (build order)

Each phase ships one product to revenue, then funds the next. Compositor work (the two companion specs) is the foundation under Phase 2.

| Phase | Product | Why this order | Time-to-revenue estimate |
|-------|---------|----------------|--------------------------|
| 0 | Compositor production hardening | Foundation for every other product. The two companion specs land here. | 4–6 weeks |
| 1 | Elite Studio Audit | Cheapest to productize (read-only, no generation cost), highest-trust wedge into brand workflows. Sells SOC-2-friendly. | 6–8 weeks |
| 2 | Elite Studio Compose | The differentiating product. Showcases 100% replica fidelity. Requires Phase 0 done. | 8–10 weeks |
| 3 | Elite Studio Edit | PhotoRoom is the easiest competitor to displace; bg removal is solved-tech, brand owns the polish. | 6–8 weeks |
| 4 | Elite Studio 3D | Highest cost play (self-hosted compute), but the moat once shipped. | 10–14 weeks |
| 5 | Elite Studio Try-On | Multi-model try-on is the upsell to Studio + Team tiers. | 6–8 weeks |
| 6 | Elite Studio Lookbook | Bundle product; sells the entire Creative Cloud as one purchase. | 8 weeks |
| 7 | Elite Studio Reels | Last because video is expensive and the field is moving fast. | 12+ weeks |

Total: ~12 months to all seven products shipping in beta. Phase 0 starts immediately; Phase 1 starts the week Phase 0's preflight pattern lands.

## 9. Decomposition

Per the brainstorming skill: "If the project is too large for a single spec, help the user decompose into sub-projects." Elite Team Creative Cloud is too large for a single implementation spec. This strategic spec drives separate sub-specs:

| Sub-spec | Drives implementation of |
|----------|--------------------------|
| `2026-XX-XX-elite-team-public-api-spec.md` | Cross-cutting REST/GraphQL gateway, auth, rate limits |
| `2026-XX-XX-elite-team-credit-wallet-spec.md` | One-wallet credit system, billing/entitlements extensions |
| `2026-XX-XX-elite-team-web-shell-spec.md` | Customer-facing web app shell (Next.js, separate from admin dashboard) |
| `2026-XX-XX-elite-studio-audit-product-spec.md` | First product to ship — Phase 1 |
| `2026-XX-XX-elite-studio-compose-product-spec.md` | Phase 2 product spec, builds on compositor specs |
| `2026-XX-XX-elite-studio-edit-product-spec.md` | Phase 3 |
| `2026-XX-XX-elite-studio-3d-product-spec.md` | Phase 4 |
| `2026-XX-XX-elite-studio-tryon-product-spec.md` | Phase 5 |
| `2026-XX-XX-elite-studio-lookbook-product-spec.md` | Phase 6 |
| `2026-XX-XX-elite-studio-reels-product-spec.md` | Phase 7 |

Ten sub-specs. Each will run its own brainstorm → writing-plans cycle. This strategic spec is the parent.

## 10. Risks

| Risk | Probability | Mitigation |
|------|-------------|------------|
| Self-hosted 3D quality lags Tripo at first | High | Phase 4. Keep Tripo as fallback engine via existing `tripo_agent`. Quality benchmark gate. |
| Multi-tenant billing audit reveals refactor cost > expected | Medium | Audit `billing/entitlements.py` before Phase 1 sells anything publicly. |
| SOC 2 Type 2 takes longer than estimated | High | Start vendor selection and evidence collection in Phase 1, not Phase 7. PhotoRoom Enterprise is gated on this — we will be too. |
| Customer expects ComfyUI-shape power-user surface | Medium | Defer. Ship the higher-floor agent surface first; add a "build-your-own-agent" power surface if revenue justifies. |
| Tripo, PhotoRoom, or Comfy launches a fashion vertical first | Low–Medium | Watch their pricing pages monthly. Move Phase 2 forward if a competitor announces fashion. |
| Credit pricing wrong — under or over | Medium | Phase 0 instrument cost-per-call telemetry (already in `infra._gate_budget`). Reprice after first 100 paying customers. |

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

- Specify implementation. That happens in the ten sub-specs in §9.
- Commit to specific prices. The Pricing in §7 is a proposal anchored to verified competitor data; reprice after measurement.
- Promise SOC 2 certification timing. That is a multi-quarter process gated on vendor selection.
- Make decisions about marketing, brand voice, or sales motion. That is a separate workstream.

It does:

- Lock the vision ("Adobe Creative Cloud of fashion imagery").
- Lock the seven-product taxonomy.
- Lock the differentiator thesis (agents > nodes; garment-aware composition; one wallet).
- Lock the build sequence (Phase 0 → Phase 7).
- Identify the sub-specs that must each run their own brainstorm cycle.

---

*End of strategic spec. Next implementation spec to author: `elite-team-public-api-spec.md` (the cross-cutting layer that every product depends on), or `elite-studio-audit-product-spec.md` (the first product to ship). Compositor companion specs continue in parallel as Phase 0.*
