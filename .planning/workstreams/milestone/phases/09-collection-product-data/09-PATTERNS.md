# Phase 9: Collection & Product Data — Pattern Map

**Mapped:** 2026-05-12
**Files analyzed:** 4 (2 existing, 2 new)
**Analogs found:** 4 / 4

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `wordpress-theme/skyyrose-flagship/inc/collection-content.php` | config/data-provider | request-response | self (existing file) | self-analog |
| `wordpress-theme/skyyrose-flagship/template-parts/collection/page.php` | component/template | request-response | self (existing file) | self-analog |
| `wordpress-theme/skyyrose-flagship/scripts/audit-collections.php` | utility/audit | batch | `scripts/verify_live_structure.py` | role-match (language mismatch: Python→PHP) |
| `tests/test_collection_data_integrity.py` | test | CRUD/batch | `tests/test_catalog_csv_integrity.py` | exact |

---

## Pattern Assignments

### `wordpress-theme/skyyrose-flagship/inc/collection-content.php` (config, request-response)

**Status:** Existing file — verification/diagnostic target, not being created.
**Analog:** Self. Source of truth for DATA-01 diagnosis.

**ABSPATH guard pattern** (line 1):
```php
defined( 'ABSPATH' ) || exit;
```

**DATA-01 hero config** (lines 28-42):
```php
function skyyrose_get_collection_content( $slug ) {
    $collections = array(
        'black-rose' => array(
            'hero_bg'     => '/branding/sr-collection-black-rose.webp',
            'hero_bg_alt' => __( 'Black Rose Collection — rose from concrete', 'skyyrose' ),
            // ...
        ),
        'love-hurts'    => array( /* ... */ ),
        'signature'     => array( /* ... */ ),
        'kids-capsule'  => array( /* ... */ ),
    );
    return isset( $collections[ $slug ] ) ? $collections[ $slug ] : null;
}
```

**Diagnostic anchor for DATA-01 verification:**
- Line 31: `'hero_bg' => '/branding/sr-collection-black-rose.webp'` — this value is the assertion target.
- Function returns `null` for unknown slugs (no fallback collection).
- All user-facing strings use `__('...', 'skyyrose')` i18n wrapper.

---

### `wordpress-theme/skyyrose-flagship/template-parts/collection/page.php` (component, request-response)

**Status:** Existing file — render path target for DATA-01 verification.
**Analog:** Self.

**Args intake + sanitize pattern** (lines 18-21):
```php
$slug = isset( $args['slug'] ) ? sanitize_key( $args['slug'] ) : '';
$c    = skyyrose_get_collection_content( $slug );
```

**Hard-fail beacon pattern** (lines 22-38):
```php
if ( ! $c ) {
    error_log(
        sprintf(
            "[SkyyRose Collections] Missing content config for slug '%s'. File: %s",
            $slug,
            __FILE__
        )
    );
    printf(
        '<div class="skyyrose-render-error" data-skyyrose-error="missing-collection-content" data-collection="%s" hidden></div>',
        esc_attr( $slug )
    );
    return;
}
```
The `data-skyyrose-error` beacon is consumed by `scripts/verify_live_structure.py` global assertion (`max_count=0`). Hard fail = early return, no partial render.

**Hero image render with cache-bust** (lines 62-67):
```php
$has_hero_bg = ! empty( $c['hero_bg'] );
// ...
<img src="<?php echo esc_url( SKYYROSE_ASSETS_URI . $c['hero_bg'] . '?v=' . SKYYROSE_VERSION ); ?>"
     alt="<?php echo esc_attr( $c['hero_bg_alt'] ); ?>"
     loading="eager" fetchpriority="high" decoding="async" width="1024" height="1024">
```

**Output escape rules in use:**
- `esc_url()` for all `src`/`href` attributes
- `esc_attr()` for all HTML attributes
- `esc_html()` for text nodes
- `sanitize_key()` on all slug inputs

---

### `wordpress-theme/skyyrose-flagship/scripts/audit-collections.php` (utility/audit, batch) — NEW

**Analog:** `scripts/verify_live_structure.py` (lines 1-517)
**Match quality:** Role-match — same audit purpose, same assertion pattern; language mismatch (Python→PHP). Claude's Discretion scope explicitly includes "PHP audit vs Python audit" — planner must decide language.

**ABSPATH guard pattern** — copy from `inc/collection-content.php` line 1:
```php
<?php
defined( 'ABSPATH' ) || exit;
// If run standalone (CLI), bootstrap WordPress:
// require_once dirname( __DIR__, 3 ) . '/wp-load.php';
```

**Assertion structure** — adapt from `verify_live_structure.py` lines 42-60:
```python
# Python original:
@dataclass(frozen=True)
class Assertion:
    selector: str
    min_count: int
    label: str
    max_count: int | None = None
```
PHP equivalent pattern:
```php
// PHP adaptation — use associative array or named struct:
$assertion = array(
    'selector'  => 'div.col-page[data-collection="black-rose"]',
    'min_count' => 1,
    'label'     => 'Black Rose collection wrapper present',
    'max_count' => null,
);
```

