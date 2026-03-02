/**
 * WordPress API Proxy — Server-Side Credential Injection
 *
 * Proxies WordPress REST API requests so WooCommerce credentials
 * never reach the browser. Credentials are read from server-only
 * env vars (no NEXT_PUBLIC_ prefix).
 *
 * POST /api/wordpress/proxy
 * Body: { method: string, endpoint: string, body?: object }
 */

import { NextRequest, NextResponse } from 'next/server';

const WORDPRESS_URL = process.env.WORDPRESS_URL;
const WP_CONSUMER_KEY = process.env.WP_CONSUMER_KEY;
const WP_CONSUMER_SECRET = process.env.WP_CONSUMER_SECRET;

/** WordPress REST API namespace prefixes that are safe to proxy. */
const ALLOWED_PREFIXES = ['/wp/', '/wc/'];

export async function POST(request: NextRequest) {
  if (!WORDPRESS_URL || !WP_CONSUMER_KEY || !WP_CONSUMER_SECRET) {
    return NextResponse.json(
      { error: 'WordPress credentials not configured' },
      { status: 503 }
    );
  }

  let payload: { method?: string; endpoint?: string; body?: unknown };
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const { method = 'GET', endpoint, body } = payload;

  if (!endpoint || typeof endpoint !== 'string') {
    return NextResponse.json({ error: 'Missing endpoint' }, { status: 400 });
  }

  // Validate endpoint starts with an allowed namespace to prevent SSRF
  const pathPart = endpoint.split('?')[0];
  if (!ALLOWED_PREFIXES.some((prefix) => pathPart.startsWith(prefix))) {
    return NextResponse.json(
      { error: 'Invalid WordPress endpoint' },
      { status: 400 }
    );
  }

  const allowedMethods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'];
  const upperMethod = method.toUpperCase();
  if (!allowedMethods.includes(upperMethod)) {
    return NextResponse.json({ error: 'Invalid HTTP method' }, { status: 400 });
  }

  const credentials = Buffer.from(
    `${WP_CONSUMER_KEY}:${WP_CONSUMER_SECRET}`
  ).toString('base64');
  const url = `${WORDPRESS_URL}/index.php?rest_route=${endpoint}`;

  const fetchOptions: RequestInit = {
    method: upperMethod,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Basic ${credentials}`,
    },
  };

  if (body && ['POST', 'PUT', 'PATCH'].includes(upperMethod)) {
    fetchOptions.body = JSON.stringify(body);
  }

  try {
    const wpResponse = await fetch(url, fetchOptions);
    const contentType = wpResponse.headers.get('content-type') ?? '';

    if (contentType.includes('application/json')) {
      const data = await wpResponse.json();
      return NextResponse.json(data, { status: wpResponse.status });
    }

    // Non-JSON (e.g. HTML error pages) — return as text
    const text = await wpResponse.text();
    return new NextResponse(text, {
      status: wpResponse.status,
      headers: { 'Content-Type': contentType || 'text/plain' },
    });
  } catch {
    return NextResponse.json(
      { error: 'Failed to reach WordPress' },
      { status: 502 }
    );
  }
}
