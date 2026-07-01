# Source of Truth (SOT) Registry

> The canonical authorities for DevSkyy. **Read these; never cache, never fork, never introduce a second.**
> Memory rots — these don't. The root-level symlinks below surface each from its real location
> (same inode, zero drift). Editing a symlink edits the canonical file.

## Data SOT

| Root symlink | Canonical path | Owns | Rules |
|---|---|---|---|
| `skyyrose-catalog.csv` | `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` | Every live SKU (33), 24 columns — name, price, collection, sizes, badge, published/is_preorder, the image columns, and the 8 `render_*` pipeline columns. | **THE product SOT.** Every product-touching path resolves through it. Edit via `/admin/catalog` or the file directly; push downstream with `scripts/sync_catalog_downstream.py`; consistency gated by `scripts/validate_catalog_consistency.py`. Never introduce a second catalog. |
| `hub-manifest.json` | `assets/hub/manifest.json` | The **VERIFIED imagery authority** — founder verdicts per `<sku>-<face>` (+ scenes/lockups/logos). Only `verdict:"verified"` serves. | **Verified upstream of the SOT — not a second copy.** `build-collection-sot.py` overrides each verified, theme-servable front/back into `sot.json` (→ PHP theme **and** `sot-images.json`), so the hub *feeds* the existing chain rather than forking it. Resolve via `skyyrose.core.asset_hub` (`served_theme_path`); promote founder verdicts via `assets/hub/ingest_verdicts.py`; stage off-theme renders (→ webp/avif) via `scripts/sync_hub_to_theme.py`. Manifest is git-tracked (blobs ignored). |
| `sot-images.json` | `data/sot-images.json` | Per-SKU front-first product imagery contract (`front` / `back` / `packshot`). | **GENERATED — DO NOT EDIT.** Regenerate: `make sot-manifest` (→ `wordpress-theme/skyyrose-flagship/data/build-collection-sot.py`). The display layer resolves product images here, not from the CSV image columns. Carries the hub overrides (row above), applied upstream in `build-collection-sot.py`. |
| `visual-manifest.json` | `wordpress-theme/skyyrose-flagship/data/visual-manifest.json` | ALL non-product imagery ownership. Filenames are NOT identity — the manifest is. | New imagery enters the manifest in the same commit. Verify pixels if in doubt. |
| `logo-registry.json` | `wordpress-theme/skyyrose-flagship/data/logo-registry.json` | Logo identities, `sku_logos`, `sku_folders` (jersey-series roster), `brand_primary` (v4+). | Canonical alongside the catalog; cross-consistency enforced by `scripts/validate_catalog_consistency.py`. |

## Brand canon

- `knowledge-base/seed/from-interview.md` — founder-authored brand canon (visual references, anti-references, Oakland canon, engineering rules). When a derived doc conflicts with the interview file, **the interview file wins.**

## OpenWolf memory (cross-session)

| Root symlink | Canonical path | Owns |
|---|---|---|
| `cerebrum.md` | `.wolf/cerebrum.md` | Learnings, User Preferences, Do-Not-Repeat, Decision Log, Project Conventions. Read before generating code. |
| `anatomy.md` | `.wolf/anatomy.md` | Per-file 2–3 line descriptions + token estimates. Read before reading files. |
| `buglog.json` | `.wolf/buglog.json` | Known bugs + fixes. Read before fixing; append after fixing. |
| — (gitignored, not symlinked) | `.wolf/memory.md` | Per-action session log. |

## Picking the right verification

The check must match the *kind* of claim (full matrix in `CLAUDE.md` → "Verification Protocol"):

- Product facts (SKU, price, name, collection) → the catalog CSV + per-SKU dossier.
- Product imagery → `sot-images.json` (front-first); non-product imagery → `visual-manifest.json`.
- Logo / roster facts → `logo-registry.json`.
- Codebase facts → Read/Grep the source; check `anatomy.md` first.
- Prior work ("did we solve this?") → `mem-search` / claude-mem observations.

---
*Root SOT registry. Symlinks point at each canonical location — there is exactly one copy of each truth.*
