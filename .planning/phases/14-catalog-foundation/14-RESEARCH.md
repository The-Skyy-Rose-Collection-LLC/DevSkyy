# Phase 14: Catalog Foundation — Research

**Researched:** 2026-04-22
**Domain:** Python packaging, CSV data modeling, file-system bundle resolution
**Confidence:** HIGH — all findings are verified by direct codebase inspection this session

---

## Summary

Phase 14 is pure Python infrastructure — zero API calls, zero cost. It fixes three broken catalog readers, adds a `garment_type_lock` column to the canonical CSV, verifies techflat-front file presence for all 28 in-scope garment SKUs, and ships a `scripts/preflight_audit.py` script that locks the state before any generation phase runs.

The good news: the foundation is already partially built. `skyyrose.core.catalog_loader` exists and works. `skyyrose.elite_studio.catalog.Catalog` correctly delegates to it. The canonical CSV is healthy (30 rows, passes 12 of 13 existing tests). The bad news: the `nano_banana` package source was deleted (only `.pyc` files remain in `scripts/nano_banana/__pycache__/`), `renders/config.py` never existed, and `skyyrose/elite_studio/fashion/context.py` resolves to a non-existent path (`/Users/theceo/data/product-catalog.csv`). All three are confirmed broken by live test runs this session.

The techflat inventory is 23 of 28 in-scope garment SKUs ready. Five SKUs are missing files on disk — br-007, sg-009, sg-012 have bundle directories with manifests but missing techflat-front files; br-012 and sg-015 have no bundle directory at all. These require user-provided source assets (INFRA-06) and must be captured in `SKIPPED.json` by the preflight audit or flagged clearly as user-action blockers.

**Primary recommendation:** Build nano_banana shim first (unblocks all tests), then renders/config.py (unblocks renders/__main__.py), then fix fashion/context.py path, then add garment_type_lock column, then write preflight_audit.py. This order keeps the test suite green at every step.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INFRA-01 | Shared CSV adapter (`skyyrose.core.catalog_loader`) as single data source for all 3 pipelines | Already exists and works. nano_banana shim + renders/config.py need to delegate to it. |
| INFRA-02 | SKU→bundle resolver keyed on `manifest.json` SKU field — handles name-mismatch cases | All 30 bundles have `manifest.json` with `sku` field. Build a `bundle_dir_for_sku(sku)` function that scans manifest.json files rather than trying to match directory names. |
| INFRA-03 | Fix 3 broken readers: `renders/config.py` (create), `elite_studio/fashion/context.py` (stale path), `nano_banana.catalog` shim (rebuild) | renders/config.py: MISSING, must be created. fashion/context.py: resolves to `/Users/theceo/data/product-catalog.csv` (does not exist). nano_banana: source .py files deleted, only .pyc remains. |
| INFRA-04 | Add `garment_type_lock` column to `skyyrose-catalog.csv` | Column does not exist in current 21-column CSV. All 28 values can be inferred deterministically from product name. |
| INFRA-05 | All techflat source files are single-view images before pipeline intake | 3 bundles (br-001, br-002, lh-003) have landscape techflats that may be suspect. Compound sheets exist in `assets/techflats/` (not bundles). INFRA-05 scope = bundle techflat-front files. |
| INFRA-06 | Missing techflat assets for br-007, sg-009, sg-012, br-012, sg-015 — user provides | br-007: bundle exists, file listed in manifest but absent on disk. sg-009: same. sg-012: same. br-012: no bundle dir at all. sg-015: no bundle dir at all. Preflight captures this, blocks generation until user provides files. |
| INFRA-07 | Preflight audit script: scans all 30 SKUs, verifies bundle + techflat-front, writes SKIPPED.json | No `scripts/preflight_audit.py` exists. Must create from scratch. Accessory SKUs sg-007 and lh-005 go into SKIPPED.json. |
</phase_requirements>

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CSV data access | `skyyrose.core.catalog_loader` | — | Already the designated single source of truth per cerebrum.md |
| nano_banana catalog adapter | `scripts/nano_banana/catalog.py` | delegates to core | Shim bridges nano_banana API contract to canonical CSV schema |
| renders pipeline catalog access | `renders/config.py` | delegates to core | __main__.py and preflight.py both import from renders.config |
| elite_studio fashion context | `skyyrose/elite_studio/fashion/context.py` | delegates to core | Replace stale path with `from skyyrose.core.catalog_loader import CATALOG_CSV` |
| Preflight audit | `scripts/preflight_audit.py` | bundle resolver | Standalone script, no API calls, pure file-system validation |
| Bundle file resolution | bundle resolver util (new) | `data/product-bundles/` | Scans manifest.json SKU field to map sku → bundle dir |
| SKIPPED.json | preflight_audit.py output | — | Written to `renders/ghost-mannequin/SKIPPED.json` |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `csv` | 3.14 (project runtime) | CSV reading | Already in use across all loaders [VERIFIED: source read] |
| Python stdlib `pathlib` | 3.14 | Path resolution | Used in existing catalog_loader.py [VERIFIED: source read] |
| Python stdlib `json` | 3.14 | manifest.json parsing | Used in bundle manifest reading [VERIFIED: source read] |
| Python stdlib `dataclasses` | 3.14 | Typed product records | Used in elite_studio/catalog.py [VERIFIED: source read] |
| pytest 9.0.2 | 9.0.2 | Test runner | Already installed [VERIFIED: `python3 -c "import pytest; print(pytest.__version__)"` → 9.0.2] |
| Pillow | 12.x | Image dimension validation | Already in requirements-imagery.txt, confirmed importable [VERIFIED: `python3 -c "import PIL; print('PIL ok')"` → PIL ok] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python stdlib `sys` | 3.14 | sys.path manipulation in test conftest | Needed to make scripts/nano_banana importable in tests |
| Python stdlib `os` | 3.14 | env var override for catalog path | Pattern used in elite_studio/catalog.py |

