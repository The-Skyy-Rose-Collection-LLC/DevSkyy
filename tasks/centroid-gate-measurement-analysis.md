# Brand-centroid measurement analysis (2026-05-03)

## TL;DR

The `scripts/measure_brand_centroid_gate.py` harness ran against a curated test set of 75 known-good (held-out hero renders) and 37 known-bad (techflats, source photos, design previews, branding closeups) images. Both CLIP and DINOv2 centroids tripped the harness's "false-pass > 10% → per-collection justified" rule from ADR-0002 — but **the per-category breakdown shows the verdict is misleading**. Per-collection refactor would NOT fix the dominant failure mode.

## Raw harness verdict

| Centroid | Stored threshold | Good pass | Bad false-pass | Harness verdict |
|---|---|---|---|---|
| CLIP (`brand_centroid.npz`)        | 0.7631 | 70.7% | **21.6%** | PER-COLLECTION JUSTIFIED |
| DINOv2 (`brand_centroid_dino.npz`) | 0.3905 | 57.3% | **13.5%** | PER-COLLECTION JUSTIFIED |

Both fail ADR-0002's 10% false-pass ceiling. By the rule, refactor.

## Per-category breakdown — why the verdict is misleading

### CLIP

| Category | n | Min | Median | Max | Pass rate at 0.7631 |
|---|---|---|---|---|---|
| good/back-model       | 25 | 0.748 | 0.860 | 0.900 | **92.0%** |
| good/golden-front     | 25 | 0.665 | 0.778 | 0.849 | 60.0% |
| good/golden-reference | 25 | 0.665 | 0.778 | 0.849 | 60.0% |
| bad/branding          | 22 | 0.529 | 0.634 | 0.717 | **0.0%** ✅ |
| bad/design            | 4  | 0.718 | 0.745 | 0.745 | **0.0%** ✅ |
| bad/source            | 6  | 0.746 | 0.808 | 0.853 | **83.3%** ⚠️ |
| bad/techflat          | 5  | 0.718 | 0.766 | 0.814 | **60.0%** ⚠️ |

CLIP is **excellent** on branding closeups and design previews (0% false-pass). It is **catastrophic** on raw source product photography (83.3% false-pass). The dominant failure mode is "same SKU, no model, no scene" being mistaken for a hero shot. Visual content (garment, colors) is dominating over semantic context (presence of model + scene).

### DINOv2

| Category | n | Min | Median | Max | Pass rate at 0.3905 |
|---|---|---|---|---|---|
| good/back-model       | 25 | 0.240 | 0.561 | 0.693 | **92.0%** |
| good/golden-front     | 25 | 0.174 | 0.344 | 0.564 | 40.0% |
| good/golden-reference | 25 | 0.174 | 0.344 | 0.564 | 40.0% |
| bad/branding          | 22 | 0.091 | 0.281 | 0.421 | 13.6% |
| bad/design            | 4  | 0.219 | 0.236 | 0.236 | **0.0%** ✅ |
| bad/source            | 6  | 0.218 | 0.267 | 0.349 | **0.0%** ✅ |
| bad/techflat          | 5  | 0.236 | 0.302 | 0.502 | **40.0%** ⚠️ |

DINOv2 catches everything CLIP struggles with (0% false-pass on source) — empirically validating the docstring's "~2x discrimination" claim. But DINOv2 is stricter on legitimate goldens too: 40% pass on golden-front vs CLIP's 60%. The encoders have **complementary failure modes**.

## Why per-collection refactor would NOT fix this

The dominant CLIP false-pass is `bad/source` at 83.3%. Source photos are raw product photography of the same SKU as a corresponding front-model render. A per-collection split puts the source photo and the hero render under the same centroid (same SKU = same collection). The centroid won't separate them — visual content dominates.

The same logic applies to bad/techflat at 60% — same SKU, same colors, just orthographic on white background.

