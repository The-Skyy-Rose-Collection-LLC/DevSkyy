---
id: 0003
title: Imagery generation reliability is the #1 launch blocker — sequence Phase 5 around it
status: ACCEPTED (Corey, 2026-05-03)
deciders: Corey Foster (founder); Phase 0 KB seed interview
date: 2026-05-03
supersedes: none
superseded_by: none
specified_by: [interview: from-interview.md §4 Reality Check]
---

# ADR 0003 — Imagery as Launch Blocker

## Status

**ACCEPTED** — Corey identified this as the #1 blocker in the Phase 0 KB seed interview (2026-05-03). This decision overrides any Phase 5 sub-phase ordering in V2 §5 that does not put imagery quality first.

## Context

The product catalog has 33 SKUs but most lack production-grade renders that match SkyyRose's editorial aesthetic. The brand's locked reference set as of 2026-05-25 (`docs/brand/visual-references.md`) is **The Five: Kith, Oaklandish, Culture Kings, Fear of God, Palm Angels** (with Aimé Leon Dore as acceptable adjacency) — none of which feature stock or technical-flat product photography. They feature **cinematic editorial photography**. The earlier reference list including The Row, Jacquemus, Document/i-D, Coach, and Drake Related was retired on 2026-05-25 — see the canon doc for the full retired list.

Until SkyyRose's product imagery reaches that bar, the site cannot launch as a luxury brand — regardless of how polished the cart, how impressive the WebXR layer, how sophisticated the AI semantic search, or how clean the drop mechanics. A luxury website with non-luxury imagery reads as a startup playing dress-up. That's worse than a clean Shopify default.

Corey's exact words: **"Imagery generation is the #1 blocker keeping the site from going live."**

## Decision

**Phase 5 sub-phase ordering is re-prioritized to put imagery-related work first.** The original V2 §5 ordering was structural (5.0 prereqs → 5.1 WC blocks → 5.2 WebGL → 5.3 editorial scroll → 5.4 drops → 5.5 mobile gallery → 5.6 AR → 5.7 semantic search → 5.8 WebXR → 5.9 Claude Lab → 5.10 Stripe).

The new ordering, anchored on imagery readiness:

1. **5.0** Prereqs (unchanged — avatar GLB rig check; gates 5.6 + 5.8)
2. **5.1** WC block cart/checkout fix (unchanged — needs to ship before drops anyway)
3. **NEW 5.1.5** Imagery pipeline reliability sweep:
   - Compositor agent (`skyyrose/elite_studio/agents/compositor_agent.py`) reliability audit
   - Nano Banana / GPT-Image / FLUX.2-pro quality bar enforcement
   - Per-SKU front + back + branding view coverage
   - Editorial scene compositing matched to Oakland canon (per `from-interview.md` §2)
4. **5.2** Native WebGL product canvas — but only after 5.1.5 confirms input quality
5. **5.6** AR try-on (FASHN) — moved up from after 5.5 because it directly produces customer-visible imagery
6. **5.3** Editorial scroll-narrative — needs imagery from 5.1.5 to be load-bearing
7. **5.4** Drop mechanics (unchanged dependency on Klaviyo + WC)
8. **5.5** Mobile gallery (unchanged)
9. **5.7** AI semantic search (Pinecone) — needs catalog images for visual search to be meaningful
10. **5.8** WebXR / spatial — depends on 5.0; lower priority than imagery
11. **5.9** Claude Lab admin tool
12. **5.10** Payment processing wiring

## Consequences

### Positive

- The site can launch when imagery is ready, even if WebXR / Claude Lab aren't finished. Those become post-launch enhancements.
- Phase 5 work is sequenced around what unblocks revenue, not around what's technically interesting.
- The "unexpected win" that Corey flagged (aesthetic translation) gets compounded by the engineering work, not undermined by it.

### Negative

- WebXR and Claude Lab — both technically interesting — sit later in the queue. Avoid the temptation to start them early "to keep momentum"; they don't unblock launch.
- The 5.1.5 insertion adds work not in the original V2 plan. Phase 5 wall-time grows.
- AR try-on (5.6) was originally gated by 5.0 prereq (avatar rig). The current 0-bones / 0-animations state of `assets/models/skyy.glb` (per OpenWolf cerebrum + project memory) is a hard blocker that must be resolved before 5.6 can advance, even with the re-prioritization.

### Neutral

- The plan's existing dependency graph still applies — 5.6 needs 5.0; 5.7 still needs Pinecone; 5.10 still depends on 5.1 styling. The re-ordering respects all existing dependencies; it changes priority within the dependency-allowed orderings.

## How to apply

When planning Phase 5 (which gets its own plan-mode session per the per-phase protocol):

1. Open with 5.0 prereq check (avatar rig is the known blocker)
2. Land 5.1 WC block fix (blocks revenue regardless of imagery)
3. **Then** spend deep time on 5.1.5 imagery reliability — `Compositor agent` end-to-end test on all 33 SKUs, document per-SKU pass/fail, fix the failures
4. Only when 5.1.5 reports green across all 33 SKUs do 5.2, 5.6, 5.3 begin

For any Phase 5 work proposed during planning that competes with 5.1.5 for resources or attention, ask: "does this make the imagery problem better or worse?" If it doesn't move imagery forward, it sits behind 5.1.5.

## Cross-references

- [`knowledge-base/seed/from-interview.md`](../seed/from-interview.md) §4 — primary source for this decision
- [`docs/SKYYROSE_V2_MASTER_PLAN.md`](../../docs/SKYYROSE_V2_MASTER_PLAN.md) §5 — original Phase 5 sub-phase ordering, now superseded by this ADR for sequencing
- [`docs/SKYYROSE_WORDPRESS_PLAN.md`](../../docs/SKYYROSE_WORDPRESS_PLAN.md) §6 — per-page editorial briefs that depend on imagery quality
- [`MEMORY.md`](../../../.claude/projects/-Users-theceo-DevSkyy/memory/MEMORY.md) "Production Imagery Pipeline (Verified Mar 8)" — current pipeline state
- `wordpress-theme/skyyrose-flagship/data/dossiers/` — per-product branding spec the imagery pipeline reads
- `skyyrose/elite_studio/agents/compositor_agent.py` — the 6-stage pipeline that needs the reliability sweep

## Open questions for Phase 5 planning

1. What is the current per-SKU pass rate of the Compositor agent on the 33-SKU catalog? (Not yet measured — measurement is part of 5.1.5)
2. Does the imagery quality bar require a human-in-the-loop review step, or can the QC stage (Gemini 3 Pro QA gate) be trusted at scale?
3. Is the existing pipeline's cost profile sustainable for re-rendering 33 SKUs across 3 view types each (99+ renders)?
4. Should 5.1.5 include AR try-on (5.6) as a parallel track since it produces customer-visible imagery?

These are questions for the Phase 5 plan-mode session, not blockers on this ADR.
