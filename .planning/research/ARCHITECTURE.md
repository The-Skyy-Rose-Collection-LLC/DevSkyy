# Architecture Patterns

**Domain:** CSV-driven multi-pipeline imagery system (SkyyRose v1.2)
**Researched:** 2026-04-22
**Confidence:** HIGH — derived from reading actual source files, not inference

---

## Current State (What Exists)

### Canonical CSV Loader — Already Correct

`skyyrose/core/catalog_loader.py` exists with the correct interface:

```python
CATALOG_CSV          # Path constant pointing to the canonical CSV
read_catalog_rows()  # list[dict[str, str]] — raw CSV rows, skips blanks
bool_col(row, key)   # "1" → True coercion
int_col(row, key)    # str → int | None
status_from_row(row) # badge/is_preorder/published → status enum string
PRODUCT_STATUS       # {"draft", "pre-order", "live", "retired"}
```

This module is the confirmed foundation. Every pipeline imports from here. The
`skyyrose/elite_studio/catalog.py` `Catalog` class already imports from it
correctly. Nothing about this module changes in v1.2.

### nano_banana — Source Files Confirmed Present

`scripts/nano_banana/` is a Python package with all source `.py` files present
and compiled. Confirmed modules:

| Module | Role |
|---|---|
| `catalog.py` | Product loader — imports `skyyrose.core.catalog_loader` correctly |
| `source_map.py` | Hardcoded SKU→techflat path dict — the piece to REPLACE with bundle_map |
| `cli.py` | CLI with `dry-run`, `generate`, `composite`, `produce`, `produce-async` subcommands |
| `pipeline.py` | `ProductionPipeline` — 5-step orchestrator; uses `_find_bundle_dir(name)` |
| `generate.py` | Provider wrappers (Gemini, FLUX, GPT-Image) |
| `router.py` | `RouteDecision` — picks engine per garment features |
| `prompt_registry.py` | Prompt templates |
| `prompts.py` | Prompt construction |
| `config.py` | API config, provider clients |
| `client.py` | Client factory |
| `engine_fal.py` | fal.ai engine |
| `vision_describe.py` | Vision analysis |
| `tournament.py` | Best-of-N tournament |
| `utils.py` | Helpers |

**Critical finding:** `pipeline.py` currently has `_find_bundle_dir(name)` which
looks up bundles **by product name**. This is the root cause of the 15 name-mismatch
cases. The function must be replaced with a SKU-indexed lookup.

### Elite Studio — Partially Correct, Stub State

- `skyyrose/elite_studio/catalog.py` — correct, imports `skyyrose.core.catalog_loader`
- `skyyrose/elite_studio/agents/compositor_agent.py` — Phase B2 stub (raises `NotImplementedError`)
- The existing plan at `docs/superpowers/plans/2026-04-20-ghost-mannequin-pipeline.md` defines
  the dual-agent ghost mannequin pipeline for Elite Studio (Tasks 1-9, full TDD test stubs included)
- Elite Studio ghost mannequin goes through `LangGraph` + dual-agent (Claude Opus + Gemini via `gemini_rest.py`)

### renders/ — FASHN Tryon Pipeline (NOT Ghost Mannequin Output Dir)

`renders/` is a Python package for the **FASHN tryon pipeline** (on-model renders).
It is NOT the ghost mannequin output directory. Key files:

- `renders/preflight.py` — STOP AND SHOW implementation exists here. Reference this as the
  pattern for the ghost mannequin cost gate.
- `renders/__main__.py` — CLI entry for FASHN runs
- `renders/config.py` — Does NOT currently exist on disk. Must be created in Step 6.

The ghost mannequin output goes to `renders/ghost-mannequin/` — a subdirectory that
does not yet exist as a Python package. It is a plain directory containing `.webp` files.

### Bundle Directories — SKU is Authoritative

`data/product-bundles/` contains 32 directories. Each has a `manifest.json` with
a `sku` field. The bundle SKU is correct and authoritative for 30 of 32 entries.
The 2 outliers are variant SKUs (`br-003-giants`, `br-003-oakland`, `br-003-white`)
that are colorway variants of `br-003`.

