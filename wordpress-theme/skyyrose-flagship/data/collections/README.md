# Per-Collection Source of Truth (`data/collections/`)

**One file per collection. Open it to find every asset for that collection — products, lockups, scenes, lookbook, logos — already resolved to the ONE correct file per role and existence-verified.**

This exists because collection assets were spread across three masters that don't
cross-check (`skyyrose-catalog.csv`, `visual-manifest.json`, `logo-registry.json`)
plus dozens of near-duplicate lockup/logo files in the tree — so the wrong file kept
getting grabbed (low-res vs high-res lockups, source-art vs display, the sherpa mis-file).

## Files

| File | Collection |
|------|-----------|
| `black-rose.json` | Black Rose (14 products) |
| `love-hurts.json` | Love Hurts (5 products) |
| `signature.json` | Signature (12 products) |
| `kids-capsule.json` | Kids Capsule (2 products) |

## How to use it

- **Need a collection's lockup?** `<slug>.json` → `lockup.display_webp.resolved`. That is THE one to use on web/homepage. `lockup.svg_master` only when you need infinite scale / CSS recolor. `lockup.source_art` is the raw master the others derive from — **never place it directly**.
- **Need a product image?** `<slug>.json` → `products[].images.{image,front_model_image,back_image,back_model_image}.resolved`.
- **Need a scene / hero / lookbook / patch?** under `imagery`.
- **`other_collection_files.files`** = every tree file matching this collection that is NOT a chosen role. Audit before use — some are legit (nav/thumb logos), some are duplicates/superseded art to retire. **Never pull one of these for a role the SOT already fills.**

## Rules (do not break)

1. **These files are GENERATED. Do not hand-edit them.** Fix the master, then regenerate.
   - Product data → `data/skyyrose-catalog.csv`
   - Imagery (lockups, scenes, lookbook, hero) → `data/visual-manifest.json` (display lockups registered there as `lockup_display`)
   - Logos / monograms → `data/logo-registry.json`
   - The high-detail display lockup files → `assets/images/lockups/<collection>-lockup.webp` (resolved via `skyyrose/core/paths.py:WP_LOCKUPS_DIR`)
2. **Regenerate:** `python3 data/build-collection-sot.py --updated YYYY-MM-DD`
3. **Verify (CI/pre-commit gate):** `python3 data/verify-collection-sot.py` — exits non-zero on missing SKUs, unresolved lockups, or any role pointing at a missing file.
4. Every `resolved` path is existence-checked at generation time. A role that can't resolve is emitted `null`, never guessed.

## Known data bugs surfaced (fix in the catalog CSV)

- `br-008`, `br-009`, `br-010` declare a `back_image` whose file does not exist
  (`*-back-model.webp`). These jerseys have no back-model render. Either remove the
  column value or produce the render — listed in each SOT's `unresolved_product_images`.
