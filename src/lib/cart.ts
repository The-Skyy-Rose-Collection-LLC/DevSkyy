/**
 * DevSkyy Shopping Cart Manager
 * Singleton pattern cart state manager with WooCommerce sync
 * SkyyRose E-commerce Integration
 */

import { Logger } from '../utils/Logger.js';

// Cart Item Interface
export interface CartItem {
  productId: string;
  sku: string;
  name: string;
  price: number;
  salePrice?: number;
  quantity: number;
  size?: string;
  color?: string;
  imageUrl?: string;
  modelUrl?: string;
}

// Cart State Interface
export interface CartState {
  items: CartItem[];
  subtotal: number;
  tax: number;
  total: number;
  itemCount: number;
  currency: string;
}

// Cart Configuration
interface CartConfig {
  taxRate: number; // Default tax rate (e.g., 0.08 for 8%)
  currency: string; // Default currency
  storageKey: string; // LocalStorage key
  wooCommerceUrl?: string; // WooCommerce REST API URL
}

// Default configuration
const DEFAULT_CONFIG: CartConfig = {
  taxRate: 0.08,
  currency: 'USD',
  storageKey: 'skyyrose_cart',
};

// Type guard for CartItem matching
function itemsMatch(
  item1: CartItem,
  item2: { productId: string; size?: string | undefined; color?: string | undefined }
): boolean {
  return (
    item1.productId === item2.productId &&
    item1.size === item2.size &&
    item1.color === item2.color
  );
}

/**
 * Shopping Cart Manager
 * Singleton pattern for managing cart state across the application
 */
export class CartManager {
  private static instance: CartManager | null = null;
  private logger: Logger;
  private config: CartConfig;
  private items: CartItem[] = [];
  private subscribers: Set<(state: CartState) => void> = new Set();

  private constructor(config: Partial<CartConfig> = {}) {
    this.logger = new Logger('CartManager');
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.loadFromLocalStorage();
    this.logger.info('CartManager initialized');
  }

  /**
   * Get singleton instance
   */
  public static getInstance(config?: Partial<CartConfig>): CartManager {
    if (!CartManager.instance) {
      CartManager.instance = new CartManager(config);
    }
    return CartManager.instance;
  }

  /**
   * Reset singleton instance (useful for testing)
   */
  public static resetInstance(): void {
    CartManager.instance = null;
  }

  /**
   * Add item to cart
   */
  public addItem(item: CartItem): void {
    try {
      // Validate item
      if (!item.productId || !item.sku || !item.name || item.price < 0) {
        throw new Error('Invalid cart item: missing required fields or invalid price');
      }

      if (item.quantity <= 0) {
        throw new Error('Invalid cart item: quantity must be greater than 0');
      }

      // Check if item already exists in cart
      const existingItemIndex = this.items.findIndex((cartItem) =>
        itemsMatch(cartItem, item)
      );

      if (existingItemIndex !== -1) {
        // Update quantity of existing item
        this.items[existingItemIndex]!.quantity += item.quantity;
        this.logger.info(`Updated quantity for item ${item.productId}`, {
          newQuantity: this.items[existingItemIndex]!.quantity,
        });
      } else {
        // Add new item
        this.items.push({ ...item });
        this.logger.info(`Added new item to cart: ${item.name}`, { item });
      }

      this.saveToLocalStorage();
      this.notifySubscribers();
    } catch (error) {
      this.logger.error('Failed to add item to cart', error);
      throw error;
    }
  }

  /**
   * Remove item from cart
   */
  public removeItem(productId: string, size?: string, color?: string): void {
    try {
      const initialLength = this.items.length;
      this.items = this.items.filter(
        (item) => !itemsMatch(item, { productId, size, color })
      );

      if (this.items.length < initialLength) {
        this.logger.info(`Removed item from cart: ${productId}`);
        this.saveToLocalStorage();
        this.notifySubscribers();
      } else {
        this.logger.warn(`Item not found in cart: ${productId}`);
      }
    } catch (error) {
      this.logger.error('Failed to remove item from cart', error);
      throw error;
    }
  }

  /**
   * Update item quantity
   */
  public updateQuantity(
    productId: string,
    quantity: number,
    size?: string,
    color?: string
  ): void {
    try {
      if (quantity < 0) {
        throw new Error('Quantity cannot be negative');
      }

      if (quantity === 0) {
        this.removeItem(productId, size, color);
        return;
      }

      const item = this.items.find((cartItem) =>
        itemsMatch(cartItem, { productId, size, color })
      );

      if (item) {
        item.quantity = quantity;
        this.logger.info(`Updated quantity for item ${productId}`, { quantity });
        this.saveToLocalStorage();
        this.notifySubscribers();
      } else {
        this.logger.warn(`Item not found in cart: ${productId}`);
      }
    } catch (error) {
      this.logger.error('Failed to update item quantity', error);
      throw error;
    }
  }

  /**
   * Clear all items from cart
   */
  public clearCart(): void {
    try {
      this.items = [];
      this.logger.info('Cart cleared');
      this.saveToLocalStorage();
      this.notifySubscribers();
    } catch (error) {
      this.logger.error('Failed to clear cart', error);
      throw error;
    }
  }

