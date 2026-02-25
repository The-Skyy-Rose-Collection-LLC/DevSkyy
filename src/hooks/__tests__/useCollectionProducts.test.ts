/**
 * Unit Tests for useCollectionProducts
 * @jest-environment jsdom
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useCollectionProducts } from '../useCollectionProducts';

const mockCategories = [
  { id: 1, slug: 'black-rose', name: 'Black Rose' },
  { id: 2, slug: 'signature', name: 'Signature' },
];

const mockRawProducts = [
  {
    id: 100,
    name: 'Test Jacket',
    slug: 'test-jacket',
    price: '199.99',
    regular_price: '199.99',
    sale_price: '',
    description: 'A test jacket',
    short_description: 'Test',
    images: [{ id: 1, src: 'img.jpg', alt: 'jacket', name: 'jacket' }],
    categories: [{ id: 1, name: 'Black Rose', slug: 'black-rose' }],
    tags: [{ id: 1, name: 'new', slug: 'new' }],
    attributes: [{ id: 1, name: 'Size', options: ['S', 'M'] }],
    stock_status: 'instock',
    stock_quantity: 10,
  },
];

describe('useCollectionProducts', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    // Clear module-level cache between tests by clearing the fetch mock
    jest.clearAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('should fetch and transform products', async () => {
    global.fetch = jest.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockCategories),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockRawProducts),
      });

    const { result } = renderHook(() =>
      useCollectionProducts({ categorySlug: 'black-rose', enableRetry: false })
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.products).toHaveLength(1);
    expect(result.current.products[0].name).toBe('Test Jacket');
    expect(result.current.products[0].inStock).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it('should handle category not found', async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue([]),
    });

    const { result } = renderHook(() =>
      useCollectionProducts({ categorySlug: 'nonexistent', enableRetry: false })
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toContain('Category not found');
  });

  it('should handle API failure', async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: false,
      statusText: 'Internal Server Error',
    });

    const { result } = renderHook(() =>
      useCollectionProducts({ categorySlug: 'api-failure-test', enableRetry: false })
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toContain('Failed to fetch categories');
  });

  it('should handle network error', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() =>
      useCollectionProducts({ categorySlug: 'network-error-test', enableRetry: false })
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('Network error');
  });

  it('should start in loading state', () => {
    global.fetch = jest.fn().mockReturnValue(new Promise(() => {})); // never resolves

    const { result } = renderHook(() =>
      useCollectionProducts({ categorySlug: 'loading-test' })
    );

    expect(result.current.loading).toBe(true);
  });
});