**The 15 "name-mismatch" cases are resolved by indexing on `manifest.json["sku"]`**,
not on product name. They are only mismatches if you lookup by name. With SKU lookup
the mapping is clean. See the exact mismatches in the section below.

---

## The 15 Name-Mismatch Cases (Documented)

These are the cases where `manifest.json["name"]` differs from `CSV["name"]`.
They look like mismatches but resolve cleanly by SKU:

| SKU | CSV name | Bundle name in manifest.json | Resolution |
|---|---|---|---|
| br-003 | "BLACK is Beautiful Jersey Series: 0. Baseball Classic" | "BLACK is Beautiful Jersey" | SKU matches — OK |
| br-008 | "BLACK is Beautiful Jersey Series: 1. SF Inspired (Football)" | "BLACK is Beautiful Jersey Series: 1. SF inspired" | Case diff — OK by SKU |
| br-009 | "BLACK is Beautiful Jersey Series: 2. Last Oakland (Football)" | "BLACK is Beautiful Jersey Series: 2. LAST OAKLAND" | Case diff — OK by SKU |
| br-010 | "BLACK is Beautiful Jersey Series: 3. The Bay (Basketball)" | "BLACK is Beautiful Jersey Series: 3. THE BAY" | Case diff — OK by SKU |
| br-011 | "BLACK is Beautiful Jersey Series: 4. The Rose (Hockey)" | "BLACK is Beautiful Jersey Series: 4. THE ROSE (SHARKS EDITION)" | Case diff — OK by SKU |
| br-012 | "BLACK is Beautiful Jersey Series: 5. Last Oakland (Baseball)" | (no bundle) | Missing bundle — create or defer |
| kids-001 | "Kids Colorblock Hoodie Set — Red/Black" | "Kids Red Set" | SKU matches — OK |
| kids-002 | "Kids Colorblock Hoodie Set — Purple/Black" | "Kids Purple Set" | SKU matches — OK |
| lh-004 | "Love Hurts Bomber Jacket" | "Love Hurts Varsity Jacket" | SKU matches — OK |
| lh-005 | "The Fannie" | "The Fannie" (manifest says lh-006) | SKU MISMATCH — CSV says lh-005, manifest says lh-006 |
| sg-015 | "The Windbreaker Set" | (no bundle) | Missing bundle — create or defer |

**The only genuine problems:**
- `lh-005` vs `lh-006`: the `manifest.json["sku"]` says `lh-006` but the CSV says `lh-005`. One of these is wrong. The ghost mannequin batch script must flag this SKU for manual resolution before running.
- `br-012` and `sg-015`: no bundle directory exists yet. Ghost script skips these.

---

## Recommended Architecture

### Layer Diagram

```
wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv
                         |
                         |  (single canonical source, never forked)
                         v
         skyyrose/core/catalog_loader.py  (EXISTS — no changes needed)
         +-----------------------------+
         | CATALOG_CSV constant        |
         | read_catalog_rows()         |
         | bool_col(), int_col()       |
         | status_from_row()           |
         +-------------+---------------+
                       |
          +------------+-------------------+
          v                                v
   skyyrose/core/bundle_map.py       skyyrose/core/garment.py
   (NEW — manifest.json index)       (NEW — GarmentSlug enum + prompt params)
                       |
                       v
          skyyrose/core/output_paths.py
          (NEW — canonical path constructors)
                       |
                       v
          skyyrose/core/product_adapter.py
          (NEW — ProductBundle; unified API for all pipelines)
                       |
          +------------+-----------+-------------+
          v            v           v             v
   renders/        nano_banana/  elite_studio/  scripts/
   config.py       catalog.py   catalog.py     ghost_mannequin.py
   (CREATE)        (REFACTOR)   (already OK)   (NEW)
```

### Component Boundaries

