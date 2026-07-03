# Source of Truth (SOT) Registry

> The canonical authorities for DevSkyy. **Read these; never cache, never fork, never introduce a second.**
> Memory rots — these don't. The root-level symlinks below surface each from its real location
> (same inode, zero drift). Editing a symlink edits the canonical file.
>
> **Freshness, not just location.** A registry entry only tells you *where* the truth lives.
> `make sot-status` tells you whether it's *actually current* against production — every domain
> below, checked or explicitly marked UNCHECKED, never silently skipped. See "Freshness status"
> at the bottom of this file.

## Data SOT

| Root symlink | Canonical path | Owns | Rules |
|---|---|---|---|
| `skyyrose-catalog.csv` | `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` | Every live SKU (33), 24 columns — name, price, collection, sizes, badge, published/is_preorder, the image columns, and the 8 `render_*` pipeline columns. | **THE product SOT.** Every product-touching path resolves through it. Edit via `/admin/catalog` or the file directly; push downstream with `scripts/sync_catalog_downstream.py`; consistency gated by `scripts/validate_catalog_consistency.py`. Never introduce a second catalog. |
| `hub-manifest.json` | `assets/hub/manifest.json` | The **VERIFIED imagery authority** — founder verdicts per `<sku>-<face>` (+ scenes/lockups/logos). Only `verdict:"verified"` serves. | **Verified upstream of the SOT — not a second copy.** `build-collection-sot.py` overrides each verified, theme-servable front/back into `sot.json` (→ PHP theme **and** `sot-images.json`), so the hub *feeds* the existing chain rather than forking it. Resolve via `skyyrose.core.asset_hub` (`served_theme_path`); promote founder verdicts via `assets/hub/ingest_verdicts.py`; stage off-theme renders (→ webp/avif) via `scripts/sync_hub_to_theme.py`. Manifest is git-tracked (blobs ignored). |
| `sot-images.json` | `data/sot-images.json` | Per-SKU front-first product imagery contract (`front` / `back` / `packshot`). | **GENERATED — DO NOT EDIT.** Regenerate: `make sot-manifest` (→ `wordpress-theme/skyyrose-flagship/data/build-collection-sot.py`). The display layer resolves product images here, not from the CSV image columns. Carries the hub overrides (row above), applied upstream in `build-collection-sot.py`. |
| `visual-manifest.json` | `wordpress-theme/skyyrose-flagship/data/visual-manifest.json` | ALL non-product imagery ownership. Filenames are NOT identity — the manifest is. | New imagery enters the manifest in the same commit. Verify pixels if in doubt. |
| `logo-registry.json` | `wordpress-theme/skyyrose-flagship/data/logo-registry.json` | Logo identities, `sku_logos`, `sku_folders` (jersey-series roster), `brand_primary` (v4+). | Canonical alongside the catalog; cross-consistency enforced by `scripts/validate_catalog_consistency.py`. |
| `dossiers` | `wordpress-theme/skyyrose-flagship/data/dossiers/` | Per-product design dossiers (one `.md` per SKU) — the rich spec the render pipeline reads. | **Corey-authored from the product, never ML-drafted.** CI-gated by `.github/workflows/dossier-check.yml`. |

## Brand canon

- `from-interview.md` → `knowledge-base/seed/from-interview.md` — founder-authored brand canon (visual references, anti-references, Oakland canon, engineering rules). When a derived doc conflicts with the interview file, **the interview file wins.**

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

## Freshness status — `make sot-status`

Every domain above (and every domain that has no root artifact at all) is registered here so
staleness is never silent. Run `make sot-status` for the live table; `make sot-status LIVE=1`
adds the read-only WooCommerce reconcile. `scripts/sot_status.py` **aggregates existing
validators — it does not reimplement any of them.** The one new check it introduces is the WC
reconcile (`scripts/wc_reconcile.py`); everything else shells out to or imports a validator that
already existed before this registry.

