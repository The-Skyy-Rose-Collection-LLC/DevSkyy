# SkyyRose LoRA v5 — Training Spec + Catalog Reconciliation

**Date:** 2026-05-26
**Author:** main session (claude-opus-4-7)
**Status:** Spec draft — assets reconciliation done, training execution blocked on photo gaps.

---

## Executive Summary

v4 LoRA (`devskyy/skyyrose-lora-v4` on Replicate) is functionally broken for production catalog coverage. Three root causes, two correctable from the repo today:

1. **Trigger-word mismatch** — model was trained with per-SKU tokens (`skyyrose_br001`, `skyyrose_lh003`, …) but founder believes the trigger is `SKYYROSE`. Captions contain zero instances of the literal `SKYYROSE` string. Prompting `SKYYROSE …` activates nothing.
2. **Hallucinated SKUs in training set** — 6 fake "design" SKUs (`br-d02/d03/d04`, `sg-d01/d03/d04`) trained as if real. They are not in the catalog and will not be sold. LoRA outputs them confidently.
3. **Coverage gap** — only 12 of 32 catalog SKUs trained. Kids Capsule (2 SKUs) entirely absent. 8 Signature SKUs and 11 Black Rose SKUs uncovered. For those, the LoRA falls back to vanilla flux output with no brand DNA.

**v5 training cannot start until photo gaps are closed.** Six catalog SKUs have **zero source photos in the repo** today. They must be sourced (or rendered + manually approved as substitute) before v5 training begins, or v5 will repeat v4's coverage gap.

---

## Catalog vs Repo Asset Reconciliation

Catalog has **32 SKUs** across 4 collections. Per-SKU asset count in canonical repo locations:

| SKU | Catalog Name | Collection | source-products | products/<sku>/ | wp-theme | Tier |
|-----|------|--------|---|---|---|---|
| br-001 | BLACK Rose Crewneck | black-rose | 4 | 4 | 3 | ✅ |
| br-002 | BLACK Rose Joggers | black-rose | 3 | 4 | 3 | ✅ |
| br-003 | BiB 0. Baseball Classic (Black) | black-rose | 7 | 7 | 3 | ✅ |
| br-004 | BLACK Rose Hoodie | black-rose | 4 | 4 | 3 | ✅ |
| br-005 | BLACK Rose Hoodie — Signature Edition | black-rose | 1 | 3 | 5 | ⚠ source-light |
| br-006 | BLACK Rose Sherpa Jacket | black-rose | 3 | 7 | 5 | ✅ |
| br-007 | BLACK Rose x Love Hurts Basketball Shorts | black-rose | 5 | 6 | 11 | ✅ |
| br-008 | BiB 1. SF Inspired (Football) | black-rose | 2 | 7 | 5 | ⚠ source-light |
| br-009 | BiB 2. Last Oakland (Football) | black-rose | 2 | 6 | 3 | ⚠ source-light |
| br-010 | BiB 3. The Bay (Basketball) | black-rose | 1 | 6 | 3 | ⚠ source-light |
| br-011 | BiB 4. The Rose (Hockey) | black-rose | 2 | 6 | 9 | ⚠ source-light |
| **br-012** | BiB 5. Baseball Classic (Last Oakland) | black-rose | **0** | **0** | 6 | 🔴 **GAP** |
| **br-014** | BiB 0. Baseball Classic (Giants) | black-rose | **0** | **0** | 3 | 🔴 **GAP** |
| **br-015** | BiB 0. Baseball Classic (White) | black-rose | **0** | **0** | 3 | 🔴 **GAP** |
| lh-002 | Love Hurts Joggers | love-hurts | 4 | 4 | 5 | ✅ |
| lh-003 | Love Hurts Basketball Shorts | love-hurts | 8 | 7 | 15 | ✅ |
| lh-004 | Love Hurts Bomber Jacket | love-hurts | 5 | 3 | 8 | ✅ |
| lh-005 | The Fannie | love-hurts | 11 | 0 | 5 | ✅ |
| sg-001 | Bridge Series 'The Bay Bridge' Shorts | signature | 4 | 3 | 5 | ✅ |
| sg-002 | Bridge Series 'Stay Golden' Shirt | signature | 3 | 3 | 5 | ✅ |
| sg-003 | Bridge Series 'Stay Golden' Shorts | signature | 4 | 3 | 5 | ✅ |
| sg-005 | Bridge Series 'The Bay Bridge' Shirt | signature | 5 | 3 | 5 | ✅ |
| sg-006 | Mint & Lavender Hoodie | signature | 3 | 3 | 5 | ✅ |
| sg-007 | The Signature Beanie | signature | 4 | 3 | 3 | ✅ |
| sg-009 | The Sherpa Jacket | signature | 3 | 3 | 5 | ✅ |
| sg-011 | Original Label Tee (White) | signature | 2 | 3 | 5 | ⚠ source-light |
| sg-012 | Original Label Tee (Orchid) | signature | 1 | 3 | 5 | ⚠ source-light |
| sg-013 | Mint & Lavender Crewneck | signature | 4 | 7 | 3 | ✅ |
| sg-014 | Mint & Lavender Sweatpants | signature | 4 | 7 | 3 | ✅ |
| **sg-015** | The Windbreaker Set | signature | **0** | **0** | 3 | 🔴 **GAP** |
| **kids-001** | Kids Colorblock Hoodie Set — Red/Black | kids-capsule | **0** | 6 | 3 | 🟠 no-source |
| **kids-002** | Kids Colorblock Hoodie Set — Purple/Black | kids-capsule | **0** | 6 | 3 | 🟠 no-source |