| Component | File | Responsibility | Imports |
|---|---|---|---|
| Raw loader | `skyyrose/core/catalog_loader.py` | CSV I/O, type coercions | stdlib only — unchanged |
| Bundle map | `skyyrose/core/bundle_map.py` | SKU to bundle directory via manifest.json index | `catalog_loader`, `pathlib`, `json`, `functools` |
| Garment router | `skyyrose/core/garment.py` | Name to GarmentSlug enum, ghost prompt params | stdlib only |
| Output paths | `skyyrose/core/output_paths.py` | Canonical output path constructors | `pathlib` only |
| Product adapter | `skyyrose/core/product_adapter.py` | `ProductBundle` frozen dataclass; unified load API | `bundle_map`, `garment`, `output_paths`, `catalog_loader` |
| Ghost batch script | `scripts/ghost_mannequin.py` | CLI batch orchestrator for ghost mannequin generation | `product_adapter`, cost gate, Gemini, fal, PIL |
| CSV update tool | `scripts/approve_ghost.py` | Approve/reject renders, update CSV `front_model_image` | `product_adapter`, `catalog_loader` |
| Cost gate | `skyyrose/core/cost_gate.py` | Shared STOP AND SHOW manifest + `input()` confirmation | stdlib only |

**No circular dependencies:** `core/` modules only import stdlib and each other in one direction.
Pipeline scripts import `product_adapter` only — never `catalog_loader`, `bundle_map`, `garment`,
or `output_paths` directly.

---

## Where the SKU-to-Bundle Mapping Lives

### Decision: `skyyrose/core/bundle_map.py` — Python module reading manifest.json files

The mapping indexes on `manifest.json["sku"]` at startup, cached with `lru_cache`. No name
normalization is needed for lookup — SKU is the key. The `_normalize()` helper is kept for
optional defensive search only.

```python
# skyyrose/core/bundle_map.py — key interface

@lru_cache(maxsize=1)
def _load_index() -> dict[str, Path]:
    """Read every manifest.json in data/product-bundles/. Returns {sku: dir_path}.
    Called once; lru_cached at module level."""

def bundle_dir(sku: str) -> Path | None:
    """Return bundle directory for sku, or None if not found."""

def techflat_front(sku: str) -> Path | None:
    """Return techflat-front.{jpeg,jpg,png} path, or None."""

def techflat_back(sku: str) -> Path | None:
    """Return techflat-back.{jpeg,jpg,png} path, or None."""

def source_photo(sku: str) -> Path | None:
    """Return source-photo.{jpeg,jpg,png} path, or None."""

def logo_ref(sku: str) -> Path | None:
    """Return logo-ref.{png,jpeg,jpg} path, or None."""

def spec_text(sku: str) -> str:
    """Return spec.txt content, or empty string."""

def all_mapped_skus() -> list[str]:
    """All SKUs with a bundle directory."""
```

### How the 3 pipelines import this

**nano_banana:** `pipeline._find_bundle_dir(name)` is replaced by `bundle_map.bundle_dir(sku)`.
The `source_map.py` module (hardcoded dict) is deprecated and replaced by `bundle_map`.

**Elite Studio:** `skyyrose/elite_studio/agents/vision_agent.py` currently constructs its own
reference path. Replace `_reference_path(sku)` to call `bundle_map.source_photo(sku) or bundle_map.techflat_front(sku)`.

**renders/ (FASHN):** `renders/preflight.py._detect_resolution_method()` calls `_find_bundle_dir(name)`
from `renders.config`. Replace with `bundle_map.bundle_dir(sku)`.

---

## Ghost Mannequin Batch Script

### Location: `scripts/ghost_mannequin.py` (NEW file)

Pattern: follows `scripts/nano_banana/cli.py` — argparse with subcommands.

**Key design decisions:**
1. The script is a thin CLI shell. Generation logic delegates to a `GhostPipeline` class.
2. `GhostPipeline` uses the same provider wrappers already in `scripts/nano_banana/generate.py`
   (Gemini 2.5 Flash Image, FLUX Fill Pro, PIL). No new provider code needed.
