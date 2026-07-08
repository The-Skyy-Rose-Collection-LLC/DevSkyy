/**
 * Next.js Proxy — authentication gate for the DevSkyy admin dashboard.
 *
 * Renamed from middleware.ts → proxy.ts (Next.js 16 convention change), then
 * extended to also gate the dashboard's API surface.
 *
 * Unauthenticated requests (no NextAuth JWT session, decoded with NEXTAUTH_SECRET):
 *   - page requests → redirected to /login?callbackUrl=<url>
 *   - /api/* requests → 401 JSON (a redirect would corrupt a fetch)
 *
 * Scope (see `config.matcher`):
 *   - GATED: every /admin/* route, and every /api/* route …
 *   - OPEN:  …EXCEPT /api/auth/* (NextAuth itself — gating it deadlocks login),
 *            /api/checkout/* (the public storefront checkout endpoint), and
 *            /api/webhooks/* (HMAC-verified inside the handler itself — a
 *            NextAuth JWT gate here would 401 the sender before the
 *            handler's own signature check ever runs; see
 *            app/api/webhooks/woocommerce/route.ts).
 *   Public pages (/login, /collections, /pre-order, /checkout) are not matched.
 *
 * Every /api/* route here is consumed only by authenticated /admin pages, so an
 * authenticated browser session passes the gate transparently. Routes that also
 * run their own getServerSession check (e.g. /api/settings, /api/mcp) keep it as
 * defense in depth.
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getToken } from 'next-auth/jwt';

export async function proxy(request: NextRequest) {
  const token = await getToken({ req: request });
  if (token) {
    return NextResponse.next();
  }

  if (request.nextUrl.pathname.startsWith('/api/')) {
    return NextResponse.json({ success: false, error: 'Unauthorized' }, { status: 401 });
  }

  const loginUrl = new URL('/login', request.url);
  loginUrl.searchParams.set('callbackUrl', request.url);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: [
    '/admin/:path*',
    // All /api routes except NextAuth (`auth`), the public checkout endpoint,
    // and webhooks (auth is HMAC-inside-handler, see comment above). No
    // current API route name begins with "auth", "checkout", or "webhooks"
    // other than those three, so the prefix exclusion is exact.
    '/api/((?!auth|checkout|webhooks).*)',
  ],
};
