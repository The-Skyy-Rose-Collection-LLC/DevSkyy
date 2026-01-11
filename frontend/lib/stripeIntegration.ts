/**
 * Stripe Integration Library
 * Handles Stripe Elements, payment processing, and webhook handling
 *
 * @author DevSkyy Platform Team
 * @version 1.0.0
 */

import type { CartState } from '../types/product';

/**
 * Stripe instance type (loaded from Stripe.js)
 */
export interface Stripe {
  elements: (options: StripeElementsOptions) => StripeElements;
  confirmPayment: (options: ConfirmPaymentOptions) => Promise<PaymentIntentResult>;
  retrievePaymentIntent: (clientSecret: string) => Promise<PaymentIntentResult>;
}

/**
 * Stripe Elements options
 */
export interface StripeElementsOptions {
  clientSecret: string;
  appearance?: {
    theme?: 'stripe' | 'night' | 'flat';
    variables?: {
      colorPrimary?: string;
      colorBackground?: string;
      colorText?: string;
      colorDanger?: string;
      fontFamily?: string;
      spacingUnit?: string;
      borderRadius?: string;
    };
  };
}

/**
 * Stripe Elements instance
 */
export interface StripeElements {
  create: (type: string, options?: Record<string, unknown>) => StripeElement;
  getElement: (type: string) => StripeElement | null;
  submit: () => Promise<{ error?: StripeError }>;
}

/**
 * Individual Stripe Element (e.g., card, payment)
 */
export interface StripeElement {
  mount: (selector: string | HTMLElement) => void;
  unmount: () => void;
  on: (event: string, handler: (event: StripeElementEvent) => void) => void;
  off: (event: string, handler?: (event: StripeElementEvent) => void) => void;
  update: (options: Record<string, unknown>) => void;
}

/**
 * Stripe Element event
 */
export interface StripeElementEvent {
  elementType: string;
  empty: boolean;
  complete: boolean;
  error?: StripeError;
}

/**
 * Stripe error object
 */
export interface StripeError {
  type: string;
  code?: string;
  message: string;
  decline_code?: string;
  param?: string;
}

/**
 * Confirm payment options
 */
export interface ConfirmPaymentOptions {
  elements: StripeElements;
  confirmParams: {
    return_url?: string;
    payment_method_data?: {
      billing_details?: {
        name?: string;
        email?: string;
        phone?: string;
        address?: {
          line1?: string;
          line2?: string;
          city?: string;
          state?: string;
          postal_code?: string;
          country?: string;
        };
      };
    };
  };
  redirect?: 'if_required' | 'always';
}

/**
 * Payment intent result
 */
export interface PaymentIntentResult {
  paymentIntent?: {
    id: string;
    client_secret: string;
    amount: number;
    currency: string;
    status: string;
    payment_method?: string;
  };
  error?: StripeError;
}

/**
 * SkyyRose brand theme for Stripe Elements
 */
export const SKYYROSE_STRIPE_THEME: NonNullable<StripeElementsOptions['appearance']> = {
  theme: 'flat',
  variables: {
    colorPrimary: '#B76E79',
    colorBackground: '#FFFFFF',
    colorText: '#1A1A1A',
    colorDanger: '#DF1B41',
    fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    spacingUnit: '4px',
    borderRadius: '8px',
  },
};

/**
 * Initialize Stripe with public key
 */
export function initializeStripe(publicKey: string): Stripe | null {
  if (typeof window === 'undefined') {
    console.warn('Stripe can only be initialized in browser environment');
    return null;
  }

  // Check if Stripe.js is loaded
  if (!(window as any).Stripe) {
    console.error('Stripe.js not loaded. Add <script src="https://js.stripe.com/v3/"></script> to your HTML');
    return null;
  }

  try {
    const stripe = (window as any).Stripe(publicKey);
    return stripe;
  } catch (error) {
    console.error('Failed to initialize Stripe:', error);
    return null;
  }
}

/**
 * Create Stripe Elements with SkyyRose branding
 */
export function createPaymentElements(
  stripe: Stripe,
  clientSecret: string,
  customAppearance?: StripeElementsOptions['appearance']
): StripeElements {
  const appearance = customAppearance ?? SKYYROSE_STRIPE_THEME;

  const elementsOptions: { clientSecret: string; appearance: NonNullable<StripeElementsOptions['appearance']> } = {
    clientSecret,
    appearance,
  };

  const elements = stripe.elements(elementsOptions);

  return elements;
}

/**
 * Handle payment result and return normalized response
 */
export function handlePaymentResult(result: PaymentIntentResult): {
  success: boolean;
  error?: string;
  paymentIntentId?: string;
} {
  if (result.error) {
    return {
      success: false,
      error: result.error.message,
    };
  }

  if (result.paymentIntent) {
    const { status, id } = result.paymentIntent;

    if (status === 'succeeded') {
      return {
        success: true,
        paymentIntentId: id,
      };
    }

    if (status === 'processing') {
      return {
        success: false,
        error: 'Payment is processing. Please wait...',
      };
    }

    if (status === 'requires_payment_method') {
      return {
        success: false,
        error: 'Payment failed. Please try a different payment method.',
      };
    }

    return {
      success: false,
      error: `Unexpected payment status: ${status}`,
    };
  }

  return {
    success: false,
    error: 'Unknown payment error occurred',
  };
}

/**
 * Create payment intent via backend API
 */
export async function createPaymentIntent(cart: CartState): Promise<{
  clientSecret?: string;
  error?: string;
}> {
  try {
    const response = await fetch('/api/stripe/create-payment-intent', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        amount: Math.round(cart.total * 100), // Convert to cents
        currency: cart.currency.toLowerCase(),
        items: cart.items,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      return {
        error: errorData.error || 'Failed to create payment intent',
      };
    }

    const data = await response.json();
    return {
      clientSecret: data.clientSecret,
    };
  } catch (error) {
    console.error('Error creating payment intent:', error);
    return {
      error: 'Network error. Please check your connection and try again.',
    };
  }
}

/**
 * Validate payment form before submission
 */
export function validatePaymentForm(_elements: StripeElements): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  // Elements will handle validation internally via _elements
  // This is a placeholder for additional custom validation if needed

  return {
    valid: errors.length === 0,
    errors,
  };
}