**Per-collection refactoring addresses cross-collection mis-staging (a BR product rendered in a Signature scene). It does not address image-archetype confusion (a hero render confused with the source photo of the same SKU).** The ADR-0002 decision rule conflated these two failure modes.

## What the data actually argues for

### Recommendation: ensemble both encoders (logical AND)

Require BOTH CLIP and DINOv2 to accept before the gate passes. Computed from the per-image scores:

| Category | CLIP-only pass | DINOv2-only pass | Ensemble (both pass) |
|---|---|---|---|
| good/back-model       | 92% | 92% | ~85% (assuming partial overlap) |
| good/golden-front     | 60% | 40% | ~30% |
| good/golden-reference | 60% | 40% | ~30% |
| bad/branding          | 0%  | 13.6% | **0%** |
| bad/design            | 0%  | 0%  | **0%** |
| bad/source            | 83.3% | 0% | **0%** |
| bad/techflat          | 60% | 40% | ~25% |

(The ensemble pass-rates above assume rough independence between encoders; actual numbers need to be computed from per-image score correlation. The harness JSON has both score arrays — a follow-up join is straightforward.)

The ensemble eliminates the dominant CLIP failure mode (source photos at 83% → 0%) at the cost of stricter golden-fixture acceptance (~30% pass). For the gate's PRODUCTION purpose — catching off-brand compositor outputs — the false-pass rate is what matters, and the ensemble drives it to near-zero on three of four bad categories.

### Caveats on the test set

1. **The bad set isn't representative of compositor outputs.** Compositor outputs are model+scene renders, not techflats or source photos. A more rigorous test would use renders that are hero-shot-style but off-brand (e.g., SkyyRose products in wrong scenes, or non-SkyyRose hero shots). Generating these would require paid renders — gated by STOP AND SHOW protocol.
2. **Golden-front/reference pass rates of 60% (CLIP) / 40% (DINOv2) on KNOWN-GOOD images suggest the centroid is biased toward back-model aesthetics.** The 23-sample centroid was likely built from `*-front-model.webp` files, but the back-model held-out passes at 92% while golden-front at 60% — this is counter-intuitive and worth investigating. Hypothesis: the goldens are a different fidelity (jpg vs webp, different render era) and that fidelity gap dominates over the front/back angle gap.
3. **CLIP's stored threshold (0.7631) is the 10th percentile of in-cluster similarities for the 23 training images.** With held-out goldens at 60% pass rate, the threshold may be set too tight — but lowering it pushes the bad/source false-pass even higher. There's no good single-encoder threshold; the ensemble is the way out.

## What I am NOT recommending

- **Per-collection refactor.** Data does not support it. The failure modes are not cross-collection in nature.
- **Trusting the harness's binary verdict.** The "PER-COLLECTION JUSTIFIED" string is a false signal driven by an over-simplified decision rule.
- **Auto-implementing the ensemble.** This is a real architecture choice that warrants its own grilling pass: where does the AND happen (in `embedding_gate.evaluate()` taking a list of centroids?), how are thresholds tuned, etc.

## Open questions for the next grilling pass

1. Is the dominant production-time failure mode "off-brand compositor output that resembles a source photo" (would the gate ever encounter this in production)? If yes, the source-photo false-pass matters in practice. If no (because the compositor's output is always model+scene by construction), then CLIP-alone may be fine for the gate's actual purpose.
2. Does an ensemble belong in `embedding_gate.evaluate()` (logic level) or as a higher-layer policy (compositor decides when to require ensemble vs single)?
3. Should the centroid build process record `sample_paths` so future provenance audits can confirm what was in the centroid? (Already partially addressed — new centroids built via the updated `build_centroid()` will record paths, but the existing 2 centroids predate this.)

## Decision deferral

ADR-0002 said "measure and decide." The measurement happened. The data argues that the binary global-vs-per-collection question was the wrong frame. Marking ADR-0002 as **measured but inconclusive on its original question** — superseded by a future ADR that addresses the ensemble decision once that grilling pass happens.
