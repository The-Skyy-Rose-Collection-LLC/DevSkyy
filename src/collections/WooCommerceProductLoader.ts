/**
 * WooCommerceProductLoader - Product Data Integration for SkyyRose Collections
 *
 * Fetches and caches product data from WooCommerce REST API for use in
 * 3D collection experiences and AR try-on.
 */

import type { ARProduct } from './ARTryOnViewer';

export interface WooCommerceProduct {
  id: number;
  name: string;
  slug: string;
  permalink: string;
  sku: string;
  price: string;
  regular_price: string;
  sale_price: string;
  description: string;
  short_description: string;
  categories: Array<{
    id: number;
    name: string;
    slug: string;
  }>;
  tags: Array<{
    id: number;
    name: string;
    slug: string;
  }>;
  images: Array<{
    id: number;
    src: string;
    alt: string;
  }>;
  attributes: Array<{
    id: number;
    name: string;
    options: string[];
  }>;
  variations: number[];
  stock_status: 'instock' | 'outofstock' | 'onbackorder';
  meta_data: Array<{
    id: number;
    key: string;
    value: string;
  }>;
}

export interface WooCommerceVariation {
  id: number;
  sku: string;
  price: string;
  image: {
    id: number;
    src: string;
    alt: string;
  };
  attributes: Array<{
    name: string;
    option: string;
  }>;
}

export interface ProductLoaderConfig {
  baseUrl: string;
  consumerKey?: string;
  consumerSecret?: string;
  cacheTimeout?: number; // ms
  collections?: string[];
}

interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

type CollectionSlug = 'black-rose' | 'love-hurts' | 'signature';

const GARMENT_CATEGORY_MAPPING: Record<string, ARProduct['category']> = {
  'hoodies': 'tops',
  'jackets': 'outerwear',
  'coats': 'outerwear',
  't-shirts': 'tops',
  'tees': 'tops',
  'shirts': 'tops',
  'pants': 'bottoms',
  'jeans': 'bottoms',
  'shorts': 'bottoms',
  'dresses': 'dresses',
  'rompers': 'full_body',
  'jumpsuits': 'full_body',
  'sets': 'full_body',
};

export class WooCommerceProductLoader {
  private config: ProductLoaderConfig;
  private productCache: Map<string, CacheEntry<WooCommerceProduct>> = new Map();
  private collectionCache: Map<string, CacheEntry<WooCommerceProduct[]>> = new Map();
  private variationCache: Map<number, CacheEntry<WooCommerceVariation[]>> = new Map();

  private readonly defaultCacheTimeout = 5 * 60 * 1000; // 5 minutes

  constructor(config: ProductLoaderConfig) {
    this.config = {
      cacheTimeout: this.defaultCacheTimeout,
      ...config,
    };
  }

