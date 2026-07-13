import { describe, expect, it } from 'vitest';

import { assertNoTraversal, requireInt } from '../path-safety';

describe('assertNoTraversal', () => {
  it('throws on a `..` segment (traversal that would smuggle creds cross-endpoint)', () => {
    expect(() => assertNoTraversal('/wc/v3/orders/../../../wp/v2/users')).toThrow(/traversal/i);
    expect(() => assertNoTraversal('/wc/v3/products/..')).toThrow(/traversal/i);
    expect(() => assertNoTraversal('/wc/v3/orders/..\\..\\wp')).toThrow(/traversal/i);
  });

  it('allows a normal path and an encoded slash (%2F is not a `..` segment)', () => {
    expect(() => assertNoTraversal('/wc/store/v1/products')).not.toThrow();
    expect(() => assertNoTraversal('/skyyrose/v1/stock/br-001')).not.toThrow();
    expect(() => assertNoTraversal('/wc/v3/orders/5')).not.toThrow();
  });
});

describe('requireInt', () => {
  it('accepts non-negative integers (number or numeric string)', () => {
    expect(requireInt(5, 'id')).toBe(5);
    expect(requireInt('42', 'id')).toBe(42);
    expect(requireInt(0, 'id')).toBe(0);
  });

  it('rejects traversal payloads, negatives, and fractions', () => {
    expect(() => requireInt('5/../../wp/v2/users', 'order id')).toThrow(/order id/i);
    expect(() => requireInt(-1, 'id')).toThrow(/expected a non-negative integer/i);
    expect(() => requireInt(1.5, 'id')).toThrow(/expected a non-negative integer/i);
    expect(() => requireInt('abc', 'id')).toThrow(/id/i);
  });
});
