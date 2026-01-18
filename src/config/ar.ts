/**
 * AR Configuration for SkyyRose Collection Experiences
 *
 * Centralizes all AR-related configuration including:
 * - API endpoints
 * - Feature flags
 * - Collection-specific settings
 * - Performance tuning
 *
 * @author DevSkyy Platform Team
 * @version 1.0.0
 */

export interface ARConfig {
  apiBaseUrl: string;
  tryOnEndpoint: string;
  sessionsEndpoint: string;
  productsEndpoint: string;
  websocketUrl: string;
  maxRetries: number;
  timeout: number;
  collections: readonly string[];
}

export interface CollectionARSettings {
  collection: string;
  accentColor: number;
  ambientIntensity: number;
  bloomStrength: number;
  particleCount: number;
  tryOnCategory: string;
}

// Environment-based configuration
const getApiBaseUrl = (): string => {
  if (typeof process !== 'undefined' && process.env?.['VITE_API_BASE_URL']) {
    return process.env['VITE_API_BASE_URL'] as string;
  }
  return 'http://localhost:8000';
};

const API_BASE_URL = getApiBaseUrl();
const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws');

/**
 * Main AR configuration
 */
export const AR_CONFIG: ARConfig = {
  apiBaseUrl: API_BASE_URL,
  tryOnEndpoint: '/api/v1/virtual-tryon',
  sessionsEndpoint: '/api/v1/ar/sessions',
  productsEndpoint: '/api/v1/ar/products',
  websocketUrl: `${WS_BASE_URL}/api/v1/ar/ws`,
  maxRetries: 3,
  timeout: 30000,
  collections: ['black_rose', 'love_hurts', 'signature'] as const,
};

/**
 * Collection-specific AR settings
 */
export const COLLECTION_AR_SETTINGS: Record<string, CollectionARSettings> = {
  black_rose: {
    collection: 'black_rose',
    accentColor: 0x8b0000,  // Dark red
    ambientIntensity: 0.4,
    bloomStrength: 0.8,
    particleCount: 1000,
    tryOnCategory: 'outerwear',
  },
  love_hurts: {
    collection: 'love_hurts',
    accentColor: 0xff1493,  // Deep pink
    ambientIntensity: 0.5,
    bloomStrength: 0.6,
    particleCount: 800,
    tryOnCategory: 'tops',
  },
  signature: {
    collection: 'signature',
    accentColor: 0xb76e79,  // Rose gold
    ambientIntensity: 0.6,
    bloomStrength: 0.5,
    particleCount: 500,
    tryOnCategory: 'tops',
  },
};

/**
 * WebXR feature detection
 */
export async function detectARCapabilities(): Promise<{
  webxrSupported: boolean;
  webcamSupported: boolean;
  recommendedMode: 'webxr' | 'webcam' | 'preview';
}> {
  let webxrSupported = false;
  let webcamSupported = false;

  // Check WebXR
  if (typeof navigator !== 'undefined' && navigator.xr) {
    try {
      webxrSupported = await navigator.xr.isSessionSupported('immersive-ar');
    } catch {
      webxrSupported = false;
    }
  }

  // Check webcam
  if (typeof navigator !== 'undefined' && navigator.mediaDevices) {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      webcamSupported = devices.some(d => d.kind === 'videoinput');
    } catch {
      webcamSupported = false;
    }
  }

  // Determine recommended mode
  let recommendedMode: 'webxr' | 'webcam' | 'preview' = 'preview';
  if (webxrSupported) {
    recommendedMode = 'webxr';
  } else if (webcamSupported) {
    recommendedMode = 'webcam';
  }

  return { webxrSupported, webcamSupported, recommendedMode };
}

/**
 * AR API client helper
 */
export class ARApiClient {
  private baseUrl: string;
  private sessionId: string | null = null;

  constructor(config: ARConfig = AR_CONFIG) {
    this.baseUrl = config.apiBaseUrl;
  }

  /**
   * Create a new AR session
   */
  async createSession(collection: string, mode: string = 'webcam'): Promise<string> {
    const response = await fetch(`${this.baseUrl}/api/v1/ar/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        collection,
        mode,
        user_agent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
        screen_width: typeof window !== 'undefined' ? window.innerWidth : undefined,
        screen_height: typeof window !== 'undefined' ? window.innerHeight : undefined,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to create AR session: ${response.statusText}`);
    }

    const data = await response.json();
    this.sessionId = data.session_id as string;
    return this.sessionId!;
  }

  /**
   * Get AR products for a collection
   */
  async getProducts(collection: string): Promise<any[]> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/ar/products/${collection}`,
      { method: 'GET' }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch AR products: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Record a try-on event
   */
  async recordTryOn(productId: string, success: boolean = true, durationMs?: number): Promise<void> {
    if (!this.sessionId) {
      console.warn('No active AR session');
      return;
    }

    const params = new URLSearchParams({
      product_id: productId,
      success: String(success),
    });
    if (durationMs !== undefined) {
      params.append('duration_ms', String(durationMs));
    }

    await fetch(
      `${this.baseUrl}/api/v1/ar/sessions/${this.sessionId}/tryon?${params}`,
      { method: 'POST' }
    );
  }

  /**
   * Submit try-on request to FASHN API
   */
  async submitTryOn(modelImageUrl: string, garmentImageUrl: string, category: string = 'tops'): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/v1/virtual-tryon`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model_image_url: modelImageUrl,
        garment_image_url: garmentImageUrl,
        category,
        provider: 'fashn',
        mode: 'balanced',
      }),
    });

    if (!response.ok) {
      throw new Error(`Try-on request failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Check try-on job status
   */
  async getTryOnStatus(jobId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/v1/virtual-tryon/${jobId}`);
    if (!response.ok) {
      throw new Error(`Failed to get try-on status: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * End the current session
   */
  async endSession(conversion: boolean = false): Promise<void> {
    if (!this.sessionId) return;

    await fetch(
      `${this.baseUrl}/api/v1/ar/sessions/${this.sessionId}?status=completed&conversion=${conversion}`,
      { method: 'PATCH' }
    );
    this.sessionId = null;
  }

  /**
   * Get current session ID
   */
  getSessionId(): string | null {
    return this.sessionId;
  }
}

// Default client instance
export const arApiClient = new ARApiClient();

export default AR_CONFIG;
