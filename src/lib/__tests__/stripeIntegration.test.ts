/**
 * Unit Tests for Stripe Integration
 * @jest-environment jsdom
 */

import {
  initializeStripe,
  createPaymentElements,
  handlePaymentResult,
  createPaymentIntent,
  validatePaymentForm,
  SKYYROSE_STRIPE_THEME,
} from '../stripeIntegration';
import type { Stripe, StripeElements, PaymentIntentResult } from '../stripeIntegration';

// --- Helpers ---

function createMockStripe(): Stripe {
  return {
    elements: jest.fn().mockReturnValue({
      create: jest.fn(),
      getElement: jest.fn(),
      submit: jest.fn(),
    }),
    confirmPayment: jest.fn(),
    retrievePaymentIntent: jest.fn(),
  };
}

function createMockElements(): StripeElements {
  return {
    create: jest.fn(),
    getElement: jest.fn(),
    submit: jest.fn(),
  };
}

// --- Tests ---

describe('Stripe Integration', () => {
  describe('SKYYROSE_STRIPE_THEME', () => {
    it('should use flat theme', () => {
      expect(SKYYROSE_STRIPE_THEME.theme).toBe('flat');
    });

    it('should use rose gold primary color', () => {
      expect(SKYYROSE_STRIPE_THEME.variables?.colorPrimary).toBe('#B76E79');
    });

    it('should have all required variables', () => {
      const vars = SKYYROSE_STRIPE_THEME.variables;
      expect(vars?.colorPrimary).toBeDefined();
      expect(vars?.colorBackground).toBeDefined();
      expect(vars?.colorText).toBeDefined();
      expect(vars?.colorDanger).toBeDefined();
      expect(vars?.fontFamily).toBeDefined();
      expect(vars?.spacingUnit).toBeDefined();
      expect(vars?.borderRadius).toBeDefined();
    });
  });

  describe('initializeStripe', () => {
    const originalStripe = (window as any).Stripe;

    afterEach(() => {
      if (originalStripe) {
        (window as any).Stripe = originalStripe;
      } else {
        delete (window as any).Stripe;
      }
    });

    it('should return null when Stripe.js is not loaded', () => {
      delete (window as any).Stripe;
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      const result = initializeStripe('pk_test_123');

      expect(result).toBeNull();
      consoleSpy.mockRestore();
    });

    it('should create Stripe instance when Stripe.js is loaded', () => {
      const mockStripeInstance = createMockStripe();
      (window as any).Stripe = jest.fn().mockReturnValue(mockStripeInstance);

      const result = initializeStripe('pk_test_123');

      expect(result).toBe(mockStripeInstance);
      expect((window as any).Stripe).toHaveBeenCalledWith('pk_test_123');
    });

    it('should return null when Stripe constructor throws', () => {
      (window as any).Stripe = jest.fn().mockImplementation(() => {
        throw new Error('Invalid key');
      });
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      const result = initializeStripe('bad_key');

      expect(result).toBeNull();
      consoleSpy.mockRestore();
    });
  });

  describe('createPaymentElements', () => {
    it('should create elements with default SkyyRose theme', () => {
      const stripe = createMockStripe();

      createPaymentElements(stripe, 'cs_test_secret');

      expect(stripe.elements).toHaveBeenCalledWith({
        clientSecret: 'cs_test_secret',
        appearance: SKYYROSE_STRIPE_THEME,
      });
    });

    it('should use custom appearance when provided', () => {
      const stripe = createMockStripe();
      const customAppearance = {
        theme: 'night' as const,
        variables: { colorPrimary: '#ff0000' },
      };

      createPaymentElements(stripe, 'cs_test_secret', customAppearance);

      expect(stripe.elements).toHaveBeenCalledWith({
        clientSecret: 'cs_test_secret',
        appearance: customAppearance,
      });
    });

    it('should return the elements instance', () => {
      const stripe = createMockStripe();
      const result = createPaymentElements(stripe, 'cs_test_secret');

      expect(result).toBeDefined();
      expect(result.create).toBeDefined();
      expect(result.getElement).toBeDefined();
      expect(result.submit).toBeDefined();
    });
  });

  describe('handlePaymentResult', () => {
    it('should return success for succeeded payment', () => {
      const result: PaymentIntentResult = {
        paymentIntent: {
          id: 'pi_123',
          client_secret: 'cs_test',
          amount: 9999,
          currency: 'usd',
          status: 'succeeded',
        },
      };

      const handled = handlePaymentResult(result);

      expect(handled.success).toBe(true);
      expect(handled.paymentIntentId).toBe('pi_123');
      expect(handled.error).toBeUndefined();
    });

    it('should return error for processing status', () => {
      const result: PaymentIntentResult = {
        paymentIntent: {
          id: 'pi_123',
          client_secret: 'cs_test',
          amount: 9999,
          currency: 'usd',
          status: 'processing',
        },
      };

      const handled = handlePaymentResult(result);

      expect(handled.success).toBe(false);
      expect(handled.error).toContain('processing');
    });

    it('should return error for requires_payment_method status', () => {
      const result: PaymentIntentResult = {
        paymentIntent: {
          id: 'pi_123',
          client_secret: 'cs_test',
          amount: 9999,
          currency: 'usd',
          status: 'requires_payment_method',
        },
      };

      const handled = handlePaymentResult(result);

      expect(handled.success).toBe(false);
      expect(handled.error).toContain('different payment method');
    });

    it('should return error for unexpected status', () => {
      const result: PaymentIntentResult = {
        paymentIntent: {
          id: 'pi_123',
          client_secret: 'cs_test',
          amount: 9999,
          currency: 'usd',
          status: 'requires_action',
        },
      };

      const handled = handlePaymentResult(result);

      expect(handled.success).toBe(false);
      expect(handled.error).toContain('Unexpected payment status');
    });

    it('should return error when result has error', () => {
      const result: PaymentIntentResult = {
        error: {
          type: 'card_error',
          code: 'card_declined',
          message: 'Your card was declined.',
          decline_code: 'generic_decline',
        },
      };

      const handled = handlePaymentResult(result);

      expect(handled.success).toBe(false);
      expect(handled.error).toBe('Your card was declined.');
    });

    it('should return unknown error when no paymentIntent and no error', () => {
      const result: PaymentIntentResult = {};

      const handled = handlePaymentResult(result);

      expect(handled.success).toBe(false);
      expect(handled.error).toContain('Unknown payment error');
    });
  });

  describe('createPaymentIntent', () => {
    const originalFetch = global.fetch;

    afterEach(() => {
      global.fetch = originalFetch;
    });

    it('should send correct request to backend', async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({ clientSecret: 'cs_test_abc' }),
      };
      global.fetch = jest.fn().mockResolvedValue(mockResponse);

      const cart = {
        items: [{ productId: 'p1', sku: 'SKU-1', name: 'Test', price: 99.99, quantity: 1 }],
        subtotal: 99.99,
        tax: 8.0,
        shipping: 5.0,
        total: 112.99,
        currency: 'USD',
      };

      const result = await createPaymentIntent(cart);

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/stripe/create-payment-intent',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.any(String),
        })
      );

      const body = JSON.parse((global.fetch as jest.Mock).mock.calls[0][1].body);
      expect(body.amount).toBe(11299); // cents
      expect(body.currency).toBe('usd');
      expect(result.clientSecret).toBe('cs_test_abc');
    });

    it('should handle API error response', async () => {
      const mockResponse = {
        ok: false,
        json: jest.fn().mockResolvedValue({ error: 'Invalid amount' }),
      };
      global.fetch = jest.fn().mockResolvedValue(mockResponse);

      const cart = {
        items: [],
        subtotal: 0,
        tax: 0,
        shipping: 0,
        total: 0,
        currency: 'USD',
      };

      const result = await createPaymentIntent(cart);

      expect(result.error).toBe('Invalid amount');
      expect(result.clientSecret).toBeUndefined();
    });

    it('should handle API error response without error message', async () => {
      const mockResponse = {
        ok: false,
        json: jest.fn().mockResolvedValue({}),
      };
      global.fetch = jest.fn().mockResolvedValue(mockResponse);

      const cart = {
        items: [],
        subtotal: 0,
        tax: 0,
        shipping: 0,
        total: 0,
        currency: 'USD',
      };

      const result = await createPaymentIntent(cart);

      expect(result.error).toBe('Failed to create payment intent');
    });

    it('should handle network errors', async () => {
      global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      const cart = {
        items: [],
        subtotal: 0,
        tax: 0,
        shipping: 0,
        total: 0,
        currency: 'USD',
      };

      const result = await createPaymentIntent(cart);

      expect(result.error).toContain('Network error');
      expect(result.clientSecret).toBeUndefined();
      consoleSpy.mockRestore();
    });
  });

  describe('validatePaymentForm', () => {
    it('should return valid for any elements', () => {
      const elements = createMockElements();
      const result = validatePaymentForm(elements);

      expect(result.valid).toBe(true);
      expect(result.errors).toEqual([]);
    });
  });
});
