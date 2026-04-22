# Architecture Patterns

**Domain:** CSV-driven multi-pipeline imagery system (SkyyRose v1.2)
**Researched:** 2026-04-22
**Confidence:** HIGH — derived from reading actual source files, not inference

---

## Current State (What Exists)

Three separate product-loading mechanisms exist today, all reading product data
independently:

| Location | What it reads | Problem |
|---|---|---|
| `renders/config.py` (not yet on disk — referenced by `__main__.py`) | `PRODUCT_CATALOG` dict, `_find_bundle_dir(name)`, `PRODUCTS_DIR` | Inline catalog, not CSV-driven |
| `skyyrose/elite_studio/fashion/context.py` | `data/product-catalog.csv` (wrong path — retired file) | Stale path, bypasses canonical loader |
| `skyyrose/elite_studio/catalog.py` | `skyyrose/core/catalog_loader.py` | Correct pattern, but only used by Elite Studio |
| `scripts/nano_banana/` (pyc-only, source deleted) | Unknown — pyc in `__pycache__` | Must be rebuilt; source gone |

The canonical loader (`skyyrose/core/catalog_loader.py`) and the Elite Studio
`Catalog` class are the correct foundation. Everything else must be migrated to
use them.

---

## Recommended Architecture

### Layer Diagram

```
wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv
                         |
                         |  (single file, never forked)
                         v
         skyyrose/core/catalog_loader.py
         +-----------------------------+
         | CATALOG_CSV constant        |
         | read_catalog_rows()         |
         | bool_col(), int_col()       |
         | status_from_row()           |
         +-------------+---------------+
                       |  (all three layers import this)
          +------------+-----------+
          v            v           v
   skyyrose/core/  skyyrose/core/  skyyrose/core/
   bundle_map.py   garment.py      output_paths.py
   (NEW)           (NEW)           (NEW)
          |              |                |
          +--------------+----------------+
                         |
              skyyrose/core/product_adapter.py
              (NEW -- thin facade over the three above)
                         |
          +--------------+-----------+
          v              v           v
   renders/         scripts/        skyyrose/
   config.py        nano_banana/    elite_studio/
   (REFACTOR)       catalog.py      catalog.py
                    (REBUILD)       (already imports core)
```

---

## Component Boundaries

| Component | File | Responsibility | Imports |
|---|---|---|---|
| Raw loader | `skyyrose/core/catalog_loader.py` | CSV I/O, type coercions | stdlib only |
| Bundle map | `skyyrose/core/bundle_map.py` | SKU to bundle directory resolution | `catalog_loader`, `pathlib` |
| Garment router | `skyyrose/core/garment.py` | Name to GarmentType enum, prompt params | stdlib only |
| Output paths | `skyyrose/core/output_paths.py` | Canonical output path construction | `pathlib` |
| Product adapter | `skyyrose/core/product_adapter.py` | Unified product record assembly | `bundle_map`, `garment`, `output_paths`, `catalog_loader` |
| Pipeline callers | `renders/`, `nano_banana/`, `elite_studio/` | Rendering logic | `product_adapter` only -- never `catalog_loader` directly |

No circular dependencies are possible because `core/` modules only import
from the stdlib and each other in one direction.

---

## Where the SKU-to-Bundle Mapping Should Live

### Decision: `skyyrose/core/bundle_map.py` — Python module, not JSON

The mapping must handle name normalization (em dash, apostrophes, special chars)
and must be testable. A JSON file cannot run normalization logic. A Python
module keeps normalization and mapping together, avoids a parse step, and
imports cleanly from all three pipelines.

The manifest.json files that already exist in each bundle directory are the
authoritative source for the mapping — `manifest.json["sku"]` is the canonical
SKU for that directory. The bundle map module reads all manifests at startup
and builds the reverse index.

