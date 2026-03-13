# Catalog Refactor Handoff

## What's Done
- `/Users/theceo/DevSkyy/product-catalog.csv` — new canonical CSV at project root
  - All 33 products (BR, LH, SG, Kids + br-003 variants)
  - Columns: type, sku, collection, collection_slug, name, price, is_preorder, edition_size, render_output_slug, render_source_override, render_back_source_override, render_is_tech_flat, render_is_accessory, render_variant_of
  - Source images verified against actual files in products dir
  - is_preorder corrected: sg-004=1, lh-005=0
- Old `products.csv` files NOT yet deleted

## What Needs to Happen (in order)

### 1. Add missing columns to product-catalog.csv
Add `description`, `sizes`, `color` columns — data is in:
- `/Users/theceo/Downloads/product-catalog.csv` (positions: description=pos5, sizes=pos9, color=pos12)
- `/Users/theceo/DevSkyy/wordpress-theme/skyyrose-flagship/inc/product-catalog.php` (for products missing from Downloads CSV: br-003 variants, sg-013, sg-014, kids)

### 2. Create `scripts/product_catalog.py` — shared reader
```python
import csv
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CATALOG_CSV = PROJECT_ROOT / "product-catalog.csv"

@lru_cache(maxsize=1)
def get_catalog() -> dict:
    catalog = {}
    with CATALOG_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row["sku"].strip()
            if not sku:
                continue
            catalog[sku] = {
                "name": row["name"].strip(),
                "collection": row["collection_slug"].strip(),
                "collection_label": row["collection"].strip(),
                "price": float(row["price"]) if row["price"].strip() else 0.0,
                "is_preorder": row["is_preorder"].strip() == "1",
                "edition_size": int(row["edition_size"]) if row["edition_size"].strip() else 250,
                "description": row.get("description", "").strip(),
                "sizes": row.get("sizes", "S|M|L|XL|2XL|3XL").strip(),
                "color": row.get("color", "").strip(),
                "output_slug": row["render_output_slug"].strip() or sku,
                "source_override": row["render_source_override"].strip() or None,
                "back_source_override": row["render_back_source_override"].strip() or None,
                "is_tech_flat": row["render_is_tech_flat"].strip() == "1",
                "is_accessory": row["render_is_accessory"].strip() == "1",
                "variant_of": row["render_variant_of"].strip() or None,
            }
    return catalog
```

### 3. Update `scripts/nano-banana-vton.py`
- DELETE lines 51–304 (PRODUCT_CATALOG dict, ACCESSORY_SKUS, BAD_SOURCE_SKUS, TECH_FLAT_SKUS)
- ADD at top: `from product_catalog import get_catalog`
- REPLACE all `PRODUCT_CATALOG` refs with `get_catalog()`
- REPLACE `sku in TECH_FLAT_SKUS` with `get_catalog().get(sku, {}).get("is_tech_flat", False)`
- REPLACE `sku in ACCESSORY_SKUS` with `get_catalog().get(sku, {}).get("is_accessory", False)`
- KEEP LOGO_TREATMENTS, BAD_SOURCE_SKUS (runtime quality, not catalog)
- Key lines to update: 355, 396, 446, 449, 458, 468, 1543, 1574, 1629, 2008, 2023, 2071

### 4. Update `scripts/vision_batch.py`
- DELETE lines 36–44 (importlib hack + PRODUCT_CATALOG/ACCESSORY_SKUS)
- ADD: `from product_catalog import get_catalog`
- REPLACE `PRODUCT_CATALOG` → `get_catalog()`, `ACCESSORY_SKUS` → set comprehension from catalog

### 5. Update `scripts/nano-banana-composite.py`
- DELETE lines 107–~270 (entire stale PRODUCT_CATALOG dict with wrong SKUs like po-001, br-008=hooded dress)
- ADD import from product_catalog
- Key lines: 1132, 1149

### 6. Update `scripts/nano-banana-3d.py`
- DELETE lines 64–~250 (entire PRODUCT_CATALOG dict — also has stale lh-001, po-* SKUs)
- ADD import from product_catalog
- Key lines: 305, 730, 805, 806, 824, 868, 872, 907

### 7. Update `agents/social_media_agent.py`
- DELETE lines 284–303 (stale PRODUCT_CATALOG dict — br-008=hooded dress, missing most products)
- ADD import from product_catalog
- Key lines: 464, 510, 511, 847, 1062

### 8. Update `wordpress-theme/skyyrose-flagship/inc/product-catalog.php`
Replace the hardcoded `$catalog = array(...)` in `skyyrose_get_product_catalog()` with a CSV reader:
```php
$csv_path = get_template_directory() . '/../../product-catalog.csv';
// OR copy product-catalog.csv into the theme: wordpress-theme/skyyrose-flagship/data/product-catalog.csv
// Parse CSV, build same array structure using render_output_slug to derive image paths:
// image = assets/images/products/{render_source_override}
// front_model_image = assets/images/products/{render_output_slug}-front-model.webp
// back_model_image = assets/images/products/{render_output_slug}-back-model.webp
// badge = is_preorder ? 'Pre-Order' : ''
```

### 9. Delete old CSVs
```bash
rm /Users/theceo/DevSkyy/skyyrose/assets/data/products.csv
rm /Users/theceo/DevSkyy/wordpress-theme/skyyrose-flagship/data/products.csv
```

### 10. Update docstrings
- `agents/claude_sdk/domain_agents/content.py` line 103: "nano-banana-vton.py PRODUCT_CATALOG" → "product-catalog.csv"
- `agents/claude_sdk/domain_agents/commerce.py` line 49: same

## Resume Prompt
"Resume the product catalog refactor. The new canonical CSV is at /Users/theceo/DevSkyy/product-catalog.csv.
Steps 1-9 are all documented in /Users/theceo/DevSkyy/.devskyy/handoffs/catalog-refactor.md.
Start with step 1 (add description/sizes/color to CSV), then create scripts/product_catalog.py,
then update each Python file and the PHP catalog. Delete the two old products.csv files at the end."

## Additional Files Found (background search)
Beyond the 7 core files, these also contain product SKU/catalog references:

### High priority (active code):
- `database/seed_catalog.py`
- `grpc_server/product_service.py`
- `api/v1/social_media.py`
- `frontend/lib/collections.ts`
- `frontend/app/api/products/route.ts`
- `frontend/app/api/social-media/generate/route.ts`
- `agents/product_generation/devskyy_fidelity/config.py`
- `agents/product_generation/devskyy_fidelity/test_fidelity.py`
- `agents/elite_web_builder/run.py`
- `skyyrose/elite_studio/agents/compositor_agent.py`
- `skyyrose/elite_studio/agents/generator_agent.py`
- `skyyrose/elite_studio/cli.py`
- `skyyrose/multi_agent/__main__.py`
- `skyyrose/skyyrose_content_agent.py`
- `scripts/composite_products.py`
- `scripts/gemini_product_gen.py`
- `scripts/gemini_lookbook.py`
- `scripts/run_compositor_pipeline.py`
- `scripts/build_lora_v4_dataset.py`

### Lower priority (build/legacy scripts):
- `skyyrose/build/*.py` and `skyyrose/build/*.js` (build-time only)
- Test files in `tests/` (may need updating after main code changes)

### Skip (compiled/cached):
- `frontend/.next/` (compiled output — rebuild after source changes)
- `.mypy_cache/` (type cache — auto-regenerated)
- `skyyrose/assets/data/*.json` (generated data files, not source)