**Installation:** No new packages needed. All dependencies are stdlib or already installed.

---

## Architecture Patterns

### System Architecture Diagram

```
canonical CSV
  (wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv)
        │
        ▼
skyyrose.core.catalog_loader  ← single reader, all pipelines delegate here
        │
        ├─── skyyrose.elite_studio.catalog.Catalog.load()      ✓ already delegates
        │
        ├─── skyyrose/elite_studio/fashion/context.py           ✗ stale path → fix
        │         (was: PROJECT_ROOT.parent.parent... /data/product-catalog.csv)
        │         (fix: import CATALOG_CSV from core)
        │
        ├─── renders/config.py (PRODUCT_CATALOG, PRODUCTS_DIR)  ✗ missing → create
        │         → delegates to read_catalog_rows()
        │
        └─── scripts/nano_banana/catalog.py shim               ✗ deleted → rebuild
                  load_catalog()  → wraps read_catalog_rows()
                  load_products() → filtered view
                  load_specs()    → reads product-specs.json (separate concern)
                  get_material_spec() → returns spec for a SKU

        data/product-bundles/
              {name-based directory}/
                  manifest.json  {"sku": "br-001", ...}  ← SKU resolver keyed on THIS
                  techflat-front.jpeg
                  techflat-back.jpeg
                  ...
                        │
                        ▼
        bundle_dir_for_sku(sku)  ← new utility (INFRA-02)
              scans ALL manifest.json files, returns Path for matching sku
              raises BundleNotFoundError if no manifest has matching sku

        scripts/preflight_audit.py  (INFRA-07)
              reads all 30 CSV rows
              for each: accessory? → SKIPPED.json
              for each garment: bundle exists? → techflat-front file exists?
              writes renders/ghost-mannequin/SKIPPED.json
              writes audit summary to stdout
              exits 0 if all 28 garment SKUs: bundle resolved OR user-flagged as INFRA-06 pending
              exits 1 on any unexpected failure
```