```python
# skyyrose/core/bundle_map.py

from __future__ import annotations
import json
import unicodedata
from pathlib import Path
from functools import lru_cache

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUNDLES_DIR = PROJECT_ROOT / "data" / "product-bundles"


def _normalize(text: str) -> str:
    """Canonical form for name comparison.

    Collapses em-dash / en-dash to hyphen, strips apostrophes,
    lowercases, strips surrounding whitespace.
    """
    text = unicodedata.normalize("NFC", text)
    text = text.replace("—", "-").replace("–", "-")
    text = text.replace("’", "").replace("'", "")
    return text.strip().lower()


@lru_cache(maxsize=1)
def _load_index() -> dict[str, Path]:
    """Read every manifest.json and return {sku: bundle_dir_path}.

    Called once; result is module-level cached.
    """
    index: dict[str, Path] = {}
    if not BUNDLES_DIR.is_dir():
        return index
    for manifest_path in BUNDLES_DIR.glob("*/manifest.json"):
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            sku = (data.get("sku") or "").strip().lower()
            if sku:
                index[sku] = manifest_path.parent
        except Exception:
            pass  # corrupt manifest -- skip, don't crash the pipeline
    return index


def bundle_dir(sku: str) -> Path | None:
    """Return the bundle directory for a SKU, or None if not found."""
    return _load_index().get(sku.strip().lower())


def techflat_front(sku: str) -> Path | None:
    """Return the techflat-front image path for a SKU, or None."""
    d = bundle_dir(sku)
    if d is None:
        return None
    for ext in (".jpeg", ".jpg", ".png", ".webp"):
        candidate = d / f"techflat-front{ext}"
        if candidate.exists():
            return candidate
    return None


def techflat_back(sku: str) -> Path | None:
    """Return the techflat-back image path for a SKU, or None."""
    d = bundle_dir(sku)
    if d is None:
        return None
    for ext in (".jpeg", ".jpg", ".png", ".webp"):
        candidate = d / f"techflat-back{ext}"
        if candidate.exists():
            return candidate
    return None


def source_photo(sku: str) -> Path | None:
    """Return source-photo path for a SKU (real photography), or None."""
    d = bundle_dir(sku)
    if d is None:
        return None
    for name in ("source-photo.jpeg", "source-photo.jpg", "source-photo.png"):
        candidate = d / name
        if candidate.exists():
            return candidate
    return None


def logo_ref(sku: str) -> Path | None:
    """Return logo-ref image path for a SKU, or None."""
    d = bundle_dir(sku)
    if d is None:
        return None
    for ext in (".png", ".jpeg", ".jpg"):
        candidate = d / f"logo-ref{ext}"
        if candidate.exists():
            return candidate
    return None


def spec_text(sku: str) -> str:
    """Return spec.txt content for a SKU, or empty string."""
    d = bundle_dir(sku)
    if d is None:
        return ""
    p = d / "spec.txt"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def all_mapped_skus() -> list[str]:
    """Return all SKUs that have a bundle directory."""
    return sorted(_load_index().keys())
```

### Why not extend manifest.json?

The manifest.json files serve as directory metadata only. They are already
correct -- `manifest.json["sku"]` is present and accurate in every bundle.
The Python module reads them at startup and builds the reverse index. No
changes to the manifest files are needed; the normalization problem is
solved in `_normalize()` and the lru_cache means the disk read happens once.

### Handling the 15 name-mismatch cases

The mismatches are between `CSV["name"]` and `manifest.json["name"]` / directory
names. Since the bundle map indexes by `manifest.json["sku"]` (not by name),
there is no name normalization needed for lookup -- SKU is always the key. The
`_normalize()` function is kept for defensive fallback only. The 15 "mismatches"
dissolve because the lookup path is always `bundle_dir(sku)`, never
`bundle_dir_by_name(csv_name)`.

---

## Garment Type Enum and Routing

### `skyyrose/core/garment.py` — New module

The garment type inference already exists in `skyyrose/elite_studio/fashion/context.py`
(`_infer_garment_type`, `_GARMENT_TYPE_KEYWORDS`) and in `fashion/knowledge.py`
(`GarmentType` dataclass, `_GARMENT_CATALOGUE`). These are currently
elite-studio-private. Move the canonical enum and keyword map to `core/garment.py`
so all pipelines use the same logic. The elite_studio versions become thin wrappers
or are replaced with imports from core.

The 10 garment types present in the catalog (derived from all 30 product names):

