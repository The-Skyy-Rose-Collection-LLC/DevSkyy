# Phase 15: Ghost Mannequin Agent + QA - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-13
**Phase:** 15-ghost-mannequin-agent-qa
**Areas discussed:** 3D-Replica path (single area; deep-dive across multiple sub-decisions due to user-shared research that reframed the architecture)

---

## 3D-Replica Path (umbrella for ground-truth, strategy, vendor, cost)

### Sub-question 1 — QA ground truth

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — techflat is ground truth | Score against techflat via visual_comparison.py | |
| Yes — but ≥96 floor (not 100) | Same as above with 96 floor as gate; 100% aspirational | |
| No — stay roadmap-literal | Only QA-01/02/04, no score-against-source | |
| Defer to research | Researcher recommends in RESEARCH.md | |
| **Other (user free-text)** | "i think the product flatlay should be the ground truth and techflat used for logo placement refernces" | ✓ |

**User's choice:** Custom — flatlay (`source-photo`) = ground truth; techflat = logo placement reference only.
**Notes:** This refines the offered options materially. The shared convo conflated the two assets; the user separated them. The bundle manifest schema (`techflat-front`, `source-photo`, `logo-ref`, `spec`) confirms the asset taxonomy supports the split.

---

### Sub-question 2 — Generation strategy (cascade vs ensemble)

User asked for "verified senior level analytics on this" before answering. Analysis covered:
- Cost model for 4 strategies (cascade-as-written ~$1.45 expected; Tier-1 ensemble fixed $3.28; full ensemble+retry+cascade ~$4.05; hybrid+jersey-rule ~$4.07)
- Quality model: ensemble of N candidates lifts pass rate from `p` to `1 - (1-p)^N`; for `p=0.7, N=3`, jumps 70% → 97.3%
- Where cascade actually wins: Tier 2/3 must have systematically different failure modes than Tier 1 (true for jersey text; not true for non-jersey)
- The hidden assumption in GM-02: cascade thinking was theoretical, never measured on actual SkyyRose SKUs
- What we don't know: real Tier-1 single-pass rate per metric on our SKUs; whether seed-mutated candidates are statistically independent; GPT-Image-1's actual jersey-text edge

| Option | Description | Selected |
|--------|-------------|----------|
| Hybrid + jersey rule | Tier-1 ensemble of 3 for ALL SKUs. Jersey vetoes cascade GPT-Image-1 → Ideogram; non-jersey vetoes get 1 mutated retry then flag. ~$4 expected / $5 cap | ✓ |
| Hybrid no jersey carve-out | Same but cascade applies to all SKUs; ~$5.85 worst case | |
| Cascade as GM-02 written | Single-shot per tier; ~$1.45 expected; high quality variance | |
| Tier-1 ensemble only, no cascade | 3 Gemini Flash candidates per SKU; pick best; on fail flag; $3.28 fixed | |

**User's choice:** Hybrid + jersey rule.
**Notes:** Locks in the architecture — ensemble where cheapest, cascade where measured value exists.

---

### Sub-question 3 — 3D path scope

| Option | Description | Selected |
|--------|-------------|----------|
| 2D-only — no ThreeDAgent in Phase 15 | Stay Gemini Flash + GPT-Image-1 + Ideogram; ThreeDAgent stays separate | |
| ThreeDAgent as final jersey rescue | Jersey path adds ThreeDAgent at end of cascade; +30 sec / SKU on deepest fallback | |
| ThreeDAgent for jersey FIRST tier | Skip 2D for jerseys; Phase 16 was originally jersey-text-fidelity solver | |
| Defer to research | Bench ThreeDAgent vs GPT-Image-1 on br-009 + br-011 | |
| **Other (user free-text)** | "EVERYTHING SHOULD BE 2D TO 3D" | ✓ |

