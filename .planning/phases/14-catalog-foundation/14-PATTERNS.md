# Phase 14: Catalog Foundation — Pattern Map

**Mapped:** 2026-04-22
**Files analyzed:** 12 (new/modified)
**Analogs found:** 12 / 12

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `scripts/nano_banana/__init__.py` | config | — | `sdk/python/agent_sdk/super_agents/__init__.py` | role-match |
| `scripts/nano_banana/catalog.py` | service | transform | `skyyrose/core/catalog_loader.py` + `.claude/worktrees` worktree snapshot | exact |
| `renders/config.py` | config | transform | `renders/preflight.py` (import style) + RESEARCH.md Pattern 2 | role-match |
| `skyyrose/elite_studio/fashion/context.py` | service | transform | self (one-line path fix) | self |
| `scripts/preflight_audit.py` | utility | file-I/O | `renders/preflight.py` + `scripts/split_techflats.py` | role-match |
| `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` | config | — | self (additive column) | self |
| `tests/test_catalog_csv_integrity.py` | test | — | self (add test cases) | self |
| `tests/scripts/nano_banana/conftest.py` | test | — | self (update `_CSV_COLUMNS`) | self |
| `tests/test_renders_config.py` | test | — | `skyyrose/elite_studio/tests/test_brand.py` | role-match |
| `tests/test_fashion_context.py` | test | — | `skyyrose/elite_studio/tests/test_brand.py` | role-match |
| `tests/test_preflight_audit.py` | test | file-I/O | `skyyrose/elite_studio/tests/test_catalog_validation.py` | role-match |

---

## Pattern Assignments

### `scripts/nano_banana/__init__.py` (config, package marker)

**Analog:** `sdk/python/agent_sdk/super_agents/__init__.py`

Project convention from `cerebrum.md` and CLAUDE.md: every package directory MUST have `__init__.py`. One-line docstring is sufficient — never an empty file.

**Pattern** (complete file content):
```python
"""nano_banana — SkyyRose AI image generation pipeline for ghost mannequin renders."""
```

---

### `scripts/nano_banana/catalog.py` (service, transform)

**Primary analog:** `skyyrose/core/catalog_loader.py` (lines 1–84) — this is the upstream the shim wraps.
**Secondary analog:** `skyyrose/elite_studio/catalog.py` (lines 1–54) — shows env-var override pattern.

**Imports pattern** (from `skyyrose/elite_studio/catalog.py` lines 17–31):
```python
from __future__ import annotations

import json
import os
from pathlib import Path

from skyyrose.core.catalog_loader import CATALOG_CSV as _CANONICAL_CSV
from skyyrose.core.catalog_loader import read_catalog_rows
```

**Env-var override pattern** (from `skyyrose/elite_studio/catalog.py` lines 43–53):
```python
_ENV_CATALOG_PATH = "SKYYROSE_CATALOG_PATH"

def default_catalog_path() -> Path:
    """Return the canonical catalog CSV path (env-overridable)."""
    override = os.getenv(_ENV_CATALOG_PATH)
    if override:
        return Path(override)
    return CANONICAL_CATALOG_CSV
```

**Core transform pattern** — map canonical column names to the nano_banana API the tests expect. The existing test at `tests/scripts/nano_banana/test_catalog.py` lines 29–50 dictates the exact output dict shape:
```python
# From tests/scripts/nano_banana/test_catalog.py lines 29-50 — required output contract:
# br["name"]            → row["name"]
# br["collection"]      → row["collection"]          (canonical col name, NOT "collection_slug")
# br["is_preorder"]     → bool_col(row, "is_preorder")
# br["output_slug"]     → row["render_output_slug"]
# br["is_tech_flat"]    → bool_col(row, "render_is_tech_flat")
# br["is_accessory"]    → bool_col(row, "render_is_accessory")
# br["garment_type"]    → row.get("garment_type_lock", "")
# br["source_override"] → row["render_source_override"] (only if non-empty)
```

