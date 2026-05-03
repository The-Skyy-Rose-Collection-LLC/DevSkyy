# Seed Index: claude-mem Observations (`~/.claude-mem/claude-mem.db`)

**Phase 0 seeding date:** 2026-05-03
**Total DevSkyy observations:** 1,300
**How to use:** Reference `[cmem #NNN]` in KB entries and OpenWolf memory rows. Full observation text is retrievable via `sqlite3 ~/.claude-mem/claude-mem.db "SELECT * FROM observations WHERE id=NNN"`. The digest at `.wolf/claude-mem-digest.md` holds the last 25 auto-synced observations (refreshed at SessionStart).

---

## Domain Index

### WordPress / WooCommerce / PHP Theme

These observations document template architecture, enqueue patterns, WooCommerce hook integration, and deploy verification.

| ID | Type | What it documents |
|----|------|-------------------|
| [cmem #34] | discovery | Homepage architecture in skyyrose-flagship — Three.js portals, collection rings, particles |
| [cmem #45] | discovery | New mascot PHP files pass PHP syntax check (add_action / wp_enqueue patterns) |
| [cmem #58] | discovery | `enqueue.php` layered dependency chain — template slug detection, asset loading order |
| [cmem #262] | discovery | `enqueue.php` WordPress hook priority order — why priority matters for asset loading |
| [cmem #324] | discovery | WooCommerce integration file structure in skyyrose-flagship (hook registration locations) |
| [cmem #329] | discovery | WooCommerce hook registration priorities |
| [cmem #374] | discovery | `skyyrose_complete_the_look` hook at priority 50 |
| [cmem #564] | bugfix | Missing Phase 4 add_action hook injected into enqueue.php |
| [cmem #924] | bugfix | `'single'` slug corrected to `'single-product'` in Phase 4 enqueue; is_singular fallback removed |
| [cmem #959] | bugfix | enqueue.php Phase 4 asset guard logic reordered and single product slug fixed |
| [cmem #1062] | bugfix | Preorder gateway fake `$fallback_products` replaced with Catalog SoT |
| [cmem #1103] | bugfix | Footer help links — size guide now opens modal, care instructions points to FAQ |

### Three.js / Immersive Experiences

These observations document the Three.js experience engine, GLB models, and the immersive template architecture.

| ID | Type | What it documents |
|----|------|-------------------|
| [cmem #64] | feature | `skyy-3d.js` — full Three.js GLB character viewer with state machine event integration |
| [cmem #65] | discovery | `enqueue.php` wires `SKYY_3D_CONFIG.modelUrl` via `wp_localize_script` + pre-existing Three.js addon system |
| [cmem #106] | discovery | Skyy 3D mascot Three.js implementation — file paths, loader, animations |
| [cmem #260] | discovery | Three.js collection experience files — named per collection (blackrose, lovehurts, signature) |
| [cmem #241] | discovery | Experience engine has PHP backend in WordPress theme |
| [cmem #1203] | discovery | Immersive Love-Hurts template exists (template-immersive-love-hurts.php) |
| [cmem #1207] | discovery | Immersive Love-Hurts template full architecture revealed |
| [cmem #1276] | refactor | Love Hurts immersive: 2-room architecture retired, replaced with single cathedral scene |
| [cmem #1280] | discovery | Immersive theme file inventory: five core files, 1,416 lines total |
| [cmem #1283] | discovery | Black Rose immersive template — 2-room structure with `skyyrose_immersive_product()` helper |
| [cmem #1287] | refactor | Love Hurts refactored to use `skyyrose_immersive_product()` adapter pattern — 70-line reduction |
| [cmem #1288] | discovery | Love Hurts post-refactor metrics: 103 lines, 70-line net reduction, PHP clean |

**Key insight from this category:** `skyyrose_immersive_product()` in `inc/immersive-product-adapter.php` is the canonical adapter for all immersive templates. Using it eliminates ~70 lines per template vs direct WC queries. [cmem #1287]

### Catalog / SKU / Dossier / Product Data

These observations trace the evolution from `catalog.yaml` / `manifest.json` to the current CSV-SoT architecture.

| ID | Type | What it documents |
|----|------|-------------------|
| [cmem #581] | decision | Real data required for product replica pipeline (no mock data, real CSV) |
| [cmem #723] | decision | `catalog.yaml` declared single source of truth; MEMORY.md product data deprecated |
| [cmem #798] | bugfix | `Catalog._from_dict()` strict= parameter signature fixed |
| [cmem #848] | bugfix | Catalog.py: removed broken duplicate SKU detection from `_validate_integrity` |
| [cmem #852] | bugfix | catalog.py silent skips converted to loud errors |
| [cmem #1043] | decision | Preorder gateway fallback products rewired to catalog SoT |
| [cmem #1062] | bugfix | Preorder gateway rewired — PHP now reads from `skyyrose_get_product_catalog()` |
| [cmem #1080] | bugfix | Retired sg-004 override removed — elite studio SKU count now matches active catalog |
| [cmem #1134] | bugfix | PHP and catalog.yaml pre-order scopes synchronized at 7 SKUs |
| [cmem #1282] | discovery | `product-catalog.php` — full SKU registry and API surface for skyyrose-flagship |

**Key insight from this category:** Every catalog integrity bug traces back to a second source of truth being created or a string comparison against directory names instead of normalized SKU identifiers. [cmem #852]

### Pipeline / Imagery / Compositor

These observations document the Elite Studio compositor, rendering pipeline, and the scorched-earth rebuild.

| ID | Type | What it documents |
|----|------|-------------------|
| [cmem #572] | decision | Compositor retrofit: instrument-first over full refactor (telemetry before circuit breaker) |
| [cmem #576] | decision | Composer pipeline: instrument-first telemetry chosen — rationale logged |
| [cmem #606] | decision | Cerebrum principle: "instrument-first" — measure before enforcing fidelity gate |
| [cmem #608] | decision | Rejected "generate 100% replicas" framing; adopted reference-first pipeline as defensible commercial claim |
| [cmem #619] | bugfix | `compositor_agent.py` fidelity gate now distinguishes pending masters from missing masters |
| [cmem #621] | discovery | Bootstrap dry-run confirms 30-SKU catalog seeds correctly with 0 locked entries |
| [cmem #647] | discovery | First live vision test: kids collection returns NO MATCH for both SKUs |
| [cmem #653] | decision | Four vision test key learnings committed to cerebrum.md |
| [cmem #1071] | decision | Full catalog Elite Studio batch render approved and started |
| [cmem #1135] | decision | Elite Studio re-run queued for sg-008, sg-013, sg-014 |
| [cmem #1166] | decision | Verification gate rule: external artifacts fire unconditionally |
| [cmem #1218] | feature | Love-Hurts template refactored to single cathedral scene with SKU-keyed hotspots |

**Key insight from this category:** The scorched-earth rebuild (April 2026, 16,950 lines deleted) was caused by wrong source data — prompts reading `data/product-specs.json` instead of the CSV's `branding_spec` column. QA scored images 100 because it measured image quality, not product identity. [cmem #581]

### Security

These observations document security fixes, TenantMiddleware hardening, and credential management.

| ID | Type | What it documents |
|----|------|-------------------|
| [cmem #366] | bugfix | `test_security.py` all 5 `RequestSigner` imports fixed to explicit SDK path |
| [cmem #1185] | discovery | Tenant middleware: JWT claim extraction without verification (pre-fix state) |
| [cmem #1192] | bugfix | Tenant middleware: X-Tenant-ID header now requires shared secret verification |
| [cmem #1193] | bugfix | Tenant spoofing vulnerability fixed: X-Tenant-ID now HMAC-verified |
| [cmem #1195] | bugfix | Critical: JWT tenant claims now fully verified in tenant middleware |
| [cmem #1273] | discovery | Security, escaping, and asset header audit: all clear with one git gap |
| [cmem #1278] | decision | TenantMiddleware security hardening: X-Tenant-ID requires internal service token |

**Key insight from this category:** Before the 2026-05 hotfix, X-Tenant-ID was trusted from any HTTP client with no verification — a complete tenant spoofing vulnerability. [cmem #1185, #1193]

### Decision-Type Observations (Highest-Value for ADRs)

These are typed `decision` in the DB — the most load-bearing observations for understanding why the architecture is the way it is.

| ID | Type | What it documents |
|----|------|-------------------|
| [cmem #11] | decision | Agent self-configuration via startup CLAUDE.md |
| [cmem #195] | decision | Git staging strategy: large GLB files excluded, all CLAUDE.md files auto-staged |
| [cmem #347] | decision | CSS scroll-driven animations selected for homepage interactions |
| [cmem #350] | decision | Drop mechanics and 3D/AR product features identified as homepage requirements |
| [cmem #382] | decision | Source of truth refactoring initiated across root directory |
| [cmem #429] | decision | Canonical architecture rules codified in `.wolf/cerebrum.md` |
| [cmem #444] | decision | Single source of truth refactor initiated across all repo components |
| [cmem #499] | decision | Goal: clean, functional, professional repository configuration |
| [cmem #572] | decision | Compositor retrofit: instrument-first over full refactor |
| [cmem #790] | decision | Shift to prevention-first strategy + prompt library for production components |
| [cmem #807] | decision | Jersey series renamed to "The Jersey Series" with mandatory membership rule |
| [cmem #886] | decision | Permanent fix planned for `renders/preflight.py` mypy dual-module error |
| [cmem #989] | decision | Parallel workstream split: PR agent + WordPress commercial build |
| [cmem #1034] | decision | WooCommerce automation session adopts verify → plan → approve protocol |
| [cmem #1042] | decision | Product image authenticity requirement enforced |
| [cmem #1044] | decision | Per-SKU source imagery audit required before any image generation |
| [cmem #1070] | decision | Full SOT sync plan for catalog.yaml ↔ overrides ↔ source-products |
| [cmem #1082] | decision | Product asset pipeline design direction |
| [cmem #1162] | decision | Love Hurts collection page: three implementation paths evaluated |
| [cmem #1166] | decision | Verification gate rule: external artifacts fire unconditionally |
| [cmem #1196] | decision | Cathedral image selected and approved for use |
| [cmem #1215] | decision | Cathedral image approved for Love-Hurts immersive experience |
| [cmem #1278] | decision | TenantMiddleware security hardening rationale |

---

## SQLite Access Patterns

When you need to look up an observation beyond what's in this index:

```bash
# Get full text of a specific observation
sqlite3 ~/.claude-mem/claude-mem.db "SELECT id, type, title, content FROM observations WHERE id=NNN AND project='DevSkyy'"

# Search by title keyword
sqlite3 ~/.claude-mem/claude-mem.db "SELECT id, type, title FROM observations WHERE project='DevSkyy' AND title LIKE '%<keyword>%' ORDER BY id DESC LIMIT 20"

# All decisions for this project
sqlite3 ~/.claude-mem/claude-mem.db "SELECT id, title FROM observations WHERE project='DevSkyy' AND type='decision' ORDER BY id ASC"

# All bugfixes involving a specific file
sqlite3 ~/.claude-mem/claude-mem.db "SELECT id, title FROM observations WHERE project='DevSkyy' AND type='bugfix' AND title LIKE '%enqueue%'"
```

---

## Observation Type Distribution (DevSkyy, as of 2026-05-03)

| Type | Approx count | Notes |
|------|--------------|-------|
| discovery | ~750 | Architectural facts, file inventories, API surfaces |
| bugfix | ~180 | Root causes + fixes — highest ROI for debugging |
| change | ~130 | Commits, deploys, file modifications |
| decision | ~120 | Architecture decisions — highest ROI for planning |
| refactor | ~60 | Code simplification, adapter patterns |
| feature | ~60 | New features shipped |

> **Tip:** When debugging, search `type='bugfix'` + keyword. When planning, search `type='decision'` + keyword. These two filters dramatically narrow the 1,300 observations to the load-bearing subset.