**User's choice:** Custom — every SKU goes through 2D-to-3D pipeline (no direct 2D path).
**Notes:** Major architectural shift. Required cost re-modeling. Critical clarification followed in next turn: "FLATLAY-MESHY I THOUGHT" — input to digitization is the flatlay, not the techflat. Locked.

---

### Sub-question 4 — Cost confirmation for 2D-to-3D path

Updated cost model presented: ~$17.78 expected for 28 SKUs (Meshy $0.50 once-per-SKU + 3-candidate Gemini RAS ensemble + jersey cascade fallback). Worst case $20.55. `.glb` artifacts cached so retries don't re-digitize.

| Option | Description | Selected |
|--------|-------------|----------|
| Confirmed, proceed | $25 hard cap for Phase 15 single-SKU testing | ✓ |
| Confirmed but tighten cap | $10 hard cap | |
| Keep .glb digitization off-path | Pre-digitize all 28 .glb in Phase 14.5 backfill, then Phase 15 only does synthesis | |
| Reconsider — too expensive | Drop 2D-to-3D for non-jersey SKUs (~$8 total) | |

**User's choice:** Confirmed, proceed.
**Notes:** Locks budget at $25 for Phase 15 single-SKU testing. Phase 18 batch budget defined separately when that phase plans.

---

### Sub-question 5 — 3D digitization vendor

User mid-flight question: "WHOS BETTER MESHY OR TRIPO." Senior comparison delivered:
- For our actual workflow (single-flatlay → scaffold-only → Gemini RAS overwrites textures), Meshy wins on Blender-friendly clean topology; Tripo's surface-detail edge is technically wasted
- Initial recommendation: Meshy (already wired via Phase 16; clean topology; mature API)
- Reversal trigger: "I THINK I HAVE MORE TRIPO CREDITS THO BUT WHATEVER WORKS BEST"
- Found `ai_3d/providers/tripo.py:226` already wraps Tripo's image-to-3D endpoint (`type: "image_to_model"`, `BASE_URL = "https://api.tripo3d.ai/v2/openapi"`) — provider client exists, just unused at agent layer
- Marginal cost = $0 with paid credits → economic call flips to Tripo

| Option | Description | Selected |
|--------|-------------|----------|
| Meshy (recommended) | Default for all 28 SKUs; already wired; clean topology; ~$0.50/SKU | |
| Tripo for everything | Tripo image-to-3D as default; +$0.15/SKU; new agent wrapper (~50 lines) | ✓ |
| Per-garment-type from day 1 | Tripo for jerseys; Meshy for non-jerseys; ~$1.35 batch overhead | |
| Round-table for first batch | Bench 3 vendors on 3 representative SKUs, pick winners | |

**User's choice:** Tripo (with "whatever works best" caveat — recommendation: Tripo default, Meshy auto-fallback if Tripo `.glb` unusable for Blender scaffold).
**Notes:** Tripo region check (`.ai` vs `.com`) required before first paid run per project memory. `get_balance` probe is free — bake into dry-run mode to verify credits ≥ projected batch cost.

---

## Claude's Discretion

- **Prompt template architecture per garment type** — registry vs single dispatch table; planner picks
- **`.glb` cache eviction policy** — default to "keep forever" (small disk footprint); planner can add TTL if storage constraint surfaces
- **Blender render parameter tuning** — start from Phase 16 ThreeDAgent's existing render config; planner tunes only if Blender output unusable

## Deferred Ideas

- HF dataset publisher + SDXL LoRA training pipeline (for non-product imagery: lookbook, editorial, collection-page atmosphere) — pre-v1.3 backlog
- Per-garment-type 3D vendor routing — only if Tripo consistently fails on jerseys
- TRELLIS local 3D digitization — bookmark for v1.3 if dedicated GPU provisioned
- Multi-angle generation (back, side, 3/4) — only front techflats confirmed; v1.3 territory
- Frontend review UI — CLI approval (Phase 17) sufficient for 30-product catalog
- Human-gated cascade approval — rejected; cap-based gate is sufficient given small per-attempt cost
