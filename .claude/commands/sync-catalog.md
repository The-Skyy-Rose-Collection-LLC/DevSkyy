# sync-catalog

Validate catalog/registry consistency, optionally apply auto-fixes, and surface files needing human review.

## What this does

1. Runs `validate_catalog_consistency.py` (read-only, exit 0 on clean)
2. If failures found, runs `sync_catalog_downstream.py --dry-run` to preview auto-fixes
3. Asks user to confirm before applying fixes
4. After sync, re-runs validator to confirm clean
5. Reports any files requiring human / sweep-agent review

## Usage

```
/sync-catalog            # validate + offer to sync
/sync-catalog --fix      # validate + auto-fix without confirmation prompt
/sync-catalog --dry-run  # validate + preview sync only, no writes
/sync-catalog --check <name>  # run a single named check
```

## Available check names

Run `python scripts/validate_catalog_consistency.py --checks <name>` for any of:

- `csv_readable` — CSV file present and well-formed
- `registry_readable` — logo-registry.json present and valid JSON
- `registry_version` — registry version >= 4
- `registry_changelog` — changelog entries have required fields
- `jersey_skus` — `_JERSEY_SKUS` frozenset in sku_resolver.py matches CSV jersey rows
- `logo_skus` — every SKU in sku_logos block exists in CSV
- `sku_folders` — every SKU in sku_folders is a known jersey SKU
- `collocated_keys` — co-located logos use `filename` key (not `file`)
- `similarities_skus` — top-level SKU keys in product-similarities.json exist in CSV
- `similarities_refs` — all similarity array SKU refs exist in CSV
- `retired_sku_guard` — no retired SKUs (br-013) appear in downstream files
- `dossier_slugs` — dossier_slug values in CSV have matching .md files
- `brand_primary` — brand_primary logo id exists in logos block

## Invoke as agent

```bash
python scripts/validate_catalog_consistency.py
# If failures:
python scripts/sync_catalog_downstream.py --dry-run
# After reviewing dry-run output:
python scripts/sync_catalog_downstream.py
# Re-validate:
python scripts/validate_catalog_consistency.py
```

## Constraints

- Does NOT edit dossier prose (.md files in data/dossiers/)
- Does NOT rewrite logo-registry.json content beyond the `updated:` date field
- Does NOT touch ProductCatalogTest.php
- Creates `.bak-pre-sync-YYYYMMDD-HHMMSS` backups before any write
- Requires explicit `y/yes` confirmation before writes (STOP AND SHOW protocol)

## When to run

- After adding, renaming, or retiring any SKU in skyyrose-catalog.csv
- After updating logo-registry.json (new logos, sku_logos, sku_folders changes)
- After the cleanup-sweep agent runs
- Before any deploy to skyyrose.co touching product data
- When the pre-commit hook blocks a commit with catalog-related failures