| Slug | CSV products | Keyword triggers | Ghost mannequin notes |
|---|---|---|---|
| `hoodie` | br-004, br-005, sg-006, kids-001, kids-002 | "hoodie" | Front + back; hood down flat; invisible mannequin |
| `crewneck` | br-001, sg-013 | "crewneck" | Front + back flat; invisible mannequin |
| `jersey` | br-003, br-008--012 | "jersey" | Flat lay only; number/lettering must be sharp |
| `joggers` | br-002, lh-002, sg-014 | "joggers", "sweatpants" | Full length; waistband detail crop |
| `shorts` | br-007, lh-003, sg-001, sg-003 | "shorts" | Front flat; inseam visible |
| `shirt` | sg-002, sg-005, sg-011, sg-012 | "shirt", "tee" | Front + back; graphic detail crop |
| `jacket` | br-006, lh-004, sg-009, sg-015 | "sherpa jacket", "varsity jacket", "jacket", "windbreaker" | Open + closed; collar detail |
| `beanie` | sg-007 | "beanie" | Product flat + on-head 3/4 angle |
| `fanny pack` | lh-005 | "fanny", "fannie" | Flat front + back; hardware detail |
| `set` | kids-001, kids-002 | "hoodie set", "set" (after more-specific matches) | Both pieces + individual |

Note: kids-001 and kids-002 are "Colorblock Hoodie Set" -- the "set" keyword
is matched before "hoodie" because the keyword map is ordered longest-phrase-first.

```python
# skyyrose/core/garment.py

from __future__ import annotations
from enum import Enum


class GarmentSlug(str, Enum):
    HOODIE = "hoodie"
    CREWNECK = "crewneck"
    JERSEY = "jersey"
    JOGGERS = "joggers"
    SHORTS = "shorts"
    SHIRT = "shirt"
    JACKET = "jacket"
    BEANIE = "beanie"
    FANNY_PACK = "fanny pack"
    SET = "set"
    UNKNOWN = "unknown"


# Order matters: longer / more-specific phrases must come before shorter ones.
_KEYWORD_MAP: list[tuple[str, GarmentSlug]] = [
    ("sherpa jacket", GarmentSlug.JACKET),
    ("varsity jacket", GarmentSlug.JACKET),
    ("bomber jacket", GarmentSlug.JACKET),
    ("windbreaker set", GarmentSlug.SET),
    ("basketball shorts", GarmentSlug.SHORTS),
    ("hoodie set", GarmentSlug.SET),
    ("colorblock hoodie set", GarmentSlug.SET),
    ("hoodie", GarmentSlug.HOODIE),
    ("crewneck", GarmentSlug.CREWNECK),
    ("jersey", GarmentSlug.JERSEY),
    ("joggers", GarmentSlug.JOGGERS),
    ("sweatpants", GarmentSlug.JOGGERS),
    ("shorts", GarmentSlug.SHORTS),
    ("shirt", GarmentSlug.SHIRT),
    ("tee", GarmentSlug.SHIRT),
    ("jacket", GarmentSlug.JACKET),
    ("windbreaker", GarmentSlug.JACKET),
    ("beanie", GarmentSlug.BEANIE),
    ("fanny", GarmentSlug.FANNY_PACK),
    ("fannie", GarmentSlug.FANNY_PACK),
    ("set", GarmentSlug.SET),
]

# Per-garment ghost mannequin prompt parameters
_GHOST_PARAMS: dict[GarmentSlug, dict] = {
    GarmentSlug.HOODIE: {
        "views": ["front", "back"],
        "mannequin_style": "invisible",
        "hood_state": "down",
        "special": "ribbed cuffs and hem visible, kangaroo pocket flat",
    },
    GarmentSlug.CREWNECK: {
        "views": ["front", "back"],
        "mannequin_style": "invisible",
        "special": "ribbed crew neck and cuffs visible",
    },
    GarmentSlug.JERSEY: {
        "views": ["front", "back"],
        "mannequin_style": "flat_lay",
        "special": (
            "number and lettering detail must be sharp and legible; "
            "no mannequin drape -- use flat lay on pure white surface; "
            "alternating rose fill on numbers: front left=rose right=plain, "
            "back left=plain right=rose"
        ),
    },
    GarmentSlug.JOGGERS: {
        "views": ["front", "back"],
        "mannequin_style": "invisible",
        "special": "full length shot; waistband detail crop required; tapered ankle visible",
    },
    GarmentSlug.SHORTS: {
        "views": ["front", "back"],
        "mannequin_style": "invisible",
        "special": "inseam length visible; waistband and print detail",
    },
    GarmentSlug.SHIRT: {
        "views": ["front", "back"],
        "mannequin_style": "invisible",
        "special": "graphic detail close-up crop required",
    },
    GarmentSlug.JACKET: {
        "views": ["front", "back", "open"],
        "mannequin_style": "invisible",
        "special": "show both open and closed; collar and cuff detail shots",
    },
    GarmentSlug.BEANIE: {
        "views": ["front", "on_head"],
        "mannequin_style": "product_flat",
        "special": "embroidery detail close-up; flat lay shows inner label",
    },
    GarmentSlug.FANNY_PACK: {
        "views": ["front", "back"],
        "mannequin_style": "product_flat",
        "special": "hardware clip detail; worn-model scale reference",
    },
    GarmentSlug.SET: {
        "views": ["set_together", "top", "bottom"],
        "mannequin_style": "invisible",
        "special": "complete set on mannequin; then individual pieces separately",
    },
    GarmentSlug.UNKNOWN: {
        "views": ["front"],
        "mannequin_style": "invisible",
        "special": "",
    },
}


def infer_garment(product_name: str, garment_type_lock: str = "") -> GarmentSlug:
    """Infer GarmentSlug from product name, with optional lock override.

    garment_type_lock: if set (from CSV garment_type_lock column), use directly.
    Otherwise, match _KEYWORD_MAP in order (longer phrases first).
    """
    if garment_type_lock:
        try:
            return GarmentSlug(garment_type_lock.strip().lower())
        except ValueError:
            pass  # bad lock value -- fall through to inference

    name_lower = product_name.lower()
    for keyword, slug in _KEYWORD_MAP:
        if keyword in name_lower:
            return slug
    return GarmentSlug.UNKNOWN


def ghost_params(slug: GarmentSlug) -> dict:
    """Return ghost mannequin prompt parameters for this garment type."""
    return _GHOST_PARAMS.get(slug, _GHOST_PARAMS[GarmentSlug.UNKNOWN])
```