**Collection floors dict** — adapt from `verify_live_structure.py` lines 62-68:
```python
# Python original:
COLLECTION_CARD_FLOORS = {
    "black-rose": 12,   # 15 actual — conservative floor
    "love-hurts": 3,    # 4 actual
    "signature": 10,    # 12 actual
    "kids-capsule": 2,
}
```
PHP equivalent:
```php
$collection_card_floors = array(
    'black-rose'   => 12,
    'love-hurts'   => 3,
    'signature'    => 10,
    'kids-capsule' => 2,
);
```

**Global assertion pattern** (no `data-skyyrose-error` beacons allowed):
```python
# Python original — verify_live_structure.py lines 75-80:
GLOBAL_ASSERTIONS: tuple[Assertion, ...] = (
    Assertion("[data-skyyrose-error]", 0, "no skyyrose render-error markers", max_count=0),
)
```

**Per-collection assertion builder** — adapt from `verify_live_structure.py` lines 82-100:
```python
# Python original:
def collection_assertions(slug: str) -> tuple[Assertion, ...]:
    floor = COLLECTION_CARD_FLOORS[slug]
    return (
        Assertion(f"div.col-page[data-collection='{slug}']", 1, f"{slug} page wrapper"),
        Assertion("section.col-hero", 1, "hero section present"),
        Assertion("div.holo", floor, f"at least {floor} holo cards"),
        Assertion(f"div.holo--{slug}", floor, f"collection-scoped holo cards"),
        THEME_CSS_ASSERTION,
    )
```

**CLI pattern** — adapt from `verify_live_structure.py` lines 380-430:
```python
# Python original argparse:
parser.add_argument("--all",  action="store_true")
parser.add_argument("--page", metavar="SLUG")
parser.add_argument("--url",  default="https://skyyrose.co")
parser.add_argument("--list", action="store_true")
parser.add_argument("--timeout", type=int, default=15)
parser.add_argument("--no-cache-bust", action="store_true")
```
PHP CLI equivalent (use `getopt` or manual `$argv` parsing):
```php
// PHP CLI pattern:
$opts = getopt( '', array( 'all', 'page:', 'url:', 'list', 'timeout:' ) );
$base_url = $opts['url'] ?? 'https://skyyrose.co';
```

**Exit code convention** — copy from `verify_live_structure.py`:
- `exit(0)` — all assertions pass
- `exit(2)` — one or more assertion failures (expected during debugging)
- `exit(3)` — environment problem (WordPress not loaded, network failure)

---

### `tests/test_collection_data_integrity.py` (test, batch) — NEW

**Analog:** `tests/test_catalog_csv_integrity.py` (lines 1-251)
**Match quality:** Exact — same module, same CSV source, same helper functions, same fixture pattern.

**Imports pattern** (lines 1-12 of analog):
```python
import csv
import os
import pytest

from skyyrose.core.catalog_loader import (
    CATALOG_CSV,
    PRODUCT_STATUS,
    bool_col,
    int_col,
    read_catalog_rows,
    status_from_row,
)
```

**Module-scoped fixture pattern** (lines 18-21 of analog):
```python
@pytest.fixture(scope="module")
def rows() -> list[dict[str, str]]:
    return read_catalog_rows(CATALOG_CSV)
```

**VALID_COLLECTIONS constant** — copy exact set (lines 24-25 of analog):
```python
VALID_COLLECTIONS = {"black-rose", "love-hurts", "signature", "kids-capsule"}
```

**RETIRED_SKU_CODES constant** — copy and extend for phase (lines 27-29 of analog):
```python
RETIRED_SKU_CODES = {
    "lh-001", "sg-004", "sg-008", "sg-010",
    "br-d01", "br-d02", "br-d03", "br-d04",
    "sg-d01", "sg-d02", "sg-d03", "sg-d04",
}
```

**Pre-order SKUs for DATA-02 verification** — from CONTEXT.md:
```python
PRE_ORDER_SKUS = {
    "br-004", "br-005", "br-006",
    "br-d01", "br-d02", "br-d03", "br-d04",
    "lh-001",
    "sg-001", "sg-d01",
}
```

**Collection validity assertion** (lines 55-62 of analog):
```python
def test_collections_are_valid(rows):
    for r in rows:
        slug = r["collection"].strip()
        assert slug in VALID_COLLECTIONS, (
            f"SKU {r['sku']!r} has unknown collection {slug!r}; "
            f"expected one of {sorted(VALID_COLLECTIONS)}"
        )
```

**Boolean column assertion** (lines 80-93 of analog):
```python
def test_boolean_columns_are_one_or_zero(rows):
    bool_cols = ["published", "is_preorder", "render_is_tech_flat", "render_is_accessory"]
    for r in rows:
        for col in bool_cols:
            raw = (r.get(col) or "").strip()
            assert raw in ("", "0", "1"), (
                f"SKU {r['sku']!r}: column {col!r} = {raw!r}; expected '0', '1', or empty"
            )
```

