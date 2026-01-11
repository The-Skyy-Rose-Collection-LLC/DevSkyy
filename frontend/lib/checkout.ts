/**
 * Checkout Manager
 * Orchestrates checkout flow, Stripe integration, and WooCommerce sync
 *
 * @author DevSkyy Platform Team
 * @version 1.0.0
 */

import type { CartState, CustomerInfo, Order } from '../types/product';
import type { Stripe, PaymentIntentResult } from './stripeIntegration';
import { initializeStripe, handlePaymentResult } from './stripeIntegration';

/**
 * Checkout configuration
 */
export interface CheckoutConfig {
  stripePublicKey: string;
  successUrl: string;
  cancelUrl: string;
  apiBaseUrl?: string;
  enableWooCommerceSync?: boolean;
}

/**
 * Checkout session data
 */
export interface CheckoutSessionData {
  sessionId: string;
  clientSecret: string;
  expiresAt: Date;
}

/**
 * WooCommerce order data
 */
export interface WooCommerceOrderData {
  payment_method: 'stripe';
  payment_method_title: string;
  set_paid: boolean;
  billing: {
    first_name: string;
    last_name: string;
    address_1: string;
    address_2?: string | undefined;
    city: string;
    state: string;
    postcode: string;
    country: string;
    email: string;
    phone?: string | undefined;
  };
  shipping: {
    first_name: string;
    last_name: string;
    address_1: string;
    address_2?: string | undefined;
    city: string;
    state: string;
    postcode: string;
    country: string;
  };
  line_items: Array<{
    product_id: number;
    quantity: number;
  }>;
  meta_data: Array<{
    key: string;
    value: string;
  }>;
}

/**
 * Checkout Manager Class
 * Handles the entire checkout flow from session creation to order completion
 */
export class CheckoutManager {
  private config: CheckoutConfig;
  private stripe: Stripe | null = null;

  constructor(config: CheckoutConfig) {
    this.config = config;
    this.stripe = initializeStripe(config.stripePublicKey);
  }

