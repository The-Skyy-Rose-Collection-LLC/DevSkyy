/**
 * ProductLoader - Loads products with 3D position data from WooCommerce REST API
 *
 * Context7 Query Used:
 * - /woocommerce/woocommerce-rest-api-docs - WooCommerce REST API product endpoints
 *
 * Implements the documented pattern for fetching products by category with
 * custom meta fields (3D positions). Uses native fetch API with proper error
 * handling and caching for optimal performance.
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

export default class ProductLoader {
  /**
   * Constructor
   */
  constructor() {
    this.cache = new Map();
    this.baseUrl = window.location.origin + '/wp-json/skyyrose/v1/products/3d';
  }

  /**
   * Load products for a specific collection category
   *
   * @param {string} categorySlug - Category slug (e.g., 'signature-collection')
   * @param {boolean} useCache - Whether to use cached data if available
   * @returns {Promise<Array>} Array of product objects with 3D position data
   */
  async loadCollectionProducts(categorySlug, useCache = true) {
    // Check cache first
    if (useCache && this.cache.has(categorySlug)) {
      console.log(`[ProductLoader] Using cached data for ${categorySlug}`);
      return this.cache.get(categorySlug);
    }

    try {
      console.log(`[ProductLoader] Fetching products for ${categorySlug}...`);
      const url = `${this.baseUrl}/${categorySlug}`;

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const products = await response.json();
      console.log(`[ProductLoader] Loaded ${products.length} products for ${categorySlug}`);

      // Cache the results
      this.cache.set(categorySlug, products);

      return products;
    } catch (error) {
      console.error(`[ProductLoader] Error loading products for ${categorySlug}:`, error);
      throw error;
    }
  }

  /**
   * Clear cache for a specific category or all categories
   *
   * @param {string|null} categorySlug - Category slug or null to clear all
   */
  clearCache(categorySlug = null) {
    if (categorySlug) {
      this.cache.delete(categorySlug);
      console.log(`[ProductLoader] Cache cleared for ${categorySlug}`);
    } else {
      this.cache.clear();
      console.log('[ProductLoader] All cache cleared');
    }
  }

  /**
   * Get cached data for a category
   *
   * @param {string} categorySlug - Category slug
   * @returns {Array|null} Cached products or null if not found
   */
  getCachedProducts(categorySlug) {
    return this.cache.get(categorySlug) || null;
  }

  /**
   * Check if products are cached for a category
   *
   * @param {string} categorySlug - Category slug
   * @returns {boolean} True if cached, false otherwise
   */
  isCached(categorySlug) {
    return this.cache.has(categorySlug);
  }
}
