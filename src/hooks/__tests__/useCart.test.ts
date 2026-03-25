/**
 * Unit Tests for useCart hook
 * @jest-environment jsdom
 */

import { renderHook, act } from '@testing-library/react';
import { useCart, useCartItemCount, useCartTotal, useIsInCart } from '../useCart';
import { CartManager } from '../../lib/cart';

// Mock Logger
jest.mock('../../utils/Logger', () => ({
  Logger: jest.fn().mockImplementation(() => ({
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    debug: jest.fn(),
  })),
}));

const testItem = {
  productId: 'prod-1',
  sku: 'SKU-001',
  name: 'Test Product',
  price: 99.99,
  quantity: 1,
};

describe('useCart', () => {
  beforeEach(() => {
    CartManager.resetInstance();
    localStorage.clear();
  });

  it('should return initial empty state', () => {
    const { result } = renderHook(() => useCart());
    expect(result.current.items).toEqual([]);
    expect(result.current.itemCount).toBe(0);
    expect(result.current.total).toBe(0);
    expect(result.current.currency).toBe('USD');
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should add item', () => {
    const { result } = renderHook(() => useCart());

    act(() => {
      result.current.addItem(testItem);
    });

    expect(result.current.items).toHaveLength(1);
    expect(result.current.itemCount).toBe(1);
  });

  it('should remove item', () => {
    const { result } = renderHook(() => useCart());

    act(() => {
      result.current.addItem(testItem);
    });

    act(() => {
      result.current.removeItem('prod-1');
    });

    expect(result.current.items).toHaveLength(0);
  });

  it('should update quantity', () => {
    const { result } = renderHook(() => useCart());

    act(() => {
      result.current.addItem(testItem);
    });

    act(() => {
      result.current.updateQuantity('prod-1', 5);
    });

    expect(result.current.items[0]!.quantity).toBe(5);
  });

  it('should clear cart', () => {
    const { result } = renderHook(() => useCart());

    act(() => {
      result.current.addItem(testItem);
    });

    act(() => {
      result.current.clearCart();
    });

    expect(result.current.items).toHaveLength(0);
  });

  it('should set error on invalid addItem', () => {
    const { result } = renderHook(() => useCart());

    act(() => {
      result.current.addItem({ ...testItem, productId: '' });
    });

    expect(result.current.error).toBeTruthy();
  });

  it('should handle non-Error exception in addItem', () => {
    const { result } = renderHook(() => useCart());
    const cm = CartManager.getInstance();
    jest.spyOn(cm, 'addItem').mockImplementation(() => { throw 'string error'; });

    act(() => {
      result.current.addItem(testItem);
    });

    expect(result.current.error).toBe('Failed to add item to cart');
  });

  it('should handle Error exception in removeItem', () => {
    const { result } = renderHook(() => useCart());
    const cm = CartManager.getInstance();
    jest.spyOn(cm, 'removeItem').mockImplementation(() => { throw new Error('remove failed'); });

    act(() => {
      result.current.removeItem('prod-1');
    });

    expect(result.current.error).toBe('remove failed');
  });

  it('should handle non-Error exception in removeItem', () => {
    const { result } = renderHook(() => useCart());
    const cm = CartManager.getInstance();
    jest.spyOn(cm, 'removeItem').mockImplementation(() => { throw 42; });

    act(() => {
      result.current.removeItem('prod-1');
    });

    expect(result.current.error).toBe('Failed to remove item from cart');
  });

  it('should handle Error exception in updateQuantity', () => {
    const { result } = renderHook(() => useCart());
    const cm = CartManager.getInstance();
    jest.spyOn(cm, 'updateQuantity').mockImplementation(() => { throw new Error('update failed'); });

    act(() => {
      result.current.updateQuantity('prod-1', 5);
    });

    expect(result.current.error).toBe('update failed');
  });

  it('should handle non-Error exception in updateQuantity', () => {
    const { result } = renderHook(() => useCart());
    const cm = CartManager.getInstance();
    jest.spyOn(cm, 'updateQuantity').mockImplementation(() => { throw null; });

    act(() => {
      result.current.updateQuantity('prod-1', 5);
    });

    expect(result.current.error).toBe('Failed to update item quantity');
  });

  it('should handle Error exception in clearCart', () => {
    const { result } = renderHook(() => useCart());
    const cm = CartManager.getInstance();
    jest.spyOn(cm, 'clearCart').mockImplementation(() => { throw new Error('clear failed'); });

    act(() => {
      result.current.clearCart();
    });

    expect(result.current.error).toBe('clear failed');
  });

  it('should handle non-Error exception in clearCart', () => {
    const { result } = renderHook(() => useCart());
    const cm = CartManager.getInstance();
    jest.spyOn(cm, 'clearCart').mockImplementation(() => { throw undefined; });

    act(() => {
      result.current.clearCart();
    });

    expect(result.current.error).toBe('Failed to clear cart');
  });

  it('should sync with WooCommerce successfully', async () => {
    const { result } = renderHook(() => useCart());
    const cm = CartManager.getInstance();
    jest.spyOn(cm, 'syncWithWooCommerce').mockResolvedValue(undefined);

    await act(async () => {
      await result.current.syncWithWooCommerce();
    });

    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('should handle Error exception in syncWithWooCommerce', async () => {
    const { result } = renderHook(() => useCart());
    const cm = CartManager.getInstance();
    jest.spyOn(cm, 'syncWithWooCommerce').mockRejectedValue(new Error('sync failed'));

    await act(async () => {
      try {
        await result.current.syncWithWooCommerce();
      } catch (e) {
        // Expected to rethrow
      }
    });

    expect(result.current.error).toBe('sync failed');
    expect(result.current.isLoading).toBe(false);
  });

  it('should handle non-Error exception in syncWithWooCommerce', async () => {
    const { result } = renderHook(() => useCart());
    const cm = CartManager.getInstance();
    jest.spyOn(cm, 'syncWithWooCommerce').mockRejectedValue('string error');

    await act(async () => {
      try {
        await result.current.syncWithWooCommerce();
      } catch (e) {
        // Expected to rethrow
      }
    });

    expect(result.current.error).toBe('Failed to sync cart with WooCommerce');
    expect(result.current.isLoading).toBe(false);
  });

  it('should clear error on successful operation', () => {
    const { result } = renderHook(() => useCart());

    // Trigger an error first
    act(() => {
      result.current.addItem({ ...testItem, productId: '' });
    });
    expect(result.current.error).toBeTruthy();

    // Successful operation should clear error
    act(() => {
      result.current.addItem(testItem);
    });
    expect(result.current.error).toBeNull();
  });

  it('should getItem and hasItem', () => {
    const { result } = renderHook(() => useCart());

    act(() => {
      result.current.addItem(testItem);
    });

    expect(result.current.getItem('prod-1')).toBeDefined();
    expect(result.current.hasItem('prod-1')).toBe(true);
    expect(result.current.hasItem('nonexistent')).toBe(false);
  });

  it('should getItem with size and color', () => {
    const { result } = renderHook(() => useCart());
    const sizedItem = { ...testItem, size: 'M', color: 'Black' };

    act(() => {
      result.current.addItem(sizedItem);
    });

    expect(result.current.getItem('prod-1', 'M', 'Black')).toBeDefined();
    expect(result.current.hasItem('prod-1', 'M', 'Black')).toBe(true);
    expect(result.current.hasItem('prod-1', 'L', 'Black')).toBe(false);
  });

  it('should return subtotal, tax, and total', () => {
    const { result } = renderHook(() => useCart());

    act(() => {
      result.current.addItem({ ...testItem, price: 100, quantity: 2 });
    });

    expect(result.current.subtotal).toBeGreaterThan(0);
    expect(result.current.total).toBeGreaterThan(0);
  });
});

describe('useCartItemCount', () => {
  beforeEach(() => {
    CartManager.resetInstance();
    localStorage.clear();
  });

  it('should return 0 initially', () => {
    const { result } = renderHook(() => useCartItemCount());
    expect(result.current).toBe(0);
  });
});

describe('useCartTotal', () => {
  beforeEach(() => {
    CartManager.resetInstance();
    localStorage.clear();
  });

  it('should return total and currency', () => {
    const { result } = renderHook(() => useCartTotal());
    expect(result.current.total).toBe(0);
    expect(result.current.currency).toBe('USD');
  });
});

describe('useIsInCart', () => {
  beforeEach(() => {
    CartManager.resetInstance();
    localStorage.clear();
  });

  it('should return false when not in cart', () => {
    const { result } = renderHook(() => useIsInCart('prod-1'));
    expect(result.current).toBe(false);
  });
});
