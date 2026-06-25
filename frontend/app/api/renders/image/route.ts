/**
 * Render image proxy.
 *
 * GET /api/renders/image?slug=<slug>&file=<file> → streams a render PNG/WEBP from
 * `renders/oai/<slug>/<file>`. These files live outside `public/`, so this route
 * is how the review queue shows real pixels.
 *
 * Path-traversal guard: `resolveRenderImage` rejects `.`/`..`/separators, allows
 * only image extensions, and verifies the resolved path is contained in the
 * renders dir. Returns 404 for anything that fails the guard.
 */
import { NextRequest, NextResponse } from 'next/server';
import { connection } from 'next/server';
import fs from 'node:fs';

import { resolveRenderImage } from '@/lib/renders';

// Cap in-memory reads so a huge (or symlink-redirected) file can't exhaust
// memory / block the event loop.
const MAX_IMAGE_BYTES = 25 * 1024 * 1024;

export async function GET(request: NextRequest) {
  await connection();

  const { searchParams } = request.nextUrl;
  const slug = searchParams.get('slug') ?? '';
  const file = searchParams.get('file') ?? '';

  const resolved = resolveRenderImage(slug, file);
  if (!resolved) {
    return new NextResponse('Not found', { status: 404 });
  }

  try {
    if (fs.statSync(resolved.path).size > MAX_IMAGE_BYTES) {
      return new NextResponse('File too large', { status: 413 });
    }
    const bytes = new Uint8Array(fs.readFileSync(resolved.path));
    return new NextResponse(bytes, {
      status: 200,
      headers: {
        'Content-Type': resolved.contentType,
        'Cache-Control': 'no-store',
      },
    });
  } catch {
    return new NextResponse('Not found', { status: 404 });
  }
}
