/**
 * Unit Tests for CartManager (cartManager.ts)
 * @jest-environment jsdom
 */

import { CartManager, getCartManager } from '../cartManager';

// Mock Logger
jest.mock('../../utils/Logger', () => ({
  Logger: jest.fn().mockImplementation(() => ({
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    debug: jest.fn(),
  })),
}));

/**
 * Factory for a minimal ShowroomProduct-shaped object.
 * No TypeScript type annotations per project rules.
 */
function createProduct(overrides = {}) {
  return {
    id: 'prod-1',
    name: 'Rose Gold Necklace',
    modelUrl: '/models/necklace.glb',
    position: [0, 0, 0],
    sku: 'SKU-RGN-001',
    price: 250,
    stockStatus: 'in_stock',
    stockQuantity: 10,
    sizes: ['S', 'M', 'L'],
    colors: [{ name: 'Rose Gold', hex: '#B76E79' }],
    images: ['https://cdn.skyyrose.co/necklace-1.jpg'],
    ...overrides,
  };
}

/**
 * Reset the singleton between tests so getCartManager() is clean.
 */
function resetSingleton() {
  // The module-level `cartManagerInstance` is not exported directly,
  // so we re-require the module to reset it. Instead, we just clear
  // localStorage and rely on creating fresh CartManager instances.
  // For the singleton tests we use a workaround below.
}

