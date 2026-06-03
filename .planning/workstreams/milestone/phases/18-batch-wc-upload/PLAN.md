# Phase 18 — Full Batch + WooCommerce Upload

## Goal
All 28 in-scope garment SKUs have a Phase-17-approved ghost-mannequin front image uploaded to WooCommerce, with an explicit user confirmation gate before any production write.

## Requirements
- **UPLOAD-01** — After 100% approval of all in-scope front ghost-mannequin images, batch upload approved images to WooCommerce Media Library and update each product's image field. Triggered only on explicit user confirmation, never autonomously.

## Depends On
- **Phase 17 (LANDED 2026-05-19, commit caf6b9a51)** — `renders/ghost-mannequin/approved/{sku}-ghost-front.webp` is the gate-locked input contract. Catalog CSV `front_model_image` already updated by `approve()`.
- **wordpress/products.py** (existing 416-line module) — `WooCommerceProducts` async client + `ProductUpdate(images=[...])`. Reused, not rewritten.
- **wordpress/auth_config.py** — `WOOCOMMERCE_KEY`, `WOOCOMMERCE_SECRET`, `WC_API_VERSION=wc/v3` env vars.

## Out of Scope
- Generating images (Phase 15).
- Approving images (Phase 17).
- Per-product image cropping, resizing, or watermarking — upload as-is from `approved/`.
- Updating non-front images (back, gallery, variants). Only `front_model_image` is touched.
- SKU-to-product-ID resolution beyond what's in the CSV. If `wc_product_id` is missing from the row, that SKU is skipped with a clear message.

## Architecture

```
skyyrose/elite_studio/upload.py     ← Pure library
    build_manifest() -> list[UploadEntry]
    upload_batch(manifest, *, dry_run=False) -> list[UploadResult]
    verify_upload(product_id, expected_image_url) -> bool
    StopAndShowError, UploadError exceptions
    UploadEntry, UploadResult, UploadManifest dataclasses
scripts/upload_approved.py          ← CLI (STOP AND SHOW gate lives here)
tests/test_upload.py                ← Integration tests with mocked WC REST
renders/ghost-mannequin/
    approved/                       ← Phase 17 contract: source files
    upload_log.json                 ← Audit log of all upload attempts
```

### Data flow

```
1. CLI: read CSV via skyyrose.core.catalog_loader
2. Library: build manifest by scanning approved/ ∩ catalog rows
3. CLI: print STOP AND SHOW manifest to stderr (table + totals)
4. CLI: prompt for literal "y" via stdin — Ctrl-C / "n" / anything else = abort
5. Library: for each manifest entry:
     a. POST file to /wp/v2/media → get media_id + source_url
     b. PUT product update: images=[{id: media_id, position: 0}]
     c. GET product → verify images[0].src == source_url
     d. Append result to upload_log.json
6. CLI: print summary table; exit 0 iff all succeeded
```

### STOP AND SHOW manifest format

Per CLAUDE.md verbatim:

```
STOP — Confirm before proceeding:

Action  : WooCommerce batch image upload
Target  : https://skyyrose.co (WC REST v3)
Manifest:
  SKU       Product ID    Image                                              Current → New
  br-001    12345         renders/ghost-mannequin/approved/br-001-ghost-...  old.webp → ghost
  br-002    12346         renders/ghost-mannequin/approved/br-002-ghost-...  old.webp → ghost
  ...                                                                        (28 rows)
Total   : 28 SKUs, est. 28 file uploads + 28 product updates + 28 verifications
Cost    : $0.00 (WordPress.com hosted, no per-call API cost) — but live site write
Auth    : WOOCOMMERCE_KEY=ck_*** (last 4: 1234)

Proceed? [y/N]
```

The `y/N` prompt requires literal lowercase `y` (or `yes`). Anything else aborts. Default is N. Bypassable only via `--yes` flag, which still prints the manifest and only suppresses the stdin prompt for non-interactive runs (CI / scripts).

### Manifest exclusion gates

A SKU is **excluded** from the manifest (logged as `SKIPPED`) if any of:
1. `approved/{sku}-ghost-front.webp` does not exist
2. CSV row has no `wc_product_id` (or value is empty/non-numeric)
3. CSV row has `published=0`
4. SKU appears in `renders/ghost-mannequin/SKIPPED.json` from Phase 14 preflight (e.g. sg-007, lh-005)

