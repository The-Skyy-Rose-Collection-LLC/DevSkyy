/**
 * Unit Tests for AR Configuration
 * @jest-environment jsdom
 */

import { AR_CONFIG, COLLECTION_AR_SETTINGS, detectARCapabilities, ARApiClient } from '../ar';

describe('AR_CONFIG', () => {
  it('should have all required fields', () => {
    expect(AR_CONFIG.apiBaseUrl).toBeDefined();
    expect(AR_CONFIG.tryOnEndpoint).toBe('/api/v1/virtual-tryon');
    expect(AR_CONFIG.sessionsEndpoint).toBe('/api/v1/ar/sessions');
    expect(AR_CONFIG.productsEndpoint).toBe('/api/v1/ar/products');
    expect(AR_CONFIG.maxRetries).toBe(3);
    expect(AR_CONFIG.timeout).toBe(30000);
  });

  it('should have 3 collections', () => {
    expect(AR_CONFIG.collections).toHaveLength(3);
    expect(AR_CONFIG.collections).toContain('black_rose');
    expect(AR_CONFIG.collections).toContain('love_hurts');
    expect(AR_CONFIG.collections).toContain('signature');
  });

  it('should have websocket URL derived from API base', () => {
    expect(AR_CONFIG.websocketUrl).toContain('/api/v1/ar/ws');
  });
});

describe('COLLECTION_AR_SETTINGS', () => {
  it('should have settings for all 3 collections', () => {
    expect(COLLECTION_AR_SETTINGS['black_rose']).toBeDefined();
    expect(COLLECTION_AR_SETTINGS['love_hurts']).toBeDefined();
    expect(COLLECTION_AR_SETTINGS['signature']).toBeDefined();
  });

  it.each(['black_rose', 'love_hurts', 'signature'])('%s should have required fields', (collection) => {
    const settings = COLLECTION_AR_SETTINGS[collection]!;
    expect(settings.collection).toBe(collection);
    expect(typeof settings.accentColor).toBe('number');
    expect(typeof settings.ambientIntensity).toBe('number');
    expect(typeof settings.bloomStrength).toBe('number');
    expect(typeof settings.particleCount).toBe('number');
    expect(typeof settings.tryOnCategory).toBe('string');
  });

  it('black_rose should have dark red accent', () => {
    expect(COLLECTION_AR_SETTINGS['black_rose']!.accentColor).toBe(0x8b0000);
  });

  it('signature should have rose gold accent', () => {
    expect(COLLECTION_AR_SETTINGS['signature']!.accentColor).toBe(0xb76e79);
  });
});

describe('detectARCapabilities', () => {
  const originalNavigator = global.navigator;

  afterEach(() => {
    Object.defineProperty(global, 'navigator', { value: originalNavigator, writable: true });
  });

  it('should return preview mode when no AR support', async () => {
    const result = await detectARCapabilities();
    expect(result.recommendedMode).toBe('preview');
  });

  it('should detect webcam support', async () => {
    Object.defineProperty(global, 'navigator', {
      value: {
        ...originalNavigator,
        mediaDevices: {
          enumerateDevices: jest.fn().mockResolvedValue([
            { kind: 'videoinput', deviceId: 'cam1', label: 'Camera', groupId: 'g1', toJSON: jest.fn() },
          ]),
        },
      },
      writable: true,
    });

    const result = await detectARCapabilities();
    expect(result.webcamSupported).toBe(true);
    expect(result.recommendedMode).toBe('webcam');
  });

  it('should handle webcam detection errors', async () => {
    Object.defineProperty(global, 'navigator', {
      value: {
        ...originalNavigator,
        mediaDevices: {
          enumerateDevices: jest.fn().mockRejectedValue(new Error('Not allowed')),
        },
      },
      writable: true,
    });

    const result = await detectARCapabilities();
    expect(result.webcamSupported).toBe(false);
  });
});

describe('ARApiClient', () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
  });

  describe('createSession', () => {
    it('should create a session and return ID', async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue({ session_id: 'sess_abc' }),
      });

      const client = new ARApiClient();
      const id = await client.createSession('black_rose');

      expect(id).toBe('sess_abc');
      expect(client.getSessionId()).toBe('sess_abc');
    });

    it('should throw on API failure', async () => {
      global.fetch = jest.fn().mockResolvedValue({ ok: false, statusText: 'Server Error' });

      const client = new ARApiClient();
      await expect(client.createSession('black_rose')).rejects.toThrow('Failed to create AR session');
    });
  });

  describe('getProducts', () => {
    it('should fetch products for collection', async () => {
      const products = [{ id: 'p1', name: 'Test' }];
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue(products),
      });

      const client = new ARApiClient();
      const result = await client.getProducts('signature');

      expect(result).toEqual(products);
    });

    it('should throw on failure', async () => {
      global.fetch = jest.fn().mockResolvedValue({ ok: false, statusText: 'Not Found' });

      const client = new ARApiClient();
      await expect(client.getProducts('bad')).rejects.toThrow('Failed to fetch AR products');
    });
  });

  describe('recordTryOn', () => {
    it('should skip when no session', async () => {
      jest.spyOn(console, 'warn').mockImplementation();
      global.fetch = jest.fn();

      const client = new ARApiClient();
      await client.recordTryOn('p1');

      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('should record try-on with session', async () => {
      global.fetch = jest.fn()
        .mockResolvedValueOnce({ ok: true, json: jest.fn().mockResolvedValue({ session_id: 's1' }) })
        .mockResolvedValueOnce({ ok: true });

      const client = new ARApiClient();
      await client.createSession('black_rose');
      await client.recordTryOn('p1', true, 5000);

      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('submitTryOn', () => {
    it('should submit try-on request', async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue({ job_id: 'job_1' }),
      });

      const client = new ARApiClient();
      const result = await client.submitTryOn('model.jpg', 'garment.jpg', 'tops');

      expect(result.job_id).toBe('job_1');
    });

    it('should throw on failure', async () => {
      global.fetch = jest.fn().mockResolvedValue({ ok: false, statusText: 'Error' });

      const client = new ARApiClient();
      await expect(client.submitTryOn('a', 'b')).rejects.toThrow('Try-on request failed');
    });
  });

  describe('getTryOnStatus', () => {
    it('should get job status', async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue({ status: 'completed' }),
      });

      const client = new ARApiClient();
      const result = await client.getTryOnStatus('job_1');

      expect(result.status).toBe('completed');
    });

    it('should throw on failure', async () => {
      global.fetch = jest.fn().mockResolvedValue({ ok: false, statusText: 'Not Found' });

      const client = new ARApiClient();
      await expect(client.getTryOnStatus('bad')).rejects.toThrow('Failed to get try-on status');
    });
  });

  describe('endSession', () => {
    it('should do nothing when no session', async () => {
      global.fetch = jest.fn();
      const client = new ARApiClient();
      await client.endSession();
      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('should end session and clear ID', async () => {
      global.fetch = jest.fn()
        .mockResolvedValueOnce({ ok: true, json: jest.fn().mockResolvedValue({ session_id: 's1' }) })
        .mockResolvedValueOnce({ ok: true });

      const client = new ARApiClient();
      await client.createSession('signature');
      expect(client.getSessionId()).toBe('s1');

      await client.endSession(true);
      expect(client.getSessionId()).toBeNull();
    });
  });
});
