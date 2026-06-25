/**
 * Render review write.
 *
 * POST /api/renders/review { slug, file, approved?, flagged?, comment? }
 *   → merges one annotation into renders/oai/_review/review-state.json (the same
 *     file the standalone `:8944` board writes). REVERSIBLE — annotation only,
 *     no file moves, no catalog/SOT mutation.
 */
import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

import {
  isSafeSegment,
  loadReviewState,
  saveReviewEntry,
  type ReviewEntry,
} from '@/lib/renders';

const bodySchema = z
  .object({
    slug: z.string().min(1),
    file: z.string().min(1),
    approved: z.boolean().optional(),
    flagged: z.boolean().optional(),
    comment: z.string().max(2000).optional(),
  })
  .strict();

export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ success: false, error: 'Invalid JSON body' }, { status: 400 });
  }

  const parsed = bodySchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { success: false, error: 'Validation failed', issues: parsed.error.issues },
      { status: 400 }
    );
  }

  const { slug, file, approved, flagged, comment } = parsed.data;
  // slug/file form the state key (`slug/file`); they must be clean single segments.
  if (!isSafeSegment(slug) || !isSafeSegment(file)) {
    return NextResponse.json({ success: false, error: 'Invalid slug or file' }, { status: 400 });
  }

  const key = `${slug}/${file}`;
  const existing = loadReviewState()[key];

  // Merge onto the existing entry so a partial update keeps the other fields.
  const entry: ReviewEntry = {
    approved: approved ?? existing?.approved ?? false,
    flagged: flagged ?? existing?.flagged ?? false,
    comment: comment ?? existing?.comment ?? '',
    updated: new Date().toISOString(),
  };

  try {
    saveReviewEntry(key, entry);
    return NextResponse.json({ success: true, data: { key, entry } });
  } catch (error) {
    const fsErr = error instanceof Error && 'code' in error ? (error as NodeJS.ErrnoException) : null;
    if (fsErr && (fsErr.code === 'EROFS' || fsErr.code === 'EACCES')) {
      return NextResponse.json(
        {
          success: false,
          error:
            'Review state is read-only in this runtime. Writes require a filesystem-backed deployment (local / self-hosted).',
        },
        { status: 503 }
      );
    }
    console.error('[api/renders/review] write error:', error);
    return NextResponse.json({ success: false, error: 'Failed to save review' }, { status: 500 });
  }
}
