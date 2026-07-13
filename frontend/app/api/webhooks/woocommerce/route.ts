/**
 * WooCommerce webhook receiver — HMAC-verified, tag-based revalidation (WS7).
 *
 * WooCommerce's delivery request carries no NextAuth session, so auth here
 * is the HMAC signature itself. This route is excluded from `proxy.ts`'s
 * JWT gate for exactly that reason — see the matcher comment there.
 *
 * POST /api/webhooks/woocommerce
 */
import { NextRequest, NextResponse } from 'next/server';
import { revalidateTag } from 'next/cache';

import { verifyWebhookSignature } from '@/lib/wp/signature';

export async function POST(request: NextRequest) {
  const rawBody = await request.text();

  const secret = process.env.WP_WEBHOOK_SECRET;
  if (!secret) {
    // Server misconfiguration, not a client error.
    console.error('[api/webhooks/woocommerce] WP_WEBHOOK_SECRET not configured');
    return NextResponse.json({ error: 'WP_WEBHOOK_SECRET not configured' }, { status: 500 });
  }

  const providedSignature = request.headers.get('x-wc-webhook-signature');
  if (!verifyWebhookSignature(rawBody, secret, providedSignature)) {
    return NextResponse.json({ error: 'invalid signature' }, { status: 401 });
  }

  const topic = request.headers.get('x-wc-webhook-topic');
  const trimmedBody = rawBody.trim();
  if (!topic || trimmedBody === '' || trimmedBody === '{}') {
    // WooCommerce sends an empty/near-empty delivery when a webhook is
    // registered (or manually re-delivered) to verify the endpoint is alive.
    return NextResponse.json({ received: true, ping: true }, { status: 200 });
  }

  if (topic.startsWith('product.')) {
    revalidateTag('catalog', 'max');
  } else if (topic.startsWith('order.')) {
    revalidateTag('orders', 'max');
  }

  return NextResponse.json({ received: true, topic }, { status: 200 });
}
