# Source of Truth (SOT) Registry

> The canonical authorities for DevSkyy. **Read these; never cache, never fork, never introduce a second.**
> Memory rots — these don't. The root-level symlinks below surface each from its real location
> (same inode, zero drift). Editing a symlink edits the canonical file.

## Data SOT

| Root symlink | Canonical path | Owns | Rules |
|---|---|---|---|
| `skyyrose-catalog.csv` | `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` | Every live SKU (33), 24 columns — name, price, collection, sizes, badge, published/is_preorder, the image columns, and the 8 `render_*` pipeline columns. | **THE product SOT.** Every product-touching path resolves through it. Edit via `/admin/catalog` or the file directly; push downstream with `scripts/sync_catalog_downstream.py`; consistency gated by `scripts/validate_catalog_consistency.py`. Never introduce a second catalog. |
| `dossiers/<name>.md` | `wordpress-theme/skyyrose-flagship/data/dossiers/` | Per-product founder-authored canon — garment truth, branding spec, negative clauses (may be per-variant, so > catalog SKU count). Reference by **name, not SKU**. `_template.md` seeds new ones. | The product **narrative** SOT — the CSV holds structured fields, the dossier holds the garment. Corey-authored from the real product, never ML-drafted; wrong dossier text overrides the reference image in renders (sg-006/sg-014 precedent). |
| `hub-manifest.json` | `assets/hub/manifest.json` | The **VERIFIED imagery authority** — founder verdicts per `<sku>-<face>` (+ scenes/lockups/logos). Only `verdict:"verified"` serves. | **Verified upstream of the SOT — not a second copy.** `build-collection-sot.py` overrides each verified, theme-servable front/back into `sot.json` (→ PHP theme **and** `sot-images.json`), so the hub *feeds* the existing chain rather than forking it. Resolve via `skyyrose.core.asset_hub` (`served_theme_path`); promote founder verdicts via `assets/hub/ingest_verdicts.py`; stage off-theme renders (→ webp/avif) via `scripts/sync_hub_to_theme.py`. Manifest is git-tracked (blobs ignored). |
| `sot-images.json` | `data/sot-images.json` | Per-SKU front-first product imagery contract (`front` / `back` / `packshot`). | **GENERATED — DO NOT EDIT.** Regenerate: `make sot-manifest` (→ `wordpress-theme/skyyrose-flagship/data/build-collection-sot.py`). The display layer resolves product images here, not from the CSV image columns. Carries the hub overrides (row above), applied upstream in `build-collection-sot.py`. |
| `visual-manifest.json` | `wordpress-theme/skyyrose-flagship/data/visual-manifest.json` | ALL non-product imagery ownership. Filenames are NOT identity — the manifest is. | New imagery enters the manifest in the same commit. Verify pixels if in doubt. |
| `logo-registry.json` | `wordpress-theme/skyyrose-flagship/data/logo-registry.json` | Logo identities, `sku_logos`, `sku_folders` (jersey-series roster), `brand_primary` (v4+). | Canonical alongside the catalog; cross-consistency enforced by `scripts/validate_catalog_consistency.py`. |
| `collections/<slug>/sot.json` | `wordpress-theme/skyyrose-flagship/data/collections/{black-rose,love-hurts,signature,kids-capsule}/sot.json` | GENERATED per-collection view — products, imagery, lockup, palette, fonts. | **GENERATED — DO NOT EDIT.** Regenerate: `build-collection-sot.py`; byte-compare drift-guarded by `scripts/validate_catalog_consistency.py` (`collection_sot_current`). Carries the hub overrides + `sot-images.json`. A test/pipeline that regenerates it in-tree must not commit the rewrite. |
| `render-keepers.json` | `wordpress-theme/skyyrose-flagship/data/render-keepers.json` | Founder keep / re-render decisions per render (source: `tasks/mockup-render-inventory.md`). | Which renders survive a re-render pass. A keeper is honored only if its asset exists on disk — else it re-renders. |

## Brand canon

- `knowledge-base/seed/from-interview.md` — founder-authored brand canon (visual references, anti-references, Oakland canon, engineering rules). When a derived doc conflicts with the interview file, **the interview file wins.**
- `wordpress-theme/skyyrose-flagship/data/brand/typography.json` (+ `typography.schema.json`) — the **typography SOT**: the `--skyyrose-font-*` role assignments (Archivo / Hanken Grotesk / Anton / Cinzel + per-collection scripts). `data/gen-design-tokens.py` regenerates the `GENERATED:global-fonts` region of `assets/css/design-tokens.css` from it — **edit the JSON, never the generated CSS**, then rebuild `.min`. Fonts self-hosted woff2 in `assets/fonts/`, zero CDN.
- Color / collection accent tokens live in `CLAUDE.md` → Brand table and `theme.json` (Font Library). Tagline: **"Luxury Grows from Concrete."**

