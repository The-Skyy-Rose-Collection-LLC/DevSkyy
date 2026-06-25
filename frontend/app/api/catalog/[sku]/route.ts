/**
 * Admin Catalog API — single-SKU UPDATE.
 *
 * PUT /api/catalog/:sku  — patch editable commerce fields on one SKU and write
 * back to the canonical CSV. Validated with Zod (strict: unknown keys rejected).
 * Image columns are intentionally NOT accepted here — they are SOT-governed.
 */
import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

import { getProduct } from '@/lib/catalog';
import { updateProductRow } from '@/lib/catalog-write';
import { collapseNewlines, type CatalogPatch } from '@/lib/catalog-csv';

const patchSchema = z
  .object({
    name: z.string().trim().min(1).max(200).optional(),
    price: z.number().nonnegative().finite().optional(),
    badge: z.string().trim().max(120).optional(),
    sizes: z.array(z.string().trim().min(1)).max(20).optional(),
    color: z.string().trim().max(80).optional(),
    editionSize: z.number().int().nonnegative().optional(),
    published: z.boolean().optional(),
    isPreorder: z.boolean().optional(),
    description: z.string().trim().max(2000).optional(),
  })
  .strict();

type PatchInput = z.infer<typeof patchSchema>;

/** Convert the typed, validated input into raw CSV cell strings. */
function toCsvPatch(input: PatchInput): CatalogPatch {
  // Collapse any CR/LF in free-text values so a pasted line break can't split a
  // CSV row (the catalog is single-line-per-record by invariant).
  const patch: CatalogPatch = {};
  if (input.name !== undefined) patch.name = collapseNewlines(input.name);
  if (input.price !== undefined) patch.price = String(input.price);
  if (input.badge !== undefined) patch.badge = collapseNewlines(input.badge);
  if (input.sizes !== undefined) patch.sizes = input.sizes.map(collapseNewlines).join('|');
  if (input.color !== undefined) patch.color = collapseNewlines(input.color);
  if (input.editionSize !== undefined) patch.edition_size = String(input.editionSize);
  if (input.published !== undefined) patch.published = input.published ? '1' : '0';
  if (input.isPreorder !== undefined) patch.is_preorder = input.isPreorder ? '1' : '0';
  if (input.description !== undefined) patch.description = collapseNewlines(input.description);
  return patch;
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ sku: string }> }
) {
  const { sku } = await params;

  if (!getProduct(sku)) {
    return NextResponse.json({ success: false, error: 'Product not found' }, { status: 404 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ success: false, error: 'Invalid JSON body' }, { status: 400 });
  }

  const parsed = patchSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { success: false, error: 'Validation failed', issues: parsed.error.issues },
      { status: 400 }
    );
  }

  const patch = toCsvPatch(parsed.data);
  if (Object.keys(patch).length === 0) {
    return NextResponse.json(
      { success: false, error: 'No editable fields supplied' },
      { status: 400 }
    );
  }

  try {
    const { product, changed } = updateProductRow(sku, patch);
    return NextResponse.json({ success: true, data: { product, changed } });
  } catch (error) {
    const fsErr = error instanceof Error && 'code' in error ? (error as NodeJS.ErrnoException) : null;
    if (fsErr && (fsErr.code === 'EROFS' || fsErr.code === 'EACCES')) {
      return NextResponse.json(
        {
          success: false,
          error:
            'Catalog is read-only in this runtime. CSV writes require a filesystem-backed deployment (local / self-hosted), not serverless.',
        },
        { status: 503 }
      );
    }
    // SKU could be deleted between the existence check and the write (rare race).
    if (error instanceof Error && error.message.startsWith('SKU not found')) {
      return NextResponse.json({ success: false, error: 'Product not found' }, { status: 404 });
    }
    // Anything else is an internal inconsistency (Zod + collapseNewlines already
    // guard the input) — log detail, return a generic message.
    console.error('[api/catalog PUT] write error:', error);
    return NextResponse.json({ success: false, error: 'Catalog write failed' }, { status: 500 });
  }
}
