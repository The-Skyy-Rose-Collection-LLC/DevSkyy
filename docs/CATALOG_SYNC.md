# Catalog Consistency & Auto-Sync

Enforcement system that catches drift between canonical data sources and downstream files automatically.

---

## Canonical Sources (never edit downstream files directly)

| Source | Path | What it owns |
|--------|------|-------------|
| **Product catalog** | `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` | All 33 SKUs, garment types, dossier slugs |
| **Logo registry** | `wordpress-theme/skyyrose-flagship/data/logo-registry.json` | All logos, placements, sku_logos, sku_folders |

---

## Downstream Files That Must Stay in Sync

| File | What must match | Auto-fixable? |
|------|-----------------|---------------|
| `skyyrose/elite_studio/sku_resolver.py` | `_JERSEY_SKUS` frozenset == CSV rows with jersey garment_type_lock | Yes |
| `wordpress-theme/.../data/product-similarities.json` | Top-level SKU keys + array refs must exist in CSV | Yes |
| `wordpress-theme/.../data/logo-registry.json` | `updated:` date field | Yes (timestamp only) |
| `wordpress-theme/.../data/dossiers/*.md` | `sku:` frontmatter must be a live SKU | **Human review** |
| `skyyrose/elite_studio/commerce.py` | Catalog summary prompt SKU list | **Human review** |
| `skyyrose/elite_studio/tests/ProductCatalogTest.php` | Test SKU list | **Human review** |

---

## Commands

### Check (read-only, safe everywhere)

```bash
make validate-catalog
# or
python scripts/validate_catalog_consistency.py
# single check:
python scripts/validate_catalog_consistency.py --checks jersey_skus
# JSON output (CI annotations):
python scripts/validate_catalog_consistency.py --json
```

### Preview auto-fixes (no writes)

```bash
make sync-catalog-dry
# or
python scripts/sync_catalog_downstream.py --dry-run
```

### Apply auto-fixes (backs up before writing)

```bash
make sync-catalog
# or
python scripts/sync_catalog_downstream.py
```

Backups are written as `.bak-pre-sync-YYYYMMDD-HHMMSS` alongside the original. These are in `.gitignore`.

### Run consistency tests

```bash
pytest skyyrose/elite_studio/tests/test_catalog_consistency.py -v
```

### Slash command (Claude Code)

```
/sync-catalog
```

---

## When to Run

| Trigger | Command |
|---------|---------|
| Add / rename / retire a SKU in the CSV | `make sync-catalog` |
| Update logo-registry.json (new logos, sku_logos, sku_folders) | `make validate-catalog` |
| After the cleanup-sweep agent runs | `make validate-catalog` |
| Before deploying to skyyrose.co (data changes) | `make validate-catalog` |
| Pre-commit hook blocks a commit | See hook output for exact fix command |
| CI fails on a PR touching `data/**` | `make sync-catalog-dry` to preview |

---

## Automation Layers

### 1. Pre-commit hook (`.git/hooks/pre-commit`)

Fires automatically on `git commit` when a catalog-related file is staged.

- Pre-formats staged `.py` files with ruff + black before the validator runs
- Blocks the commit if any check fails
- Prints fix instructions in the error output
- Bypass (emergency only): `SKIP_CATALOG_VALIDATE=1 git commit`

### 2. PostToolUse hook (`.claude/hooks/catalog-drift-guard.sh`)

Fires after Claude edits any catalog or registry file mid-session.

- Runs the validator in quiet mode
- **Non-blocking** — prints a warning but does not fail the tool call
- The pre-commit hook is the hard gate

### 3. CI workflow (`.github/workflows/catalog-validate.yml`)

Runs on every PR and push to `main` that touches `data/**` or `elite_studio/sku_resolver.py`.

Two jobs:
- `validate` — runs the Python validator + pytest test suite
- `retired-sku-scan` — `git grep` sweep for retired SKU strings (hard fail)

---

## Available Checks

| Check name | What it verifies |
|-----------|-----------------|
| `csv_readable` | CSV present and well-formed |
| `registry_readable` | logo-registry.json present and valid JSON |
| `registry_version` | Registry version >= 4 |
| `registry_changelog` | Changelog entries have version, date, author, notes |
| `jersey_skus` | `_JERSEY_SKUS` frozenset matches CSV jersey rows |
| `logo_skus` | Every SKU in sku_logos exists in catalog CSV |
| `sku_folders` | Every SKU in sku_folders is a jersey SKU per CSV |
| `collocated_keys` | Co-located logos use `filename` key (not `file`) |
| `similarities_skus` | Top-level SKU keys in product-similarities.json exist in CSV |
| `similarities_refs` | All SKU refs in similarity arrays exist in CSV |
| `retired_sku_guard` | No retired SKUs (br-013) appear in downstream files |
| `dossier_slugs` | All dossier_slug values have matching .md files |
| `brand_primary` | brand_primary logo id exists in the logos block |

---

## Retired SKUs

| SKU | Retired | Reason |
|-----|---------|--------|
| `br-013` | 2026-05-25 | Confirmed duplicate of br-003 (Baseball Classic Black) |

Retired SKUs must not appear in: `sku_resolver.py`, `logo-registry.json`, `product-similarities.json`, `commerce.py`, or any `scripts/*.py`.

Dossiers are excluded from the automated guard — review manually if a dossier prose references a retired SKU.

---

## Adding a New SKU

1. Add row to `skyyrose-catalog.csv` with all required columns
2. If it's a jersey: set `garment_type_lock` to a jersey type (e.g., `baseball-jersey`)
3. Run `make sync-catalog` — `_JERSEY_SKUS` and similarities.json update automatically
4. Add to `logo-registry.json` `sku_logos` block if it gets logo placements
5. If jersey: add to `logo-registry.json` `sku_folders` block with product folder name
6. Run `make validate-catalog` — should pass clean

## Retiring a SKU

1. Remove the row from `skyyrose-catalog.csv`
2. Run `make sync-catalog` — cleans downstream files automatically
3. Add the SKU to `_RETIRED_SKUS` frozenset in `scripts/validate_catalog_consistency.py`
4. Update `docs/CATALOG_SYNC.md` Retired SKUs table
5. Run `make validate-catalog` to confirm clean
6. Human review: update any dossier prose that references the retired SKU
