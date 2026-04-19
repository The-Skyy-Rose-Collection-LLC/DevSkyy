# Canonical Catalog — Elite Web Builder Reference

**Single source of truth:** `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`

Every agent in this team reads from that CSV. Do NOT duplicate the SKU list in prompts, tests, or template scaffolds — import/fetch from the canonical file.

## Current catalog (30 SKUs, as of 2026-04-19)

### BLACK ROSE (12 products)

| SKU | Name | Price | Status |
|-----|------|-------|--------|
| br-001 | BLACK Rose Crewneck | $35 | Active |
| br-002 | BLACK Rose Joggers | $50 | Active |
| br-003 | BLACK is Beautiful Jersey Series: 0. Baseball Classic | $100 | Pre-Order |
| br-004 | BLACK Rose Hoodie | $40 | Active |
| br-005 | BLACK Rose Hoodie — Signature Edition | $65 | Active |
| br-006 | BLACK Rose Sherpa Jacket | $95 | Pre-Order |
| br-007 | BLACK Rose x Love Hurts Basketball Shorts | $65 | Active |
| br-008 | BLACK is Beautiful Jersey Series: 1. SF Inspired (Football) | $115 | Pre-Order |
| br-009 | BLACK is Beautiful Jersey Series: 2. Last Oakland (Football) | $115 | Pre-Order |
| br-010 | BLACK is Beautiful Jersey Series: 3. The Bay (Basketball) | $100 | Pre-Order |
| br-011 | BLACK is Beautiful Jersey Series: 4. The Rose (Hockey) | $115 | Pre-Order |
| br-012 | BLACK is Beautiful Jersey Series: 5. Last Oakland (Baseball) | $100 | Pre-Order |

### LOVE HURTS (4 products)

| SKU | Name | Price | Status |
|-----|------|-------|--------|
| lh-002 | Love Hurts Joggers | $95 | Active |
| lh-003 | Love Hurts Basketball Shorts | $75 | Active |
| lh-004 | Love Hurts Bomber Jacket | $265 | Active |
| lh-005 | The Fannie | $45 | Pre-Order |

### SIGNATURE (12 products)

| SKU | Name | Price | Status |
|-----|------|-------|--------|
| sg-001 | The Bridge Series 'The Bay Bridge' Shorts | $195 | Pre-Order |
| sg-002 | The Bridge Series 'Stay Golden' Shirt | $65 | Pre-Order |
| sg-003 | The Bridge Series 'Stay Golden' Shorts | $65 | Pre-Order |
| sg-005 | The Bridge Series 'The Bay Bridge' Shirt | $25 | Pre-Order |
| sg-006 | Mint & Lavender Hoodie | $45 | Active |
| sg-007 | The Signature Beanie | $25 | Active |
| sg-009 | The Sherpa Jacket | $80 | Active |
| sg-011 | Original Label Tee (White) | $30 | Active |
| sg-012 | Original Label Tee (Orchid) | $30 | Active |
| sg-013 | Mint & Lavender Crewneck | $40 | Active |
| sg-014 | Mint & Lavender Sweatpants | $45 | Active |
| sg-015 | The Windbreaker Set | $85 | Pre-Order |

### KIDS CAPSULE (2 products)

| SKU | Name | Price | Status |
|-----|------|-------|--------|
| kids-001 | Kids Colorblock Hoodie Set — Red/Black | $65 | Active |
| kids-002 | Kids Colorblock Hoodie Set — Purple/Black | $65 | Active |

## Retired SKUs — NEVER resurrect

`lh-001` (legacy The Fannie code — renumbered to lh-005), the old `lh-005 Love Hurts Windbreaker` (erased), `sg-004 The Signature Hoodie` (deleted), `sg-008`, `sg-010`, `br-d01..d04`, `sg-d01..d04`. Historical references in docs/tests are acceptable; production code and customer-facing copy must not mention these codes.

## CSV schema (21 columns)

`sku, name, price, collection, description, badge, image, front_model_image, back_image, back_model_image, sizes, color, edition_size, published, is_preorder, branding_spec, render_output_slug, render_source_override, render_back_source_override, render_is_tech_flat, render_is_accessory`

Booleans use `1` / `0`. Badge is free text (`Pre-Order`, `Draft`, or empty = Active). Image paths in the `image` / `front_model_image` / `back_image` / `back_model_image` columns are theme-relative (e.g. `assets/images/products/br-001-crewneck.png`). Render override paths (`render_source_override`, `render_back_source_override`) are bare filenames relative to the theme products dir.

## How agents should read the catalog

**Python agents:**
```python
from skyyrose.elite_studio.catalog import Catalog
cat = Catalog.load()
p = cat.require("lh-005")
print(p.name, p.branding_summary)
```

**Nano Banana / imagery pipeline:**
```python
from scripts.nano_banana.catalog import load_catalog
catalog = load_catalog()
```

**PHP (WP theme):**
```php
$product = skyyrose_get_product( 'sg-015' );
$all     = skyyrose_get_product_catalog();
```

## Pre-Order rules (current — 13 SKUs)

**Black Rose Pre-Order:** Sherpa Jacket (br-006) + full Jersey Series (br-003 Baseball Classic, br-008 SF Football, br-009 Last Oakland Football, br-010 The Bay Basketball, br-011 The Rose Hockey, br-012 Last Oakland Baseball).
**Love Hurts Pre-Order:** The Fannie only (lh-005).
**Signature Pre-Order:** Bridge Series (sg-001/002/003/005) + Windbreaker (sg-015).
**Kids:** none pre-order.

Everything else is **Active** — published, shoppable, not gated on pre-order checkout. 0 items in `Draft` status.

## Brand copy rules (reminder)

- **Only tagline:** "Luxury Grows from Concrete."
- **Retired tagline (NEVER use):** "Where Love Meets Luxury"
- **Brand name:** SkyyRose (one word). "Skyy Rose" is only correct when referring to the founder's daughter by name.
- Founder: Corey Foster.
