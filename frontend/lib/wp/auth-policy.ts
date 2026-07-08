/**
 * Auth-tier routing for the WordPress↔dashboard wiring client (WS7).
 *
 * Framework-free by design (no `server-only`, no `@/` aliases) so it can be
 * unit-tested directly with vitest — `lib/wp/client.ts` composes this with
 * `server-only` to build the actual server-side request primitive.
 */

export type AuthTier = 'public' | 'wc' | 'wp-app';

const WC_PREFIX = '/wc/v3/';

const PUBLIC_PREFIXES = [
  '/wc/store/',
  '/skyyrose/v1/collections',
  '/skyyrose/v1/stock/',
  '/skyyrose/v1/products/3d/',
  '/skyyrose/v1/kids-capsule/',
  '/skyyrose/v1/personalization/',
];

const WP_APP_PREFIXES = ['/skyyrose/v1/settings', '/skyyrose/v1/analytics/summary', '/agents-manager/'];

/**
 * Resolve which credential tier a WP REST API path requires. Throws on an
 * unmatched path instead of defaulting — a new route must be added here
 * explicitly, never silently treated as public or authed.
 */
export function resolveAuthTier(path: string): AuthTier {
  if (path.startsWith(WC_PREFIX)) return 'wc';
  if (PUBLIC_PREFIXES.some((prefix) => path.startsWith(prefix))) return 'public';
  if (WP_APP_PREFIXES.some((prefix) => path.startsWith(prefix))) return 'wp-app';
  throw new Error(`resolveAuthTier: no rule matches "${path}" — add an explicit rule, do not default.`);
}
