# SOT-First Product Image Resolver — Build + Reconciliation

**Built 2026-06-30. Source-only; deploy STOP-AND-SHOW gated.**

## What was built
1. **Runtime resolver** — `skyyrose_sot_product_image( $sku, $view )` + `skyyrose_sot_product_image_uri()`
   in `inc/collection-sot-reader.php`. Reads the deployed per-collection `data/collections/<slug>/sot.json`
   (front-first: front_model_image → image), falls back to catalog CSV columns, then placeholder.
   Reuses the existing cached loader `skyyrose_get_collection_sot()`.
2. **11 tiles converted** — `front-page.php` (7 refs) + `template-landing-kids-capsule.php` (4 refs) now
   call the resolver by SKU+view. Zero `/images/products/...` literals remain.
3. **Gate** — `check_no_hardcoded_product_images` in `scripts/validate_catalog_consistency.py` fails the
   build if any template hardcodes an `/images/products/...` path. "SOT seen before everything," enforced.

## Verification (all ran 2026-06-30)
- Resolver runtime harness: **8/8** SKU+view → correct SOT path (real catalog + real sot.json).
- php -l + PHPCS: clean on resolver + both templates.
- Validator: **17/17** checks pass; new gate **proven can-fail** (flags a violation, ignores the resolver call).
- black + ruff clean; 6 catalog tests pass (no regression).
- Eyes-on (pixels) all 6 new SOT images = correct garment for SKU+collection.

## Reconciliation — what each tile renders now vs. after
| Tile (SKU) | Was (hardcoded) | Now (SOT front) | Verdict |
|---|---|---|---|
| br-006 ×3 | sherpa packshot 1024² 59KB | br-006-onmodel 1024×1536 240KB | **ADOPT** — on-model upgrade, correct garment |
| lh-004 ×2 | varsity 896×1200 103KB | lh-004-onmodel 1024×1536 298KB | **ADOPT** — same varsity-bomber, on-model |
| sg-009 | sherpa packshot 1024² 60KB | sg-009-onmodel 1024×1536 223KB | **ADOPT** — on-model upgrade |
| sg-006 | hoodie packshot 1024² 60KB | sg-006-onmodel 1024×1536 203KB | **ADOPT** — on-model upgrade |
| kids-001 front | red-set on-model 896×1200 83KB | kids-001-onmodel 1024×1536 152KB | **ADOPT** — on-model, correct |
| kids-001 back | red-set-back | (same) | no change |
| kids-002 back | purple-set-back | (same) | no change |
| **kids-002 front** | purple-set **on-model** 896×1200 142KB | **ghost-mannequin** 1024² 60KB | **DECIDE** — SOT front is a ghost; on-model exists |

## The one decision: kids-002 front
- The catalog sets kids-002 `front_model_image = ghost/kids-002-ghost-front.webp` (a flat ghost render).
- An on-model purple-set shot exists and is live: `kids-purple-set-front-model.webp` (142KB, on-model).
- kids-001 uses an on-model; kids-002 was set to a ghost — likely a leftover, not intentional.
- **Recommended:** repoint kids-002 `front_model_image` → the on-model (1-line catalog edit + regen),
  for consistency with kids-001. Then the resolver renders the on-model. (Founder call — it changes the SOT.)
- Until decided, the kids-capsule landing renders the ghost. Deploy is held anyway.

## Deploy gate
Source-only so far. Going live needs `deploy-theme.sh` → skyyrose.co (STOP-AND-SHOW), then
post-verify (curl 200 + Playwright mobile/desktop). Hold until kids-002 decided + founder approves.
