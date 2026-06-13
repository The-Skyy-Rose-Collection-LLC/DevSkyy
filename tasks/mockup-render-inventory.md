# Mockup Render Inventory — keep / re-render pass

All images the 5 landing prototypes pulled from `wordpress-theme/skyyrose-flagship/assets/images/products/`.
Founder marks keepers; anything unmarked stays in the re-render queue. (2026-06-10)

## Model-shot renders (AI) — keep candidates

- [ ] `bridge-bay-bridge-shorts-front-model.webp` — sg-001, Bay Bridge shorts on white
- [ ] `stay-golden-tee-front-model.webp` — sg-002 (also used as v1 story image)
- [ ] `signature-windbreaker-set-front-model.webp` — sg-015
- [ ] `signature-beanie-front-model.webp` — sg-007
- [ ] `original-label-tee-orchid-front-model.webp` — sg-012
- [ ] `bridge-bay-bridge-shirt-front-model.webp` — sg-005
- [x] `black-rose-sherpa-jacket-front-model.webp` — br-006 hooded satin — **founder-approved 2026-06-10 ("real product")**
- [x] `signature-sherpa-jacket-front-closed.webp` — sg-009 red-rose closed jacket — **founder-approved 2026-06-10 ("good render, save it")** (rescued from BR subdir, commit a1f84aa2e)
- [ ] `black-is-beautiful-jersey-front-model.webp` — br-003 baseball classic
- [ ] `jersey-last-oakland-football-front-model.webp` — br-009
- [ ] `jersey-the-bay-basketball-front-model.webp` — br-010 (CSV notes existing render already canon-blessed)
- [ ] `jersey-the-rose-hockey-front-model.webp` — br-011 (CSV notes existing render already canon-blessed)
- [ ] `jersey-last-oakland-baseball-front-model.webp` — br-012
- [ ] `the-fannie-front-model.webp` — lh-005

## Ghost renders (placeholder tier — likely re-render)

- [ ] `ghost/lh-002-ghost-front.webp` — Love Hurts Joggers (Black)
- [ ] `ghost/lh-003-ghost-front.webp` — Love Hurts Basketball Shorts
- [ ] `ghost/lh-004-ghost-front.webp` — Love Hurts Bomber ($265 hero product on a ghost — high priority re-render)
- [ ] `ghost/lh-006-ghost-front.webp` — Love Hurts Joggers (White)
- [ ] `ghost/kids-001-ghost-front.webp` / `ghost/kids-002-ghost-front.webp` — Kids sets (pre-order state, lower priority)

## Notes

- Every checked keeper drops out of the OAI re-render batch → direct cost savings on the gpt-image-2 run.
- The `renders/oai/_review` board (review-state.json) tracks the NEW pipeline by product slug; these theme assets are the prior generation. When the re-render batch runs, port keeper approvals into review-state so the pipeline skips them.
- br-006 real photo `br-006-sherpa-jacket.jpeg` stays the WC catalog `image`; render is the landing/front-model surface.