---

## Output Path Convention

### `skyyrose/core/output_paths.py` — New module

```python
# skyyrose/core/output_paths.py

from __future__ import annotations
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Ghost mannequin renders (pending human review before CSV update)
GHOST_MANNEQUIN_DIR = PROJECT_ROOT / "renders" / "ghost-mannequin"

# FASHN tryon renders (existing pipeline)
TRYON_DIR = PROJECT_ROOT / "renders" / "tryon"

# Elite Studio compositor output
COMPOSITOR_DIR = PROJECT_ROOT / "renders" / "compositor"


def ghost_front(sku: str) -> Path:
    """Canonical path: renders/ghost-mannequin/{sku}-ghost-front.webp"""
    return GHOST_MANNEQUIN_DIR / f"{sku}-ghost-front.webp"


def ghost_back(sku: str) -> Path:
    """Canonical path: renders/ghost-mannequin/{sku}-ghost-back.webp"""
    return GHOST_MANNEQUIN_DIR / f"{sku}-ghost-back.webp"


def tryon_render(sku: str, model_id: str, sample: int) -> Path:
    """Canonical path: renders/tryon/{sku}/{sku}-{model_id}-s{NN}.webp"""
    return TRYON_DIR / sku / f"{sku}-{model_id}-s{sample:02d}.webp"


def compositor_output(sku: str, view: str = "front") -> Path:
    """Canonical path: renders/compositor/{sku}-composite-{view}.webp"""
    return COMPOSITOR_DIR / f"{sku}-composite-{view}.webp"


def ensure_dirs() -> None:
    """Create all output directories if they do not exist."""
    for d in (GHOST_MANNEQUIN_DIR, TRYON_DIR, COMPOSITOR_DIR):
        d.mkdir(parents=True, exist_ok=True)
```

---

## Shared Product Adapter

### `skyyrose/core/product_adapter.py` — New module

This is the single import surface for all pipeline callers. Pipelines never
import `catalog_loader`, `bundle_map`, `garment`, or `output_paths` directly.

