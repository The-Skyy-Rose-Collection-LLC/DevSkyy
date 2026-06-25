/**
 * Canonical catalog WRITE path (server-only).
 *
 * Writes back to `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`
 * — the ONE source of truth — via an atomic temp-file rename. Only the edited
 * SKU's row is re-serialized (see `applyPatch`); all other rows, and all 24
 * columns, are preserved verbatim.
 *
 * IMPORTANT boundaries (surfaced in the UI, not hidden):
 *  - A save updates the upstream CSV only. It does NOT reach skyyrose.co — that
 *    requires `scripts/sync_catalog_downstream.py` + a WordPress deploy.
 *  - Image columns are NOT writable here: they are governed by the generated
 *    SOT manifest (`data/sot-images.json`). Image assignment is the renders/
 *    review queue's job, not this editor's.
 *  - On a read-only filesystem (e.g. serverless), the write raises EROFS/EACCES
 *    and the caller returns a clear error — it is not silently dropped.
 */
import 'server-only';

import fs from 'node:fs';
import path from 'node:path';

import { resolveCsvPath, resetCatalogCache, getProduct, type CatalogProduct } from './catalog';
import { applyPatch, type CatalogPatch } from './catalog-csv';

export interface UpdateResult {
  product: CatalogProduct;
  changed: boolean;
}

/**
 * Apply `patch` (raw CSV cell strings, editable columns only) to one SKU and
 * persist it atomically. Returns the re-read product and whether anything
 * changed on disk.
 */
export function updateProductRow(sku: string, patch: CatalogPatch): UpdateResult {
  const csvPath = resolveCsvPath();
  const original = fs.readFileSync(csvPath, 'utf-8');

  const { text, changed } = applyPatch(original, sku, patch);

  if (changed) {
    const dir = path.dirname(csvPath);
    // Concurrency model: this whole function is SYNCHRONOUS (no `await` between
    // read and rename), so the single-threaded event loop runs it to completion
    // without interleaving — two concurrent requests serialize, the second reads
    // the first's write. Keep it synchronous; making it async would reintroduce a
    // read-modify-write race and need a lock. The unique temp name (pid + time +
    // random) additionally guards against cross-process collisions, and same-dir
    // placement keeps rename() atomic (same filesystem).
    const tmp = path.join(
      dir,
      `.skyyrose-catalog.${process.pid}.${Date.now()}.${Math.random().toString(36).slice(2)}.tmp`
    );
    try {
      fs.writeFileSync(tmp, text, 'utf-8');
      fs.renameSync(tmp, csvPath);
    } catch (err) {
      // Best-effort cleanup of the temp file; rethrow the original cause.
      try {
        if (fs.existsSync(tmp)) fs.unlinkSync(tmp);
      } catch {
        // ignore cleanup failure
      }
      throw err;
    }
    resetCatalogCache();
  }

  const product = getProduct(sku);
  if (!product) {
    throw new Error(`SKU not found after write: ${sku}`);
  }
  return { product, changed };
}
