/**
 * Admin Catalog API — RAW catalog read for the /admin/catalog editor.
 *
 * Unlike `/api/products` (which marketing-SHAPES rows with derived fields like
 * `remaining` and `originalPrice`), this returns the canonical `CatalogProduct`
 * verbatim plus the read-only SOT image set per SKU. It is the editor's source
 * of truth for what is actually on disk.
 *
 * GET /api/catalog → { success, data: { products, total, collections } }
 */
import { NextResponse } from 'next/server';
import { connection } from 'next/server';

import { getCatalog, getCollectionSlugs } from '@/lib/catalog';
import { getSotImagesForSku } from '@/lib/sot-images';

export async function GET() {
  // `await connection()` opts this route out of static prerendering under
  // `cacheComponents`, so it always reads the catalog fresh from disk and never
  // serves a build-time snapshot after a write.
  await connection();
  try {
    const products = getCatalog().map((p) => ({
      ...p,
      sot: getSotImagesForSku(p.sku),
    }));

    return NextResponse.json({
      success: true,
      data: {
        products,
        total: products.length,
        collections: getCollectionSlugs(),
      },
    });
  } catch (error) {
    // Log the detail server-side; the raw message can include internal paths
    // (process.cwd()) from the resolver — don't leak it to the client.
    console.error('[api/catalog] read error:', error);
    return NextResponse.json({ success: false, error: 'Catalog unavailable' }, { status: 500 });
  }
}
