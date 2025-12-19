/**
 * Shopping Cart Manager
 * Client-side cart management with localStorage persistence
 *
 * @author DevSkyy Platform Team
 * @version 1.0.0
 */

import { Logger } from '../utils/Logger.js';
import type { ShowroomProduct, CartItem, CartState } from '../types/product.js';
import type { AddToCartOptions } from './productInteraction.js';

/**
 * Cart configuration
 */
export interface CartConfig {
  storageKey?: string;
  taxRate?: number;
  shippingCost?: number;
  currency?: string;
}

/**
 * Cart event types
 */
export type CartEventType = 'item_added' | 'item_removed' | 'item_updated' | 'cart_cleared';

export interface CartEvent {
  type: CartEventType;
  item?: CartItem | undefined;
  cart: CartState;
}

/**
 * Cart event callback
 */
export type CartCallback = (event: CartEvent) => void;

/**
 * Default configuration
 */
const DEFAULT_CONFIG: Required<CartConfig> = {
  storageKey: 'skyyrose_cart',
  taxRate: 0.08,  // 8% tax
  shippingCost: 0,  // Free shipping
  currency: 'USD',
};

/**
 * Shopping cart manager
 */
export class CartManager {
  private logger: Logger;
  private config: Required<CartConfig>;
  private items: CartItem[] = [];
  private callbacks: Set<CartCallback> = new Set();

  constructor(config: CartConfig = {}) {
    this.logger = new Logger('CartManager');
    this.config = { ...DEFAULT_CONFIG, ...config };

    // Load cart from localStorage
    this.loadFromStorage();
  }

  /**
   * Add item to cart
   */
  public async addItem(
    product: ShowroomProduct,
    quantity: number,
    options?: AddToCartOptions
  ): Promise<void> {
    // Validate quantity
    if (quantity <= 0) {
      throw new Error('Quantity must be greater than 0');
    }

    // Check if item already exists in cart
    const existingIndex = this.items.findIndex(
      (item) =>
        item.productId === product.id &&
        item.size === options?.size &&
        item.color?.name === options?.color?.name
    );

    let cartItem: CartItem;

    if (existingIndex !== -1) {
      // Update existing item quantity
      const existingItem = this.items[existingIndex];
      if (existingItem) {
        existingItem.quantity += quantity;
        cartItem = existingItem;
        this.logger.info(`Updated cart item: ${product.name} (qty: ${existingItem.quantity})`);
      } else {
        // This shouldn't happen, but TypeScript requires it
        throw new Error('Cart item not found after index check');
      }
    } else {
      // Add new item
      cartItem = {
        productId: product.id,
        sku: product.sku,
        name: product.name,
        price: product.salePrice || product.price,
        quantity,
        size: options?.size,
        color: options?.color,
        imageUrl: product.images?.[0],
      };
      this.items.push(cartItem);
      this.logger.info(`Added to cart: ${product.name} (qty: ${quantity})`);
    }

    // Save to storage
    this.saveToStorage();

    // Notify listeners
    this.notifyListeners({
      type: 'item_added',
      item: cartItem,
      cart: this.getCartState(),
    });
  }

  /**
   * Remove item from cart
   */
  public removeItem(productId: string, size?: string, colorName?: string): void {
    const index = this.items.findIndex(
      (item) =>
        item.productId === productId &&
        item.size === size &&
        item.color?.name === colorName
    );

    if (index === -1) {
      this.logger.warn(`Item not found in cart: ${productId}`);
      return;
    }

    const removedItem = this.items[index];
    if (!removedItem) {
      this.logger.warn(`Item at index ${index} not found`);
      return;
    }
    this.items.splice(index, 1);

    this.logger.info(`Removed from cart: ${removedItem.name}`);

    // Save to storage
    this.saveToStorage();

    // Notify listeners
    this.notifyListeners({
      type: 'item_removed',
      item: removedItem,
      cart: this.getCartState(),
    });
  }

  /**
   * Update item quantity
   */
  public updateQuantity(
    productId: string,
    quantity: number,
    size?: string,
    colorName?: string
  ): void {
    const item = this.items.find(
      (item) =>
        item.productId === productId &&
        item.size === size &&
        item.color?.name === colorName
    );

    if (!item) {
      this.logger.warn(`Item not found in cart: ${productId}`);
      return;
    }

    if (quantity <= 0) {
      this.removeItem(productId, size, colorName);
      return;
    }

    item.quantity = quantity;

    this.logger.info(`Updated quantity: ${item.name} (qty: ${quantity})`);

    // Save to storage
    this.saveToStorage();

    // Notify listeners
    this.notifyListeners({
      type: 'item_updated',
      item,
      cart: this.getCartState(),
    });
  }

