/**
 * Live WooCommerce catalog counts vs the canonical CSV, by collection (WS7).
 *
 * Surfaces drift (e.g. a product unpublished or miscategorized in WC vs the
 * CSV) — it does not reconcile it. Per project memory, live love-hurts/
 * signature counts were each -1 vs CSV as of 2026-07-07; that is real
 * production drift to report, not a bug in this route.
 *
 * GET /api/catalog/summary
 */
import { NextResponse } from 'next/server';
import { connection } from 'next/server';

import { getCatalog, getCollectionSlugs } from '@/lib/catalog';
import { wpRequestRaw, type WcStoreProduct } from '@/lib/wp/client';

export async function GET() {
  await connection();

  const response = await wpRequestRaw('/wc/store/v1/products?per_page=100');
  if (!response.ok) {
    return NextResponse.json(
      { success: false, error: `WooCommerce Store API returned ${response.status}` },
      { status: 502 }
    );
  }
  const products = (await response.json()) as WcStoreProduct[];

  const knownSlugs = getCollectionSlugs();
  const liveCounts: Record<string, number> = Object.fromEntries(knownSlugs.map((slug) => [slug, 0]));
  const uncategorized: string[] = [];

  for (const product of products) {
    const matchedSlugs = product.categories.map((category) => category.slug).filter((slug) => knownSlugs.includes(slug));
    if (matchedSlugs.length === 0) {
      uncategorized.push(product.name ?? String(product.id));
    }
    for (const slug of matchedSlugs) {
      liveCounts[slug] += 1;
    }
  }

  const csvProducts = getCatalog();
  const csvCounts: Record<string, number> = Object.fromEntries(
    knownSlugs.map((slug) => [slug, csvProducts.filter((product) => product.collection === slug).length])
  );

  const drift = knownSlugs
    .filter((slug) => liveCounts[slug] !== csvCounts[slug])
    .map((slug) => ({ collection: slug, live: liveCounts[slug], csv: csvCounts[slug] }));

  return NextResponse.json({ success: true, live: liveCounts, csv: csvCounts, drift, uncategorized });
}
