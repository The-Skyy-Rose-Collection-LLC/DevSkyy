/**
 * Orders-count for the Operator Console's nav badge (ConsoleShell fetches
 * this client-side via useQuery — see frontend/CLAUDE.md's catalog gotcha:
 * lib/wp/client.ts is server-only and can't be called from a client component
 * directly). proxy.ts's blanket /api/* matcher was removed in favor of
 * per-handler withAuth() (lib/api-auth.ts) — gate here, not at the edge.
 */
import { NextResponse } from 'next/server';
import { getOrders } from '@/lib/wp/client';
import { withAuth } from '@/lib/api-auth';

export const GET = withAuth(async () => {
  try {
    const orders = await getOrders();
    return NextResponse.json({ count: orders.length });
  } catch (error) {
    // WooCommerce credentials not wired yet (see /admin/settings) — the badge
    // just doesn't render rather than failing the whole nav.
    console.error('[api/console/orders-count]', error);
    return NextResponse.json({ count: 0 });
  }
});