3. The STOP AND SHOW gate runs before the first API call, shared via `skyyrose/core/cost_gate.py`.
4. Output goes to `renders/ghost-mannequin/{sku}-ghost-front.webp` — this directory
   is separate from the `renders/` Python package (FASHN pipeline).

```
scripts/ghost_mannequin.py
    ↓ argparse: generate --sku br-001 | --all | --collection black-rose | --dry-run
    ↓ load ProductBundle objects via product_adapter.load_all()
    ↓ filter: ghost_ready == True (has techflat-front on disk)
    ↓ STOP AND SHOW cost manifest (cost_gate.confirm())
    ↓ for each product:
         Stage 1: fal_client BRIA RMBG 2.0 → alpha matte
         Stage 2: Gemini 2.5 Flash Image → ghost mannequin generation
                  if collar fail → FLUX Fill Pro inpaint (collar zone only)
         Stage 3: Gemini Flash QA → structured pass/fail check
                  if fail → log to review_queue, skip write
         Stage 4: PIL composite on #FFFFFF → pure white guarantee
         write: renders/ghost-mannequin/{sku}-ghost-front.webp
         log: per-SKU result to renders/ghost-mannequin/batch-log.json
```

**CLI interface mirrors nano-banana:**

```bash
python scripts/ghost_mannequin.py generate --sku br-001
python scripts/ghost_mannequin.py generate --all
python scripts/ghost_mannequin.py generate --collection black-rose
python scripts/ghost_mannequin.py generate --dry-run        # STOP AND SHOW only, no API calls
python scripts/ghost_mannequin.py approve --sku br-001      # delegates to approve_ghost.py
python scripts/ghost_mannequin.py reject --sku br-001 --reason "collar collapsed"
```

**Integration with existing nano-banana pipeline:**
- Does NOT call `nano_banana.pipeline.ProductionPipeline`. That pipeline is for on-model
  renders (tryon style). Ghost mannequin is a separate, simpler 4-stage pipeline.
- Shares provider auth: same `.env.secrets`, same `fal_client`, same `google.genai` client.
- Does NOT use `nano_banana.router` — routing for ghost mannequin is simpler: Gemini
  2.5 Flash Image for all SKUs, FLUX Fill Pro only as collar fallback.
- Prompt templates are defined in the ghost script itself (`_GHOST_PROMPT_TEMPLATE`,
  `_JERSEY_ADDITIONS`, `_COLLAR_FALLBACK_PROMPT`). Not in `nano_banana.prompt_registry`.

**Integration with Elite Studio ghost mannequin (Plan B2):**
- `scripts/ghost_mannequin.py` is the **batch CLI** for 30-product runs from techflats.
- `skyyrose/elite_studio/` ghost mannequin (the plan doc) is the **dual-agent LangGraph pipeline**
  for single-SKU high-fidelity generation with dual vision consensus.
- They are parallel, not sequential. Both write to `renders/ghost-mannequin/`.
- For v1.2, `scripts/ghost_mannequin.py` is the primary deliverable. Elite Studio Phase B2
  is a follow-on milestone.

---

## STOP AND SHOW Cost Gate

### Location: `skyyrose/core/cost_gate.py` (NEW file)

**Why here:** The STOP AND SHOW gate must be shared across all three pipelines
(`renders/`, `nano_banana/`, `scripts/ghost_mannequin.py`). It cannot live in
one pipeline and be imported by the others — that creates a cross-layer dependency.
`skyyrose/core/` is the correct home (stdlib-only imports, no pipeline dependencies).

**Pattern:** Based on `renders/preflight.py` which already implements the canonical
STOP AND SHOW format. Extract the display + confirmation logic into a reusable module.