**SPECS_JSON pattern** — separate concern from catalog CSV, loaded from `data/product-specs.json`. The test at lines 128–139 expects `load_specs()` to return `{}` gracefully when file is missing:
```python
# From tests/scripts/nano_banana/test_catalog.py lines 134-139:
def test_load_specs_missing_file(self, tmp_path, monkeypatch):
    monkeypatch.setattr(catalog_mod, "SPECS_JSON", tmp_path / "nonexistent.json")
    specs = load_specs()
    assert specs == {}  # silent empty return on missing file
```

**`find_source_image` stub** — `load_products()` calls `find_source_image` internally. Tests in `test_catalog.py` lines 66–68 mock it to avoid filesystem hits. The shim must expose `find_source_image` as a module-level name so `monkeypatch.patch("nano_banana.catalog.find_source_image", ...)` works:
```python
# From tests/scripts/nano_banana/test_catalog.py lines 71-74:
def test_no_filter_returns_all(self) -> None:
    with patch("nano_banana.catalog.find_source_image", self._stub_source):
        products = load_products(self.catalog)
    assert len(products) == 4
```

---

### `renders/config.py` (config, transform)

**Primary analog:** `renders/preflight.py` — shows the imports the config must export and the `_find_bundle_dir` / `PRODUCTS_DIR` names used by preflight.

**What renders/__main__.py imports** (verified lines 18–19):
```python
from renders.config import PRODUCT_CATALOG
from renders.preflight import PreflightAborted, preflight_verify
```

**What renders/preflight.py imports** (verified lines 61–62):
```python
from renders.config import PRODUCTS_DIR, _find_bundle_dir
```

**File-level path constant pattern** (from `skyyrose/core/catalog_loader.py` lines 17–26):
```python
from __future__ import annotations
import json
from pathlib import Path
from skyyrose.core.catalog_loader import read_catalog_rows, CATALOG_CSV

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = (
    PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products"
)
_BUNDLES_DIR = PROJECT_ROOT / "data" / "product-bundles"
```

