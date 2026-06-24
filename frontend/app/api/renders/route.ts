/**
 * Render review queue API.
 *
 * GET /api/renders → the OAI render queue: every render on disk joined with its
 * review-state annotation and (best-effort) QC verdict, plus summary counts.
 */
import { NextResponse } from 'next/server';
import { connection } from 'next/server';

import { getRenderQueue } from '@/lib/renders';

export async function GET() {
  // Dynamic under `cacheComponents`: always reflect the current disk state.
  await connection();
  try {
    const queue = getRenderQueue();
    return NextResponse.json({ success: true, data: queue });
  } catch (error) {
    // Log detail server-side; the resolver message can include internal paths.
    console.error('[api/renders] read error:', error);
    return NextResponse.json({ success: false, error: 'Renders unavailable' }, { status: 500 });
  }
}