### Tier definitions

- ✅ **Healthy** — ≥3 photos in `source-products/<collection>/<sku>-*` AND ≥3 elsewhere
- ⚠ **Source-light** — 1–2 photos in `source-products/<collection>/<sku>-*` (acceptable for v5 with caveat: less style variation in LoRA)
- 🟠 **No-source** — 0 photos in `source-products/` but rendered photos exist in `products/<sku>/` or wp-theme. Acceptable if renders are real (not Gemini hallucinations).
- 🔴 **GAP** — only wp-theme deploy copy exists. Source-product photos must be acquired before v5 training.

### Counts

- **Healthy:** 22 SKUs (69%)
- **Source-light:** 5 SKUs (br-005, br-008, br-009, br-010, br-011, sg-011, sg-012) — usable, prefer 3+ for v5
- **No-source:** 2 SKUs (kids-001, kids-002) — verify if `products/kids-001/*` and `products/kids-002/*` are real photos vs Gemini-generated
- **GAP:** 4 SKUs (br-012, br-014, br-015, sg-015) — blocks v5 coverage parity with catalog

---

## v5 Spec

### Trigger word

**Single global token:** `SKYYROSE`

Rationale: v4 used per-SKU tokens (`skyyrose_br001`, `skyyrose_lh003`, …). Forces the operator to know the per-SKU token at prompt time, defeats the brand-as-style abstraction, and makes integration into elite_studio pipelines fragile (every prompt must look up the right token).

v5 captions take the form:

```
SKYYROSE Black Rose collection crewneck, br-001, on-model front view, studio lighting, editorial product photography
```

Single `SKYYROSE` activates the brand DNA. Collection + SKU + view named in plain English. LoRA learns the brand aesthetic globally; prompts disambiguate via natural language.

### Caption template

```
SKYYROSE {collection} collection {garment_type}, {sku}, {view}, {context}, {style_descriptor}
```

Examples:

- `SKYYROSE Black Rose collection crewneck, br-001, on-model front view, soft studio lighting, editorial product photography`
- `SKYYROSE Signature collection beanie, sg-007, flat-lay on concrete, golden hour, lifestyle product photography`
- `SKYYROSE Love Hurts collection bomber jacket, lh-004, on-model 3/4 view, Bay Area rooftop, editorial fashion photography`
- `SKYYROSE Kids Capsule colorblock hoodie set, kids-001, on-child front view, studio backdrop, lifestyle product photography`

### Coverage target

- **32 of 32 catalog SKUs** (zero gap, zero hallucinated d-SKUs)
- Minimum **5 photos per SKU** for "healthy" tier
- Minimum **3 photos per SKU** acceptable (with note in training log)
- Mix of views per SKU when available: front model, back model, flat-lay, detail/closeup

### Image specs

- **Aspect ratios:** mix of 1:1 (1024×1024) and 3:4 (768×1024) — v4 was 1:1-only which made portrait outputs weaker
- **Format:** JPG, quality 90+
- **Resolution:** original or downsampled to longest-side 1024px
- **No techflats** — v4 captions explicitly tagged "technical flat lay illustration, product design reference" which polluted the style register. Techflats are reference-only; not training material.

### Asset types — EXCLUDE

- AI-generated images (Gemini, FLUX, etc. — except verified-by-founder approval)
- Technical flat illustrations / CAD-style renders
- Stock photo composites
- Watermarked or social-platform-scraped images

### Asset types — INCLUDE

- Real product photography (model shots, flat-lays)
- High-fidelity 3D renders that match real product silhouette (only if founder approves the specific render)

### Hyperparameters (Replicate `ostris/flux-dev-lora-trainer`)

| Param | v4 (likely) | v5 |
|-------|-------------|-----|
| trigger_word | per-SKU tokens (bug) | `SKYYROSE` |
| steps | unknown | 2000 (default flux-dev-lora) |
| lora_rank | unknown | 16 (good for style + product DNA balance) |
| learning_rate | unknown | 4e-4 (default) |
| caption_dropout_rate | unknown | 0.05 (small dropout, retains caption signal) |
| autocaption | n/a | **false** — we author every caption manually |
| batch_size | 1 | 1 |

---

## Execution Phases

### Phase A — Photo acquisition (blocks training)

