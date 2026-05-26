# Catalog Extension Proposal — 12 New Pre-Order SKUs

**Date:** 2026-05-26
**Status:** Draft — awaiting founder approval before writing to `skyyrose-catalog.csv`

User said: "make sure all skus and names line up." This proposal flags every naming collision and series-numbering question before committing rows.

---

## Naming convention recap (from existing catalog)

| Collection | Pattern |
|---|---|
| black-rose | `BLACK Rose <Garment>` OR `BLACK is Beautiful Jersey Series: N. <Variant>` |
| love-hurts | `Love Hurts <Garment>` OR `The <Name>` (e.g. The Fannie) |
| signature | `The Bridge Series '<Sub>' <Garment>`, `Mint & Lavender <Garment>`, `Original Label Tee (<Color>)`, `The <Garment>` |
| kids-capsule | `Kids Colorblock <Garment> Set — <Colorway>` |

---

## Proposed 12 new SKU rows

### Category B — Real products with photos (4 SKUs)

| SKU | Proposed Name | Collection | Price | Asset Truth | ⚠ Collision / Notes |
|-----|---------------|------------|-------|-------------|---------------------|
| **lh-001** | The Fannie Pack | love-hurts | $85 | `lh-001-fannie-pack-front-preorder.jpeg`, `lh-001-fannie-pack-techflat.jpeg` + 3 single-fannie shots | ⚠ lh-005 = "The Fannie" (single bag, $45). lh-001 filename has "pack" → multi-bag bundle. **Or:** lh-001 was original Fannie SKU, lh-005 the rerelease. Founder: pack-bundle or duplicate-retire? |
| **sg-004** | Mint Hoodie (Solid) | signature | $45 | `sg-004-mint-hoodie.jpeg` + 4 editorial composites | ⚠ sg-006 = "Mint & Lavender Hoodie". sg-004 single-photo titled just "mint-hoodie". Likely solid mint vs duotone. Confirm? |
| **sg-008** | The Windbreaker Set — Retro | signature | $95 | `sg-008-techflat-windbreaker.jpeg`, `sg-008-windbreaker-set-retro-front.jpg` | ⚠ sg-015 = "The Windbreaker Set" ($85). sg-008 filename says "retro" — variant of sg-015. Higher price assumes premium "retro" tier. Founder: same SKU different colorway or distinct product? |
| **sg-010** | The Bridge Series — Bay Bridge & Golden Gate Set | signature | $145 | Many files: `bridge-shorts-golden-gate`, `bridge-shorts-bay-bridge`, `bay-bridge-set-techflat-back`, `golden-gate-tee-shorts-combo` | ⚠ Looks like a BUNDLE SKU combining sg-001 (Bay Bridge Shorts) + Golden Gate variant. Could also be 2 separate SKUs (sg-010 + sg-011 needed). Founder: bundle SKU or split into two? |

### Category C — Hallucinated design SKUs declared real (8 SKUs)

User confirmed these ARE real upcoming designs. Series-numbering question is the main collision concern.

**Position decision for BiB Series:** existing series uses numbers 0-5. Adding 4 more jerseys breaks the sequence unless they fit numbered slots. Options:
- **Option A (recommended)**: keep `br-d0X` as the SKU identifier, but name with descriptive title that doesn't force them into the numeric series. Less risk of series-number renumber later.
- **Option B**: assign them numeric BiB slots (6, 7, 8, 9) and rename SKUs to `br-016` through `br-019`. Cleaner long-term but requires renaming everywhere.

Option A drafted below; ask founder if B is preferred.

