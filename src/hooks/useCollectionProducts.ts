/**
 * useCollectionProducts Hook
 *
 * Fetches products from WordPress/WooCommerce filtered by collection category.
 * Includes caching (5 min TTL), loading states, error handling, and retry logic.
 *
 * @hook
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import type { Product } from '../types/collections';

export interface UseCollectionProductsOptions {
  /** Collection category slug (e.g., 'black-rose', 'signature', 'love-hurts') */
  categorySlug: string;

  /** Number of products to fetch (default: 20) */
  perPage?: number;

  /** Enable automatic retry on failure (default: true) */
  enableRetry?: boolean;

  /** Maximum retry attempts (default: 3) */
  maxRetries?: number;

  /** Cache TTL in milliseconds (default: 300000 = 5 min) */
  cacheTTL?: number;
}

export interface UseCollectionProductsResult {
  /** Products array */
  products: Product[];

  /** Loading state */
  loading: boolean;

  /** Error message (null if no error) */
  error: string | null;

  /** Retry the fetch manually */
  retry: () => void;

  /** Refetch products (bypasses cache) */
  refetch: () => void;
}

interface CacheEntry {
  data: Product[];
  timestamp: number;
}

// In-memory cache (shared across hook instances)
const productCache = new Map<string, CacheEntry>();

/**
 * Fetch products from WordPress/WooCommerce API
 */
async function fetchProductsFromAPI(
  categorySlug: string,
  perPage: number
): Promise<Product[]> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // First, get category ID by slug
  const categoriesResponse = await fetch(
    `${apiUrl}/api/v1/wordpress/products/categories?per_page=100`
  );

  if (!categoriesResponse.ok) {
    throw new Error(`Failed to fetch categories: ${categoriesResponse.statusText}`);
  }

  const categories = await categoriesResponse.json();
  const category = categories.find(
    (cat: { slug: string; id: number }) => cat.slug === categorySlug
  );

  if (!category) {
    throw new Error(`Category not found: ${categorySlug}`);
  }

  // Fetch products filtered by category
  const productsResponse = await fetch(
    `${apiUrl}/api/v1/wordpress/products?category=${category.id}&per_page=${perPage}&status=publish`
  );

  if (!productsResponse.ok) {
    throw new Error(`Failed to fetch products: ${productsResponse.statusText}`);
  }

  const rawProducts = await productsResponse.json();

  // Transform to our Product interface
  return rawProducts.map((raw: any) => ({
    id: raw.id,
    name: raw.name,
    slug: raw.slug,
    price: raw.price,
    regularPrice: raw.regular_price,
    salePrice: raw.sale_price || undefined,
    description: raw.description,
    shortDescription: raw.short_description,
    images: raw.images.map((img: any) => ({
      id: img.id,
      src: img.src,
      alt: img.alt || raw.name,
      name: img.name || raw.name,
    })),
    categories: raw.categories.map((cat: any) => ({
      id: cat.id,
      name: cat.name,
      slug: cat.slug,
    })),
    tags: raw.tags?.map((tag: any) => ({
      id: tag.id,
      name: tag.name,
      slug: tag.slug,
    })) || [],
    attributes: raw.attributes?.map((attr: any) => ({
      id: attr.id,
      name: attr.name,
      options: attr.options,
    })) || [],
    inStock: raw.stock_status === 'instock',
    stockQuantity: raw.stock_quantity,
  }));
}

/**
 * Hook to fetch collection products with caching and retry logic
 */
export function useCollectionProducts(
  options: UseCollectionProductsOptions
): UseCollectionProductsResult {
  const {
    categorySlug,
    perPage = 20,
    enableRetry = true,
    maxRetries = 3,
    cacheTTL = 300000, // 5 min
  } = options;

  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const retryCount = useRef(0);
  const isMounted = useRef(true);

  const fetchProducts = useCallback(
    async (bypassCache = false) => {
      setLoading(true);
      setError(null);

      const cacheKey = `${categorySlug}-${perPage}`;

      // Check cache (unless bypassing)
      if (!bypassCache) {
        const cached = productCache.get(cacheKey);
        if (cached && Date.now() - cached.timestamp < cacheTTL) {
          setProducts(cached.data);
          setLoading(false);
          return;
        }
      }

      try {
        const fetchedProducts = await fetchProductsFromAPI(categorySlug, perPage);

        if (!isMounted.current) return;

        // Update cache
        productCache.set(cacheKey, {
          data: fetchedProducts,
          timestamp: Date.now(),
        });

        setProducts(fetchedProducts);
        setError(null);
        retryCount.current = 0;
      } catch (err) {
        if (!isMounted.current) return;

        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch products';
        setError(errorMessage);

        // Retry logic
        if (enableRetry && retryCount.current < maxRetries) {
          retryCount.current += 1;
          setTimeout(() => {
            if (isMounted.current) {
              fetchProducts(bypassCache);
            }
          }, 1000 * retryCount.current); // Exponential backoff
        }
      } finally {
        if (isMounted.current) {
          setLoading(false);
        }
      }
    },
    [categorySlug, perPage, enableRetry, maxRetries, cacheTTL]
  );

  const retry = useCallback(() => {
    retryCount.current = 0;
    fetchProducts(false);
  }, [fetchProducts]);

  const refetch = useCallback(() => {
    retryCount.current = 0;
    fetchProducts(true);
  }, [fetchProducts]);

  useEffect(() => {
    isMounted.current = true;
    fetchProducts(false);

    return () => {
      isMounted.current = false;
    };
  }, [fetchProducts]);

  return {
    products,
    loading,
    error,
    retry,
    refetch,
  };
}

export default useCollectionProducts;
