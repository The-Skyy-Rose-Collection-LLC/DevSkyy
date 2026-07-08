import { describe, expect, it } from 'vitest';

import { computeWebhookSignature, verifyWebhookSignature } from '../signature';

describe('webhook signature', () => {
  const secret = 'test-secret';
  const body = JSON.stringify({ id: 42, topic: 'product.updated' });

  it('accepts a signature computed from the same body and secret', () => {
    const signature = computeWebhookSignature(body, secret);
    expect(verifyWebhookSignature(body, secret, signature)).toBe(true);
  });

  it('rejects a tampered body', () => {
    const signature = computeWebhookSignature(body, secret);
    expect(verifyWebhookSignature(`${body}x`, secret, signature)).toBe(false);
  });

  it('rejects a signature computed with the wrong secret', () => {
    const signature = computeWebhookSignature(body, `${secret}-wrong`);
    expect(verifyWebhookSignature(body, secret, signature)).toBe(false);
  });

  it('rejects a null signature', () => {
    expect(verifyWebhookSignature(body, secret, null)).toBe(false);
  });

  it('rejects a malformed base64 signature without throwing', () => {
    expect(() => verifyWebhookSignature(body, secret, '***not-base64***')).not.toThrow();
    expect(verifyWebhookSignature(body, secret, '***not-base64***')).toBe(false);
  });
});