| SKU | Proposed Name | Collection | Price | Asset Truth | ⚠ Collision / Notes |
|-----|---------------|------------|-------|-------------|---------------------|
| **br-d01** | BLACK is Beautiful Hockey Jersey — Teal | black-rose | $115 | 3 techflats, teal hockey | ⚠ br-011 = "BiB Series: 4. The Rose (Hockey)". This is the teal variant. Founder: position in numbered series? |
| **br-d02** | BLACK is Beautiful Football Jersey — Red #80 | black-rose | $115 | 3 techflats, red football #80 | ⚠ br-008 = "1. SF Inspired (Football)", br-009 = "2. Last Oakland (Football)". Additional football design. |
| **br-d03** | BLACK is Beautiful Football Jersey — White #32 | black-rose | $115 | 3 techflats, white football #32 | ⚠ Same series collision as br-d02. |
| **br-d04** | BLACK is Beautiful Basketball Jersey — Court Edition | black-rose | $100 | 3 techflats, basketball | ⚠ br-010 = "3. The Bay (Basketball)". Additional basketball variant. "Court Edition" is a placeholder — needs founder name. |
| **sg-d01** | The Windbreaker Set — Design Variant | signature | $85 | 1 techflat | ⚠ **THREE windbreaker SKUs now:** sg-008 (Retro), sg-015 (current), sg-d01 (design). May be over-specified. Possibly merge or distinguish by colorway. Name is placeholder. |
| **sg-d02** | Signature Collection Shorts | signature | $65 | 1 photo: collection-shorts | ⚠ Generic name. Two existing "Collection Shorts": sg-001 Bay Bridge, sg-003 Stay Golden. Needs a unique sub-name (color? print?). |
| **sg-d03** | Mint & Lavender Sweatsuit Set | signature | $95 | 1 photo: mint-sweatsuit-set | ⚠ Likely the SET version of sg-006 (hoodie) + sg-014 (sweatpants). Bundle SKU. |
| **sg-d04** | Cream Bridge Shorts | signature | $65 | 1 photo: cream-shorts | ⚠ Third Bridge Series shorts color (after Bay Bridge sg-001 and Stay Golden sg-003). Or distinct product? Name assumes Bridge Series sibling. |

---

## Open questions for founder ruling

1. **lh-001** — Fannie Pack (bundle) or retire as duplicate of lh-005?
2. **sg-004** — solid Mint Hoodie distinct from sg-006 Mint & Lavender?
3. **sg-008 vs sg-015 vs sg-d01** — are these three distinct windbreaker SKUs, or two should merge?
4. **sg-010** — bundle SKU OR split into two (`sg-010` Bay Bridge Set + new SKU for Golden Gate)?
5. **br-d01-04** — Option A (keep d-prefix, descriptive names) or Option B (rename to br-016/017/018/019 and slot into numbered BiB Series)?
6. **sg-d02** — what's the sub-name? "Collection Shorts" alone is too generic.
7. **sg-d04** — Bridge Series sibling or standalone?
8. **All 12 prices** — confirm or correct per row.

---

## Series-number reservation (Option B detail)

If founder picks Option B for the d-prefix BR SKUs:

| Current d-SKU | Would become | BiB Series slot |
|---|---|---|
| br-d01 (Hockey Teal) | br-016 | Variant of #4 The Rose Hockey, or new #6 |
| br-d02 (Football Red #80) | br-017 | Variant of #1 SF or #2 Last Oakland |
| br-d03 (Football White #32) | br-018 | Variant of #1 SF or #2 Last Oakland |
| br-d04 (Basketball) | br-019 | Variant of #3 The Bay |

This requires updating every file that references `br-d0X` strings — 5+ code refs each (config.py, multi_agent/agents.py, tests, vision reports, lora trigger map). Big change.

---

## Once approved, I will:

1. Append 12 rows to `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`
2. Create 12 dossier stubs in `wordpress-theme/skyyrose-flagship/data/dossiers/<slug>.md` — placeholders for founder to flesh out
3. Update `wordpress-theme/skyyrose-flagship/data/logo-registry.json` with entries for each new SKU
4. Run `python3 scripts/validate_catalog_consistency.py` (or equivalent) to verify all references align
5. Single commit: `feat(catalog): add 12 pre-order SKUs (4 Cat B + 8 Cat C) [DRAFT NAMES]`
6. Report back which references still need founder name confirmation

**No deploy.** Catalog-only change, no WP site impact until next theme deploy.
