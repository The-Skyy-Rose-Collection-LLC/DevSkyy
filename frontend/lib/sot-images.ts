/**
 * Read-only SOT (source-of-truth) product-imagery reader (server-only).
 *
 * Surfaces the GENERATED manifest `data/sot-images.json` — the front-first
 * imagery contract produced by `skyyrose.core.sot_images` (regenerated with
 * `make sot-manifest`). The manifest header says DO NOT EDIT; this module only
 * READS it so the catalog editor can show which images the SOT resolver will
 * serve for a SKU. Image *assignment* is the renders/review queue's job.
 */
import 'server-only';

import fs from 'node:fs';
import path from 'node:path';

import { resolveRepoFile } from './catalog';

export interface SotImageSet {
  front: string;
  back: string;
  packshot: string;
}

const SOT_RELATIVE = path.join('data', 'sot-images.json');

interface SotCache {
  images: Record<string, Partial<SotImageSet>>;
  mtimeMs: number;
}

let sotCache: SotCache | null = null;

function load(): Record<string, Partial<SotImageSet>> {
  let manifestPath: string;
  try {
    manifestPath = resolveRepoFile(SOT_RELATIVE);
  } catch {
    return {};
  }

  try {
    const stat = fs.statSync(manifestPath);
    if (sotCache && sotCache.mtimeMs === stat.mtimeMs) {
      return sotCache.images;
    }
    const raw = JSON.parse(fs.readFileSync(manifestPath, 'utf-8')) as unknown;
    const images =
      raw && typeof raw === 'object' && 'images' in raw && typeof (raw as { images: unknown }).images === 'object'
        ? ((raw as { images: Record<string, Partial<SotImageSet>> }).images ?? {})
        : {};
    sotCache = { images, mtimeMs: stat.mtimeMs };
    return images;
  } catch {
    return {};
  }
}

/** SOT image set for one SKU (front-first), or null if the SKU is absent. */
export function getSotImagesForSku(sku: string): Partial<SotImageSet> | null {
  return load()[sku] ?? null;
}
