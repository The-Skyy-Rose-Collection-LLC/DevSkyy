/**
 * SkyyRose dashboard ↔ WordPress typed client (WS7 wiring core).
 *
 * URL-FORM EVIDENCE (2026-07-07): the direct `${WP_BASE_URL}/wp-json<path>`
 * form is verified HTTP 200 this session for PUBLIC GETs — curl against
 * skyyrose/v1/collections, wc/store/v1/products, and the skyyrose/v1 /
 * agents-manager discovery docs. The SAME direct-path form is verified for
 * AUTHED calls (wc/v3/products with WC Basic auth, wp/v2/users/me and
 * skyyrose/v1/settings with Application-Password Basic auth) — but only via
 * `scripts/remediation/setup_credentials.py`'s Python `requests` calls
 * (HG-7, closed 2026-07-05). It is NOT independently verified from Node's
 * `fetch` under Vercel's runtime. Counter-evidence: the legacy proxy
 * (`app/api/wordpress/proxy/route.ts`) uses `index.php?rest_route=` for its
 * authed calls and has real production consumers. URL construction is
 * isolated in `buildUrl()` below so a form-flip is a one-line change if
 * `scripts/remediation/wiring_audit.py`'s authed wc/v3 check fails live.
 *
 * Coexists with the legacy stack (`app/api/wordpress/proxy/route.ts`,
 * `lib/wordpress/*`, `WORDPRESS_URL`/`WOOCOMMERCE_KEY`/`WOOCOMMERCE_SECRET`)
 * — that stack has its own real consumers and is untouched here. This
 * client uses ONLY the `WP_*`/`WC_*` env names from
 * `scripts/remediation/setup_credentials.py`'s `ENV_KEYS` contract.
 */
import 'server-only';

import { resolveAuthTier, type AuthTier } from './auth-policy';
import { RequestThrottle } from './throttle';

type WpEnvKey = 'WP_BASE_URL' | 'WP_APP_USER' | 'WP_APP_PASSWORD' | 'WC_CONSUMER_KEY' | 'WC_CONSUMER_SECRET';

function requireEnv(key: WpEnvKey): string {
  const value = process.env[key];
  if (!value) {
    throw new Error(`Missing required env var: ${key}`);
  }
  return value;
}

function buildUrl(path: string): string {
  const base = requireEnv('WP_BASE_URL').replace(/\/$/, '');
  return `${base}/wp-json${path.startsWith('/') ? path : `/${path}`}`;
}

function authHeader(tier: AuthTier): Record<string, string> {
  if (tier === 'public') return {};
  if (tier === 'wc') {
    const key = requireEnv('WC_CONSUMER_KEY');
    const secret = requireEnv('WC_CONSUMER_SECRET');
    return { Authorization: `Basic ${Buffer.from(`${key}:${secret}`).toString('base64')}` };
  }
  const user = requireEnv('WP_APP_USER');
  const password = requireEnv('WP_APP_PASSWORD');
  return { Authorization: `Basic ${Buffer.from(`${user}:${password}`).toString('base64')}` };
}

const throttle = new RequestThrottle();

export class WpRequestError extends Error {
  constructor(
    public readonly status: number,
    public readonly path: string,
    bodyText: string
  ) {
    super(`WP request failed (${status}) for ${path}: ${bodyText.slice(0, 500)}`);
    this.name = 'WpRequestError';
  }
}

/**
 * Low-level fetch primitive: resolves the auth tier, throttles to the
 * request budget, retries on 429 honoring `Retry-After` (max
 * `throttle.maxRetries`), and tags cacheable public GETs `['catalog']` for
 * `revalidateTag`. Returns the raw `Response` so callers that need headers
 * (e.g. `X-WP-Total`) can read them — JSON-returning callers use `wpRequest`.
 */
export async function wpRequestRaw(path: string, init: RequestInit = {}): Promise<Response> {
  const tier = resolveAuthTier(path);
  const method = (init.method ?? 'GET').toUpperCase();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...authHeader(tier),
    ...(init.headers as Record<string, string> | undefined),
  };
  const fetchInit: RequestInit = {
    ...init,
    method,
    headers,
    ...(tier === 'public' && method === 'GET' ? { next: { tags: ['catalog'] } } : {}),
  };

  let attempt = 0;
  for (;;) {
    await throttle.wait();
    const response = await fetch(buildUrl(path), fetchInit);
    if (response.status === 429 && attempt < throttle.maxRetries) {
      const delayMs = throttle.computeBackoffMs(attempt, response.headers.get('Retry-After'));
      await new Promise((resolve) => setTimeout(resolve, delayMs));
      attempt += 1;
      continue;
    }
    return response;
  }
}

