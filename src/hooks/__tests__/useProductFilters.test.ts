/**
 * Unit Tests for useProductFilters
 * @jest-environment jsdom
 */

import { renderHook, act } from '@testing-library/react';
import { useProductFilters, ProductFilters } from '../useProductFilters';
import { Product } from '../../types/collections';

function createProduct(overrides: Partial<Product> = {}): Product {
  return {
    id: 1,
    name: 'Test Product',
    slug: 'test-product',
    price: '99.99',
    regularPrice: '99.99',
    description: 'Desc',
    shortDescription: 'Short',
    images: [],
    categories: [],
    tags: [],
    attributes: [],
    inStock: true,
    ...overrides,
  };
}

const sampleProducts: Product[] = [
  createProduct({
    id: 1, name: 'Shirt A', price: '50', attributes: [
      { id: 1, name: 'Size', options: ['S', 'M', 'L'] },
      { id: 2, name: 'Color', options: ['Red', 'Blue'] },
    ],
  }),
  createProduct({
    id: 2, name: 'Shirt B', price: '100', attributes: [
      { id: 1, name: 'Size', options: ['M', 'L', 'XL'] },
      { id: 2, name: 'Color', options: ['Black'] },
    ],
  }),
  createProduct({
    id: 3, name: 'Shirt C', price: '75', attributes: [
      { id: 1, name: 'Size', options: ['S'] },
      { id: 2, name: 'Color', options: ['Red'] },
    ],
  }),
];

describe('useProductFilters', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/');
  });

  it('should return all products with default filters', () => {
    const { result } = renderHook(() => useProductFilters(sampleProducts));
    expect(result.current.filteredProducts).toHaveLength(3);
  });

  it('should extract available sizes', () => {
    const { result } = renderHook(() => useProductFilters(sampleProducts));
    expect(result.current.availableFilters.sizes).toEqual(['L', 'M', 'S', 'XL']);
  });

  it('should extract available colors', () => {
    const { result } = renderHook(() => useProductFilters(sampleProducts));
    expect(result.current.availableFilters.colors).toEqual(['Black', 'Blue', 'Red']);
  });

  it('should calculate price range', () => {
    const { result } = renderHook(() => useProductFilters(sampleProducts));
    expect(result.current.availableFilters.priceRange).toEqual([50, 100]);
  });

  it('should filter by size', () => {
    const { result } = renderHook(() => useProductFilters(sampleProducts));

    act(() => {
      result.current.updateFilters({ sizes: ['XL'] });
    });

    expect(result.current.filteredProducts).toHaveLength(1);
    expect(result.current.filteredProducts[0]!.name).toBe('Shirt B');
  });

  it('should filter by color', () => {
    const { result } = renderHook(() => useProductFilters(sampleProducts));

    act(() => {
      result.current.updateFilters({ colors: ['Red'] });
    });

    expect(result.current.filteredProducts).toHaveLength(2);
  });

  it('should filter by price range', () => {
    const { result } = renderHook(() => useProductFilters(sampleProducts));

    act(() => {
      result.current.updateFilters({ priceRange: [60, 90] });
    });

    expect(result.current.filteredProducts).toHaveLength(1);
    expect(result.current.filteredProducts[0]!.name).toBe('Shirt C');
  });

  it('should sort by price low to high', () => {
    const { result } = renderHook(() => useProductFilters(sampleProducts));

    act(() => {
      result.current.updateFilters({ sortBy: 'price-low' });
    });

    expect(result.current.filteredProducts[0]!.price).toBe('50');
    expect(result.current.filteredProducts[2]!.price).toBe('100');
  });

  it('should sort by price high to low', () => {
    const { result } = renderHook(() => useProductFilters(sampleProducts));

    act(() => {
      result.current.updateFilters({ sortBy: 'price-high' });
    });

    expect(result.current.filteredProducts[0]!.price).toBe('100');
  });

  it('should sort by popular (id asc)', () => {
    const { result } = renderHook(() => useProductFilters(sampleProducts));

    act(() => {
      result.current.updateFilters({ sortBy: 'popular' });
    });

    expect(result.current.filteredProducts[0]!.id).toBe(1);
  });

  it('should sort by newest (id desc) by default', () => {
    const { result } = renderHook(() => useProductFilters(sampleProducts));
    expect(result.current.filteredProducts[0]!.id).toBe(3);
  });

  it('should report hasActiveFilters', () => {
    const { result } = renderHook(() => useProductFilters(sampleProducts));
    expect(result.current.hasActiveFilters).toBe(false);

    act(() => {
      result.current.updateFilters({ sizes: ['S'] });
    });

    expect(result.current.hasActiveFilters).toBe(true);
  });

  it('should clear filters', () => {
    const { result } = renderHook(() => useProductFilters(sampleProducts));

    act(() => {
      result.current.updateFilters({ sizes: ['S'], colors: ['Red'] });
    });

    expect(result.current.hasActiveFilters).toBe(true);

    act(() => {
      result.current.clearFilters();
    });

    expect(result.current.hasActiveFilters).toBe(false);
    expect(result.current.filteredProducts).toHaveLength(3);
  });

  it('should accept initial filters', () => {
    const { result } = renderHook(() =>
      useProductFilters(sampleProducts, { sortBy: 'price-low' })
    );

    expect(result.current.filters.sortBy).toBe('price-low');
  });

  it('should handle empty products', () => {
    const { result } = renderHook(() => useProductFilters([]));
    expect(result.current.filteredProducts).toHaveLength(0);
    expect(result.current.availableFilters.priceRange).toEqual([0, 1000]);
  });
});