  /**
   * Get all cart items
   */
  public getItems(): CartItem[] {
    return [...this.items];
  }

  /**
   * Get cart state with calculated totals
   */
  public getState(): CartState {
    const subtotal = this.calculateSubtotal();
    const tax = this.calculateTax(subtotal);
    const total = subtotal + tax;
    const itemCount = this.items.reduce((sum, item) => sum + item.quantity, 0);

    return {
      items: this.getItems(),
      subtotal,
      tax,
      total,
      itemCount,
      currency: this.config.currency,
    };
  }

  /**
   * Calculate cart subtotal
   */
  private calculateSubtotal(): number {
    return this.items.reduce((sum, item) => {
      const price = item.salePrice ?? item.price;
      return sum + price * item.quantity;
    }, 0);
  }

  /**
   * Calculate tax
   */
  private calculateTax(subtotal: number): number {
    return subtotal * this.config.taxRate;
  }

  /**
   * Sync cart with WooCommerce
   */
  public async syncWithWooCommerce(): Promise<void> {
    try {
      if (!this.config.wooCommerceUrl) {
        this.logger.warn('WooCommerce URL not configured, skipping sync');
        return;
      }

      this.logger.info('Syncing cart with WooCommerce...');

      // Prepare cart data for WooCommerce
      const cartData = {
        items: this.items.map((item) => ({
          product_id: item.productId,
          quantity: item.quantity,
          variation_id: item.size || item.color ? `${item.size}-${item.color}` : undefined,
        })),
      };

      // Make API request to WooCommerce
      const response = await fetch(`${this.config.wooCommerceUrl}/wp-json/wc/store/v1/cart`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(cartData),
      });

      if (!response.ok) {
        throw new Error(`WooCommerce sync failed: ${response.statusText}`);
      }

      const result = await response.json();
      this.logger.info('Cart synced with WooCommerce successfully', { result });
    } catch (error) {
      this.logger.error('Failed to sync cart with WooCommerce', error);
      throw error;
    }
  }

  /**
   * Save cart to localStorage
   */
  public saveToLocalStorage(): void {
    try {
      if (typeof window === 'undefined') {
        return; // Skip if not in browser environment
      }

      const cartData = {
        items: this.items,
        timestamp: new Date().toISOString(),
      };

      localStorage.setItem(this.config.storageKey, JSON.stringify(cartData));
      this.logger.debug('Cart saved to localStorage');
    } catch (error) {
      this.logger.error('Failed to save cart to localStorage', error);
    }
  }

  /**
   * Load cart from localStorage
   */
  public loadFromLocalStorage(): void {
    try {
      if (typeof window === 'undefined') {
        return; // Skip if not in browser environment
      }

      const storedData = localStorage.getItem(this.config.storageKey);

      if (storedData) {
        const cartData = JSON.parse(storedData);
        this.items = cartData.items || [];
        this.logger.info('Cart loaded from localStorage', {
          itemCount: this.items.length,
        });
        this.notifySubscribers();
      }
    } catch (error) {
      this.logger.error('Failed to load cart from localStorage', error);
      this.items = [];
    }
  }

  /**
   * Subscribe to cart updates
   * @returns Unsubscribe function
   */
  public subscribe(callback: (state: CartState) => void): () => void {
    this.subscribers.add(callback);
    this.logger.debug('New subscriber added', { totalSubscribers: this.subscribers.size });

    // Immediately call callback with current state
    callback(this.getState());

    // Return unsubscribe function
    return () => {
      this.subscribers.delete(callback);
      this.logger.debug('Subscriber removed', { totalSubscribers: this.subscribers.size });
    };
  }

  /**
   * Notify all subscribers of state changes
   */
  private notifySubscribers(): void {
    const state = this.getState();
    this.subscribers.forEach((callback) => {
      try {
        callback(state);
      } catch (error) {
        this.logger.error('Error in cart subscriber callback', error);
      }
    });
  }

  /**
   * Get cart configuration
   */
  public getConfig(): CartConfig {
    return { ...this.config };
  }

  /**
   * Update cart configuration
   */
  public updateConfig(config: Partial<CartConfig>): void {
    this.config = { ...this.config, ...config };
    this.logger.info('Cart configuration updated', { config: this.config });
    this.notifySubscribers();
  }

  /**
   * Get item by product ID
   */
  public getItem(productId: string, size?: string, color?: string): CartItem | undefined {
    return this.items.find((item) => itemsMatch(item, { productId, size, color }));
  }

  /**
   * Check if item exists in cart
   */
  public hasItem(productId: string, size?: string, color?: string): boolean {
    return this.getItem(productId, size, color) !== undefined;
  }

  /**
   * Get total item count
   */
  public getItemCount(): number {
    return this.items.reduce((sum, item) => sum + item.quantity, 0);
  }
}

// Export singleton instance getter
export const getCartManager = (config?: Partial<CartConfig>): CartManager => {
  return CartManager.getInstance(config);
};

// Export default instance
export const cartManager = CartManager.getInstance();