1. **br-012, br-014, br-015** — three baseball jersey variants in BiB series. If real product photos do not exist, founder must shoot 3+ photos per SKU OR approve substitute photos from BiB Jersey 0 (br-003) with manual edits to swap badge/colorway.
2. **sg-015 (The Windbreaker Set)** — verify if photos exist outside repo (founder's camera roll, dropbox, etc.). If not, schedule shoot.
3. **kids-001, kids-002** — verify `products/kids-001/*` and `products/kids-002/*` are real child-model photos vs Gemini renders. If renders, founder approves use OR schedules child-model shoot.

### Phase B — Staging dir build

Output dir: `/Users/theceo/DevSkyy/datasets/skyyrose_lora_v5/`

Existing dir (created 2026-04-21) is **stale and uses wrong trigger word.** Rebuild from scratch:

1. `images/` — 32 sub-folders, one per SKU, 5+ photos each, named `<sku>_<view>_<gender>.jpg`
2. `captions/` — one `.txt` per image with v5 caption template
3. `metadata.jsonl` — Replicate trainer manifest format
4. `dataset_info.json` — README-style summary (SKU count, photo count, caption template version)

### Phase C — Zip + upload to Replicate

```bash
cd /Users/theceo/DevSkyy/datasets/skyyrose_lora_v5
zip -r ../skyyrose-lora-v5-training.zip images/ captions/ metadata.jsonl dataset_info.json

# Upload + train (paid — ~$2.50 for 2000 steps on flux-dev-lora)
replicate train ostris/flux-dev-lora-trainer \
  --destination devskyy/skyyrose-lora-v5 \
  -i input_images=@../skyyrose-lora-v5-training.zip \
  -i trigger_word=SKYYROSE \
  -i steps=2000 \
  -i lora_rank=16
```

### Phase D — Validation

1. Generate 1 image per SKU (32 images, ~$1.30 on `dev` mode at $0.04/img)
2. Founder visual review — pass/fail per SKU
3. Compare against catalog dossier descriptions for accuracy
4. Identify any per-SKU underfits → retrain with weighted samples for those SKUs in v6

---

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Photos for 4 GAP SKUs unavailable | High | Phase A acquires or substitutes; if neither possible, v5 ships with documented 4-SKU coverage hole and falls back to non-LoRA generation for those |
| Kids Capsule photos are AI-generated, not real | Medium | Founder verifies. If AI, retrain Kids Capsule with real photos in v6 or schedule shoot now. |
| New trigger `SKYYROSE` collides with vanilla flux training data | Low | Custom uppercase brand token unlikely in flux corpus; verify with control prompt `SKYYROSE` to vanilla flux pre-training to set baseline |
| Source-light SKUs (5) underfit | Medium | Acceptable; mark as "secondary-tier coverage" in dataset_info.json; v6 can supplement |
| Manual captioning is slow | High (160+ captions) | Author template per SKU, use script to fill view/context, founder reviews random sample of 20 |

---

## Open questions for founder

1. **Phase A**: do real product photos exist for br-012, br-014, br-015, sg-015 outside the repo? If yes, where?
2. **Kids Capsule**: are `products/kids-001/*` and `products/kids-002/*` real photos or AI-generated?
3. **Trigger word**: confirm `SKYYROSE` as the single global v5 trigger (founder said yes verbally; spec records it).
4. **Aspect-ratio mix**: 50/50 1:1 and 3:4, or weighted toward 3:4 since editorial output is mostly portrait?
5. **Budget ceiling for Phase D validation**: $1.30 for 32 SKUs × 1 image OR $5.20 for 32 × 4 images (more confidence per SKU)?

---

## Appendix A — Existing v5 staging dir is stale

`/Users/theceo/DevSkyy/datasets/skyyrose_lora_v5/` was created **2026-04-21**, contains 64 images + 64 captions covering 30 SKUs, but uses the **wrong per-SKU trigger format** (`skyyrose_sg001`, `skyyrose_br001`, …) and **all images are techflats** (captions tagged "technical flat lay illustration, product design reference").

**Action:** rename to `_v5-staging-deprecated-2026-04-21` to preserve history; rebuild `v5/` from scratch under this spec.

---

## Appendix B — v4 training audit raw data

- Source: `/Users/theceo/Downloads/skyyrose_v4_training/`
- 52 images, 52 captions (Replicate model card claimed 105 — discrepancy unexplained)
- 18 unique SKU-tokens; 12 real, 6 hallucinated (`br-d02/d03/d04`, `sg-d01/d03/d04`)
- Trigger format: per-SKU (`skyyrose_<sku>`), zero global `SKYYROSE`
- All images 1024×1024 (no portrait aspect)
- Mixed: real photos + technical flat illustrations + composites (style register is incoherent)

---

## Appendix C — Authoritative asset locations in repo

| Purpose | Path |
|---------|------|
| Source product photos (canonical) | `skyyrose/assets/images/source-products/<collection>/<sku>-*.{jpg,png,webp}` |
| Per-SKU rendered/processed | `skyyrose/assets/images/products/<sku>/*` |
| WP theme deployed images | `wordpress-theme/skyyrose-flagship/assets/images/products/<sku>-*` |
| Brand assets (logos, patches) | `wordpress-theme/skyyrose-flagship/assets/images/{logos,hero-overlays}/` |
| Per-product dossiers (canon) | `wordpress-theme/skyyrose-flagship/data/dossiers/<dossier-slug>.md` |
| Catalog source-of-truth | `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` |
| 3D renders (round table) | `renders/3d/<sku>/` |
| Editorial composites | `editorial-staging/<collection>/` |
| Quarantined renders (failed QA) | `renders/quarantine/<sku>/` |
