---
name: Shocking-Not-Impressive Criteria
specified_by: [v2: §2 thesis pillars, §5 Phase 0 outputs]
phase: 0
test_command: node scripts/measurement/run-shocking-eval.js
pass_threshold: ≥3/5 pillars demonstrably first-of-kind via observable criteria
last_updated: 2026-05-03
last_updated_by: eval-harness (Phase 0)
---

# Shocking-Not-Impressive Criteria

The "shocking" eval is what separates a competent build from a *category-defining* build. V2's thesis is that this is the **first WordPress fashion theme to ship native WebGL × WebXR × Editorial × Drop × AR — all under one editorial design language with no seam between content and commerce.**

If we can't observably prove ≥3 of the 5 pillars are first-of-kind in this category, we built another nice fashion site. Not what we set out to build.

## The 5 thesis pillars (from V2 §2)

| # | Pillar | Observable criterion | Verification method |
|---|--------|----------------------|---------------------|
| 1 | **WebGL native** | A native WebGL product canvas (not just decorative 3D scenes) is the *defining identity* of the theme. Every product has a 3D moment. | Survey 50 ThemeForest fashion themes; document WebGL adoption. Skyyrose has WebGL on >50% of product pages; competition has 0%. |
| 2 | **Editorial scroll narratives** | Every product page is a story that ends at the cart button. Scroll-driven, chapter-structured, copy-led. Not a spec sheet. | Compare 3 PDPs to The Row, Aimé Leon Dore, Bottega editorial product pages. Match or surpass on scroll storytelling. Then compare to top 5 ThemeForest fashion theme demo PDPs — none of them tell stories; all are spec sheets. |
| 3 | **Drop mechanics** | Pre-styled countdown → waitlist → unlock → live restock, native to the theme. Not a plugin bolt-on. | Drop a test product. Verify the full flow works without WooCommerce plugin additions. Compare against Supreme/Aimé Leon Dore drop UX — match for tension, beat for visual cohesion. |
| 4 | **WebXR / spatial layer** | WebXR session starts on Vision Pro Safari + Quest 3 browser. Hand-tracking controls for navigation. Standard 3D fallback always available on desktop. | Test on real devices. Document session start time. Verify fallback triggers on unsupported devices. No fashion ThemeForest theme ships WebXR. |
| 5 | **AI semantic search + AR try-on integrated** | Pinecone-backed search returns relevance > keyword. FASHN try-on returns 4-model output in < 8s. Both integrate with WC product schema, not standalone. | Test 50 hand-graded queries (precision@5 ≥ 0.7). Try-on roundtrip < 8s avg. Both surfaces visually integrated into PDP, not modal-bolt-on. |

## Test command

```bash
node scripts/measurement/run-shocking-eval.js
```

Exits 0 if ≥3/5 pillars PASS observable criteria. Reads `eval/shocking-rows/<pillar>.md` for per-pillar evidence.

## Per-pillar row format

```yaml
---
pillar: <1-5>
name: <pillar name>
observable_criterion: <one-line>
verification_artifact: <path to evidence — screenshots, recordings, comparison docs>
competition_survey:
  - source: <ThemeForest URL or competitor site>
    has_pillar: <bool>
    notes: <one-line>
last_evaluated: <YYYY-MM-DD>
status: <PASS | FAIL>
---

<prose: what's been built, why it qualifies as first-of-kind, what the gap to competition is>
```

## What "first-of-kind" means

A pillar is first-of-kind if **either**:

1. **Categorical novelty** — no shipped WordPress fashion theme on ThemeForest or comparable marketplace has this feature at all. (Most likely true for WebXR pillar.)
2. **Categorical depth** — competitors have a shallow version of this feature; Skyyrose's implementation is meaningfully deeper / more native / more integrated. (Most likely true for WebGL canvas + Editorial scroll-narrative pillars.)

If competitors have a shipped version that matches Skyyrose's approach, the pillar **does not qualify** — even if Skyyrose's implementation is better-polished. "Better than X" is impressive, not shocking. "Doesn't exist anywhere else, in this category" is shocking.

## The 3-of-5 threshold

Per V2 §2: "≥3/5 pillars demonstrably first-of-kind." This is the minimum bar. The build can ship without all 5 (some are higher-risk than others — WebXR depends on device support; AR depends on FASHN reliability). But less than 3 means we built another nice fashion site, and the §3 critique re-run in Phase 7 will say so.

## Phase entry checklist

- Phase 0 establishes the rubric (this file)
- Phase 5 sub-phases produce the evidence (5.2 = pillar 1, 5.3 = pillar 2, 5.4 = pillar 3, 5.8 = pillar 4, 5.6 + 5.7 = pillar 5)
- Phase 7 critique re-run includes shocking eval. If <3/5 PASS, the V2 build's shocking thesis is documented as "fell short of original thesis" and the next iteration plans for the gap.