```python
# skyyrose/core/product_adapter.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from skyyrose.core import bundle_map as _bundle_map
from skyyrose.core import garment as _garment
from skyyrose.core import output_paths as _output_paths
from skyyrose.core.catalog_loader import read_catalog_rows, status_from_row


@dataclass(frozen=True)
class ProductBundle:
    """Complete product record for pipeline consumption.

    Combines CSV fields, resolved bundle paths, garment type, and
    canonical output paths into a single immutable object.
    """

    # From CSV
    sku: str
    name: str
    collection: str
    status: str  # 'live' | 'pre-order' | 'draft' | 'retired'
    price_usd: float
    branding_spec: str
    render_output_slug: str
    is_tech_flat: bool
    is_accessory: bool
    csv_image: str
    csv_front_model_image: str
    csv_back_image: str
    csv_back_model_image: str

    # Resolved from bundle (None if no bundle directory found)
    bundle_directory: Path | None
    techflat_front: Path | None
    techflat_back: Path | None
    source_photo: Path | None
    logo_ref: Path | None
    spec_text: str

    # Derived
    garment_slug: _garment.GarmentSlug
    ghost_render_params: dict[str, Any]

    # Output paths (directories not yet created -- call output_paths.ensure_dirs())
    out_ghost_front: Path
    out_ghost_back: Path

    @property
    def primary_source(self) -> Path | None:
        """Best available source image for rendering.

        Prefers real photography over techflat.
        For ghost mannequin runs, always use techflat_front instead.
        """
        return self.source_photo or self.techflat_front

    @property
    def has_bundle(self) -> bool:
        return self.bundle_directory is not None

    @property
    def ghost_ready(self) -> bool:
        """True if techflat-front exists on disk and can enter ghost pipeline."""
        return self.techflat_front is not None and self.techflat_front.exists()


def load_all(
    *,
    active_only: bool = True,
    collection: str | None = None,
    skus: list[str] | None = None,
) -> list[ProductBundle]:
    """Load all products from the canonical CSV as ProductBundle objects.

    Filters (all optional):
        active_only: exclude 'retired' products (default True)
        collection:  restrict to one collection slug
        skus:        restrict to an explicit list of SKUs
    """
    rows = read_catalog_rows()
    bundles = []
    for row in rows:
        sku = row["sku"].strip().lower()

        if skus is not None and sku not in [s.lower() for s in skus]:
            continue

        status = status_from_row(row)
        if active_only and status == "retired":
            continue

        col = row.get("collection", "").strip()
        if collection and col != collection:
            continue

        bundles.append(_row_to_bundle(sku, row, status))

    return bundles


def load_sku(sku: str) -> ProductBundle:
    """Load a single product by SKU. Raises KeyError if not found."""
    rows = read_catalog_rows()
    sku_lower = sku.strip().lower()
    for row in rows:
        if row["sku"].strip().lower() == sku_lower:
            status = status_from_row(row)
            return _row_to_bundle(sku_lower, row, status)
    raise KeyError(f"SKU {sku!r} not found in catalog")


def _row_to_bundle(sku: str, row: dict, status: str) -> ProductBundle:
    name = row.get("name", "").strip()
    garment_slug = _garment.infer_garment(
        name,
        garment_type_lock=row.get("garment_type_lock", "").strip(),
    )
    return ProductBundle(
        sku=sku,
        name=name,
        collection=row.get("collection", "").strip(),
        status=status,
        price_usd=float(row.get("price") or 0.0),
        branding_spec=row.get("branding_spec", "").strip(),
        render_output_slug=row.get("render_output_slug", sku).strip() or sku,
        is_tech_flat=row.get("render_is_tech_flat", "").strip() == "1",
        is_accessory=row.get("render_is_accessory", "").strip() == "1",
        csv_image=row.get("image", "").strip(),
        csv_front_model_image=row.get("front_model_image", "").strip(),
        csv_back_image=row.get("back_image", "").strip(),
        csv_back_model_image=row.get("back_model_image", "").strip(),
        bundle_directory=_bundle_map.bundle_dir(sku),
        techflat_front=_bundle_map.techflat_front(sku),
        techflat_back=_bundle_map.techflat_back(sku),
        source_photo=_bundle_map.source_photo(sku),
        logo_ref=_bundle_map.logo_ref(sku),
        spec_text=_bundle_map.spec_text(sku),
        garment_slug=garment_slug,
        ghost_render_params=_garment.ghost_params(garment_slug),
        out_ghost_front=_output_paths.ghost_front(sku),
        out_ghost_back=_output_paths.ghost_back(sku),
    )
```

