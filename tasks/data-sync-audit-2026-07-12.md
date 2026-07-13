# SkyyRose Data-Sync Audit — Consolidated Report
**Date:** 2026-07-12 · **Scope:** Canonical chain per `SOT.md` — catalog CSV, `sot-images.json`, `visual-manifest.json`, `logo-registry.json`, embeddings, hub manifest. **Method:** read-only, 5 parallel domain audits (repoint safety, image truth map, embeddings/ML, product-fact conflicts, repo hygiene/guards), synthesized here. No files were edited in any domain pass or in producing this report.

---

## 1. EXECUTIVE SUMMARY

The canonical chain is **structurally sound and actually in sync** — the headline "116 dead CSV image paths" finding that triggered this audit was a measurement artifact (naive repo-root resolution vs. the real theme-relative resolution both production consumers use); all 116 values resolve to real, git-tracked files, and `sot-images.json`/`sot.json` are byte-fresh per the 23/23-green gate. The **real, live drift** is elsewhere and smaller in surface: `visual-manifest.json`'s own verifier is orphaned from CI and fails today (1 genuine missing file + 6 manifest-authoring typos), the embeddings file `catalog_ml_audit.py` expects has zero git history (never generated, not lost), and CI has **no guard at all** on the CSV's four image columns — currently harmless, but a silent-failure trap for the next bulk edit. Separately, **13 product-fact conflicts** surfaced between the CSV `color`/`description` fields and founder-authored dossiers/verified renders — these are founder calls, not auto-resolvable. Nothing here blocks shipping; nothing here is urgent-fire, but three mechanical fixes and one new guard close the gaps for $0.

---

## 2. MECHANICAL FIXES READY (autonomous, $0, verifiable)

### 2.1 — CSV image-column strategy: **no CSV edit, add a guard instead**
**Verdict (Domain A):** Leave `skyyrose-catalog.csv`'s `image`/`front_model_image`/`back_image`/`back_model_image` columns untouched. All 116 non-empty values already resolve correctly via the real consumer path (`sot_common.resolve_asset()` → `WP_ASSETS_DIR` = `wordpress-theme/skyyrose-flagship/assets/`); repointing them would be pure churn with real risk (`front_model_image`/`back_model_image` flow byte-for-byte into `sot-images.json` for 2/33 and 3/33 SKUs respectively where no hub override fires — an edit there changes served output, not just provenance). **Action: none on the CSV.** The fix is the new validator in §2.3, which encodes the correct resolution semantics so future drift is caught instead of silently passing.
- **Target files:** none (no-op by design)
- **Verified by:** `scripts/validate_catalog_consistency.py` stays 23/23 green (unchanged, since nothing changes)

### 2.2 — Reconcile `visual-manifest.json` (fixes the one live, reproducible failure found this pass)
**Target file:** `wordpress-theme/skyyrose-flagship/data/visual-manifest.json`
**Fix:**
- (a) **6 false-positive entries** — normalize double-extension paths to the manifest's own documented convention (extension-less `path` + bare-extension `formats`, not `path` already carrying the extension): `black_rose.lockup_display` (`images/lockups/black-rose-lockup.webp` → strip `.webp` from `path`), and the equivalent for `love-hurts-lockup.webp`, `signature-lockup.webp`, `black-rose-script.svg`, `love-hurts-full-lettering.svg`, `signature-script.svg`.
- (b) **1 genuine miss** — `brand_global.lockups[7]` (`kids-capsule`, `formats: ["avif","webp"]`, `status: "verified"`) claims an `.avif` that doesn't exist; only `.webp` is on disk. Either regenerate the AVIF or correct `formats` to `["webp"]` and drop the false `"verified"` claim on a format that isn't there.
- (c) Wire `wordpress-theme/skyyrose-flagship/data/verify-visual-manifest.py` into `.github/workflows/catalog-validate.yml` (already watches `wordpress-theme/skyyrose-flagship/data/**`) — currently the script exists, works, and is referenced nowhere.
- **Verified by:** `python3 wordpress-theme/skyyrose-flagship/data/verify-visual-manifest.py` → exit 0, "checked N files, MISSING (0)" (currently: exit 1, 7 missing). Re-run after each sub-fix.