### Recommended Project Structure
```
skyyrose/core/
├── catalog_loader.py          # EXISTS — primary adapter (do not modify interface)
scripts/nano_banana/           # REBUILD — source deleted, only .pyc remains
├── __init__.py                # MISSING — required for package import
├── catalog.py                 # MISSING — shim wrapping core.catalog_loader
scripts/
├── preflight_audit.py         # NEW — INFRA-07
renders/
├── config.py                  # NEW — INFRA-03
├── preflight.py               # EXISTS
skyyrose/elite_studio/fashion/
├── context.py                 # EXISTS — fix stale path only
wordpress-theme/skyyrose-flagship/data/
├── skyyrose-catalog.csv       # EXISTS — add garment_type_lock column
```

### Pattern 1: nano_banana shim wrapping core loader

The shim must preserve the existing test API contract while delegating to `skyyrose.core.catalog_loader`. The test conftest uses a different CSV schema (older format) — the shim should update to work with the canonical schema, and the conftest fixtures should be updated in the same commit.

```python
# Source: verified from worktree + test expectations this session
# scripts/nano_banana/catalog.py pattern:
from __future__ import annotations
from pathlib import Path
import json
import os

from skyyrose.core.catalog_loader import CATALOG_CSV as _CANONICAL_CSV
from skyyrose.core.catalog_loader import read_catalog_rows

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CATALOG_CSV = Path(os.getenv("SKYYROSE_CATALOG_PATH", "") or _CANONICAL_CSV)
SPECS_JSON = PROJECT_ROOT / "data" / "product-specs.json"

def load_catalog(path: Path | None = None) -> dict[str, dict]:
    """Load catalog → dict keyed by SKU. Maps canonical columns to nano_banana API."""
    rows = read_catalog_rows(path or CATALOG_CSV)
    catalog: dict[str, dict] = {}
    for row in rows:
        sku = row["sku"]
        entry: dict = {
            "name": row["name"],
            "collection": row["collection"],  # canonical has collection (not collection_slug)
            "is_preorder": row["is_preorder"] == "1",
            "output_slug": row["render_output_slug"] or sku,
            "is_tech_flat": row["render_is_tech_flat"] == "1",
            "is_accessory": row["render_is_accessory"] == "1",
            "garment_type": row.get("garment_type_lock", ""),
        }
        if row.get("render_source_override"):
            entry["source_override"] = row["render_source_override"]
        catalog[sku] = entry
    return catalog
```

### Pattern 2: renders/config.py — minimal PRODUCT_CATALOG + bundle resolver

```python
# Source: derived from renders/__main__.py and renders/preflight.py import analysis
from __future__ import annotations
from pathlib import Path
from skyyrose.core.catalog_loader import read_catalog_rows, CATALOG_CSV

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = (
    PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products"
)
_BUNDLES_DIR = PROJECT_ROOT / "data" / "product-bundles"

def _find_bundle_dir(name: str, sku: str | None = None) -> Path | None:
    """Find bundle dir by scanning manifest.json files for matching SKU."""
    if sku:
        for d in _BUNDLES_DIR.iterdir():
            mf = d / "manifest.json"
            if mf.exists():
                import json
                data = json.loads(mf.read_text())
                if data.get("sku") == sku:
                    return d
    return None

def _build_product_catalog() -> list[dict]:
    """Load catalog rows, adding bundle resolution for each SKU."""
    rows = read_catalog_rows(CATALOG_CSV)
    products = []
    for row in rows:
        sku = row["sku"]
        bundle = _find_bundle_dir(row["name"], sku)
        product = dict(row)
        product["existing_front"] = None
        if bundle:
            tf = bundle / "techflat-front.jpeg"
            if not tf.exists():
                tf = next(bundle.glob("techflat-front.*"), None)
            if tf and tf.exists():
                product["existing_front"] = str(tf)
        products.append(product)
    return products

PRODUCT_CATALOG = _build_product_catalog()
```