---

## How Pipelines Import from the Adapter

### renders/ (FASHN tryon pipeline)

`renders/config.py` does not exist on disk yet. It must be created. Replace
the inline `PRODUCT_CATALOG` dict construction with:

```python
# renders/config.py
from skyyrose.core.product_adapter import load_all, ProductBundle

PRODUCT_CATALOG: list[ProductBundle] = load_all(active_only=True)
```

The `renders/__main__.py` already imports `PRODUCT_CATALOG` from `renders.config`.
Once `renders/config.py` exists and returns `ProductBundle` objects, update
attribute access from `p["sku"]` dict-style to `p.sku` attribute-style throughout
`renders/__main__.py` and `renders/preflight.py`.

### scripts/nano_banana/ (rebuild)

Source .py files are gone (only .pyc remain). The rebuild becomes trivial:

```python
# scripts/nano_banana/catalog.py  (new file replacing deleted source)
from skyyrose.core.product_adapter import load_all, load_sku, ProductBundle

__all__ = ["load_all", "load_sku", "ProductBundle"]
```

All other nano_banana modules that previously imported from an internal catalog
module import from this shim instead.

### skyyrose/elite_studio/catalog.py (already correct -- minor fix needed)

The `Catalog` class already imports from `skyyrose.core.catalog_loader` correctly.

The one bug: `skyyrose/elite_studio/fashion/context.py` line 23 sets
`_CATALOG_PATH` to `data/product-catalog.csv` (retired path). Replace
`_load_catalog()` and the stale `_CATALOG_PATH` constant with a call to
`product_adapter.load_all()`, and replace the `garment_type` inference with
`garment.infer_garment(product_name)` from `skyyrose.core.garment`.

---

## Build Order

What must exist before what:

```
Step 1  skyyrose/core/bundle_map.py        stdlib + pathlib only
Step 2  skyyrose/core/garment.py           stdlib only
Step 3  skyyrose/core/output_paths.py      pathlib only
Step 4  skyyrose/core/product_adapter.py   steps 1-3 + catalog_loader.py (already exists)
Step 5  skyyrose/core/__init__.py update   expose the new public modules
---
Step 6  renders/config.py (create)         depends on step 4
Step 7  renders/__main__.py refactor       dict access -> attribute access
Step 8  renders/preflight.py refactor      remove _find_bundle_dir import (now in bundle_map)
---
Step 9  scripts/nano_banana/catalog.py (rebuild)  depends on step 4
---
Step 10 elite_studio/fashion/context.py fix  replace stale CSV path with product_adapter
---
Step 11 ghost mannequin batch script        depends on steps 4, 3
Step 12 CSV front_model_image update tool   depends on step 11 + human review gate
```

Steps 1-5: one commit ("feat(core): canonical bundle map + garment router + output paths + product adapter")
Steps 6-8: one commit ("refactor(renders): wire FASHN pipeline to product adapter")
Step 9: one commit ("refactor(nano-banana): rebuild catalog module from product adapter")
Step 10: one commit ("fix(elite-studio): replace stale catalog path in fashion context")
Steps 11-12: separate commits, step 12 blocked by human approval.

---

## Data Flow