describe('CartManager', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.restoreAllMocks();
  });

  // ----------------------------------------------------------------
  // Constructor & Configuration
  // ----------------------------------------------------------------
  describe('constructor and config', () => {
    it('should initialize with default configuration', () => {
      const cart = new CartManager();
      const config = cart.getConfig();
      expect(config.storageKey).toBe('skyyrose_cart');
      expect(config.taxRate).toBe(0.08);
      expect(config.shippingCost).toBe(0);
      expect(config.currency).toBe('USD');
    });

    it('should accept custom configuration', () => {
      const cart = new CartManager({
        storageKey: 'custom_cart',
        taxRate: 0.10,
        shippingCost: 15,
        currency: 'EUR',
      });
      const config = cart.getConfig();
      expect(config.storageKey).toBe('custom_cart');
      expect(config.taxRate).toBe(0.10);
      expect(config.shippingCost).toBe(15);
      expect(config.currency).toBe('EUR');
    });

    it('should merge partial config with defaults', () => {
      const cart = new CartManager({ currency: 'GBP' });
      const config = cart.getConfig();
      expect(config.currency).toBe('GBP');
      expect(config.taxRate).toBe(0.08);
    });

    it('should return a copy from getConfig, not the internal object', () => {
      const cart = new CartManager();
      const config1 = cart.getConfig();
      const config2 = cart.getConfig();
      expect(config1).toEqual(config2);
      expect(config1).not.toBe(config2);
    });
  });

  // ----------------------------------------------------------------
  // addItem
  // ----------------------------------------------------------------
  describe('addItem', () => {
    it('should add a new item to an empty cart', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct(), 1);
      expect(cart.getItems()).toHaveLength(1);
      expect(cart.getItems()[0].name).toBe('Rose Gold Necklace');
    });

    it('should use salePrice when available', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct({ salePrice: 199 }), 1);
      expect(cart.getItems()[0].price).toBe(199);
    });

    it('should use regular price when salePrice is undefined', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct({ salePrice: undefined }), 1);
      expect(cart.getItems()[0].price).toBe(250);
    });

    it('should use regular price when salePrice is 0 (falsy)', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct({ salePrice: 0 }), 1);
      // salePrice: 0 is falsy, so `product.salePrice || product.price` => 250
      expect(cart.getItems()[0].price).toBe(250);
    });

    it('should store first image as imageUrl', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct(), 1);
      expect(cart.getItems()[0].imageUrl).toBe('https://cdn.skyyrose.co/necklace-1.jpg');
    });

    it('should handle product with no images', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct({ images: undefined }), 1);
      expect(cart.getItems()[0].imageUrl).toBeUndefined();
    });

    it('should handle product with empty images array', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct({ images: [] }), 1);
      expect(cart.getItems()[0].imageUrl).toBeUndefined();
    });

    it('should throw when quantity is 0', async () => {
      const cart = new CartManager();
      await expect(cart.addItem(createProduct(), 0)).rejects.toThrow(
        'Quantity must be greater than 0'
      );
    });

    it('should throw when quantity is negative', async () => {
      const cart = new CartManager();
      await expect(cart.addItem(createProduct(), -5)).rejects.toThrow(
        'Quantity must be greater than 0'
      );
    });

    it('should increment quantity for existing item with same product/size/color', async () => {
      const cart = new CartManager();
      const product = createProduct();
      const options = { size: 'M', color: { name: 'Rose Gold', hex: '#B76E79' } };
      await cart.addItem(product, 2, options);
      await cart.addItem(product, 3, options);
      expect(cart.getItems()).toHaveLength(1);
      expect(cart.getItems()[0].quantity).toBe(5);
    });

    it('should treat different sizes as separate items', async () => {
      const cart = new CartManager();
      const product = createProduct();
      await cart.addItem(product, 1, { size: 'S' });
      await cart.addItem(product, 1, { size: 'L' });
      expect(cart.getItems()).toHaveLength(2);
    });

    it('should treat different colors as separate items', async () => {
      const cart = new CartManager();
      const product = createProduct();
      await cart.addItem(product, 1, { color: { name: 'Rose Gold', hex: '#B76E79' } });
      await cart.addItem(product, 1, { color: { name: 'Black', hex: '#000000' } });
      expect(cart.getItems()).toHaveLength(2);
    });

    it('should treat undefined options as a distinct variant from specified options', async () => {
      const cart = new CartManager();
      const product = createProduct();
      await cart.addItem(product, 1);
      await cart.addItem(product, 1, { size: 'M' });
      expect(cart.getItems()).toHaveLength(2);
    });

    it('should persist to localStorage after adding', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct(), 1);
      const stored = JSON.parse(localStorage.getItem('skyyrose_cart'));
      expect(stored.items).toHaveLength(1);
      expect(stored.timestamp).toBeDefined();
    });
  });

  // ----------------------------------------------------------------
  // removeItem
  // ----------------------------------------------------------------
  describe('removeItem', () => {
    it('should remove an item by productId', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct(), 1);
      cart.removeItem('prod-1');
      expect(cart.getItems()).toHaveLength(0);
    });

    it('should remove matching size and color variant only', async () => {
      const cart = new CartManager();
      const product = createProduct();
      await cart.addItem(product, 1, { size: 'S', color: { name: 'Rose Gold', hex: '#B76E79' } });
      await cart.addItem(product, 1, { size: 'L', color: { name: 'Black', hex: '#000000' } });
      cart.removeItem('prod-1', 'S', 'Rose Gold');
      expect(cart.getItems()).toHaveLength(1);
      expect(cart.getItems()[0].size).toBe('L');
    });

    it('should do nothing when productId does not exist', () => {
      const cart = new CartManager();
      expect(() => cart.removeItem('nonexistent')).not.toThrow();
      expect(cart.getItems()).toHaveLength(0);
    });

    it('should do nothing when size does not match', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct(), 1, { size: 'M' });
      cart.removeItem('prod-1', 'XL');
      expect(cart.getItems()).toHaveLength(1);
    });

    it('should persist to localStorage after removal', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct(), 1);
      cart.removeItem('prod-1');
      const stored = JSON.parse(localStorage.getItem('skyyrose_cart'));
      expect(stored.items).toHaveLength(0);
    });
  });

  // ----------------------------------------------------------------
  // updateQuantity
  // ----------------------------------------------------------------
  describe('updateQuantity', () => {
    it('should update the quantity of an existing item', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct(), 1);
      cart.updateQuantity('prod-1', 10);
      expect(cart.getItems()[0].quantity).toBe(10);
    });

    it('should remove the item when quantity is set to 0', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct(), 3);
      cart.updateQuantity('prod-1', 0);
      expect(cart.getItems()).toHaveLength(0);
    });

    it('should remove the item when quantity is negative', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct(), 3);
      cart.updateQuantity('prod-1', -1);
      expect(cart.getItems()).toHaveLength(0);
    });

    it('should do nothing when item does not exist', () => {
      const cart = new CartManager();
      expect(() => cart.updateQuantity('ghost', 5)).not.toThrow();
    });

    it('should match by size and color for the correct variant', async () => {
      const cart = new CartManager();
      const product = createProduct();
      await cart.addItem(product, 1, { size: 'S', color: { name: 'Red', hex: '#FF0000' } });
      await cart.addItem(product, 1, { size: 'L', color: { name: 'Blue', hex: '#0000FF' } });
      cart.updateQuantity('prod-1', 7, 'S', 'Red');
      const items = cart.getItems();
      const small = items.find(i => i.size === 'S');
      const large = items.find(i => i.size === 'L');
      expect(small.quantity).toBe(7);
      expect(large.quantity).toBe(1);
    });

    it('should save to localStorage after update', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct(), 1);
      cart.updateQuantity('prod-1', 99);
      const stored = JSON.parse(localStorage.getItem('skyyrose_cart'));
      expect(stored.items[0].quantity).toBe(99);
    });
  });

  // ----------------------------------------------------------------
  // clearCart
  // ----------------------------------------------------------------
  describe('clearCart', () => {
    it('should remove all items', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct({ id: 'p1' }), 1);
      await cart.addItem(createProduct({ id: 'p2', sku: 'SKU-2', name: 'Item 2' }), 2);
      cart.clearCart();
      expect(cart.getItems()).toHaveLength(0);
      expect(cart.isEmpty()).toBe(true);
    });

    it('should persist empty cart to localStorage', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct(), 1);
      cart.clearCart();
      const stored = JSON.parse(localStorage.getItem('skyyrose_cart'));
      expect(stored.items).toHaveLength(0);
    });

    it('should not throw when clearing an already empty cart', () => {
      const cart = new CartManager();
      expect(() => cart.clearCart()).not.toThrow();
    });
  });

  // ----------------------------------------------------------------
  // getItems
  // ----------------------------------------------------------------
  describe('getItems', () => {
    it('should return a copy of the items array', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct(), 1);
      const items = cart.getItems();
      items.push({ productId: 'hack', sku: '', name: '', price: 0, quantity: 0 });
      expect(cart.getItems()).toHaveLength(1);
    });

    it('should return empty array for new cart', () => {
      const cart = new CartManager();
      expect(cart.getItems()).toEqual([]);
    });
  });

  // ----------------------------------------------------------------
  // getItemCount
  // ----------------------------------------------------------------
  describe('getItemCount', () => {
    it('should return 0 for empty cart', () => {
      const cart = new CartManager();
      expect(cart.getItemCount()).toBe(0);
    });

    it('should sum quantities across all items', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct({ id: 'p1' }), 3);
      await cart.addItem(createProduct({ id: 'p2', sku: 'SKU-2', name: 'P2' }), 5);
      expect(cart.getItemCount()).toBe(8);
    });
  });

  // ----------------------------------------------------------------
  // Pricing calculations
  // ----------------------------------------------------------------
  describe('pricing calculations', () => {
    it('getSubtotal should sum price * quantity', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct({ id: 'p1', price: 100 }), 2);
      await cart.addItem(createProduct({ id: 'p2', sku: 'SKU-2', name: 'P2', price: 50 }), 3);
      expect(cart.getSubtotal()).toBe(350);
    });

    it('getSubtotal should return 0 for empty cart', () => {
      const cart = new CartManager();
      expect(cart.getSubtotal()).toBe(0);
    });

    it('getTax should calculate at configured rate', async () => {
      const cart = new CartManager({ taxRate: 0.10 });
      await cart.addItem(createProduct({ price: 200 }), 1);
      expect(cart.getTax()).toBeCloseTo(20);
    });

    it('getTax should be 0 when taxRate is 0', async () => {
      const cart = new CartManager({ taxRate: 0 });
      await cart.addItem(createProduct({ price: 200 }), 1);
      expect(cart.getTax()).toBe(0);
    });

    it('getShipping should return configured shipping cost', () => {
      const cart = new CartManager({ shippingCost: 12.99 });
      expect(cart.getShipping()).toBe(12.99);
    });

    it('getShipping should return 0 by default (free shipping)', () => {
      const cart = new CartManager();
      expect(cart.getShipping()).toBe(0);
    });

    it('getTotalPrice should equal subtotal + tax + shipping', async () => {
      const cart = new CartManager({ taxRate: 0.08, shippingCost: 10 });
      await cart.addItem(createProduct({ price: 100 }), 1);
      // subtotal=100, tax=8, shipping=10 => total=118
      expect(cart.getTotalPrice()).toBeCloseTo(118);
    });

    it('getTotalPrice should be 0 for empty cart with free shipping', () => {
      const cart = new CartManager();
      expect(cart.getTotalPrice()).toBe(0);
    });

    it('getTotalPrice for empty cart with shipping cost should equal shipping only', () => {
      const cart = new CartManager({ shippingCost: 15 });
      expect(cart.getTotalPrice()).toBe(15);
    });
  });

  // ----------------------------------------------------------------
  // getCartState
  // ----------------------------------------------------------------
  describe('getCartState', () => {
    it('should return complete cart state with all fields', async () => {
      const cart = new CartManager({ taxRate: 0.08, shippingCost: 5, currency: 'USD' });
      await cart.addItem(createProduct({ price: 100 }), 2);
      const state = cart.getCartState();
      expect(state.items).toHaveLength(1);
      expect(state.subtotal).toBe(200);
      expect(state.tax).toBeCloseTo(16);
      expect(state.shipping).toBe(5);
      expect(state.total).toBeCloseTo(221);
      expect(state.currency).toBe('USD');
    });

    it('should reflect updated cart after changes', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct(), 1);
      const state1 = cart.getCartState();
      cart.clearCart();
      const state2 = cart.getCartState();
      expect(state1.items).toHaveLength(1);
      expect(state2.items).toHaveLength(0);
    });
  });

  // ----------------------------------------------------------------
  // isEmpty
  // ----------------------------------------------------------------
  describe('isEmpty', () => {
    it('should return true for new cart', () => {
      const cart = new CartManager();
      expect(cart.isEmpty()).toBe(true);
    });

    it('should return false after adding an item', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct(), 1);
      expect(cart.isEmpty()).toBe(false);
    });

    it('should return true after clearing', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct(), 1);
      cart.clearCart();
      expect(cart.isEmpty()).toBe(true);
    });
  });

  // ----------------------------------------------------------------
  // exportForCheckout
  // ----------------------------------------------------------------
  describe('exportForCheckout', () => {
    it('should return the same shape as getCartState', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct(), 2);
      const exported = cart.exportForCheckout();
      const state = cart.getCartState();
      expect(exported).toEqual(state);
    });
  });

  // ----------------------------------------------------------------
  // setTaxRate
  // ----------------------------------------------------------------
  describe('setTaxRate', () => {
    it('should update the tax rate', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct({ price: 100 }), 1);
      cart.setTaxRate(0.15);
      expect(cart.getTax()).toBeCloseTo(15);
    });

    it('should accept 0', () => {
      const cart = new CartManager();
      expect(() => cart.setTaxRate(0)).not.toThrow();
      expect(cart.getConfig().taxRate).toBe(0);
    });

    it('should accept 1', () => {
      const cart = new CartManager();
      expect(() => cart.setTaxRate(1)).not.toThrow();
      expect(cart.getConfig().taxRate).toBe(1);
    });

    it('should throw for negative rate', () => {
      const cart = new CartManager();
      expect(() => cart.setTaxRate(-0.01)).toThrow('Tax rate must be between 0 and 1');
    });

    it('should throw for rate greater than 1', () => {
      const cart = new CartManager();
      expect(() => cart.setTaxRate(1.01)).toThrow('Tax rate must be between 0 and 1');
    });

    it('should save to localStorage after change', () => {
      const cart = new CartManager();
      cart.setTaxRate(0.05);
      // Verify localStorage was updated (saveToStorage was called)
      const stored = localStorage.getItem('skyyrose_cart');
      expect(stored).toBeTruthy();
    });
  });

  // ----------------------------------------------------------------
  // setShippingCost
  // ----------------------------------------------------------------
  describe('setShippingCost', () => {
    it('should update shipping cost', () => {
      const cart = new CartManager();
      cart.setShippingCost(25);
      expect(cart.getShipping()).toBe(25);
    });

    it('should accept 0', () => {
      const cart = new CartManager({ shippingCost: 10 });
      cart.setShippingCost(0);
      expect(cart.getShipping()).toBe(0);
    });

    it('should throw for negative cost', () => {
      const cart = new CartManager();
      expect(() => cart.setShippingCost(-1)).toThrow('Shipping cost cannot be negative');
    });

    it('should save to localStorage after change', () => {
      const cart = new CartManager();
      cart.setShippingCost(9.99);
      const stored = localStorage.getItem('skyyrose_cart');
      expect(stored).toBeTruthy();
    });
  });

  // ----------------------------------------------------------------
  // subscribe / event system
  // ----------------------------------------------------------------
  describe('subscribe and events', () => {
    it('should notify listeners on item_added', async () => {
      const cart = new CartManager();
      const cb = jest.fn();
      cart.subscribe(cb);
      await cart.addItem(createProduct(), 1);
      expect(cb).toHaveBeenCalledTimes(1);
      expect(cb).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'item_added' })
      );
    });

    it('should include the cart item in add event', async () => {
      const cart = new CartManager();
      const cb = jest.fn();
      cart.subscribe(cb);
      await cart.addItem(createProduct(), 1);
      const event = cb.mock.calls[0][0];
      expect(event.item).toBeDefined();
      expect(event.item.productId).toBe('prod-1');
    });

    it('should include full cart state in every event', async () => {
      const cart = new CartManager();
      const cb = jest.fn();
      cart.subscribe(cb);
      await cart.addItem(createProduct(), 1);
      const event = cb.mock.calls[0][0];
      expect(event.cart).toBeDefined();
      expect(event.cart.items).toHaveLength(1);
      expect(event.cart.subtotal).toBeDefined();
      expect(event.cart.total).toBeDefined();
    });

    it('should notify listeners on item_removed', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct(), 1);
      const cb = jest.fn();
      cart.subscribe(cb);
      cart.removeItem('prod-1');
      expect(cb).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'item_removed' })
      );
    });

    it('should notify listeners on item_updated', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct(), 1);
      const cb = jest.fn();
      cart.subscribe(cb);
      cart.updateQuantity('prod-1', 5);
      expect(cb).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'item_updated' })
      );
    });

    it('should notify listeners on cart_cleared', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct(), 1);
      const cb = jest.fn();
      cart.subscribe(cb);
      cart.clearCart();
      expect(cb).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'cart_cleared' })
      );
    });

    it('should not include item in cart_cleared event', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct(), 1);
      const cb = jest.fn();
      cart.subscribe(cb);
      cart.clearCart();
      const event = cb.mock.calls[0][0];
      expect(event.item).toBeUndefined();
    });

    it('should unsubscribe when returned function is called', async () => {
      const cart = new CartManager();
      const cb = jest.fn();
      const unsubscribe = cart.subscribe(cb);
      unsubscribe();
      await cart.addItem(createProduct(), 1);
      expect(cb).not.toHaveBeenCalled();
    });

    it('should support multiple subscribers', async () => {
      const cart = new CartManager();
      const cb1 = jest.fn();
      const cb2 = jest.fn();
      cart.subscribe(cb1);
      cart.subscribe(cb2);
      await cart.addItem(createProduct(), 1);
      expect(cb1).toHaveBeenCalledTimes(1);
      expect(cb2).toHaveBeenCalledTimes(1);
    });

    it('should handle subscriber errors gracefully without breaking other subscribers', async () => {
      const cart = new CartManager();
      const badCb = jest.fn().mockImplementation(() => {
        throw new Error('subscriber error');
      });
      const goodCb = jest.fn();
      cart.subscribe(badCb);
      cart.subscribe(goodCb);
      await cart.addItem(createProduct(), 1);
      expect(badCb).toHaveBeenCalled();
      expect(goodCb).toHaveBeenCalled();
    });

    it('should not notify after all subscribers unsubscribe', async () => {
      const cart = new CartManager();
      const cb1 = jest.fn();
      const cb2 = jest.fn();
      const unsub1 = cart.subscribe(cb1);
      const unsub2 = cart.subscribe(cb2);
      unsub1();
      unsub2();
      await cart.addItem(createProduct(), 1);
      expect(cb1).not.toHaveBeenCalled();
      expect(cb2).not.toHaveBeenCalled();
    });
  });

  // ----------------------------------------------------------------
  // localStorage persistence
  // ----------------------------------------------------------------
  describe('localStorage persistence', () => {
    it('should load items from localStorage on construction', async () => {
      const data = {
        items: [{
          productId: 'p-saved',
          sku: 'SKU-SAVED',
          name: 'Saved Product',
          price: 100,
          quantity: 2,
        }],
        timestamp: Date.now(),
      };
      localStorage.setItem('skyyrose_cart', JSON.stringify(data));
      const cart = new CartManager();
      expect(cart.getItems()).toHaveLength(1);
      expect(cart.getItems()[0].productId).toBe('p-saved');
    });

    it('should handle corrupt JSON in localStorage', () => {
      localStorage.setItem('skyyrose_cart', '{{not valid json}}');
      const cart = new CartManager();
      expect(cart.getItems()).toHaveLength(0);
    });

    it('should handle missing items key in stored data', () => {
      localStorage.setItem('skyyrose_cart', JSON.stringify({ timestamp: Date.now() }));
      const cart = new CartManager();
      expect(cart.getItems()).toHaveLength(0);
    });

    it('should clear expired cart older than 7 days', () => {
      const eightDaysAgo = Date.now() - (8 * 24 * 60 * 60 * 1000);
      const data = {
        items: [{ productId: 'old', sku: 'OLD', name: 'Old', price: 50, quantity: 1 }],
        timestamp: eightDaysAgo,
      };
      localStorage.setItem('skyyrose_cart', JSON.stringify(data));
      const cart = new CartManager();
      expect(cart.getItems()).toHaveLength(0);
    });

    it('should keep cart that is less than 7 days old', () => {
      const oneDayAgo = Date.now() - (1 * 24 * 60 * 60 * 1000);
      const data = {
        items: [{ productId: 'recent', sku: 'REC', name: 'Recent', price: 50, quantity: 1 }],
        timestamp: oneDayAgo,
      };
      localStorage.setItem('skyyrose_cart', JSON.stringify(data));
      const cart = new CartManager();
      expect(cart.getItems()).toHaveLength(1);
    });

    it('should treat missing timestamp as expired', () => {
      const data = {
        items: [{ productId: 'no-ts', sku: 'NTS', name: 'No Timestamp', price: 50, quantity: 1 }],
      };
      localStorage.setItem('skyyrose_cart', JSON.stringify(data));
      const cart = new CartManager();
      // timestamp defaults to 0, age = Date.now() - 0, which is > 7 days
      expect(cart.getItems()).toHaveLength(0);
    });

    it('should handle localStorage.setItem failure gracefully', async () => {
      const cart = new CartManager();
      // Make setItem throw (e.g., storage quota exceeded)
      jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
        throw new Error('QuotaExceededError');
      });
      // addItem should not throw even if save fails
      await expect(cart.addItem(createProduct(), 1)).resolves.not.toThrow();
      // Item is still in memory
      expect(cart.getItems()).toHaveLength(1);
    });

    it('should use custom storageKey', async () => {
      const cart = new CartManager({ storageKey: 'my_custom_key' });
      await cart.addItem(createProduct(), 1);
      expect(localStorage.getItem('my_custom_key')).toBeTruthy();
      expect(localStorage.getItem('skyyrose_cart')).toBeNull();
    });
  });

  // ----------------------------------------------------------------
  // Singleton: getCartManager
  // ----------------------------------------------------------------
  describe('getCartManager singleton', () => {
    // We need to reset the module-level variable between tests.
    // The cleanest way is to re-import the module.
    beforeEach(() => {
      jest.resetModules();
    });

    it('should return the same instance on subsequent calls', () => {
      // Re-require to get a fresh module with null singleton
      jest.isolateModules(() => {
        const mod = require('../cartManager');
        const a = mod.getCartManager();
        const b = mod.getCartManager();
        expect(a).toBe(b);
      });
    });

    it('should create instance with provided config on first call', () => {
      jest.isolateModules(() => {
        const mod = require('../cartManager');
        const instance = mod.getCartManager({ currency: 'CAD', taxRate: 0.13 });
        expect(instance.getConfig().currency).toBe('CAD');
        expect(instance.getConfig().taxRate).toBe(0.13);
      });
    });

    it('should ignore config on subsequent calls (singleton already created)', () => {
      jest.isolateModules(() => {
        const mod = require('../cartManager');
        mod.getCartManager({ currency: 'CAD' });
        const second = mod.getCartManager({ currency: 'JPY' });
        // Second call's config is ignored - singleton was already created
        expect(second.getConfig().currency).toBe('CAD');
      });
    });
  });

  // ----------------------------------------------------------------
  // Edge cases and complex scenarios
  // ----------------------------------------------------------------
  describe('edge cases', () => {
    it('should handle adding multiple different products', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct({ id: 'a', sku: 'A', name: 'Product A', price: 10 }), 1);
      await cart.addItem(createProduct({ id: 'b', sku: 'B', name: 'Product B', price: 20 }), 2);
      await cart.addItem(createProduct({ id: 'c', sku: 'C', name: 'Product C', price: 30 }), 3);
      expect(cart.getItems()).toHaveLength(3);
      expect(cart.getItemCount()).toBe(6);
      expect(cart.getSubtotal()).toBe(10 + 40 + 90);
    });

    it('should handle very large quantities', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct({ price: 1 }), 999999);
      expect(cart.getItemCount()).toBe(999999);
      expect(cart.getSubtotal()).toBe(999999);
    });

    it('should handle very small prices (cents)', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct({ price: 0.01 }), 1);
      expect(cart.getSubtotal()).toBeCloseTo(0.01);
    });

    it('should handle rapid add/remove cycles', async () => {
      const cart = new CartManager();
      for (let i = 0; i < 10; i++) {
        await cart.addItem(createProduct(), 1);
        cart.removeItem('prod-1');
      }
      expect(cart.isEmpty()).toBe(true);
    });

    it('should handle updateQuantity triggering removal and then re-adding', async () => {
      const cart = new CartManager();
      await cart.addItem(createProduct(), 5);
      cart.updateQuantity('prod-1', 0); // triggers removeItem
      expect(cart.isEmpty()).toBe(true);
      await cart.addItem(createProduct(), 3);
      expect(cart.getItems()).toHaveLength(1);
      expect(cart.getItemCount()).toBe(3);
    });

    it('should correctly compute totals with tax and shipping for multiple items', async () => {
      const cart = new CartManager({ taxRate: 0.10, shippingCost: 20 });
      await cart.addItem(createProduct({ id: 'a', sku: 'A', name: 'A', price: 100 }), 2); // 200
      await cart.addItem(createProduct({ id: 'b', sku: 'B', name: 'B', price: 50 }), 1);  // 50
      // subtotal = 250, tax = 25, shipping = 20, total = 295
      expect(cart.getSubtotal()).toBe(250);
      expect(cart.getTax()).toBeCloseTo(25);
      expect(cart.getTotalPrice()).toBeCloseTo(295);
    });
  });
});
