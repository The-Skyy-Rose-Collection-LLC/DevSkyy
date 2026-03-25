/**
 * Unit Tests for WooCommerceProductLoader
 * @jest-environment jsdom
 */

// Mock ARTryOnViewer to avoid Three.js dependencies
jest.mock('../ARTryOnViewer', () => ({}));

import { WooCommerceProductLoader, getProductLoader, initProductLoader } from '../WooCommerceProductLoader';

function makeProduct(overrides) {
  return {
    id: 1,
    name: 'Test Jacket',
    slug: 'test-jacket',
    permalink: 'https://skyyrose.co/product/test-jacket',
    sku: 'SKU-001',
    price: '199.99',
    regular_price: '249.99',
    sale_price: '199.99',
    description: 'A beautiful test jacket',
    short_description: 'Test jacket',
    categories: [{ id: 10, name: 'Jackets', slug: 'jackets' }],
    tags: [{ id: 20, name: 'new', slug: 'new' }],
    images: [{ id: 100, src: 'https://skyyrose.co/img/jacket.jpg', alt: 'Jacket' }],
    attributes: [{ id: 1, name: 'Size', options: ['S', 'M', 'L'] }],
    variations: [],
    stock_status: 'instock',
    meta_data: [],
    ...overrides,
  };
}

function mockFetchResponse(data, ok) {
  return {
    ok: ok !== false,
    status: ok !== false ? 200 : 404,
    json: jest.fn().mockResolvedValue(data),
  };
}