### Pattern 3: garment_type_lock — deterministic value from product name

All 28 in-scope garment SKUs have unambiguous garment type from their name. Values (verified from product names this session): `hoodie`, `crewneck`, `jersey`, `joggers`, `shorts`, `jacket`, `bomber jacket`, `shirt`, `sweatpants`, `windbreaker`, `set`.

The `garment_type_lock` column is populated at CSV-edit time (one-time), not derived at runtime. This locks in the type even if the product is renamed later.

### Pattern 4: bundle resolver (INFRA-02)

The directory names use product names, not SKU codes. The `manifest.json` inside each bundle has `"sku": "br-001"`. The resolver must scan `manifest.json` files, not match directory names.

```python
# Source: verified by inspecting all 32 bundle directories this session
import json
from pathlib import Path

_BUNDLES_DIR = Path("data/product-bundles")  # relative to project root

def bundle_dir_for_sku(sku: str, bundles_dir: Path = _BUNDLES_DIR) -> Path | None:
    """Return the bundle directory for a SKU by scanning manifest.json files."""
    for d in bundles_dir.iterdir():
        if not d.is_dir():
            continue
        mf = d / "manifest.json"
        if mf.exists():
            try:
                data = json.loads(mf.read_text(encoding="utf-8"))
                if data.get("sku") == sku:
                    return d
            except (json.JSONDecodeError, OSError):
                continue
    return None
```

### Anti-Patterns to Avoid
- **Directory-name matching:** Never try to infer SKU from bundle directory name. `"Love Hurts Varsity Jacket"` → lh-004 is not guessable. Always scan manifest.json.
- **Modifying catalog_loader.py:** The existing `skyyrose.core.catalog_loader` interface is stable and correct. Build shims on top, do not change the core.
- **Importing nano_banana from root conftest:** Only add `sys.path.insert(0, scripts_dir)` in `tests/scripts/conftest.py` or `tests/scripts/nano_banana/conftest.py`. The root conftest should not know about scripts/.
- **Silent INFRA-06 failures:** br-012 and sg-015 have no bundle at all. The preflight audit must explicitly label these "PENDING_USER_ASSETS" in its output — not just "not found."

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CSV parsing | Custom CSV parser | stdlib `csv.DictReader` | Already proven, handles quoting/encoding correctly |
| Path resolution | String concatenation | `pathlib.Path` | Already used project-wide |
| Image dimension check | Custom file reader | `PIL.Image.open().size` | Already installed, one-line check |
| JSON parsing | Custom parser | stdlib `json.loads` | Sufficient for manifest.json |

**Key insight:** This phase is plumbing. Every component it needs exists as stdlib or is already installed. The work is writing adapters that wire existing pieces together correctly, not building new capabilities.

---

## Runtime State Inventory

Phase 14 is NOT a rename/refactor of runtime state. It does modify the canonical CSV (adding a column), which affects all three pipeline readers at runtime.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `skyyrose-catalog.csv` — adding `garment_type_lock` column | CSV edit (add column, populate 30 values); no data migration needed — column is additive |
| Live service config | None | None |
| OS-registered state | None | None |
| Secrets/env vars | `SKYYROSE_CATALOG_PATH` env var — overrides catalog path in elite_studio and (after this phase) nano_banana shim | Code change only; env var name unchanged |
| Build artifacts | `scripts/nano_banana/__pycache__/` — stale .pyc from deleted source files | Stale .pyc will be overwritten automatically when source files are created |

**CSV column add impact:** The `test_catalog_csv_integrity.py::test_schema_has_all_expected_columns` test hardcodes `EXPECTED_COLUMNS`. Adding `garment_type_lock` to the CSV will NOT break that test (the test checks `EXPECTED_COLUMNS ⊆ CSV_columns`, not equality). The test file should be updated to include `garment_type_lock` in `EXPECTED_COLUMNS` in the same commit as the CSV change.