A SKU is **included** only if all four checks pass. The CLI exits with `error` and code 1 if the manifest is empty.

### Idempotency

If `wc_product_id`'s existing `images[0].src` already matches the would-be-uploaded URL (by basename + WC media GUID), the row is logged as `ALREADY_SYNCED` and no upload runs for it. Allows re-running the CLI safely.

## Plans

### 18-01 — `skyyrose/elite_studio/upload.py` core library

**Surface area**
- `class StopAndShowError(Exception)` — manifest empty or user declined
- `class UploadError(Exception)` — WC REST failure (4xx/5xx, timeout)
- `@dataclass(frozen=True) UploadEntry` — `sku, product_id, source_path, current_image_url`
- `@dataclass(frozen=True) UploadResult` — `sku, product_id, media_id, source_url, status, verified, error`
- `@dataclass(frozen=True) UploadManifest` — `entries, skipped, generated_at`
- `def build_manifest(*, root=None, catalog_rows=None) -> UploadManifest`
- `async def upload_batch(manifest, *, wc_client=None, dry_run=False) -> list[UploadResult]`
- `async def verify_upload(wc_client, product_id, expected_url) -> bool`

**Implementation notes**
- `build_manifest` is pure: takes catalog rows (or reads via `skyyrose.core.catalog_loader.read_catalog_rows()`) + scans `approved/` dir. No network.
- `upload_batch` accepts an optional `wc_client` for test injection. If None, constructs `WooCommerceProducts()` from env.
- `dry_run=True` performs all reads + manifest validation but no POST/PUT calls. Returns synthetic `UploadResult` with `status="DRY_RUN"`.
- Each upload wrapped in try/except `httpx.HTTPError`; failures collected, not raised — caller sees one summary at the end with red/green per row.

### 18-02 — `scripts/upload_approved.py` CLI

```
usage: upload-approved [-h] [--yes] [--dry-run] [--root ROOT]
```

- `--dry-run`: build manifest, print STOP AND SHOW, but answer `n` automatically and exit 0
- `--yes`: skip the stdin prompt (for CI). STOP AND SHOW manifest still printed to stderr.
- Default: interactive `y/N` prompt via `input()` with `\n` flush.
- After confirmation: invoke `asyncio.run(upload_batch(manifest))`, render result table.
- Exit codes: 0 = all uploaded + verified; 1 = any failure (manifest empty, abort, WC error, verification mismatch); 2 = argparse usage.

### 18-03 — `tests/test_upload.py` integration suite

Test classes:

- `TestBuildManifest` — pure unit tests, no network:
  - Scans approved/ correctly, builds entries
  - Excludes SKU missing from approved/
  - Excludes SKU with empty wc_product_id
  - Excludes SKU with published=0
  - Excludes SKUs in SKIPPED.json
  - Returns empty manifest when nothing eligible

- `TestUploadBatch` — uses `respx` or `httpx.MockTransport` to intercept WC REST:
  - Successful upload path: POST media → 201; PUT product → 200; GET verify → matches
  - Media POST 4xx: row marked `FAILED`, batch continues
  - Product PUT 5xx: row marked `FAILED`, retry once with backoff, then fail
  - Verification mismatch (uploaded URL ≠ returned images[0].src): row `VERIFICATION_FAILED`
  - Idempotency: pre-existing matching image → `ALREADY_SYNCED`, no upload call
  - `dry_run=True`: zero HTTP calls; all entries `DRY_RUN`

- `TestStopAndShowGate` — CLI-level via subprocess:
  - Empty manifest → exit 1 with `manifest empty`
  - `--dry-run` → exit 0, no upload calls intercepted
  - Stdin "n" → exit 1 with `user declined`
  - Stdin "y" → proceeds (mocked transport)
  - `--yes` + empty manifest → still exits 1 (gate cannot bypass empty-manifest check)

Total: ~18 tests across 3 classes. Coverage target ≥85% on `skyyrose/elite_studio/upload.py`.

## Success Criteria → Test Mapping

