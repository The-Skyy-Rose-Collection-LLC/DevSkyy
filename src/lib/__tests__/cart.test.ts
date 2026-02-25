/**
 * Unit Tests for CartManager
 * @jest-environment jsdom
 */

import { CartManager, CartItem } from '../cart';

// Mock Logger
jest.mock('../../utils/Logger', () => ({
  Logger: jest.fn().mockImplementation(() => ({
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    debug: jest.fn(),
  })),
}));

function createItem(overrides: Partial<CartItem> = {}): CartItem {
  return {
    productId: 'prod-1',
    sku: 'SKU-001',
    name: 'Test Product',
    price: 99.99,
    quantity: 1,
    ...overrides,
  };
}

describe('CartManager', () => {
  beforeEach(() => {
    CartManager.resetInstance();
    localStorage.clear();
  });

  describe('singleton', () => {
    it('should return same instance', () => {
      const a = CartManager.getInstance();
      const b = CartManager.getInstance();
      expect(a).toBe(b);
    });

    it('should reset instance', () => {
      const a = CartManager.getInstance();
      CartManager.resetInstance();
      const b = CartManager.getInstance();
      expect(a).not.toBe(b);
    });
  });

  describe('addItem', () => {
    it('should add a new item', () => {
      const cart = CartManager.getInstance();
      cart.addItem(createItem());
      expect(cart.getItems()).toHaveLength(1);
      expect(cart.getItems()[0]!.name).toBe('Test Product');
    });

    it('should increment quantity for existing item', () => {
      const cart = CartManager.getInstance();
      cart.addItem(createItem({ quantity: 1 }));
      cart.addItem(createItem({ quantity: 2 }));
      expect(cart.getItems()).toHaveLength(1);
      expect(cart.getItems()[0]!.quantity).toBe(3);
    });

    it('should treat different sizes as different items', () => {
      const cart = CartManager.getInstance();
      cart.addItem(createItem({ size: 'S' }));
      cart.addItem(createItem({ size: 'L' }));
      expect(cart.getItems()).toHaveLength(2);
    });

    it('should treat different colors as different items', () => {
      const cart = CartManager.getInstance();
      cart.addItem(createItem({ color: 'Red' }));
      cart.addItem(createItem({ color: 'Blue' }));
      expect(cart.getItems()).toHaveLength(2);
    });

    it('should throw for missing required fields', () => {
      const cart = CartManager.getInstance();
      expect(() => cart.addItem(createItem({ productId: '' }))).toThrow('Invalid cart item');
    });

    it('should throw for negative price', () => {
      const cart = CartManager.getInstance();
      expect(() => cart.addItem(createItem({ price: -1 }))).toThrow('Invalid cart item');
    });

    it('should throw for zero quantity', () => {
      const cart = CartManager.getInstance();
      expect(() => cart.addItem(createItem({ quantity: 0 }))).toThrow('quantity must be greater than 0');
    });

    it('should save to localStorage', () => {
      const cart = CartManager.getInstance();
      cart.addItem(createItem());
      const stored = JSON.parse(localStorage.getItem('skyyrose_cart')!);
      expect(stored.items).toHaveLength(1);
    });
  });

  describe('removeItem', () => {
    it('should remove item by productId', () => {
      const cart = CartManager.getInstance();
      cart.addItem(createItem());
      cart.removeItem('prod-1');
      expect(cart.getItems()).toHaveLength(0);
    });

    it('should remove item matching size and color', () => {
      const cart = CartManager.getInstance();
      cart.addItem(createItem({ size: 'S', color: 'Red' }));
      cart.addItem(createItem({ size: 'L', color: 'Blue' }));
      cart.removeItem('prod-1', 'S', 'Red');
      expect(cart.getItems()).toHaveLength(1);
      expect(cart.getItems()[0]!.size).toBe('L');
    });

    it('should handle non-existent item gracefully', () => {
      const cart = CartManager.getInstance();
      expect(() => cart.removeItem('nonexistent')).not.toThrow();
    });
  });

  describe('updateQuantity', () => {
    it('should update quantity', () => {
      const cart = CartManager.getInstance();
      cart.addItem(createItem());
      cart.updateQuantity('prod-1', 5);
      expect(cart.getItems()[0]!.quantity).toBe(5);
    });

    it('should remove item when quantity is 0', () => {
      const cart = CartManager.getInstance();
      cart.addItem(createItem());
      cart.updateQuantity('prod-1', 0);
      expect(cart.getItems()).toHaveLength(0);
    });

    it('should throw for negative quantity', () => {
      const cart = CartManager.getInstance();
      cart.addItem(createItem());
      expect(() => cart.updateQuantity('prod-1', -1)).toThrow('cannot be negative');
    });

    it('should handle non-existent item', () => {
      const cart = CartManager.getInstance();
      expect(() => cart.updateQuantity('nonexistent', 5)).not.toThrow();
    });
  });

  describe('clearCart', () => {
    it('should clear all items', () => {
      const cart = CartManager.getInstance();
      cart.addItem(createItem({ productId: 'p1' }));
      cart.addItem(createItem({ productId: 'p2', sku: 'SKU-2', name: 'P2' }));
      cart.clearCart();
      expect(cart.getItems()).toHaveLength(0);
    });
  });

  describe('getState', () => {
    it('should calculate subtotal correctly', () => {
      const cart = CartManager.getInstance();
      cart.addItem(createItem({ price: 100, quantity: 2 }));
      const state = cart.getState();
      expect(state.subtotal).toBe(200);
    });

    it('should use salePrice when available', () => {
      const cart = CartManager.getInstance();
      cart.addItem(createItem({ price: 100, salePrice: 75, quantity: 1 }));
      const state = cart.getState();
      expect(state.subtotal).toBe(75);
    });

    it('should calculate tax at 8%', () => {
      const cart = CartManager.getInstance();
      cart.addItem(createItem({ price: 100, quantity: 1 }));
      const state = cart.getState();
      expect(state.tax).toBeCloseTo(8);
    });

    it('should calculate total = subtotal + tax', () => {
      const cart = CartManager.getInstance();
      cart.addItem(createItem({ price: 100, quantity: 1 }));
      const state = cart.getState();
      expect(state.total).toBeCloseTo(108);
    });

    it('should count total items', () => {
      const cart = CartManager.getInstance();
      cart.addItem(createItem({ productId: 'p1', quantity: 3 }));
      cart.addItem(createItem({ productId: 'p2', sku: 'SKU-2', name: 'P2', quantity: 2 }));
      expect(cart.getState().itemCount).toBe(5);
    });

    it('should include currency', () => {
      const cart = CartManager.getInstance();
      expect(cart.getState().currency).toBe('USD');
    });
  });

  describe('subscribe', () => {
    it('should call subscriber immediately with current state', () => {
      const cart = CartManager.getInstance();
      const cb = jest.fn();
      cart.subscribe(cb);
      expect(cb).toHaveBeenCalledWith(expect.objectContaining({ items: [] }));
    });

    it('should notify on addItem', () => {
      const cart = CartManager.getInstance();
      const cb = jest.fn();
      cart.subscribe(cb);
      cb.mockClear();
      cart.addItem(createItem());
      expect(cb).toHaveBeenCalledTimes(1);
    });

    it('should unsubscribe', () => {
      const cart = CartManager.getInstance();
      const cb = jest.fn();
      const unsub = cart.subscribe(cb);
      cb.mockClear();
      unsub();
      cart.addItem(createItem());
      expect(cb).not.toHaveBeenCalled();
    });

    it('should handle subscriber errors gracefully', () => {
      const cart = CartManager.getInstance();
      // First call (immediate) succeeds, second call (from addItem) throws
      let callCount = 0;
      const badCb = jest.fn().mockImplementation(() => {
        callCount++;
        if (callCount > 1) throw new Error('bad');
      });
      cart.subscribe(badCb);
      expect(() => cart.addItem(createItem())).not.toThrow();
    });
  });

  describe('localStorage', () => {
    it('should load from localStorage on init', () => {
      const data = { items: [createItem()], timestamp: new Date().toISOString() };
      localStorage.setItem('skyyrose_cart', JSON.stringify(data));
      const cart = CartManager.getInstance();
      expect(cart.getItems()).toHaveLength(1);
    });

    it('should handle corrupt localStorage data', () => {
      localStorage.setItem('skyyrose_cart', 'not json');
      const cart = CartManager.getInstance();
      expect(cart.getItems()).toHaveLength(0);
    });
  });

  describe('syncWithWooCommerce', () => {
    it('should skip when no URL configured', async () => {
      const cart = CartManager.getInstance();
      await expect(cart.syncWithWooCommerce()).resolves.not.toThrow();
    });

    it('should make API request when URL configured', async () => {
      CartManager.resetInstance();
      const mockResponse = { ok: true, json: jest.fn().mockResolvedValue({}) };
      global.fetch = jest.fn().mockResolvedValue(mockResponse);

      const cart = CartManager.getInstance({ wooCommerceUrl: 'https://shop.test' });
      cart.addItem(createItem());
      await cart.syncWithWooCommerce();

      expect(global.fetch).toHaveBeenCalledWith(
        'https://shop.test/wp-json/wc/store/v1/cart',
        expect.any(Object)
      );
    });

    it('should throw on failed sync', async () => {
      CartManager.resetInstance();
      global.fetch = jest.fn().mockResolvedValue({ ok: false, statusText: 'Server Error' });

      const cart = CartManager.getInstance({ wooCommerceUrl: 'https://shop.test' });
      await expect(cart.syncWithWooCommerce()).rejects.toThrow('sync failed');
    });
  });

  describe('config', () => {
    it('should return config copy', () => {
      const cart = CartManager.getInstance();
      const config = cart.getConfig();
      expect(config.currency).toBe('USD');
      expect(config.taxRate).toBe(0.08);
    });

    it('should update config', () => {
      const cart = CartManager.getInstance();
      cart.updateConfig({ currency: 'EUR' });
      expect(cart.getConfig().currency).toBe('EUR');
    });
  });

  describe('getItem / hasItem', () => {
    it('should find item by id', () => {
      const cart = CartManager.getInstance();
      cart.addItem(createItem());
      expect(cart.getItem('prod-1')).toBeDefined();
      expect(cart.hasItem('prod-1')).toBe(true);
    });

    it('should return undefined for missing item', () => {
      const cart = CartManager.getInstance();
      expect(cart.getItem('nope')).toBeUndefined();
      expect(cart.hasItem('nope')).toBe(false);
    });
  });

  describe('getItemCount', () => {
    it('should sum quantities', () => {
      const cart = CartManager.getInstance();
      cart.addItem(createItem({ quantity: 3 }));
      expect(cart.getItemCount()).toBe(3);
    });
  });
});