```python
# skyyrose/core/cost_gate.py — key interface

@dataclass
class CostLineItem:
    stage: str          # "Stage 1: BRIA RMBG 2.0"
    tool: str           # "fal.ai"
    cost_per_item: float
    item_count: int
    subtotal: float
    notes: str = ""

@dataclass
class CostManifest:
    action: str         # "Ghost mannequin batch — 30 SKUs"
    items: list[CostLineItem]
    total_usd: float
    sku_list: list[str]

class PreflightAborted(RuntimeError):
    """Raised when user declines or source files are missing."""

def confirm(manifest: CostManifest, *, skip: bool = False) -> None:
    """Print manifest table + prompt for 'y'. Raise PreflightAborted if declined.

    skip=True for CI/non-interactive contexts (--skip-preflight flag).
    Follows the CLAUDE.md STOP AND SHOW format exactly.
    """

def build_ghost_manifest(products: list[ProductBundle]) -> CostManifest:
    """Build cost manifest for a ghost mannequin batch run."""

def build_tryon_manifest(products, num_models, num_samples) -> CostManifest:
    """Build cost manifest for a FASHN tryon run (replaces renders/preflight logic)."""
```

**Migration path for existing pipelines:**
- `renders/preflight.py` continues to work unchanged in v1.2. The `cost_gate` module
  is the target state for v1.3 when `renders/preflight.py` is refactored.
- `scripts/ghost_mannequin.py` uses `cost_gate` directly from the start.
- `nano_banana/cli.py` currently shows `--- Cost Estimate ---` inline in `cmd_produce`.
  It uses `router.estimate_batch_cost()`. Migrate to `cost_gate.confirm()` in the
  refactor step (Step 9).

---

## CSV `front_model_image` Update Tool

### Location: `scripts/approve_ghost.py` (NEW file)

**How it integrates safely with the canonical CSV:**

The CSV is a plain text file. Updating it in-place requires a read-modify-write
that preserves all other fields and row order exactly. The tool must:

1. Read the entire CSV with `csv.DictReader`
2. Find the row where `sku == target_sku`
3. Update `front_model_image` to the relative path of the approved render
4. Write all rows back with `csv.DictWriter` using the same fieldnames in the same order
5. Validate: re-read the CSV and confirm the update is correct before returning

**The canonical relative path format** (from existing CSV rows):
```
assets/images/products/{sku}-ghost-front.webp
```
This is the WordPress theme path. Before updating the CSV, the approved render
must be copied from `renders/ghost-mannequin/{sku}-ghost-front.webp` to
`wordpress-theme/skyyrose-flagship/assets/images/products/{sku}-ghost-front.webp`.

```python
# scripts/approve_ghost.py — CLI

# approve: copies render to wp assets dir, updates CSV front_model_image
python scripts/approve_ghost.py approve --sku br-001

# reject: logs rejection reason to renders/ghost-mannequin/rejected.json
python scripts/approve_ghost.py reject --sku br-001 --reason "collar collapsed"

# status: shows all pending/approved/rejected renders
python scripts/approve_ghost.py status
```

**Shared via `scripts/ghost_mannequin.py`:**
The ghost mannequin batch script's `approve` and `reject` subcommands delegate to
`approve_ghost.py` functions. They are in a separate file because approval is a
separate concern from generation and may be run days later.

**Safety rules:**
- Never overwrite a `front_model_image` that already has a real value without `--force`.
- Always print the old value and new value before writing.
- The CSV write is atomic: write to a `.tmp` file, rename to replace.

---

## Data Flow (End to End)

```
skyyrose-catalog.csv
    ↓ read_catalog_rows()  [catalog_loader]
    ↓ status_from_row()    [catalog_loader]
    ↓ infer_garment(name)  [garment]
    ↓ bundle_dir(sku)      [bundle_map] ← reads manifest.json once, lru_cached
    ↓ techflat_front(sku)  [bundle_map]
    ↓ ghost_front(sku)     [output_paths]
    ↓ ProductBundle        [product_adapter] — frozen, immutable

ProductBundle consumed by:
    ghost_mannequin.py      .techflat_front → generation → .out_ghost_front
    renders/__main__.py     .primary_source → FASHN → tryon_render()
    elite_studio/catalog.py .branding_spec, .logo_ref → compositor
    approve_ghost.py        .out_ghost_front → copy to WP assets → CSV update
```