  /**
   * Create a Stripe checkout session
   * Option 1: Redirect to Stripe Checkout (hosted page)
   */
  async createCheckoutSession(cart: CartState): Promise<{
    sessionId?: string;
    error?: string;
  }> {
    try {
      const apiUrl = this.config.apiBaseUrl || '';
      const response = await fetch(`${apiUrl}/api/stripe/create-checkout-session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          cart,
          successUrl: this.config.successUrl,
          cancelUrl: this.config.cancelUrl,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        return {
          error: errorData.error || 'Failed to create checkout session',
        };
      }

      const data = await response.json();
      return {
        sessionId: data.sessionId,
      };
    } catch (error) {
      console.error('Error creating checkout session:', error);
      return {
        error: 'Network error. Please check your connection and try again.',
      };
    }
  }

  /**
   * Redirect to Stripe Checkout
   */
  async redirectToCheckout(sessionId: string): Promise<void> {
    if (!this.stripe) {
      throw new Error('Stripe not initialized');
    }

    // Save Three.js state before redirect
    this.saveThreeJsState();

    try {
      // Redirect to Stripe Checkout
      const result = await (this.stripe as any).redirectToCheckout({
        sessionId,
      });

      if (result.error) {
        throw new Error(result.error.message);
      }
    } catch (error) {
      console.error('Error redirecting to checkout:', error);
      throw error;
    }
  }

  /**
   * Process embedded payment using Stripe Elements
   * Option 2: Embedded checkout (modal)
   */
  async processPayment(
    elements: any, // StripeElements
    cart: CartState,
    customer: CustomerInfo
  ): Promise<{
    success: boolean;
    orderId?: string;
    error?: string;
  }> {
    if (!this.stripe) {
      return {
        success: false,
        error: 'Stripe not initialized',
      };
    }

    try {
      // Build address without undefined values
      const billingAddress: Record<string, string> = {
        line1: customer.billingAddress?.line1 || customer.shippingAddress.line1,
        city: customer.billingAddress?.city || customer.shippingAddress.city,
        state: customer.billingAddress?.state || customer.shippingAddress.state,
        postal_code: customer.billingAddress?.postalCode || customer.shippingAddress.postalCode,
        country: customer.billingAddress?.country || customer.shippingAddress.country,
      };
      const line2Value = customer.billingAddress?.line2 || customer.shippingAddress.line2;
      if (line2Value) billingAddress['line2'] = line2Value;

      // Build billing details without undefined values
      const billingDetails: Record<string, unknown> = {
        name: `${customer.firstName} ${customer.lastName}`,
        email: customer.email,
        address: billingAddress,
      };
      if (customer.phone) billingDetails['phone'] = customer.phone;

      // Confirm payment with Stripe
      const result: PaymentIntentResult = await this.stripe.confirmPayment({
        elements,
        confirmParams: {
          payment_method_data: {
            billing_details: billingDetails as {
              name?: string;
              email?: string;
              phone?: string;
              address?: Record<string, string>;
            },
          },
        },
        redirect: 'if_required',
      });

      // Handle payment result
      const paymentResult = handlePaymentResult(result);

      if (!paymentResult.success) {
        return {
          success: false,
          error: paymentResult.error ?? 'Payment failed',
        };
      }

      // Sync order to WooCommerce
      let wcOrderId: number | undefined;
      if (this.config.enableWooCommerceSync) {
        wcOrderId = await this.createWooCommerceOrder(
          cart,
          paymentResult.paymentIntentId!,
          customer
        );
      }

      // Create order record
      const order = await this.createOrder(cart, paymentResult.paymentIntentId!, customer, wcOrderId);

      return {
        success: true,
        orderId: order.orderId,
      };
    } catch (error) {
      console.error('Payment processing error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Payment failed',
      };
    }
  }

  /**
   * Create WooCommerce order via API
   */
  async createWooCommerceOrder(
    cart: CartState,
    stripePaymentId: string,
    customer: CustomerInfo
  ): Promise<number> {
    try {
      const apiUrl = this.config.apiBaseUrl || '';

      // Build WooCommerce order data
      const orderData: WooCommerceOrderData = {
        payment_method: 'stripe',
        payment_method_title: 'Credit Card (Stripe)',
        set_paid: true,
        billing: {
          first_name: customer.firstName,
          last_name: customer.lastName,
          address_1: customer.billingAddress?.line1 || customer.shippingAddress.line1,
          address_2: customer.billingAddress?.line2 || customer.shippingAddress.line2,
          city: customer.billingAddress?.city || customer.shippingAddress.city,
          state: customer.billingAddress?.state || customer.shippingAddress.state,
          postcode: customer.billingAddress?.postalCode || customer.shippingAddress.postalCode,
          country: customer.billingAddress?.country || customer.shippingAddress.country,
          email: customer.email,
          phone: customer.phone,
        },
        shipping: {
          first_name: customer.firstName,
          last_name: customer.lastName,
          address_1: customer.shippingAddress.line1,
          address_2: customer.shippingAddress.line2,
          city: customer.shippingAddress.city,
          state: customer.shippingAddress.state,
          postcode: customer.shippingAddress.postalCode,
          country: customer.shippingAddress.country,
        },
        line_items: cart.items.map((item) => ({
          product_id: parseInt(item.productId),
          quantity: item.quantity,
        })),
        meta_data: [
          {
            key: '_stripe_payment_intent_id',
            value: stripePaymentId,
          },
          {
            key: '_3d_collection_order',
            value: 'true',
          },
        ],
      };

      const response = await fetch(`${apiUrl}/api/woocommerce/orders`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData),
      });

      if (!response.ok) {
        throw new Error('Failed to create WooCommerce order');
      }

      const data = await response.json();
      return data.id;
    } catch (error) {
      console.error('Error creating WooCommerce order:', error);
      throw error;
    }
  }

  /**
   * Create order record in database
   */
  private async createOrder(
    cart: CartState,
    paymentIntentId: string,
    customer: CustomerInfo,
    wcOrderId?: number
  ): Promise<Order> {
    try {
      const apiUrl = this.config.apiBaseUrl || '';
      const response = await fetch(`${apiUrl}/api/orders`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          cart,
          customer,
          paymentIntentId,
          wcOrderId,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create order');
      }

      const order = await response.json();
      return order;
    } catch (error) {
      console.error('Error creating order:', error);
      throw error;
    }
  }

  /**
   * Save Three.js state before leaving page
   */
  private saveThreeJsState(): void {
    try {
      // Save camera position, scene state, etc.
      const state = {
        timestamp: Date.now(),
        // Additional state can be captured here
      };

      sessionStorage.setItem('threejs_state', JSON.stringify(state));
    } catch (error) {
      console.error('Error saving Three.js state:', error);
    }
  }

  /**
   * Restore Three.js state after returning from checkout.
   * Dispatches a custom event with saved state for scene components to handle.
   */
  restoreThreeJsState(): void {
    try {
      const stateJson = sessionStorage.getItem('threejs_state');
      if (!stateJson) return;

      const savedState = JSON.parse(stateJson) as {
        timestamp: number;
        cameraPosition?: { x: number; y: number; z: number };
        cameraTarget?: { x: number; y: number; z: number };
        selectedProduct?: string;
        sceneState?: Record<string, unknown>;
      };

      // Dispatch event for Three.js scene components to restore state
      const restoreEvent = new CustomEvent('threejs:restore', {
        detail: {
          savedState,
          timestamp: Date.now(),
        },
      });
      window.dispatchEvent(restoreEvent);

      // Log restoration for debugging
      console.debug('Three.js state restored:', {
        savedAt: new Date(savedState.timestamp).toISOString(),
        hasCamera: !!savedState.cameraPosition,
        hasProduct: !!savedState.selectedProduct,
      });

      // Clear saved state after restoration
      sessionStorage.removeItem('threejs_state');
    } catch (error) {
      console.error('Error restoring Three.js state:', error);
    }
  }

  /**
   * Show success animation (confetti)
   */
  showSuccessAnimation(): void {
    // This will be implemented by the SuccessCelebration component
    const event = new CustomEvent('checkout:success', {
      detail: {
        timestamp: Date.now(),
      },
    });
    window.dispatchEvent(event);
  }

  /**
   * Get checkout session status
   */
  async getSessionStatus(sessionId: string): Promise<{
    status: string;
    paymentStatus?: string;
    error?: string;
  }> {
    try {
      const apiUrl = this.config.apiBaseUrl || '';
      const response = await fetch(`${apiUrl}/api/stripe/session-status/${sessionId}`);

      if (!response.ok) {
        throw new Error('Failed to get session status');
      }

      const data = await response.json();
      return {
        status: data.status,
        paymentStatus: data.payment_status,
      };
    } catch (error) {
      console.error('Error getting session status:', error);
      return {
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }
}

/**
 * Create default checkout manager instance
 */
export function createCheckoutManager(config: CheckoutConfig): CheckoutManager {
  return new CheckoutManager(config);
}