describe('WooCommerceProductLoader', () => {
  let loader;
  const defaultConfig = { baseUrl: 'https://skyyrose.co' };

  beforeEach(() => {
    jest.clearAllMocks();
    loader = new WooCommerceProductLoader(defaultConfig);
    global.fetch = jest.fn();
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    console.error.mockRestore();
    delete global.fetch;
  });

  describe('constructor', () => {
    it('should create with default cache timeout', () => {
      expect(loader).toBeDefined();
    });

    it('should accept custom config', () => {
      const custom = new WooCommerceProductLoader({
        baseUrl: 'https://example.com',
        consumerKey: 'ck_test',
        consumerSecret: 'cs_test',
        cacheTimeout: 60000,
      });
      expect(custom).toBeDefined();
    });
  });

  describe('buildApiUrl (via fetchProduct)', () => {
    it('should build URL with auth params when configured', async () => {
      const authedLoader = new WooCommerceProductLoader({
        baseUrl: 'https://skyyrose.co',
        consumerKey: 'ck_abc',
        consumerSecret: 'cs_xyz',
      });

      global.fetch = jest.fn().mockResolvedValue(mockFetchResponse(makeProduct()));

      await authedLoader.fetchProduct(1);

      const calledUrl = global.fetch.mock.calls[0][0];
      expect(calledUrl).toContain('consumer_key=ck_abc');
      expect(calledUrl).toContain('consumer_secret=cs_xyz');
    });

    it('should not include auth params when not configured', async () => {
      global.fetch = jest.fn().mockResolvedValue(mockFetchResponse(makeProduct()));

      await loader.fetchProduct(1);

      const calledUrl = global.fetch.mock.calls[0][0];
      expect(calledUrl).not.toContain('consumer_key');
    });
  });

  describe('fetchProduct', () => {
    it('should fetch and return product', async () => {
      const product = makeProduct();
      global.fetch = jest.fn().mockResolvedValue(mockFetchResponse(product));

      const result = await loader.fetchProduct(1);
      expect(result).toEqual(product);
    });

    it('should return cached product on second call', async () => {
      const product = makeProduct();
      global.fetch = jest.fn().mockResolvedValue(mockFetchResponse(product));

      await loader.fetchProduct(1);
      const result = await loader.fetchProduct(1);

      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(result).toEqual(product);
    });

    it('should return null on HTTP error', async () => {
      global.fetch = jest.fn().mockResolvedValue(mockFetchResponse(null, false));

      const result = await loader.fetchProduct(999);
      expect(result).toBeNull();
    });

    it('should return null on network error', async () => {
      global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));

      const result = await loader.fetchProduct(1);
      expect(result).toBeNull();
    });
  });

  describe('fetchProductBySlug', () => {
    it('should fetch product by slug', async () => {
      const product = makeProduct();
      global.fetch = jest.fn().mockResolvedValue(mockFetchResponse([product]));

      const result = await loader.fetchProductBySlug('test-jacket');
      expect(result).toEqual(product);
    });

    it('should return null when no product found', async () => {
      global.fetch = jest.fn().mockResolvedValue(mockFetchResponse([]));

      const result = await loader.fetchProductBySlug('nonexistent');
      expect(result).toBeNull();
    });

    it('should cache result', async () => {
      const product = makeProduct();
      global.fetch = jest.fn().mockResolvedValue(mockFetchResponse([product]));

      await loader.fetchProductBySlug('test-jacket');
      await loader.fetchProductBySlug('test-jacket');

      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    it('should return null on HTTP error', async () => {
      global.fetch = jest.fn().mockResolvedValue(mockFetchResponse(null, false));

      const result = await loader.fetchProductBySlug('bad');
      expect(result).toBeNull();
    });

    it('should return null on network error', async () => {
      global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));

      const result = await loader.fetchProductBySlug('bad');
      expect(result).toBeNull();
    });
  });

  describe('fetchCollectionProducts', () => {
    it('should fetch products by category', async () => {
      const products = [makeProduct()];
      global.fetch = jest.fn()
        .mockResolvedValueOnce(mockFetchResponse([{ id: 10, name: 'Black Rose', slug: 'black-rose' }]))
        .mockResolvedValueOnce(mockFetchResponse(products));

      const result = await loader.fetchCollectionProducts('black-rose');
      expect(result).toEqual(products);
    });

    it('should return cached collection on second call', async () => {
      const products = [makeProduct()];
      global.fetch = jest.fn()
        .mockResolvedValueOnce(mockFetchResponse([{ id: 10, name: 'Black Rose', slug: 'black-rose' }]))
        .mockResolvedValueOnce(mockFetchResponse(products));

      await loader.fetchCollectionProducts('black-rose');
      const result = await loader.fetchCollectionProducts('black-rose');

      expect(global.fetch).toHaveBeenCalledTimes(2); // only the first two calls
      expect(result).toEqual(products);
    });

    it('should fall back to tag-based lookup when no category found', async () => {
      const products = [makeProduct()];
      global.fetch = jest.fn()
        .mockResolvedValueOnce(mockFetchResponse([])) // no categories
        .mockResolvedValueOnce(mockFetchResponse([{ id: 5, name: 'black-rose', slug: 'black-rose' }])) // tag
        .mockResolvedValueOnce(mockFetchResponse(products)); // products by tag

      const result = await loader.fetchCollectionProducts('black-rose');
      expect(result).toEqual(products);
    });

    it('should return empty array on category fetch error', async () => {
      global.fetch = jest.fn().mockResolvedValue(mockFetchResponse(null, false));

      const result = await loader.fetchCollectionProducts('black-rose');
      expect(result).toEqual([]);
    });

    it('should return empty array on products fetch error', async () => {
      global.fetch = jest.fn()
        .mockResolvedValueOnce(mockFetchResponse([{ id: 10, slug: 'black-rose' }]))
        .mockResolvedValueOnce(mockFetchResponse(null, false));

      const result = await loader.fetchCollectionProducts('black-rose');
      expect(result).toEqual([]);
    });

    it('should return empty array on network error', async () => {
      global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));

      const result = await loader.fetchCollectionProducts('black-rose');
      expect(result).toEqual([]);
    });
  });

  describe('fetchProductVariations', () => {
    it('should fetch variations', async () => {
      const variations = [{ id: 1, sku: 'V1', price: '99', image: { id: 1, src: 'img.jpg', alt: '' }, attributes: [] }];
      global.fetch = jest.fn().mockResolvedValue(mockFetchResponse(variations));

      const result = await loader.fetchProductVariations(1);
      expect(result).toEqual(variations);
    });

    it('should cache variations', async () => {
      const variations = [{ id: 1, sku: 'V1', price: '99', image: { id: 1, src: 'img.jpg', alt: '' }, attributes: [] }];
      global.fetch = jest.fn().mockResolvedValue(mockFetchResponse(variations));

      await loader.fetchProductVariations(1);
      await loader.fetchProductVariations(1);

      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    it('should return empty on error', async () => {
      global.fetch = jest.fn().mockResolvedValue(mockFetchResponse(null, false));

      const result = await loader.fetchProductVariations(999);
      expect(result).toEqual([]);
    });

    it('should return empty on network error', async () => {
      global.fetch = jest.fn().mockRejectedValue(new Error('fail'));

      const result = await loader.fetchProductVariations(1);
      expect(result).toEqual([]);
    });
  });

  describe('convertToARProduct', () => {
    it('should convert basic product', () => {
      const product = makeProduct();
      const result = loader.convertToARProduct(product, 'black-rose');

      expect(result.id).toBe('1');
      expect(result.name).toBe('Test Jacket');
      expect(result.sku).toBe('SKU-001');
      expect(result.price).toBe(199.99);
      expect(result.collection).toBe('black_rose');
    });

    it('should map jacket category to outerwear', () => {
      const product = makeProduct({ categories: [{ id: 1, name: 'Jackets', slug: 'jackets' }] });
      const result = loader.convertToARProduct(product, 'black-rose');
      expect(result.category).toBe('outerwear');
    });

    it('should map pants category to bottoms', () => {
      const product = makeProduct({ categories: [{ id: 1, name: 'Pants', slug: 'pants' }] });
      const result = loader.convertToARProduct(product, 'signature');
      expect(result.category).toBe('bottoms');
    });

    it('should map dresses category', () => {
      const product = makeProduct({ categories: [{ id: 1, name: 'Dresses', slug: 'dresses' }] });
      const result = loader.convertToARProduct(product, 'love-hurts');
      expect(result.category).toBe('dresses');
    });

    it('should default to tops for unknown category', () => {
      const product = makeProduct({ categories: [{ id: 1, name: 'Misc', slug: 'misc' }] });
      const result = loader.convertToARProduct(product, 'black-rose');
      expect(result.category).toBe('tops');
    });

    it('should use tryon meta image when available', () => {
      const product = makeProduct({
        meta_data: [{ id: 1, key: '_tryon_garment_image', value: 'https://cdn/tryon.jpg' }],
      });
      const result = loader.convertToARProduct(product, 'black-rose');
      expect(result.garmentImageUrl).toBe('https://cdn/tryon.jpg');
    });

    it('should fall back to first product image', () => {
      const product = makeProduct();
      const result = loader.convertToARProduct(product, 'black-rose');
      expect(result.garmentImageUrl).toBe('https://skyyrose.co/img/jacket.jpg');
    });

    it('should handle product with no images', () => {
      const product = makeProduct({ images: [], meta_data: [] });
      const result = loader.convertToARProduct(product, 'black-rose');
      expect(result.garmentImageUrl).toBe('');
    });

    it('should handle non-numeric price', () => {
      const product = makeProduct({ price: 'free' });
      const result = loader.convertToARProduct(product, 'black-rose');
      expect(result.price).toBe(0);
    });
  });

  describe('getProductMetaValue', () => {
    it('should return meta value for matching key', () => {
      const product = makeProduct({
        meta_data: [{ id: 1, key: '_custom_key', value: 'custom_value' }],
      });
      expect(loader.getProductMetaValue(product, '_custom_key')).toBe('custom_value');
    });

    it('should return null for missing key', () => {
      const product = makeProduct({ meta_data: [] });
      expect(loader.getProductMetaValue(product, '_missing')).toBeNull();
    });
  });

  describe('get3DModelUrl', () => {
    it('should return _3d_model_url when available', () => {
      const product = makeProduct({
        meta_data: [{ id: 1, key: '_3d_model_url', value: '/models/jacket.glb' }],
      });
      expect(loader.get3DModelUrl(product)).toBe('/models/jacket.glb');
    });

    it('should fall back to _glb_model_path', () => {
      const product = makeProduct({
        meta_data: [{ id: 1, key: '_glb_model_path', value: '/glb/jacket.glb' }],
      });
      expect(loader.get3DModelUrl(product)).toBe('/glb/jacket.glb');
    });

    it('should return null when no model meta', () => {
      const product = makeProduct({ meta_data: [] });
      expect(loader.get3DModelUrl(product)).toBeNull();
    });
  });

  describe('getHotspotPosition', () => {
    it('should parse valid JSON position', () => {
      const product = makeProduct({
        meta_data: [{ id: 1, key: '_hotspot_position', value: '{"x":1,"y":2,"z":3}' }],
      });
      expect(loader.getHotspotPosition(product)).toEqual({ x: 1, y: 2, z: 3 });
    });

    it('should return null for invalid JSON', () => {
      const product = makeProduct({
        meta_data: [{ id: 1, key: '_hotspot_position', value: 'bad json' }],
      });
      expect(loader.getHotspotPosition(product)).toBeNull();
    });

    it('should return null when no position meta', () => {
      const product = makeProduct({ meta_data: [] });
      expect(loader.getHotspotPosition(product)).toBeNull();
    });
  });

  describe('cache management', () => {
    it('clearCache should clear all caches', async () => {
      const product = makeProduct();
      global.fetch = jest.fn().mockResolvedValue(mockFetchResponse(product));

      await loader.fetchProduct(1);
      expect(loader.getCacheStats().products).toBe(1);

      loader.clearCache();
      expect(loader.getCacheStats()).toEqual({ products: 0, collections: 0, variations: 0 });
    });

    it('clearProductCache should clear specific product', async () => {
      global.fetch = jest.fn().mockResolvedValue(mockFetchResponse(makeProduct()));

      await loader.fetchProduct(1);
      expect(loader.getCacheStats().products).toBe(1);

      loader.clearProductCache(1);
      expect(loader.getCacheStats().products).toBe(0);
    });

    it('clearCollectionCache should clear specific collection', async () => {
      const products = [makeProduct()];
      global.fetch = jest.fn()
        .mockResolvedValueOnce(mockFetchResponse([{ id: 10, slug: 'black-rose' }]))
        .mockResolvedValueOnce(mockFetchResponse(products));

      await loader.fetchCollectionProducts('black-rose');
      expect(loader.getCacheStats().collections).toBe(1);

      loader.clearCollectionCache('black-rose');
      expect(loader.getCacheStats().collections).toBe(0);
    });

    it('getCacheStats should return counts', () => {
      expect(loader.getCacheStats()).toEqual({ products: 0, collections: 0, variations: 0 });
    });
  });
});

describe('getProductLoader', () => {
  beforeEach(() => {
    jest.resetModules();
  });

  it('should create instance with config', () => {
    const mod = require('../WooCommerceProductLoader');
    const instance = mod.initProductLoader({ baseUrl: 'https://example.com' });
    expect(instance).toBeDefined();
  });

  it('should return same instance on subsequent calls', () => {
    const mod = require('../WooCommerceProductLoader');
    const first = mod.initProductLoader({ baseUrl: 'https://example.com' });
    const second = mod.getProductLoader();
    expect(second).toBe(first);
  });

  it('should throw when no instance configured', () => {
    const mod = require('../WooCommerceProductLoader');
    expect(() => mod.getProductLoader()).toThrow('No instance configured');
  });
});