| Domain | Artifact | Update command | Freshness check + trigger | Notes |
|---|---|---|---|---|
| Catalog | `skyyrose-catalog.csv` + `logo-registry.json` | Edit CSV / `/admin/catalog`; `make sync-catalog` | `scripts/validate_catalog_consistency.py` — CI on every PR touching catalog data (`.github/workflows/catalog-validate.yml`); local pre-commit via `.husky/pre-commit` when staged files match catalog patterns | 16 checks as of this writing (jersey roster, logo cross-refs, similarities, preorder invariant, v7-cards, etc.) |
| Dossiers | `dossiers/` (33 `.md` files) | Author manually per product | `scripts/check_dossier_coverage.py` + `scripts/validate_dossier.py` + catalog validator's `dossier_slugs` check — CI on every PR (`.github/workflows/dossier-check.yml`) | Corey-authored; no ML-drafted fallback |
| Product imagery | `sot-images.json` | `make sot-manifest` | Catalog validator's `sot_images_current` check — same CI job as Catalog | Generated file; never hand-edit |
| Non-product imagery | `visual-manifest.json` | Hand-edit in the same commit as new imagery | **UNCHECKED** — no standalone consistency validator exists yet comparing the manifest against the actual non-product image files on disk | Verified manually today per `CLAUDE.md`'s imagery-ownership rule |
| Collection content (sot.json ×4) | `wordpress-theme/skyyrose-flagship/data/collections/{black-rose,love-hurts,signature,kids-capsule}/sot.json` | `bash scripts/freshness-guard.sh --fix` | `data/verify-collection-sot.py` (also run as freshness-guard CHECK 1) — local pre-commit via `.husky/pre-commit`; **now also in `catalog-validate.yml` CI** (was local-only before this registry) | |
| Brand canon | `from-interview.md` | Founder edits directly | **UNCHECKED** — founder-authored source text; no generated downstream artifact exists to diff against for drift | |
| Theme version triple | `style.css` / `functions.php` / `readme.txt` | Bump all three together | freshness-guard CHECK 3 — local pre-commit; **now also in CI** | |
| Hub pixels | `hub-manifest.json` (`assets/hub/manifest.json`) | `assets/hub/ingest_verdicts.py`; `scripts/sync_hub_to_theme.py` | **Presence-gated** `skyyrose.core.asset_hub.verify_integrity()` — wired into `sot-status` only (not yet its own CI gate) | **Tree is real, wiring landed on main** (`a11ca3208`, "tie verified asset-hub to the SOT chain") — this SOT.md previously (pre-registry) described the hub as tracked-but-unwired; that was already stale by the time this registry was written. Every verified manifest entry's pixels live under `assets/hub/collections/**`, which is **gitignored** (`.gitignore:217`); the manifest itself is tracked and always present. `sot_status.py` checks for that directory before calling `verify_integrity()` — absent (any fresh clone or CI runner) → `UNCHECKED`, same treatment as 3D/GLB and scene backdrops below; present → runs the real validator and reports OK/DRIFT on its actual findings. |
| 3D / GLB | `renders/3d/` (GLBs + `qc/*.json`) | Render pipeline output | **Presence probe only** inside `sot_status.py` (directory exists + non-empty) — not a content-consistency validator | Gitignored disk-only assets (`.gitignore:404`); absent in any fresh checkout by design |
| Scene backdrops | `wordpress-theme/skyyrose-flagship/assets/scenes/` | Render pipeline output | **Presence probe only**, same mechanism as 3D/GLB | Gitignored (`.gitignore:256`) |
| Fonts | `wordpress-theme/skyyrose-flagship/theme.json` (Font Library) | Hand-edit + `docs/google-fonts-selfhost.md` process | **UNCHECKED** — no automated check found; self-hosted `@font-face` declarations are hand-maintained | |
| WC store | `https://skyyrose.co` (WooCommerce REST) | N/A — live production data | **NEW:** `scripts/wc_reconcile.py` — read-only `GET /wp-json/wc/v3/products`, BasicAuth from `.env.wordpress`; compares SKU set (both directions), price, name, `published`, `is_preorder` against the CSV | Never writes. Run via `make sot-status LIVE=1` or standalone; `LIVE-SKIPPED` (not a failure) when credentials are absent |
| WP menus | live-only (WordPress nav menus) | Edit in WP admin | **UNCHECKED** — live-only surface, not backed by a repo artifact; no probe implemented yet | A `wc_reconcile`-style live probe is a plausible future addition |
| Legal pages | live-only (WP.com published pages) | Publish via WP.com MCP | **UNCHECKED** — live-only surface; no probe implemented yet | Pages themselves are already live per project memory |

**Status vocabulary:** `OK` (validator passed) · `DRIFT` (validator found inconsistency) ·
`BROKEN` (validator itself failed to run) · `UNCHECKED` (no validator wired — reason given) ·
`LIVE-SKIPPED` (a live check was requested but credentials/network were unavailable). Exit code
is non-zero only on `DRIFT`/`BROKEN` — `UNCHECKED` and `LIVE-SKIPPED` are informational and never
fail CI.

**Known dead hook:** `.git/hooks/pre-commit` still contains an orphaned catalog-validation gate
from before Husky adoption (`core.hooksPath=.husky/_` means Git never invokes it). Its
file-pattern-triggered logic was ported into `.husky/pre-commit` rather than deleted outright —
left in place as a record, not a live gate.

---
*Root SOT registry. Symlinks point at each canonical location — there is exactly one copy of each truth.*
