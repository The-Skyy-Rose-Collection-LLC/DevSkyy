/**
 * DevSkyy useCart Hook
 * React hook for cart state management
 * SkyyRose E-commerce Integration
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { CartManager, CartItem, CartState } from '../lib/cart.js';
import { Logger } from '../utils/Logger.js';

// Hook return type
export interface UseCartReturn {
  // State
  state: CartState;
  items: CartItem[];
  subtotal: number;
  tax: number;
  total: number;
  itemCount: number;
  currency: string;
  isLoading: boolean;
  error: string | null;

  // Actions
  addItem: (item: CartItem) => void;
  removeItem: (productId: string, size?: string, color?: string) => void;
  updateQuantity: (productId: string, quantity: number, size?: string, color?: string) => void;
  clearCart: () => void;
  syncWithWooCommerce: () => Promise<void>;

  // Utilities
  getItem: (productId: string, size?: string, color?: string) => CartItem | undefined;
  hasItem: (productId: string, size?: string, color?: string) => boolean;
}

/**
 * Custom React hook for cart management
 * Provides cart state and actions with automatic updates
 */
export function useCart(): UseCartReturn {
  const logger = useMemo(() => new Logger('useCart'), []);
  const cartManager = useMemo(() => CartManager.getInstance(), []);

  // State
  const [state, setState] = useState<CartState>(cartManager.getState());
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Subscribe to cart updates
  useEffect(() => {
    logger.debug('Subscribing to cart updates');

    const unsubscribe = cartManager.subscribe((newState) => {
      setState(newState);
    });

    return () => {
      logger.debug('Unsubscribing from cart updates');
      unsubscribe();
    };
  }, [cartManager, logger]);

  // Add item to cart
  const addItem = useCallback(
    (item: CartItem) => {
      try {
        setError(null);
        cartManager.addItem(item);
        logger.info('Item added to cart', { item });
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to add item to cart';
        setError(errorMessage);
        logger.error('Error adding item to cart', err);
      }
    },
    [cartManager, logger]
  );

  // Remove item from cart
  const removeItem = useCallback(
    (productId: string, size?: string, color?: string) => {
      try {
        setError(null);
        cartManager.removeItem(productId, size, color);
        logger.info('Item removed from cart', { productId, size, color });
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to remove item from cart';
        setError(errorMessage);
        logger.error('Error removing item from cart', err);
      }
    },
    [cartManager, logger]
  );

  // Update item quantity
  const updateQuantity = useCallback(
    (productId: string, quantity: number, size?: string, color?: string) => {
      try {
        setError(null);
        cartManager.updateQuantity(productId, quantity, size, color);
        logger.info('Item quantity updated', { productId, quantity, size, color });
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to update item quantity';
        setError(errorMessage);
        logger.error('Error updating item quantity', err);
      }
    },
    [cartManager, logger]
  );

  // Clear cart
  const clearCart = useCallback(() => {
    try {
      setError(null);
      cartManager.clearCart();
      logger.info('Cart cleared');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to clear cart';
      setError(errorMessage);
      logger.error('Error clearing cart', err);
    }
  }, [cartManager, logger]);

  // Sync with WooCommerce
  const syncWithWooCommerce = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      await cartManager.syncWithWooCommerce();
      logger.info('Cart synced with WooCommerce');
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to sync cart with WooCommerce';
      setError(errorMessage);
      logger.error('Error syncing cart with WooCommerce', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [cartManager, logger]);

  // Get specific item
  const getItem = useCallback(
    (productId: string, size?: string, color?: string): CartItem | undefined => {
      return cartManager.getItem(productId, size, color);
    },
    [cartManager]
  );

  // Check if item exists
  const hasItem = useCallback(
    (productId: string, size?: string, color?: string): boolean => {
      return cartManager.hasItem(productId, size, color);
    },
    [cartManager]
  );

  return {
    // State
    state,
    items: state.items,
    subtotal: state.subtotal,
    tax: state.tax,
    total: state.total,
    itemCount: state.itemCount,
    currency: state.currency,
    isLoading,
    error,

    // Actions
    addItem,
    removeItem,
    updateQuantity,
    clearCart,
    syncWithWooCommerce,

    // Utilities
    getItem,
    hasItem,
  };
}

/**
 * Hook for cart item count (lightweight)
 * Use this when you only need the count, not the full cart state
 */
export function useCartItemCount(): number {
  const cartManager = useMemo(() => CartManager.getInstance(), []);
  const [itemCount, setItemCount] = useState<number>(cartManager.getItemCount());

  useEffect(() => {
    const unsubscribe = cartManager.subscribe((state) => {
      setItemCount(state.itemCount);
    });

    return unsubscribe;
  }, [cartManager]);

  return itemCount;
}

/**
 * Hook for cart total (lightweight)
 * Use this when you only need the total, not the full cart state
 */
export function useCartTotal(): { total: number; currency: string } {
  const cartManager = useMemo(() => CartManager.getInstance(), []);
  const [total, setTotal] = useState<number>(cartManager.getState().total);
  const [currency, setCurrency] = useState<string>(cartManager.getState().currency);

  useEffect(() => {
    const unsubscribe = cartManager.subscribe((state) => {
      setTotal(state.total);
      setCurrency(state.currency);
    });

    return unsubscribe;
  }, [cartManager]);

  return { total, currency };
}

/**
 * Hook to check if a specific item is in cart
 */
export function useIsInCart(
  productId: string,
  size?: string,
  color?: string
): boolean {
  const cartManager = useMemo(() => CartManager.getInstance(), []);
  const [isInCart, setIsInCart] = useState<boolean>(
    cartManager.hasItem(productId, size, color)
  );

  useEffect(() => {
    const unsubscribe = cartManager.subscribe(() => {
      setIsInCart(cartManager.hasItem(productId, size, color));
    });

    return unsubscribe;
  }, [cartManager, productId, size, color]);

  return isInCart;
}