**Bundle resolver pattern** (INFRA-02 — from RESEARCH.md Pattern 4, scan manifest.json not directory names):
```python
def _find_bundle_dir(name: str, sku: str | None = None) -> Path | None:
    """Find bundle dir by scanning manifest.json files for matching SKU."""
    if sku:
        for d in _BUNDLES_DIR.iterdir():
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

**Module-level PRODUCT_CATALOG build** — import-time compute is the existing codebase pattern (preflight.py line 60 and __main__.py line 18 both import at module level). The catalog build is <0.1s:
```python
# Pattern: module-level initialization (same as PRODUCT_STATUS in catalog_loader.py line 28)
PRODUCT_CATALOG = _build_product_catalog()
```

---

### `skyyrose/elite_studio/fashion/context.py` (service, transform — one-line fix)

**Analog:** self — existing file at `/Users/theceo/DevSkyy/skyyrose/elite_studio/fashion/context.py`

**Current broken line** (line 23):
```python
_CATALOG_PATH = Path(__file__).parent.parent.parent.parent.parent / "data" / "product-catalog.csv"
# Resolves to: /Users/theceo/data/product-catalog.csv  (DOES NOT EXIST)
```

**Fix — replace lines 1–23 imports block** with canonical import pattern from `skyyrose/elite_studio/catalog.py` lines 25–26:
```python
# Replace the broken _CATALOG_PATH line with:
from skyyrose.core.catalog_loader import CATALOG_CSV as _CATALOG_PATH
```

Also update line 280 — `row.get("collection_slug", "")` references a non-existent column. The canonical CSV column is `collection` (verified from `skyyrose/core/catalog_loader.py` and CSV schema in `tests/test_catalog_csv_integrity.py` lines 27–49):
```python
# Line 280 — replace:
collection_slug = row.get("collection_slug", "").strip()
# With:
collection_slug = row.get("collection", "").strip()
```

---

### `scripts/preflight_audit.py` (utility, file-I/O)

**Primary analog:** `renders/preflight.py` — shows the three-category classification pattern (missing/glob/ready), the stdout summary format, and the exit-code contract.

**Secondary analog:** `scripts/split_techflats.py` — shows the standalone script structure (no argparse, `PROJECT_ROOT` constant, `main()` function, `if __name__ == "__main__":`).

**Script structure pattern** (from `scripts/split_techflats.py` lines 1–20):
```python
#!/usr/bin/env python3
"""One-line summary.

Longer description.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# ...

def main() -> int:  # returns exit code
    ...

if __name__ == "__main__":
    sys.exit(main())
```

**Three-category classification pattern** (from `renders/preflight.py` lines 162–174 — adapt for audit):
```python
# READY:              bundle dir exists AND techflat-front file exists on disk
# SKIPPED:            render_is_accessory == "1" (sg-007, lh-005)
# PENDING_USER_ASSETS: garment but missing bundle dir or techflat-front file
#                      (br-007, sg-009, sg-012, br-012, sg-015)
```

**stdout summary format** (from `renders/preflight.py` lines 143–160, adapted):
```python
# Pattern: wide separator lines, per-SKU status rows, final summary block
print(f"  [{i:02d}]  {row['sku']:<12}  {status}")
print(f"        {row['name']}  [{row['collection']}]")
```

**SKIPPED.json write pattern** (from RESEARCH.md Code Examples):
```python
import json
from datetime import datetime, timezone

skipped_path.parent.mkdir(parents=True, exist_ok=True)
skipped_path.write_text(
    json.dumps(
        {
            "reason": "out-of-scope accessories — deferred to v1.3 flat-lay pipeline",
            "skipped": [{"sku": r["sku"], "name": r["name"], "collection": r["collection"]} for r in accessory_rows],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_in_scope_garments": 28,
            "total_skipped_accessories": len(accessory_rows),
        },
        indent=2,
    ),
    encoding="utf-8",
)
```

**Exit-code contract** (from RESEARCH.md Pitfall 4 — exit 0 with warnings for INFRA-06 pending, not hard fail):
```python
# Exit 0: all 30 SKUs processed (READY + SKIPPED + PENDING_USER_ASSETS = 30)
# Exit 1: unexpected error (CSV unreadable, bundle dir missing entirely, etc.)
# PENDING_USER_ASSETS rows: printed clearly but do NOT cause exit 1
```

---

### `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` (config — column addition)

**Analog:** self — the existing CSV. No code pattern needed; this is a data edit.

**Column placement:** append `garment_type_lock` as column 22 (after `render_is_accessory`).

**Value set** (verified from RESEARCH.md Code Examples — all 30 rows):
```
# 28 garment rows get a non-empty value; 2 accessory rows (sg-007, lh-005) get empty string
br-001=crewneck   br-002=joggers      br-003=jersey      br-004=hoodie
br-005=hoodie     br-006=jacket       br-007=shorts      br-008=jersey
br-009=jersey     br-010=jersey       br-011=jersey      br-012=jersey
lh-002=joggers    lh-003=shorts       lh-004=bomber jacket
sg-001=shorts     sg-002=shirt        sg-003=shorts      sg-005=shirt
sg-006=hoodie     sg-009=jacket       sg-011=shirt       sg-012=shirt
sg-013=crewneck   sg-014=sweatpants   sg-015=set
kids-001=hoodie   kids-002=hoodie
```

---

### `tests/test_catalog_csv_integrity.py` (test — add cases)

**Analog:** self — the existing file at `/Users/theceo/DevSkyy/tests/test_catalog_csv_integrity.py`

**Add `garment_type_lock` to EXPECTED_COLUMNS** (line 49, after `render_is_accessory`):
```python
# Current EXPECTED_COLUMNS set — add one entry:
EXPECTED_COLUMNS = {
    # ... existing 21 columns ...
    "render_is_accessory",
    "garment_type_lock",    # ADD THIS
}
```

**New test cases to add** — following the exact style of existing tests (lines 101–142, parametrize pattern):
```python
ACCESSORY_SKUS = {"sg-007", "lh-005"}

def test_garment_type_lock_non_empty_for_garment_skus(rows: list[dict[str, str]]) -> None:
    """garment_type_lock must be non-empty for every non-accessory row."""
    missing = [
        r["sku"] for r in rows
        if not bool_col(r, "render_is_accessory")
        and not (r.get("garment_type_lock") or "").strip()
    ]
    assert not missing, f"garment rows with empty garment_type_lock: {missing}"

def test_garment_type_lock_empty_for_accessories(rows: list[dict[str, str]]) -> None:
    """garment_type_lock should be empty for accessory rows."""
    for r in rows:
        if bool_col(r, "render_is_accessory"):
            val = (r.get("garment_type_lock") or "").strip()
            assert not val, f"{r['sku']}: accessory should have empty garment_type_lock, got {val!r}"
```

---

### `tests/scripts/nano_banana/conftest.py` (test — update `_CSV_COLUMNS`)

**Analog:** self — the existing file at `/Users/theceo/DevSkyy/tests/scripts/nano_banana/conftest.py`

**Replace `_CSV_COLUMNS`** (lines 15–33) to match canonical CSV schema (`EXPECTED_COLUMNS` from `tests/test_catalog_csv_integrity.py` lines 27–49). Key removals: `type`, `collection_slug`, `render_variant_of`. Key additions: `badge`, `image`, `front_model_image`, `back_image`, `back_model_image`, `color`, `edition_size`, `published`, `branding_spec`, `garment_type_lock`.

**Updated `_CSV_COLUMNS`**:
```python
_CSV_COLUMNS = [
    "sku",
    "name",
    "price",
    "collection",
    "description",
    "badge",
    "image",
    "front_model_image",
    "back_image",
    "back_model_image",
    "sizes",
    "color",
    "edition_size",
    "published",
    "is_preorder",
    "branding_spec",
    "render_output_slug",
    "render_source_override",
    "render_back_source_override",
    "render_is_tech_flat",
    "render_is_accessory",
    "garment_type_lock",
]
```

**Update `_SAMPLE_ROWS`** — rename `collection_slug` key to `collection`, remove `type` and `render_variant_of`, add missing columns with empty-string defaults. The test assertions in `test_catalog.py` lines 29–50 check `br["collection"] == "black-rose"` — so the fixture row value must be the slug, not the display name:
```python
# Sample row diff:
# REMOVE: "type": "simple", "collection": "Black Rose", "collection_slug": "black-rose", "render_variant_of": ""
# ADD:    "collection": "black-rose", "badge": "", "image": "", "front_model_image": "",
#         "back_image": "", "back_model_image": "", "published": "1", "branding_spec": "",
#         "garment_type_lock": "crewneck"
```

---

### `tests/test_renders_config.py` (test — new file)

**Analog:** `skyyrose/elite_studio/tests/test_brand.py` — smoke-test pattern for a module that loads data at import time. Key pattern: test that the module imports cleanly and the top-level constant has the right type.

**Imports pattern** (from `skyyrose/elite_studio/tests/test_brand.py` lines 1–12):
```python
"""Smoke tests for renders/config.py — import guard and PRODUCT_CATALOG shape."""
from __future__ import annotations
import pytest
```

**Core smoke-test pattern** (from `skyyrose/elite_studio/tests/test_brand.py` lines 55–60 and `tests/test_catalog_csv_integrity.py` lines 74–75):
```python
def test_renders_config_imports_without_error() -> None:
    """renders/config.py must import cleanly (PRODUCT_CATALOG built at import time)."""
    import renders.config as cfg
    assert hasattr(cfg, "PRODUCT_CATALOG")

def test_product_catalog_is_a_list_of_dicts() -> None:
    from renders.config import PRODUCT_CATALOG
    assert isinstance(PRODUCT_CATALOG, list)
    assert len(PRODUCT_CATALOG) == 30
    assert all(isinstance(p, dict) for p in PRODUCT_CATALOG)
    assert all("sku" in p for p in PRODUCT_CATALOG)

def test_products_dir_is_a_path() -> None:
    from renders.config import PRODUCTS_DIR
    from pathlib import Path
    assert isinstance(PRODUCTS_DIR, Path)
```

---

### `tests/test_fashion_context.py` (test — new file)

**Analog:** `skyyrose/elite_studio/tests/test_brand.py` — monkeypatch env var pattern to redirect the loader to a controlled CSV path.

**Monkeypatch env override pattern** (from `skyyrose/elite_studio/tests/test_brand.py` lines 55–59):
```python
@pytest.fixture
def patched_catalog(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    csv_path = tmp_path / "catalog.csv"
    # ... write minimal CSV ...
    monkeypatch.setenv("SKYYROSE_CATALOG_PATH", str(csv_path))
    # Also patch the module-level cache so monkeypatching env takes effect
    import skyyrose.elite_studio.fashion.context as ctx_mod
    monkeypatch.setattr(ctx_mod, "_catalog_cache", None)
    return csv_path
```

**Core test cases** (adapted from `tests/test_catalog_csv_integrity.py` lines 74–75 style):
```python
def test_load_catalog_reads_canonical_csv_path() -> None:
    """_load_catalog() must resolve to the canonical CSV, not the old stale path."""
    from skyyrose.core.catalog_loader import CATALOG_CSV
    import skyyrose.elite_studio.fashion.context as ctx_mod
    # The module constant must equal CATALOG_CSV (or resolve to same file)
    assert Path(str(ctx_mod._CATALOG_PATH)).resolve() == Path(str(CATALOG_CSV)).resolve()

def test_load_catalog_returns_dict_keyed_by_sku(patched_catalog) -> None:
    import skyyrose.elite_studio.fashion.context as ctx_mod
    catalog = ctx_mod._load_catalog()
    assert "br-001" in catalog

def test_build_from_product_catalog_uses_collection_column(patched_catalog) -> None:
    """Must read 'collection' column, not non-existent 'collection_slug'."""
    from skyyrose.elite_studio.fashion.context import FashionContextBuilder
    # Should not raise KeyError on 'collection_slug'
    builder = FashionContextBuilder()
    # build_from_product_catalog is tested via the module-level _load_catalog
    catalog = builder._load_catalog()  # actually ctx._load_catalog()
    row = catalog.get("br-001", {})
    assert "collection" in row or row == {}  # either found or gracefully missed
```

---

### `tests/test_preflight_audit.py` (test — new file)

**Primary analog:** `skyyrose/elite_studio/tests/test_catalog_validation.py` — tests a file-scanning utility with tmp_path fixtures and assert-on-output pattern.

**Secondary analog:** `tests/test_catalog_csv_integrity.py` — shows the `monkeypatch` + `tmp_path` style for redirecting file paths.

**tmp_path bundle setup pattern** (from `tests/scripts/nano_banana/conftest.py` lines 213–230):
```python
@pytest.fixture
def bundle_tree(tmp_path: Path) -> Path:
    """Create a minimal product-bundles/ tree for testing."""
    bundles = tmp_path / "product-bundles"
    for sku, name in [("br-001", "BLACK Rose Crewneck"), ("sg-007", "The Signature Beanie")]:
        d = bundles / name
        d.mkdir(parents=True)
        (d / "manifest.json").write_text(json.dumps({"sku": sku, "name": name}))
        if sku != "sg-007":  # accessory — no techflat needed
            (d / "techflat-front.jpeg").write_bytes(b"\xff\xd8\xff")  # minimal JPEG header
    return tmp_path
```

**PENDING_USER_ASSETS assertion pattern** (key INFRA-06 behavior):
```python
def test_missing_bundle_flagged_as_pending(bundle_tree, monkeypatch, capsys):
    """br-012 and sg-015 (no bundle dir) must appear in PENDING_USER_ASSETS, not READY."""
    # ... setup minimal CSV with br-012 as garment, no bundle dir ...
    result = run_audit(bundles_dir=bundle_tree / "product-bundles", ...)
    assert "PENDING_USER_ASSETS" in result or "br-012" in capsys.readouterr().out

def test_skipped_json_contains_only_accessories(bundle_tree, tmp_path):
    """SKIPPED.json must list only sg-007 and lh-005, not garment SKUs."""
    skipped_path = tmp_path / "SKIPPED.json"
    run_audit(..., skipped_out=skipped_path)
    data = json.loads(skipped_path.read_text())
    skipped_skus = {s["sku"] for s in data["skipped"]}
    assert skipped_skus == {"sg-007", "lh-005"}
    # Garment SKUs must not appear in skipped
    assert "br-012" not in skipped_skus
```

**Exit-code test pattern** (from `renders/preflight.py` line 273 style):
```python
def test_audit_exits_0_with_pending_garments(monkeypatch, tmp_path, capsys):
    """Script exits 0 even when some garment SKUs are PENDING_USER_ASSETS."""
    import scripts.preflight_audit as audit_mod
    # redirect paths, call main(), assert return value == 0
    rc = audit_mod.main(bundles_dir=..., skipped_out=..., catalog_path=...)
    assert rc == 0
```

---

## Shared Patterns

### `from __future__ import annotations` Header
**Source:** Every Python file in `skyyrose/` and `renders/`
**Apply to:** All new Python files — `scripts/nano_banana/catalog.py`, `renders/config.py`, `scripts/preflight_audit.py`, all test files.
```python
from __future__ import annotations
```

### Path Constants — PROJECT_ROOT from `__file__`
**Source:** `skyyrose/core/catalog_loader.py` lines 22–26
**Apply to:** `renders/config.py`, `scripts/preflight_audit.py`
```python
PROJECT_ROOT = Path(__file__).resolve().parents[N]  # N=2 from renders/, N=1 from scripts/
```

### SKYYROSE_CATALOG_PATH Env-Var Override
**Source:** `skyyrose/elite_studio/catalog.py` lines 43–53
**Apply to:** `scripts/nano_banana/catalog.py`, `renders/config.py`
```python
CATALOG_CSV = Path(os.getenv("SKYYROSE_CATALOG_PATH", "") or _CANONICAL_CSV)
```

### `monkeypatch.setattr(module, "CATALOG_CSV", path)` Test Override
**Source:** `tests/scripts/nano_banana/conftest.py` lines 116–127
**Apply to:** All new test files that involve catalog path redirection.
```python
monkeypatch.setattr(catalog_mod, "CATALOG_CSV", csv_path)
```

### Silent-Return on Missing Optional Files
**Source:** `skyyrose/elite_studio/fashion/context.py` lines 45–50 and `tests/scripts/nano_banana/test_catalog.py` lines 134–139
**Apply to:** `scripts/nano_banana/catalog.py` — `load_specs()` when `product-specs.json` is missing.
```python
try:
    with open(path, encoding="utf-8") as f:
        return json.load(f)
except FileNotFoundError:
    return {}
except Exception as exc:
    logger.warning("Failed to load %s: %s", path, exc)
    return {}
```

### Bundle Manifest Scan — Error-Tolerant Loop
**Source:** RESEARCH.md Pattern 4 (confirmed by `renders/preflight.py` import of `_find_bundle_dir`)
**Apply to:** `renders/config.py` (`_find_bundle_dir`) and `scripts/preflight_audit.py` (same logic inline or imported).
```python
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

---

## No Analog Found

All files have close analogs in the codebase. No entries in this section.

---

## Key Anti-Patterns (from RESEARCH.md)

| Anti-Pattern | Source of Truth | Correct Pattern |
|---|---|---|
| `collection_slug` column in CSV | Only in old conftest fixtures — not in canonical CSV | Use `collection` column |
| `type` column in CSV | Only in old nano_banana conftest | Column does not exist in canonical schema |
| `render_variant_of` column | Only in old nano_banana conftest | Column does not exist in canonical schema |
| Directory-name bundle lookup | `renders/preflight.py` comment | Scan `manifest.json` SKU field |
| `_CATALOG_PATH = Path(__file__).parent.parent...` (5 levels) | `fashion/context.py` line 23 stale path | `from skyyrose.core.catalog_loader import CATALOG_CSV as _CATALOG_PATH` |
| Empty `__init__.py` | cerebrum.md rule | One-line docstring minimum |

---

## Metadata

**Analog search scope:** `skyyrose/`, `renders/`, `scripts/`, `tests/`, `.claude/worktrees/`
**Files scanned:** 11 full reads + RESEARCH.md
**Pattern extraction date:** 2026-04-22