---

## Build Order (Respecting Dependencies)

```
Step 1   skyyrose/core/bundle_map.py      NEW     stdlib + pathlib only
Step 2   skyyrose/core/garment.py         NEW     stdlib only
Step 3   skyyrose/core/output_paths.py    NEW     pathlib only
Step 4   skyyrose/core/product_adapter.py NEW     steps 1-3 + catalog_loader (exists)
Step 5   skyyrose/core/cost_gate.py       NEW     stdlib only
         [commit: feat(core): canonical bundle map + garment + output paths + adapter + cost gate]

Step 6   renders/config.py                CREATE  imports product_adapter
Step 7   renders/__main__.py              REFACTOR dict access → attribute access
Step 8   renders/preflight.py             REFACTOR replace _find_bundle_dir(name) with bundle_map.bundle_dir(sku)
         [commit: refactor(renders): wire FASHN pipeline to product adapter]

Step 9   scripts/nano_banana/pipeline.py  MODIFY  replace _find_bundle_dir(name) with bundle_map.bundle_dir(sku)
Step 10  scripts/nano_banana/source_map.py RETIRE  replace calls with bundle_map equivalents
         [commit: refactor(nano-banana): replace name-based bundle lookup with SKU-indexed bundle_map]

Step 11  scripts/ghost_mannequin.py       CREATE  depends on steps 1-5
Step 12  scripts/approve_ghost.py         CREATE  depends on step 11 (review gate)
         [commit: feat(imagery): ghost mannequin batch script + approve/reject CSV update tool]

Step 13  skyyrose/elite_studio — lh-005/lh-006 sku mismatch in manifest.json resolved manually
         [commit: fix(bundles): correct lh-006 manifest sku to lh-005]
```

Steps 1-5 are strictly independent of each other at the file level and can be
written in a single commit. Each step only depends on files that exist before it
in the sequence.

Steps 11-12 are blocked by steps 1-5 completing (need `ProductBundle` and `cost_gate`).
Steps 6-10 are blocked by step 4 completing. Steps 6-10 are independent of each other
and can be done in any order.

Step 13 must happen before the ghost mannequin batch runs `lh-005`.

---

## New vs Modified Files

### New Files

| File | Type | Why New |
|---|---|---|
| `skyyrose/core/bundle_map.py` | Core module | SKU→bundle resolution; needed by all pipelines |
| `skyyrose/core/garment.py` | Core module | Garment type routing; currently private to elite_studio |
| `skyyrose/core/output_paths.py` | Core module | Canonical output paths; needed by script + CSV tool |
| `skyyrose/core/product_adapter.py` | Core module | Unified `ProductBundle`; single import for pipelines |
| `skyyrose/core/cost_gate.py` | Core module | Shared STOP AND SHOW gate |
| `renders/config.py` | Pipeline config | Doesn't exist yet; `__main__.py` imports it |
| `scripts/ghost_mannequin.py` | Batch script | Main deliverable for v1.2 |
| `scripts/approve_ghost.py` | CLI tool | CSV update after review approval |

### Modified Files

| File | What Changes |
|---|---|
| `skyyrose/core/__init__.py` | Expose new public modules (`bundle_map`, `garment`, `output_paths`, `product_adapter`, `cost_gate`) |
| `scripts/nano_banana/pipeline.py` | Replace `_find_bundle_dir(name)` with `bundle_map.bundle_dir(sku)` |
| `scripts/nano_banana/source_map.py` | Retire hardcoded dict; replace with calls to `bundle_map` |
| `renders/__main__.py` | Dict-style `p["sku"]` access → attribute-style `p.sku` |
| `renders/preflight.py` | Replace `_find_bundle_dir(name)` import with `bundle_map.bundle_dir(sku)` |
| `data/product-bundles/The Fannie/manifest.json` | Fix `sku` from `lh-006` to `lh-005` (genuine SKU mismatch) |

### Untouched Files

