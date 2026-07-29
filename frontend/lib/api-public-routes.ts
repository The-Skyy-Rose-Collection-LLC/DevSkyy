/**
 * Dashboard API routes deliberately reachable without a session.
 *
 * THIS LIST DOES NOT OPEN ANYTHING. It is an assertion of intent consumed only
 * by the coverage test — `withAuth()` never reads it at runtime. What makes a
 * route public is the ABSENCE of the wrapper on its handlers; this list is how
 * you declare that absence was deliberate. Adding a name here without also
 * unwrapping the handlers leaves the route gated and the test silent.
 * Conversely, unwrapping without adding it here fails the build. Both halves,
 * same change, or you get a lie in one direction or the other.
 *
 * Kept in its own dependency-free module on purpose: `tests/api-auth-coverage`
 * imports this list, and pulling it from `lib/api-auth` would drag `next-auth`
 * and `next/server` into the test runner. vitest.config.ts documents why that
 * boundary matters — a test that cannot import its subject gets skipped, and a
 * skipped auth-coverage test is indistinguishable from a passing one.
 *
 * Entries are carried over verbatim from the matcher of the removed proxy.ts
 * and match a route directory EXACTLY. Prefix matching would let a future
 * `checkout-status/` silently inherit `checkout/`'s exemption — the same
 * fail-open shape the old matcher's `(?:/|$)` anchors were written to stop.
 */
export const PUBLIC_API_ROUTES: readonly string[] = [
  // NextAuth itself. Gating it deadlocks sign-in: you would need a session to
  // reach the endpoint that issues sessions.
  'auth/[...nextauth]',

  // Public storefront checkout endpoint — called by anonymous shoppers.
  'checkout',

  // Authenticated by HMAC signature inside the handler. A session gate here
  // would 401 WooCommerce before the handler's own signature check ever runs.
  'webhooks/woocommerce',
];