### 2.3 — New validator: `csv_image_columns_resolve`
**Target file:** `scripts/validate_catalog_consistency.py`
**Fix:** add a check (pattern-matched to existing `check_dossier_slugs`, line 611) that asserts every non-empty value in the four CSV image columns resolves via `sot_common.resolve_asset()` rooted at `WP_ASSETS_DIR` — the exact function/root `build-collection-sot.py:64,73` uses in production. Register in `ALL_CHECKS` (line 982) as `"csv_image_columns_resolve"` and add a line to the module docstring's check list (lines 20-38). Full function body specified in Domain A/E findings (ready to paste in).
- **Verified by:** running the full `validate_catalog_consistency.py` suite → passes today with **0 failures** (nothing to catch currently — this institutionalizes correct semantics for the *next* break, e.g. a bad `/admin/catalog` bulk-edit or asset-tree reorg, so it fails CI loud instead of silently).

### 2.4 — Embeddings path: build the missing generator (not a repoint — repoint provably breaks)
**Target file (new):** a ~50-80 line script (e.g. `scripts/generate_product_embeddings.py`) that loops the 33 catalog SKUs, resolves each front-model image via `data/sot-images.json` (the canonical served-image resolver — never the raw CSV columns), calls `skyyrose.core.clip_embedder.embed_image()`, and writes CLIP-format output (`{"model": ..., "dim": 512, "products": {sku: {...}}}`) to `wordpress-theme/skyyrose-flagship/data/product-embeddings.json`.
**Why not repoint:** `catalog_ml_audit.py:54` hardcodes that missing path expecting a `{sku: {...}}` **dict** of **512-d CLIP** vectors. The only existing file (`skyyrose/assets/data/product-embeddings.json`) is a **list**-shaped, **3072-d Gemini text-embedding** dump, stale (Feb 2026), covering 19/33 SKUs plus one phantom SKU (`sg-010`, not in the current catalog). Repointing to it crashes immediately (`AttributeError` on `.keys()` on a list) and, even patched, produces a `ValueError` on shape mismatch in the CLIP-alignment analysis — a category error (text-semantic space vs. CLIP joint space), not a formatting bug.
**Cost:** $0 — local HF model (`openai/clip-vit-base-patch32`, already wired via `skyyrose.core.embeddings.clip.ClipEncoder`, `transformers` installed), one-time ~600MB download, CPU/GPU local compute, no per-call API. Not STOP-AND-SHOW gated.
- **Verified by:** `python scripts/catalog_ml_audit.py` runs clean (currently FATAL on missing file) with output matching its own docstring (33 SKUs × 512-d CLIP). Also unblocks `scripts/build_product_similarities.py` and `scripts/check_catalog_duplicates.py`, which hardcode the same path.
- **Note:** this is new code, not "done" in this read-only pass — flagged as ready build work, not yet written.

### 2.5 — Local semantic index (separate from 2.4, also $0)
**Action:** `python scripts/index_skyyrose_catalog.py --commit` — confirmed to route through `CatalogRetriever.initialize()`'s **local** defaults (`sentence-transformers` + `chromadb`, both already installed), never `for_production()` (Voyage+Pinecone). No API key touched, no production index written.
- **Verified by:** local Chroma collection populated; `CatalogRetriever.retrieve()` / `find_similar_by_sku()` return results against it.

---

## 3. FOUNDER DECISIONS (product-fact conflicts)

CSV `color` field inconsistently mixes **garment body color** with **print/graphic/theme color**. A single policy call (body-color-only vs. theme-color-allowed) would resolve items 1–7 in one pass. Full evidence trail (dossier quotes, hub image paths) is in the Domain D audit; numbered for reference:

