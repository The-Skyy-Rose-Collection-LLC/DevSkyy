# Brand centroid is global pending false-pass measurement data

**Date:** 2026-05-03
**Status:** accepted

Two reasonable architectures were considered for the brand-style centroid that backs the embedding gate: (a) **per-collection centroids** — four `.npz` files, one each for Black Rose, Love Hurts, Signature, Kids Capsule, loaded by the gate keyed on the SKU's collection — gives semantic correctness for cross-collection mis-staging (a BR SKU rendered in a Signature scene would fail the BR gate); and (b) **global centroid + DINOv2 encoder** — one CLIP `.npz` plus one DINOv2 `.npz`, pooling all 23 approved hero shots — relies on DINOv2's empirical ~2x discrimination gap over CLIP to compensate for the lack of per-collection refinement. We chose to **defer the per-collection refactor pending measurement data**: a labeled set of ~50 known-good and ~50 known-bad renders run against the current global gate at threshold 0.7631 will produce a false-pass rate. If false-pass < 5%, global is sufficient. If > 10%, per-collection is justified. Between 5% and 10% is a judgment call. Until that data exists, the as-shipped global centroids stand; CONTEXT.md flags this as a known-deferred decision so future readers don't mistake the choice for an oversight.

## Considered options
- (a) Per-collection: 4 centroids, ~6/2/3/2 samples each. Stronger semantic correctness; small samples make per-collection percentile thresholds noisy (especially Kids Capsule at n=2).
- (b) Global: 1 centroid pooling all approved hero shots. Simpler; cross-collection variance pulls the threshold down (current 0.7631 is on the loose end of the typical 0.65-0.75 range).
- (c) Defer + measure: chose this. ~2 hours of harness scaffolding + ~100 labeled renders → empirical answer.

## Consequences
- The measurement harness lives at `scripts/measure_brand_centroid_gate.py` and runs against `--good-dir` + `--bad-dir`. Until those dirs are curated, the harness scaffolding is in place but unused.
- When the data lands, this ADR is either reaffirmed (false-pass low, keep global) or superseded by ADR-NNNN ("Brand centroid is per-collection") that links back to this one.
