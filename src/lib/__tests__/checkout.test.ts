/**
 * Unit Tests for CheckoutManager
 * @jest-environment jsdom
 */

import { CheckoutManager, createCheckoutManager } from '../checkout';

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
  });

  describe('processPayment', () => {
    it('should return error when stripe not initialized', async () => {
      const mgr = new CheckoutManager(defaultConfig);
      const result = await mgr.processPayment({}, mockCart, mockCustomer);
      expect(result.success).toBe(false);
      expect(result.error).toContain('Stripe not initialized');
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