## OpenWolf memory (cross-session)

| Root symlink | Canonical path | Owns |
|---|---|---|
| `cerebrum.md` | `.wolf/cerebrum.md` | Learnings, User Preferences, Do-Not-Repeat, Decision Log, Project Conventions. Read before generating code. |
| `anatomy.md` | `.wolf/anatomy.md` | Per-file 2–3 line descriptions + token estimates. Read before reading files. |
| `buglog.json` | `.wolf/buglog.json` | Known bugs + fixes. Read before fixing; append after fixing. |
| — (gitignored, not symlinked) | `.wolf/memory.md` | Per-action session log. |

## Domain configuration map (current-state, token-cheap)

> **Rule: config questions resolve HERE, not in old docs.** For any domain below, read only the files in its row.
> `docs/archive/`, `tasks/`, and root-level handoff docs are **historical** — never source configuration,
> paths, or commands from them. (Root was reorganized 2026-07-07; pre-that paths in archived docs are stale.)

| Domain | Canonical config | Entry points | Commands |
|---|---|---|---|
| **Python API** | `pyproject.toml`, `requirements.txt` (+`-dev`,`-full`), `mypy.ini`, `pyrightconfig.json`, `conftest.py`, `alembic.ini`, `.env` / `.env.example` | `main_enterprise.py` | `make install` · `make test` · `make format` · `make lint` |
| **Frontend dashboard** | `frontend/package.json`, root `vercel.json`, `eslint.config.mjs`, `.nvmrc` | `frontend/` (Next.js 16 / React 19) | `cd frontend && npm run dev` · `npm run build` |
| **WordPress theme** | `wordpress-theme/skyyrose-flagship/style.css` (version), `.phpcs.xml`, `theme.json`, `.env.wordpress` | `wordpress-theme/skyyrose-flagship/` | `cd wordpress-theme && npm run deploy` · `npm run lint:php` — serve `.min`: rebuild after CSS/JS edits |
| **Imagery (OAI gpt-image-2)** | `requirements-imagery.txt`, `.env.hf`, judge envs `.env.judge-{gemini-vision,gpt-vision,opus-thinking}` | `scripts/oai-render-run.py`, engine `scripts/oai_render/` | `dry-run --sku <sku>`; paid `generate` needs `--yes` (STOP-AND-SHOW) |
| **MCP / agents** | `.mcp.json`, `fastmcp.config.json`, `requirements-mcp.txt`, `skills-lock.json` | `devskyy_mcp.py`, `mcp_service.py`, `agents/base_super_agent/agent.py` | `docker compose up -d` (API) |
| **Infra / deploy** | `Dockerfile`(+`.mcp`), `docker-compose.yml`(+`.staging`), `fly.toml`, `nginx*.conf`, `init.sql`, `prometheus.yml`, `.env.docker` | `scripts/deploy-theme.sh`, `scripts/deploy_hf_spaces.sh` | see `CLAUDE.md` → Deploy table |
| **Data / one-off tooling** | `data/redirects.csv`, `data/skyyrose_clothing_barcodes.txt`, `config/autotrain_config.yaml` | consumers: `scripts/structural_audit.py`, `scripts/generate_clothing_barcodes.py`, `scripts/training/finetune_pipeline.py` | generated reports land in `.reports/` |
| **Agent suite** | `skyyrose-suite/.claude-plugin/marketplace.json` | 5 plugins — `skyyrose` (orchestrator) + `-core` / `-design` / `-market` / `-qa`; skills auto-discover from each plugin's `skills/` dir | `claude plugin marketplace add ./skyyrose-suite` · hardening set documented in `skyyrose-suite/HARDENING.md` |
| **Docs** | current: `README.md`, `CLAUDE.md`, `SOT.md`, `CHANGELOG.md`, `docs/` | — | historical: `docs/archive/`, `tasks/` (read-only context, never config) |

## Picking the right verification

The check must match the *kind* of claim (full matrix in `CLAUDE.md` → "Verification Protocol"):

- Product facts (SKU, price, name, collection) → the catalog CSV + per-SKU dossier.
- Product imagery → `sot-images.json` (front-first); non-product imagery → `visual-manifest.json`.
- Logo / roster facts → `logo-registry.json`.
- Codebase facts → Read/Grep the source; check `anatomy.md` first.
- Prior work ("did we solve this?") → `mem-search` / claude-mem observations.

---
*Root SOT registry. Symlinks point at each canonical location — there is exactly one copy of each truth.*