  private buildApiUrl(endpoint: string, params?: Record<string, string>): string {
    const url = new URL(`${this.config.baseUrl}/wp-json/wc/v3/${endpoint}`);

    if (this.config.consumerKey && this.config.consumerSecret) {
      url.searchParams.set('consumer_key', this.config.consumerKey);
      url.searchParams.set('consumer_secret', this.config.consumerSecret);
    }

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.set(key, value);
      });
    }

    return url.toString();
  }

  private isCacheValid<T>(entry: CacheEntry<T> | undefined): boolean {
    if (!entry) return false;
    const cacheTimeout = this.config.cacheTimeout || this.defaultCacheTimeout;
    return Date.now() - entry.timestamp < cacheTimeout;
  }

  async fetchProduct(productId: number): Promise<WooCommerceProduct | null> {
    const cacheKey = `product_${productId}`;
    const cached = this.productCache.get(cacheKey);

    if (this.isCacheValid(cached)) {
      return cached!.data;
    }

    try {
      const response = await fetch(this.buildApiUrl(`products/${productId}`));

      if (!response.ok) {
        console.error(`[WooCommerceLoader] Failed to fetch product ${productId}:`, response.status);
        return null;
      }

      const product: WooCommerceProduct = await response.json();

      this.productCache.set(cacheKey, {
        data: product,
        timestamp: Date.now(),
      });

      return product;
    } catch (error) {
      console.error(`[WooCommerceLoader] Error fetching product ${productId}:`, error);
      return null;
    }
  }

  async fetchProductBySlug(slug: string): Promise<WooCommerceProduct | null> {
    const cacheKey = `product_slug_${slug}`;
    const cached = this.productCache.get(cacheKey);

    if (this.isCacheValid(cached)) {
      return cached!.data;
    }

    try {
      const response = await fetch(
        this.buildApiUrl('products', { slug, per_page: '1' })
      );

      if (!response.ok) {
        console.error(`[WooCommerceLoader] Failed to fetch product by slug ${slug}:`, response.status);
        return null;
      }

      const products: WooCommerceProduct[] = await response.json();

      const product = products[0];
      if (!product) {
        return null;
      }

      this.productCache.set(cacheKey, {
        data: product,
        timestamp: Date.now(),
      });

      return product;
    } catch (error) {
      console.error(`[WooCommerceLoader] Error fetching product by slug ${slug}:`, error);
      return null;
    }
  }

  async fetchCollectionProducts(
    collectionSlug: CollectionSlug,
    limit = 50
  ): Promise<WooCommerceProduct[]> {
    const cacheKey = `collection_${collectionSlug}`;
    const cached = this.collectionCache.get(cacheKey);

    if (this.isCacheValid(cached)) {
      return cached!.data;
    }

    try {
      // First, find the collection/category ID
      const categoriesResponse = await fetch(
        this.buildApiUrl('products/categories', {
          slug: collectionSlug,
          per_page: '1',
        })
      );

      if (!categoriesResponse.ok) {
        console.error(`[WooCommerceLoader] Failed to fetch category ${collectionSlug}`);
        return [];
      }

      const categories = await categoriesResponse.json();

      if (categories.length === 0) {
        // Try tag-based lookup
        return this.fetchCollectionByTag(collectionSlug, limit);
      }

      const categoryId = categories[0].id;

      // Fetch products in this category
      const productsResponse = await fetch(
        this.buildApiUrl('products', {
          category: categoryId.toString(),
          per_page: limit.toString(),
          status: 'publish',
        })
      );

      if (!productsResponse.ok) {
        console.error(`[WooCommerceLoader] Failed to fetch products for category ${categoryId}`);
        return [];
      }

      const products: WooCommerceProduct[] = await productsResponse.json();

      this.collectionCache.set(cacheKey, {
        data: products,
        timestamp: Date.now(),
      });

      return products;
    } catch (error) {
      console.error(`[WooCommerceLoader] Error fetching collection ${collectionSlug}:`, error);
      return [];
    }
  }

  private async fetchCollectionByTag(
    tagSlug: string,
    limit: number
  ): Promise<WooCommerceProduct[]> {
    try {
      const tagsResponse = await fetch(
        this.buildApiUrl('products/tags', {
          slug: tagSlug,
          per_page: '1',
        })
      );

      if (!tagsResponse.ok) {
        return [];
      }

      const tags = await tagsResponse.json();

      if (tags.length === 0) {
        return [];
      }

      const tagId = tags[0].id;

      const productsResponse = await fetch(
        this.buildApiUrl('products', {
          tag: tagId.toString(),
          per_page: limit.toString(),
          status: 'publish',
        })
      );

      if (!productsResponse.ok) {
        return [];
      }

      return productsResponse.json();
    } catch (error) {
      console.error(`[WooCommerceLoader] Error fetching by tag ${tagSlug}:`, error);
      return [];
    }
  }

  async fetchProductVariations(productId: number): Promise<WooCommerceVariation[]> {
    const cached = this.variationCache.get(productId);

    if (this.isCacheValid(cached)) {
      return cached!.data;
    }

    try {
      const response = await fetch(
        this.buildApiUrl(`products/${productId}/variations`, {
          per_page: '100',
        })
      );

      if (!response.ok) {
        console.error(`[WooCommerceLoader] Failed to fetch variations for ${productId}`);
        return [];
      }

      const variations: WooCommerceVariation[] = await response.json();

      this.variationCache.set(productId, {
        data: variations,
        timestamp: Date.now(),
      });

      return variations;
    } catch (error) {
      console.error(`[WooCommerceLoader] Error fetching variations:`, error);
      return [];
    }
  }

  convertToARProduct(product: WooCommerceProduct, collection: CollectionSlug): ARProduct {
    // Extract garment image (first image or meta-defined try-on image)
    const tryOnImageMeta = product.meta_data.find(m => m.key === '_tryon_garment_image');
    const garmentImageUrl = tryOnImageMeta?.value ||
      product.images[0]?.src ||
      '';

    // Determine category from product categories
    let category: ARProduct['category'] = 'tops';
    for (const cat of product.categories) {
      const slug = cat.slug.toLowerCase();
      if (GARMENT_CATEGORY_MAPPING[slug]) {
        category = GARMENT_CATEGORY_MAPPING[slug];
        break;
      }
    }

    // Map collection slug to ARProduct collection type
    const collectionType = collection.replace('-', '_') as ARProduct['collection'];

    return {
      id: product.id.toString(),
      name: product.name,
      sku: product.sku,
      price: parseFloat(product.price) || 0,
      garmentImageUrl,
      category,
      collection: collectionType,
    };
  }

  async getARProductsForCollection(
    collectionSlug: CollectionSlug
  ): Promise<ARProduct[]> {
    const products = await this.fetchCollectionProducts(collectionSlug);

    const arProducts: ARProduct[] = [];

    for (const product of products) {
      const arProduct = this.convertToARProduct(product, collectionSlug);

      // Fetch variations if available
      if (product.variations.length > 0) {
        const variations = await this.fetchProductVariations(product.id);
        arProduct.variants = variations.map(v => ({
          id: v.id.toString(),
          name: v.attributes.map(a => a.option).join(' / '),
          garmentImageUrl: v.image?.src || arProduct.garmentImageUrl,
        }));
      }

      arProducts.push(arProduct);
    }

    return arProducts;
  }

  getProductMetaValue(product: WooCommerceProduct, key: string): string | null {
    const meta = product.meta_data.find(m => m.key === key);
    return meta?.value || null;
  }

  get3DModelUrl(product: WooCommerceProduct): string | null {
    return this.getProductMetaValue(product, '_3d_model_url') ||
           this.getProductMetaValue(product, '_glb_model_path');
  }

  getHotspotPosition(product: WooCommerceProduct): { x: number; y: number; z: number } | null {
    const positionMeta = this.getProductMetaValue(product, '_hotspot_position');
    if (!positionMeta) return null;

    try {
      return JSON.parse(positionMeta);
    } catch {
      return null;
    }
  }

  clearCache(): void {
    this.productCache.clear();
    this.collectionCache.clear();
    this.variationCache.clear();
  }

  clearProductCache(productId: number): void {
    this.productCache.delete(`product_${productId}`);
    this.variationCache.delete(productId);
  }

  clearCollectionCache(collectionSlug: CollectionSlug): void {
    this.collectionCache.delete(`collection_${collectionSlug}`);
  }

  getCacheStats(): {
    products: number;
    collections: number;
    variations: number;
  } {
    return {
      products: this.productCache.size,
      collections: this.collectionCache.size,
      variations: this.variationCache.size,
    };
  }
}

// Singleton instance for shared usage
let loaderInstance: WooCommerceProductLoader | null = null;

export function getProductLoader(config?: ProductLoaderConfig): WooCommerceProductLoader {
  if (!loaderInstance && config) {
    loaderInstance = new WooCommerceProductLoader(config);
  }

  if (!loaderInstance) {
    throw new Error('[WooCommerceLoader] No instance configured. Call with config first.');
  }

  return loaderInstance;
}

export function initProductLoader(config: ProductLoaderConfig): WooCommerceProductLoader {
  loaderInstance = new WooCommerceProductLoader(config);
  return loaderInstance;
}

export default WooCommerceProductLoader;
