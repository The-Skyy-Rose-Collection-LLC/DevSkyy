/**
 * WordPress Proxy Client
 *
 * Shared fetch utility for all WordPress client classes.
 * Routes requests through /api/wordpress/proxy so credentials
 * stay server-side.
 */

const PROXY_URL = '/api/wordpress/proxy';

export async function wpProxyFetch(
  method: string,
  endpoint: string,
  body?: unknown
): Promise<any> {
  const response = await fetch(PROXY_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ method, endpoint, body }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`WordPress API error: ${response.status} ${errorText}`);
  }

  return response.json();
}