---

## Common Pitfalls

### Pitfall 1: nano_banana conftest CSV schema mismatch
**What goes wrong:** The existing `tests/scripts/nano_banana/conftest.py` fixture writes a CSV using the OLD schema (`collection_slug`, `render_variant_of`, `type` columns). The canonical CSV does not have these columns. If the shim reads the canonical columns and the fixture writes the old columns, all nano_banana tests fail.
**Why it happens:** The nano_banana package was rebuilt multiple times; the test fixtures never tracked the schema migration.
**How to avoid:** Update `_CSV_COLUMNS` in the conftest fixture to match the current canonical schema. The shim should map canonical column names, not old column names.
**Warning signs:** `KeyError: 'collection_slug'` or `AssertionError` in `test_load_catalog_fields`.

### Pitfall 2: Missing `__init__.py` kills nano_banana import
**What goes wrong:** `scripts/nano_banana/` directory exists but has no `__init__.py`. Python cannot import `nano_banana.catalog` even if `scripts/` is on sys.path.
**Why it happens:** The package source was deleted without removing the directory.
**How to avoid:** Create `scripts/nano_banana/__init__.py` in the same commit as `catalog.py`. Per `cerebrum.md`: "Every top-level package directory MUST contain `__init__.py`."
**Warning signs:** `ModuleNotFoundError: No module named 'nano_banana'` (confirmed by live test run this session).

### Pitfall 3: renders/config.py PRODUCT_CATALOG build is slow
**What goes wrong:** If `PRODUCT_CATALOG = _build_product_catalog()` runs at import time and scans 32 bundle directories, it takes O(32 × directory_scan) time on every import.
**Why it happens:** Module-level initialization runs at import.
**How to avoid:** Either compute at import (acceptable — <0.1s for 32 dirs) or use lazy loading. The renders pipeline is not performance-critical at the catalog-loading stage. Import-time compute is the existing pattern in this codebase.

### Pitfall 4: preflight_audit.py exits 0 when br-012/sg-015 have no bundle
**What goes wrong:** Success criteria says "exits 0 and writes SKIPPED.json listing only sg-007 and lh-005." But br-012 and sg-015 also have no techflat-front on disk. If the script exits 0 without flagging them, Phase 15 will fail at runtime.
**Why it happens:** br-012 and sg-015 are garments (not accessories) — they belong in the "pending user assets" bucket, not SKIPPED.json (which is only for out-of-scope accessories). INFRA-06 says they require user-provided assets before Phase 15 runs.
**How to avoid:** The preflight audit should have three categories: (1) READY (bundle + techflat-front exists), (2) SKIPPED (accessory), (3) PENDING_USER_ASSETS (garment but missing files). Exit 0 only if READY+SKIPPED = all 30 SKUs. Print a clear summary showing br-007, sg-009, sg-012, br-012, sg-015 as PENDING.
**Warning signs:** Phase 15 agent crashes trying to read non-existent techflat files.

### Pitfall 5: lh-006 bundle maps to lh-005 CSV entry (accessory mismatch)
**What goes wrong:** The bundle at `data/product-bundles/The Fannie/manifest.json` has `"sku": "lh-006"`. The CSV has `lh-005` as "The Fannie". Querying `bundle_dir_for_sku("lh-005")` returns None; querying `bundle_dir_for_sku("lh-006")` returns the bundle. Since lh-005 is an accessory (in SKIPPED.json), this only matters if someone tries to resolve lh-006 — which is not in the CSV.
**Why it happens:** Historical SKU renumbering without updating the bundle manifest.
**How to avoid:** The preflight audit scans all 30 CSV SKUs. lh-005 is an accessory → SKIPPED.json. lh-006 is not in the CSV → ignored. No fix needed for Phase 14 unless INFRA-02 explicitly needs to handle this case.