**Tier A — confirmed, dossier + image agree, CSV is wrong:**
1. **sg-015** — CSV `color=Black`; dossier explicitly overrides ("NOT solid black... WHITE body + PINK hood + rainbow chevron").
2. **sg-005** — CSV `color=Navy`; garment is solid white with blue/dark rose-bridge graphic (CSV's own `description` already agrees with dossier, not with `color`).
3. **sg-002** — CSV `color=Gold`; garment is solid white with purple/violet graphic, no gold on it.
4. **sg-003** — CSV `color=Gold`; white-mesh shorts, purple-violet/navy print — "Stay Golden" is the theme name, not the garment color.
5. **lh-003** — CSV `color=Black`; white-mesh shorts with all-over red-rose print, black only as trim.
6. **lh-004** — CSV `color=Black`; two-tone bomber, white body dominant + black raglan sleeves/hood.
7. **sg-009** — CSV `color=Cream`; solid black shell, cream/white only as interior sherpa lining.

**Tier B — likely, lower confidence (multi-tone, a color omitted/overstated):**
8. **kids-002** — CSV `color=Purple/Black`; render+dossier show lavender/pink + purple, no true black.
9. **kids-001** — CSV `color=Red/Black`; render shows a prominent white diagonal panel unlisted in the field.

**Render-fidelity vs. dossier (questions the hub "verified" verdict, not just the CSV):**
10. **br-010** — verified render's "THE BAY" wordmark is white/grey; dossier specifies gold/yellow. CSV `color=White/Gold` is actually correct — the render is the mismatch.
11. **kids-002** — verified render's arm-patch graphic doesn't match either SKU's `branding_spec` (wrong patch text/design).

**Name/description drift:**
12. **sg-001** — `description` calls it an "exclusive ensemble"; dossier confirms single-piece (shorts only, no top).

**Price anomaly:**
13. **sg-001** ($195) vs **sg-003** ($65) — same series/construction, no material difference visible in either dossier; 3x gap worth a look.

**Confirmed clean, no action needed:** br-001–007, br-009, br-011, br-012, br-014, br-015, lh-002, lh-005, lh-006, sg-006, sg-007, sg-011, sg-012, sg-013, sg-014.

---

## 4. GATED ACTIONS (paid/production — do NOT run without explicit STOP-AND-SHOW confirmation)

1. **Paid embeddings regen at production grade** — switching §2.4/§2.5 from local (free) to `CatalogRetriever.for_production()` (Voyage embeddings + the provisioned Pinecone `skyyrose-catalog` index, us-west-2, dim=1024, cosine). Cost: Voyage per-token embedding charge for 33 SKUs' text (one-time, small, but real money) plus ongoing Pinecone usage.
2. **`answer_question()` live serving** — ~$0.0001 Voyage + ~$0.001–0.002 Claude Haiku **per question** if RAG Q&A is exposed live — a recurring serving cost, not a one-time regen; scale with traffic before enabling.
3. **WooCommerce conform writes** — once the founder rules on §3's 13 color-field decisions, pushing the corrected `color` values (and any `description`/price changes) to live WooCommerce products via REST is a production write — needs manifest + cost-free-but-irreversible confirmation per the STOP-AND-SHOW protocol (WC writes are always gated regardless of dollar cost).
4. **Theme deploy to skyyrose.co** — any of the mechanical fixes above that touch files under `wordpress-theme/skyyrose-flagship/` (visual-manifest reconciliation, new validator) still need `bash scripts/deploy-theme.sh` / `npm run deploy` to reach production — SFTP push, gated.
5. **Queued gpt-image-2 renders for "pending" hub items** — 13 back-face + 2 front-face (`br-009`, `br-012`) hub entries are `verdict:"pending"` (not founder-verified); promoting/replacing them means a paid `oai-render-run.py generate` dispatch — cost + manifest must be shown before running.

---

## 5. RECOMMENDED GUARDS (so it stays in sync)

1. **`csv_image_columns_resolve`** (§2.3) — closes the only structural gap found: zero CI enforcement on the CSV's 4 image columns today.
2. **Wire `verify-visual-manifest.py` into CI** (§2.2c) — a working verifier sitting completely unused; the natural home is `catalog-validate.yml`, which already watches the right path.
3. **Fix the fail-open skip in `tests/test_asset_hub.py`** — currently `pytestmark = pytest.mark.skipif(not hub._MANIFEST_PATH.exists(), ...)` silently skips instead of failing if the hub manifest is ever absent (a bad checkout, path drift). Per house doctrine (bug-230, "gates fail closed"), this should fail loud, not skip quiet.
4. **Wire `scripts/freshness-guard.sh --all` into CI**, not just the local pre-commit hook — its own header comment already (incorrectly) claims CI coverage; make that true. Currently bypassable with `--no-verify` and entirely absent on a bare CI runner.
5. **Re-run `scripts/wolf_recurring_sync.py`-style triage on the 7 other orphaned `validate_*`/`sync_*` scripts** (`validate_3d_assets.py`, `validate_environment.py`, `validate_production.py`, `validate_wordpress_env.py`, `sync_brand_to_php.py`, `sync_hub_to_theme.py`, `sync_vault_products.py`) — decide per-script: wire into CI, wire into Makefile-only (manual/local), or deprecate if genuinely dead. Not urgent; flagged so it doesn't silently rot further.
6. **Once §2.4's embeddings generator exists**, add a freshness check (byte/hash compare against current catalog SKU set) mirroring the `sot_images_current` pattern, so a catalog SKU add/remove doesn't silently leave the embeddings file stale again.

---

*Domain audits: A (repoint safety), B (image truth map, 132-cell table), C (embeddings/ML), D (product-fact conflicts), E (repo hygiene/guard gaps). All read-only against `/Users/theceo/DevSkyy` main checkout. No files edited in any pass.*
