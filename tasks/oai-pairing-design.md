# OAI Render — Paired On-Model Design (2026-06-08)

Founder rule: certain coordinating SKUs are **shown together on one model** (paired look)
but **sold separately**. Ghost-mannequin shots stay per-SKU (product cards). The on-model
shot for a paired SKU is the PAIR, not the individual garment.

## Pairs registry (founder-confirmed)

| id | collection | SKUs | label |
|----|-----------|------|-------|
| br-rose-set      | black-rose   | br-001 + br-002 | BLACK Rose Crewneck + Joggers |
| sg-baybridge-set | signature    | sg-001 + sg-005 | Bridge Series 'The Bay Bridge' Shorts + Shirt |
| sg-staygolden-set| signature    | sg-002 + sg-003 | Bridge Series 'Stay Golden' Shirt + Shorts |
| sg-mintlav-set   | signature    | sg-013 + sg-014 | Mint & Lavender Crewneck + Sweatpants |
| lh-bomber-black  | love-hurts   | lh-004 + lh-002 | Love Hurts Bomber + Joggers (Black) |
| lh-bomber-white  | love-hurts   | lh-004 + lh-006 | Love Hurts Bomber + Joggers (White) |
| kids-red-set     | kids-capsule | kids-001 + kids-001-joggers | Kids Colorblock Red — Hoodie + Joggers |
| kids-purple-set  | kids-capsule | kids-002 + kids-002-joggers | Kids Colorblock Purple — Hoodie + Joggers |

- `lh-004` (bomber) belongs to TWO pairs → produces TWO paired on-model looks. A SKU→pairs
  lookup must return a LIST, not a single pair.
- **Kids caveat:** `kids-001-joggers` / `kids-002-joggers` exist in the source map (real render
  sources) but are NOT separate catalog SKUs (the catalog lists kids-001/002 as "Hoodie Set").
  The pair planner resolves partner refs by source-map key, so this works without a catalog row.
  `kids-001`/`kids-002` source = the HOODIE specifically (kids-red-hoodie-front.jpeg). Kids is
  launch-mode/teaser → not in the validation batch; lower urgency.
- NOT paired (single-SKU coordinated set whose on-model already shows the full outfit):
  `sg-015` The Windbreaker Set. (`sg-006` Mint & Lavender HOODIE is separate from the crew+sweat
  pair and renders solo.)

## Matrix change

Per target SKU:
- **ghost-front** — always (product card)
- **ghost-back** — iff `has_back_source(sku)` (product card)
- **on-model** —
  - if SKU ∈ a pair → ONE paired on-model render per unique pair (dedupe; references + dossiers
    from BOTH garments; collection scene). The individual SKU does NOT also get a solo on-model.
  - else → individual on-model (front, collection scene).

Pair on-model is emitted once per pair even if both members are in `targets` (dedupe by pair id).
When only one member is a target (e.g. validation batch has br-001 but not br-002), the pair render
still pulls the partner's references from the catalog — partner needs no ghost render to be a target.

## Scene policy — NO generic content (founder-locked 2026-06-08)

- Every collection MUST have a specific, branded scene in `COLLECTION_SCENES`. No generic
  "studio set" filler — not as a fallback, not inside any scene string.
- **DELETE `_DEFAULT_ONMODEL_SCENE`.** `_background_for(style="on-model", collection)` HARD-FAILS
  (raise `MissingReferenceError` / a SceneError) when the collection has no scene — no silent
  generic fallback (mirrors the no-silent-fallback rule used in the 3D pipeline). A new collection
  without a scene must fail loudly, not ship a generic image.
- Scene wording stays place/mood-specific and on-canon:
  - black-rose: Oakland-anchored Bay Bridge (canon: **Bay Bridge = Oakland**, not SF). Drop "San
    Francisco" → "the Oakland side of the Bay Bridge". (Pending scene-canon audit confirmation.)
  - love-hurts: Beauty-and-the-Beast from the **Beast's POV** — gothic château, brooding.
  - signature: Golden Gate / Bay Area golden-hour street-luxury swag.
  - kids-capsule: throne room, "heir to the throne" — regal but child-appropriate.

## Reference strategy for on-model (solo + pair)