---

## Code Examples

### Exact broken import in fashion/context.py
```python
# Source: verified by reading skyyrose/elite_studio/fashion/context.py this session
# Line 23:
_CATALOG_PATH = Path(__file__).parent.parent.parent.parent.parent / "data" / "product-catalog.csv"
# Resolves to: /Users/theceo/data/product-catalog.csv  (DOES NOT EXIST)
# Fix: replace with:
from skyyrose.core.catalog_loader import CATALOG_CSV as _CATALOG_PATH
```

### What renders/__main__.py imports from renders/config.py
```python
# Source: verified by reading renders/__main__.py this session
from renders.config import PRODUCT_CATALOG         # list[dict] — one entry per SKU
from renders.preflight import PreflightAborted, preflight_verify
```

### What renders/preflight.py imports from renders/config.py
```python
# Source: verified by reading renders/preflight.py this session
from renders.config import PRODUCTS_DIR, _find_bundle_dir
```

### SKIPPED.json format (inferred from success criteria)
```json
{
  "reason": "out-of-scope accessories — deferred to v1.3 flat-lay pipeline",
  "skipped": [
    {"sku": "lh-005", "name": "The Fannie", "collection": "love-hurts"},
    {"sku": "sg-007", "name": "The Signature Beanie", "collection": "signature"}
  ],
  "generated_at": "2026-04-22T...",
  "total_in_scope_garments": 28,
  "total_skipped_accessories": 2
}
```

