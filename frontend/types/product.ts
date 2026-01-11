/**
 * Product Types for 3D Collections
 * Extended product interfaces for e-commerce integration
 *
 * @author DevSkyy Platform Team
 * @version 1.0.0
 */

/**
 * Stock status enumeration
 */
export type StockStatus = 'in_stock' | 'low_stock' | 'out_of_stock';

/**
 * Product color variant
 */
export interface ProductColor {
  name: string;
  hex: string;
}

/**
 * Extended product interface for 3D showroom with e-commerce capabilities
 */
export interface ShowroomProduct {
  // Core 3D properties
  id: string;
  name: string;
  modelUrl: string;
  position: [number, number, number];
  rotation?: [number, number, number];
  scale?: [number, number, number];
  spotlightColor?: number;

  // E-commerce properties
  sku: string;
  price: number;
  salePrice?: number;
  stockStatus: StockStatus;
  stockQuantity: number;
  sizes: string[];
  colors: ProductColor[];
  wcProductId?: number;  // WooCommerce product ID

  // Optional metadata
  description?: string;
  category?: string;
  tags?: string[];
  images?: string[];
}

/**
 * Inventory status interface
 */
export interface InventoryStatus {
  productId: string;
  stockStatus: StockStatus;
  stockQuantity: number;
  reservedQuantity: number;
  lastUpdated?: Date;
}

/**
 * Cart item interface
 */
export interface CartItem {
  productId: string;
  sku: string;
  name: string;
  price: number;
  quantity: number;
  size?: string | undefined;
  color?: ProductColor | undefined;
  imageUrl?: string | undefined;
}

/**
 * Product interaction event
 */
export interface ProductInteractionEvent {
  type: 'hover' | 'click' | 'add_to_cart' | 'view_details';
  productId: string;
  timestamp: Date;
  metadata?: Record<string, unknown>;
}

/**
 * Cart state interface
 */
export interface CartState {
  items: CartItem[];
  subtotal: number;
  tax: number;
  shipping: number;
  total: number;
  currency: string;
}

/**
 * Customer information for checkout
 */
export interface CustomerInfo {
  email: string;
  firstName: string;
  lastName: string;
  phone?: string | undefined;
  shippingAddress: Address;
  billingAddress?: Address | undefined;
  sameAsBilling?: boolean | undefined;
}

/**
 * Address interface
 */
export interface Address {
  line1: string;
  line2?: string | undefined;
  city: string;
  state: string;
  postalCode: string;
  country: string;
}

/**
 * Checkout session interface
 */
export interface CheckoutSession {
  id: string;
  sessionId: string;
  cart: CartState;
  customer: CustomerInfo;
  paymentIntentId?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  createdAt: Date;
  expiresAt: Date;
}

/**
 * Order interface
 */
export interface Order {
  id: string;
  orderId: string;
  wcOrderId?: number;
  cart: CartState;
  customer: CustomerInfo;
  paymentIntentId: string;
  status: 'processing' | 'completed' | 'failed' | 'refunded';
  createdAt: Date;
  completedAt?: Date;
}