| File | Reason |
|---|---|
| `skyyrose/core/catalog_loader.py` | Already correct; interface is stable |
| `skyyrose/elite_studio/catalog.py` | Already imports `catalog_loader` correctly |
| `skyyrose/elite_studio/agents/` | Phase B2 plan is a separate milestone |
| `wordpress-theme/` PHP files | PHP catalog helpers are independent of Python pipelines |

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Name-based bundle lookup

The current `pipeline._find_bundle_dir(name)` matches the product name against
bundle directory names. This breaks for 11 of 30 products (em dashes, apostrophes,
capitalization, name changes). **Never index on name. Always use SKU via `manifest.json["sku"]`.**

### Anti-Pattern 2: Writing CSV fields in multiple places

The `front_model_image` column must only be written by `approve_ghost.py`. Ghost generation
writes to `renders/ghost-mannequin/` (pending). Only the explicit approval step touches
the canonical CSV. Any other code that writes CSV fields directly is a reliability hazard.

### Anti-Pattern 3: Ghost batch script calling FASHN or Elite Studio

Ghost mannequin is a separate, simpler pipeline. It does not compose with the FASHN
tryon pipeline (`renders/`) or the Elite Studio compositor (`skyyrose/elite_studio/`).
The three pipelines share only the CSV adapter and cost gate — not generation logic.

### Anti-Pattern 4: Hardcoded cost constants in script files

Cost per API call changes. The `_COST_PER_SAMPLE`, `_BG_REMOVE_COST` constants currently
duplicated in `renders/preflight.py` should not be duplicated again in `ghost_mannequin.py`.
They live in `cost_gate.py` and are imported from there.

### Anti-Pattern 5: Output path construction in each pipeline

Each pipeline must call `output_paths.ghost_front(sku)` / `output_paths.ghost_back(sku)`.
No pipeline should construct the `renders/ghost-mannequin/{sku}-ghost-front.webp` string
inline. The CSV update tool imports the same function and knows exactly where to look.

---

## Confidence Assessment

| Area | Confidence | Basis |
|---|---|---|
| Bundle map design | HIGH | Read manifest.json in 5+ bundle dirs; sku field confirmed present and correct |
| nano_banana source files | HIGH | Confirmed present — source .py files exist in `scripts/nano_banana/` |
| renders/ = FASHN pipeline | HIGH | Read `renders/preflight.py` — cost constants are FASHN-specific ($0.075/image) |
| STOP AND SHOW pattern | HIGH | Full implementation confirmed in `renders/preflight.py` |
| ghost_mannequin.py not yet existing | HIGH | No file found; must be created |
| renders/config.py not existing | HIGH | Confirmed missing; `__main__.py` imports it |
| lh-005/lh-006 sku mismatch | HIGH | Confirmed: `The Fannie/manifest.json` has `"sku": "lh-006"` but catalog says lh-005 |
| br-012 / sg-015 missing bundles | HIGH | Confirmed: no bundle directory for either |
| Cost gate shared module | MEDIUM | Pattern clear from `renders/preflight.py`; new module needs writing |
| Garment types | HIGH | Read `scripts/nano_banana/router.py` + all 30 CSV product names |

## Sources

All findings derived from direct file reads and pyc decompilation in this session:

- `/Users/theceo/DevSkyy/skyyrose/core/catalog_loader.py` — read in full
- `/Users/theceo/DevSkyy/skyyrose/elite_studio/catalog.py` — read in full
- `/Users/theceo/DevSkyy/scripts/nano_banana/__pycache__/*.pyc` — all modules decompiled (strings + names)
- `/Users/theceo/DevSkyy/renders/preflight.py` — read in full
- `/Users/theceo/DevSkyy/docs/superpowers/plans/2026-04-20-ghost-mannequin-pipeline.md` — read in full
- `data/product-bundles/*/manifest.json` — all 32 manifests read via cross-reference script
- `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` — headers + 5 rows confirmed
- Cross-reference script output: 19/30 exact matches; 11 mismatches catalogued