/** JSON-returning wrapper around `wpRequestRaw`. Throws `WpRequestError` on non-2xx. */
export async function wpRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await wpRequestRaw(path, init);
  if (!response.ok) {
    const bodyText = await response.text().catch(() => '');
    throw new WpRequestError(response.status, path, bodyText);
  }
  return (await response.json()) as T;
}

// ─── Typed shapes (only what the dashboard actually reads/writes) ─────────

export interface WcCategoryRef {
  id?: number;
  name?: string;
  slug: string;
}

export interface WcStoreProduct {
  id: number;
  name: string;
  slug?: string;
  categories: WcCategoryRef[];
  [key: string]: unknown;
}

export interface WcOrder {
  id: number;
  status: string;
  [key: string]: unknown;
}

export interface SkyyRoseCollection {
  slug?: string;
  label?: string;
  category?: string;
  [key: string]: unknown;
}

export type SkyyRoseSettings = Record<string, unknown>;

export interface GetProductsResult {
  products: WcStoreProduct[];
  total: number;
}

export interface BatchProductOps {
  create?: Record<string, unknown>[];
  update?: Record<string, unknown>[];
  delete?: number[];
}

// ─── Typed methods ──────────────────────────────────────────────────────

export async function getCollections(): Promise<Record<string, SkyyRoseCollection>> {
  const data = await wpRequest<{ collections: Record<string, SkyyRoseCollection> }>('/skyyrose/v1/collections');
  return data.collections;
}

export async function getProducts(opts: { category?: string; page?: number } = {}): Promise<GetProductsResult> {
  const params = new URLSearchParams({ per_page: '100', page: String(opts.page ?? 1) });
  if (opts.category) params.set('category', opts.category);
  const path = `/wc/store/v1/products?${params.toString()}`;
  const response = await wpRequestRaw(path);
  if (!response.ok) {
    const bodyText = await response.text().catch(() => '');
    throw new WpRequestError(response.status, path, bodyText);
  }
  const products = (await response.json()) as WcStoreProduct[];
  const total = Number.parseInt(response.headers.get('X-WP-Total') ?? String(products.length), 10);
  return { products, total };
}

export async function getStock(sku: string): Promise<unknown> {
  return wpRequest(`/skyyrose/v1/stock/${encodeURIComponent(sku)}`);
}

export async function get3DProducts(category: string): Promise<unknown[]> {
  return wpRequest<unknown[]>(`/skyyrose/v1/products/3d/${encodeURIComponent(category)}`);
}

export async function getOrders(opts: { status?: string } = {}): Promise<WcOrder[]> {
  const params = new URLSearchParams();
  if (opts.status) params.set('status', opts.status);
  const qs = params.toString();
  return wpRequest<WcOrder[]>(`/wc/v3/orders${qs ? `?${qs}` : ''}`);
}

export async function updateOrder(id: number, patch: Record<string, unknown>): Promise<WcOrder> {
  return wpRequest<WcOrder>(`/wc/v3/orders/${id}`, { method: 'PUT', body: JSON.stringify(patch) });
}

export async function updateProduct(id: number, patch: Record<string, unknown>): Promise<WcStoreProduct> {
  return wpRequest<WcStoreProduct>(`/wc/v3/products/${id}`, { method: 'PUT', body: JSON.stringify(patch) });
}

export async function batchProducts(ops: BatchProductOps): Promise<unknown> {
  return wpRequest('/wc/v3/products/batch', { method: 'POST', body: JSON.stringify(ops) });
}

export async function getSettings(): Promise<SkyyRoseSettings> {
  return wpRequest<SkyyRoseSettings>('/skyyrose/v1/settings');
}

export async function updateSettings(patch: Record<string, unknown>): Promise<SkyyRoseSettings> {
  return wpRequest<SkyyRoseSettings>('/skyyrose/v1/settings', { method: 'PATCH', body: JSON.stringify(patch) });
}

export async function pushNarrative(payload: Record<string, unknown>): Promise<unknown> {
  return wpRequest('/skyyrose/v1/settings/narrative', { method: 'POST', body: JSON.stringify(payload) });
}

export async function getAnalyticsSummary(): Promise<unknown> {
  return wpRequest('/skyyrose/v1/analytics/summary');
}

export async function agentsOpenState(action: 'get' | 'set', value?: Record<string, unknown>): Promise<unknown> {
  if (action === 'get') return wpRequest('/agents-manager/open-state');
  return wpRequest('/agents-manager/open-state', { method: 'POST', body: JSON.stringify(value ?? {}) });
}
