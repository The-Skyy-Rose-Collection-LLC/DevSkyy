/**
 * WordPress↔dashboard wiring health check (WS7).
 *
 * Probes 3 tiers: public read, authed WooCommerce REST, authed WP
 * Application-Password REST. A missing `WP_APP_PASSWORD` degrades
 * `authed_wp` to `false` with a reason instead of failing the whole probe —
 * app-password provisioning is a manual wp-admin step (see
 * `scripts/remediation/setup_credentials.py`).
 *
 * GET /api/health
 */
import { NextResponse } from 'next/server';
import { connection } from 'next/server';

import { wpRequestRaw } from '@/lib/wp/client';

export async function GET() {
  // `await connection()` opts this route out of static prerendering under
  // `cacheComponents`, so every probe is live — never a build-time snapshot
  // (same pattern as /api/catalog, bug-161).
  await connection();
  const start = Date.now();

  const reachable = await wpRequestRaw('/skyyrose/v1/collections')
    .then((response) => response.ok)
    .catch(() => false);

  const authedWc = await wpRequestRaw('/wc/v3/products?per_page=1')
    .then((response) => response.ok)
    .catch(() => false);

  let authedWp = false;
  let wpReason: string | undefined;
  if (!process.env.WP_APP_PASSWORD) {
    wpReason = 'WP_APP_PASSWORD not configured';
  } else {
    authedWp = await wpRequestRaw('/skyyrose/v1/settings')
      .then((response) => response.ok)
      .catch((error: unknown) => {
        wpReason = error instanceof Error ? error.message : String(error);
        return false;
      });
  }

  return NextResponse.json({
    dashboard: 'ok',
    wp: {
      reachable,
      authed_wc: authedWc,
      authed_wp: authedWp,
      ...(wpReason ? { wp_reason: wpReason } : {}),
    },
    latency_ms: Date.now() - start,
  });
}