  /**
   * Clear cart
   */
  public clearCart(): void {
    this.items = [];

    this.logger.info('Cart cleared');

    // Save to storage
    this.saveToStorage();

    // Notify listeners
    this.notifyListeners({
      type: 'cart_cleared',
      cart: this.getCartState(),
    });
  }

  /**
   * Get cart items
   */
  public getItems(): CartItem[] {
    return [...this.items];
  }

  /**
   * Get item count
   */
  public getItemCount(): number {
    return this.items.reduce((total, item) => total + item.quantity, 0);
  }

  /**
   * Calculate subtotal
   */
  public getSubtotal(): number {
    return this.items.reduce((total, item) => total + item.price * item.quantity, 0);
  }

  /**
   * Calculate tax
   */
  public getTax(): number {
    return this.getSubtotal() * this.config.taxRate;
  }

  /**
   * Get shipping cost
   */
  public getShipping(): number {
    return this.config.shippingCost;
  }

  /**
   * Calculate total price
   */
  public getTotalPrice(): number {
    return this.getSubtotal() + this.getTax() + this.getShipping();
  }

  /**
   * Get complete cart state
   */
  public getCartState(): CartState {
    return {
      items: this.getItems(),
      subtotal: this.getSubtotal(),
      tax: this.getTax(),
      shipping: this.getShipping(),
      total: this.getTotalPrice(),
      currency: this.config.currency,
    };
  }

  /**
   * Check if cart is empty
   */
  public isEmpty(): boolean {
    return this.items.length === 0;
  }

  /**
   * Subscribe to cart events
   */
  public subscribe(callback: CartCallback): () => void {
    this.callbacks.add(callback);

    // Return unsubscribe function
    return () => {
      this.callbacks.delete(callback);
    };
  }

  /**
   * Notify all listeners
   */
  private notifyListeners(event: CartEvent): void {
    for (const callback of this.callbacks) {
      try {
        callback(event);
      } catch (error) {
        this.logger.error('Error in cart callback', error);
      }
    }
  }

  /**
   * Save cart to localStorage
   */
  private saveToStorage(): void {
    try {
      const data = {
        items: this.items,
        timestamp: Date.now(),
      };
      localStorage.setItem(this.config.storageKey, JSON.stringify(data));
    } catch (error) {
      this.logger.error('Failed to save cart to storage', error);
    }
  }

  /**
   * Load cart from localStorage
   */
  private loadFromStorage(): void {
    try {
      const data = localStorage.getItem(this.config.storageKey);
      if (data) {
        const parsed = JSON.parse(data);
        this.items = parsed.items || [];

        // Check if cart is older than 7 days
        const timestamp = parsed.timestamp || 0;
        const age = Date.now() - timestamp;
        const maxAge = 7 * 24 * 60 * 60 * 1000; // 7 days

        if (age > maxAge) {
          this.logger.info('Cart expired, clearing');
          this.clearCart();
        } else {
          this.logger.info(`Loaded ${this.items.length} items from storage`);
        }
      }
    } catch (error) {
      this.logger.error('Failed to load cart from storage', error);
      this.items = [];
    }
  }

  /**
   * Export cart for checkout
   */
  public exportForCheckout(): CartState {
    return this.getCartState();
  }

  /**
   * Set tax rate
   */
  public setTaxRate(rate: number): void {
    if (rate < 0 || rate > 1) {
      throw new Error('Tax rate must be between 0 and 1');
    }
    this.config.taxRate = rate;
    this.saveToStorage();
  }

  /**
   * Set shipping cost
   */
  public setShippingCost(cost: number): void {
    if (cost < 0) {
      throw new Error('Shipping cost cannot be negative');
    }
    this.config.shippingCost = cost;
    this.saveToStorage();
  }

  /**
   * Get configuration
   */
  public getConfig(): Required<CartConfig> {
    return { ...this.config };
  }
}

/**
 * Create a singleton cart manager instance
 */
let cartManagerInstance: CartManager | null = null;

export function getCartManager(config?: CartConfig): CartManager {
  if (!cartManagerInstance) {
    cartManagerInstance = new CartManager(config);
  }
  return cartManagerInstance;
}

export default CartManager;