On-model is a FRONT shot. Passing BACK techflats as references invites multi-panel/2-view
collage (the batch-1 sg-015 defect). So:
- `build_references(sku, collection, include_back=False)` → front-relevant refs only
  (ground-truth photo + front techflat + sport-patch/logo). Used for on-model.
- ghost-front: include_back=True (back techflat as construction-only ref, per VIEW directive).
- ghost-back: uses the back techflat as the view to render.
- Pair on-model: concat garment-A front refs + garment-B front refs, relabel
  "GARMENT A — …" / "GARMENT B — …". Cap at config.MAX_REFERENCE_IMAGES (16); 2×~3 = ~6, safe.

## Prompt for pairs

`build_pair_prompt(*, garments=[{name,sku,reference_labels,dossier_text,is_patch}, …], collection, style="on-model")`:
- PRESENTATION (on-model) + VIEW (front) + collection scene background.
- "COORDINATED LOOK: a single model wearing BOTH garments together as one styled outfit —
  GARMENT A: <name>; GARMENT B: <name>. They are sold separately but photographed as a set.
  Exactly ONE model, one cohesive look — never a split/collage/multi-panel of separate items."
- Inject BOTH dossiers, each clearly delimited under its garment, each followed by the
  PRESENTATION OVERRIDE (scene/pose in dossier is ignored; spec governs WHAT is on each garment).
- Patch fidelity block applies per-garment that is a jersey (none of the paired SKUs are jerseys,
  but keep the logic general).

## Output paths

- Solo: `renders/oai/<slug>/{ghost,ghost-back,on-model}.png`
- Pair: `renders/oai/pair__<skuA>__<skuB>/on-model.png` (greppable, no collision, both products
  reference the same hero image).

## Validation batch impact (br-010, sg-015, br-001) — unchanged count

- br-010: ghost + ghost-back + on-model(solo) = 3
- sg-015: ghost + on-model(solo, shows the full windbreaker set) = 2
- br-001: ghost + ghost-back + on-model(PAIRED with br-002) = 3
- Total = 8 images, ~$3.20. (The pair only changes WHAT br-001's on-model depicts.)

## Build order — DONE 2026-06-08

1. ✅ Audit `w73fy6bxv` (23 agents, 16 findings) — folded in.
2. ✅ Implemented: `include_back` on build_references; PAIRS registry (8) + get_pairs_for_sku;
   build_pair_prompt + PAIR_NEGATIVE_GUARDRAILS; plan_pair + run() matrix dedupe; pair output path.
3. ✅ Audit must-fixes applied: `## Scene direction` stripped (CRITICAL multi-panel root cause);
   spec header narrowed to construction/materials only; style/view ValueError guards; SceneError
   hard-fail (no generic scene); lh-006→white-joggers, br-012 back restored, sg-001 composite
   excluded; cost worst-case ceiling; enforce_cap in run().
4. ✅ Verify workflow `wpzkak6un` (clean except deferred sg-015); inline assertions green.
5. ✅ Surfaces: `make render` / `make render-dry`; MCP tools `devskyy_oai_render_plan` +
   `devskyy_oai_render_generate` (confirm-gated). One engine (pipeline.run), three faces.
6. ✅ First paid batch fired: br-010 + br-001, 6 images, $2.40, 0 errored. Outputs in
   renders/oai/{jersey-the-bay-basketball,black-rose-crewneck,pair__br-001__br-002}/.

## Open / deferred

- **sg-015 (Windbreaker)**: RESOLVED 2026-07-01. The 4-panel composite split at the exact 50/50
  midpoint, which bled the pants waistband into the jacket crop (jacket row > half the composite
  height). Fixed via `split_2x2(..., row_split=553)` in `scripts/split_techflats.py` (measured from
  the whitespace gap between panels, y=547-559) — also fixed `TECHFLATS` pointing at the wrong
  `assets/techflats` path instead of `assets/products/techflats`. All 4 crops re-verified clean
  (eyes-on, no cross-panel bleed). No longer excluded from paid runs.
- **Founder visual verdict pending** on the 6-image batch before scaling to the full 81 (≈$32.40).
- **lh-006 flatlay** still resolves a techflat (labeled GROUND TRUTH) — correct garment now, but
  label is a techflat not a photo; refine before the lh-bomber-white pair renders in the full run.
