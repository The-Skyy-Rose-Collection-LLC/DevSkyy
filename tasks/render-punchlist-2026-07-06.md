# Render Punch-List — Eyes-On Imagery Audit 2026-07-06

Vision audit of all 33 SKUs (front + back pixels vs catalog CSV + dossiers), run by the launch-campaign workflow. 13 clean, 20 flagged. Full per-SKU detail: workflow journal `wf_1dfb8a45-9a2/journal.jsonl`.

## URGENT — data landmine (free fix, do first)

- **br-011 CSV back-image column points at `jersey-the-rose-hockey-back-model.webp` = an unrelated "POUT 23" jersey** (no rose, no SkyyRose identity). The resolved manifest serves a different (draft-quality but on-brand) file, so the landmine is dormant — but any consumer reading the CSV column directly serves the wrong garment. Repoint/clear the CSV cell.

## wrong_garment (3) — most severe, never ship

| SKU | Problem |
|---|---|
| kids-001 | Garment silhouette/colorway doesn't match catalog product |
| kids-002 | Ghost front shows different garment than catalog |
| sg-002 | Correct tee, WRONG chest branding (known defect, bug-146 family) |

## hallucinated_back (4) — back shows design that doesn't exist

| SKU | Problem |
|---|---|
| br-012 | Back = generic "30" jersey; spec = black rose in gold clouds + SR monogram. (Also: br-012-onmodel.webp is wrong colorway — black not green — don't substitute it) |
| br-014 | Back trim/number WHITE, front colorway is Giants ORANGE — generic shared back asset suspected |
| br-015 | Same white-trim generic back pattern as br-014 |
| lh-002 | Back inconsistent with front's colorway/design |

## incomplete_render (6) — required design element missing

| SKU | Missing |
|---|---|
| br-003 | Back centered embroidered rose absent (small chance it's tonal black-on-black — zoom-verify before paying for re-render) |
| br-006 | "Big embroidered rose logo on back" absent — plain back |
| br-008 | Back '0' should contain rose fill (reversed from front) — plain white |
| br-011 | Back on-brand but draft-quality (flat/neon, not photoreal like siblings) |
| lh-004 | Element missing per dossier |
| sg-015 | Known 2x2-split boundary family issue |

## ghost_composite (7) — ghost-mannequin in an on-model slot (house-style call, lower severity)

lh-006, sg-003, sg-005, sg-011, sg-012, sg-013, sg-014 — fronts correct; BACK slots resolve to ghost composites. Decide: acceptable house style for backs, or re-render on-model?

## Founder decisions needed (all paid re-renders gated)

1. Fix br-011 CSV cell (free) — approve now?
2. Re-render batch: which of the 13 hard defects (wrong_garment + hallucinated_back + incomplete_render) go to OAI gpt-image-2? Rough order: 3 wrong_garment first, then 4 hallucinated backs, then incompletes.
3. Ghost-composite backs: bless as house style or queue for on-model re-render?
4. br-003: cheap zoom-verify before any paid re-render.
