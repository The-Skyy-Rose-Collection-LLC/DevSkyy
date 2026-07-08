import { describe, expect, it } from 'vitest';

import { resolveAuthTier } from '../auth-policy';

describe('resolveAuthTier', () => {
  it('routes /wc/v3/* to the wc tier', () => {
    expect(resolveAuthTier('/wc/v3/products')).toBe('wc');
    expect(resolveAuthTier('/wc/v3/orders/12')).toBe('wc');
    expect(resolveAuthTier('/wc/v3/products/batch')).toBe('wc');
  });

  it('routes public storefront + skyyrose read endpoints to the public tier', () => {
    expect(resolveAuthTier('/wc/store/v1/products')).toBe('public');
    expect(resolveAuthTier('/skyyrose/v1/collections')).toBe('public');
    expect(resolveAuthTier('/skyyrose/v1/stock/br-001')).toBe('public');
    expect(resolveAuthTier('/skyyrose/v1/products/3d/black-rose')).toBe('public');
    expect(resolveAuthTier('/skyyrose/v1/kids-capsule/matching-set/1')).toBe('public');
    expect(resolveAuthTier('/skyyrose/v1/personalization/abc123')).toBe('public');
  });

  it('routes settings/analytics/agents-manager to the wp-app tier', () => {
    expect(resolveAuthTier('/skyyrose/v1/settings')).toBe('wp-app');
    expect(resolveAuthTier('/skyyrose/v1/settings/narrative')).toBe('wp-app');
    expect(resolveAuthTier('/skyyrose/v1/analytics/summary')).toBe('wp-app');
    expect(resolveAuthTier('/agents-manager/open-state')).toBe('wp-app');
  });

  it('throws on an unmatched path instead of defaulting', () => {
    expect(() => resolveAuthTier('/unknown/v1/whatever')).toThrow(/no rule matches/);
  });
});
