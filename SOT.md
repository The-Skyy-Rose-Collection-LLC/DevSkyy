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
| `typography.json` | `wordpress-theme/skyyrose-flagship/data/brand/typography.json` | **THE brand typography SOT** — universal font roles (display **Archivo**, body **Hanken Grotesk**, ui **Anton**, mono, caps **Cinzel**, system **Inter**) + the 4 per-collection name-scripts (Black Rose Script / Pinyon Script / Grand Hotel / Love Hurts Graffiti). Per-collection palette + script/caps live in `data/collections/<slug>/identity.json`. | **GENERATES** the `--skyyrose-font-*` `:root` + `[data-collection]` tokens in `assets/css/design-tokens.css` via `data/gen-design-tokens.py` (writes ONLY between `GENERATED:*` markers; a verifier asserts the live CSS matches a fresh generation). Retired fonts (Playfair Display / Cormorant Garamond / Bebas Neue / Yellowtail — cut 2026-07-10) must never reappear. Rebuild `.min` after regen (theme serves `.min`). |
| _no symlink (×4 per-collection)_ → `data/collections/<slug>/identity.json` | `wordpress-theme/skyyrose-flagship/data/collections/{black-rose,love-hurts,signature,kids-capsule}/identity.json` | **THE per-collection identity SOT** — palette, name-script/caps fonts, story seed, lockup ref, hero imagery (`status:"verified"`). | SOURCE. Schema `identity.schema.json`; drift-gated by `data/verify-collection-sot.py` + CI (`catalog-validate`, `catalog-drift-guard`, `freshness-guard`). Feeds `sot.json` (row below) and the `[data-collection]` tokens via `gen-design-tokens.py`. Collection metadata resolves here — not `brand.yaml`/`config/collections.py` (downstream mirrors). |
| _no symlink (×4, GENERATED)_ → `data/collections/<slug>/sot.json` | `wordpress-theme/skyyrose-flagship/data/collections/{…}/sot.json` | Assembled per-collection view the WP theme reads (identity + catalog + imagery + logos, resolved). | **GENERATED — DO NOT EDIT.** `data/build-collection-sot.py` (canon = identity.json); verified by `data/verify-collection-sot.py`; read via `inc/collection-sot-reader.php`; feeds `sot-images.json`. |

## Brand canon

- `knowledge-base/seed/from-interview.md` — founder-authored brand canon (visual references, anti-references, Oakland canon, engineering rules). When a derived doc conflicts with the interview file, **the interview file wins.**
- `assets/brand/brand.yaml` — structured brand identity: tagline (active + retired history), legal_name / founder / origin / mission, semantic + neutral colors, social handles, prod/dashboard URLs. Generates `inc/brand.generated.php` via `scripts/sync_brand_to_php.py`. **Fonts are NOT owned here** — typography resolves via `typography.json` (its in-file `typography:` block is stale/dead and slated for removal). Collection metadata → `identity.json`, not here.

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
| **MCP / agents** | `.mcp.json`, `fastmcp.config.json`, `requirements-mcp.txt`, `skills-lock.json`, **`llm/model_ids.py`** (canonical LLM model-ID strings — the ONLY source), **`knowledge-base/prompts/INDEX.yaml`** (prompt registry — locations/models/versions, never duplicates prompt text) | `devskyy_mcp.py`, `mcp_service.py`, `agents/base_super_agent/agent.py` | `docker compose up -d` (API) |
| **Infra / deploy** | `Dockerfile`(+`.mcp`), `docker-compose.yml`(+`.staging`), `fly.toml`, `nginx*.conf`, `init.sql`, `prometheus.yml`, `.env.docker` | `scripts/deploy-theme.sh`, `scripts/deploy_hf_spaces.sh` | see `CLAUDE.md` → Deploy table |
| **Data / one-off tooling** | `data/redirects.csv`, `data/skyyrose_clothing_barcodes.txt`, `config/autotrain_config.yaml` | consumers: `scripts/structural_audit.py`, `scripts/generate_clothing_barcodes.py`, `scripts/training/finetune_pipeline.py` | generated reports land in `.reports/` |
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
