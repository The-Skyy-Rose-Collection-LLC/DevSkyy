/**
 * Unit Tests for CheckoutManager
 * @jest-environment jsdom
 */

import { CheckoutManager, createCheckoutManager } from '../checkout';
import { handlePaymentResult, initializeStripe } from '../stripeIntegration';

// Mock stripeIntegration
jest.mock('../stripeIntegration', () => ({
  initializeStripe: jest.fn().mockReturnValue(null),
  handlePaymentResult: jest.fn().mockReturnValue({ success: true, paymentIntentId: 'pi_test' }),
}));

const mockCart = {
  items: [{ productId: '123', sku: 'SKU-1', name: 'Test', price: 100, quantity: 1 }],
  subtotal: 100,
  tax: 8,
  shipping: 0,
  total: 108,
  currency: 'USD',
};

const mockCustomer = {
  email: 'test@example.com',
  firstName: 'John',
  lastName: 'Doe',
  phone: '555-1234',
  shippingAddress: {
    line1: '123 Main St',
    line2: 'Apt 4',
    city: 'NYC',
    state: 'NY',
    postalCode: '10001',
    country: 'US',
  },
  billingAddress: {
    line1: '456 Billing Ave',
    line2: 'Suite 100',
    city: 'Brooklyn',
    state: 'NY',
    postalCode: '11201',
    country: 'US',
  },
};

const mockCustomerNoBilling = {
  email: 'test@example.com',
  firstName: 'John',
  lastName: 'Doe',
  shippingAddress: {
    line1: '123 Main St',
    city: 'NYC',
    state: 'NY',
    postalCode: '10001',
    country: 'US',
  },
};

const defaultConfig = {
  stripePublicKey: 'pk_test_123',
  successUrl: 'https://example.com/success',
  cancelUrl: 'https://example.com/cancel',
};

