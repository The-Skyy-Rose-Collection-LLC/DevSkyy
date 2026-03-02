/**
 * WordPress Media Upload Proxy — Server-Side Credential Injection
 *
 * Proxies multipart file uploads to WordPress REST API so
 * WooCommerce credentials never reach the browser.
 *
 * POST /api/wordpress/proxy/upload
 * Body: FormData with 'file' field + optional metadata fields
 */

import { NextRequest, NextResponse } from 'next/server';

const WORDPRESS_URL = process.env.WORDPRESS_URL;
const WP_CONSUMER_KEY = process.env.WP_CONSUMER_KEY;
const WP_CONSUMER_SECRET = process.env.WP_CONSUMER_SECRET;

export async function POST(request: NextRequest) {
  if (!WORDPRESS_URL || !WP_CONSUMER_KEY || !WP_CONSUMER_SECRET) {
    return NextResponse.json(
      { error: 'WordPress credentials not configured' },
      { status: 503 }
    );
  }

  const formData = await request.formData();
  const file = formData.get('file');
  if (!file) {
    return NextResponse.json({ error: 'Missing file field' }, { status: 400 });
  }

  const credentials = Buffer.from(
    `${WP_CONSUMER_KEY}:${WP_CONSUMER_SECRET}`
  ).toString('base64');
  const url = `${WORDPRESS_URL}/index.php?rest_route=/wp/v2/media`;

  // Forward the entire FormData with credentials attached
  const wpFormData = new FormData();
  for (const [key, value] of formData.entries()) {
    wpFormData.append(key, value);
  }

  try {
    const wpResponse = await fetch(url, {
      method: 'POST',
      headers: {
        Authorization: `Basic ${credentials}`,
        // Do NOT set Content-Type — fetch auto-sets multipart boundary
      },
      body: wpFormData,
    });

    const data = await wpResponse.json();
    return NextResponse.json(data, { status: wpResponse.status });
  } catch {
    return NextResponse.json(
      { error: 'Failed to upload to WordPress' },
      { status: 502 }
    );
  }
}