| Success Criterion | Test |
|---|---|
| 1. Batch runs against all 28 SKUs without unhandled exceptions | `TestUploadBatch::test_media_post_4xx_continues_batch` + `test_product_put_5xx_continues_batch` |
| 2. STOP AND SHOW manifest before any WC API write | `TestStopAndShowGate::test_stdin_n_exits_1_with_user_declined` + `test_dry_run_makes_zero_http_calls` |
| 3. WC image field reflects new ghost mannequin (REST GET verified) | `TestUploadBatch::test_verify_upload_returns_true_on_match` + `test_verification_mismatch_marks_failed` |
| 4. SKUs without approved/{sku}-ghost-front.webp excluded | `TestBuildManifest::test_excludes_sku_missing_from_approved` |

## Verification Commands

```bash
# Pre-implementation: confirm Phase 17 contract intact
pytest tests/test_review.py -v   # 53 tests must still pass

# Phase 18 dev cycle
pytest tests/test_upload.py -v
pytest tests/test_upload.py --cov=skyyrose.elite_studio.upload --cov-report=term-missing

# Type check + lint
mypy skyyrose/elite_studio/upload.py scripts/upload_approved.py
ruff check skyyrose/elite_studio/upload.py scripts/upload_approved.py tests/test_upload.py
black --check skyyrose/elite_studio/upload.py scripts/upload_approved.py tests/test_upload.py

# CLI smoke (no API calls — manifest only)
python scripts/upload_approved.py --dry-run

# CLI dry-run with subset (after Phase 17 produces real approved/ files)
python scripts/upload_approved.py --dry-run --root .

# PRODUCTION RUN — requires STOP AND SHOW confirmation
python scripts/upload_approved.py
```

## Risk Register

| Risk | Severity | Mitigation |
|---|---|---|
| Wrong product_id from CSV → wrong product gets image | **CRITICAL** | Manifest includes `current_image_url` column so user can sanity-check before typing `y` |
| WC media library bloat from repeated uploads | HIGH | Idempotency check on media URL → no re-upload if already in WC. Doc note: there is no automatic cleanup of orphan media |
| Partial batch failure leaves inconsistent state | HIGH | Each upload + update + verify is per-SKU atomic; failures logged; user can re-run safely (idempotency catches done rows) |
| Rate limiting (WC enforces ~25 req/sec) | MEDIUM | Sequential per-SKU (not parallel); 3 requests per SKU × 28 SKUs = 84 reqs in ~10s well under cap. Linear backoff on 429. |
| WC_API auth fails mid-batch | MEDIUM | First-request smoke check (`wc_client.list(per_page=1)`) before manifest is shown — exits 1 with clear error before STOP AND SHOW |
| WordPress.com REST routing quirk | LOW | Per CLAUDE.md memory: site uses `index.php?rest_route=` not `/wp-json/`. WC client already handles this. Confirm in 18-02 against staging if available. |
| Phase 17 approved file deleted between manifest build and upload | LOW | Re-check file exists immediately before each POST; skip if vanished |

## Cost Estimate

- WordPress.com hosting: **$0.00 incremental** for WC REST calls (no metered API)
- WC Media Library storage: 28 × ~1.5MB = ~42MB total
- WC database writes: 28 product updates
- Time: ~10s end-to-end at sequential pace

**Confirmation gate is for production-write risk, not cost.** STOP AND SHOW reads as low-cost but high-blast-radius.

## Definition of Done

- [ ] `skyyrose/elite_studio/upload.py` exists, public surface implemented
- [ ] `scripts/upload_approved.py` CLI with `--dry-run`, `--yes`, `--root` flags
- [ ] `tests/test_upload.py` ≥18 tests across 3 classes
- [ ] `pytest tests/test_upload.py -v` all green
- [ ] Coverage ≥85% on `skyyrose.elite_studio.upload`
- [ ] `mypy + ruff + black` clean on all three files
- [ ] No `TODO`/`FIXME`/`pass`/`raise NotImplementedError` in delivered code
- [ ] PHASE-18-DRY-RUN.md captures the actual STOP AND SHOW manifest from a real dry-run against the live catalog
- [ ] Production run executed ONLY after explicit user confirmation; result table saved to `phases/18-batch-wc-upload/18-UAT.md`
- [ ] Single `feat:` commit for Phase 18 implementation; separate commit for the live-run UAT artifact

## Pre-execution Gate

Per CLAUDE.md STOP AND SHOW: **the production CLI run is itself a gate.** The PLAN can be implemented and tests can run autonomously, but invoking `python scripts/upload_approved.py` (without `--dry-run`) against the live skyyrose.co WC API requires explicit user `y` at runtime. No automation may bypass this.