describe('CheckoutManager', () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    jest.restoreAllMocks();
  });

  describe('createCheckoutSession', () => {
    it('should create a checkout session', async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue({ sessionId: 'sess_123' }),
      });

      const mgr = new CheckoutManager(defaultConfig);
      const result = await mgr.createCheckoutSession(mockCart);

      expect(result.sessionId).toBe('sess_123');
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/stripe/create-checkout-session',
        expect.objectContaining({ method: 'POST' })
      );
    });

    it('should use apiBaseUrl when configured', async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue({ sessionId: 'sess_123' }),
      });

      const mgr = new CheckoutManager({ ...defaultConfig, apiBaseUrl: 'https://api.test' });
      await mgr.createCheckoutSession(mockCart);

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.test/api/stripe/create-checkout-session',
        expect.any(Object)
      );
    });

    it('should handle API error', async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        json: jest.fn().mockResolvedValue({ error: 'Bad request' }),
      });

      const mgr = new CheckoutManager(defaultConfig);
      const result = await mgr.createCheckoutSession(mockCart);

      expect(result.error).toBe('Bad request');
    });

    it('should handle API error without message', async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        json: jest.fn().mockResolvedValue({}),
      });

      const mgr = new CheckoutManager(defaultConfig);
      const result = await mgr.createCheckoutSession(mockCart);

      expect(result.error).toBe('Failed to create checkout session');
    });

    it('should handle network error', async () => {
      global.fetch = jest.fn().mockRejectedValue(new Error('Network'));
      jest.spyOn(console, 'error').mockImplementation();

      const mgr = new CheckoutManager(defaultConfig);
      const result = await mgr.createCheckoutSession(mockCart);

      expect(result.error).toContain('Network error');
    });
  });

  describe('redirectToCheckout', () => {
    it('should throw when stripe not initialized', async () => {
      const mgr = new CheckoutManager(defaultConfig);
      await expect(mgr.redirectToCheckout('sess_123')).rejects.toThrow('Stripe not initialized');
    });

    it('should redirect when stripe is initialized', async () => {
      const mockRedirect = jest.fn().mockResolvedValue({});
      (initializeStripe).mockReturnValue({
        redirectToCheckout: mockRedirect,
        confirmPayment: jest.fn(),
      });

      const mgr = new CheckoutManager(defaultConfig);
      await mgr.redirectToCheckout('sess_123');

      expect(mockRedirect).toHaveBeenCalledWith({ sessionId: 'sess_123' });
    });

    it('should throw when redirect returns error', async () => {
      const mockRedirect = jest.fn().mockResolvedValue({ error: { message: 'Session expired' } });
      (initializeStripe).mockReturnValue({
        redirectToCheckout: mockRedirect,
        confirmPayment: jest.fn(),
      });

      jest.spyOn(console, 'error').mockImplementation();
      const mgr = new CheckoutManager(defaultConfig);
      await expect(mgr.redirectToCheckout('sess_123')).rejects.toThrow('Session expired');
    });

    it('should save Three.js state before redirect', async () => {
      const mockRedirect = jest.fn().mockResolvedValue({});
      (initializeStripe).mockReturnValue({
        redirectToCheckout: mockRedirect,
        confirmPayment: jest.fn(),
      });

      const mgr = new CheckoutManager(defaultConfig);
      await mgr.redirectToCheckout('sess_123');

      const saved = sessionStorage.getItem('threejs_state');
      expect(saved).not.toBeNull();
      const parsed = JSON.parse(saved);
      expect(parsed.timestamp).toBeDefined();
    });
  });

  describe('processPayment', () => {
    it('should return error when stripe not initialized', async () => {
      (initializeStripe).mockReturnValue(null);
      const mgr = new CheckoutManager(defaultConfig);
      const result = await mgr.processPayment({}, mockCart, mockCustomerNoBilling);
      expect(result.success).toBe(false);
      expect(result.error).toContain('Stripe not initialized');
    });

    it('should process payment successfully', async () => {
      const mockConfirmPayment = jest.fn().mockResolvedValue({
        paymentIntent: { id: 'pi_success', status: 'succeeded' },
      });
      (initializeStripe).mockReturnValue({ confirmPayment: mockConfirmPayment });
      (handlePaymentResult).mockReturnValue({ success: true, paymentIntentId: 'pi_success' });

      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue({ orderId: 'order-1' }),
      });

      const mgr = new CheckoutManager(defaultConfig);
      const result = await mgr.processPayment({}, mockCart, mockCustomerNoBilling);

      expect(result.success).toBe(true);
      expect(result.orderId).toBe('order-1');
    });

    it('should process payment with billing address and phone', async () => {
      const mockConfirmPayment = jest.fn().mockResolvedValue({
        paymentIntent: { id: 'pi_success', status: 'succeeded' },
      });
      (initializeStripe).mockReturnValue({ confirmPayment: mockConfirmPayment });
      (handlePaymentResult).mockReturnValue({ success: true, paymentIntentId: 'pi_success' });

      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue({ orderId: 'order-2' }),
      });

      const mgr = new CheckoutManager(defaultConfig);
      const result = await mgr.processPayment({}, mockCart, mockCustomer);

      expect(result.success).toBe(true);
      // Verify billing address was used in confirmPayment call
      const confirmArgs = mockConfirmPayment.mock.calls[0][0];
      expect(confirmArgs.confirmParams.payment_method_data.billing_details.phone).toBe('555-1234');
      expect(confirmArgs.confirmParams.payment_method_data.billing_details.address.line1).toBe('456 Billing Ave');
      expect(confirmArgs.confirmParams.payment_method_data.billing_details.address.line2).toBe('Suite 100');
    });

    it('should sync to WooCommerce when enabled', async () => {
      const mockConfirmPayment = jest.fn().mockResolvedValue({
        paymentIntent: { id: 'pi_wc', status: 'succeeded' },
      });
      (initializeStripe).mockReturnValue({ confirmPayment: mockConfirmPayment });
      (handlePaymentResult).mockReturnValue({ success: true, paymentIntentId: 'pi_wc' });

      global.fetch = jest.fn()
        .mockResolvedValueOnce({ ok: true, json: jest.fn().mockResolvedValue({ id: 789 }) }) // WC order
        .mockResolvedValueOnce({ ok: true, json: jest.fn().mockResolvedValue({ orderId: 'order-wc' }) }); // Order record

      const mgr = new CheckoutManager({ ...defaultConfig, enableWooCommerceSync: true });
      const result = await mgr.processPayment({}, mockCart, mockCustomerNoBilling);

      expect(result.success).toBe(true);
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    it('should return error when payment fails', async () => {
      const mockConfirmPayment = jest.fn().mockResolvedValue({
        error: { message: 'Card declined' },
      });
      (initializeStripe).mockReturnValue({ confirmPayment: mockConfirmPayment });
      (handlePaymentResult).mockReturnValue({ success: false, error: 'Card declined' });

      const mgr = new CheckoutManager(defaultConfig);
      const result = await mgr.processPayment({}, mockCart, mockCustomerNoBilling);

      expect(result.success).toBe(false);
      expect(result.error).toBe('Card declined');
    });

    it('should return default error when payment result has no error message', async () => {
      const mockConfirmPayment = jest.fn().mockResolvedValue({});
      (initializeStripe).mockReturnValue({ confirmPayment: mockConfirmPayment });
      (handlePaymentResult).mockReturnValue({ success: false });

      const mgr = new CheckoutManager(defaultConfig);
      const result = await mgr.processPayment({}, mockCart, mockCustomerNoBilling);

      expect(result.success).toBe(false);
      expect(result.error).toBe('Payment failed');
    });

    it('should handle exception during payment', async () => {
      const mockConfirmPayment = jest.fn().mockRejectedValue(new Error('Network timeout'));
      (initializeStripe).mockReturnValue({ confirmPayment: mockConfirmPayment });

      jest.spyOn(console, 'error').mockImplementation();
      const mgr = new CheckoutManager(defaultConfig);
      const result = await mgr.processPayment({}, mockCart, mockCustomerNoBilling);

      expect(result.success).toBe(false);
      expect(result.error).toBe('Network timeout');
    });

    it('should handle non-Error exception during payment', async () => {
      const mockConfirmPayment = jest.fn().mockRejectedValue('string error');
      (initializeStripe).mockReturnValue({ confirmPayment: mockConfirmPayment });

      jest.spyOn(console, 'error').mockImplementation();
      const mgr = new CheckoutManager(defaultConfig);
      const result = await mgr.processPayment({}, mockCart, mockCustomerNoBilling);

      expect(result.success).toBe(false);
      expect(result.error).toBe('Payment failed');
    });
  });

  describe('createWooCommerceOrder', () => {
    it('should create WooCommerce order', async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue({ id: 456 }),
      });

      const mgr = new CheckoutManager({ ...defaultConfig, apiBaseUrl: 'https://api.test' });
      const orderId = await mgr.createWooCommerceOrder(mockCart, 'pi_test', mockCustomer);

      expect(orderId).toBe(456);
      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.test/api/woocommerce/orders',
        expect.objectContaining({ method: 'POST' })
      );
    });

    it('should throw on API failure', async () => {
      global.fetch = jest.fn().mockResolvedValue({ ok: false });
      jest.spyOn(console, 'error').mockImplementation();

      const mgr = new CheckoutManager(defaultConfig);
      await expect(mgr.createWooCommerceOrder(mockCart, 'pi_test', mockCustomer)).rejects.toThrow(
        'Failed to create WooCommerce order'
      );
    });

    it('should throw on network error', async () => {
      global.fetch = jest.fn().mockRejectedValue(new Error('Connection refused'));
      jest.spyOn(console, 'error').mockImplementation();

      const mgr = new CheckoutManager(defaultConfig);
      await expect(mgr.createWooCommerceOrder(mockCart, 'pi_test', mockCustomer)).rejects.toThrow(
        'Connection refused'
      );
    });

    it('should include stripe payment ID and billing/shipping data', async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue({ id: 100 }),
      });

      const mgr = new CheckoutManager(defaultConfig);
      await mgr.createWooCommerceOrder(mockCart, 'pi_stripe_123', mockCustomer);

      const body = JSON.parse(global.fetch.mock.calls[0][1].body);
      expect(body.payment_method).toBe('stripe');
      expect(body.billing.email).toBe('test@example.com');
      expect(body.billing.first_name).toBe('John');
      expect(body.shipping.address_1).toBe('123 Main St');
      expect(body.meta_data[0].value).toBe('pi_stripe_123');
      expect(body.line_items[0].product_id).toBe(123);
    });
  });

  describe('restoreThreeJsState', () => {
    it('should dispatch event when state exists', () => {
      const state = { timestamp: Date.now() };
      sessionStorage.setItem('threejs_state', JSON.stringify(state));
      const spy = jest.spyOn(window, 'dispatchEvent');
      jest.spyOn(console, 'debug').mockImplementation();

      const mgr = new CheckoutManager(defaultConfig);
      mgr.restoreThreeJsState();

      expect(spy).toHaveBeenCalledWith(expect.objectContaining({ type: 'threejs:restore' }));
      expect(sessionStorage.getItem('threejs_state')).toBeNull();
    });

    it('should do nothing when no saved state', () => {
      sessionStorage.clear();
      const spy = jest.spyOn(window, 'dispatchEvent');

      const mgr = new CheckoutManager(defaultConfig);
      mgr.restoreThreeJsState();

      expect(spy).not.toHaveBeenCalled();
    });

    it('should handle corrupt state gracefully', () => {
      sessionStorage.setItem('threejs_state', 'not json');
      jest.spyOn(console, 'error').mockImplementation();

      const mgr = new CheckoutManager(defaultConfig);
      expect(() => mgr.restoreThreeJsState()).not.toThrow();
    });
  });

  describe('showSuccessAnimation', () => {
    it('should dispatch checkout:success event', () => {
      const spy = jest.spyOn(window, 'dispatchEvent');

      const mgr = new CheckoutManager(defaultConfig);
      mgr.showSuccessAnimation();

      expect(spy).toHaveBeenCalledWith(expect.objectContaining({ type: 'checkout:success' }));
    });
  });

  describe('getSessionStatus', () => {
    it('should fetch session status', async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue({ status: 'complete', payment_status: 'paid' }),
      });

      const mgr = new CheckoutManager(defaultConfig);
      const result = await mgr.getSessionStatus('sess_123');

      expect(result.status).toBe('complete');
      expect(result.paymentStatus).toBe('paid');
    });

    it('should handle fetch error', async () => {
      global.fetch = jest.fn().mockResolvedValue({ ok: false });
      jest.spyOn(console, 'error').mockImplementation();

      const mgr = new CheckoutManager(defaultConfig);
      const result = await mgr.getSessionStatus('sess_123');

      expect(result.status).toBe('error');
      expect(result.error).toBeDefined();
    });

    it('should handle network error', async () => {
      global.fetch = jest.fn().mockRejectedValue(new Error('Timeout'));
      jest.spyOn(console, 'error').mockImplementation();

      const mgr = new CheckoutManager(defaultConfig);
      const result = await mgr.getSessionStatus('sess_123');

      expect(result.status).toBe('error');
      expect(result.error).toBe('Timeout');
    });
  });

  describe('createCheckoutManager', () => {
    it('should return a CheckoutManager instance', () => {
      const mgr = createCheckoutManager(defaultConfig);
      expect(mgr).toBeInstanceOf(CheckoutManager);
    });
  });
});