```
CSV row
  -> read_catalog_rows()       [catalog_loader]
  -> status_from_row()         [catalog_loader]
  -> infer_garment(name)       [garment]
  -> bundle_dir(sku)           [bundle_map]  <-- reads manifest.json once, lru_cached
  -> techflat_front(sku)       [bundle_map]
  -> ghost_front(sku)          [output_paths]
  -> ProductBundle (frozen)    [product_adapter]

ProductBundle consumed by:
  ghost mannequin pipeline  reads .techflat_front  writes to .out_ghost_front
  FASHN tryon pipeline      reads .primary_source  writes to tryon_render(sku, model, sample)
  Elite Studio compositor   reads .branding_spec, .logo_ref, .garment_slug
  CSV update tool           reads .out_ghost_front (after review), writes CSV front_model_image
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Name-based bundle lookup

What goes wrong: resolving `data/product-bundles/` directories by matching
the CSV `name` field to the directory name. 15 of 30 products have mismatches
(em dashes, apostrophes, capitalization differences).

Prevention: always index on `manifest.json["sku"]`. Directory names are
irrelevant to the lookup.

### Anti-Pattern 2: Multiple CSV readers

What goes wrong: `fashion/context.py` currently opens `data/product-catalog.csv`
(retired path) independently of `catalog_loader.py`. Two read paths diverge silently.

Prevention: all CSV access goes through `catalog_loader.read_catalog_rows()`.
No other code opens the CSV file directly.

### Anti-Pattern 3: Inline product dicts in pipeline config

What goes wrong: building `PRODUCT_CATALOG` as a static hardcoded list,
separate from the CSV. Adding a new product requires editing two files.

Prevention: `renders/config.py` calls `product_adapter.load_all()` at import
time. The CSV is the only place to add a product.

### Anti-Pattern 4: garment_type_lock in override JSON only

What goes wrong: the garment type lock lives in
`skyyrose/elite_studio/prompts/overrides/` (camelCase `garmentTypeLock`)
and is not available to other pipelines.

Prevention: add a `garment_type_lock` column to the CSV. The `product_adapter`
reads it and passes it to `infer_garment()`. Override JSONs continue to work
for elite-studio-specific overrides, but the garment type is authoritative
from the CSV for all pipelines.

### Anti-Pattern 5: Output path construction in each pipeline

What goes wrong: each pipeline constructs its own output path string, which
cannot be referenced from the CSV update tool without duplicating the string logic.

Prevention: all output paths come from `output_paths.py`. The CSV update
tool imports the same function and knows exactly where to look.

---

## Scalability Considerations

| Concern | Current (30 products) | Future (300+ products) |
|---|---|---|
| Bundle index | lru_cache on `_load_index()`, one disk scan at startup | Same -- scale is fine |
| CSV load | ~1ms | Add lru_cache to read_catalog_rows if called in tight loops |
| Output dirs | Flat `ghost-mannequin/` directory | Add `sku[:2]/` sharding if >1000 files |
| Ghost batch | Sequential by default | Add `--workers N` for concurrent execution |

---

## Confidence Assessment

| Area | Confidence | Basis |
|---|---|---|
| Bundle map design | HIGH | Read manifest.json in multiple bundle dirs; sku field present and correct in all checked |
| Garment types | HIGH | Read `fashion/knowledge.py` catalogue + `fashion/context.py` keywords; cross-checked all 30 CSV product names |
| Output path convention | HIGH | `renders/ghost-mannequin/{sku}-ghost-front.webp` matches PROJECT.md requirement explicitly |
| Adapter import safety | HIGH | Dependency chain verified: `core/` imports only stdlib; no pipeline imports `core/` creating a cycle |
| renders/config.py | MEDIUM | `__main__.py` imports `renders.config` but the file is not on disk. Must be created as part of Step 6. |
| nano_banana catalog | LOW | Source .py files deleted; only .pyc remain in `__pycache__`. Module must be rebuilt. Rebuilt module structure assumed from cache filenames. |
| fashion/context.py stale path | HIGH | Line 23 confirmed: `_CATALOG_PATH = Path(...) / "data" / "product-catalog.csv"` -- retired file path |

## Sources

All findings derived from direct file reads in this session:

- `/Users/theceo/DevSkyy/skyyrose/core/catalog_loader.py`
- `/Users/theceo/DevSkyy/skyyrose/elite_studio/catalog.py`
- `/Users/theceo/DevSkyy/skyyrose/elite_studio/fashion/context.py`
- `/Users/theceo/DevSkyy/skyyrose/elite_studio/fashion/knowledge.py`
- `/Users/theceo/DevSkyy/skyyrose/elite_studio/models.py`
- `/Users/theceo/DevSkyy/skyyrose/elite_studio/prompts/templates.py`
- `/Users/theceo/DevSkyy/renders/__init__.py`, `__main__.py`, `preflight.py`
- `/Users/theceo/DevSkyy/data/product-bundles/*/manifest.json` (multiple)
- `/Users/theceo/DevSkyy/.planning/PROJECT.md`
- CSV columns confirmed: `sku, name, price, collection, description, badge, image, front_model_image, back_image, back_model_image, sizes, color, edition_size, published, is_preorder, branding_spec, render_output_slug, render_source_override, render_back_source_override, render_is_tech_flat, render_is_accessory`