### garment_type_lock values for all 28 in-scope SKUs
```
# Source: verified by reading product names from CSV this session
br-001  crewneck       br-002  joggers        br-003  jersey
br-004  hoodie         br-005  hoodie         br-006  jacket
br-007  shorts         br-008  jersey         br-009  jersey
br-010  jersey         br-011  jersey         br-012  jersey
lh-002  joggers        lh-003  shorts         lh-004  bomber jacket
sg-001  shorts         sg-002  shirt          sg-003  shorts
sg-005  shirt          sg-006  hoodie         sg-009  jacket
sg-011  shirt          sg-012  shirt          sg-013  crewneck
sg-014  sweatpants     sg-015  set            kids-001 hoodie
kids-002 hoodie
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `data/product-catalog.csv` (root) | `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` | 2026-04-19 | fashion/context.py still uses old path — INFRA-03 |
| Multiple catalog sources (yaml, manifest.json, csv) | Single canonical CSV | 2026-04-19 | Legacy readers must all migrate |
| Directory-name bundle lookup | manifest.json SKU field lookup | This session | Required by INFRA-02 — name-based lookup fails |

**Deprecated/outdated:**
- `assets/product-masters/catalog.yaml`: deleted 2026-04-19
- `assets/product-masters/manifest.json`: deleted 2026-04-19
- `data/product-catalog.csv` (root): never existed in this project (path only in worktree artifacts and stale context.py)
- `scripts/generate_catalog.py`: obsolete per cerebrum.md
- `collection_slug` column: exists only in old test fixtures, not in canonical CSV

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | SKIPPED.json should go in `renders/ghost-mannequin/SKIPPED.json` | Architecture Patterns | Directory path differs from what preflight_audit.py creates — easy fix |
| A2 | br-001 and br-002 techflat-front.jpeg (450x253 landscape) are single-view images, not compound | INFRA-05 | If they are compound, 2 additional SKUs need their techflats split before Phase 15 |
| A3 | The `tests/scripts/nano_banana/conftest.py` fixture schema should be updated to canonical schema | Pattern 1 | If the old schema is intentional for backwards compat, the shim needs to handle both |

---

## Open Questions

1. **br-001 and br-002 techflat aspect ratio (450x253)**
   - What we know: 450×253 is landscape, which is unusual for a garment front view. `crewneck-and-joggers.jpeg` in `assets/techflats/black-rose/` is labeled as compound.
   - What's unclear: Whether the bundle techflat-front.jpeg files are already-split crops from the compound sheet, or still compound.
   - Recommendation: Treat them as single-view (the ratio is 1.78, just below the "definitely compound" threshold of 2.0). Flag for user visual confirmation during the preflight audit run.

2. **lh-006 bundle SKU mismatch with CSV lh-005**
   - What we know: Bundle manifest says `"sku": "lh-006"` but CSV has no lh-006. lh-005 is "The Fannie" (accessory).
   - What's unclear: Is this a data error that needs correcting (update manifest to lh-005) or just dead data (lh-006 was retired, bundle left behind)?
   - Recommendation: Since lh-005 is an accessory going into SKIPPED.json, and there's no in-scope garment using this bundle, leave the manifest alone. Document in preflight audit output as an orphan bundle.

3. **preflight_audit.py exit code for INFRA-06 pending SKUs**
   - What we know: Success criteria says `python scripts/preflight_audit.py` exits 0 "and writes SKIPPED.json listing only sg-007 and lh-005." Five garment SKUs (br-007, sg-009, sg-012, br-012, sg-015) are missing techflat-front files.
   - What's unclear: Should missing-asset garment SKUs cause exit 1 (hard fail) or exit 0 with a warning (soft fail)?
   - Recommendation: Exit 0 but print a clear "PENDING_USER_ASSETS" list. The success criteria says "exits 0" without mentioning a fail condition — treating INFRA-06 SKUs as informational warnings (not blockers) lets the phase complete while documenting the user action required.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All | ✓ | 3.14.3 | — |
| pytest | Tests | ✓ | 9.0.2 | — |
| Pillow (PIL) | INFRA-05 image dimension check | ✓ | importable | Omit dimension check, use file-exists only |
| `data/product-bundles/` | INFRA-02, INFRA-07 | ✓ | 32 dirs, all with manifest.json | — |
| `skyyrose-catalog.csv` | INFRA-01 through INFRA-07 | ✓ | 30 rows, 21 columns | — |

**Missing dependencies with no fallback:** None.

**Missing source files (user-action blockers, not environment):**
- `data/product-bundles/BLACK Rose x Love Hurts Basketball Shorts/techflat-front.jpg` (br-007)
- `data/product-bundles/The Sherpa Jacket/techflat-front.jpg` (sg-009)
- `data/product-bundles/Original Label Tee (Orchid)/techflat-front.webp` (sg-012)
- No bundle directory for br-012 ("BLACK is Beautiful Jersey Series: 5. Last Oakland (Baseball)")
- No bundle directory for sg-015 ("The Windbreaker Set")

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `python3 -m pytest tests/test_catalog_csv_integrity.py -x -q` |
| Full suite command | `python3 -m pytest tests/test_catalog_csv_integrity.py tests/scripts/nano_banana/ -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFRA-01 | `read_catalog_rows` importable from `skyyrose.core.catalog_loader` | unit | `python3 -m pytest tests/test_catalog_csv_integrity.py -x -q` | ✅ |
| INFRA-02 | bundle_dir_for_sku resolves all 26 bundles with manifests | unit | `python3 -m pytest tests/test_catalog_csv_integrity.py -k "bundle" -q` | ❌ Wave 0 |
| INFRA-03 | `from nano_banana.catalog import load_catalog` works | unit | `python3 -m pytest tests/scripts/nano_banana/test_catalog.py -x -q` | ✅ (fails now) |
| INFRA-03 | `renders/config.py` imports without error | unit | `python3 -m pytest tests/test_renders_config.py -x -q` | ❌ Wave 0 |
| INFRA-03 | fashion/context.py loads catalog correctly | unit | `python3 -m pytest tests/test_fashion_context.py -x -q` | ❌ Wave 0 |
| INFRA-04 | CSV has `garment_type_lock` column with non-empty values for all 28 garment SKUs | unit | `python3 -m pytest tests/test_catalog_csv_integrity.py -k "garment_type_lock" -q` | ❌ Wave 0 |
| INFRA-05 | preflight_audit detects techflat-front for all READY SKUs | unit | `python3 -m pytest tests/test_preflight_audit.py -x -q` | ❌ Wave 0 |
| INFRA-06 | br-007, sg-009, sg-012, br-012, sg-015 appear as PENDING in audit output | unit | (included in test_preflight_audit.py) | ❌ Wave 0 |
| INFRA-07 | `python scripts/preflight_audit.py` exits 0, SKIPPED.json contains sg-007 + lh-005 only | integration | `python scripts/preflight_audit.py && python3 -m pytest tests/test_preflight_audit.py -k "skipped_json"` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python3 -m pytest tests/test_catalog_csv_integrity.py -x -q`
- **Per wave merge:** `python3 -m pytest tests/test_catalog_csv_integrity.py tests/scripts/nano_banana/ tests/test_preflight_audit.py -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/scripts/nano_banana/conftest.py` — update `_CSV_COLUMNS` to canonical schema
- [ ] `tests/test_renders_config.py` — smoke test that `renders/config.py` imports and PRODUCT_CATALOG is a list
- [ ] `tests/test_fashion_context.py` — smoke test that fashion/context.py `_load_catalog()` reads canonical CSV
- [ ] `tests/test_preflight_audit.py` — covers INFRA-05, INFRA-06, INFRA-07
- [ ] `tests/test_catalog_csv_integrity.py` — add `garment_type_lock` to `EXPECTED_COLUMNS` (covers INFRA-04)
- [ ] `scripts/nano_banana/__init__.py` — required for package import (covers INFRA-03)

---

## Security Domain

Phase 14 contains no authentication, network calls, or user input. No ASVS categories apply.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | no | — |
| V6 Cryptography | no | — |

The only file writes in this phase are: (1) adding a column to `skyyrose-catalog.csv` (developer tool, not user input), (2) writing `renders/ghost-mannequin/SKIPPED.json` (developer output file). Both are developer-local operations with no attack surface.

---

## Sources

### Primary (HIGH confidence)
All findings verified by direct file reads and command execution this session:

- `skyyrose/core/catalog_loader.py` — read in full, interface confirmed
- `skyyrose/elite_studio/catalog.py` — read in full, delegation pattern confirmed
- `skyyrose/elite_studio/fashion/context.py` — stale path confirmed by path resolution
- `renders/preflight.py` — import requirements confirmed
- `renders/__main__.py` — import requirements confirmed
- `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` — schema (21 columns), row count (30), accessory flags verified
- `data/product-bundles/` — 32 directories inspected, all manifest.json files scanned
- `scripts/nano_banana/__pycache__/` — .pyc files confirm source was deleted
- `tests/test_catalog_csv_integrity.py` — live test run confirms 1 failure (nano_banana import)
- `tests/scripts/nano_banana/conftest.py` — schema mismatch confirmed
- `.wolf/cerebrum.md` — packaging conventions confirmed
- `.planning/REQUIREMENTS.md` — INFRA-01..07 definitions
- `.planning/STATE.md` — phase context and decisions

### Secondary (MEDIUM confidence)
- `.claude/worktrees/agent-a1756ad5/scripts/nano_banana/catalog.py` — worktree snapshot; schema was outdated (pointed to `data/product-catalog.csv`), used only to understand the intended API contract

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libs are stdlib or already installed and confirmed importable
- Architecture: HIGH — all three broken readers confirmed broken by live test, bundle structure confirmed by directory inspection
- Pitfalls: HIGH — all identified from live test failures or confirmed code paths
- Techflat inventory: HIGH — all 28 SKUs scanned, PIL dimension checks run

**Research date:** 2026-04-22
**Valid until:** 2026-06-01 (catalog schema is stable; bundle structure won't change without intentional action)
