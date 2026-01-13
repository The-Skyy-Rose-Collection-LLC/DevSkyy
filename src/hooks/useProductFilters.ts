/**
 * Product Filtering and Sorting Hook
 *
 * Manages filter state with URL parameter synchronization for shareable filtered views.
 * Supports filtering by: size, color, price range
 * Supports sorting by: newest, price-low, price-high, popular
 *
 * @hook
 */

import { useCallback, useMemo, useState, useEffect } from 'react';
import type { Product } from '../types/collections';

export type SortOption = 'newest' | 'price-low' | 'price-high' | 'popular';

export interface ProductFilters {
  sizes: string[];
  colors: string[];
  priceRange: [number, number];
  sortBy: SortOption;
}

export interface UseProductFiltersResult {
  filters: ProductFilters;
  filteredProducts: Product[];
  availableFilters: {
    sizes: string[];
    colors: string[];
    priceRange: [number, number];
  };
  updateFilters: (updates: Partial<ProductFilters>) => void;
  clearFilters: () => void;
  hasActiveFilters: boolean;
}

const DEFAULT_FILTERS: ProductFilters = {
  sizes: [],
  colors: [],
  priceRange: [0, Infinity],
  sortBy: 'newest',
};

/**
 * Extract unique attribute values from products
 */
function extractAttributeValues(products: Product[], attributeName: string): string[] {
  const values = new Set<string>();

  products.forEach((product) => {
    const attr = product.attributes.find(
      (a) => a.name.toLowerCase() === attributeName.toLowerCase()
    );
    if (attr) {
      attr.options.forEach((option) => values.add(option));
    }
  });

  return Array.from(values).sort();
}

/**
 * Calculate price range from products
 */
function calculatePriceRange(products: Product[]): [number, number] {
  if (products.length === 0) return [0, 1000];

  const prices = products.map((p) => parseFloat(p.price) || 0);
  return [Math.floor(Math.min(...prices)), Math.ceil(Math.max(...prices))];
}

/**
 * Check if product matches filter criteria
 */
function matchesFilters(product: Product, filters: ProductFilters): boolean {
  // Price filter
  const price = parseFloat(product.price) || 0;
  if (price < filters.priceRange[0] || price > filters.priceRange[1]) {
    return false;
  }

  // Size filter
  if (filters.sizes.length > 0) {
    const sizeAttr = product.attributes.find(
      (a) => a.name.toLowerCase() === 'size'
    );
    if (!sizeAttr || !sizeAttr.options.some((opt) => filters.sizes.includes(opt))) {
      return false;
    }
  }

  // Color filter
  if (filters.colors.length > 0) {
    const colorAttr = product.attributes.find(
      (a) => a.name.toLowerCase() === 'color' || a.name.toLowerCase() === 'colour'
    );
    if (!colorAttr || !colorAttr.options.some((opt) => filters.colors.includes(opt))) {
      return false;
    }
  }

  return true;
}

/**
 * Sort products based on sort option
 */
function sortProducts(products: Product[], sortBy: SortOption): Product[] {
  const sorted = [...products];

  switch (sortBy) {
    case 'price-low':
      return sorted.sort((a, b) => {
        const priceA = parseFloat(a.price) || 0;
        const priceB = parseFloat(b.price) || 0;
        return priceA - priceB;
      });

    case 'price-high':
      return sorted.sort((a, b) => {
        const priceA = parseFloat(a.price) || 0;
        const priceB = parseFloat(b.price) || 0;
        return priceB - priceA;
      });

    case 'popular':
      // TODO: Implement based on sales data or view count
      // For now, sort by ID (assuming lower IDs are more established)
      return sorted.sort((a, b) => a.id - b.id);

    case 'newest':
    default:
      // Assuming higher IDs are newer products
      return sorted.sort((a, b) => b.id - a.id);
  }
}

/**
 * Parse URL search params into filters
 */
function parseFiltersFromURL(searchParams: URLSearchParams): Partial<ProductFilters> {
  const filters: Partial<ProductFilters> = {};

  const sizes = searchParams.get('sizes');
  if (sizes) {
    filters.sizes = sizes.split(',').filter(Boolean);
  }

  const colors = searchParams.get('colors');
  if (colors) {
    filters.colors = colors.split(',').filter(Boolean);
  }

  const priceMin = searchParams.get('priceMin');
  const priceMax = searchParams.get('priceMax');
  if (priceMin || priceMax) {
    filters.priceRange = [
      priceMin ? parseFloat(priceMin) : 0,
      priceMax ? parseFloat(priceMax) : Infinity,
    ];
  }

  const sortBy = searchParams.get('sortBy') as SortOption;
  if (sortBy && ['newest', 'price-low', 'price-high', 'popular'].includes(sortBy)) {
    filters.sortBy = sortBy;
  }

  return filters;
}

/**
 * Convert filters to URL search params
 */
function filtersToURLParams(filters: ProductFilters): URLSearchParams {
  const params = new URLSearchParams();

  if (filters.sizes.length > 0) {
    params.set('sizes', filters.sizes.join(','));
  }

  if (filters.colors.length > 0) {
    params.set('colors', filters.colors.join(','));
  }

  if (filters.priceRange[0] > 0 || filters.priceRange[1] < Infinity) {
    if (filters.priceRange[0] > 0) {
      params.set('priceMin', filters.priceRange[0].toString());
    }
    if (filters.priceRange[1] < Infinity) {
      params.set('priceMax', filters.priceRange[1].toString());
    }
  }

  if (filters.sortBy !== 'newest') {
    params.set('sortBy', filters.sortBy);
  }

  return params;
}

/**
 * Hook for managing product filters with URL synchronization
 */
export function useProductFilters(
  products: Product[],
  initialFilters?: Partial<ProductFilters>
): UseProductFiltersResult {
  const [filters, setFilters] = useState<ProductFilters>(() => ({
    ...DEFAULT_FILTERS,
    ...initialFilters,
  }));

  // Sync filters with URL (client-side only)
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const searchParams = new URLSearchParams(window.location.search);
    const urlFilters = parseFiltersFromURL(searchParams);

    if (Object.keys(urlFilters).length > 0) {
      setFilters((prev) => ({ ...prev, ...urlFilters }));
    }
  }, []);

  // Update URL when filters change
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const params = filtersToURLParams(filters);
    const newURL = params.toString()
      ? `${window.location.pathname}?${params.toString()}`
      : window.location.pathname;

    window.history.replaceState({}, '', newURL);
  }, [filters]);

  // Extract available filter options from all products
  const availableFilters = useMemo(() => {
    const sizes = extractAttributeValues(products, 'size');
    const colors = extractAttributeValues(products, 'color');
    const priceRange = calculatePriceRange(products);

    return { sizes, colors, priceRange };
  }, [products]);

  // Filter and sort products
  const filteredProducts = useMemo(() => {
    const filtered = products.filter((product) => matchesFilters(product, filters));
    return sortProducts(filtered, filters.sortBy);
  }, [products, filters]);

  const updateFilters = useCallback((updates: Partial<ProductFilters>) => {
    setFilters((prev) => ({ ...prev, ...updates }));
  }, []);

  const clearFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
  }, []);

  const hasActiveFilters = useMemo(() => {
    return (
      filters.sizes.length > 0 ||
      filters.colors.length > 0 ||
      filters.priceRange[0] > 0 ||
      filters.priceRange[1] < Infinity ||
      filters.sortBy !== 'newest'
    );
  }, [filters]);

  return {
    filters,
    filteredProducts,
    availableFilters,
    updateFilters,
    clearFilters,
    hasActiveFilters,
  };
}