**DATA-02 pre-order assertion** — new test, extend analog pattern:
```python
def test_preorder_skus_flagged(rows):
    """DATA-02: Named pre-order SKUs must have is_preorder=1."""
    flagged = {r["sku"] for r in rows if bool_col(r, "is_preorder")}
    for sku in PRE_ORDER_SKUS:
        assert sku in flagged, f"SKU {sku!r} expected is_preorder=1 but flag is missing"
```

**DATA-03 cross-collection leakage assertion** — new test, extend analog pattern:
```python
def test_no_cross_collection_sku_leakage(rows):
    """DATA-03: SKU prefix must match its declared collection slug."""
    prefix_map = {
        "br-": "black-rose",
        "lh-": "love-hurts",
        "sg-": "signature",
        "kc-": "kids-capsule",
    }
    for r in rows:
        sku = r["sku"]
        declared = r["collection"].strip()
        for prefix, expected_collection in prefix_map.items():
            if sku.startswith(prefix):
                assert declared == expected_collection, (
                    f"SKU {sku!r} prefix implies {expected_collection!r} "
                    f"but collection is {declared!r}"
                )
```

---

## Shared Patterns

### ABSPATH Guard
**Source:** `wordpress-theme/skyyrose-flagship/inc/collection-content.php` line 1
**Apply to:** All new PHP files
```php
defined( 'ABSPATH' ) || exit;
```

### Output Escaping
**Source:** `wordpress-theme/skyyrose-flagship/template-parts/collection/page.php` lines 62-67
**Apply to:** All PHP template output
```php
esc_url()    // src, href attributes
esc_attr()   // all HTML attributes
esc_html()   // text nodes
sanitize_key()  // slug/key inputs before use
```

### Hard-Fail Beacon
**Source:** `wordpress-theme/skyyrose-flagship/template-parts/collection/page.php` lines 22-38
**Apply to:** Any PHP template part that loads config from `skyyrose_get_collection_content()`
```php
if ( ! $c ) {
    error_log( sprintf( "[SkyyRose Collections] Missing content config for slug '%s'. File: %s", $slug, __FILE__ ) );
    printf(
        '<div class="skyyrose-render-error" data-skyyrose-error="missing-collection-content" data-collection="%s" hidden></div>',
        esc_attr( $slug )
    );
    return;
}
```
This beacon is asserted absent (`max_count=0`) by `verify_live_structure.py` post-deploy.

### SKYYROSE_VERSION Cache-Bust
**Source:** `wordpress-theme/skyyrose-flagship/template-parts/collection/page.php` lines 64-65
**Apply to:** Any PHP template rendering versioned assets
```php
echo esc_url( SKYYROSE_ASSETS_URI . $c['hero_bg'] . '?v=' . SKYYROSE_VERSION );
```

### pytest Module-Scoped Fixture
**Source:** `tests/test_catalog_csv_integrity.py` lines 18-21
**Apply to:** All CSV-based test files
```python
@pytest.fixture(scope="module")
def rows() -> list[dict[str, str]]:
    return read_catalog_rows(CATALOG_CSV)
```

### Catalog Loader Imports
**Source:** `tests/test_catalog_csv_integrity.py` lines 1-12
**Apply to:** `tests/test_collection_data_integrity.py`
```python
from skyyrose.core.catalog_loader import (
    CATALOG_CSV, PRODUCT_STATUS, bool_col, int_col, read_catalog_rows, status_from_row,
)
```

---

## No Analog Found

None — all four files have analogs. See language mismatch note below.

---

## Language Mismatch — Planner Decision Required

| File | Expected Language | Closest Analog Language | Decision in CONTEXT.md |
|------|-------------------|------------------------|------------------------|
| `wordpress-theme/skyyrose-flagship/scripts/audit-collections.php` | PHP | Python (`scripts/verify_live_structure.py`) | "Claude's Discretion" — "exact verification script structure (PHP audit vs Python audit)" |

**Recommendation for planner:** No PHP audit scripts exist anywhere in the project. The Python `verify_live_structure.py` is fully implemented (517 lines) and already asserts collection page structure post-deploy. A PHP CLI audit would require a WordPress bootstrap load sequence. Given the task is DATA-01 verification (read-only, post-deploy gate), **extending `verify_live_structure.py`** with a stricter Black Rose hero assertion is lower risk than introducing a new PHP CLI. The planner should surface this choice as PLAN.md decision point 1.

---

## Metadata

**Analog search scope:** `wordpress-theme/skyyrose-flagship/inc/`, `wordpress-theme/skyyrose-flagship/template-parts/collection/`, `scripts/`, `tests/`
**Files scanned:** 5 files read (`collection-content.php`, `template-parts/collection/page.php`, `verify_live_structure.py`, `test_catalog_csv_integrity.py`, `test_collection_page_manager.py`)
**Pattern extraction date:** 2026-05-12
