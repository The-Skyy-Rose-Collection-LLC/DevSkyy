/**
 * Canonical product catalog reader (server-only).
 *
 * Reads `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` — the
 * ONE source of truth for every SkyyRose SKU. Parsed once per server process,
 * cached in module scope, hot-reloaded in `next dev` when the file changes.
 *
 * Never hardcode SKU lists or product names in admin UIs or API routes — call
 * `getCatalog()` / `getProduct(sku)` / `getCollectionProducts(slug)` instead.
 */
// Server-only: this module uses node:fs. Only import from route handlers or
// server components — importing from a client component will fail the build.
import fs from 'node:fs';
import path from 'node:path';

export interface CatalogProduct {
  sku: string;
  name: string;
  price: number;
  collection: string;
  description: string;
  badge: string;
  image: string;
  frontModelImage: string;
  backImage: string;
  backModelImage: string;
  sizes: string[];
  color: string;
  editionSize: number;
  published: boolean;
  isPreorder: boolean;
  brandingSpec: string;
}

const CANONICAL_CSV_RELATIVE = path.join(
  'wordpress-theme',
  'skyyrose-flagship',
  'data',
  'skyyrose-catalog.csv'
);

function resolveCsvPath(): string {
  // Walk up from cwd until we find a directory containing the canonical CSV.
  let dir = process.cwd();
  for (let i = 0; i < 6; i += 1) {
    const candidate = path.join(dir, CANONICAL_CSV_RELATIVE);
    if (fs.existsSync(candidate)) return candidate;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  throw new Error(
    `Canonical catalog not found. Expected to find ${CANONICAL_CSV_RELATIVE} walking up from ${process.cwd()}.`
  );
}

function parseCsv(text: string): CatalogProduct[] {
  const lines = text.split(/\r?\n/).filter((l) => l.length > 0);
  if (lines.length < 2) return [];

  const headers = splitCsvRow(lines[0]);
  const out: CatalogProduct[] = [];

  for (let i = 1; i < lines.length; i += 1) {
    const cells = splitCsvRow(lines[i]);
    if (cells.every((c) => c.trim() === '')) continue;
    const row: Record<string, string> = {};
    headers.forEach((h, idx) => {
      row[h] = (cells[idx] ?? '').trim();
    });
    if (!row.sku) continue;

    out.push({
      sku: row.sku,
      name: row.name ?? '',
      price: row.price ? Number.parseFloat(row.price) : 0,
      collection: row.collection ?? '',
      description: row.description ?? '',
      badge: row.badge ?? '',
      image: row.image ?? '',
      frontModelImage: row.front_model_image ?? '',
      backImage: row.back_image ?? '',
      backModelImage: row.back_model_image ?? '',
      sizes: row.sizes ? row.sizes.split('|').map((s) => s.trim()).filter(Boolean) : [],
      color: row.color ?? '',
      editionSize: row.edition_size ? Number.parseInt(row.edition_size, 10) || 0 : 0,
      published: row.published === '1',
      isPreorder: row.is_preorder === '1',
      brandingSpec: row.branding_spec ?? '',
    });
  }

  return out;
}

function splitCsvRow(line: string): string[] {
  const out: string[] = [];
  let cur = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        cur += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (ch === ',' && !inQuotes) {
      out.push(cur);
      cur = '';
    } else {
      cur += ch;
    }
  }
  out.push(cur);
  return out;
}

interface CacheEntry {
  products: CatalogProduct[];
  mtimeMs: number;
}

let cache: CacheEntry | null = null;

function loadFresh(): CatalogProduct[] {
  const csvPath = resolveCsvPath();
  const stat = fs.statSync(csvPath);
  if (cache && cache.mtimeMs === stat.mtimeMs) return cache.products;
  const text = fs.readFileSync(csvPath, 'utf-8');
  const products = parseCsv(text);
  cache = { products, mtimeMs: stat.mtimeMs };
  return products;
}

/** Full catalog, keyed by array order (matches CSV row order). */
export function getCatalog(): CatalogProduct[] {
  return loadFresh();
}

/** Single product by SKU, or null if not in the canonical catalog. */
export function getProduct(sku: string): CatalogProduct | null {
  return loadFresh().find((p) => p.sku === sku) ?? null;
}

/** All products in a collection slug (`black-rose`, `love-hurts`, `signature`, `kids-capsule`). */
export function getCollectionProducts(slug: string): CatalogProduct[] {
  return loadFresh().filter((p) => p.collection === slug);
}

/** Distinct collection slugs present in the catalog. */
export function getCollectionSlugs(): string[] {
  return Array.from(new Set(loadFresh().map((p) => p.collection)));
}
