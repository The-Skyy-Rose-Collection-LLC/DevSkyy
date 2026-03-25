/**
 * Unit Tests for Price Utilities
 */

import {
  formatPrice,
  calculateDiscount,
  getPriceDisplayClass,
  hasValidDiscount,
  getEffectivePrice,
  formatPriceRange,
} from '../priceUtils';

describe('priceUtils', () => {
  describe('formatPrice', () => {
    it('should format USD price', () => {
      expect(formatPrice(99.99)).toBe('$99.99');
    });

    it('should format zero', () => {
      expect(formatPrice(0)).toBe('$0.00');
    });

    it('should format large amounts', () => {
      expect(formatPrice(1234.56)).toBe('$1,234.56');
    });

    it('should format with custom currency', () => {
      const result = formatPrice(50, 'EUR');
      expect(result).toContain('50.00');
    });

    it('should round to 2 decimal places', () => {
      expect(formatPrice(9.999)).toBe('$10.00');
    });
  });

  describe('calculateDiscount', () => {
    it('should calculate percentage', () => {
      expect(calculateDiscount(100, 75)).toBe(25);
    });

    it('should return 0 when no discount', () => {
      expect(calculateDiscount(100, 100)).toBe(0);
    });

    it('should return 0 when sale > original', () => {
      expect(calculateDiscount(50, 75)).toBe(0);
    });

    it('should return 0 for zero original', () => {
      expect(calculateDiscount(0, 0)).toBe(0);
    });

    it('should round to nearest integer', () => {
      expect(calculateDiscount(100, 67)).toBe(33);
    });
  });

  describe('getPriceDisplayClass', () => {
    it('should return discounted class', () => {
      expect(getPriceDisplayClass(true)).toBe('price-discounted');
    });

    it('should return regular class', () => {
      expect(getPriceDisplayClass(false)).toBe('price-regular');
    });
  });

  describe('hasValidDiscount', () => {
    it('should return true for valid discount', () => {
      expect(hasValidDiscount(100, 75)).toBe(true);
    });

    it('should return false when no salePrice', () => {
      expect(hasValidDiscount(100)).toBe(false);
    });

    it('should return false for zero salePrice', () => {
      expect(hasValidDiscount(100, 0)).toBe(false);
    });

    it('should return false when salePrice >= price', () => {
      expect(hasValidDiscount(100, 100)).toBe(false);
      expect(hasValidDiscount(100, 150)).toBe(false);
    });
  });

  describe('getEffectivePrice', () => {
    it('should return salePrice when valid', () => {
      expect(getEffectivePrice(100, 75)).toBe(75);
    });

    it('should return original when no discount', () => {
      expect(getEffectivePrice(100)).toBe(100);
    });

    it('should return original when salePrice invalid', () => {
      expect(getEffectivePrice(100, 0)).toBe(100);
      expect(getEffectivePrice(100, 150)).toBe(100);
    });
  });

  describe('formatPriceRange', () => {
    it('should format single price when min equals max', () => {
      expect(formatPriceRange(50, 50)).toBe('$50.00');
    });

    it('should format range when different', () => {
      const result = formatPriceRange(25, 100);
      expect(result).toBe('$25.00 - $100.00');
    });

    it('should accept custom currency', () => {
      const result = formatPriceRange(10, 20, 'GBP');
      expect(result).toContain('10.00');
      expect(result).toContain('20.00');
    });
  });
});
