/**
 * Price Utilities
 * Helper functions for price formatting and discount calculations
 *
 * @author DevSkyy Platform Team
 * @version 1.0.0
 */

/**
 * Format price with currency symbol
 *
 * @param amount - The price amount
 * @param currency - Currency code (default: 'USD')
 * @returns Formatted price string
 */
export function formatPrice(amount: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

/**
 * Calculate discount percentage
 *
 * @param original - Original price
 * @param sale - Sale price
 * @returns Discount percentage (0-100)
 */
export function calculateDiscount(original: number, sale: number): number {
  if (original <= 0 || sale >= original) return 0;
  return Math.round(((original - sale) / original) * 100);
}

/**
 * Get CSS class name for price display based on discount status
 *
 * @param hasDiscount - Whether the product has a discount
 * @returns CSS class name
 */
export function getPriceDisplayClass(hasDiscount: boolean): string {
  return hasDiscount ? 'price-discounted' : 'price-regular';
}

/**
 * Check if price has a valid discount
 *
 * @param price - Original price
 * @param salePrice - Sale price (optional)
 * @returns True if there's a valid discount
 */
export function hasValidDiscount(price: number, salePrice?: number): boolean {
  return salePrice !== undefined && salePrice > 0 && salePrice < price;
}

/**
 * Get the effective price (sale price if available, otherwise original)
 *
 * @param price - Original price
 * @param salePrice - Sale price (optional)
 * @returns The effective price
 */
export function getEffectivePrice(price: number, salePrice?: number): number {
  return hasValidDiscount(price, salePrice) ? salePrice! : price;
}

/**
 * Format price range for products with multiple variants
 *
 * @param minPrice - Minimum price
 * @param maxPrice - Maximum price
 * @param currency - Currency code (default: 'USD')
 * @returns Formatted price range string
 */
export function formatPriceRange(
  minPrice: number,
  maxPrice: number,
  currency: string = 'USD'
): string {
  if (minPrice === maxPrice) {
    return formatPrice(minPrice, currency);
  }
  return `${formatPrice(minPrice, currency)} - ${formatPrice(maxPrice, currency)}`;
}
