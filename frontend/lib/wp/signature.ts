/**
 * WooCommerce webhook HMAC signature — compute + verify (WS7).
 *
 * Mirrors WooCommerce's own scheme: `base64_encode(hash_hmac('sha256',
 * payload, secret, true))`. Framework-free (node:crypto only) so it can be
 * unit-tested directly with vitest.
 */

import { createHmac, timingSafeEqual } from 'node:crypto';

export function computeWebhookSignature(rawBody: string, secret: string): string {
  return createHmac('sha256', secret).update(rawBody, 'utf8').digest('base64');
}

/**
 * Constant-time signature check. Returns false (never throws) for a missing
 * or malformed signature — the caller maps false to a 401.
 */
export function verifyWebhookSignature(
  rawBody: string,
  secret: string,
  providedSignatureB64: string | null
): boolean {
  if (!providedSignatureB64) return false;
  const expected = Buffer.from(computeWebhookSignature(rawBody, secret), 'base64');
  const provided = Buffer.from(providedSignatureB64, 'base64');
  if (expected.length !== provided.length) return false; // timingSafeEqual requires equal lengths
  return timingSafeEqual(expected, provided);
}
